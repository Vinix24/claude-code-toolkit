"""Settings and paths shared by the estimator scripts.

Every tunable number has its default here. A JSON config file overrides any of them per key:

  1. the defaults below;
  2. $ESTIMATOR_HOME/config.json (default ~/.claude/estimator/config.json), when it exists;
  3. a file passed with --config.

Dictionaries (quality_factors, external_dep_premiums) merge per key, so a config can add one
dependency type without repeating the others. Every other value replaces the default.

The defaults are the settings I use on my own measurements. They are starting values for the
calibration loop, not facts about your work: calibrate.py tells you when to change them.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

SKILL_DIR = Path(__file__).resolve().parent.parent
EXAMPLE_BENCHMARKS = SKILL_DIR / "benchmarks.example.md"

DEFAULTS: dict = {
    # Benchmark table to estimate from. None: $ESTIMATOR_HOME/topic-statistics.md, else the example.
    "benchmarks": None,
    # Time outside Claude Code sessions (meetings, reviews, thinking offline), as a multiplier.
    "overhead": 1.4,
    # How many features you really keep moving at the same time.
    "parallel_cap": 3,
    # When set, the report converts wall-clock hours into calendar weeks.
    "hours_per_week": None,
    # Multiplier on block minutes per quality target.
    "quality_factors": {"poc": 1.0, "demo": 1.4, "production-ready": 2.2},
    "default_quality": "demo",
    # Minutes of connection probing per external dependency, before any feature code works.
    "external_dep_premiums": {
        "rest_api_key": 15,
        "oauth2": 30,
        "non_public_schema": 30,
        "enterprise_oauth": 45,
        "custom_legacy_auth": 60,
        "streaming_api": 75,
    },
    "default_external_dep_premium": 25,
    # [minimum N, factor]: the buffer comes from the lowest-N topic in a feature.
    "confidence_buffers": [[15, 1.25], [5, 1.4], [0, 1.5]],
    "confidence_labels": [[20, "high"], [10, "medium"], [5, "low-medium"], [0, "low"]],
    # Topics below this N get a warning in the report.
    "low_n_warning": 5,
    # Work-block segmentation (refresh_topic_stats.py).
    "mode": "gap",
    "gap_minutes": 5.0,
    "min_block_minutes": 1.0,
    # Turn mode only: pauses inside a turn longer than this are left out. None counts every wait.
    "max_wait_minutes": None,
    # Classifier overrides: None keeps the built-in rules in workblocks.py.
    "topic_rules": None,
    "tool_topics": None,
    # Calibration (calibrate.py).
    "calibration_tolerance": 0.2,
    "calibration_min_features": 5,
    "drift_min_n": 15,
}

MERGED_DICTS = ("quality_factors", "external_dep_premiums")


def estimator_home() -> Path:
    """Where the estimator keeps its own files: block store, table, estimates, calibration log."""
    return Path(os.environ.get("ESTIMATOR_HOME") or Path.home() / ".claude" / "estimator").expanduser()


def claude_projects_dir() -> Path:
    """The transcripts folder of the active Claude Code config dir."""
    base = os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
    return Path(base).expanduser() / "projects"


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"estimator: cannot read config {path}: {exc}")
    if not isinstance(data, dict):
        raise SystemExit(f"estimator: config {path} must hold a JSON object")
    return data


def merge_settings(base: dict, override: dict, source: str = "config") -> dict:
    """Return base with override applied per key; unknown keys are reported, not used."""
    merged = {k: (dict(v) if isinstance(v, dict) else v) for k, v in base.items()}
    for key, value in override.items():
        if key not in DEFAULTS:
            print(f"estimator: unknown key '{key}' in {source}, ignored", file=sys.stderr)
            continue
        if key in MERGED_DICTS and isinstance(value, dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def load_settings(config_path: Optional[Path] = None) -> dict:
    settings = merge_settings(DEFAULTS, {})
    home_config = estimator_home() / "config.json"
    if home_config.exists():
        settings = merge_settings(settings, _read_json(home_config), str(home_config))
    if config_path is not None:
        settings = merge_settings(settings, _read_json(Path(config_path).expanduser()), str(config_path))
    return settings


def resolve_benchmarks(cli_path: Optional[Path], settings: dict) -> tuple[Path, bool]:
    """(benchmark table, is_example). The example is the last resort and is flagged in every report."""
    if cli_path is not None:
        path = Path(cli_path).expanduser()
    elif settings.get("benchmarks"):
        path = Path(settings["benchmarks"]).expanduser()
    elif (estimator_home() / "topic-statistics.md").exists():
        path = estimator_home() / "topic-statistics.md"
    else:
        path = EXAMPLE_BENCHMARKS
    return path, path.resolve() == EXAMPLE_BENCHMARKS.resolve()
