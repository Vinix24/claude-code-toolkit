# claude-code-timekeeper

Measure how much *active* time Claude Code actually spent on a piece of work, and what the tokens would cost at API rates. Two tiny hooks plus one reporting script. No dependencies beyond Python 3, `jq`, and the transcripts Claude Code already writes.

## Why

The naive way to measure a Claude Code session is "first prompt to last prompt". That number lies: it counts every minute you were away from the keyboard as if it were work. On a session with a few long pauses, the calendar span can be 3x the real working time.

The fix is to bound each turn. A `UserPromptSubmit` hook marks when a turn starts; a `Stop` hook marks when Claude finishes. Active time is the sum of `(Stop - UserPromptSubmit)` across turns. That counts tool calls and generation (real work) and excludes the idle gaps between turns.

```
prompt ──[ Claude works: tools + generation ]── stop      ← counted (active)
                                                  │
                                            you are away    ← NOT counted (idle)
                                                  │
prompt ──[ Claude works ]── stop                            ← counted
```

On top of that, the reporter reads the session transcripts and sums token usage per model, then prices it at list API rates, with cache writes and reads costed separately.

## Honest framing on cost

If you run Claude Code on a subscription (OAuth login), the cost figure is the **API-equivalent**: what the same tokens would cost at list API rates, not what you actually paid. It is a useful value or replacement-cost metric (for example, "this client's work consumed X tokens = $Y at API rates"), but label it that way. It is not your bill.

## Install

```bash
git clone https://github.com/Vinix24/claude-code-toolkit
cd claude-code-toolkit/timekeeper
./install.sh
```

`install.sh` copies the two hooks into `~/.claude/hooks/`, registers them in `~/.claude/settings.json` (idempotent, backs up first), and is safe to re-run. The hooks take effect from a **new** Claude Code session.

What the hooks write (append-only JSONL in `~/.claude/`):

- `prompt-times.jsonl`: one line per prompt (`ts_utc`, `ts_local`, `session_id`, `cwd`).
- `stop-times.jsonl`: one line per turn-end.

## Usage

```bash
# All-time, for one folder (e.g. a client project)
python3 report.py --path ~/work/clients/acme

# One UTC day
python3 report.py --path ~/work/clients/acme --date 2026-06-15

# Also show EUR at a given USD->EUR rate
python3 report.py --path ~/work/clients/acme --fx 0.92

# Machine-readable
python3 report.py --path ~/work/clients/acme --json
```

Example output:

```
claude-code-timekeeper  |  /Users/me/work/clients/acme  |  all-time
========================================================================
Active work time : 6.40 h   [prompt->stop]
Raw span (idle!) : 41.10 h   (reference only, not work time)
Prompts / stops  : 88 / 88
------------------------------------------------------------------------
Tokens           : 12,460,331 total
  input          : 410,221
  output         : 88,140
  cache write 5m : 1,002,455
  cache write 1h : 0
  cache read     : 10,959,515
------------------------------------------------------------------------
  claude-opus-4-8           12,460,331 tok   $   42.18
------------------------------------------------------------------------
API-equivalent cost : $42.18 USD
```

`--path` is a prefix match on the working directory, so it works at any granularity: one client folder, a parent directory of many projects, or your whole home directory for a global total.

## Pricing

Rates live in `pricing.json` (USD per 1M tokens, input and output per model). Cache rates are derived from the input rate: cache write 5m = 1.25x input, cache write 1h = 2x input, cache read = 0.1x input. Update the file when Anthropic changes pricing or add models you use. Unpriced models still have their tokens counted; they are flagged and excluded from the cost total.

## Limitations

- **Active time is turn wall-clock, including tool waits.** It is "session working time", not pure human effort. A model that sits blocked on a slow tool or an outage still accrues active time. That is usually what you want for effort tracking, but know what it measures.
- **Time hooks are not retroactive.** Sessions before you installed the hooks have no `prompt-times` / `stop-times`, so active time is unavailable for them. Token usage and cost are read from transcripts and work retroactively.
- **Dates.** Transcripts are filtered by UTC date; the time logs by local date. For a daily report near midnight, expect minor edge effects.

## Privacy

Everything stays on your machine. The hooks write to `~/.claude/`, the reporter reads `~/.claude/` and the local transcripts. Nothing is sent anywhere. Note that `prompt-times.jsonl` / `stop-times.jsonl` contain your working-directory paths and session IDs; the repo ships no data.

## License

MIT. See `LICENSE`.
