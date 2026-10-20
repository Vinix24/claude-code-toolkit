"""PostToolUse-hook: lint elk tekstbestand dat Claude schrijft en geef de
bevindingen terug aan de sessie.

Waarom een hook en niet alleen een regel in CLAUDE.md: een instructie die in
elke sessie meelaadt dwingt niets af. In het corpus waarop deze linter is
gemeten stonden 3.282 em-dashes, terwijl de schrijfregels die in elke sessie
laadden "geen em-dashes" zeiden. Deze hook draait de harness, niet het model.

Blokkeert nooit. Hij meldt en het model repareert. Bij proza is een treffer een
afweging en geen fout, en een poort die een schrijfactie tegenhoudt kost dan
meer dan hij oplevert.

Invoer: hook-JSON op stdin. Uitvoer: hook-JSON op stdout, of niets.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent / "skills" / "slop-check" / "scripts"))

import slop_lint as sl  # noqa: E402

INSTRUCTIE = (
    "De slop-linter vond treffers in het bestand dat je zojuist schreef. "
    "Beoordeel ze en repareer wat een echte tic is; een opsomming van "
    "gelijkwaardige elementen en een citaat zijn dat niet. Twijfel je bij een "
    "regel, laat hem staan en meld het."
)


def bestandspad(invoer: dict) -> Path | None:
    respons = invoer.get("tool_response")
    pad = respons.get("filePath") if isinstance(respons, dict) else None
    if not pad:
        tool_input = invoer.get("tool_input")
        pad = tool_input.get("file_path") if isinstance(tool_input, dict) else None
    return Path(pad) if isinstance(pad, str) and pad else None


def verwerk(invoer: dict) -> dict | None:
    """De hook-uitvoer voor deze invoer, of None als er niets te melden is."""
    pad = bestandspad(invoer)
    if pad is None or not pad.is_file():
        return None

    cfg = sl.laad_config(pad)
    if not cfg["enabled"]:
        return None
    if pad.suffix.lower() not in cfg["extensions"]:
        return None
    if sl.NEGEER_DIRS & set(pad.resolve().parts):
        return None
    if not sl.in_scope(pad, cfg):
        return None

    lagen = sl.bouw_lagen(cfg)
    res = sl.scan([pad], lagen, cfg["min_words"])
    if not sl.boven_de_lat(res, cfg["max_density"]):
        return None

    # Een melding bij elk schoon bestand leert je de hook te negeren, en dan is
    # de volgende echte melding ook weg. Daarom alleen bij treffers.
    tekst = sl.rapport(res, lagen, regels=True, relatief_aan=cfg.wortel)
    return {
        "systemMessage": f"slop-linter: {len(res.bevindingen)} treffers in {pad.name}",
        "suppressOutput": True,
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": f"{INSTRUCTIE}\n\n{tekst}",
        },
    }


def main() -> int:
    try:
        invoer = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(invoer, dict):
        return 0
    uitvoer = verwerk(invoer)
    if uitvoer is not None:
        print(json.dumps(uitvoer, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
