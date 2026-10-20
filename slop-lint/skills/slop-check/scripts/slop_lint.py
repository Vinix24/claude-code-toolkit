#!/usr/bin/env python3
"""Deterministische slop-linter voor Nederlands proza.

Vangt de tics die tekst van een taalmodel herkenbaar maken: em-dashes,
buzzwords, AI-openers, kommaketens en retorische frames zoals "niet X maar Y".
Geen model en geen netwerk: dezelfde tekst geeft altijd dezelfde uitslag.

De regels zijn gemeten op een corpus van ruim 300.000 woorden eigen proza
(blogs, klantdocumenten, mails), niet uit een lijst verzonnen. Die meting wees
twee dingen aan:

  1. De klassieke woordenlijst is een opgelost probleem. Vijf buzzwords in
     310.000 woorden. Meegenomen omdat het gratis is, niet omdat het loont.
  2. Het volume zit in de structuur: 1.219 keer `, en` en 1.284 zinnen met drie
     of meer komma's. Volledig deterministisch te vangen.

Een tweede beoordeling op 120 zinnen vond drie frames die de regex miste; ze
staan hieronder gemarkeerd. Dezelfde beoordeling liet zien dat `, en` ook op
legitieme opsommingen afgaat. Een opsomming van gelijkwaardige elementen telt
daarom NIET mee, zie `_is_opsomming`.

Dekking: markdown, platte tekst, Word (met python-docx) en e-mail. Bij e-mail
wordt geciteerde tekst weggegooid: wat de ander schreef is niet jouw tekst.

Draaien:
    python3 slop_lint.py tekst.md               # losse bestanden of mappen
    python3 slop_lint.py                        # de map waarin je staat
    python3 slop_lint.py --profiel content      # een profiel uit de config
    python3 slop_lint.py --laag structuur       # een enkele laag
    python3 slop_lint.py --uit komma-maar       # een regel uitzetten
    python3 slop_lint.py --max-dichtheid 4      # pas falen boven een lat

Configuratie: `.claude/slop-lint.json` in het project (gezocht vanaf de map
waarin je staat, omhoog), daarna `~/.claude/slop-lint.json`, daarna de defaults.
De sleutels staan in README.md.

Uitsluiten in de tekst zelf: zet `slop-negeer:` met een reden op dezelfde regel.

Exitcode 1 zodra er iets gevonden is (of boven de lat), 0 als het schoon is,
2 bij een gebruiksfout. Daarmee kan dit als poort in CI draaien.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path

NEGEER_DIRS = {
    "node_modules", ".git", ".next", "dist", "build", "venv", ".venv",
    "__pycache__", "vendor", ".claude", ".pytest_cache",
}
NEGEER_MARKER = "slop-negeer:"
EXTENSIES = {".md", ".txt", ".docx", ".eml"}

# --------------------------------------------------------------------------
# Laag 1 -- gesloten woordenlijst. Zeldzaam, maar gratis.
# --------------------------------------------------------------------------

LEXICAAL = {
    "buzzword": r"\b(revolutionair|baanbrekend|game.?changer|disruptief|"
                r"next.?gen(eration)?|cutting.?edge|state.?of.?the.?art|"
                r"best.?in.?class|world.?class|holistisch|seamless|naadloze?|"
                r"empower\w*|ontgrendel\w*|unleash|unlock)\b",
    "ai-opener": r"(in de hedendaagse|in today'?s|stel je (een wereld )?voor|"
                 r"imagine a world|laten we (erin )?duiken|let'?s dive|"
                 r"in dit artikel (bespreken|verkennen)|delve into)",
    "ai-overgang": r"(het is (belangrijk|goed) om (op te merken|te vermelden)|"
                   r"it'?s worth noting|in essentie|in wezen|"
                   r"tot slot kunnen we|daarnaast moeten we|"
                   r"bovendien is het cruciaal|samengevat:)",
    "eerlijk-tic": r"(eerlijk gezegd|om eerlijk te zijn|maar eerlijk|"
                   r"eerlijk over |, eerlijk\b)",
    "caveat": r"\bcaveats?\b",
    # "De snelheid van Sonnet is echt." is een vertaling van "X is real".
    # Alleen als predicaat aan het eind van een zinsdeel; "is echt goed" is een
    # versterker en gewoon Nederlands.
    "is-echt-calque": r"\b(is|zijn|was|waren) (ook |wel )?(echt|reëel)\s*[.!,;:]"
                      r"|\b(is|are|was|were) (very )?real\s*[.!,;:]",
    "em-dash": r"—",
}

# --------------------------------------------------------------------------
# Laag 2 -- structuur. Hier zit het volume.
# --------------------------------------------------------------------------

STRUCTUUR = {
    "komma-en": r",\s+en\b",
    "komma-maar": r",\s+maar\b",
    "komma-dan": r",\s+dan\b",
    "komma-dus": r",\s+dus\b",
    "komma-want": r",\s+want\b",
}

# --------------------------------------------------------------------------
# Laag 3 -- frames: een skelet met gaten.
# --------------------------------------------------------------------------

FRAMES = {
    "niet-X-maar-Y": r"\bniet\b[^.!?]{3,70}?\bmaar\b",
    "geen-X-maar-Y": r"\bgeen\b[^.!?]{3,70}?\bmaar\b",
    "niet-omdat-maar": r"\bniet omdat\b[^.!?]{3,90}?\bmaar\b",
    "de-vraag-is-niet": r"\bde vraag is niet\b",
    "het-probleem-is-niet": r"\bhet (echte )?probleem (is|zit|was) niet\b",
    "het-zit-niet-in": r"\b(zit|zat) (het |hem )?niet in\b",
    "dat-is-niet-X-dat-is": r"\bdat is (niet|geen)\b[^.!?]{3,70}[.!?]\s+\b(dat|het) is\b",
    "X-is-niet-Y-het-is": r"\bis (niet|geen)\b[^.!?]{3,70}[.!?]\s+het (is|gaat)\b",
    # Een eerdere versie eiste met een lookbehind dat de drieslag een zin BEGON
    # en miste daardoor "De aanpak is sneller, beter, slimmer." Wat de vorm
    # kenmerkt is niet waar hij staat maar dat hij een zin AFSLUIT: drie losse
    # woorden, dan een punt.
    "drieslag": r"\b\w+,\s\w+,\s\w+\.",
    "niet-alleen-maar-ook": r"\bniet alleen\b[^.!?]{3,70}?\bmaar ook\b",
    # Tweede beoordeling: "Maar de calculator weegt, kiest en tekent." De
    # drieslag hierboven eist "X, Y, Z." en mist de vorm met "en" ervoor.
    "drieslag-met-en": r"\b\w+,\s+\w+\s+en\s+\w+\.",
    # Tweede beoordeling: "Niet omdat de AI het niet kan." De "maar" staat in de
    # zin erna, dus niet-omdat-maar (die beide helften in een zin eist) mist hem.
    "niet-omdat-los": r"(?:^|[.!?]\s)Niet omdat\b[^.!?]{3,80}[.!?]",
    # Tweede beoordeling: "This isn't just clean architecture." Engelse variant
    # van niet-alleen-maar-ook.
    "not-just-X": r"\b(isn'?t|aren'?t|is not|are not)\s+just\b",
}

LAGEN = {"lexicaal": LEXICAAL, "structuur": STRUCTUUR, "frames": FRAMES}
EIGEN_LAAG = "eigen"
ALLE_LAAGNAMEN = [*LAGEN, EIGEN_LAAG]

# Een opsomming van gelijkwaardige elementen telt niet mee; vier van de vier
# `, en`-treffers die de tweede beoordeling laag scoorde waren opsommingen.
# Herkenning: minstens twee komma's VOOR de ", en", zonder werkwoord-achtig
# vervolg. Bewust ruim: liever een tic missen dan een lijst beschuldigen.
# De tussendelen mogen NIET zelf met "en" beginnen. Zonder die eis excuseerde
# deze guard ook een kommaketen ("nagekeken, en het klopt, en dat is fijn, en
# dus stop ik"), en dat is precies het tegenovergestelde van wat hij moet doen.
_OPSOMMING = re.compile(
    r",(?!\s*en\b)[^,.!?]{1,60},(?!\s*en\b)[^,.!?]{1,60},\s+en\b", re.I
)


def _is_opsomming(zin: str) -> bool:
    return bool(_OPSOMMING.search(zin))


# --------------------------------------------------------------------------
# Configuratie
# --------------------------------------------------------------------------

CONFIG_NAAM = "slop-lint.json"

DEFAULTS = {
    "enabled": True,
    "include": ["*"],
    "exclude": [],
    "extensions": sorted(EXTENSIES),
    "disable": [],
    "rules": {},
    "min_words": 40,
    "max_density": None,
    "profiles": {},
}


@dataclass
class Config:
    waarden: dict
    wortel: Path
    bronnen: list[Path] = field(default_factory=list)
    meldingen: list[str] = field(default_factory=list)

    def __getitem__(self, sleutel: str):
        return self.waarden[sleutel]


def gebruikersbestand() -> Path:
    """Altijd in de home-map, ook als CLAUDE_CONFIG_DIR ergens anders heen wijst:
    zo bedient één bestand meerdere accounts."""
    return Path.home() / ".claude" / CONFIG_NAAM


def zoek_projectbestand(start: Path) -> Path | None:
    """Het dichtstbijzijnde `.claude/slop-lint.json`, omhoog vanaf `start`."""
    gebruiker = gebruikersbestand().resolve()
    huidig = start if start.is_dir() else start.parent
    huidig = huidig.resolve()
    for map_ in [huidig, *huidig.parents]:
        kandidaat = map_ / ".claude" / CONFIG_NAAM
        if kandidaat.is_file() and kandidaat != gebruiker:
            return kandidaat
    return None


def _lijst_van_tekst(waarde) -> bool:
    return isinstance(waarde, list) and all(isinstance(x, str) for x in waarde)


def _toets_regel(naam: str, spec) -> tuple[str | None, str | None, str | None]:
    """(patroon, laag, foutmelding) voor één eigen regel."""
    if isinstance(spec, str):
        patroon, laag = spec, None
    elif isinstance(spec, dict) and isinstance(spec.get("pattern"), str):
        patroon, laag = spec["pattern"], spec.get("layer")
    else:
        return None, None, "verwacht een regex of {\"pattern\": ..., \"layer\": ...}"
    if laag is not None and laag not in ALLE_LAAGNAMEN:
        return None, None, f"onbekende laag '{laag}', kies uit {', '.join(ALLE_LAAGNAMEN)}"
    try:
        re.compile(patroon)
    except re.error as fout:
        return None, None, f"regex compileert niet: {fout}"
    return patroon, laag, None


def _pas_toe(waarden: dict, nieuw: dict, bron: Path, meldingen: list[str]) -> None:
    """Zet de geldige sleutels uit `nieuw` over op `waarden`. Een foute waarde
    valt terug op wat er al stond, met een melding."""
    def fout(sleutel: str, reden: str) -> None:
        meldingen.append(f"slop-lint: {bron}: '{sleutel}' ongeldig ({reden}), genegeerd")

    for sleutel, waarde in nieuw.items():
        if sleutel not in DEFAULTS:
            meldingen.append(f"slop-lint: {bron}: onbekende sleutel '{sleutel}', genegeerd")
            continue
        if sleutel == "enabled":
            if isinstance(waarde, bool):
                waarden[sleutel] = waarde
            else:
                fout(sleutel, "verwacht true of false")
        elif sleutel in ("include", "exclude", "disable"):
            if _lijst_van_tekst(waarde):
                waarden[sleutel] = list(waarde)
            else:
                fout(sleutel, "verwacht een lijst met tekst")
        elif sleutel == "extensions":
            if _lijst_van_tekst(waarde) and all(x.startswith(".") for x in waarde):
                waarden[sleutel] = [x.lower() for x in waarde]
            else:
                fout(sleutel, "verwacht een lijst als [\".md\", \".txt\"]")
        elif sleutel == "min_words":
            if isinstance(waarde, int) and not isinstance(waarde, bool) and waarde >= 0:
                waarden[sleutel] = waarde
            else:
                fout(sleutel, "verwacht een geheel getal van 0 of meer")
        elif sleutel == "max_density":
            if waarde is None or (isinstance(waarde, (int, float))
                                  and not isinstance(waarde, bool) and waarde >= 0):
                waarden[sleutel] = waarde
            else:
                fout(sleutel, "verwacht een getal van 0 of meer, of null")
        elif sleutel == "rules":
            if not isinstance(waarde, dict):
                fout(sleutel, "verwacht een object met regelnaam als sleutel")
                continue
            samengevoegd = dict(waarden["rules"])
            for naam, spec in waarde.items():
                _, _, reden = _toets_regel(naam, spec)
                if reden:
                    fout(f"rules.{naam}", reden)
                else:
                    samengevoegd[naam] = spec
            waarden[sleutel] = samengevoegd
        elif sleutel == "profiles":
            if isinstance(waarde, dict) and all(_lijst_van_tekst(v) for v in waarde.values()):
                waarden[sleutel] = {**waarden["profiles"], **waarde}
            else:
                fout(sleutel, "verwacht een object met per naam een lijst met paden")


def _lees_json(pad: Path, meldingen: list[str]) -> dict | None:
    try:
        inhoud = json.loads(pad.read_text(encoding="utf-8"))
    except (OSError, ValueError) as fout:
        meldingen.append(f"slop-lint: {pad}: niet te lezen ({fout}), genegeerd")
        return None
    if not isinstance(inhoud, dict):
        meldingen.append(f"slop-lint: {pad}: verwacht een JSON-object, genegeerd")
        return None
    return inhoud


def laad_config(start: Path, expliciet: Path | None = None) -> Config:
    """Defaults, dan het gebruikersbestand, dan het projectbestand, dan een
    expliciet opgegeven bestand. Lijsten vervangen elkaar; `rules` en `profiles`
    worden per naam samengevoegd.

    `include`, `exclude` en `profiles` gelden ten opzichte van de projectmap: de
    map waarin `.claude/slop-lint.json` staat. Zonder projectbestand is dat de
    home-map als er een gebruikersbestand is, anders de startmap."""
    waarden = json.loads(json.dumps(DEFAULTS))
    meldingen: list[str] = []
    bronnen: list[Path] = []
    wortel = start if start.is_dir() else start.parent

    gebruiker = gebruikersbestand()
    if gebruiker.is_file():
        inhoud = _lees_json(gebruiker, meldingen)
        if inhoud is not None:
            _pas_toe(waarden, inhoud, gebruiker, meldingen)
            bronnen.append(gebruiker)
            wortel = Path.home()

    project = zoek_projectbestand(start)
    if project is not None:
        inhoud = _lees_json(project, meldingen)
        if inhoud is not None:
            _pas_toe(waarden, inhoud, project, meldingen)
            bronnen.append(project)
            wortel = project.parent.parent

    if expliciet is not None:
        inhoud = _lees_json(expliciet, meldingen)
        if inhoud is not None:
            _pas_toe(waarden, inhoud, expliciet, meldingen)
            bronnen.append(expliciet)

    return Config(waarden=waarden, wortel=wortel.resolve(), bronnen=bronnen, meldingen=meldingen)


def bouw_lagen(cfg: Config, extra_uit: list[str] | None = None) -> dict[str, dict[str, str]]:
    """De ingebouwde lagen, plus de eigen regels, min wat uit staat.

    Een eigen regel met de naam van een ingebouwde regel vervangt die, in zijn
    oorspronkelijke laag tenzij er een andere laag bij staat."""
    lagen = {naam: dict(patronen) for naam, patronen in LAGEN.items()}
    lagen[EIGEN_LAAG] = {}
    for naam, spec in cfg["rules"].items():
        patroon, laag, _ = _toets_regel(naam, spec)
        oorspronkelijk = next((k for k, v in lagen.items() if naam in v), None)
        for patronen in lagen.values():
            patronen.pop(naam, None)
        lagen[laag or oorspronkelijk or EIGEN_LAAG][naam] = patroon
    for naam in [*cfg["disable"], *(extra_uit or [])]:
        gevonden = False
        for patronen in lagen.values():
            if patronen.pop(naam, None) is not None:
                gevonden = True
        if not gevonden:
            cfg.meldingen.append(f"slop-lint: regel '{naam}' bestaat niet, kan niet uit")
    return lagen


def in_scope(pad: Path, cfg: Config) -> bool:
    """Valt dit bestand onder `include` en buiten `exclude`?"""
    try:
        rel = pad.resolve().relative_to(cfg.wortel).as_posix()
    except ValueError:
        rel = pad.resolve().as_posix()
    if not any(fnmatchcase(rel, p) for p in cfg["include"]):
        return False
    return not any(fnmatchcase(rel, p) for p in cfg["exclude"])


# --------------------------------------------------------------------------
# Tekst uit de verschillende dragers halen
# --------------------------------------------------------------------------

def _strip_markdown(raw: str) -> str:
    if raw.startswith("---"):
        deel = raw.split("---", 2)
        raw = deel[2] if len(deel) > 2 else raw
    raw = re.sub(r"```.*?```", " ", raw, flags=re.S)
    # Inline code wordt "§", geen spatie. Met een spatie werd "`A`, `B` en `C`"
    # tot ",  en" en sloeg komma-en aan op een opsomming van codenamen. Het teken
    # is geen woordteken, dus de drieslag ziet "`a`, `b`, `c`." ook niet als
    # drie woorden.
    raw = re.sub(r"`[^`]*`", "§", raw)
    raw = re.sub(r"^\s*\|.*$", " ", raw, flags=re.M)
    raw = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", raw)
    raw = re.sub(r"^#{1,6}\s*", "", raw, flags=re.M)
    raw = re.sub(r"^\s*>\s?", "", raw, flags=re.M)
    raw = re.sub(r"\*\*?|__?", "", raw)
    return re.split(r"\n##\s*(?:Image Brief|Carousel Brief)", raw)[0]


_REPLY_GRENS = re.compile(
    r"^(?:-{2,}\s*(?:Original Message|Oorspronkelijk bericht)|"
    r"(?:Op|On)\s.{0,80}\s(?:schreef|wrote)\s*:?|"
    r"(?:From|Van|Sent|Verzonden):\s)",
    re.M,
)


def _strip_email(raw: str) -> str:
    """Alleen het eigen deel van een mail. Kop, citaat en reply-keten eruit.

    Wat de ander schreef is niet jouw tekst. Zonder deze knip meet je andermans
    tics en tel je bovendien elke reply opnieuw mee.
    """
    body = raw.split("\n\n", 1)[1] if "\n\n" in raw else raw
    body = _REPLY_GRENS.split(body)[0]
    regels = [r for r in body.splitlines() if not r.lstrip().startswith(">")]
    return "\n".join(regels)


def _lees_docx(pad: Path) -> str:
    try:
        import docx  # noqa: PLC0415
    except ImportError:
        return ""
    # Breed vangen is hier een meting, geen reflex. Een run over 927 echte
    # Word-bestanden viel twee keer om op twee VERSCHILLENDE klassen: een
    # bestand dat geen zip is, en een zip met stukke XML erin. Een onleesbaar
    # Word-bestand hoort overgeslagen te worden, niet een scan af te breken.
    try:
        doc = docx.Document(str(pad))
    except Exception:
        return ""
    stukken = [p.text for p in doc.paragraphs]
    for tabel in doc.tables:
        for rij in tabel.rows:
            stukken.extend(cel.text for cel in rij.cells)
    return "\n".join(stukken)


def lees_tekst(pad: Path) -> str:
    suffix = pad.suffix.lower()
    if suffix == ".docx":
        return _lees_docx(pad)
    try:
        raw = pad.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    if suffix == ".eml":
        return _strip_email(raw)
    if suffix == ".md":
        return _strip_markdown(raw)
    return raw


# --------------------------------------------------------------------------
# Meten
# --------------------------------------------------------------------------

@dataclass
class Bevinding:
    pad: Path
    regelnr: int
    laag: str
    naam: str
    fragment: str


@dataclass
class Uitslag:
    bevindingen: list[Bevinding] = field(default_factory=list)
    bestanden: int = 0
    woorden: int = 0
    overgeslagen: int = 0
    per_bestand: dict = field(default_factory=dict)
    per_naam: dict = field(default_factory=dict)

    @property
    def dichtheid(self) -> float:
        return 1000 * len(self.bevindingen) / self.woorden if self.woorden else 0.0


def toets_bestand(pad: Path, lagen: dict[str, dict[str, str]]) -> tuple[list[Bevinding], int]:
    tekst = lees_tekst(pad)
    if not tekst.strip():
        return [], 0
    woorden = len(tekst.split())
    uit: list[Bevinding] = []

    # Regelnummers zijn alleen zinvol voor de dragers waar ze bestaan.
    regels = tekst.splitlines() if pad.suffix.lower() in {".md", ".txt", ".eml"} else []

    for laagnaam, patronen in lagen.items():
        for naam, patroon in patronen.items():
            for m in re.finditer(patroon, tekst, re.I):
                fragment = tekst[max(0, m.start() - 45):m.end() + 45].replace("\n", " ").strip()
                if NEGEER_MARKER in fragment:
                    continue
                if naam == "komma-en" and _is_opsomming(fragment):
                    continue
                regelnr = 0
                if regels:
                    vooraf = tekst[:m.start()].count("\n")
                    regelnr = vooraf + 1
                    if NEGEER_MARKER in regels[min(vooraf, len(regels) - 1)]:
                        continue
                uit.append(Bevinding(pad, regelnr, laagnaam, naam, fragment[:150]))
    return uit, woorden


def verzamel(paden: list[Path], extensies=EXTENSIES) -> list[Path]:
    extensies = {e.lower() for e in extensies}
    gevonden: list[Path] = []
    for wortel in paden:
        if wortel.is_file():
            gevonden.append(wortel)
            continue
        for p in sorted(wortel.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in extensies:
                continue
            if NEGEER_DIRS & set(p.parts):
                continue
            gevonden.append(p)
    return gevonden


def scan(bestanden: list[Path], lagen: dict[str, dict[str, str]], min_woorden: int = 40) -> Uitslag:
    res = Uitslag()
    for pad in bestanden:
        bev, woorden = toets_bestand(pad, lagen)
        if woorden < min_woorden:
            res.overgeslagen += 1
            continue
        res.bestanden += 1
        res.woorden += woorden
        res.bevindingen.extend(bev)
        if bev:
            res.per_bestand[pad] = len(bev)
        for b in bev:
            res.per_naam[b.naam] = res.per_naam.get(b.naam, 0) + 1
    return res


def _toon(pad: Path, relatief_aan: Path) -> str:
    try:
        return str(pad.resolve().relative_to(relatief_aan.resolve()))
    except ValueError:
        return str(pad)


def rapport(res: Uitslag, lagen: dict[str, dict[str, str]], *, regels: bool,
            top: int = 10, stil: bool = False, relatief_aan: Path | None = None) -> str:
    relatief_aan = relatief_aan or Path.cwd()
    uit = [
        f"Gescand: {res.bestanden} bestanden, {res.woorden:,} woorden "
        f"({res.overgeslagen} overgeslagen onder de woordgrens)",
        f"Gevonden: {len(res.bevindingen)} treffers in {len(res.per_bestand)} bestanden",
    ]
    if res.woorden:
        uit.append(f"Dichtheid: {res.dichtheid:.2f} per 1.000 woorden")

    if res.per_naam:
        uit += ["", "Per patroon:"]
        for naam, n in sorted(res.per_naam.items(), key=lambda x: -x[1]):
            laag = next((k for k, v in lagen.items() if naam in v), "?")
            uit.append(f"  {n:>6}  {laag:<10} {naam}")

    # Bij een kleine run is het aantal niet het antwoord; je wilt de regel zien.
    # Boven de drempel zou dat duizenden regels worden, dus dan de ranglijst.
    if res.bevindingen and regels and not stil:
        uit += ["", "Per treffer:"]
        for b in sorted(res.bevindingen, key=lambda x: (str(x.pad), x.regelnr)):
            pad = _toon(b.pad, relatief_aan)
            uit.append(f"  {pad}:{b.regelnr}" if b.regelnr else f"  {pad}")
            uit.append(f"      {b.naam}: ...{b.fragment}...")
    elif res.per_bestand and not stil:
        uit += ["", f"Slechtste {min(top, len(res.per_bestand))} bestanden:"]
        for pad, n in sorted(res.per_bestand.items(), key=lambda x: -x[1])[:top]:
            uit.append(f"  {n:>4}  {_toon(pad, relatief_aan)}")
    return "\n".join(uit)


def boven_de_lat(res: Uitslag, max_dichtheid: float | None) -> bool:
    """Zonder lat faalt elke treffer. Met lat faalt alleen tekst die SLECHTER is
    dan de afgesproken lat. Een poort op nul hield in de meting 49 van 60
    gepubliceerde blogs tegen, en een poort die alles tegenhoudt wordt uitgezet."""
    if max_dichtheid is None:
        return bool(res.bevindingen)
    return res.dichtheid > max_dichtheid


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paden", nargs="*", help="bestanden of mappen; leeg = profiel of de huidige map")
    ap.add_argument("--profiel", help="een profiel uit `profiles` in de config")
    ap.add_argument("--laag", action="append", choices=ALLE_LAAGNAMEN,
                    help="beperk tot een laag; meerdere keren toegestaan")
    ap.add_argument("--uit", action="append", default=[], metavar="REGEL",
                    help="zet een regel uit voor deze run; meerdere keren toegestaan")
    ap.add_argument("--config", type=Path, metavar="PAD",
                    help="een extra configbestand, bovenop project en gebruiker")
    ap.add_argument("--min-woorden", type=int, default=None, metavar="N",
                    help="sla bestanden onder N woorden over (standaard min_words uit de config, 40)")
    ap.add_argument("--top", type=int, default=10, help="hoeveel slechtste bestanden tonen")
    ap.add_argument("--regels", action=argparse.BooleanOptionalAction, default=None,
                    help="elke treffer met bestand:regel tonen (standaard aan bij 5 bestanden of minder)")
    ap.add_argument("--stil", action="store_true", help="alleen de samenvatting")
    ap.add_argument("--max-dichtheid", type=float, default=None, metavar="N",
                    help="faal pas boven N treffers per 1.000 woorden, in plaats van bij "
                         "elke treffer. Bedoeld als ratchet: zet hem op de huidige mediaan "
                         "en verlaag hem, nooit verhogen.")
    args = ap.parse_args(argv)

    cwd = Path.cwd()
    cfg = laad_config(cwd, args.config)
    lagen = bouw_lagen(cfg, args.uit)
    if args.laag:
        lagen = {k: v for k, v in lagen.items() if k in args.laag}
    for melding in cfg.meldingen:
        print(melding, file=sys.stderr)

    if args.paden:
        wortels = [Path(p) if Path(p).is_absolute() else cwd / p for p in args.paden]
    elif args.profiel:
        if args.profiel not in cfg["profiles"]:
            bekend = ", ".join(sorted(cfg["profiles"])) or "geen"
            print(f"onbekend profiel '{args.profiel}' (bekend: {bekend})", file=sys.stderr)
            return 2
        wortels = [cfg.wortel / p for p in cfg["profiles"][args.profiel]]
    else:
        wortels = [cwd]
    wortels = [w for w in wortels if w.exists()]
    if not wortels:
        print("geen bestaande paden opgegeven", file=sys.stderr)
        return 2

    min_woorden = args.min_woorden if args.min_woorden is not None else cfg["min_words"]
    res = scan(verzamel(wortels, cfg["extensions"]), lagen, min_woorden)
    toon_regels = args.regels if args.regels is not None else (res.bestanden <= 5)
    print(rapport(res, lagen, regels=toon_regels, top=args.top, stil=args.stil, relatief_aan=cwd))

    lat = args.max_dichtheid if args.max_dichtheid is not None else cfg["max_density"]
    if lat is None:
        return 1 if res.bevindingen else 0
    if boven_de_lat(res, lat):
        print(f"\nROOD: {res.dichtheid:.2f} per 1.000 woorden boven de lat van {lat:.2f}")
        return 1
    print(f"\nGROEN: {res.dichtheid:.2f} per 1.000 woorden, lat {lat:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
