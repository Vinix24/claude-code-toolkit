"""Every number in the worked examples is what the scripts compute today."""
from __future__ import annotations

import json

import compute_estimate as ce
from conftest import PKG
from estimator_config import DEFAULTS, merge_settings

EXAMPLES_DOC = (PKG / "docs" / "examples.md").read_text()
TABLE = PKG / "benchmarks.example.md"


def record(name: str, cap: int = 3) -> dict:
    specs = json.loads((PKG / "examples" / f"{name}.features.json").read_text())
    return ce.build_record(specs, ce.parse_benchmarks(TABLE), merge_settings(DEFAULTS, {}), TABLE, True,
                           name, DEFAULTS["overhead"], cap, None)


def hours(minutes: float) -> str:
    return f"{minutes / 60:.1f}"


def test_examples_page_repeats_the_example_table(tmp_path):
    first_table = EXAMPLES_DOC.split("## Minutes per work block", 1)[1].split("## Small samples lie", 1)[0]
    page = tmp_path / "page.md"
    page.write_text(first_table)
    assert ce.parse_benchmarks(page) == ce.parse_benchmarks(TABLE)


def test_worked_estimate_one():
    feature = record("pdf-extractor")["features"][0]
    raw, bands = feature["raw_block_minutes"], feature["bands_minutes"]
    assert f"| {raw['median']:.2f} | {raw['p75']:.2f} | {raw['p95']:.2f} |" in EXAMPLES_DOC
    assert f"| {bands['median']:.2f} | {bands['p75']:.2f} | {bands['p95']:.2f} |" in EXAMPLES_DOC
    assert f"| **{hours(bands['median'])}** | **{hours(bands['p75'])}** | **{hours(bands['p95'])}** |" in EXAMPLES_DOC
    assert f"lowest N is {feature['min_topic_n']}" in EXAMPLES_DOC


def test_worked_estimate_two_per_feature():
    for f in record("knowledge-base")["features"]:
        b = f["bands_minutes"]
        row = f"| {f['min_topic_n']} | {hours(b['median'])} | {hours(b['p75'])} | {hours(b['p95'])} |"
        assert f"| `{f['feature_id']}` |" in EXAMPLES_DOC
        assert row in EXAMPLES_DOC, f["feature_id"]


def test_worked_estimate_two_totals():
    def cells(values):
        return " | ".join(hours(values[b]) for b in ce.BANDS)

    three = record("knowledge-base", 3)["totals"]
    assert f"| Effort (sum of all features) | {cells(three['effort_minutes'])} |" in EXAMPLES_DOC
    assert f"| {cells(three['critical_path_minutes'])} |" in EXAMPLES_DOC
    assert " > ".join(three["critical_path"]["median"]) in EXAMPLES_DOC
    for cap, label in ((1, "one feature at a time"), (2, "at most two at once"), (3, "at most three at once")):
        wall = record("knowledge-base", cap)["totals"]["wall_clock_minutes"]
        assert f"| Wall-clock, {label} | {cells(wall)} |" in EXAMPLES_DOC
    ratio = three["effort_minutes"]["median"] / three["wall_clock_minutes"]["median"]
    assert f"differ by {ratio:.2f} times" in EXAMPLES_DOC


def test_level_by_level_comparison():
    rec = record("knowledge-base")
    minutes = {f["feature_id"]: f["bands_minutes"]["median"] for f in rec["features"]}
    levels = [["schema"], ["connector-oauth", "connector-files", "embedding"], ["retrieval-server"],
              ["eval-loop", "dashboard"], ["deploy"]]
    by_level = sum(max(minutes[f] for f in level) for level in levels)
    assert f"gives {hours(by_level)} hours on the median band against {hours(rec['totals']['wall_clock_minutes']['median'])}" in EXAMPLES_DOC
