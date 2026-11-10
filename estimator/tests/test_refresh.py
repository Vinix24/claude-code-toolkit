"""refresh_topic_stats.py end to end on a fake transcripts folder."""
from __future__ import annotations

import json

import pytest

import compute_estimate as ce
import refresh_topic_stats as rts
from conftest import assistant, prompt, write_transcript


@pytest.fixture
def projects(tmp_path):
    root = tmp_path / "projects"
    test_file = {"file_path": "/work/app/tests/test_a.py", "content": "def test_a():\n    assert True\n"}
    write_transcript(root / "-work-app" / "s1.jsonl", [
        prompt(0, "s1", "/work/app"), assistant(3, "s1", "/work/app", tool="Write", tool_input=test_file),
        prompt(30, "s1", "/work/app"), assistant(32, "s1", "/work/app", tool="Write", tool_input=test_file),
    ])
    write_transcript(root / "-work-site" / "s2.jsonl", [
        prompt(60 * 24 * 10, "s2", "/work/site"),
        assistant(60 * 24 * 10 + 4, "s2", "/work/site", tool="Edit",
                  tool_input={"file_path": "/work/site/README.md", "old_string": "a", "new_string": "b"}),
    ])
    return root


def run(projects, data_dir, *extra):
    return rts.main(["--projects", str(projects), "--data-dir", str(data_dir), *extra])


def test_writes_a_table_that_compute_estimate_reads(projects, tmp_path, capsys):
    data = tmp_path / "data"
    assert run(projects, data) == 0
    rows = ce.parse_benchmarks(data / "topic-statistics.md")
    assert rows["python_test"]["n"] == 2
    assert rows["python_test"]["median"] == pytest.approx(2.5)
    assert rows["documentation"]["n"] == 1
    assert "transcripts read: 2" in capsys.readouterr().out


def test_second_run_reads_only_changed_transcripts(projects, tmp_path, capsys):
    data = tmp_path / "data"
    run(projects, data)
    capsys.readouterr()
    run(projects, data)
    assert "transcripts read: 0, unchanged: 2" in capsys.readouterr().out
    with (projects / "-work-site" / "s2.jsonl").open("a") as fh:
        fh.write(json.dumps(assistant(60 * 24 * 10 + 5, "s2", "/work/site")) + "\n")
    run(projects, data)
    assert "transcripts read: 1, unchanged: 1" in capsys.readouterr().out


def test_changing_the_mode_rebuilds_the_store(projects, tmp_path, capsys):
    data = tmp_path / "data"
    run(projects, data)
    capsys.readouterr()
    run(projects, data, "--mode", "turn")
    assert "transcripts read: 2" in capsys.readouterr().out
    run(projects, data, "--mode", "turn", "--max-wait-min", "30")
    assert "transcripts read: 2" in capsys.readouterr().out
    run(projects, data, "--mode", "turn", "--max-wait-min", "30")
    assert "transcripts read: 0" in capsys.readouterr().out


def test_filtered_run_writes_actuals_but_not_the_main_table(projects, tmp_path, capsys):
    data = tmp_path / "data"
    actual = tmp_path / "actual.json"
    assert run(projects, data, "--path", "/work/app", "--until", "2026-10-05", "--summary-json", str(actual)) == 0
    assert not (data / "topic-statistics.md").exists()
    summary = json.loads(actual.read_text())
    assert summary["schema"] == "estimator.actual/1"
    assert summary["topics"] == {"python_test": {"blocks": 2, "minutes": 5.0, "median": 2.5}}
    assert "table not written" in capsys.readouterr().out


def test_date_filter_selects_by_block_start(projects, tmp_path):
    data = tmp_path / "data"
    actual = tmp_path / "actual.json"
    run(projects, data, "--since", "2026-10-05", "--summary-json", str(actual), "--no-table")
    assert set(json.loads(actual.read_text())["topics"]) == {"documentation"}


def test_short_blocks_are_left_out(projects, tmp_path):
    data = tmp_path / "data"
    actual = tmp_path / "actual.json"
    run(projects, data, "--min-block-min", "2.8", "--summary-json", str(actual), "--no-table")
    topics = json.loads(actual.read_text())["topics"]
    assert topics["python_test"]["blocks"] == 1
    assert topics["documentation"]["blocks"] == 1


def test_percentile_interpolates():
    assert rts.percentile([1.0, 2.0, 3.0, 4.0], 50) == 2.5
    assert rts.percentile([1.0, 2.0, 3.0, 4.0], 95) == pytest.approx(3.85)
    assert rts.percentile([7.0], 95) == 7.0
    assert rts.percentile([], 50) == 0.0
