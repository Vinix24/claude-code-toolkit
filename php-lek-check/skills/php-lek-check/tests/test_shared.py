import copy
import json
import re
import shutil
import subprocess
import sys
import unittest
from email.message import Message
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

from scripts import check

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = json.loads((ROOT / "cases.json").read_text())


def run_case(item):
    headers = Message()
    for name, values in item["headers"].items():
        for value in values if isinstance(values, list) else [values]:
            headers[name] = value
    return check.evaluate(headers, item["html"], item["cookie"], item["cms"], FIXTURES["url"])


class PrivacyParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_sources = False
        self.script = None
        self.scripts = {}
        self.styles = []
        self.in_style = False
        self.csp = None
        self.violations = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "section" and attrs.get("id") == "sources":
            self.in_sources = True
        if tag == "meta" and attrs.get("http-equiv", "").lower() == "content-security-policy":
            self.csp = attrs.get("content", "")
        if tag in ("iframe", "object", "embed", "base") or (tag == "meta" and attrs.get("http-equiv", "").lower() == "refresh"):
            self.violations.append(tag)
        for name in ("src", "href", "srcset", "poster", "data", "action"):
            value = attrs.get(name, "").strip()
            if value and not value.startswith(("#", "data:")):
                if not (self.in_sources and tag == "a" and name == "href" and value.startswith("https://")):
                    self.violations.append(name + ":" + attrs[name])
            if name == "src" and attrs.get(name) and not attrs[name].startswith("data:"):
                self.violations.append("Niet-ingebouwde bron: " + attrs[name])
        if tag == "script":
            self.script = attrs.get("id", "zonder-id")
            self.scripts[self.script] = ""
        if tag == "style":
            self.in_style = True
        if attrs.get("style"):
            self.styles.append(attrs["style"])

    def handle_endtag(self, tag):
        if tag == "section":
            self.in_sources = False
        if tag == "script":
            self.script = None
        if tag == "style":
            self.in_style = False

    def handle_data(self, text):
        if self.script:
            self.scripts[self.script] += text
        if self.in_style:
            self.styles.append(text)


def assert_private_html(test, html):
    parser = PrivacyParser()
    parser.feed(html)
    test.assertEqual(parser.violations, [])
    required = ("default-src 'none'", "connect-src 'none'", "img-src data:", "style-src 'unsafe-inline'",
                "script-src 'unsafe-inline'", "form-action 'none'", "base-uri 'none'")
    directives = {part.strip() for part in (parser.csp or "").split(";")}
    test.assertTrue(set(required).issubset(directives))
    test.assertLess(html.index('http-equiv="Content-Security-Policy"'), html.index("<style>"))
    test.assertNotRegex("\n".join(parser.styles), r"(?i)@import|url\s*\(")
    for name, script in parser.scripts.items():
        test.assertNotRegex(script, r"XMLHttpRequest|WebSocket|EventSource|sendBeacon|localStorage|sessionStorage|indexedDB|document\.cookie\s*=")
        if name != "bookmarklet-source":
            test.assertNotRegex(script, r"\bfetch\s*\(")
    test.assertEqual(len(re.findall(r"\bfetch\s*\(", parser.scripts["bookmarklet-source"])), 1)
    outside_bookmarklet = html.replace(parser.scripts["bookmarklet-source"], "")
    test.assertNotRegex(outside_bookmarklet, r"\bfetch\s*\(|XMLHttpRequest")


class SharedTests(unittest.TestCase):
    def test_shared_cases(self):
        for item in FIXTURES["cases"]:
            with self.subTest(case=item["name"]):
                result = run_case(item)
                for key, value in item["expected"].items():
                    self.assertEqual(result[key], value, key)
                self.assertNotRegex(json.dumps(result), r"(?i)gepatcht|veilig|private-value")

    @unittest.skipUnless(shutil.which("node"), "Node ontbreekt; draai ook node --test tests/*.test.cjs.")
    def test_python_javascript_full_result_parity(self):
        completed = subprocess.run(["node", str(ROOT / "tests/export_results.cjs")], capture_output=True, text=True, check=True)
        javascript = json.loads(completed.stdout)
        self.assertEqual(len(javascript), len(FIXTURES["cases"]))
        for item, other in zip(FIXTURES["cases"], javascript):
            with self.subTest(case=item["name"]):
                self.assertEqual(run_case(item), other)

    def test_patch_mutation_is_detected(self):
        mutated = copy.deepcopy(check.DATA)
        mutated["patches"]["8.4"] = 26
        item = next(item for item in FIXTURES["cases"] if item["name"] == "php-8.4.26")
        with patch.object(check, "DATA", mutated):
            with self.assertRaises(AssertionError):
                self.assertEqual(run_case(item)["uitkomst"], item["expected"]["uitkomst"])

    def test_built_page_is_current(self):
        from scripts.build import build
        self.assertEqual((ROOT / "index.html").read_text(), build())

    def test_page_has_no_external_connections(self):
        assert_private_html(self, (ROOT / "index.html").read_text())

    def test_network_guard_detects_regressions(self):
        html = (ROOT / "index.html").read_text()
        mutants = [html.replace('<main>', '<main><img src="https://tracker.example/pixel">'),
                   html.replace('<main>', '<main><a href="https://tracker.example/">test</a>'),
                   html.replace('<style>', '<style>@import "https://tracker.example/style.css";'),
                   html.replace('<style>', '<style>body{background:url(https://tracker.example/pixel)}'),
                   html.replace('<script id="page-script">', '<script id="page-script">fetch("https://tracker.example/");'),
                   html.replace('<script id="page-script">', '<script id="page-script">new XMLHttpRequest();'),
                   html.replace('<main>', '<main onclick="fetch(\'/tracker\')">'),
                   html.replace('<main>', '<main><img src="/tracker">'),
                   html.replace("connect-src 'none'", "connect-src *")]
        for mutant in mutants:
            with self.subTest(mutant=mutants.index(mutant)), self.assertRaises(AssertionError):
                assert_private_html(self, mutant)

    def test_python_script_stays_short(self):
        self.assertLess(len((ROOT / "scripts/check.py").read_text().splitlines()), 200)


if __name__ == "__main__":
    unittest.main()
