"""Turn Claude Code transcripts into classified work blocks.

Claude Code writes one JSONL transcript per session under ~/.claude/projects/<encoded-cwd>/.
Every user and assistant line becomes an event with a topic. Events become work blocks.

Two ways to cut blocks. Both leave idle time out.

  gap   A block ends at every pause longer than gap_minutes between two events.
        Duration = last event - first event. This is the method behind benchmarks.example.md.
  turn  Prompt-to-stop. A turn runs from a prompt to the last event before the next prompt.
        Turns with at most gap_minutes of idle between them form one block, and the block's
        duration is the sum of its turns, so that idle is not counted either. This is the
        definition timekeeper uses for active time. A wait inside a turn counts, however long, unless
        max_wait_minutes is set: then a longer pause inside a turn (a permission prompt left open
        overnight, a laptop asleep mid-turn) is left out as well.

A block's topic is the most frequent topic among its events, leaving out analysis_only when any
other topic occurs: reading and searching are scaffolding around the real work.

The classifier is rule-based (regular expressions on tool names, file paths and text). No model
is called. Pure standard library.
"""
from __future__ import annotations

import difflib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

# Topic rules, applied in this order: the first pattern that matches wins.
DEFAULT_TOPIC_RULES: list[tuple[str, str]] = [
    ("database_setup", r"(supabase/migrations/|migrations/\d+|CREATE\s+TABLE|ALTER\s+TABLE|CREATE\s+SCHEMA|CREATE\s+INDEX|apply_migration|DROP\s+TABLE|CREATE\s+EXTENSION)"),
    ("database_query", r"(execute_sql|\bSELECT\s+.*FROM\b|\bINSERT\s+INTO\b|\bUPDATE\s+\w+\s+SET\b|\bDELETE\s+FROM\b|pg_dump|\bWITH\s+\w+\s+AS\b)"),
    ("python_test", r"(/tests?/[^/]*test_\w+\.py|test_\w+\.py$|/tests?/conftest\.py|pytest|unittest|/test/)"),
    ("frontend_work", r"(\.tsx$|\.jsx$|/components/[^/]+\.(tsx|jsx|ts)|next\.config|app/\w+/page\.tsx|/pages/[^/]+\.tsx|/styles/.*\.css)"),
    ("parser_work", r"(extract.?msg|pypdf|PyMuPDF|fitz|openpyxl|pandas\.read_(excel|csv)|BeautifulSoup|bs4|html\.parser|pdftotext|tesseract|pytesseract|mailparser|transcript)"),
    ("api_integration", r"(requests\.(get|post|put|delete)|httpx\.(get|post|put|delete|AsyncClient)|aiohttp\.|fetch\(|axios\.|/api/v\d|graphql_url|webhook|/oauth/|access_token|bearer\s|x-api-key)"),
    ("data_cleaning", r"(deduplica|dedup|normalize|sanitize|pii.?redact|langdetect|detect_language|strip_html|cleanup_text|drop_duplicates|fillna|merge_records)"),
    ("deployment", r"(\.github/workflows/|github/actions|Dockerfile|docker-compose|vercel\.json|netlify\.toml|fly\.toml|deploy\.sh|kubectl|terraform|/ci/|/cd/|pipeline\.ya?ml)"),
    ("documentation", r"(README\.md|CHANGELOG|/docs/|\.md$|CONTRIBUTING)"),
    ("python_module", r"(\.py$|/scripts/\w+\.py|/src/.*\.py)"),
]

# Tool-name rules, checked before the topic rules: a database tool says more than any path.
DEFAULT_TOOL_TOPICS: list[tuple[str, str]] = [
    (r"^mcp__.+__apply_migration$", "database_setup"),
    (r"^mcp__.+__(execute_sql|list_tables)$", "database_query"),
]

ERROR_RE = re.compile(r"(Traceback|Error:|FAILED|ModuleNotFoundError|SyntaxError|ImportError|TypeError|ValueError|FileNotFoundError|connection refused|insufficient_quota|RateLimitError|permission denied)", re.I)
# Generated or bulk files: their size says nothing about the work, so their lines are not counted.
GENERATED_RE = re.compile(r"(\.lock$|package-lock\.json$|/goldens?/|/snapshots?/|\.snap$|CHANGELOG\.md$|\.junit\.xml$|/fixtures/.*\.(jsonl?|txt|html)$)", re.I)
COMMAND_PATH_RE = re.compile(r"(?:^|[\s\"'=])((?:~|/)[^\s\"'|;&<>()]+)")
DIFF_LINE_CAP = 2000  # above this, count raw lines instead of a line diff (SequenceMatcher is quadratic)


