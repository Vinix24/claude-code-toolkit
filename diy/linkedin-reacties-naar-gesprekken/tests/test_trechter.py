"""Tests voor de trechterregel. Draai vanuit deze map: python3 -m unittest discover tests"""
from __future__ import annotations

import datetime as dt
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "trechter" / "scripts"))

import trechter  # noqa: E402

KOP = "week,reageerders,uit_doelgroep,gesprekken,afspraken,klanten\n"
TOT = dt.date(2026, 11, 27)  # vrijdag in week 2026-W48


def logboek(regels: str, kop: str = KOP) -> trechter.Logboek:
    with tempfile.TemporaryDirectory() as map_:
        pad = Path(map_) / "trechter.csv"
        pad.write_text(kop + regels, encoding="utf-8")
        return trechter.lees(pad)


def uitslag(regels: str, **opties) -> trechter.Uitslag:
    return trechter.beoordeel(logboek(regels), TOT, **opties)


def uitkomsten(u: trechter.Uitslag) -> list[str]:
    return [s.uitkomst for s in u.stappen]


class Knelpunten(unittest.TestCase):
    def test_zichtbaarheid_bij_te_weinig_reageerders(self):
        u = uitslag("2026-W45,2,1,0,0,0\n2026-W46,3,2,1,0,0\n2026-W47,2,2,0,0,0\n2026-W48,2,1,0,0,0\n")
        self.assertEqual(u.knelpunt, "zichtbaarheid")
        self.assertEqual(uitkomsten(u), ["KNELPUNT"] + ["niet beoordeeld"] * 4)

    def test_doelgroep_onder_de_helft(self):
        u = uitslag("2026-W45,6,2,1,0,0\n2026-W46,6,2,1,1,0\n2026-W47,6,3,1,0,0\n2026-W48,6,2,0,0,0\n")
        self.assertEqual(u.knelpunt, "doelgroep")
        self.assertEqual(uitkomsten(u)[:2], ["loopt", "KNELPUNT"])

    def test_precies_de_helft_haalt_de_grens(self):
        u = uitslag("2026-W48,10,5,5,5,5\n")
        self.assertNotEqual(u.knelpunt, "doelgroep")
        self.assertEqual(u.stappen[1].verhouding, Fraction(1, 2))

    def test_opvolging(self):
        u = uitslag("2026-W47,10,8,1,1,0\n2026-W48,10,8,1,0,0\n")
        self.assertEqual(u.knelpunt, "opvolging")
        self.assertIn("2 van 16", u.reden)

    def test_afspraak(self):
        u = uitslag("2026-W47,10,8,4,0,0\n2026-W48,10,8,4,1,0\n")
        self.assertEqual(u.knelpunt, "afspraak")

    def test_klant(self):
        u = uitslag("2026-W47,20,15,8,3,0\n2026-W48,20,15,8,3,0\n")
        self.assertEqual(u.knelpunt, "klant")

    def test_geen_knelpunt(self):
        u = uitslag("2026-W47,20,15,8,3,1\n2026-W48,20,15,8,3,1\n")
        self.assertIsNone(u.knelpunt)
        self.assertEqual(uitkomsten(u), ["loopt"] * 5)
        self.assertIn("Geen knelpunt", trechter.rapport(u))


class KlantVenster(unittest.TestCase):
    # Afspraken in week 39, de opdrachten daaruit getekend in week 41. In de laatste vier weken
    # staan 8 afspraken en 1 klant. Over twaalf weken zijn het 10 afspraken en 3 klanten.
    REGELS = (
        "2026-W39,10,8,4,2,0\n2026-W41,10,8,4,0,2\n"
        "2026-W45,10,8,3,2,0\n2026-W46,10,8,3,2,0\n2026-W47,10,8,3,2,1\n2026-W48,10,8,3,2,0\n"
    )

    def test_klant_telt_over_twaalf_weken(self):
        u = uitslag(self.REGELS)
        self.assertIsNone(u.knelpunt)
        self.assertEqual(u.stappen[-1].naam, "Klanten (12 weken)")
        self.assertEqual(u.stappen[-1].verhouding, Fraction(3, 10))

    def test_over_vier_weken_zou_het_een_knelpunt_zijn(self):
        u = uitslag(self.REGELS, grenzen=trechter.Grenzen(klant_weken=4))
        self.assertEqual(u.knelpunt, "klant")
        self.assertIn("1 van 8", u.reden)

    def test_actie_wacht_op_uitstaande_voorstellen(self):
        self.assertIn("voorstellen uit", trechter.ACTIES["klant"])


class TeWeinigData(unittest.TestCase):
    def test_minimum_geldt_ook_voor_de_doelgroepstap(self):
        u = uitslag("2026-W48,4,1,0,0,0\n", grenzen=trechter.Grenzen(reageerders=3))
        self.assertIsNone(u.knelpunt)
        self.assertEqual(uitkomsten(u)[:2], ["loopt", "te weinig data"])

    def test_te_weinig_gesprekken_stopt_de_beoordeling(self):
        # 3 gesprekken uit 12 doelgroep haalt 1 op 5, maar 3 gesprekken is te weinig voor de afspraakstap.
        u = uitslag("2026-W47,8,6,2,0,0\n2026-W48,8,6,1,0,0\n")
        self.assertIsNone(u.knelpunt)
        self.assertEqual(uitkomsten(u), ["loopt", "loopt", "loopt", "te weinig data", "niet beoordeeld"])
        self.assertIn("Nog geen knelpunt", trechter.rapport(u))

    def test_minimum_is_instelbaar(self):
        u = uitslag("2026-W47,8,6,2,0,0\n2026-W48,8,6,1,0,0\n", grenzen=trechter.Grenzen(minimum=3))
        self.assertEqual(u.knelpunt, "afspraak")


