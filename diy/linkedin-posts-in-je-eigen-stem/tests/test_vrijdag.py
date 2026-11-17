"""Tests voor de vrijdagregel. Draai vanuit de pluginmap: python3 -m unittest discover tests"""
from __future__ import annotations

import contextlib
import datetime as dt
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "vrijdag" / "scripts"))

import vrijdag  # noqa: E402

TOT = dt.date(2026, 11, 13)
KOP = "datum,pijler,haak,eerste_regel,vertoningen,interacties\n"


def draai(inhoud: str, *extra: str) -> tuple[int, str, str]:
    """Schrijft het logboek in een tijdelijke map, draait het script en ruimt de map daarna op."""
    uit, fout = io.StringIO(), io.StringIO()
    with tempfile.TemporaryDirectory() as map_:
        pad = Path(map_) / "logboek.csv"
        pad.write_text(inhoud, encoding="utf-8")
        with contextlib.redirect_stdout(uit), contextlib.redirect_stderr(fout):
            code = vrijdag.main([str(pad), "--tot", TOT.isoformat(), *extra])
    return code, uit.getvalue(), fout.getvalue()


def rij(datum: str, pijler: str, vertoningen: int | str, interacties: int | str) -> str:
    return f'{datum},{pijler},K1,"eerste regel",{vertoningen},{interacties}\n'


class Regels(unittest.TestCase):
    def test_schalen_houden_schrappen(self):
        inhoud = KOP
        # Klantverhalen: 4%, Tips: 2%, Nieuws: 1%. Totale mediaan: 2%.
        for d in ("2026-10-01", "2026-10-08", "2026-10-15"):
            inhoud += rij(d, "Klantverhalen", 1000, 40)
            inhoud += rij(d, "Tips", 1000, 20)
            inhoud += rij(d, "Nieuws", 1000, 10)
        code, uit, _ = draai(inhoud)
        self.assertEqual(code, 0)
        self.assertIn("| Klantverhalen | 3 | 4,0% | 2,00 x | schalen |", uit)
        self.assertIn("| Tips | 3 | 2,0% | 1,00 x | houden |", uit)
        self.assertIn("| Nieuws | 3 | 1,0% | 0,50 x | schrappen |", uit)
        self.assertIn("Jouw mediane interactiegraad: 2,0%.", uit)

    def test_grenzen_zijn_exact(self):
        inhoud = KOP
        # Basis 2%. Pijler A precies 1,25 x (2,5%), pijler B precies 0,75 x (1,5%).
        for d in ("2026-10-01", "2026-10-02", "2026-10-03"):
            inhoud += rij(d, "Basis", 1000, 20)
            inhoud += rij(d, "Basis", 1000, 20)
            inhoud += rij(d, "A", 1000, 25)
            inhoud += rij(d, "B", 1000, 15)
        _, uit, _ = draai(inhoud)
        self.assertIn("| A | 3 | 2,5% | 1,25 x | schalen |", uit)
        self.assertIn("| B | 3 | 1,5% | 0,75 x | houden |", uit)

    def test_te_weinig_posts_in_pijler(self):
        inhoud = KOP
        for d in ("2026-10-01", "2026-10-08", "2026-10-15"):
            inhoud += rij(d, "Tips", 1000, 20)
        inhoud += rij("2026-10-20", "Nieuw", 1000, 90)
        _, uit, _ = draai(inhoud)
        self.assertIn("| Nieuw | 1 | 9,0% |", uit)
        self.assertIn("| te weinig data |", uit)

    def test_te_weinig_posts_in_totaal(self):
        inhoud = KOP + rij("2026-10-01", "Tips", 1000, 20) + rij("2026-10-02", "Tips", 1000, 30)
        code, uit, _ = draai(inhoud)
        self.assertEqual(code, 0)
        self.assertIn("Te weinig data voor een advies", uit)
        self.assertNotIn("| Pijler |", uit)

    def test_geen_interacties_geeft_geen_advies(self):
        inhoud = KOP
        for d in ("2026-10-01", "2026-10-02", "2026-10-03"):
            inhoud += rij(d, "Tips", 1000, 0)
        _, uit, _ = draai(inhoud)
        self.assertIn("Geen advies: in dit venster is geen enkele interactie gemeten.", uit)


