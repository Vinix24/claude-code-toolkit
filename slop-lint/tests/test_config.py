"""Tests voor de configuratie: waar hij gezocht wordt, hoe lagen samengaan en wat
er met een foute waarde gebeurt."""
from __future__ import annotations

import json

import slop_lint as sl
from conftest import VULLING, draai_cli, schrijf_config


def test_zonder_bestanden_gelden_de_defaults(tmp_path):
    cfg = sl.laad_config(tmp_path)
    assert cfg.waarden == sl.DEFAULTS
    assert cfg.bronnen == []
    assert cfg.meldingen == []


def test_project_wint_van_gebruiker_per_sleutel(tmp_path, lege_home):
    schrijf_config(lege_home, {"min_words": 10, "disable": ["komma-maar"]})
    project = tmp_path / "project"
    schrijf_config(project, {"min_words": 20})
    cfg = sl.laad_config(project)
    assert cfg["min_words"] == 20
    assert cfg["disable"] == ["komma-maar"]


def test_rules_en_profiles_worden_per_naam_samengevoegd(tmp_path, lege_home):
    schrijf_config(lege_home, {"rules": {"a": "aaa"}, "profiles": {"x": ["X"]}})
    project = tmp_path / "project"
    schrijf_config(project, {"rules": {"b": "bbb"}, "profiles": {"y": ["Y"]}})
    cfg = sl.laad_config(project)
    assert set(cfg["rules"]) == {"a", "b"}
    assert set(cfg["profiles"]) == {"x", "y"}


def test_projectbestand_wordt_omhoog_gezocht(tmp_path):
    project = tmp_path / "project"
    schrijf_config(project, {"min_words": 5})
    diep = project / "a" / "b"
    diep.mkdir(parents=True)
    cfg = sl.laad_config(diep / "tekst.md")
    assert cfg["min_words"] == 5
    assert cfg.wortel == project.resolve()


def test_gebruikersbestand_telt_niet_ook_als_projectbestand(lege_home):
    """Wie binnen zijn home-map werkt, loopt omhoog langs ~/.claude. Dat bestand
    is het gebruikersbestand en mag de projectmap niet naar HOME verleggen als
    tweede bron."""
    schrijf_config(lege_home, {"min_words": 7})
    werk = lege_home / "werk"
    werk.mkdir()
    cfg = sl.laad_config(werk)
    assert len(cfg.bronnen) == 1


def test_foute_waarde_valt_terug_met_melding(tmp_path):
    schrijf_config(tmp_path, {"min_words": "veel", "enabled": "ja"})
    cfg = sl.laad_config(tmp_path)
    assert cfg["min_words"] == 40
    assert cfg["enabled"] is True
    assert len(cfg.meldingen) == 2


def test_onbekende_sleutel_geeft_melding(tmp_path):
    schrijf_config(tmp_path, {"taal": "nl"})
    cfg = sl.laad_config(tmp_path)
    assert any("onbekende sleutel 'taal'" in m for m in cfg.meldingen)


def test_kapotte_json_geeft_melding_en_defaults(tmp_path):
    pad = tmp_path / ".claude" / "slop-lint.json"
    pad.parent.mkdir()
    pad.write_text("{niet json", encoding="utf-8")
    cfg = sl.laad_config(tmp_path)
    assert cfg.waarden == sl.DEFAULTS
    assert cfg.meldingen


def test_regel_met_kapotte_regex_wordt_overgeslagen(tmp_path):
    schrijf_config(tmp_path, {"rules": {"stuk": "(", "heel": "kortom"}})
    cfg = sl.laad_config(tmp_path)
    assert set(cfg["rules"]) == {"heel"}
    assert any("rules.stuk" in m for m in cfg.meldingen)


def test_eigen_regel_komt_in_de_eigen_laag(tmp_path):
    schrijf_config(tmp_path, {"rules": {"kortom": r"\bkortom\b"}})
    lagen = sl.bouw_lagen(sl.laad_config(tmp_path))
    assert lagen["eigen"] == {"kortom": r"\bkortom\b"}


