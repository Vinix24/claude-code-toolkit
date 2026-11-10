#!/usr/bin/env python3
"""Compare estimates with what the work took, and tell which factor to change.

Three commands:

  record  one finished feature: the estimate record (compute_estimate.py) against the actual blocks
          (refresh_topic_stats.py --summary-json, filtered to that feature's folder and dates).
          Appends one line to the calibration log.
  report  every recorded feature: median ratios per topic and per quality target, how often the
          actual landed inside each band, and the overhead the totals imply.
  drift   two benchmark tables (an old snapshot and a new one): which topic medians moved.

An estimate misses for one of three reasons, and each has its own fix:

  blocks ratio      actual blocks / planned blocks       wrong decomposition: fix your block counts
  per-block ratio   actual median / table median          stale table or changed work: refresh, check drift
  implied overhead  total hours / in-session hours        wrong overhead factor: change it in the config

A ratio is only acted on after calibration_min_features features (default 5) and when its median
lies outside 1 +/- calibration_tolerance (default 0.2).
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from compute_estimate import BANDS, parse_benchmarks  # noqa: E402
from estimator_config import estimator_home, load_settings  # noqa: E402


def _ratio(actual: Optional[float], planned: Optional[float]) -> Optional[float]:
    if actual is None or not planned:
        return None
    return round(actual / planned, 3)


def verdict(ratios: list[float], tolerance: float, min_features: int) -> str:
    if len(ratios) < min_features:
        return "too few"
    m = statistics.median(ratios)
    if m > 1 + tolerance:
        return "raise"
    if m < 1 - tolerance:
        return "lower"
    return "keep"


def band_hit(actual: float, bands: dict[str, float]) -> str:
    for band in BANDS:
        if actual <= bands[band]:
            return f"<= {band}"
    return "> p95"


def compare(estimate: dict, feature_id: str, actual: dict, total_hours: Optional[float] = None) -> dict:
    """One calibration record: per-topic ratios plus where the actual landed in the bands."""
    feature = next((f for f in estimate["features"] if f["feature_id"] == feature_id), None)
    if feature is None:
        raise ValueError(f"feature '{feature_id}' is not in the estimate")
    if feature["skipped"]:
        raise ValueError(f"feature '{feature_id}' was not estimated, nothing to compare")
    scale = feature["quality_factor"] * feature.get("extra_factor", 1.0)
    planned = {
        t: {"blocks": v["blocks"] * scale, "minutes": v["blocks"] * scale * v["median"], "table_median": v["median"]}
        for t, v in feature["topics"].items()
    }
    observed = actual.get("topics", {})
    per_topic: dict[str, dict] = {}
    for topic in sorted(set(planned) | set(observed)):
        p, a = planned.get(topic), observed.get(topic)
        per_topic[topic] = {
            "planned": p is not None,
            "planned_blocks": round(p["blocks"], 2) if p else 0,
            "actual_blocks": a["blocks"] if a else 0,
            "planned_minutes": round(p["minutes"], 2) if p else 0,
            "actual_minutes": a["minutes"] if a else 0,
            "table_median": p["table_median"] if p else None,
            "actual_median": a["median"] if a else None,
            "blocks_ratio": _ratio(a["blocks"] if a else 0, p["blocks"]) if p else None,
            "per_block_ratio": _ratio(a["median"], p["table_median"]) if (a and p) else None,
            "minutes_ratio": _ratio(a["minutes"] if a else 0, p["minutes"]) if p else None,
        }
    actual_minutes = sum(v["actual_minutes"] for v in per_topic.values())
    unplanned = sum(v["actual_minutes"] for v in per_topic.values() if not v["planned"])
    session_bands = {b: feature["bands_minutes"][b] / feature["overhead"] for b in BANDS}
    record = {
        "schema": "estimator.calibration/1",
        "recorded": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "project": estimate["meta"]["project"],
        "estimate_created": estimate["meta"]["created"],
        "benchmarks_sha256": estimate["meta"]["benchmarks"]["sha256"],
        "feature_id": feature_id,
        "quality_target": feature["quality_target"],
        "external_deps": feature["external_deps"],
        "per_topic": per_topic,
        "actual_session_minutes": round(actual_minutes, 2),
        "session_bands_minutes": {b: round(v, 2) for b, v in session_bands.items()},
        "session_ratio": _ratio(actual_minutes, session_bands["median"]),
        "session_band_hit": band_hit(actual_minutes, session_bands),
        "unplanned_share": round(unplanned / actual_minutes, 3) if actual_minutes else None,
        "overhead_used": feature["overhead"],
    }
    if total_hours is not None:
        total = total_hours * 60
        record["total_minutes"] = round(total, 2)
        record["total_ratio"] = _ratio(total, feature["bands_minutes"]["median"])
        record["total_band_hit"] = band_hit(total, feature["bands_minutes"])
        record["implied_overhead"] = _ratio(total, actual_minutes)
    return record


def summarize(records: list[dict], tolerance: float, min_features: int) -> dict:
    """Median ratios and verdicts over all calibration records."""
    by_topic: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    by_quality: dict[str, list[float]] = defaultdict(list)
    for r in records:
        planned_blocks = sum(v["planned_blocks"] for v in r["per_topic"].values() if v["planned"])
        actual_planned_blocks = sum(v["actual_blocks"] for v in r["per_topic"].values() if v["planned"])
        if planned_blocks:
            by_quality[r["quality_target"]].append(actual_planned_blocks / planned_blocks)
        for topic, v in r["per_topic"].items():
            for key in ("blocks_ratio", "per_block_ratio", "minutes_ratio"):
                if v.get(key) is not None:
                    by_topic[topic][key].append(v[key])
    topics = {}
    for topic, ratios in sorted(by_topic.items()):
        topics[topic] = {
            key: {"features": len(values), "median": round(statistics.median(values), 3),
                  "verdict": verdict(values, tolerance, min_features)}
            for key, values in ratios.items()
        }
    quality = {
        q: {"features": len(v), "median_blocks_ratio": round(statistics.median(v), 3),
            "verdict": verdict(v, tolerance, min_features)}
        for q, v in sorted(by_quality.items())
    }
    hits: dict[str, int] = defaultdict(int)
    for r in records:
        hits[r["session_band_hit"]] += 1
    session = [r["session_ratio"] for r in records if r.get("session_ratio") is not None]
    with_total = [r for r in records if r.get("implied_overhead") is not None]
    implied = [r["implied_overhead"] for r in with_total]
    unplanned = [r["unplanned_share"] for r in records if r.get("unplanned_share") is not None]
    used = [r["overhead_used"] for r in records]
    return {
        "features": len(records),
        "with_external_deps": sum(1 for r in records if r["external_deps"]),
        "topics": topics,
        "quality": quality,
        "session_band_hits": dict(hits),
        "median_session_ratio": round(statistics.median(session), 3) if session else None,
        "session_verdict": verdict(session, tolerance, min_features),
        "median_implied_overhead": round(statistics.median(implied), 3) if implied else None,
        "overhead_records": len(with_total),
        "overhead_verdict": verdict([r["implied_overhead"] / r["overhead_used"] for r in with_total], tolerance, min_features),
        "overhead_used": statistics.median(used) if used else None,
        "median_unplanned_share": round(statistics.median(unplanned), 3) if unplanned else None,
    }


def drift(old: dict[str, dict], new: dict[str, dict], tolerance: float, min_n: int) -> list[dict]:
    """Per topic: how far the median and p95 moved between two benchmark tables."""
    rows = []
    for topic in sorted(set(old) | set(new)):
        o, n = old.get(topic), new.get(topic)
        row = {"topic": topic, "old_n": o["n"] if o else None, "new_n": n["n"] if n else None,
               "old_median": o["median"] if o else None, "new_median": n["median"] if n else None,
               "median_ratio": _ratio(n["median"], o["median"]) if (o and n) else None,
               "p95_ratio": _ratio(n["p95"], o["p95"]) if (o and n) else None}
        if not (o and n):
            row["verdict"] = "only in one table"
        elif min(o["n"], n["n"]) < min_n:
            row["verdict"] = "small N"
        elif abs(row["median_ratio"] - 1) > tolerance:
            row["verdict"] = "drift"
        else:
            row["verdict"] = "stable"
        rows.append(row)
    return rows


def _fmt(value, spec: str = ".2f") -> str:
    return "-" if value is None else format(value, spec)


def print_record(r: dict) -> None:
    print(f"feature {r['feature_id']} ({r['quality_target']}): in-session {r['actual_session_minutes'] / 60:.1f} h, "
          f"ratio {_fmt(r['session_ratio'])} to the median band, landed {r['session_band_hit']}")
    print("| Topic | Planned blocks | Actual blocks | Blocks ratio | Table median | Actual median | Per-block ratio |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for topic, v in r["per_topic"].items():
        name = topic if v["planned"] else f"{topic} (unplanned)"
        print(f"| {name} | {v['planned_blocks']:g} | {v['actual_blocks']} | {_fmt(v['blocks_ratio'])} | "
              f"{_fmt(v['table_median'])} | {_fmt(v['actual_median'])} | {_fmt(v['per_block_ratio'])} |")
    print(f"unplanned share of in-session time: {_fmt(r['unplanned_share'], '.0%')}")
    if "total_ratio" in r:
        print(f"total {r['total_minutes'] / 60:.1f} h: ratio {_fmt(r['total_ratio'])} to the median band, landed "
              f"{r['total_band_hit']}, implied overhead {_fmt(r['implied_overhead'])} (used {r['overhead_used']})")


def print_summary(s: dict) -> None:
    print(f"{s['features']} features recorded, {s['with_external_deps']} with external dependencies")
    print("| Topic | Features | Blocks ratio | Per-block ratio | Minutes ratio |")
    print("|---|---:|---|---|---|")
    for topic, v in s["topics"].items():
        cells = []
        for key in ("blocks_ratio", "per_block_ratio", "minutes_ratio"):
            c = v.get(key)
            cells.append(f"{c['median']:.2f} ({c['verdict']})" if c else "-")
        count = max(c["features"] for c in v.values())
        print(f"| {topic} | {count} | {' | '.join(cells)} |")
    for q, v in s["quality"].items():
        print(f"quality '{q}': median blocks ratio {v['median_blocks_ratio']:.2f} over {v['features']} features ({v['verdict']})")
    print(f"in-session median ratio: {_fmt(s['median_session_ratio'])} ({s['session_verdict']}); "
          f"band hits: {', '.join(f'{k} {v}' for k, v in sorted(s['session_band_hits'].items()))}")
    if s["median_implied_overhead"] is not None:
        print(f"implied overhead: median {s['median_implied_overhead']:.2f} over {s['overhead_records']} features, "
              f"configured {s['overhead_used']} ({s['overhead_verdict']})")
    print(f"median unplanned share: {_fmt(s['median_unplanned_share'], '.0%')}")


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Compare estimates with actuals and spot drift.")
    ap.add_argument("--config", type=Path, help="config file with overrides")
    sub = ap.add_subparsers(dest="command", required=True)
    rec = sub.add_parser("record", help="record one finished feature")
    rec.add_argument("--estimate", type=Path, required=True, help="estimate JSON written by compute_estimate.py")
    rec.add_argument("--feature", required=True, help="feature_id inside that estimate")
    rec.add_argument("--actual", type=Path, required=True, help="JSON from refresh_topic_stats.py --summary-json")
    rec.add_argument("--total-hours", type=float, help="all hours the feature took, meetings and reviews included")
    rec.add_argument("--log", type=Path, help="calibration log (default: <data-dir>/calibration.jsonl)")
    rep = sub.add_parser("report", help="summarize the calibration log")
    rep.add_argument("--log", type=Path)
    rep.add_argument("--json", action="store_true")
    dr = sub.add_parser("drift", help="compare two benchmark tables")
    dr.add_argument("--old", type=Path, required=True)
    dr.add_argument("--new", type=Path, required=True)
    for p in (rep, dr):
        p.add_argument("--tolerance", type=float, help="ratio band around 1.0 that counts as on target")
    rep.add_argument("--min-features", type=int, help="features needed before a verdict")
    dr.add_argument("--min-n", type=int, help="N needed in both tables before a move counts as drift")
    args = ap.parse_args(argv)

    settings = load_settings(args.config)
    tolerance = getattr(args, "tolerance", None)
    tolerance = float(tolerance if tolerance is not None else settings["calibration_tolerance"])

    if args.command == "drift":
        min_n = args.min_n if args.min_n is not None else settings["drift_min_n"]
        rows = drift(parse_benchmarks(args.old), parse_benchmarks(args.new), tolerance, min_n)
        print("| Topic | Old N | New N | Old median | New median | Median ratio | p95 ratio | Verdict |")
        print("|---|---:|---:|---:|---:|---:|---:|---|")
        for r in rows:
            print(f"| {r['topic']} | {_fmt(r['old_n'], 'd')} | {_fmt(r['new_n'], 'd')} | {_fmt(r['old_median'])} | "
                  f"{_fmt(r['new_median'])} | {_fmt(r['median_ratio'])} | {_fmt(r['p95_ratio'])} | {r['verdict']} |")
        return 0

    log = (args.log or estimator_home() / "calibration.jsonl").expanduser()
    if args.command == "record":
        try:
            record = compare(json.loads(args.estimate.read_text()), args.feature,
                             json.loads(args.actual.read_text()), args.total_hours)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a") as fh:
            fh.write(json.dumps(record) + "\n")
        print_record(record)
        print(f"appended to {log}")
        return 0

    if not log.exists():
        print(f"no calibration log at {log}: record a finished feature first", file=sys.stderr)
        return 2
    records = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
    min_features = args.min_features if args.min_features is not None else settings["calibration_min_features"]
    result = summarize(records, tolerance, min_features)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
