"""Tests voor de hook, end-to-end via run.sh zoals Claude Code hem start."""
from __future__ import annotations

import json

from conftest import VULLING, draai_hook, schrijf_config

TIC = "Ik heb het nagekeken, en het klopt deels. "


def _schrijf(pad, tekst=TIC + VULLING):
    pad.parent.mkdir(parents=True, exist_ok=True)
    pad.write_text(tekst, encoding="utf-8")
    return pad


def _write(pad):
    return {"hook_event_name": "PostToolUse", "tool_name": "Write",
            "tool_input": {"file_path": str(pad)},
            "tool_response": {"filePath": str(pad)}}


def test_tic_levert_context_voor_het_model(tmp_path):
    pad = _schrijf(tmp_path / "a.md")
    r = draai_hook(_write(pad), tmp_path)
    assert r.returncode == 0
    uit = json.loads(r.stdout)
    context = uit["hookSpecificOutput"]["additionalContext"]
    assert uit["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    assert "komma-en" in context
    assert "a.md:1" in context
    assert "1 treffers in a.md" in uit["systemMessage"]


def test_edit_zonder_tool_response_werkt_ook(tmp_path):
    pad = _schrijf(tmp_path / "a.md")
    r = draai_hook({"tool_name": "Edit", "tool_input": {"file_path": str(pad)}}, tmp_path)
    assert "komma-en" in r.stdout


def test_schoon_bestand_zwijgt(tmp_path):
    pad = _schrijf(tmp_path / "a.md", "Ik heb het nagekeken en het klopt deels. " + VULLING)
    r = draai_hook(_write(pad), tmp_path)
    assert r.returncode == 0
    assert r.stdout == ""


def test_uit_via_omgeving(tmp_path):
    pad = _schrijf(tmp_path / "a.md")
    r = draai_hook(_write(pad), tmp_path, CLAUDE_SLOP_LINT="off")
    assert r.returncode == 0
    assert r.stdout == ""


def test_uit_via_project(tmp_path):
    schrijf_config(tmp_path, {"enabled": False})
    pad = _schrijf(tmp_path / "a.md")
    assert draai_hook(_write(pad), tmp_path).stdout == ""


def test_buiten_include_zwijgt(tmp_path):
    schrijf_config(tmp_path, {"include": ["Content/*"]})
    buiten = _schrijf(tmp_path / "notities" / "a.md")
    binnen = _schrijf(tmp_path / "Content" / "b.md")
    assert draai_hook(_write(buiten), tmp_path).stdout == ""
    assert "komma-en" in draai_hook(_write(binnen), tmp_path).stdout


def test_andere_extensie_zwijgt(tmp_path):
    pad = _schrijf(tmp_path / "code.py")
    assert draai_hook(_write(pad), tmp_path).stdout == ""


def test_vendor_map_zwijgt(tmp_path):
    pad = _schrijf(tmp_path / "node_modules" / "pakket" / "README.md")
    assert draai_hook(_write(pad), tmp_path).stdout == ""


def test_kort_bestand_zwijgt(tmp_path):
    pad = _schrijf(tmp_path / "a.md", TIC)
    assert draai_hook(_write(pad), tmp_path).stdout == ""


def test_onder_de_lat_zwijgt(tmp_path):
    schrijf_config(tmp_path, {"max_density": 99})
    pad = _schrijf(tmp_path / "a.md")
    assert draai_hook(_write(pad), tmp_path).stdout == ""


def test_uitgezette_regel_zwijgt(tmp_path):
    schrijf_config(tmp_path, {"disable": ["komma-en"]})
    pad = _schrijf(tmp_path / "a.md")
    assert draai_hook(_write(pad), tmp_path).stdout == ""


def test_onzin_op_stdin_blokkeert_niet(tmp_path):
    r = draai_hook("geen json", tmp_path)
    assert r.returncode == 0
    assert r.stdout == ""


def test_niet_bestaand_bestand_zwijgt(tmp_path):
    r = draai_hook(_write(tmp_path / "weg.md"), tmp_path)
    assert r.returncode == 0
    assert r.stdout == ""


def test_ontbrekende_python_geeft_nooit_exit_2(tmp_path):
    """Exit 2 blokkeert de sessie. Een kapotte installatie mag dat nooit doen."""
    pad = _schrijf(tmp_path / "a.md")
    r = draai_hook(_write(pad), tmp_path, SLOP_LINT_PYTHON="python-die-niet-bestaat")
    assert r.returncode == 1
    assert "not found" in r.stderr