class Classifier:
    """Rule-based topic classifier. Rules can be replaced through the config file."""

    def __init__(self, topic_rules: Optional[Iterable] = None, tool_topics: Optional[Iterable] = None):
        rules = DEFAULT_TOPIC_RULES if topic_rules is None else [tuple(r) for r in topic_rules]
        tools = DEFAULT_TOOL_TOPICS if tool_topics is None else [tuple(r) for r in tool_topics]
        self.topic_rules = [(topic, re.compile(pattern, re.I)) for topic, pattern in rules]
        self.tool_topics = [(re.compile(pattern), topic) for pattern, topic in tools]

    def classify(self, meta: dict) -> str:
        for name in meta["tool_names"]:
            for pattern, topic in self.tool_topics:
                if pattern.search(name):
                    return topic
        combined = " ".join(meta["file_paths"]) + "\n" + meta["text_summary"]
        for topic, pattern in self.topic_rules:
            if pattern.search(combined):
                return topic
        if meta["has_error"]:
            return "bug_fix"
        return "analysis_only"


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _diff_counts(old: str, new: str) -> tuple[int, int]:
    """Lines added and removed between two strings, as a line diff (unchanged lines do not count)."""
    a, b = old.splitlines(), new.splitlines()
    if len(a) > DIFF_LINE_CAP or len(b) > DIFF_LINE_CAP:
        return len(b), len(a)
    added = removed = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag in ("replace", "delete"):
            removed += i2 - i1
        if tag in ("replace", "insert"):
            added += j2 - j1
    return added, removed


def edit_line_counts(name: str, inp: dict) -> tuple[int, int]:
    """(lines added, lines removed) of one Edit, MultiEdit or Write call; (0, 0) for anything else.

    Write counts its whole content as added: the transcript does not hold the file it replaced.
    Edits made through Bash (sed, heredocs) are invisible here.
    """
    path = inp.get("file_path")
    if not isinstance(path, str) or GENERATED_RE.search(path):
        return 0, 0
    if name == "Edit":
        return _diff_counts(str(inp.get("old_string") or ""), str(inp.get("new_string") or ""))
    if name == "MultiEdit":
        added = removed = 0
        for edit in inp.get("edits") or []:
            if isinstance(edit, dict):
                a, r = _diff_counts(str(edit.get("old_string") or ""), str(edit.get("new_string") or ""))
                added, removed = added + a, removed + r
        return added, removed
    if name == "Write":
        return len(str(inp.get("content") or "").splitlines()), 0
    return 0, 0


def is_prompt(ev: dict) -> bool:
    """True for a line that opens a turn: any user content that is not a tool result.

    That includes lines Claude Code marks isMeta. Turns started by the system (a scheduled wake-up,
    a finished background task, a message from another session) are written that way, and skipping
    them would glue the idle before them onto the previous turn.
    """
    if ev.get("type") != "user":
        return False
    content = (ev.get("message") or {}).get("content")
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, list):
        kinds = {b.get("type") for b in content if isinstance(b, dict)}
        return "tool_result" not in kinds and bool(kinds & {"text", "image"})
    return False


def extract_event_meta(ev: dict) -> dict:
    """The parts of one transcript line the classifier and the block statistics need."""
    out = {
        "ts": ev.get("timestamp"),
        "type": ev.get("type"),
        "session": ev.get("sessionId") or ev.get("session_id") or "",
        "cwd": ev.get("cwd") or "",
        "sidechain": bool(ev.get("isSidechain")),
        "is_prompt": is_prompt(ev),
        "tool_calls_count": 0,
        "tool_names": [],
        "file_paths": [],
        "text_summary": "",
        "model": "",
        "has_error": False,
        "lines_added": 0,
        "lines_removed": 0,
    }
    msg = ev.get("message")
    if not isinstance(msg, dict):
        return out
    out["model"] = msg.get("model", "") or ""
    content = msg.get("content")
    text_parts: list[str] = []
    if isinstance(content, str):
        text_parts.append(content[:1000])
    elif isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            kind = block.get("type")
            if kind == "text":
                text_parts.append(str(block.get("text", ""))[:600])
            elif kind == "tool_use":
                name = block.get("name", "")
                out["tool_names"].append(name)
                out["tool_calls_count"] += 1
                inp = block.get("input", {})
                if not isinstance(inp, dict):
                    continue
                added, removed = edit_line_counts(name, inp)
                out["lines_added"] += added
                out["lines_removed"] += removed
                for key, value in inp.items():
                    if not isinstance(value, str):
                        continue
                    if key in ("file_path", "path", "notebook_path"):
                        out["file_paths"].append(value)
                    elif key == "command":
                        out["file_paths"].extend(m.group(1) for m in COMMAND_PATH_RE.finditer(value))
                        text_parts.append(value[:600])
                    elif key in ("query", "old_string", "new_string", "content"):
                        text_parts.append(value[:300])
                    elif key == "pattern":
                        text_parts.append(value[:200])
            elif kind == "tool_result":
                result = block.get("content", "")
                if isinstance(result, str):
                    text_parts.append(result[:500])
                elif isinstance(result, list):
                    for sub in result:
                        if isinstance(sub, dict) and sub.get("type") == "text":
                            text_parts.append(str(sub.get("text", ""))[:500])
    out["text_summary"] = "\n".join(text_parts)[:3000]
    out["has_error"] = bool(ERROR_RE.search(out["text_summary"]))
    return out


