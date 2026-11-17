#!/usr/bin/env python3
"""Vrijdagregel voor de LinkedIn-redactie.

Leest linkedin/logboek.csv en zegt per pijler: schalen, houden, schrappen of
te weinig data. Vaste regels, geen AI. Alleen de standaardbibliotheek.

Gebruik:
    python3 vrijdag.py linkedin/logboek.csv
    python3 vrijdag.py linkedin/logboek.csv --tot 2026-11-13 --weken 8 --minimum 3 --rijp 7

Exitcodes: 0 = rapport geschreven, 2 = bestand of kolommen niet bruikbaar.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import re
import statistics
import sys
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

# Breuken in plaats van kommagetallen: dan valt 25/1000 gedeeld door 20/1000 precies op 1,25.
SCHALEN = Fraction(5, 4)
SCHRAPPEN = Fraction(3, 4)
VERPLICHT = ("datum", "pijler", "vertoningen", "interacties")
# Cijfers, of groepjes van drie na een punt, komma of spatie. \s telt ook de vaste spatie die een export soms gebruikt.
HEEL_GETAL = re.compile(r"\d+|\d{1,3}(?:[.,\s]\d{3})+")
GEEN_PIJLER = "geen pijler"


@dataclass
class Post:
    regel: int
    datum: dt.date
    pijler: str
    eerste_regel: str
    vertoningen: int
    interacties: int

    @property
    def graad(self) -> Fraction:
        return Fraction(self.interacties, self.vertoningen)


@dataclass
class Logboek:
    posts: list[Post] = field(default_factory=list)
    zonder_cijfers: list[int] = field(default_factory=list)
    nul_vertoningen: list[int] = field(default_factory=list)
    onleesbaar: list[int] = field(default_factory=list)


@dataclass
class Pijler:
    naam: str
    posts: list[Post]
    mediaan: Fraction
    verhouding: Fraction | None
    advies: str


@dataclass
class Uitslag:
    tot: dt.date
    van: dt.date
    weken: int
    minimum: int
    rijp: int
    mediaan: Fraction | None
    pijlers: list[Pijler]
    meegeteld: int
    te_jong: int
    logboek: Logboek


def getal(tekst: str) -> int | None:
    """Een heel getal, met of zonder scheiding per duizend: 1234, 1.234, 1,234 en 1 234 worden 1234.

    Al het andere geeft None, ook -10, 1,2k en 12,5. Het rapport noemt die regel dan, zodat de
    gebruiker hem verbetert. Een stille gok zou het advies verschuiven.
    """
    schoon = tekst.strip()
    if not HEEL_GETAL.fullmatch(schoon):
        return None
    return int(re.sub(r"\D", "", schoon))


def datum(tekst: str) -> dt.date | None:
    for vorm in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(tekst.strip(), vorm).date()
        except ValueError:
            continue
    return None


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
        wanneer = datum(waarden.get("datum", ""))
        if wanneer is None:
            logboek.onleesbaar.append(nr)
            continue
        vertoningen = getal(waarden.get("vertoningen", ""))
        interacties = getal(waarden.get("interacties", ""))
        if vertoningen is None or interacties is None:
            logboek.zonder_cijfers.append(nr)
            continue
        if vertoningen == 0:
            logboek.nul_vertoningen.append(nr)
            continue
        logboek.posts.append(
            Post(
                regel=nr,
                datum=wanneer,
                pijler=waarden.get("pijler") or GEEN_PIJLER,
                eerste_regel=waarden.get("eerste_regel", ""),
                vertoningen=vertoningen,
                interacties=interacties,
            )
        )
    return logboek


def advies(aantal: int, verhouding: Fraction | None, minimum: int) -> str:
    if aantal < minimum or verhouding is None:
        return "te weinig data"
    if verhouding >= SCHALEN:
        return "schalen"
    if verhouding < SCHRAPPEN:
        return "schrappen"
    return "houden"


def beoordeel(logboek: Logboek, tot: dt.date, weken: int = 8, minimum: int = 3, rijp: int = 7) -> Uitslag:
    van = tot - dt.timedelta(weeks=weken)
    grens = tot - dt.timedelta(days=rijp)
    in_venster = [p for p in logboek.posts if van < p.datum <= tot]
    meegeteld = [p for p in in_venster if p.datum <= grens]
    te_jong = len(in_venster) - len(meegeteld)

    mediaan = statistics.median(p.graad for p in meegeteld) if meegeteld else None
    genoeg = mediaan is not None and mediaan > 0 and len(meegeteld) >= minimum

    per_pijler: dict[str, list[Post]] = {}
    for post in meegeteld:
        per_pijler.setdefault(post.pijler, []).append(post)

    pijlers = []
    for naam in sorted(per_pijler, key=str.lower):
        posts = per_pijler[naam]
        eigen = statistics.median(p.graad for p in posts)
        verhouding = eigen / mediaan if genoeg else None
        pijlers.append(Pijler(naam, posts, eigen, verhouding, advies(len(posts), verhouding, minimum)))

    return Uitslag(tot, van, weken, minimum, rijp, mediaan, pijlers, len(meegeteld), te_jong, logboek)


def procent(waarde: Fraction) -> str:
    return f"{float(waarde) * 100:.1f}%".replace(".", ",")


def keer(waarde: Fraction) -> str:
    return f"{float(waarde):.2f} x".replace(".", ",")


def rapport(u: Uitslag) -> str:
    uit = [f"# Vrijdag: {u.tot.isoformat()}", ""]
    uit.append(
        f"Venster: {(u.van + dt.timedelta(days=1)).isoformat()} tot en met {u.tot.isoformat()} "
        f"({u.weken} weken). Posts jonger dan {u.rijp} dagen tellen niet mee: hun cijfers lopen nog op."
    )
    if u.mediaan is None:
        uit.append("Posts met cijfers in dit venster: 0.")
    else:
        uit.append(f"Posts met cijfers: {u.meegeteld}. Jouw mediane interactiegraad: {procent(u.mediaan)}.")
    uit.append("")

    if u.meegeteld < u.minimum:
        uit.append(f"Te weinig data voor een advies: er zijn minder dan {u.minimum} posts met cijfers.")
    elif not u.mediaan:
        uit.append("Geen advies: in dit venster is geen enkele interactie gemeten.")
    else:
        uit.append("| Pijler | Posts | Mediane interactiegraad | Ten opzichte van jouw mediaan | Advies |")
        uit.append("|---|---|---|---|---|")
        for p in u.pijlers:
            ten_opzichte = keer(p.verhouding) if p.verhouding is not None else "-"
            uit.append(f"| {p.naam} | {len(p.posts)} | {procent(p.mediaan)} | {ten_opzichte} | {p.advies} |")
        beste = [
            (p.naam, max(p.posts, key=lambda post: post.graad)) for p in u.pijlers if p.advies == "schalen"
        ]
        if beste:
            uit += ["", "Sterkste post per pijler om op te schalen:"]
            for naam, post in beste:
                regel = f': "{post.eerste_regel}"' if post.eerste_regel else ""
                uit.append(f"- {naam}, {post.datum.isoformat()}{regel} ({procent(post.graad)})")

    niet = []
    if u.te_jong:
        niet.append(f"- {u.te_jong} post(s) jonger dan {u.rijp} dagen")
    if u.logboek.zonder_cijfers:
        regels = ", ".join(str(n) for n in u.logboek.zonder_cijfers)
        niet.append(f"- vertoningen of interacties leeg of geen heel getal (schrijf 1.234, niet 1,2k): regel {regels}")
    if u.logboek.nul_vertoningen:
        regels = ", ".join(str(n) for n in u.logboek.nul_vertoningen)
        niet.append(f"- 0 vertoningen, daar valt geen percentage uit te rekenen: regel {regels}")
    if u.logboek.onleesbaar:
        regels = ", ".join(str(n) for n in u.logboek.onleesbaar)
        niet.append(f"- datum onleesbaar, gebruik JJJJ-MM-DD: regel {regels}")
    if niet:
        uit += ["", "Niet meegeteld:"] + niet

    uit += [
        "",
        "De regel: interactiegraad = interacties / vertoningen. Per pijler de mediaan, vergeleken met "
        f"jouw mediaan over alle posts. Schalen vanaf {keer(SCHALEN)}, schrappen onder {keer(SCHRAPPEN)}, "
        f"daartussen houden. Minder dan {u.minimum} posts in een pijler: te weinig data.",
    ]
    return "\n".join(uit) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vrijdagregel: schalen, houden of schrappen per pijler.")
    parser.add_argument("logboek", type=Path, help="pad naar logboek.csv")
    parser.add_argument("--tot", help="laatste dag van het venster, JJJJ-MM-DD (standaard vandaag)")
    parser.add_argument("--weken", type=int, default=8, help="lengte van het venster in weken (standaard 8)")
    parser.add_argument("--minimum", type=int, default=3, help="minimaal aantal posts voor een advies (standaard 3)")
    parser.add_argument("--rijp", type=int, default=7, help="posts jonger dan dit aantal dagen tellen niet mee (standaard 7)")
    args = parser.parse_args(argv)

    tot = dt.date.today()
    if args.tot:
        tot = datum(args.tot)
        if tot is None:
            print(f"--tot is geen datum: {args.tot}", file=sys.stderr)
            return 2
    if not args.logboek.exists():
        print(f"bestand niet gevonden: {args.logboek}", file=sys.stderr)
        return 2
    try:
        logboek = lees(args.logboek)
    except (ValueError, UnicodeDecodeError, csv.Error) as fout:
        print(fout, file=sys.stderr)
        return 2
    print(rapport(beoordeel(logboek, tot, args.weken, args.minimum, args.rijp)), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
