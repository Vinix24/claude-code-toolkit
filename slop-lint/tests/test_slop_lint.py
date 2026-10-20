"""Tests voor de regels van de slop-linter.

Elke test moet kunnen falen op GEDRAG, niet op een ontbrekend symbool: elk
patroon krijgt daarom een zin die hem hoort te vangen EN een zin die er dicht
tegenaan ligt en hem NIET mag vangen. Een detector die alles vangt is even
waardeloos als een die niets vangt.

Draaien:  python3 -m pytest -q   (vanuit slop-lint/)
"""

from __future__ import annotations

import re
import zipfile

import pytest

import slop_lint as sl
from conftest import VULLING, draai_cli


def treffers(tekst: str, laag: str | None = None) -> list[str]:
    """Namen van de patronen die op deze tekst aanslaan."""
    lagen = {laag: sl.LAGEN[laag]} if laag else sl.LAGEN
    uit = []
    for _, patronen in lagen.items():
        for naam, patroon in patronen.items():
            if re.search(patroon, tekst, re.I):
                uit.append(naam)
    return uit


# ---------------------------------------------------------------------------
# Laag 2 -- structuur, waar het volume zit
# ---------------------------------------------------------------------------

def test_komma_en_wordt_gevangen():
    assert "komma-en" in treffers("Ik heb het nagekeken, en het klopt deels.")


def test_en_zonder_komma_is_schoon():
    assert "komma-en" not in treffers("Ik heb het nagekeken en het klopt deels.")


@pytest.mark.parametrize("zin,naam", [
    ("Het kan, maar het kost tijd.", "komma-maar"),
    ("Werkt het niet, dan bel je mij.", "komma-dan"),
    ("Het is laat, dus ik stop.", "komma-dus"),
    ("Ik stop nu, want het is laat.", "komma-want"),
])
def test_overige_kommaketens(zin, naam):
    assert naam in treffers(zin, "structuur")


# ---------------------------------------------------------------------------
# De opsommings-uitzondering uit anti-ai-tics.md
# ---------------------------------------------------------------------------

def test_opsomming_van_gelijkwaardige_elementen_telt_niet():
    zin = ("hoeveel dispatches verwerkt, hoeveel afgewezen, "
           "welke gates getriggerd, en wat de kosten waren")
    assert sl._is_opsomming(zin)


def test_twee_bijzinnen_zijn_geen_opsomming():
    assert not sl._is_opsomming("Ik heb het nagekeken, en het klopt deels.")


def test_opsomming_wordt_niet_als_bevinding_geteld(tmp_path):
    pad = tmp_path / "a.md"
    pad.write_text(
        "Het overzicht toont hoeveel dispatches verwerkt, hoeveel afgewezen, "
        "welke gates getriggerd, en wat de kosten waren. " + VULLING,
        encoding="utf-8")
    bev, _ = sl.toets_bestand(pad, {"structuur": sl.STRUCTUUR})
    assert [b.naam for b in bev if b.naam == "komma-en"] == []


# ---------------------------------------------------------------------------
# Laag 3 -- frames, inclusief de drie die de tweede beoordeling vond
# ---------------------------------------------------------------------------

def test_drieslag_met_komma():
    assert "drieslag" in treffers("Dat werkt. Sneller, beter, slimmer. Klaar.")


def test_drieslag_midden_in_een_zin():
    """De oude lookbehind eiste dat de drieslag een zin begon en miste daardoor
    precies het voorbeeld uit de eigen schrijfregels."""
    assert "drieslag" in treffers("De aanpak is sneller, beter, slimmer.")


def test_twee_elementen_is_geen_drieslag():
    assert "drieslag" not in treffers("De aanpak is sneller, beter.")


def test_drieslag_met_en():
    assert "drieslag-met-en" in treffers("Maar de calculator weegt, kiest en tekent.")


def test_gewone_opsomming_van_twee_is_geen_drieslag():
    assert "drieslag-met-en" not in treffers("De calculator weegt en tekent.")


def test_niet_omdat_los_over_twee_zinnen():
    assert "niet-omdat-los" in treffers("Het lukte niet. Niet omdat de AI het niet kan.")


def test_engelse_not_just_variant():
    assert "not-just-X" in treffers("This isn't just clean architecture.")


def test_gewone_engelse_ontkenning_is_schoon():
    assert "not-just-X" not in treffers("This isn't clean architecture.")


