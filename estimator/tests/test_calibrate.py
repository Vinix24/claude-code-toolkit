"""calibrate.py: ratios of one feature, verdicts over many, and drift between two tables."""
from __future__ import annotations

import json

import pytest

import calibrate as cal
import compute_estimate as ce
from conftest import write_table
from estimator_config import DEFAULTS, merge_settings


@pytest.fixture
def estimate(tmp_path):
    table = write_table(tmp_path / "t.md", {"alpha": (20, 10.0, 20.0, 40.0), "beta": (30, 5.0, 10.0, 30.0)})
    specs = [{"feature_id": "f", "topic_blocks": {"alpha": 2, "beta": 4}, "quality_target": "poc"}]
    return ce.build_record(specs, ce.parse_benchmarks(table), merge_settings(DEFAULTS, {}), table, False, "p", 1.5, 2, None)


ACTUAL = {"topics": {"alpha": {"blocks": 3, "minutes": 36.0, "median": 12.0},
                     "beta": {"blocks": 4, "minutes": 20.0, "median": 5.0},
                     "bug_fix": {"blocks": 2, "minutes": 14.0, "median": 7.0}}}


def test_compare_splits_the_miss_into_ratios(estimate):
    r = cal.compare(estimate, "f", ACTUAL, total_hours=2.0)
    alpha, beta, bug = r["per_topic"]["alpha"], r["per_topic"]["beta"], r["per_topic"]["bug_fix"]
    assert alpha["blocks_ratio"] == 1.5          # 3 blocks against 2 planned
    assert alpha["per_block_ratio"] == 1.2       # median 12 against the table's 10
    assert alpha["minutes_ratio"] == 1.8         # 36 against 2 x 10
    assert beta["blocks_ratio"] == 1.0 and beta["per_block_ratio"] == 1.0
    assert bug["planned"] is False and bug["blocks_ratio"] is None
    assert r["actual_session_minutes"] == 70.0
    assert r["unplanned_share"] == pytest.approx(0.2)
    # session median band: (2 x 10 + 4 x 5) x buffer 1.25 = 50 minutes
    assert r["session_bands_minutes"]["median"] == pytest.approx(50.0)
    assert r["session_ratio"] == 1.4
    assert r["session_band_hit"] == "<= p75"
    assert r["implied_overhead"] == pytest.approx(120 / 70, abs=1e-3)
    assert r["total_ratio"] == pytest.approx(120 / 75, abs=1e-3)


def test_compare_refuses_an_unknown_feature(estimate):
    with pytest.raises(ValueError):
        cal.compare(estimate, "nope", ACTUAL)


def record_with(blocks_ratio, quality="demo"):
    planned = 10.0
    return {
        "quality_target": quality, "external_deps": [], "overhead_used": 1.4, "session_band_hit": "<= median",
        "session_ratio": blocks_ratio, "unplanned_share": 0.1, "implied_overhead": 1.4 * blocks_ratio,
        "per_topic": {"alpha": {"planned": True, "planned_blocks": planned, "actual_blocks": planned * blocks_ratio,
                                "blocks_ratio": blocks_ratio, "per_block_ratio": 1.0, "minutes_ratio": blocks_ratio}},
    }


def test_verdicts_need_enough_features():
    assert cal.verdict([1.5] * 4, 0.2, 5) == "too few"
    assert cal.verdict([1.5] * 5, 0.2, 5) == "raise"
    assert cal.verdict([0.7] * 5, 0.2, 5) == "lower"
    assert cal.verdict([0.9, 1.0, 1.1, 1.15, 0.85], 0.2, 5) == "keep"


def test_summary_points_at_the_factor_to_change():
    s = cal.summarize([record_with(1.5) for _ in range(5)], tolerance=0.2, min_features=5)
    assert s["topics"]["alpha"]["blocks_ratio"]["verdict"] == "raise"
    assert s["topics"]["alpha"]["per_block_ratio"]["verdict"] == "keep"
    assert s["quality"]["demo"]["median_blocks_ratio"] == 1.5
    assert s["overhead_verdict"] == "raise"
    assert s["session_band_hits"] == {"<= median": 5}


def test_drift_flags_only_well_measured_moves(tmp_path):
    old = ce.parse_benchmarks(write_table(tmp_path / "old.md", {
        "big": (100, 10.0, 15.0, 30.0), "steady": (50, 8.0, 12.0, 20.0), "rare": (4, 16.0, 20.0, 50.0), "gone": (30, 5.0, 6.0, 9.0)}))
    new = ce.parse_benchmarks(write_table(tmp_path / "new.md", {
        "big": (400, 6.0, 12.0, 30.0), "steady": (90, 8.4, 12.0, 21.0), "rare": (300, 10.0, 18.0, 45.0)}))
    verdicts = {r["topic"]: r["verdict"] for r in cal.drift(old, new, tolerance=0.2, min_n=15)}
    assert verdicts == {"big": "drift", "steady": "stable", "rare": "small N", "gone": "only in one table"}


def test_cli_record_then_report(tmp_path, estimate, capsys):
    est_path, act_path, log = tmp_path / "est.json", tmp_path / "act.json", tmp_path / "cal.jsonl"
    est_path.write_text(json.dumps(estimate))
    act_path.write_text(json.dumps(ACTUAL))
    for _ in range(2):
        assert cal.main(["record", "--estimate", str(est_path), "--feature", "f", "--actual", str(act_path),
                         "--log", str(log)]) == 0
    assert len(log.read_text().splitlines()) == 2
    capsys.readouterr()
    assert cal.main(["report", "--log", str(log)]) == 0
    out = capsys.readouterr().out
    assert "2 features recorded" in out and "too few" in out


def test_cli_drift(tmp_path, capsys):
    old = write_table(tmp_path / "old.md", {"a": (20, 10.0, 15.0, 30.0)})
    new = write_table(tmp_path / "new.md", {"a": (40, 5.0, 8.0, 20.0)})
    assert cal.main(["drift", "--old", str(old), "--new", str(new)]) == 0
    assert "| a | 20 | 40 | 10.00 | 5.00 | 0.50 | 0.67 | drift |" in capsys.readouterr().out