def test_eigen_regel_met_ingebouwde_naam_vervangt_in_dezelfde_laag(tmp_path):
    schrijf_config(tmp_path, {"rules": {"buzzword": r"\bsynergie\b"}})
    lagen = sl.bouw_lagen(sl.laad_config(tmp_path))
    assert lagen["lexicaal"]["buzzword"] == r"\bsynergie\b"
    assert "buzzword" not in lagen["eigen"]


def test_regel_uitzetten_haalt_hem_uit_de_laag(tmp_path):
    schrijf_config(tmp_path, {"disable": ["komma-maar"]})
    lagen = sl.bouw_lagen(sl.laad_config(tmp_path))
    assert "komma-maar" not in lagen["structuur"]
    assert "komma-en" in lagen["structuur"]


def test_onbekende_regel_uitzetten_geeft_melding(tmp_path):
    schrijf_config(tmp_path, {"disable": ["bestaat-niet"]})
    cfg = sl.laad_config(tmp_path)
    sl.bouw_lagen(cfg)
    assert any("bestaat-niet" in m for m in cfg.meldingen)


def test_include_en_exclude_gelden_vanaf_de_projectmap(tmp_path):
    schrijf_config(tmp_path, {"include": ["Content/*"], "exclude": ["Content/concept/*"]})
    cfg = sl.laad_config(tmp_path)
    assert sl.in_scope(tmp_path / "Content" / "blog" / "a.md", cfg)
    assert not sl.in_scope(tmp_path / "Content" / "concept" / "b.md", cfg)
    assert not sl.in_scope(tmp_path / "README.md", cfg)


# ---------------------------------------------------------------------------
# De CLI met config
# ---------------------------------------------------------------------------

def _tic_bestand(map_):
    pad = map_ / "tekst.md"
    pad.write_text("Het kan, maar het kost tijd. " + VULLING, encoding="utf-8")
    return pad


def test_cli_uit_zet_een_regel_uit(tmp_path):
    pad = _tic_bestand(tmp_path)
    assert draai_cli([str(pad)], tmp_path).returncode == 1
    assert draai_cli(["--uit", "komma-maar", str(pad)], tmp_path).returncode == 0


def test_cli_leest_disable_uit_het_project(tmp_path):
    schrijf_config(tmp_path, {"disable": ["komma-maar"]})
    pad = _tic_bestand(tmp_path)
    assert draai_cli([str(pad)], tmp_path).returncode == 0


def test_cli_profiel_uit_de_config(tmp_path):
    schrijf_config(tmp_path, {"profiles": {"blog": ["Content"]}})
    (tmp_path / "Content").mkdir()
    _tic_bestand(tmp_path / "Content")
    r = draai_cli(["--profiel", "blog"], tmp_path)
    assert r.returncode == 1
    assert "Content/tekst.md" in r.stdout


def test_cli_onbekend_profiel_is_een_gebruiksfout(tmp_path):
    r = draai_cli(["--profiel", "bestaat-niet"], tmp_path)
    assert r.returncode == 2
    assert "onbekend profiel" in r.stderr


def test_cli_max_density_uit_de_config_werkt_als_lat(tmp_path):
    schrijf_config(tmp_path, {"max_density": 99})
    pad = _tic_bestand(tmp_path)
    r = draai_cli([str(pad)], tmp_path)
    assert r.returncode == 0
    assert "GROEN" in r.stdout


def test_cli_meldt_configfouten_op_stderr(tmp_path):
    schrijf_config(tmp_path, {"min_words": -1})
    pad = _tic_bestand(tmp_path)
    r = draai_cli([str(pad)], tmp_path)
    assert "min_words" in r.stderr


def test_defaults_zijn_geldige_json():
    assert json.loads(json.dumps(sl.DEFAULTS)) == sl.DEFAULTS
