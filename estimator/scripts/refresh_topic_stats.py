#!/usr/bin/env python3
"""Mine your Claude Code transcripts into work blocks and write your own topic-statistics table.

Reads every transcript under ~/.claude/projects (or the folders you pass), cuts it into work blocks
(see workblocks.py), keeps them in a block store, and writes a markdown table with N, median, p25,
p75 and p95 minutes per topic. compute_estimate.py reads that table.

Incremental: the state file remembers the size of each transcript it read. Only a transcript whose
size changed is read again, and its blocks replace the ones it had. Blocks of a transcript that has
since been deleted stay in the store, so the store is the durable record. Changing --mode or
--gap-min rebuilds the store, because the blocks depend on them.

Filters (--path, --since, --until, --skip-subagents) select which stored blocks go into the output.
A filtered run does not overwrite your main table unless you pass --out: use it with --summary-json
to measure what one finished feature actually took (see calibrate.py).

Usage:
  refresh_topic_stats.py                          # update the store, rewrite the table
  refresh_topic_stats.py --mode turn              # prompt-to-stop blocks instead of gap blocks
  refresh_topic_stats.py --path ~/work/app --since 2026-10-01 --until 2026-10-14 \\
      --summary-json actual.json                  # what one feature took, per topic
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import sys
import tempfile
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from estimator_config import claude_projects_dir, estimator_home, load_settings  # noqa: E402
from workblocks import Classifier, blocks_of_transcript, parse_ts  # noqa: E402

MIN_LINES_FOR_RATE = 5  # a block with fewer changed lines says nothing about minutes per line
TABLE_HEADER = "| Topic | N blocks | Median min | Mean min | p25 | p75 | p95 | Mean tool-calls | Mean errors | Total hours | Median lines | Min per 100 lines |"


def percentile(sorted_values: list[float], p: float) -> float:
    """Percentile with linear interpolation between closest ranks, 0 <= p <= 100."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    k = (len(sorted_values) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


