#!/usr/bin/env python3
"""Vragenhulp bij PHP2Shell. Alleen standaardbibliotheek; geen opslag."""
import argparse
import json
import re
import sys
from html.parser import HTMLParser
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

RULES_FILE = Path(__file__).with_name("rules.json")
if not RULES_FILE.exists():
    RULES_FILE = Path(__file__).resolve().parent.parent / "rules.json"
DATA = json.loads(RULES_FILE.read_text(encoding="utf-8"))
PURPOSE, COMPARISON = DATA["purpose"], DATA["comparison"]
TIMEOUT, MAX_HTML = 15, 1024 * 1024
PATTERNS = {key: re.compile(value, re.I) for key, value in DATA["patterns"].items()}


class PageSignals(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values, self.attributes = [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta" and (attrs.get("name") or "").lower() == "generator":
            self.values.append(attrs.get("content") or "")
        self.attributes.extend((name, attrs[name] or "") for name in ("src", "action", "href") if name in attrs)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Eerst controleren; nooit automatisch een andere host bezoeken.


def validate_url(url):
    parts = urlsplit(url)
    if (parts.scheme not in ("http", "https") or not parts.hostname
            or parts.username is not None or parts.password is not None
            or "\\" in url or any(ord(c) <= 32 or ord(c) == 127 for c in url)):
        raise ValueError("Gebruik een volledige http://- of https://-URL zonder inloggegevens of spaties.")
    return parts.hostname, parts.port or (443 if parts.scheme == "https" else 80), parts.scheme


def fetch(url, timeout=TIMEOUT):
    origin = validate_url(url)
    opener = build_opener(ProxyHandler({}), NoRedirect())
    for step in range(6):
        request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; PHP-versiecheck/3.0)",
                                       "Accept-Encoding": "identity"})
        try:
            response = opener.open(request, timeout=timeout)
        except HTTPError as exc:
            response = exc
        with response:
            if response.code in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                if not location or step == 5:
                    raise ValueError("Doorverwijzing ontbreekt of er zijn te veel doorverwijzingen.")
                target = urljoin(url, location)
                destination = validate_url(target)
                upgrade = origin[1:] == (80, "http") and destination[1:] == (443, "https")
                if destination[0] != origin[0] or (destination != origin and not upgrade):
                    raise ValueError("Doorverwijzing naar een andere host, poort of naar http gestopt. Gebruik zelf het uiteindelijke websiteadres.")
                origin, url = destination, target
                continue
            return url, response.code, response.headers, response.read(MAX_HTML + 1)
    raise ValueError("Te veel doorverwijzingen.")


def choose_version(number, suffix):
    key = ".".join(map(str, number[:2]))
    facts = {"suffix": bool(suffix), "known_branch": key in DATA["patches"],
             "prerelease": bool(PATTERNS["prerelease"].search(suffix)),
             "fixed": key in DATA["patches"] and number[2] >= DATA["patches"][key]}
    for rule in DATA["rules"]:
        if all(number[:2] <= tuple(value) if name == "max_branch" else facts[name] == value
               for name, value in rule["when"].items()):
            return rule["result"], number, ".".join(map(str, number)) + suffix
    raise ValueError("Geen beoordelingsregel gevonden.")


def make_message(url, version):
    message = DATA["message"].format(url=url or "(vul je websiteadres in)", version=version or "niet zichtbaar")
    return message + "\n\nVoor je websitebouwer: zo weet je het zeker\n" + "\n".join(
        f"{index}. {step}" for index, step in enumerate(DATA["builder_steps"], 1))


