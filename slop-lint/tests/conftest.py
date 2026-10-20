"""Gedeelde fixtures: paden in het pakket en een geïsoleerde HOME.

Elke test draait met een eigen lege HOME. Anders zou een `~/.claude/slop-lint.json`
op de machine van wie de tests draait de uitslag stil veranderen.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PAKKET = Path(__file__).resolve().parents[1]
SCRIPTS = PAKKET / "skills" / "slop-check" / "scripts"
LINTER = SCRIPTS / "slop_lint.py"
RUN_SH = PAKKET / "hooks" / "run.sh"

sys.path.insert(0, str(SCRIPTS))

VULLING = " ".join(["vulling"] * 60)


@pytest.fixture(autouse=True)
def lege_home(tmp_path_factory, monkeypatch):
    home = tmp_path_factory.mktemp("home")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("CLAUDE_SLOP_LINT", raising=False)
    monkeypatch.delenv("SLOP_LINT_PYTHON", raising=False)
    return home


def schrijf_config(map_: Path, inhoud: dict) -> Path:
    pad = map_ / ".claude" / "slop-lint.json"
    pad.parent.mkdir(parents=True, exist_ok=True)
    pad.write_text(json.dumps(inhoud), encoding="utf-8")
    return pad


def draai_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(LINTER), *args], capture_output=True,
                          text=True, cwd=str(cwd), env=dict(os.environ))


def draai_hook(invoer, cwd: Path, **env) -> subprocess.CompletedProcess:
    tekst = invoer if isinstance(invoer, str) else json.dumps(invoer)
    omgeving = {**os.environ, "SLOP_LINT_PYTHON": sys.executable, **env}
    return subprocess.run(["sh", str(RUN_SH)], input=tekst, capture_output=True,
                          text=True, cwd=str(cwd), env=omgeving)