def test_niet_x_maar_y():
    assert "niet-X-maar-Y" in treffers("Het is niet de techniek maar de governance.")


# ---------------------------------------------------------------------------
# Laag 1 -- woordenlijst
# ---------------------------------------------------------------------------

def test_buzzword_en_em_dash():
    gevonden = treffers("Een revolutionair systeem — echt waar.")
    assert "buzzword" in gevonden
    assert "em-dash" in gevonden


@pytest.mark.parametrize("zin", [
    "De snelheid van Sonnet is echt.",
    "De besparing is ook echt, alleen klein.",
    "Het risico is reëel.",
    "The speed gain is real.",
])
def test_is_echt_als_vertaling_van_is_real(zin):
    assert "is-echt-calque" in treffers(zin, "lexicaal")


@pytest.mark.parametrize("zin", [
    "Sonnet 5.5 is echt goed in zelfstandig werken.",
    "Is dit echt nodig voor een offerte van twee pagina's?",
    "This is a real problem for small teams.",
])
def test_echt_als_versterker_is_schoon(zin):
    assert "is-echt-calque" not in treffers(zin, "lexicaal")


def test_schone_zin_levert_niets():
    assert treffers("De migratie draaide in veertien seconden.") == []


# ---------------------------------------------------------------------------
# De negeer-marker
# ---------------------------------------------------------------------------

def test_negeer_marker_onderdrukt_de_treffer(tmp_path):
    pad = tmp_path / "b.md"
    pad.write_text(
        "Een revolutionair systeem. slop-negeer: citaat uit de brochure\n" + VULLING,
        encoding="utf-8")
    bev, _ = sl.toets_bestand(pad, {"lexicaal": sl.LEXICAAL})
    assert [b.naam for b in bev if b.naam == "buzzword"] == []


def test_zonder_marker_wordt_hij_wel_gevangen(tmp_path):
    pad = tmp_path / "c.md"
    pad.write_text("Een revolutionair systeem.\n" + VULLING, encoding="utf-8")
    bev, _ = sl.toets_bestand(pad, {"lexicaal": sl.LEXICAAL})
    assert any(b.naam == "buzzword" for b in bev)


# ---------------------------------------------------------------------------
# De dragers: markdown, e-mail, docx
# ---------------------------------------------------------------------------

def test_codeblok_telt_niet_mee():
    tekst = sl._strip_markdown("```\nrevolutionair\n```\nGewone zin.")
    assert "revolutionair" not in tekst


def test_frontmatter_telt_niet_mee():
    tekst = sl._strip_markdown('---\ntitel: "revolutionair"\n---\nGewone zin.')
    assert "revolutionair" not in tekst


def test_geciteerde_mail_telt_niet_mee():
    raw = ("From: iemand\nSubject: test\n\n"
           "Mijn eigen zin.\n"
           "> Een revolutionair idee van de ander.\n")
    eigen = sl._strip_email(raw)
    assert "Mijn eigen zin." in eigen
    assert "revolutionair" not in eigen


def test_reply_keten_wordt_afgekapt():
    raw = ("From: ik\nSubject: x\n\n"
           "Mijn eigen zin.\n\n"
           "Op 1 januari schreef iemand:\n"
           "Een revolutionair idee van de ander.\n")
    eigen = sl._strip_email(raw)
    assert "Mijn eigen zin." in eigen
    assert "revolutionair" not in eigen


def test_onleesbare_docx_geeft_lege_tekst_geen_crash(tmp_path):
    """Twee soorten kapot, allebei echt voorgekomen in het corpus."""
    geen_zip = tmp_path / "geenzip.docx"
    geen_zip.write_bytes(b"dit is geen zip")
    assert sl._lees_docx(geen_zip) == ""

    # Een geldige zip met onleesbare XML erin: lxml.etree.XMLSyntaxError.
    zf = zipfile
    stukke_xml = tmp_path / "stuk.docx"
    with zf.ZipFile(stukke_xml, "w") as z:
        z.writestr("[Content_Types].xml", "<Types<<>")
        z.writestr("word/document.xml", "<w:document")
    assert sl._lees_docx(stukke_xml) == ""


# ---------------------------------------------------------------------------
# Eigenschappen die geldig blijven als de lijsten groeien
# ---------------------------------------------------------------------------