def write_atomic(path: Path, text: str) -> None:
    """Write via a temp file in the same folder, then rename, so a crash never leaves half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(text)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def find_transcripts(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if root.is_dir():
            files.extend(p for p in root.rglob("*.jsonl") if p.is_file())
    return sorted(files)


def _load_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return default


def _load_store(path: Path) -> dict[str, list[dict]]:
    by_file: dict[str, list[dict]] = defaultdict(list)
    if not path.exists():
        return by_file
    with path.open() as fh:
        for line in fh:
            try:
                block = json.loads(line)
            except json.JSONDecodeError:
                continue
            by_file[block.get("source_file", "")].append(block)
    return by_file


def refresh(roots: list[Path], data_dir: Path, classifier: Classifier, mode: str, gap_minutes: float) -> tuple[int, int, list[dict]]:
    """(transcripts read, transcripts unchanged, every stored block). Updates store and state."""
    store_path, state_path = data_dir / "work-blocks.jsonl", data_dir / "refresh-state.json"
    settings = {"mode": mode, "gap_minutes": gap_minutes}
    state = _load_json(state_path, {})
    if state.get("settings") != settings:
        state, by_file = {"settings": settings, "files": {}}, defaultdict(list)
    else:
        by_file = _load_store(store_path)
    files: dict[str, int] = state.setdefault("files", {})
    read = unchanged = 0
    for path in find_transcripts(roots):
        key, size = str(path), path.stat().st_size
        if files.get(key) == size:
            unchanged += 1
            continue
        try:
            by_file[key] = blocks_of_transcript(path, classifier, mode, gap_minutes)
        except OSError as exc:
            print(f"WARN: {path}: {exc}", file=sys.stderr)
            continue
        files[key] = size
        read += 1
    blocks = [b for file_blocks in by_file.values() for b in file_blocks]
    write_atomic(store_path, "".join(json.dumps(b, ensure_ascii=False) + "\n" for b in blocks))
    write_atomic(state_path, json.dumps(state, indent=0, sort_keys=True))
    return read, unchanged, blocks


def _day(value: Optional[str]) -> Optional[date]:
    return date.fromisoformat(value) if value else None


def select_blocks(blocks: list[dict], min_minutes: float, path_prefix: Optional[str] = None,
                  since: Optional[date] = None, until: Optional[date] = None,
                  skip_subagents: bool = False) -> list[dict]:
    """Blocks that pass the filters; a block seen twice (same session and start) counts once."""
    seen: set[tuple[str, str]] = set()
    selected: list[dict] = []
    for b in blocks:
        key = (b.get("session", ""), b.get("start_ts", ""))
        if key in seen or b.get("wall_clock_minutes", 0) < min_minutes:
            continue
        if skip_subagents and b.get("subagent"):
            continue
        if path_prefix and not str(b.get("cwd", "")).startswith(path_prefix):
            continue
        if since or until:
            started = parse_ts(b["start_ts"]).astimezone(timezone.utc).date()
            if (since and started < since) or (until and started > until):
                continue
        seen.add(key)
        selected.append(b)
    return selected


def topic_rows(blocks: list[dict]) -> list[dict]:
    """One statistics row per topic, most blocks first."""
    by_topic: dict[str, list[dict]] = defaultdict(list)
    for b in blocks:
        by_topic[b["topic"]].append(b)
    rows = []
    for topic, items in sorted(by_topic.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        durations = sorted(b["wall_clock_minutes"] for b in items)
        changed = [(b.get("lines_added") or 0) + (b.get("lines_removed") or 0) for b in items]
        with_lines = [c for c in changed if c > 0]
        rates = [b["wall_clock_minutes"] / c * 100 for b, c in zip(items, changed) if c >= MIN_LINES_FOR_RATE]
        rows.append({
            "topic": topic,
            "n": len(items),
            "median": statistics.median(durations),
            "mean": statistics.mean(durations),
            "p25": percentile(durations, 25),
            "p75": percentile(durations, 75),
            "p95": percentile(durations, 95),
            "mean_tools": statistics.mean(b.get("tool_call_count") or 0 for b in items),
            "mean_errors": statistics.mean(b.get("error_count") or 0 for b in items),
            "total_minutes": sum(durations),
            "median_lines": statistics.median(with_lines) if with_lines else None,
            "min_per_100_lines": statistics.median(rates) if rates else None,
            "blocks": items,
        })
    return rows


def _label(cwd: str) -> str:
    home = str(Path.home())
    return ("~" + cwd[len(home):]) if cwd.startswith(home) else (cwd or "?")


def render_table(rows: list[dict], header: dict, notes: Optional[str], examples: int) -> str:
    lines = [
        "# Topic statistics: my Claude Code work blocks",
        "",
        f"Generated {header['generated']} by refresh_topic_stats.py. Mode `{header['mode']}`, gap {header['gap_minutes']} min, "
        f"blocks shorter than {header['min_block_minutes']} min excluded. {header['blocks']} blocks.",
    ]
    if header.get("filters"):
        lines.append(f"Filters: {header['filters']}.")
    lines += [
        "",
        "## Per-topic distribution (minutes per work block)",
        "",
        TABLE_HEADER,
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        med_lines = f"{r['median_lines']:.0f}" if r["median_lines"] is not None else "-"
        rate = f"{r['min_per_100_lines']:.1f}" if r["min_per_100_lines"] is not None else "-"
        lines.append(
            f"| {r['topic']} | {r['n']} | {r['median']:.2f} | {r['mean']:.2f} | {r['p25']:.2f} | {r['p75']:.2f} | {r['p95']:.2f} | "
            f"{r['mean_tools']:.1f} | {r['mean_errors']:.2f} | {r['total_minutes'] / 60:.1f} | {med_lines} | {rate} |"
        )
    if notes:
        lines += ["", notes.rstrip()]
    if examples > 0:
        lines += ["", "## Longest blocks per topic", "",
                  "Read these before you trust a p95: a long tail is often a misclassified or idle-heavy block.", ""]
        for r in rows:
            lines.append(f"### {r['topic']}")
            lines.append("")
            for b in sorted(r["blocks"], key=lambda x: -x["wall_clock_minutes"])[:examples]:
                lines.append(
                    f"- {b['wall_clock_minutes']:.1f} min, `{_label(b.get('cwd', ''))}`, session `{b['session'][:8]}`, "
                    f"start {b['start_ts'][:16]}, {b.get('tool_call_count', 0)} tool calls, {b.get('error_count', 0)} errors"
                )
            lines.append("")
    lines += [
        "## How to read this table",
        "",
        "- Minutes are time inside Claude Code sessions with idle left out. Thinking offline, meetings and reviews are not in it.",
        "- The mean sits above the median because block times are right-skewed. A feature of many blocks totals close to blocks x mean, not blocks x median.",
        "- A p95 more than three times the median signals a long tail: first-time work, debugging spirals or misclassified blocks.",
        "- The classifier is rule-based. Spot-check a sample of blocks before you trust a topic.",
        f"- Lines come from Edit, MultiEdit and Write calls, generated files excluded; edits through Bash are not counted. "
        f"*Min per 100 lines* is the median over blocks with at least {MIN_LINES_FOR_RATE} changed lines: a sanity check, not an estimate input.",
        "",
    ]
    return "\n".join(lines)


def summary(rows: list[dict], header: dict) -> dict:
    """Per-topic actuals for calibrate.py: blocks, minutes and median minutes per block."""
    return {
        "schema": "estimator.actual/1",
        "generated": header["generated"],
        "mode": header["mode"],
        "gap_minutes": header["gap_minutes"],
        "min_block_minutes": header["min_block_minutes"],
        "filters": header.get("filters", ""),
        "blocks": sum(r["n"] for r in rows),
        "minutes": round(sum(r["total_minutes"] for r in rows), 2),
        "topics": {
            r["topic"]: {"blocks": r["n"], "minutes": round(r["total_minutes"], 2), "median": round(r["median"], 2)}
            for r in rows
        },
    }


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Turn your Claude Code transcripts into a topic-statistics table.")
    ap.add_argument("--projects", type=Path, nargs="+", help="transcript folders (default: ~/.claude/projects)")
    ap.add_argument("--data-dir", type=Path, help="block store and table folder (default: $ESTIMATOR_HOME or ~/.claude/estimator)")
    ap.add_argument("--config", type=Path, help="config file with overrides")
    ap.add_argument("--mode", choices=("gap", "turn"), help="gap blocks or prompt-to-stop turn blocks")
    ap.add_argument("--gap-min", type=float, help="pause in minutes that ends a block")
    ap.add_argument("--min-block-min", type=float, help="leave out blocks shorter than this many minutes")
    ap.add_argument("--path", help="only blocks whose working directory starts with this path")
    ap.add_argument("--since", help="only blocks that start on or after this UTC date (YYYY-MM-DD)")
    ap.add_argument("--until", help="only blocks that start on or before this UTC date (YYYY-MM-DD)")
    ap.add_argument("--skip-subagents", action="store_true", help="leave out subagent transcripts (they overlap the parent session)")
    ap.add_argument("--out", type=Path, help="table to write (default: <data-dir>/topic-statistics.md; a filtered run needs --out)")
    ap.add_argument("--summary-json", type=Path, help="also write per-topic actuals as JSON, for calibrate.py")
    ap.add_argument("--snapshot", action="store_true", help="also keep a dated copy of the table under <data-dir>/snapshots/")
    ap.add_argument("--examples", type=int, default=3, help="longest blocks listed per topic (0 leaves the section out)")
    ap.add_argument("--no-table", action="store_true", help="only update the block store")
    args = ap.parse_args(argv)

    settings = load_settings(args.config)
    data_dir = (args.data_dir or estimator_home()).expanduser()
    mode = args.mode or settings["mode"]
    gap = float(args.gap_min if args.gap_min is not None else settings["gap_minutes"])
    min_block = float(args.min_block_min if args.min_block_min is not None else settings["min_block_minutes"])
    roots = [p.expanduser() for p in (args.projects or [claude_projects_dir()])]
    classifier = Classifier(settings.get("topic_rules"), settings.get("tool_topics"))

    read, unchanged, stored = refresh(roots, data_dir, classifier, mode, gap)
    path_prefix = str(Path(args.path).expanduser().resolve()) if args.path else None
    filters = ", ".join(f for f in (
        f"path {path_prefix}" if path_prefix else "",
        f"since {args.since}" if args.since else "",
        f"until {args.until}" if args.until else "",
        "subagents skipped" if args.skip_subagents else "",
    ) if f)
    selected = select_blocks(stored, min_block, path_prefix, _day(args.since), _day(args.until), args.skip_subagents)
    print(f"transcripts read: {read}, unchanged: {unchanged}, blocks in store: {len(stored)}, blocks selected: {len(selected)}")

    rows = topic_rows(selected)
    header = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "mode": mode, "gap_minutes": gap, "min_block_minutes": min_block,
        "blocks": len(selected), "filters": filters,
    }
    if args.summary_json:
        write_atomic(args.summary_json.expanduser(), json.dumps(summary(rows, header), indent=2) + "\n")
        print(f"wrote {args.summary_json}")
    if args.no_table:
        return 0
    if filters and not args.out:
        print("filtered run: table not written (pass --out to write it elsewhere)")
        return 0
    out = (args.out or data_dir / "topic-statistics.md").expanduser()
    notes_path = data_dir / "topic-statistics-notes.md"
    notes = notes_path.read_text() if notes_path.exists() else None
    write_atomic(out, render_table(rows, header, notes, args.examples))
    print(f"wrote {out}")
    if args.snapshot:
        snapshot = data_dir / "snapshots" / f"topic-statistics-{header['generated']}.md"
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(out, snapshot)
        print(f"wrote {snapshot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
