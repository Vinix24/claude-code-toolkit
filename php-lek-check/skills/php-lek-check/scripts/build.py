#!/usr/bin/env python3
"""Bouw één offline HTML-bestand. Geen netwerk of externe pakketten."""
import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build():
    data = json.loads((ROOT / "rules.json").read_text(encoding="utf-8"))
    read = lambda name: (ROOT / "src" / name).read_text(encoding="utf-8").strip()
    compact = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    core, render = read("core.js"), read("render.js")
    bookmarklet = read("bookmarklet.js").replace("/*__RULES__*/", compact).replace("/*__CORE__*/", core).replace("/*__RENDER__*/", render)
    order = ("hidden", "none", "outdated", "distribution", "unsupported", "unsupported_suffix", "legacy", "updated")
    outcomes = "\n".join('<article class="outcome"><h3>' + html.escape(data["results"][key]["title"]) +
        '</h3><p><strong>' + html.escape(data["results"][key]["assessment"]) + '</strong></p><p>' +
        html.escape(data["results"][key]["explanation"]) + '</p></article>' for key in order)
    replacements = {"PAGE_INTRO": html.escape(data["page_intro"]), "BUTTON": html.escape(data["button"]),
        "BUILDER_STEPS": "".join("<li>" + html.escape(step) + "</li>" for step in data["builder_steps"]),
        "OUTCOMES": outcomes, "DATE": html.escape(data["verified"]), "RULES_JSON": compact,
        "BOOKMARKLET": bookmarklet.replace("</", "<\\/"), "CORE": core, "RENDER": render, "PAGE_SCRIPT": read("page.js")}
    page = read("index.template.html")
    for name, value in replacements.items():
        page = page.replace("__" + name + "__", value)
    return page + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Controleer of index.html actueel is, zonder te schrijven")
    args = parser.parse_args()
    output = build()
    path = ROOT / "index.html"
    if args.check:
        if not path.exists() or path.read_text(encoding="utf-8") != output:
            raise SystemExit("index.html wijkt af. Draai python3 -B scripts/build.py.")
        print("index.html komt overeen met de gedeelde regels en bronbestanden.")
    else:
        path.write_text(output, encoding="utf-8")
        print(f"index.html gebouwd ({len(output.encode('utf-8'))} bytes).")
