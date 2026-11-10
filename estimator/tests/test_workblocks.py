"""Block segmentation and classification in workblocks.py."""
from __future__ import annotations

import pytest

import workblocks as wb
from conftest import assistant, prompt, tool_result, write_transcript

CLASSIFIER = wb.Classifier()


def blocks(tmp_path, events, mode, gap=5.0):
    path = write_transcript(tmp_path / "projects" / "p" / "s.jsonl", events)
    return wb.blocks_of_transcript(path, CLASSIFIER, mode, gap)


def test_gap_mode_ends_a_block_at_a_long_pause(tmp_path):
    events = [prompt(0), assistant(1), assistant(2), prompt(10), assistant(11)]
    result = blocks(tmp_path, events, "gap")
    assert [b["wall_clock_minutes"] for b in result] == [2.0, 1.0]


def test_turn_mode_counts_prompt_to_stop_and_leaves_idle_out(tmp_path):
    events = [
        prompt(0), assistant(0.5), assistant(2),   # turn 1: 2 minutes
        prompt(4), assistant(5),                   # 2 minutes idle, same block; turn 2: 1 minute
        prompt(20), assistant(23),                 # 15 minutes idle: a new block
    ]
    result = blocks(tmp_path, events, "turn")
    assert [b["wall_clock_minutes"] for b in result] == [3.0, 3.0]
    gap_result = blocks(tmp_path, events, "gap")
    assert [b["wall_clock_minutes"] for b in gap_result] == [5.0, 3.0]


def test_turn_mode_keeps_a_long_tool_wait_inside_the_turn(tmp_path):
    events = [prompt(0), assistant(0.5, tool="Bash", tool_input={"command": "make test"}),
              tool_result(9), assistant(9.5)]
    assert [b["wall_clock_minutes"] for b in blocks(tmp_path, events, "turn")] == [9.5]
    assert [b["wall_clock_minutes"] for b in blocks(tmp_path, events, "gap")] == [0.5, 0.5]


def test_sessions_are_cut_separately(tmp_path):
    events = [prompt(0, session="a"), assistant(2, session="a"), prompt(1, session="b"), assistant(4, session="b")]
    result = sorted(blocks(tmp_path, events, "gap"), key=lambda b: b["session"])
    assert [(b["session"], b["wall_clock_minutes"]) for b in result] == [("a", 2.0), ("b", 3.0)]


def test_dominant_topic_leaves_out_reading():
    def ev(topic):
        return {"topic": topic, "cwd": "/w", "ts": "2026-10-01T09:00:00Z", "tool_calls_count": 0, "has_error": False,
                "lines_added": 0, "lines_removed": 0, "model": "", "sidechain": False}
    group = [ev("analysis_only")] * 5 + [ev("python_test")] * 2 + [ev("documentation")]
    assert wb.make_block("s", group, 3.0)["topic"] == "python_test"
    assert wb.make_block("s", [ev("analysis_only")], 1.0)["topic"] == "analysis_only"


def meta(**kw):
    base = {"tool_names": [], "file_paths": [], "text_summary": "", "has_error": False}
    base.update(kw)
    return base


@pytest.mark.parametrize("fields, topic", [
    ({"file_paths": ["/w/tests/test_parser.py"]}, "python_test"),
    ({"file_paths": ["/w/app/components/Card.tsx"]}, "frontend_work"),
    ({"tool_names": ["mcp__mydb__apply_migration"]}, "database_setup"),
    ({"tool_names": ["mcp__mydb__execute_sql"], "file_paths": ["/w/tests/test_x.py"]}, "database_query"),
    ({"text_summary": "CREATE TABLE users (id int)"}, "database_setup"),
    ({"file_paths": ["/w/src/service.py"]}, "python_module"),
    ({"text_summary": "Traceback (most recent call last)", "has_error": True}, "bug_fix"),
    ({}, "analysis_only"),
])
def test_default_rules(fields, topic):
    assert CLASSIFIER.classify(meta(**fields)) == topic


def test_rules_can_be_replaced():
    custom = wb.Classifier(topic_rules=[["go_service", r"\.go$"]], tool_topics=[])
    assert custom.classify(meta(file_paths=["/w/cmd/main.go"])) == "go_service"
    assert custom.classify(meta(file_paths=["/w/src/service.py"])) == "analysis_only"


def test_is_prompt():
    assert wb.is_prompt(prompt(0))
    assert not wb.is_prompt(tool_result(0))
    assert not wb.is_prompt({**prompt(0), "isMeta": True})
    assert wb.is_prompt({"type": "user", "message": {"content": [{"type": "text", "text": "hi"}]}})
    assert not wb.is_prompt(assistant(0))


def test_edit_line_counts():
    assert wb.edit_line_counts("Edit", {"file_path": "/w/a.py", "old_string": "a\nb\nc", "new_string": "a\nB\nc"}) == (1, 1)
    assert wb.edit_line_counts("Write", {"file_path": "/w/a.py", "content": "1\n2\n3\n"}) == (3, 0)
    assert wb.edit_line_counts("Write", {"file_path": "/w/package-lock.json", "content": "x\n" * 500}) == (0, 0)
    assert wb.edit_line_counts("Read", {"file_path": "/w/a.py"}) == (0, 0)


def test_block_carries_lines_and_cwd(tmp_path):
    events = [prompt(0, cwd="/work/app"),
              assistant(1, cwd="/work/app", tool="Write", tool_input={"file_path": "/work/app/src/m.py", "content": "a\nb\n"})]
    (block,) = blocks(tmp_path, events, "gap")
    assert block["cwd"] == "/work/app"
    assert block["lines_added"] == 2
    assert block["topic"] == "python_module"


def test_unknown_mode_is_an_error():
    with pytest.raises(ValueError):
        wb.blocks_from_events([], "hourly", 5.0)
