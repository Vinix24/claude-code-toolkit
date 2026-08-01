#!/usr/bin/env python3
"""claude-code-timekeeper — active time + token usage + API-equivalent cost.

Reports, for a given working-directory prefix (e.g. a client folder):

  - Active work time: sum of (Stop - UserPromptSubmit) per turn. Counts tool-call
    and generation time, excludes idle between turns. Needs the two hooks installed.
  - Raw span: first prompt -> last event. Reference only; includes idle.
  - Token usage + API-equivalent cost: parsed from the Claude Code session
    transcripts under ~/.claude/projects/.

IMPORTANT framing: if you run Claude Code on a subscription (OAuth), the cost
below is the API-EQUIVALENT (what the same tokens would cost at list API rates),
not what you actually paid. Useful as a value / replacement-cost metric for
client work; label it as such, never as "my cost".

Usage:
  report.py --path /abs/path/to/folder [--date YYYY-MM-DD] [--fx 0.92] [--json]

  --path   cwd prefix to match (a client folder, a project, or your whole home).
  --date   restrict to one UTC day (transcripts) / local day (time logs).
  --fx     also show cost in EUR at this USD->EUR rate.
  --json   emit machine-readable JSON instead of the text report.
"""
import argparse
import glob
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
PROJECTS = HOME / ".claude" / "projects"
PRICING_DEFAULT = Path(__file__).resolve().parent / "pricing.json"

# cache-write / cache-read multipliers relative to the model's input rate
CW_5M = 1.25   # 5-minute TTL cache write
CW_1H = 2.0    # 1-hour TTL cache write
CR = 0.10      # cache read


def load_pricing(path):
    data = json.loads(Path(path).read_text())
    return {k: v for k, v in data.items() if not k.startswith("_")}


def rate_for(model, pricing):
    norm = model.split("[")[0].strip()  # drop suffixes like [1m]
    if norm in pricing:
        return norm, pricing[norm]
    for k in pricing:
        if norm.startswith(k) or k.startswith(norm):
            return k, pricing[k]
    return None, None


def load_times(name, path_prefix, date):
    p = HOME / ".claude" / name
    out = []
    if not p.exists():
        return out
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except Exception:
            continue
        if not str(e.get("cwd", "")).startswith(path_prefix):
            continue
        if date and not str(e.get("ts_local", "")).startswith(date):
            continue
        out.append(e)
    return out


def t_local(e):
    return datetime.fromisoformat(e["ts_local"].replace("Z", "+00:00"))


def active_and_raw(path_prefix, date):
    prompts = load_times("prompt-times.jsonl", path_prefix, date)
    stops = load_times("stop-times.jsonl", path_prefix, date)
    if not prompts:
        return None
    events = sorted(
        [("p", t_local(e)) for e in prompts] + [("s", t_local(e)) for e in stops],
        key=lambda x: x[1],
    )
    active = 0.0
    openp = None
    for kind, ts in events:
        if kind == "p":
            openp = ts
        elif kind == "s" and openp is not None:
            active += (ts - openp).total_seconds()
            openp = None
    first = t_local(prompts[0])
    last = max([t_local(e) for e in prompts] + [t_local(e) for e in stops])
    return {
        "active_hours": active / 3600,
        "raw_hours": (last - first).total_seconds() / 3600,
        "prompts": len(prompts),
        "stops": len(stops),
    }


def collect_usage(path_prefix, date):
    """Return {model: {input, output, cw5m, cw1h, cr}} summed over matching transcript lines."""
    per_model = {}
    if not PROJECTS.exists():
        return per_model
    for proj in sorted(PROJECTS.iterdir()):
        if not proj.is_dir():
            continue
        files = sorted(glob.glob(str(proj / "*.jsonl")))
        if not files:
            continue
        # gate the whole project dir on the first line that carries a cwd
        # (the first transcript line is often a summary/meta line with no cwd)
        gate_ok = False
        try:
            with open(files[0]) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        e = json.loads(line)
                    except Exception:
                        continue
                    cwd = e.get("cwd")
                    if cwd is None:
                        continue
                    gate_ok = str(cwd).startswith(path_prefix)
                    break
        except Exception:
            pass
        if not gate_ok:
            continue
        for fp in files:
            for line in open(fp):
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                if not str(e.get("cwd", "")).startswith(path_prefix):
                    continue
                if date and not str(e.get("timestamp", "")).startswith(date):
                    continue
                msg = e.get("message") or {}
                u = msg.get("usage")
                if not u:
                    continue
                model = msg.get("model") or "unknown"
                m = per_model.setdefault(
                    model, {"input": 0, "output": 0, "cw5m": 0, "cw1h": 0, "cr": 0}
                )
                m["input"] += u.get("input_tokens", 0) or 0
                m["output"] += u.get("output_tokens", 0) or 0
                m["cr"] += u.get("cache_read_input_tokens", 0) or 0
                cc = u.get("cache_creation") or {}
                w5 = cc.get("ephemeral_5m_input_tokens")
                w1 = cc.get("ephemeral_1h_input_tokens")
                if w5 is None and w1 is None:
                    # fall back to the flat field, treat as 5m
                    m["cw5m"] += u.get("cache_creation_input_tokens", 0) or 0
                else:
                    m["cw5m"] += w5 or 0
                    m["cw1h"] += w1 or 0
    return per_model


