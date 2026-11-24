#!/usr/bin/env python3
"""Trechterregel voor LinkedIn: waar lekt het tussen een reactie en een klant?

Leest linkedin/trechter.csv met per week vijf tellingen en zegt welke stap het
knelpunt is. Vaste regels, geen AI. Alleen de standaardbibliotheek.

Gebruik:
    python3 trechter.py linkedin/trechter.csv
    python3 trechter.py linkedin/trechter.csv --tot 2026-11-27 --weken 4

Exitcodes: 0 = rapport geschreven, 2 = bestand, kolommen of opties niet bruikbaar.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import re
import sys
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

TELLINGEN = ("reageerders", "uit_doelgroep", "gesprekken", "afspraken", "klanten")
VERPLICHT = ("week",) + TELLINGEN
# Cijfers, of groepjes van drie na een punt, komma of spatie. Zelfde regel als de vrijdagregel.
HEEL_GETAL = re.compile(r"\d+|\d{1,3}(?:[.,\s]\d{3})+")
ISO_WEEK = re.compile(r"(\d{4})-?W(\d{1,2})", re.I)

ACTIES = {
    "zichtbaarheid": (
        "Te weinig reacties om de rest te beoordelen. Werk eerst aan zichtbaarheid: "
        "post vaker en reageer inhoudelijk onder posts van mensen uit je doelgroep."
    ),
    "doelgroep": (
        "De meeste reacties komen van mensen die niet bij je kopen. Kijk eerst in de statistieken van je posts "
        "wie er meeleest: functie, branche en bedrijfsgrootte. Lezen je kopers mee zonder te reageren? Dan liggen "
        "je onderwerpen goed en zit het in de drempel om te reageren. Lezen ze niet mee? Schrijf dan over de "
        "problemen van je klanten, in hun eigen woorden. Stuur intussen iedereen uit je doelgroep die wel "
        "reageerde één bericht."
    ),
    "opvolging": (
        "Mensen uit je doelgroep reageren, maar er volgt zelden een gesprek. Werk aan opvolging: "
        "stuur iedereen uit je doelgroep die inhoudelijk reageerde één persoonlijk bericht."
    ),
    "afspraak": (
        "Gesprekken leiden zelden tot een afspraak. Werk aan de volgende stap: "
        "bied in het gesprek één kleine, concrete stap aan."
    ),
    "klant": (
        "Afspraken leiden zelden tot een opdracht. Een opdracht volgt vaak weken na de afspraak: staan er nog "
        "voorstellen uit, wacht dan met dit oordeel tot ze beslist zijn. Zijn ze beslist? Dan ligt het na "
        "LinkedIn: kijk naar je aanbod en je verkoopgesprek."
    ),
}


@dataclass(frozen=True)
class Grenzen:
    reageerders: int = 10
    doelgroep: Fraction = Fraction(1, 2)
    opvolging: Fraction = Fraction(1, 5)
    afspraak: Fraction = Fraction(1, 4)
    klant: Fraction = Fraction(1, 5)
    minimum: int = 5
    # Een opdracht volgt vaak weken na de afspraak. Daarom telt de stap klant over een langer venster.
    klant_weken: int = 12


@dataclass
class Week:
    regel: int
    maandag: dt.date
    tellingen: dict[str, int]


@dataclass
class Logboek:
    weken: dict[dt.date, Week] = field(default_factory=dict)
    dubbel: list[tuple[str, int]] = field(default_factory=list)
    onleesbaar: list[int] = field(default_factory=list)
    zonder_cijfers: list[int] = field(default_factory=list)
    onlogisch: list[int] = field(default_factory=list)


@dataclass
class Stap:
    naam: str
    telling: int
    verhouding: Fraction | None
    grens: str
    uitkomst: str


@dataclass
class Uitslag:
    van: dt.date | None
    tot: dt.date | None
    weken: int
    klant_weken: int
    ontbrekend: list[dt.date]
    oud: bool
    stappen: list[Stap]
    knelpunt: str | None
    reden: str
    logboek: Logboek


def getal(tekst: str) -> int | None:
    """Een heel getal, met of zonder scheiding per duizend. Al het andere geeft None."""
    schoon = tekst.strip()
    if not HEEL_GETAL.fullmatch(schoon):
        return None
    return int(re.sub(r"\D", "", schoon))


def maandag(tekst: str) -> dt.date | None:
    """De maandag van de week: uit 2026-W47, 2026W47 of een datum in die week."""
    schoon = tekst.strip()
    iso = ISO_WEEK.fullmatch(schoon)
    if iso:
        try:
            return dt.date.fromisocalendar(int(iso.group(1)), int(iso.group(2)), 1)
        except ValueError:
            return None
    for vorm in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            dag = dt.datetime.strptime(schoon, vorm).date()
        except ValueError:
            continue
        return dag - dt.timedelta(days=dag.weekday())
    return None


def weeknaam(dag: dt.date) -> str:
    jaar, week, _ = dag.isocalendar()
    return f"{jaar}-W{week:02d}"


def lees(pad: Path) -> Logboek:
    tekst = pad.read_text(encoding="utf-8-sig")
    regels = tekst.splitlines()
    if not regels:
        raise ValueError(f"{pad} is leeg")
    kopregel = regels[0]
    scheiding = ";" if kopregel.count(";") > kopregel.count(",") else ","
    lezer = csv.DictReader(io.StringIO(tekst), delimiter=scheiding)
    kop = [(k or "").strip().lower() for k in (lezer.fieldnames or [])]
    ontbreekt = [k for k in VERPLICHT if k not in kop]
    if ontbreekt:
        raise ValueError(f"kolom ontbreekt in {pad}: {', '.join(ontbreekt)}")

    logboek = Logboek()
    for rij in lezer:
        nr = lezer.line_num
        waarden = {(k or "").strip().lower(): (v or "").strip() for k, v in rij.items() if k}
        if not any(waarden.values()):
            continue
        week = maandag(waarden.get("week", ""))
        if week is None:
            logboek.onleesbaar.append(nr)
            continue
        tellingen = {k: getal(waarden.get(k, "")) for k in TELLINGEN}
        if any(v is None for v in tellingen.values()):
            logboek.zonder_cijfers.append(nr)
            continue
        if tellingen["uit_doelgroep"] > tellingen["reageerders"]:
            logboek.onlogisch.append(nr)
            continue
        if week in logboek.weken:
            logboek.dubbel.append((weeknaam(week), nr))
        logboek.weken[week] = Week(nr, week, tellingen)
    return logboek


def procent(waarde: Fraction) -> str:
    """Afgerond zoals op school: 12,5% wordt 13%. round() zou naar het even getal afronden."""
    return f"{int(waarde * 100 + Fraction(1, 2))}%"


def beoordeel(logboek: Logboek, tot: dt.date, weken: int = 4, grenzen: Grenzen = Grenzen()) -> Uitslag:
    deze_week = tot - dt.timedelta(days=tot.weekday())
    klant_weken = max(weken, grenzen.klant_weken)
    gelogd = sorted(w for w in logboek.weken if w <= deze_week)
    if not gelogd:
        return Uitslag(None, None, weken, klant_weken, [], False, [], None, "Er staat nog geen week met cijfers in het logboek.", logboek)

    laatste = gelogd[-1]

    def optellen(aantal: int) -> dict[str, int]:
        weken_terug = [laatste - dt.timedelta(weeks=i) for i in range(aantal)]
        return {n: sum(logboek.weken[w].tellingen[n] for w in weken_terug if w in logboek.weken) for n in TELLINGEN}

    venster = [laatste - dt.timedelta(weeks=i) for i in reversed(range(weken))]
    ontbrekend = [w for w in venster if w not in logboek.weken]
    oud = (deze_week - laatste).days > 14
    som = optellen(weken)
    r, d, g, a = som["reageerders"], som["uit_doelgroep"], som["gesprekken"], som["afspraken"]
    lang = optellen(klant_weken)
    a_lang, k_lang = lang["afspraken"], lang["klanten"]
    klant_naam = f"Klanten ({klant_weken} weken)"

    stappen: list[Stap] = []
    knelpunt: str | None = None
    reden = ""

    def rest() -> None:
        namen = [("Uit je doelgroep", d), ("Gesprekken", g), ("Afspraken", a), (klant_naam, k_lang)]
        for naam, telling in namen:
            stappen.append(Stap(naam, telling, None, "", "niet beoordeeld"))

    if r < grenzen.reageerders:
        stappen.append(Stap("Reageerders", r, None, f"minimaal {grenzen.reageerders}", "KNELPUNT"))
        rest()
        knelpunt = "zichtbaarheid"
        reden = f"{r} reageerders in {weken} weken, minder dan {grenzen.reageerders}."
        return Uitslag(venster[0], laatste, weken, klant_weken, ontbrekend, oud, stappen, knelpunt, reden, logboek)
    stappen.append(Stap("Reageerders", r, None, f"minimaal {grenzen.reageerders}", "loopt"))

    # (naam, telling, noemer, grens, knelpuntnaam, omschrijving van de noemer)
    keten = [
        ("Uit je doelgroep", d, r, grenzen.doelgroep, "doelgroep", "reageerders"),
        ("Gesprekken", g, d, grenzen.opvolging, "opvolging", "reageerders uit je doelgroep"),
        ("Afspraken", a, g, grenzen.afspraak, "afspraak", "gesprekken"),
        (klant_naam, k_lang, a_lang, grenzen.klant, "klant", f"afspraken in {klant_weken} weken"),
    ]
    for naam, telling, noemer, grens, knelnaam, noemernaam in keten:
        if knelpunt or reden:
            stappen.append(Stap(naam, telling, None, procent(grens), "niet beoordeeld"))
            continue
        if noemer < grenzen.minimum:
            stappen.append(Stap(naam, telling, None, procent(grens), "te weinig data"))
            reden = f"{noemer} {noemernaam}, minder dan {grenzen.minimum}. Deze stap en de stappen eronder zijn nog niet te beoordelen."
            continue
        verhouding = Fraction(telling, noemer)
        if verhouding < grens:
            stappen.append(Stap(naam, telling, verhouding, procent(grens), "KNELPUNT"))
            knelpunt = knelnaam
            reden = f"{telling} van {noemer} {noemernaam} is {procent(verhouding)}, minder dan {procent(grens)}."
        else:
            stappen.append(Stap(naam, telling, verhouding, procent(grens), "loopt"))

    if not knelpunt and not reden:
        reden = "Elke stap haalt zijn grens."
    return Uitslag(venster[0], laatste, weken, klant_weken, ontbrekend, oud, stappen, knelpunt, reden, logboek)


def rapport(u: Uitslag, grenzen: Grenzen = Grenzen()) -> str:
    if u.tot is None:
        return f"# Trechter\n\n{u.reden}\n"
    uit = [f"# Trechter: {weeknaam(u.van)} tot en met {weeknaam(u.tot)}", ""]
    uit.append(
        f"Opgeteld over {u.weken} weken. Een percentage over één week is bij deze aantallen ruis. "
        f"Klanten tel ik over {u.klant_weken} weken, tegen de afspraken uit diezelfde weken: "
        "een opdracht volgt vaak weken na de afspraak."
    )
    if u.ontbrekend:
        uit.append(
            f"Niet ingevuld: {', '.join(weeknaam(w) for w in u.ontbrekend)}. "
            "Het rapport telt alleen de weken die er wel staan. Vul ze in als je de cijfers nog hebt."
        )
    if u.oud:
        uit.append(f"Let op: je laatste ingevulde week is {weeknaam(u.tot)}. Vul de weken daarna eerst in.")
    uit += ["", "| Stap | Telling | Van de stap erboven | Grens | Uitkomst |", "|---|---|---|---|---|"]
    for s in u.stappen:
        verhouding = procent(s.verhouding) if s.verhouding is not None else "-"
        uit.append(f"| {s.naam} | {s.telling} | {verhouding} | {s.grens or '-'} | {s.uitkomst} |")
    uit.append("")
    if u.knelpunt:
        uit.append(f"**Knelpunt: {u.knelpunt}.** {u.reden}")
        uit.append("")
        uit.append(ACTIES[u.knelpunt])
    elif all(s.uitkomst == "loopt" for s in u.stappen):
        uit.append(f"**Geen knelpunt.** {u.reden} Houd dit tempo vast en tel volgende week opnieuw.")
    else:
        uit.append(f"**Nog geen knelpunt te zien.** {u.reden} Tel door; met meer weken wordt het zichtbaar.")

    niet = []
    lb = u.logboek
    if lb.dubbel:
        niet.append("- week staat er twee keer in, de laatste regel telt: " + ", ".join(f"{w} (regel {n})" for w, n in lb.dubbel))
    if lb.zonder_cijfers:
        niet.append("- een telling leeg of geen heel getal: regel " + ", ".join(str(n) for n in lb.zonder_cijfers))
    if lb.onlogisch:
        niet.append("- meer uit je doelgroep dan reageerders: regel " + ", ".join(str(n) for n in lb.onlogisch))
    if lb.onleesbaar:
        niet.append("- week onleesbaar, gebruik 2026-W47 of een datum als 2026-11-16: regel " + ", ".join(str(n) for n in lb.onleesbaar))
    if niet:
        uit += ["", "Niet meegeteld:"] + niet

    uit += [
        "",
        f"De regel: tel {u.weken} weken op en loop de stappen van boven naar beneden. De eerste stap onder zijn grens is "
        f"het knelpunt; de stappen eronder worden niet beoordeeld. Minder dan {grenzen.reageerders} reageerders is "
        f"knelpunt zichtbaarheid. Daaronder telt een stap pas mee bij minimaal {grenzen.minimum} in de stap erboven. "
        f"De stap klant telt over {u.klant_weken} weken. Eén knelpunt tegelijk houdt het werk klein; een lagere stap "
        "meet pas iets als er genoeg doorkomt. De grenzen zijn startwaarden, geen benchmark.",
    ]
    return "\n".join(uit) + "\n"


def breuk(tekst: str) -> Fraction:
    """Een grens als 1/5, 0,2, 0.2 of 20%."""
    schoon = tekst.strip().replace(",", ".")
    if schoon.endswith("%"):
        waarde = Fraction(schoon[:-1]) / 100
    else:
        waarde = Fraction(schoon)
    if not 0 < waarde <= 1:
        raise argparse.ArgumentTypeError(f"grens moet tussen 0 en 1 liggen: {tekst}")
    return waarde


def positief(tekst: str) -> int:
    waarde = int(tekst)
    if waarde < 1:
        raise argparse.ArgumentTypeError(f"moet 1 of meer zijn: {tekst}")
    return waarde


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Trechterregel: welke stap tussen reactie en klant lekt?")
    parser.add_argument("logboek", type=Path, help="pad naar trechter.csv")
    parser.add_argument("--tot", help="een dag in de laatste week die meetelt, JJJJ-MM-DD (standaard vandaag)")
    parser.add_argument("--weken", type=positief, default=4, help="hoeveel weken optellen (standaard 4)")
    parser.add_argument("--reageerders", type=positief, default=10, help="minimum reageerders (standaard 10)")
    parser.add_argument("--doelgroep", type=breuk, default=Fraction(1, 2), help="grens doelgroep (standaard 1/2)")
    parser.add_argument("--opvolging", type=breuk, default=Fraction(1, 5), help="grens gesprekken (standaard 1/5)")
    parser.add_argument("--afspraak", type=breuk, default=Fraction(1, 4), help="grens afspraken (standaard 1/4)")
    parser.add_argument("--klant", type=breuk, default=Fraction(1, 5), help="grens klanten (standaard 1/5)")
    parser.add_argument("--minimum", type=positief, default=5, help="minimum in de stap erboven (standaard 5)")
    parser.add_argument("--klant-weken", type=positief, default=12, help="venster voor de stap klant (standaard 12)")
    args = parser.parse_args(argv)

    tot = dt.date.today()
    if args.tot:
        try:
            tot = dt.datetime.strptime(args.tot, "%Y-%m-%d").date()
        except ValueError:
            print(f"--tot is geen datum als JJJJ-MM-DD: {args.tot}", file=sys.stderr)
            return 2
    if not args.logboek.exists():
        print(f"bestand niet gevonden: {args.logboek}", file=sys.stderr)
        return 2
    grenzen = Grenzen(
        args.reageerders, args.doelgroep, args.opvolging, args.afspraak, args.klant, args.minimum, args.klant_weken
    )
    try:
        logboek = lees(args.logboek)
    except (ValueError, UnicodeDecodeError, csv.Error) as fout:
        print(fout, file=sys.stderr)
        return 2
    print(rapport(beoordeel(logboek, tot, args.weken, grenzen), grenzen), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
