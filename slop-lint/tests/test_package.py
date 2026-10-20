"""Tests op de verpakking: manifest, marketplace, hooks.json en de skill.

Een plugin die niet laadt faalt stil: Claude Code slaat hem over en de hook draait
nooit. Deze tests maken dat luid."""
from __future__ import annotations

import json
import re
import subprocess

from conftest import PAKKET, RUN_SH, VULLING, draai_cli

MARKETPLACE = PAKKET.parent / ".claude-plugin" / "marketplace.json"


def _manifest():
    return json.loads((PAKKET / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))


def test_versie_in_manifest_marketplace_en_changelog_is_gelijk():
    manifest = _manifest()
    markt = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    entry = next(p for p in markt["plugins"] if p["name"] == manifest["name"])
    assert entry["version"] == manifest["version"]
    assert (PAKKET.parent / entry["source"]).resolve() == PAKKET
    assert f"## {manifest['version']}" in (PAKKET / "CHANGELOG.md").read_text(encoding="utf-8")


def test_hooks_json_wijst_naar_een_bestaand_script():
    hooks = json.loads((PAKKET / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    commando = hooks["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
    assert "${CLAUDE_PLUGIN_ROOT}/hooks/run.sh" in commando
    assert commando.endswith("|| exit 1")
    assert RUN_SH.is_file()


def test_run_sh_is_geldig_posix_sh():
    assert subprocess.run(["sh", "-n", str(RUN_SH)]).returncode == 0


def test_skill_frontmatter_klopt_met_de_map():
    skill = PAKKET / "skills" / "slop-check" / "SKILL.md"
    kop = skill.read_text(encoding="utf-8").split("---")[1]
    naam = re.search(r"^name:\s*(\S+)", kop, re.M).group(1)
    assert naam == skill.parent.name
    assert re.search(r"^description:\s*\S", kop, re.M)


def test_skill_map_is_op_zichzelf_bruikbaar():
    """De skill moet ook los te uploaden zijn, zonder de rest van de plugin.
    Het script mag dus niets buiten zijn eigen map importeren."""
    script = (PAKKET / "skills" / "slop-check" / "scripts" / "slop_lint.py").read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([\w.]+)", script, re.M)
    toegestaan = {"__future__", "argparse", "json", "re", "sys", "dataclasses",
                  "fnmatch", "pathlib", "docx"}
    assert set(imports) <= toegestaan


def test_min_woorden_nul_lint_ook_een_kort_fragment(tmp_path):
    pad = tmp_path / "kort.md"
    pad.write_text("Het kan, maar het kost tijd.", encoding="utf-8")
    assert draai_cli([str(pad)], tmp_path).returncode == 0
    assert draai_cli(["--min-woorden", "0", str(pad)], tmp_path).returncode == 1


def test_lang_fragment_haalt_de_standaardgrens(tmp_path):
    pad = tmp_path / "lang.md"
    pad.write_text("Het kan, maar het kost tijd. " + VULLING, encoding="utf-8")
    assert draai_cli([str(pad)], tmp_path).returncode == 1