def evaluate(headers, html="", cookie="", cms=False, url=""):
    fields = {name: headers.get_all(name, []) for name in ("X-Powered-By", "Server", "Set-Cookie", "Link")}
    evidence = {key: " | ".join(fields[key]) for key in ("X-Powered-By", "Server")}
    parser = PageSignals()
    parser.feed(html)
    signals = set()
    for key, value in evidence.items():
        if PATTERNS["php"].search(value):
            signals.add(f"Header {key} noemt PHP.")
    if evidence["X-Powered-By"].strip() and not PATTERNS["php"].search(evidence["X-Powered-By"]):
        signals.add(DATA["signals"]["custom"])
    for value in parser.values:
        match = PATTERNS["cms"].search(value)
        if match:
            signals.add(f"HTML-metatag generator noemt {match[0]}.")
    for name, value in parser.attributes:
        match = PATTERNS["path"].search(value)
        if match:
            signals.add(f"HTML-attribuut {name} bevat {match[0]}.")
    if any(PATTERNS["cookie"].search(value) for value in [v.split(";")[0] for v in fields["Set-Cookie"]] + [cookie]):
        signals.add(DATA["signals"]["cookie"])
    if PATTERNS["link"].search(" ".join(fields["Link"])):
        signals.add(DATA["signals"]["link"])
    if cms:
        signals.add(DATA["signals"]["cms_flag"])
    evidence.update(generator=parser.values, signalen=sorted(signals))
    header_text = " ".join(evidence[key] for key in ("X-Powered-By", "Server"))
    candidates = [choose_version(tuple(map(int, m.group(1, 2, 3))), m.group(4))
                  for m in PATTERNS["version"].finditer(header_text)]
    key, _, version = min(candidates, key=lambda c: (DATA["results"][c[0]]["priority"], c[1])) if candidates else (
        "hidden" if signals else "none", (), None)
    definition = DATA["results"][key]
    return {"doel": PURPOSE, "url": url, "uitkomst": definition["code"], "beoordeling": definition["assessment"],
            "php_versie": version, "vergelijking": COMPARISON, "titel": definition["title"],
            "toelichting": definition["explanation"], "aanwijzingen": evidence, "bericht_hoster": make_message(url, version)}


def check(url, timeout=TIMEOUT):
    result = {"doel": PURPOSE, "url": url, "uitkomst": None, "beoordeling": "onbekend", "php_versie": None, "vergelijking": COMPARISON}
    try:
        final_url, status, headers, body = fetch(url, timeout)
        encoding = headers.get("Content-Encoding", "identity").lower()
        html = body[:MAX_HTML].decode("utf-8", errors="replace") if encoding == "identity" else ""
        result = evaluate(headers, html, url=url)
        result.update(eind_url=final_url, http_status=status, html_afgekapt=len(body) > MAX_HTML)
        if result["uitkomst"] == "geen_php" and (status >= 400 or len(body) > MAX_HTML or encoding != "identity"):
            raise ValueError("Pagina niet volledig te beoordelen: foutpagina, te groot of gecomprimeerd. Vraag het na bij je hoster.")
    except (OSError, URLError, HTTPException, ValueError) as exc:
        reason = str(exc) if isinstance(exc, ValueError) else "Verbinding mislukt of time-out (15 seconden). Controleer je adres en internetverbinding."
        result.update(uitkomst=None, beoordeling="onbekend", titel="Controle niet afgerond", toelichting=reason)
    result["bericht_hoster"] = make_message(url, result["php_versie"])
    return result


def clean(value):
    return "".join(c if c.isprintable() or c == "\n" else "?" for c in str(value))


def main(argv=None):
    parser = argparse.ArgumentParser(description=PURPOSE)
    parser.add_argument("url", help="Volledig websiteadres, bijvoorbeeld https://jouwsite.nl")
    parser.add_argument("--json", action="store_true", help="Machineleesbare uitslag")
    args = parser.parse_args(argv)
    result = check(args.url)
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(PURPOSE + "\n")
        print(clean(f"{result['titel']}\nBeoordeling: {result['beoordeling']}\n"
                    f"PHP-versie: {result['php_versie'] or 'niet zichtbaar'}\n{result['toelichting']}"))
        print("Gevonden signalen: " + clean("; ".join(result.get("aanwijzingen", {}).get("signalen", [])) or "geen"))
        print(COMPARISON)
        if result.get("html_afgekapt"):
            print("Alleen de eerste 1 MiB van de pagina is bekeken.")
        if not result["uitkomst"]:
            print("Open de site, druk F12, kies Netwerk, herlaad en open het eerste verzoek.")
            print("Kijk bij Response Headers naar X-Powered-By en Server.")
        print("\nBericht voor je websitebouwer of hoster:\n" + clean(result["bericht_hoster"]))
    return 0 if result["uitkomst"] else 2


if __name__ == "__main__":
    sys.exit(main())
