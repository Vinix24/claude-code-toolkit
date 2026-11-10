"""Deterministic parts of compute_estimate.py: the table parser, the bands and the dependency graph."""
from __future__ import annotations

import json

import pytest

import compute_estimate as ce
from conftest import PKG, write_table
from estimator_config import DEFAULTS, load_settings, merge_settings

STATS = {
    "alpha": {"n": 20, "median": 10.0, "p75": 20.0, "p95": 40.0},
    "beta": {"n": 8, "median": 5.0, "p75": 10.0, "p95": 30.0},
}


def settings(**override):
    return merge_settings(DEFAULTS, override)


# ---------------------------------------------------------------- table parser

def test_parse_example_benchmarks():
    rows = ce.parse_benchmarks(PKG / "benchmarks.example.md")
    assert len(rows) == 11
    assert rows["python_test"] == {"n": 2550, "median": 7.79, "p75": 14.64, "p95": 31.47}
    assert "analysis_only" not in rows


def test_parse_full_table_by_header_name(tmp_path):
    path = tmp_path / "full.md"
    path.write_text(
        "# Topic statistics\n\nintro text\n\n"
        "| Topic | N blocks | Median min | p25 | p75 | p95 | Mean tool-calls | Mean errors | Total hours | Median lines | Min per 100 lines |\n"
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n"
        "| python_test | 12 | 6.50 | 3.00 | 9.00 | 20.00 | 30.0 | 1.00 | 1.3 | 100 | 4.0 |\n"
        "| odd_topic | 3 | - | - | - | - | 0.0 | 0.00 | 0.1 | - | - |\n"
        "\nnotes in between\n\n"
        "| Topic | N blocks | Median min | p25 | p75 | p95 |\n|---|---:|---:|---:|---:|---:|\n"
        "| later_table | 1 | 1.0 | 1.0 | 1.0 | 1.0 |\n"
    )
    rows = ce.parse_benchmarks(path)
    assert rows == {"python_test": {"n": 12, "median": 6.5, "p25": 3.0, "p75": 9.0, "p95": 20.0}}


def test_parse_rejects_a_table_without_p95(tmp_path):
    path = tmp_path / "bad.md"
    path.write_text("| Topic | N blocks | Median min | p75 |\n|---|---|---|---|\n| a | 1 | 2 | 3 |\n")
    with pytest.raises(ValueError):
        ce.parse_benchmarks(path)


# ---------------------------------------------------------------- bands

def test_bands_follow_the_formula():
    feature = {"feature_id": "f", "topic_blocks": {"alpha": 2, "beta": 1}, "quality_target": "demo",
               "external_deps": ["rest_api_key"]}
    out = ce.estimate_feature(feature, STATS, settings(), overhead=1.5)
    # raw minutes per band: 2 x alpha + 1 x beta; quality demo 1.4; premium 15; buffer from min N 8 = 1.4
    assert out["raw_block_minutes"] == {"median": 25.0, "p75": 50.0, "p95": 110.0}
    assert out["buffer"] == 1.4
    assert out["bands_minutes"]["median"] == pytest.approx((25 * 1.4 + 15) * 1.5 * 1.4)
    assert out["bands_minutes"]["p75"] == pytest.approx((50 * 1.4 + 15) * 1.5 * 1.4)
    assert out["bands_minutes"]["p95"] == pytest.approx((110 * 1.4 + 15) * 1.5 * 1.4)
    assert out["confidence"] == "low-medium"
    assert out["warnings"] == []


def test_bands_are_ordered_median_p75_p95():
    out = ce.estimate_feature({"feature_id": "f", "topic_blocks": {"alpha": 3}}, STATS, settings(), 1.4)
    b = out["bands_minutes"]
    assert b["median"] < b["p75"] < b["p95"]


@pytest.mark.parametrize("n, buffer, label", [
    (20, 1.25, "high"), (19, 1.25, "medium"), (15, 1.25, "medium"), (14, 1.4, "medium"),
    (10, 1.4, "medium"), (9, 1.4, "low-medium"), (5, 1.4, "low-medium"), (4, 1.5, "low"), (0, 1.5, "low"),
])
def test_confidence_thresholds(n, buffer, label):
    assert ce.confidence_buffer(n, DEFAULTS) == buffer
    assert ce.confidence_label(n, DEFAULTS) == label


