"""Alle netwerkproeven gebruiken uitsluitend een HTTP-server op localhost."""

import contextlib
import io
import json
import os
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from scripts import check


class CheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.routes = {}
        cls.requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                cls.requests.append((self.command, self.path, dict(self.headers)))
                status, headers, body, delay = cls.routes.get(self.path, (404, [], b"", 0))
                time.sleep(delay)
                try:
                    self.send_response(status)
                    for key, value in headers:
                        self.send_header(key, value)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def log_message(self, *args):
                pass

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.routes.clear()
        self.requests.clear()

    def page(self, php=None, html="", path="/", status=200, headers=(), delay=0):
        fields = list(headers)
        if php is not None:
            fields.append(("X-Powered-By", php))
        self.routes[path] = (status, fields, html.encode(), delay)
        return self.base + path

    def assert_outcome(self, result, expected):
        self.assertIsNotNone(result["uitkomst"])
        self.assertEqual(result["uitkomst"], expected)
        for word in ("gepatcht", "veilig"):
            self.assertNotIn(word, json.dumps(result, ensure_ascii=False).lower())
        self.assertIn("CVE-2026-109618", result["bericht_hoster"])
        self.assertIn("CVE-2026-109619", result["bericht_hoster"])
        self.assertIn("21 oktober 2026", result["bericht_hoster"])

    def test_outdated(self):
        result = check.check(self.page("PHP/8.3.20"))
        self.assert_outcome(result, "verouderd")
        self.assertEqual(result["beoordeling"], "kan kwetsbaar zijn")
        self.assertEqual(result["titel"], "Een oud PHP-nummer is zichtbaar.")
        self.assertEqual(result["php_versie"], "8.3.20")
        self.assertIn("8.3.20", result["bericht_hoster"])

    def test_distribution_suffix(self):
        for version in ("8.2.34-1~deb12u1", "8.3.20-0ubuntu0.24.04.1", "8.4.26+deb13u1"):
            with self.subTest(version=version):
                result = check.check(self.page("PHP/" + version))
                self.assert_outcome(result, "distributie")
                self.assertEqual(result["beoordeling"], "onbekend")
                self.assertEqual(result["php_versie"], version)

    def test_legacy(self):
        for version in ("8.1.33", "8.0.30", "7.4.33"):
            with self.subTest(version=version):
                result = check.check(self.page("PHP/" + version))
                self.assert_outcome(result, "oud")
                self.assertEqual(result["titel"], "PHP 7.4 tot en met 8.1")
                self.assertEqual(result["beoordeling"], "kan kwetsbaar zijn, tenzij je hoster een backport heeft toegepast")

    def test_unsupported_legacy(self):
        for version in ("5.4.0", "5.6.40", "7.0.33", "7.2.34", "7.3.33"):
            with self.subTest(version=version):
                result = check.check(self.page("PHP/" + version))
                self.assert_outcome(result, "oud")
                self.assertEqual(result["titel"], "Een PHP-versie zonder reparatie van PHP is zichtbaar")
                self.assertEqual(result["beoordeling"], "kan kwetsbaar zijn; PHP zelf noemt voor deze versie geen reparatie, upgrade nodig")

    def test_legacy_distribution_suffixes(self):
        for version in ("7.4.33-1~deb11u1", "8.0.30-0ubuntu1", "8.1.33+deb12u1"):
            with self.subTest(version=version):
                result = check.check(self.page("PHP/" + version))
                self.assert_outcome(result, "distributie")
                self.assertEqual(result["beoordeling"], "onbekend")
        for version in ("5.6.40-1~deb8u1", "7.2.34-1~deb10u1", "7.3.33+ubuntu1"):
            with self.subTest(version=version):
                result = check.check(self.page("PHP/" + version))
                self.assert_outcome(result, "oud")
                self.assertEqual(result["beoordeling"], "kan kwetsbaar zijn, vraag de leverancier om bevestiging")
                self.assertIn("noemen voor 7.3 en ouder geen backport", result["toelichting"])

    def test_assessment_severity_order(self):
        # Waardeer de werkelijk uitgegeven tekst, niet een interne categorie of prioriteit.
        severity = {
            "onbekend": 0,
            "lijkt bijgewerkt volgens het versienummer": 1,
            "kan kwetsbaar zijn": 2,
            "kan kwetsbaar zijn, tenzij je hoster een backport heeft toegepast": 3,
            "kan kwetsbaar zijn; PHP zelf noemt voor deze versie geen reparatie, upgrade nodig": 4,
        }
        groups = [("5.4.0", "5.6.40", "7.2.34", "7.3.33"),
                  ("7.4.33", "8.0.30", "8.1.33"),
                  ("8.2.34", "8.3.20", "8.4.26", "8.5.11"),
                  ("8.2.35", "8.3.36", "8.4.27", "8.5.12")]
        ranks = []
        for group in groups:
            ranks.append([])
            for version in group:
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    code = check.main([self.page("PHP/" + version), "--json"])
                self.assertEqual(code, 0)
                assessment = json.loads(stdout.getvalue())["beoordeling"]
                self.assertIn(assessment, severity)
                ranks[-1].append(severity[assessment])
        for older, newer in zip(ranks, ranks[1:]):
            self.assertGreater(min(older), max(newer), "Een oudere PHP-reeks krijgt een mildere of gelijke beoordeling.")

    def test_legacy_mixed_headers_choose_strongest_assessment(self):
        cases = [("7.4.33", "7.2.34", "7.2.34"), ("7.2.34", "7.4.33", "7.2.34"),
                 ("8.3.20", "7.4.33", "7.4.33"), ("8.1.33-1ubuntu1", "8.3.20", "8.3.20"),
                 ("7.2.34-1ubuntu1", "7.3.33", "7.3.33"),
                 ("7.4.33", "7.2.34-1ubuntu1", "7.2.34-1ubuntu1")]
        for powered_by, server, expected in cases:
            with self.subTest(powered_by=powered_by, server=server):
                result = check.check(self.page("PHP/" + powered_by, headers=[("Server", "PHP/" + server)]))
                self.assertEqual(result["php_versie"], expected)

    def test_updated_number(self):
        result = check.check(self.page("PHP/8.4.27"))
        self.assert_outcome(result, "bijgewerkt")
        self.assertEqual(result["beoordeling"], "lijkt bijgewerkt volgens het versienummer")
        self.assertEqual(result["titel"], "Het versienummer lijkt bijgewerkt.")

    def test_hidden(self):
        for cms in ("WordPress 6.8.3", "Joomla!", "Drupal 11"):
            with self.subTest(cms=cms):
                html = f'<META content="{cms}" NAME="Generator" />'
                self.assert_outcome(check.check(self.page(html=html)), "verborgen")
        self.assert_outcome(check.check(self.page("PHP")), "verborgen")
        self.assert_outcome(check.check(self.page("PHP/8.4")), "verborgen")

    def test_absent(self):
        html = '<meta name="generator" content="Hugo"><p>WordPress, PHP/8.4.26</p>'
        self.assert_outcome(check.check(self.page(html=html)), "geen_php")

    def assert_hidden_signal(self, *, expected, **page_args):
        before = len(self.requests)
        result = check.check(self.page(**page_args))
        self.assert_outcome(result, "verborgen")
        self.assertIsNone(result["php_versie"])
        self.assertEqual(result["beoordeling"], "onbekend")
        self.assertTrue(any(expected in signal for signal in result["aanwijzingen"]["signalen"]))
        self.assertEqual(len(self.requests), before + 1)
        return result

    def test_session_cookie_signal(self):
        result = self.assert_hidden_signal(expected="PHPSESSID", headers=[("Set-Cookie", "other=abc"),
            ("Set-Cookie", "PHPSESSID=private-session-123; Path=/; HttpOnly")])
        self.assertNotIn("private-session-123", json.dumps(result))
        self.assertNotIn("Cookie", self.requests[-1][2])

    def test_wordpress_link_header_signal(self):
        self.assert_hidden_signal(expected="Link-header", headers=[
            ("Link", '<https://example.org/wp-json/>; rel="https://api.w.org/"')])

    def test_php_header_without_number_signal(self):
        self.assert_hidden_signal(expected="X-Powered-By noemt PHP", php="PHP")

    def test_custom_powered_by_signal(self):
        self.assert_hidden_signal(expected="kan ook een andere techniek zijn", php="Hosting op maat 8.4.27")

    def assert_attribute_signal(self, value, expected):
        for tag, attribute in (("a", "href"), ("img", "src"), ("form", "action")):
            with self.subTest(attribute=attribute, value=value):
                html = f'<{tag} {attribute}="{value}"></{tag}>'
                self.assert_hidden_signal(expected=f"{attribute} bevat {expected}", html=html)

    def test_php_attribute_signal(self):
        self.assert_attribute_signal("https://example.org/contact.php", ".php")

    def test_wordpress_content_signal(self):
        self.assert_attribute_signal("/wp-content/style.css?ver=8.4.27", "/wp-content/")

    def test_wordpress_includes_signal(self):
        self.assert_attribute_signal("/wp-includes/script.js?ver=8.4.27", "/wp-includes/")

    def test_wordpress_json_signal(self):
        self.assert_attribute_signal("/wp-json/wp/v2/", "/wp-json/")

    def test_index_php_query_signal(self):
        self.assert_attribute_signal("index.php?option=8.4.27", ".php")

    def test_cms_and_asset_versions_never_become_php_versions(self):
        for html in ('<meta name="generator" content="WordPress 8.4.27">',
                     '<meta name="generator" content="Joomla 8.3.20">',
                     '<meta name="generator" content="Drupal 8.5.12">',
                     '<meta name="generator" content="WordPress PHP/8.4.27">',
                     '<script src="/wp-includes/script.js?ver=8.4.27"></script>',
                     '<a href="/wp-json/?ver=PHP/8.4.27">API</a>'):
            with self.subTest(html=html):
                result = check.check(self.page(html=html))
                self.assert_outcome(result, "verborgen")
                self.assertIsNone(result["php_versie"])
                self.assertIn("Gevonden PHP-versie: niet zichtbaar", result["bericht_hoster"])

    def test_similar_strings_are_not_signals(self):
        cases = [dict(headers=[("Set-Cookie", "other=PHPSESSID; Path=/")]),
                 dict(headers=[("Set-Cookie", "PHPSESSID_extra=value")]),
                 dict(headers=[("Link", '<https://api.w.org/>; rel="alternate"')]),
                 dict(html='<a href="/image.php.jpg">Photo</a>'),
                 dict(html='<!-- <a href="/wp-json/"> --> <p>/index.php?</p>'),
                 dict(html='<script>var path = "/wp-content/file.php";</script>')]
        for args in cases:
            with self.subTest(args=args):
                self.assert_outcome(check.check(self.page(**args)), "geen_php")

    def test_header_caveat_in_both_number_outcomes(self):
        for version in ("5.6.40", "7.2.34", "7.3.33-1~deb10u1", "7.4.33", "8.4.26", "8.4.27"):
            stdout = io.StringIO()
            with self.subTest(version=version), contextlib.redirect_stdout(stdout):
                check.main([self.page("PHP/" + version)])
            output = stdout.getvalue()
            self.assertIn("CDN", output)
            self.assertIn("cache", output)
            if version == "8.4.27":
                self.assertIn("andere server", output)
                self.assertIn("meer servers", output)
            else:
                self.assertIn("tussenserver", output)

    def test_legacy_advice_is_limited_to_primary_evidence(self):
        for version in ("5.4.0", "7.3.33", "7.4.33", "8.0.30", "8.1.33"):
            with self.subTest(version=version):
                result = check.check(self.page("PHP/" + version))
                self.assert_outcome(result, "oud")
                if version in ("5.4.0", "7.3.33"):
                    self.assertIn("noemen voor 7.3 en ouder geen backport", result["toelichting"])
                    self.assertIn("Een leverancier kan wel een reparatie hebben", result["toelichting"])
                else:
                    self.assertIn("7.4, 8.0 en 8.1", result["toelichting"])
                self.assertNotIn("geen enkele fix", result["toelichting"])

    def test_purpose_signals_and_wording_in_text_and_json(self):
        cases = [dict(php="PHP/8.4.26"), dict(php="PHP/8.4.26-1~deb13u1"), dict(php="PHP/7.3.33"),
                 dict(php="PHP/7.2.34-1ubuntu1"), dict(php="PHP/7.4.33"), dict(php="PHP/7.4.33-1~deb11u1"),
                 dict(php="PHP/8.4.27"), dict(php="PHP"), dict(), dict(status=403)]
        for args in cases:
            for option in ([], ["--json"]):
                stdout = io.StringIO()
                with self.subTest(args=args, option=option), contextlib.redirect_stdout(stdout):
                    check.main([self.page(**args)] + option)
                output = stdout.getvalue()
                for word in ("gepatcht", "veilig"):
                    self.assertNotIn(word, output.lower())
                if option:
                    result = json.loads(output)
                    self.assertEqual(result["doel"], check.PURPOSE)
                    self.assertEqual(next(iter(result)), "doel")
                    self.assertIn("8.2.34 kan kwetsbaar zijn", result["vergelijking"])
                else:
                    self.assertTrue(output.startswith(check.PURPOSE))
                    self.assertIn("Gevonden signalen:", output)
                    self.assertIn("8.2.35 is de reparatie", output)

    def test_hoster_message_asks_three_concrete_questions(self):
        result = check.check(self.page("PHP/8.4.26"))
        message = result["bericht_hoster"]
        for text in ("exacte PHP-versie per server", "update van 21 oktober 2026", "Zo nee",
                     "backport", "upgrade", "8.2.35", "8.3.36", "8.4.27", "8.5.12"):
            self.assertIn(text, message)

    def test_legacy_hoster_message_requests_confirmation_or_dated_upgrade(self):
        for version in ("5.4.0", "7.2.34", "7.3.33-1~deb10u1", "7.4.33", "8.1.33-1ubuntu1"):
            with self.subTest(version=version):
                result = check.check(self.page("PHP/" + version))
                message = result["bericht_hoster"]
                self.assertIn("Gevonden PHP-versie: " + version, message)
                self.assertIn("bevestig de toegepaste backport van de leverancier", message)
                self.assertIn("datum voor een upgrade naar een ondersteunde reeks", message)

    def test_release_boundaries(self):
        # Letterlijke verwachtingen: 8.4.27 -> 8.4.26 in de code moet deze test breken.
        cases = [("8.2.34", "verouderd"), ("8.2.35", "bijgewerkt"), ("8.2.36", "bijgewerkt"),
                 ("8.3.35", "verouderd"), ("8.3.36", "bijgewerkt"), ("8.3.37", "bijgewerkt"),
                 ("8.4.26", "verouderd"), ("8.4.27", "bijgewerkt"), ("8.4.28", "bijgewerkt"),
                 ("8.5.11", "verouderd"), ("8.5.12", "bijgewerkt"), ("8.5.13", "bijgewerkt"),
                 ("8.4.9", "verouderd"), ("8.4.100", "bijgewerkt"), ("8.4.27-1~deb13u1", "bijgewerkt")]
        for version, expected in cases:
            with self.subTest(version=version):
                self.assert_outcome(check.check(self.page("PHP/" + version)), expected)

    def test_server_header(self):
        url = self.page(headers=[("Server", "Apache PHP/8.4.26")])
        self.assert_outcome(check.check(url), "verouderd")

    def test_conflicting_headers_keep_old_version(self):
        url = self.page("PHP/8.4.27", headers=[("Server", "Apache PHP/8.3.20"),
                                             ("X-Powered-By", "PHP/8.2.35")])
        result = check.check(url)
        self.assert_outcome(result, "verouderd")
        self.assertEqual(result["php_versie"], "8.3.20")

    def test_redirect(self):
        url = self.page(path="/page", status=302, headers=[("Location", "/page/")])
        self.page("PHP/8.4.27", path="/page/")
        result = check.check(url)
        self.assert_outcome(result, "bijgewerkt")
        self.assertEqual(result["eind_url"], self.base + "/page/")
        self.assertEqual([(m, p) for m, p, _ in self.requests], [("GET", "/page"), ("GET", "/page/")])

    def test_external_redirect_never_requested(self):
        for target in (f"http://localhost:{self.server.server_port}/other", "https://example.org/",
                       "http://127.0.0.1:9/", "file:///tmp/test", "http://user:pass@127.0.0.1/"):
            with self.subTest(target=target):
                self.requests.clear()
                url = self.page(status=302, headers=[("Location", target)])
                with self.assertRaises(ValueError):
                    check.fetch(url)
                self.assertEqual(len(self.requests), 1)

    def test_redirect_loop_stops(self):
        url = self.page(status=302, headers=[("Location", "/")])
        with self.assertRaisesRegex(ValueError, "te veel"):
            check.fetch(url)
        self.assertEqual(len(self.requests), 6)

    def test_timeout(self):
        url = self.page("PHP/8.4.27", delay=0.2)
        start = time.monotonic()
        with self.assertRaises((OSError, check.URLError)):
            check.fetch(url, timeout=0.03)
        self.assertLess(time.monotonic() - start, 1)
        self.assertEqual(len(self.requests), 1)

    def test_timeout_has_unknown_result_and_hoster_message(self):
        result = check.check(self.page(delay=0.2), timeout=0.03)
        self.assertIsNone(result["uitkomst"])
        self.assertEqual(result["beoordeling"], "onbekend")
        self.assertIn("niet zichtbaar", result["bericht_hoster"])
        self.assertEqual(len(self.requests), 1)

    def test_malformed_http_does_not_crash(self):
        with patch.object(check, "fetch", side_effect=check.HTTPException("Invalid status line")):
            result = check.check(self.base)
        self.assertIsNone(result["uitkomst"])
        self.assertEqual(result["beoordeling"], "onbekend")
        self.assertEqual(self.requests, [])

    def test_only_one_get_and_no_assets(self):
        url = self.page("PHP/8.4.27", '<img src="https://example.org/tracker"><script src="/script.js"></script>',
                        path="/chosen?view=1")
        check.check(url)
        self.assertEqual([(m, p) for m, p, _ in self.requests], [("GET", "/chosen?view=1")])
        self.assertTrue(self.requests[0][2]["User-Agent"].startswith("Mozilla/"))
        self.assertNotIn("Cookie", self.requests[0][2])

    def test_proxy_environment_ignored(self):
        env = {"http_proxy": "http://127.0.0.1:9", "HTTP_PROXY": "http://127.0.0.1:9",
               "no_proxy": "", "NO_PROXY": ""}
        with patch.dict(os.environ, env):
            self.assert_outcome(check.check(self.page("PHP/8.4.27")), "bijgewerkt")

    def test_input_rejected_before_network(self):
        for url in ("file:///etc/passwd", "ftp://example.org", "https://", "example.org",
                    "https://user:pass@example.org", "https://example.org\n", "https://example.org:bad",
                    "https://example.org\\@other.org"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                check.validate_url(url)
        self.assertEqual(self.requests, [])

    def test_unknown_or_prerelease_version_not_marked_patched(self):
        for version in ("8.6.0", "9.0.0", "8.4.27RC1", "8.5.12-dev"):
            with self.subTest(version=version):
                result = check.check(self.page("PHP/" + version))
                self.assertIsNone(result["uitkomst"])
                self.assertEqual(result["php_versie"], version)

    def test_json_cli_and_message(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = check.main([self.page("PHP/8.3.20"), "--json"])
        self.assertEqual(code, 0)
        self.assert_outcome(json.loads(stdout.getvalue()), "verouderd")
        self.assertEqual(len(self.requests), 1)

    def test_http_failure_is_not_no_php(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = check.main([self.page(status=403), "--json"])
        result = json.loads(stdout.getvalue())
        self.assertEqual(code, 2)
        self.assertIsNone(result["uitkomst"])
        self.assertEqual(result["beoordeling"], "onbekend")

    def test_body_limit_reported(self):
        html = 'x' * (check.MAX_HTML + 1) + '<meta name="generator" content="WordPress">'
        result = check.check(self.page(html=html))
        self.assertTrue(result["html_afgekapt"])
        self.assertIsNone(result["uitkomst"])

    def test_text_ends_with_copyable_message(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = check.main([self.page("PHP/8.4.27")])
        output = stdout.getvalue()
        self.assertEqual(code, 0)
        self.assertNotIn("veilig", output.lower())
        self.assertIn("Bericht voor je websitebouwer of hoster:", output)
        self.assertIn("Bedankt!\n\nVoor je websitebouwer: zo weet je het zeker", output)
        self.assertIn("<?php echo PHP_VERSION;", output)
        self.assertIn("verwijder het bestand direct", output)
        self.assertTrue(output.rstrip().endswith(check.DATA["builder_steps"][-1]))


if __name__ == "__main__":
    unittest.main()
