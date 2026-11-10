#!/usr/bin/env python3
"""Hour bands and wall-clock time for a decomposed feature list, from your own benchmark table.

Input: a JSON array of feature specs (see SKILL.md, phase 2):

  {"feature_id": "pdf-extractor", "feature_name": "PDF extractor",
   "topic_blocks": {"parser_work": 3, "python_test": 4}, "external_deps": ["rest_api_key"],
   "dependencies": ["schema"], "quality_target": "production-ready", "extra_factor": 1.0}

Per feature and per band (median, p75, p95):

  minutes = (sum(blocks x topic minutes) x quality factor x extra factor + dependency premium)
            x overhead x confidence buffer

Over all features it reports three different numbers. They answer different questions:

  effort         the sum of all features: hours of work
  critical path  the longest dependency chain: the wall-clock floor, however many sessions you run
  wall-clock     a list schedule with at most --parallel-cap features at once

The benchmark table is read fresh on every run, so a refresh of your measurements feeds straight
into the next estimate. Every run also writes a JSON record of the estimate, the input for calibrate.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from estimator_config import estimator_home, load_settings, resolve_benchmarks  # noqa: E402

BANDS = ("median", "p75", "p95")
REQUIRED_COLUMNS = ("topic", "n", "median", "p75", "p95")
COLUMN_ALIASES = {
    "topic": "topic",
    "n blocks": "n", "n": "n",
    "median min": "median", "median": "median", "p50": "median",
    "p25": "p25", "p75": "p75", "p95": "p95",
}
EPS = 1e-9


# ---------------------------------------------------------------- benchmark table

def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_benchmarks(path: Path) -> dict[str, dict]:
    """Rows of the first markdown table whose header names Topic, N, median, p75 and p95.

    Columns are found by header name, so the example file (five columns) and a full table written by
    refresh_topic_stats.py (eleven columns) both work. A row whose numbers do not parse is skipped.
    """
    if not path.exists():
        raise FileNotFoundError(f"benchmark table not found: {path}")
    columns: Optional[dict[str, int]] = None
    rows: dict[str, dict] = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if columns is None:
            if not stripped.startswith("|"):
                continue
            names = [COLUMN_ALIASES.get(c.lower()) for c in _cells(stripped)]
            if all(col in names for col in REQUIRED_COLUMNS):
                columns = {name: i for i, name in enumerate(names) if name}
            continue
        if not stripped.startswith("|"):
            break
        if re.fullmatch(r"\|[\s:|-]+\|?", stripped):
            continue
        cells = _cells(stripped)
        try:
            row = {"n": int(cells[columns["n"]])}
            for band in ("median", "p25", "p75", "p95"):
                if band in columns:
                    row[band] = float(cells[columns[band]])
        except (ValueError, IndexError):
            continue
        rows[cells[columns["topic"]]] = row
    if not rows:
        raise ValueError(f"no topic rows found in {path}: expected a table with Topic, N blocks, Median min, p75 and p95")
    return rows


# ---------------------------------------------------------------- one feature

def _threshold_value(table: list, n: int):
    for minimum, value in sorted(table, key=lambda item: -item[0]):
        if n >= minimum:
            return value
    return sorted(table, key=lambda item: item[0])[0][1]


def confidence_buffer(n: int, settings: dict) -> float:
    """Buffer factor from the lowest N among a feature's topics: fewer blocks measured, wider band."""
    return float(_threshold_value(settings["confidence_buffers"], n))


def confidence_label(n: int, settings: dict) -> str:
    return str(_threshold_value(settings["confidence_labels"], n))