def test_extra_factor_scales_block_minutes_not_the_premium():
    base = {"feature_id": "f", "topic_blocks": {"alpha": 1}, "quality_target": "poc", "external_deps": ["oauth2"]}
    plain = ce.estimate_feature(base, STATS, settings(), 1.0)
    legacy = ce.estimate_feature({**base, "extra_factor": 1.2}, STATS, settings(), 1.0)
    assert plain["bands_minutes"]["median"] == pytest.approx((10 + 30) * 1.25)
    assert legacy["bands_minutes"]["median"] == pytest.approx((10 * 1.2 + 30) * 1.25)


def test_unknown_names_warn_and_fall_back():
    feature = {"feature_id": "f", "topic_blocks": {"alpha": 1, "gamma": 4}, "quality_target": "gold-plated",
               "external_deps": ["carrier_pigeon"]}
    out = ce.estimate_feature(feature, STATS, settings(), 1.0)
    assert out["quality_target"] == "demo"
    assert out["premium_minutes"] == DEFAULTS["default_external_dep_premium"]
    assert "gamma" not in out["topics"]
    assert len(out["warnings"]) == 3


def test_feature_without_known_topics_is_skipped():
    out = ce.estimate_feature({"feature_id": "f", "topic_blocks": {"gamma": 1}}, STATS, settings(), 1.0)
    assert out["skipped"] is True


def test_low_n_topic_gets_a_warning():
    out = ce.estimate_feature({"feature_id": "f", "topic_blocks": {"rare": 1}},
                              {"rare": {"n": 2, "median": 1.0, "p75": 2.0, "p95": 3.0}}, settings(), 1.0)
    assert out["buffer"] == 1.5
    assert any("N=2" in w for w in out["warnings"])


# ---------------------------------------------------------------- critical path and schedule

DIAMOND = {"a": 2.0, "b": 5.0, "c": 1.0, "d": 3.0}
DIAMOND_DEPS = {"a": [], "b": ["a"], "c": ["a"], "d": ["b", "c"]}


def test_critical_path_is_the_longest_chain():
    length, chain = ce.critical_path(DIAMOND, DIAMOND_DEPS)
    assert length == 10.0
    assert chain == ["a", "b", "d"]


def test_schedule_with_one_slot_is_the_sum():
    makespan, _ = ce.schedule(DIAMOND, DIAMOND_DEPS, cap=1)
    assert makespan == sum(DIAMOND.values())


def test_schedule_with_enough_slots_is_the_critical_path():
    makespan, timeline = ce.schedule(DIAMOND, DIAMOND_DEPS, cap=4)
    assert makespan == 10.0
    assert timeline["d"] == (7.0, 10.0)


def test_schedule_fills_free_slots():
    durations = {"a": 4.0, "b": 3.0, "c": 3.0, "d": 2.0}
    makespan, timeline = ce.schedule(durations, {k: [] for k in durations}, cap=2)
    assert timeline == {"a": (0.0, 4.0), "b": (0.0, 3.0), "c": (3.0, 6.0), "d": (4.0, 6.0)}
    assert makespan == 6.0


def test_schedule_starts_the_critical_chain_first():
    # a -> x is the long chain. Waiting for b and c before x starts would cost 16; the list schedule takes 11.
    durations = {"a": 1.0, "x": 10.0, "b": 5.0, "c": 5.0}
    deps = {"a": [], "x": ["a"], "b": [], "c": []}
    makespan, timeline = ce.schedule(durations, deps, cap=2)
    assert makespan == 11.0
    assert timeline["x"] == (1.0, 11.0)


def test_cycle_is_an_error():
    with pytest.raises(ValueError, match="cycle"):
        ce.critical_path({"a": 1.0, "b": 1.0}, {"a": ["b"], "b": ["a"]})


def test_schedule_rejects_a_zero_cap():
    with pytest.raises(ValueError):
        ce.schedule({"a": 1.0}, {"a": []}, cap=0)