def test_elk_patroon_compileert():
    for laag, patronen in sl.LAGEN.items():
        for naam, patroon in patronen.items():
            re.compile(patroon)  # faalt luid bij een kapotte regex


def test_patroonnamen_zijn_uniek_over_de_lagen():
    namen = [n for p in sl.LAGEN.values() for n in p]
    assert len(namen) == len(set(namen))


def test_elke_extensie_heeft_een_lezer(tmp_path):
    for ext in sl.EXTENSIES:
        pad = tmp_path / f"x{ext}"
        pad.write_bytes(b"") if ext == ".docx" else pad.write_text("tekst", encoding="utf-8")
        sl.lees_tekst(pad)  # mag niet crashen


def test_vendor_mappen_worden_overgeslagen(tmp_path):
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "r.md").write_text("revolutionair", encoding="utf-8")
    (tmp_path / "eigen.md").write_text("gewone tekst", encoding="utf-8")
    gevonden = sl.verzamel([tmp_path])
    assert [p.name for p in gevonden] == ["eigen.md"]


# ---------------------------------------------------------------------------
# De drempel als ratchet
# ---------------------------------------------------------------------------

def test_zonder_drempel_faalt_elke_treffer(tmp_path):
    p = tmp_path / "a.md"
    p.write_text("Ik heb het nagekeken, en het klopt. " + VULLING, encoding="utf-8")
    assert draai_cli([str(p)], tmp_path).returncode == 1


def test_met_ruime_drempel_slaagt_dezelfde_tekst(tmp_path):
    p = tmp_path / "b.md"
    p.write_text("Ik heb het nagekeken, en het klopt. " + VULLING, encoding="utf-8")
    r = draai_cli(["--max-dichtheid", "99", str(p)], tmp_path)
    assert r.returncode == 0
    assert "GROEN" in r.stdout


def test_drempel_kan_wel_degelijk_falen(tmp_path):
    """Een lat die nooit rood wordt bewaakt niets."""
    p = tmp_path / "c.md"
    p.write_text("Ik heb het nagekeken, en het klopt, en dat is fijn, en dus stop ik. "
                 + " ".join(["vulling"] * 40), encoding="utf-8")
    r = draai_cli(["--max-dichtheid", "1", str(p)], tmp_path)
    assert r.returncode == 1
    assert "ROOD" in r.stdout


def test_kommaketen_is_geen_opsomming(tmp_path):
    """De guard excuseerde ooit een keten van bijzinnen als lijst. Het
    onderscheid is dat de delen van een keten met 'en' beginnen."""
    keten = "Ik heb het nagekeken, en het klopt, en dat is fijn, en dus stop ik."
    assert not sl._is_opsomming(keten)


def test_echte_opsomming_blijft_uitgezonderd():
    lijst = ("hoeveel dispatches verwerkt, hoeveel afgewezen, "
             "welke gates getriggerd, en wat de kosten waren")
    assert sl._is_opsomming(lijst)


# ---------------------------------------------------------------------------
# Inline code mag geen treffers maken die er in de tekst niet staan
# ---------------------------------------------------------------------------

def test_opsomming_van_inline_code_is_geen_komma_en(tmp_path):
    """Gevonden doordat de linter zijn eigen skilltekst las: inline code werd een
    spatie en liet een losse komma voor 'en' achter."""
    pad = tmp_path / "a.md"
    pad.write_text("Lees de woordenboeken `LEXICAAL`, `STRUCTUUR` en `FRAMES` door. "
                   + VULLING, encoding="utf-8")
    bev, _ = sl.toets_bestand(pad, sl.LAGEN)
    assert [b.naam for b in bev] == []


def test_drie_codenamen_zijn_geen_drieslag(tmp_path):
    pad = tmp_path / "b.md"
    pad.write_text("De sleutels zijn `include`, `exclude`, `disable`. " + VULLING, encoding="utf-8")
    bev, _ = sl.toets_bestand(pad, sl.LAGEN)
    assert "drieslag" not in [b.naam for b in bev]


def test_echte_komma_en_naast_inline_code_blijft_gevangen(tmp_path):
    pad = tmp_path / "c.md"
    pad.write_text("Ik draaide `pytest`, en het was groen. " + VULLING, encoding="utf-8")
    bev, _ = sl.toets_bestand(pad, sl.LAGEN)
    assert "komma-en" in [b.naam for b in bev]