class Venster(unittest.TestCase):
    def test_alleen_de_laatste_vier_weken(self):
        # Week 43 heeft veel reageerders maar valt buiten het venster van 45 tot en met 48.
        u = uitslag("2026-W43,50,40,20,10,5\n2026-W45,2,1,0,0,0\n2026-W46,2,1,0,0,0\n2026-W47,2,1,0,0,0\n2026-W48,2,1,0,0,0\n")
        self.assertEqual(u.knelpunt, "zichtbaarheid")
        self.assertEqual(trechter.weeknaam(u.van), "2026-W45")

    def test_ontbrekende_week_wordt_gemeld(self):
        u = uitslag("2026-W45,10,8,4,2,1\n2026-W47,10,8,4,2,1\n2026-W48,10,8,4,2,1\n")
        self.assertEqual([trechter.weeknaam(w) for w in u.ontbrekend], ["2026-W46"])
        self.assertIn("Niet ingevuld: 2026-W46", trechter.rapport(u))

    def test_toekomstige_week_telt_niet(self):
        u = uitslag("2026-W48,20,15,8,3,1\n2026-W50,1,0,0,0,0\n")
        self.assertEqual(trechter.weeknaam(u.tot), "2026-W48")

    def test_oud_logboek_krijgt_een_waarschuwing(self):
        u = uitslag("2026-W40,20,15,8,3,1\n")
        self.assertTrue(u.oud)
        self.assertIn("Let op", trechter.rapport(u))

    def test_leeg_logboek(self):
        u = uitslag("")
        self.assertIsNone(u.tot)
        self.assertIn("nog geen week", trechter.rapport(u))

    def test_jaarwisseling(self):
        u = trechter.beoordeel(
            logboek("2025-W52,10,8,4,2,1\n2026-W01,10,8,4,2,1\n"), dt.date(2026, 1, 2)
        )
        self.assertEqual(u.ontbrekend, [dt.date(2025, 12, 15), dt.date(2025, 12, 8)][::-1])


class Invoer(unittest.TestCase):
    def test_week_als_datum(self):
        self.assertEqual(trechter.maandag("2026-11-20"), dt.date(2026, 11, 16))
        self.assertEqual(trechter.maandag("20-11-2026"), dt.date(2026, 11, 16))
        self.assertEqual(trechter.maandag("2026-W47"), dt.date(2026, 11, 16))
        self.assertEqual(trechter.maandag("2026w47"), dt.date(2026, 11, 16))
        self.assertIsNone(trechter.maandag("week 47"))
        self.assertIsNone(trechter.maandag("2026-W60"))

    def test_puntkomma_als_scheiding(self):
        lb = logboek("2026-W48;12;7;3;1;0\n", kop=KOP.replace(",", ";"))
        self.assertEqual(len(lb.weken), 1)

    def test_rare_regels_tellen_niet_mee_en_worden_genoemd(self):
        lb = logboek("onzin,1,1,1,1,1\n2026-W47,1.2k,1,1,1,1\n2026-W48,5,9,1,1,1\n,,,,,\n")
        self.assertEqual(lb.onleesbaar, [2])
        self.assertEqual(lb.zonder_cijfers, [3])
        self.assertEqual(lb.onlogisch, [4])
        self.assertEqual(lb.weken, {})

    def test_dubbele_week_de_laatste_telt(self):
        lb = logboek("2026-W48,1,1,1,1,1\n2026-W48,20,15,8,3,1\n")
        self.assertEqual(lb.weken[dt.date(2026, 11, 23)].tellingen["reageerders"], 20)
        self.assertEqual(lb.dubbel, [("2026-W48", 3)])

    def test_duizendtallen(self):
        self.assertEqual(trechter.getal("1.234"), 1234)
        self.assertIsNone(trechter.getal("-3"))


class Opdrachtregel(unittest.TestCase):
    def draai(self, *args: str) -> tuple[int, str, str]:
        uit, fout = io.StringIO(), io.StringIO()
        with redirect_stdout(uit), redirect_stderr(fout):
            code = trechter.main(list(args))
        return code, uit.getvalue(), fout.getvalue()

    def test_ontbrekende_kolom_geeft_exitcode_2(self):
        with tempfile.TemporaryDirectory() as map_:
            pad = Path(map_) / "trechter.csv"
            pad.write_text("week,reageerders\n2026-W48,10\n", encoding="utf-8")
            code, _, fout = self.draai(str(pad))
        self.assertEqual(code, 2)
        self.assertIn("uit_doelgroep", fout)

    def test_ontbrekend_bestand(self):
        code, _, fout = self.draai("bestaat-niet.csv")
        self.assertEqual(code, 2)

    def test_grenzen_via_opties(self):
        with tempfile.TemporaryDirectory() as map_:
            pad = Path(map_) / "trechter.csv"
            pad.write_text(KOP + "2026-W48,10,4,2,1,0\n", encoding="utf-8")
            code, uit, _ = self.draai(str(pad), "--tot", "2026-11-27", "--doelgroep", "40%")
        self.assertEqual(code, 0)
        self.assertNotIn("Knelpunt: doelgroep", uit)

    def test_ongeldige_grens(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            trechter.main(["x.csv", "--opvolging", "2"])


if __name__ == "__main__":
    unittest.main()