def test_plan_sums_effort_and_ignores_unknown_dependencies():
    features = [
        ce.estimate_feature({"feature_id": "one", "topic_blocks": {"alpha": 1}, "quality_target": "poc"}, STATS, settings(), 1.0),
        ce.estimate_feature({"feature_id": "two", "topic_blocks": {"alpha": 1}, "quality_target": "poc",
                             "dependencies": ["one", "missing"]}, STATS, settings(), 1.0),
    ]
    totals = ce.plan(features, parallel_cap=3)
    assert totals["effort_minutes"]["median"] == pytest.approx(2 * 10 * 1.25)
    assert totals["critical_path"]["median"] == ["one", "two"]
    assert totals["wall_clock_minutes"]["median"] == pytest.approx(2 * 10 * 1.25)
    assert any("missing" in w for w in totals["warnings"])


def test_duplicate_feature_ids_are_refused(tmp_path):
    table = write_table(tmp_path / "t.md", {"alpha": (20, 10.0, 20.0, 40.0)})
    specs = [{"feature_id": "x", "topic_blocks": {"alpha": 1}}, {"feature_id": "x", "topic_blocks": {"alpha": 2}}]
    with pytest.raises(ValueError, match="duplicate"):
        ce.build_record(specs, ce.parse_benchmarks(table), settings(), table, False, "p", 1.0, 2, None)


# ---------------------------------------------------------------- command line and config

def test_cli_writes_report_and_record(tmp_path):
    table = write_table(tmp_path / "mine.md", {"alpha": (20, 10.0, 20.0, 40.0), "beta": (8, 5.0, 10.0, 30.0)})
    specs = tmp_path / "features.json"
    specs.write_text(json.dumps([
        {"feature_id": "schema", "topic_blocks": {"alpha": 2}},
        {"feature_id": "api", "topic_blocks": {"beta": 3}, "dependencies": ["schema"]},
        {"feature_id": "ui", "topic_blocks": {"alpha": 1}, "dependencies": ["schema"]},
    ]))
    report, record = tmp_path / "out.md", tmp_path / "out.json"
    rc = ce.main(["--features", str(specs), "--benchmarks", str(table), "--parallel-cap", "2",
                  "--hours-per-week", "30", "--output", str(report), "--json-out", str(record)])
    assert rc == 0
    text = report.read_text()
    assert "**Effort**" in text and "Critical path" in text and "Calendar at 30" in text
    assert "example measurements" not in text
    data = json.loads(record.read_text())
    assert data["schema"] == "estimator.estimate/1"
    assert data["meta"]["benchmarks"]["example"] is False
    assert data["totals"]["critical_path"]["median"][0] == "schema"


def test_cli_falls_back_to_the_example_and_says_so(tmp_path, capsys):
    specs = tmp_path / "features.json"
    specs.write_text(json.dumps([{"feature_id": "f", "topic_blocks": {"python_test": 2}}]))
    rc = ce.main(["--features", str(specs), "--output", str(tmp_path / "r.md")])
    assert rc == 0
    assert "example" in capsys.readouterr().err
    assert "example measurements" in (tmp_path / "r.md").read_text()
    assert json.loads((tmp_path / "r.estimate.json").read_text())["meta"]["benchmarks"]["example"] is True


def test_cli_never_overwrites_the_features_file(tmp_path):
    specs = tmp_path / "plan.json"
    original = json.dumps([{"feature_id": "f", "topic_blocks": {"python_test": 2}}])
    specs.write_text(original)
    assert ce.main(["--features", str(specs), "--output", str(tmp_path / "plan.md"), "--json-out", str(specs)]) == 2
    assert specs.read_text() == original


def test_config_file_merges_per_key(isolated_env):
    config = isolated_env / ".claude" / "estimator" / "config.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({"overhead": 1.1, "quality_factors": {"demo": 2.0}, "no_such_key": 1}))
    s = load_settings()
    assert s["overhead"] == 1.1
    assert s["quality_factors"] == {"poc": 1.0, "demo": 2.0, "production-ready": 2.2}
    assert "no_such_key" not in s