def estimate_feature(feature: dict, stats: dict[str, dict], settings: dict, overhead: float) -> dict:
    """Bands in minutes for one feature, plus everything that went into them."""
    fid = str(feature.get("feature_id") or "?")
    warnings: list[str] = []
    quality = feature.get("quality_target") or settings["default_quality"]
    factors = settings["quality_factors"]
    if quality not in factors:
        warnings.append(f"unknown quality target '{quality}', used '{settings['default_quality']}'")
        quality = settings["default_quality"]
    quality_factor = float(factors[quality])
    extra_factor = float(feature.get("extra_factor", 1.0))

    raw = {band: 0.0 for band in BANDS}
    topics: dict[str, dict] = {}
    min_n: Optional[int] = None
    for topic, count in (feature.get("topic_blocks") or {}).items():
        row = stats.get(topic)
        if row is None:
            warnings.append(f"unknown topic '{topic}', left out of the estimate")
            continue
        if not isinstance(count, (int, float)) or count < 0:
            warnings.append(f"topic '{topic}' has an invalid block count {count!r}, left out")
            continue
        min_n = row["n"] if min_n is None else min(min_n, row["n"])
        if row["n"] < settings["low_n_warning"]:
            warnings.append(f"topic '{topic}' has N={row['n']}: low confidence, wide buffer applied")
        for band in BANDS:
            raw[band] += count * row[band]
        topics[topic] = {"blocks": count, "n": row["n"], **{band: row[band] for band in BANDS}}

    if min_n is None:
        warnings.append("no known topics: feature not estimated")
        return {"feature_id": fid, "name": feature.get("feature_name", fid), "skipped": True,
                "dependencies": list(feature.get("dependencies") or []), "warnings": warnings}

    premiums = settings["external_dep_premiums"]
    deps = list(feature.get("external_deps") or [])
    for dep in deps:
        if dep not in premiums:
            warnings.append(f"external dependency '{dep}' has no premium of its own, used the default")
    premium = sum(float(premiums.get(d, settings["default_external_dep_premium"])) for d in deps)
    buffer = confidence_buffer(min_n, settings)
    bands = {band: (raw[band] * quality_factor * extra_factor + premium) * overhead * buffer for band in BANDS}
    return {
        "feature_id": fid,
        "name": feature.get("feature_name", fid),
        "skipped": False,
        "dependencies": list(feature.get("dependencies") or []),
        "quality_target": quality,
        "quality_factor": quality_factor,
        "extra_factor": extra_factor,
        "topics": topics,
        "raw_block_minutes": {band: round(v, 2) for band, v in raw.items()},
        "external_deps": deps,
        "premium_minutes": premium,
        "overhead": overhead,
        "buffer": buffer,
        "min_topic_n": min_n,
        "confidence": confidence_label(min_n, settings),
        "bands_minutes": {band: round(v, 2) for band, v in bands.items()},
        "warnings": warnings,
    }


# ---------------------------------------------------------------- the dependency graph