def cost_for(tok, rate):
    """USD for one model's token counts.

    Cache-tarieven worden standaard afgeleid uit het input-tarief met de
    Anthropic-factoren. Een model mag die afleiding overrulen met absolute
    tarieven (cache_read / cache_write_5m / cache_write_1h), want die factoren
    gelden alleen voor Anthropic. DeepSeek draait via een Anthropic-COMPATIBEL
    endpoint, dus de tokens komen in Anthropic-vorm binnen terwijl DeepSeek op
    zijn eigen model afrekent: daar bestaat geen opslag voor een cache write
    (dat is een cache miss = input-tarief) en is de cache-read-korting veel
    groter dan 0.1x. Zie de _note-velden in pricing.json.
    """
    inp = rate["input"]
    cw5m = rate.get("cache_write_5m", inp * CW_5M)
    cw1h = rate.get("cache_write_1h", inp * CW_1H)
    cr = rate.get("cache_read", inp * CR)
    return (
        tok["input"] * inp
        + tok["output"] * rate["output"]
        + tok["cw5m"] * cw5m
        + tok["cw1h"] * cw1h
        + tok["cr"] * cr
    ) / 1_000_000


def main(argv=None):
    ap = argparse.ArgumentParser(description="Active time + token usage + API-equivalent cost.")
    ap.add_argument("--path", required=True, help="cwd prefix to match (client folder / project)")
    ap.add_argument("--date", default=None, help="restrict to YYYY-MM-DD")
    ap.add_argument("--pricing", default=str(PRICING_DEFAULT))
    ap.add_argument("--fx", type=float, default=None, help="USD->EUR rate, e.g. 0.92")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    path_prefix = str(Path(args.path).resolve())
    pricing = load_pricing(args.pricing)

    timing = active_and_raw(path_prefix, args.date)
    usage = collect_usage(path_prefix, args.date)

    total_cost = 0.0
    total_tok = {"input": 0, "output": 0, "cw5m": 0, "cw1h": 0, "cr": 0}
    rows = []
    unknown_models = []
    for model in sorted(usage):
        tok = usage[model]
        if sum(tok.values()) == 0:
            continue  # skip zero-usage pseudo-models (e.g. <synthetic>)
        key, rate = rate_for(model, pricing)
        c = cost_for(tok, rate) if rate else 0.0
        if not rate:
            unknown_models.append(model)
        total_cost += c
        for k in total_tok:
            total_tok[k] += tok[k]
        rows.append({"model": model, "priced_as": key, "tokens": tok, "usd": c})

    if args.json:
        print(json.dumps({
            "path": path_prefix, "date": args.date,
            "timing": timing, "per_model": rows,
            "total_tokens": total_tok, "total_usd": total_cost,
            "total_eur": (total_cost * args.fx) if args.fx else None,
            "unknown_models": unknown_models,
        }, indent=2))
        return

    print(f"claude-code-timekeeper  |  {path_prefix}" + (f"  |  {args.date}" if args.date else "  |  all-time"))
    print("=" * 72)
    if timing:
        src = "prompt->stop" if timing["stops"] else "GEEN stops (schat zelf)"
        print(f"Active work time : {timing['active_hours']:.2f} h   [{src}]")
        print(f"Raw span (idle!) : {timing['raw_hours']:.2f} h   (reference only, not work time)")
        print(f"Prompts / stops  : {timing['prompts']} / {timing['stops']}")
    else:
        print("Active work time : n/a (no prompt-times for this path/date)")
    print("-" * 72)
    grand = sum(total_tok.values())
    print(f"Tokens           : {grand:,} total")
    print(f"  input          : {total_tok['input']:,}")
    print(f"  output         : {total_tok['output']:,}")
    print(f"  cache write 5m : {total_tok['cw5m']:,}")
    print(f"  cache write 1h : {total_tok['cw1h']:,}")
    print(f"  cache read     : {total_tok['cr']:,}")
    print("-" * 72)
    for r in rows:
        t = r["tokens"]
        tot = sum(t.values())
        print(f"  {r['model']:<22} {tot:>12,} tok   ${r['usd']:>9.2f}"
              + ("" if r["priced_as"] else "   [UNKNOWN MODEL - not priced]"))
    print("-" * 72)
    print(f"API-equivalent cost : ${total_cost:,.2f} USD" + (f"   (~EUR {total_cost*args.fx:,.2f})" if args.fx else ""))
    print("Note: API-EQUIVALENT (list rates). On a subscription this is NOT what you paid;")
    print("use it as a value / replacement-cost metric for client work.")
    if unknown_models:
        print(f"WARN: unpriced models (add to pricing.json): {', '.join(unknown_models)}")


if __name__ == "__main__":
    main()