class Invoer(unittest.TestCase):
    def test_puntkomma_en_nederlandse_getallen(self):
        inhoud = (
            "datum;pijler;haak;eerste_regel;vertoningen;interacties\n"
            "01-10-2026;Tips;K1;eerste;1.000;20\n"
            "08-10-2026;Tips;K2;tweede;2.000;40\n"
            "15-10-2026;Tips;K3;derde;1 000;20\n"
        )
        code, uit, _ = draai(inhoud)
        self.assertEqual(code, 0)
        self.assertIn("| Tips | 3 | 2,0% | 1,00 x | houden |", uit)

    def test_regels_zonder_cijfers_worden_gemeld(self):
        inhoud = KOP
        for d in ("2026-10-01", "2026-10-08", "2026-10-15"):
            inhoud += rij(d, "Tips", 1000, 20)
        inhoud += rij("2026-10-20", "Tips", "", "")
        inhoud += rij("2026-10-21", "Tips", 0, 0)
        _, uit, _ = draai(inhoud)
        self.assertIn("Posts met cijfers: 3.", uit)
        self.assertIn("leeg of geen heel getal (schrijf 1.234, niet 1,2k): regel 5\n", uit)
        self.assertIn("0 vertoningen, daar valt geen percentage uit te rekenen: regel 6", uit)

    def test_alleen_hele_getallen_tellen(self):
        for tekst in ("1234", "1.234", "1,234", "1 234", "1\u00a0234", "1\u202f234", " 1.234.567 "):
            self.assertEqual(vrijdag.getal(tekst), int("".join(c for c in tekst if c.isdigit())), tekst)
        for tekst in ("-10", "1,2k", "1,2K", "12,5", "1.23", "1.2345", "", "ca. 100"):
            self.assertIsNone(vrijdag.getal(tekst), tekst)

    def test_een_afgekort_getal_wordt_gemeld_en_niet_geteld(self):
        inhoud = KOP
        for d in ("2026-10-01", "2026-10-08", "2026-10-15"):
            inhoud += rij(d, "Tips", 1000, 20)
        inhoud += rij("2026-10-20", "Tips", '"1,2k"', 30)
        _, uit, _ = draai(inhoud)
        self.assertIn("Posts met cijfers: 3.", uit)
        self.assertIn("regel 5", uit)

    def test_jonge_posts_en_oude_posts_tellen_niet(self):
        inhoud = KOP
        for d in ("2026-10-01", "2026-10-08", "2026-10-15"):
            inhoud += rij(d, "Tips", 1000, 20)
        inhoud += rij("2026-11-10", "Tips", 1000, 90)  # jonger dan 7 dagen
        inhoud += rij("2026-08-01", "Tips", 1000, 90)  # buiten 8 weken
        _, uit, _ = draai(inhoud)
        self.assertIn("Posts met cijfers: 3.", uit)
        self.assertIn("1 post(s) jonger dan 7 dagen", uit)

    def test_onleesbare_datum(self):
        inhoud = KOP + rij("gisteren", "Tips", 1000, 20)
        _, uit, _ = draai(inhoud)
        self.assertIn("datum onleesbaar, gebruik JJJJ-MM-DD: regel 2", uit)

    def test_kolom_ontbreekt(self):
        code, _, fout = draai("datum,pijler,vertoningen\n2026-10-01,Tips,1000\n")
        self.assertEqual(code, 2)
        self.assertIn("kolom ontbreekt", fout)
        self.assertIn("interacties", fout)

    def test_komma_in_eerste_regel(self):
        inhoud = KOP
        for d in ("2026-10-01", "2026-10-08", "2026-10-15"):
            inhoud += f'{d},Tips,K1,"Ik dacht, dat klopt niet",1000,40\n'
        for d in ("2026-10-02", "2026-10-09", "2026-10-16"):
            inhoud += rij(d, "Nieuws", 1000, 10)
        _, uit, _ = draai(inhoud)
        self.assertIn('Tips, 2026-10-01: "Ik dacht, dat klopt niet" (4,0%)', uit)

    def test_bestand_bestaat_niet(self):
        uit, fout = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(uit), contextlib.redirect_stderr(fout):
            code = vrijdag.main(["/bestaat/niet/logboek.csv"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