def _minutes(start: datetime, end: datetime) -> float:
    return (end - start).total_seconds() / 60.0


def segment_gap(events: list[dict], gap_minutes: float, max_wait: Optional[float] = None) -> list[tuple[list[dict], float]]:
    """Split time-ordered events at every pause longer than gap_minutes."""
    groups: list[list[dict]] = []
    current: list[dict] = []
    last: Optional[datetime] = None
    for ev in events:
        ts = ev["_dt"]
        if last is not None and _minutes(last, ts) > gap_minutes:
            groups.append(current)
            current = []
        current.append(ev)
        last = ts
    if current:
        groups.append(current)
    return [(g, _minutes(g[0]["_dt"], g[-1]["_dt"])) for g in groups]


def _turn_minutes(turn: list[dict], max_wait: Optional[float]) -> float:
    if max_wait is None:
        return _minutes(turn[0]["_dt"], turn[-1]["_dt"])
    steps = (_minutes(a["_dt"], b["_dt"]) for a, b in zip(turn, turn[1:]))
    return sum(step for step in steps if step <= max_wait)


def segment_turns(events: list[dict], gap_minutes: float, max_wait: Optional[float] = None) -> list[tuple[list[dict], float]]:
    """Prompt-to-stop turns, merged into blocks when the idle between two turns is at most gap_minutes."""
    turns: list[list[dict]] = []
    for ev in events:
        if ev["is_prompt"] or not turns:
            turns.append([ev])
        else:
            turns[-1].append(ev)
    blocks: list[tuple[list[dict], float]] = []
    current: list[dict] = []
    active = 0.0
    previous_end: Optional[datetime] = None
    for turn in turns:
        start, end = turn[0]["_dt"], turn[-1]["_dt"]
        if previous_end is not None and _minutes(previous_end, start) > gap_minutes:
            blocks.append((current, active))
            current, active = [], 0.0
        current.extend(turn)
        active += _turn_minutes(turn, max_wait)
        previous_end = end
    if current:
        blocks.append((current, active))
    return blocks


def make_block(session: str, group: list[dict], minutes: float) -> dict:
    """One work block from a time-ordered run of events of one session."""
    topic_counts: Counter = Counter(e["topic"] for e in group)
    working = Counter({t: c for t, c in topic_counts.items() if t != "analysis_only"})
    dominant = (working or topic_counts).most_common(1)[0][0]
    cwd = next((e["cwd"] for e in group if e["cwd"]), "")
    return {
        "topic": dominant,
        "cwd": cwd,
        "session": session,
        "start_ts": group[0]["ts"],
        "end_ts": group[-1]["ts"],
        "wall_clock_minutes": round(minutes, 2),
        "event_count": len(group),
        "tool_call_count": sum(e["tool_calls_count"] for e in group),
        "error_count": sum(1 for e in group if e["has_error"]),
        "lines_added": sum(e["lines_added"] for e in group),
        "lines_removed": sum(e["lines_removed"] for e in group),
        "topic_mix": dict(topic_counts),
        "models": sorted({e["model"] for e in group if e["model"]}),
        "subagent": any(e["sidechain"] for e in group),
    }


def blocks_from_events(events: list[dict], mode: str, gap_minutes: float, max_wait: Optional[float] = None) -> list[dict]:
    """Blocks of classified events (each with ts, topic and the meta fields), per session."""
    if mode not in ("gap", "turn"):
        raise ValueError(f"unknown mode '{mode}', expected 'gap' or 'turn'")
    segment = segment_gap if mode == "gap" else segment_turns
    by_session: dict[str, list[dict]] = defaultdict(list)
    for ev in events:
        try:
            ev["_dt"] = parse_ts(ev["ts"])
        except (KeyError, TypeError, ValueError):
            continue
        by_session[ev["session"]].append(ev)
    blocks: list[dict] = []
    for session, session_events in by_session.items():
        session_events.sort(key=lambda e: e["_dt"])
        for group, minutes in segment(session_events, gap_minutes, max_wait):
            blocks.append(make_block(session, group, minutes))
    return blocks


def events_of_transcript(path: Path, classifier: Classifier) -> list[dict]:
    """Classified user and assistant events of one transcript file."""
    events: list[dict] = []
    is_subagent_file = "subagents" in path.parts
    with path.open(errors="replace") as fh:
        for line in fh:
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(ev, dict) or not ev.get("timestamp") or ev.get("type") not in ("user", "assistant"):
                continue
            meta = extract_event_meta(ev)
            meta["session"] = meta["session"] or path.stem
            meta["sidechain"] = meta["sidechain"] or is_subagent_file
            meta["topic"] = classifier.classify(meta)
            del meta["text_summary"], meta["file_paths"], meta["tool_names"]
            events.append(meta)
    return events


def blocks_of_transcript(path: Path, classifier: Classifier, mode: str, gap_minutes: float,
                         max_wait: Optional[float] = None) -> list[dict]:
    blocks = blocks_from_events(events_of_transcript(path, classifier), mode, gap_minutes, max_wait)
    for block in blocks:
        block["source_file"] = str(path)
    return blocks