def topological_order(durations: dict[str, float], deps: dict[str, list[str]]) -> list[str]:
    """Features in dependency order; raises ValueError on a cycle."""
    indegree = {f: 0 for f in durations}
    children: dict[str, list[str]] = defaultdict(list)
    for f, parents in deps.items():
        for p in parents:
            if p not in durations or f not in durations:
                raise ValueError(f"dependency '{f}' -> '{p}' names a feature without a duration")
            indegree[f] += 1
            children[p].append(f)
    ready = sorted(f for f, d in indegree.items() if d == 0)
    order: list[str] = []
    while ready:
        f = ready.pop(0)
        order.append(f)
        for child in sorted(children[f]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
        ready.sort()
    if len(order) < len(durations):
        stuck = sorted(f for f in durations if f not in order)
        raise ValueError(f"dependency cycle between: {', '.join(stuck)}")
    return order


def critical_path(durations: dict[str, float], deps: dict[str, list[str]]) -> tuple[float, list[str]]:
    """Length and features of the longest dependency chain: wall-clock with unlimited parallel sessions."""
    finish: dict[str, float] = {}
    previous: dict[str, Optional[str]] = {}
    for f in topological_order(durations, deps):
        best: Optional[str] = None
        for p in sorted(deps.get(f, [])):
            if best is None or finish[p] > finish[best] + EPS:
                best = p
        finish[f] = durations[f] + (finish[best] if best else 0.0)
        previous[f] = best
    if not finish:
        return 0.0, []
    end = max(sorted(finish), key=lambda f: finish[f])
    chain: list[str] = []
    node: Optional[str] = end
    while node:
        chain.append(node)
        node = previous[node]
    return finish[end], list(reversed(chain))


def schedule(durations: dict[str, float], deps: dict[str, list[str]], cap: int) -> tuple[float, dict[str, tuple[float, float]]]:
    """List schedule with at most `cap` features running at once.

    Whenever a slot is free, the ready feature with the longest remaining chain starts first (ties by
    id), so the critical path is never kept waiting behind a short side feature.
    """
    if cap < 1:
        raise ValueError("parallel cap must be at least 1")
    order = topological_order(durations, deps)
    children: dict[str, list[str]] = defaultdict(list)
    for f, parents in deps.items():
        for p in parents:
            children[p].append(f)
    remaining: dict[str, float] = {}
    for f in reversed(order):
        remaining[f] = durations[f] + max((remaining[c] for c in children[f]), default=0.0)

    now = 0.0
    done: set[str] = set()
    running: list[tuple[float, str]] = []
    timeline: dict[str, tuple[float, float]] = {}
    while len(done) < len(durations):
        ready = sorted(
            (f for f in durations if f not in timeline and all(p in done for p in deps.get(f, []))),
            key=lambda f: (-remaining[f], f),
        )
        while ready and len(running) < cap:
            f = ready.pop(0)
            timeline[f] = (now, now + durations[f])
            running.append((now + durations[f], f))
        now = min(end for end, _ in running)
        done.update(f for end, f in running if end <= now + EPS)
        running = [(end, f) for end, f in running if end > now + EPS]
    makespan = max((end for _, end in timeline.values()), default=0.0)
    return makespan, timeline


def plan(features: list[dict], parallel_cap: int) -> dict:
    """Effort, critical path and capped wall-clock per band over the estimated features."""
    estimated = [f for f in features if not f["skipped"]]
    ids = {f["feature_id"] for f in estimated}
    warnings: list[str] = []
    deps: dict[str, list[str]] = {}
    for f in estimated:
        kept = []
        for d in f["dependencies"]:
            if d in ids:
                kept.append(d)
            else:
                warnings.append(f"`{f['feature_id']}` depends on '{d}', which is not an estimated feature: dependency ignored")
        deps[f["feature_id"]] = kept
    out: dict = {"warnings": warnings, "effort_minutes": {}, "critical_path_minutes": {},
                 "wall_clock_minutes": {}, "critical_path": {}, "schedule": {}}
    for band in BANDS:
        durations = {f["feature_id"]: f["bands_minutes"][band] for f in estimated}
        out["effort_minutes"][band] = round(sum(durations.values()), 2)
        length, chain = critical_path(durations, deps)
        out["critical_path_minutes"][band] = round(length, 2)
        out["critical_path"][band] = chain
        makespan, timeline = schedule(durations, deps, parallel_cap)
        out["wall_clock_minutes"][band] = round(makespan, 2)
        out["schedule"][band] = {f: [round(s, 2), round(e, 2)] for f, (s, e) in timeline.items()}
    return out


# ---------------------------------------------------------------- output

def _h(minutes: float) -> str:
    return f"{minutes / 60:.1f}"


def _bands_h(values: dict[str, float]) -> str:
    return " / ".join(_h(values[b]) for b in BANDS)


def render_report(record: dict) -> str:
    features, totals, meta = record["features"], record["totals"], record["meta"]
    lines = [
        f"# Estimate: {meta['project']}",
        "",
        f"Computed {meta['created']} from `{meta['benchmarks']['path']}` "
        f"({meta['benchmarks']['blocks_behind_topics']} measured blocks behind the topics used). "
        f"Overhead {meta['overhead']}x, parallel cap {meta['parallel_cap']}.",
    ]
    if meta["benchmarks"]["example"]:
        lines += ["", "**These are one developer's example measurements, not yours.** Run refresh_topic_stats.py "
                      "on your own transcripts and estimate again before you rely on this."]
    lines += [
        "",
        "## Per feature (hours)",
        "",
        "| ID | Feature | Topic blocks | Quality | Confidence (min N) | Median | p75 | p95 | Depends on |",
        "|---|---|---|---|---|---:|---:|---:|---|",
    ]
    for f in features:
        if f["skipped"]:
            lines.append(f"| `{f['feature_id']}` | {f['name']} | - | - | - | - | - | - | not estimated |")
            continue
        mix = ", ".join(f"{t} x{v['blocks']:g}" for t, v in f["topics"].items())
        b = f["bands_minutes"]
        lines.append(
            f"| `{f['feature_id']}` | {f['name']} | {mix} | {f['quality_target']} | {f['confidence']} ({f['min_topic_n']}) | "
            f"{_h(b['median'])} | {_h(b['p75'])} | {_h(b['p95'])} | {', '.join(f['dependencies']) or '-'} |"
        )
    effort, cp, wall = totals["effort_minutes"], totals["critical_path_minutes"], totals["wall_clock_minutes"]
    lines += [
        "",
        "## Totals (hours, median / p75 / p95)",
        "",
        f"- **Effort** (sum of all features): **{_bands_h(effort)}**",
        f"- **Critical path** (longest dependency chain, unlimited parallel sessions): {_bands_h(cp)}",
        f"  - chain on the median band: {' > '.join(totals['critical_path']['median']) or '-'}",
        f"- **Wall-clock** (at most {meta['parallel_cap']} features at once): **{_bands_h(wall)}**",
    ]
    if wall["median"] > 0:
        lines.append(f"- Parallel ratio on the median band: {effort['median'] / wall['median']:.2f} (effort / wall-clock)")
    if meta.get("hours_per_week"):
        weeks = " / ".join(f"{wall[b] / 60 / meta['hours_per_week']:.1f}" for b in BANDS)
        lines.append(f"- Calendar at {meta['hours_per_week']:g} working hours per week: {weeks} weeks")
    lines += [
        "",
        "Read the median band as the base, p75 as the likely outcome and p95 as the planning buffer. "
        "Never pass on one number.",
        "",
        "## Schedule on the median band (hours from start)",
        "",
        "| Feature | Start | End |",
        "|---|---:|---:|",
    ]
    for fid, (start, end) in sorted(totals["schedule"]["median"].items(), key=lambda kv: (kv[1][0], kv[0])):
        lines.append(f"| `{fid}` | {_h(start)} | {_h(end)} |")
    flags = [f"- `{f['feature_id']}`: {w}" for f in features for w in f["warnings"]]
    flags += [f"- {w}" for w in totals["warnings"]]
    flags += [f"- `{f['feature_id']}`: external dependencies {', '.join(f['external_deps'])} "
              f"(+{f['premium_minutes']:g} min connection probing)" for f in features
              if not f["skipped"] and f["external_deps"]]
    if flags:
        lines += ["", "## Risk flags", ""] + flags
    lines.append("")
    return "\n".join(lines)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "estimate"


def build_record(specs: list[dict], stats: dict[str, dict], settings: dict, benchmarks: Path, is_example: bool,
                 project: str, overhead: float, parallel_cap: int, hours_per_week: Optional[float]) -> dict:
    features = [estimate_feature(spec, stats, settings, overhead) for spec in specs]
    ids = [f["feature_id"] for f in features]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise ValueError(f"duplicate feature_id: {', '.join(duplicates)}")
    used_topics = {t for f in features if not f["skipped"] for t in f["topics"]}
    return {
        "schema": "estimator.estimate/1",
        "meta": {
            "project": project,
            "created": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "benchmarks": {
                "path": str(benchmarks),
                "example": is_example,
                "sha256": hashlib.sha256(benchmarks.read_bytes()).hexdigest(),
                "blocks_behind_topics": sum(stats[t]["n"] for t in used_topics),
            },
            "overhead": overhead,
            "parallel_cap": parallel_cap,
            "hours_per_week": hours_per_week,
            "quality_factors": settings["quality_factors"],
            "confidence_buffers": settings["confidence_buffers"],
        },
        "features": features,
        "totals": plan(features, parallel_cap),
    }


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Hour bands and wall-clock time from your own benchmark table.")
    ap.add_argument("--features", type=Path, required=True, help="JSON array of feature specs")
    ap.add_argument("--benchmarks", type=Path, help="benchmark table (default: config, then ~/.claude/estimator/topic-statistics.md, then the example)")
    ap.add_argument("--config", type=Path, help="config file with overrides")
    ap.add_argument("--overhead", type=float, help="multiplier for time outside Claude Code sessions")
    ap.add_argument("--parallel-cap", type=int, help="most features in progress at the same time")
    ap.add_argument("--hours-per-week", type=float, help="convert wall-clock hours to calendar weeks")
    ap.add_argument("--project-name", default="Project")
    ap.add_argument("--output", type=Path, help="markdown report (default: <data-dir>/estimates/<date>-<project>.md)")
    ap.add_argument("--json-out", type=Path, help="estimate record for calibrate.py (default: next to the report)")
    args = ap.parse_args(argv)

    settings = load_settings(args.config)
    benchmarks, is_example = resolve_benchmarks(args.benchmarks, settings)
    stats = parse_benchmarks(benchmarks)
    if is_example:
        print(f"WARN: no benchmark table of your own; using the example file {benchmarks}", file=sys.stderr)
    specs = json.loads(args.features.read_text())
    if not isinstance(specs, list):
        print("ERROR: --features must hold a JSON array", file=sys.stderr)
        return 2
    overhead = float(args.overhead if args.overhead is not None else settings["overhead"])
    cap = int(args.parallel_cap if args.parallel_cap is not None else settings["parallel_cap"])
    hours_per_week = args.hours_per_week if args.hours_per_week is not None else settings["hours_per_week"]
    try:
        record = build_record(specs, stats, settings, benchmarks, is_example, args.project_name, overhead, cap, hours_per_week)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    stem = f"{record['meta']['created']}-{_slug(args.project_name)}"
    output = (args.output or estimator_home() / "estimates" / f"{stem}.md").expanduser()
    json_out = (args.json_out or output.with_name(output.stem + ".estimate.json")).expanduser()
    if args.features.resolve() in (output.resolve(), json_out.resolve()):
        print("ERROR: the report or the record would overwrite the --features file", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(record))
    json_out.write_text(json.dumps(record, indent=2) + "\n")
    t = record["totals"]
    print(f"effort (h, median/p75/p95): {_bands_h(t['effort_minutes'])}")
    print(f"wall-clock with cap {cap} (h): {_bands_h(t['wall_clock_minutes'])}")
    print(f"wrote {output}")
    print(f"wrote {json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
