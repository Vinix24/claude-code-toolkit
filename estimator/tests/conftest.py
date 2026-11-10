"""Shared fixtures: the scripts on the path, an isolated home, and builders for tables and transcripts."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG / "scripts"))

T0 = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    """No test may read or write the real ~/.claude."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("ESTIMATOR_HOME", str(home / ".claude" / "estimator"))
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    return home


def write_table(path: Path, rows: dict[str, tuple[int, float, float, float]]) -> Path:
    """A five-column benchmark table: topic -> (N, median, p75, p95)."""
    lines = ["| Topic | N blocks | Median min | p75 | p95 |", "|---|---:|---:|---:|---:|"]
    lines += [f"| {t} | {n} | {m} | {p75} | {p95} |" for t, (n, m, p75, p95) in rows.items()]
    path.write_text("\n".join(lines) + "\n")
    return path


def at(minutes: float) -> str:
    return (T0 + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def prompt(minutes: float, session: str = "s1", cwd: str = "/work/app", text: str = "go") -> dict:
    return {"type": "user", "timestamp": at(minutes), "sessionId": session, "cwd": cwd,
            "message": {"role": "user", "content": text}}


def assistant(minutes: float, session: str = "s1", cwd: str = "/work/app", tool: str = None,
              tool_input: dict = None, text: str = "ok") -> dict:
    content = [{"type": "text", "text": text}]
    if tool:
        content.append({"type": "tool_use", "name": tool, "input": tool_input or {}})
    return {"type": "assistant", "timestamp": at(minutes), "sessionId": session, "cwd": cwd,
            "message": {"role": "assistant", "model": "test-model", "content": content}}


def tool_result(minutes: float, session: str = "s1", cwd: str = "/work/app", text: str = "done") -> dict:
    return {"type": "user", "timestamp": at(minutes), "sessionId": session, "cwd": cwd,
            "message": {"role": "user", "content": [{"type": "tool_result", "content": text}]}}


def write_transcript(path: Path, events: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(e) + "\n" for e in events))
    return path
