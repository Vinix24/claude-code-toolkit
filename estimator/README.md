# claude-code-estimator

Estimate a PRD from your own measured work. A Claude Code skill plus three small scripts: one turns your transcripts into a table of minutes per work block, one turns a feature list into hour bands and a wall-clock time, and one compares finished work with its estimate. Python 3.9 or newer, standard library only, nothing leaves your machine.

## Why

Estimates made from memory drift towards what you hope. Claude Code already writes a transcript of every session, with a timestamp on every event. That is enough to measure how long a block of each kind of work actually takes you, and how wide the spread is.

Two things follow from measuring it:

- **The answer is a band, not a number.** In my own data the p95 of a work block is 3.9 to 5.8 times its median. An estimate that hides that spread hides the part that goes wrong.
- **Effort and wall-clock are different numbers.** In the worked example in the docs, eight features with dependencies come to 31.2 hours of effort and 18.7 hours of wall-clock on the median band. Parallel sessions change the second, not the first.

## How it works

```
~/.claude/projects/*.jsonl ──► refresh_topic_stats.py ──► your topic table (N, median, p75, p95)
                                                                │
PRD ──► features as topic blocks (the skill, with the guide) ──┤
                                                                ▼
                                                     compute_estimate.py ──► bands, critical path, schedule
                                                                │                 + a JSON record
finished feature ──► refresh_topic_stats.py --path --since ──► calibrate.py ──► which factor to change
```

1. **Work blocks.** Each transcript is cut into blocks of continuous work with idle left out: by gap (a pause over 5 minutes ends a block) or by turn (prompt to stop, like [timekeeper](../timekeeper/)). A rule-based classifier gives each block a topic such as `python_test`, `frontend_work` or `api_integration`.
2. **Your table.** Per topic: N, median, mean, p25, p75 and p95 minutes per block.
3. **Decomposition.** Each feature of a PRD becomes a count of blocks per topic, plus its quality target, external dependencies and the features it depends on. The skill does this with `references/topic-mix-guide.md`.
4. **Arithmetic.** Per feature and band, the block minutes are multiplied by the quality factor and a premium per external dependency is added. The result is multiplied by the overhead and by a confidence buffer that widens when a topic has few blocks. Over the features: effort (sum), critical path (longest chain) and wall-clock (a schedule with a parallel cap).
5. **Calibration.** When a feature is done, its actual blocks are measured the same way. `calibrate.py` splits the miss into decomposition, stale table and overhead, and says which factor to change once five features agree.

## Install

```bash
git clone https://github.com/Vinix24/claude-code-toolkit
cd claude-code-toolkit/estimator
./install.sh
python3 scripts/refresh_topic_stats.py
```

`install.sh` copies the skill into `~/.claude/skills/estimator` (or `$CLAUDE_CONFIG_DIR/skills/estimator`) and is safe to re-run. The refresh builds your own table in `~/.claude/estimator/topic-statistics.md`. The first run reads every transcript you have and can take minutes; after that it reads only what changed.

Then ask Claude Code to estimate a PRD. The skill decomposes it, runs the scripts and shows the report.

## Usage without the skill

```bash
# Your table; --mode turn for prompt-to-stop blocks, --snapshot to keep a dated copy
python3 scripts/refresh_topic_stats.py

# An estimate from a feature list
python3 scripts/compute_estimate.py --features examples/knowledge-base.features.json \
  --project-name "Knowledge base" --parallel-cap 2

# After the work: what one feature took, and the comparison
python3 scripts/refresh_topic_stats.py --path ~/work/app --since 2026-10-06 --until 2026-10-10 \
  --summary-json actual.json
python3 scripts/calibrate.py record --estimate ~/.claude/estimator/estimates/<file>.estimate.json \
  --feature <feature_id> --actual actual.json
python3 scripts/calibrate.py report

# Did my table move?
python3 scripts/calibrate.py drift --old <old snapshot> --new ~/.claude/estimator/topic-statistics.md
```

## Files

| Path | What it is |
|---|---|
| `SKILL.md` | The skill: from a PRD to features, topic blocks, the report and the calibration step |
| `scripts/refresh_topic_stats.py` | Transcripts to work blocks to your table; filtered runs give the actuals of one feature |
| `scripts/compute_estimate.py` | Bands, critical path, capped schedule, markdown report and JSON record |
| `scripts/calibrate.py` | Estimate against actual, verdicts per factor, drift between two tables |
| `scripts/workblocks.py` | Block segmentation (gap and turn) and the classifier |
| `scripts/estimator_config.py` | Every default and the config file loader |
| `references/topic-mix-guide.md` | Block counts per feature type, quality factors, dependency premiums |
| `benchmarks.example.md` | A selection of my own measured rows, the fallback until you have a table |
| `examples/*.features.json` | The two worked estimates from the docs, to rerun |
| `docs/` | The documentation site pages |

## Configuration

`~/.claude/estimator/config.json` (or `$ESTIMATOR_HOME/config.json`, or a file passed with `--config`) overrides any default per key. `quality_factors` and `external_dep_premiums` merge per entry; everything else replaces.

| Key | Default | What it does |
|---|---|---|
| `benchmarks` | none | Table to estimate from. Without it: `~/.claude/estimator/topic-statistics.md`, then the example |
| `overhead` | `1.4` | Multiplier for time outside Claude Code sessions |
| `parallel_cap` | `3` | Most features in progress at once |
| `hours_per_week` | none | Converts wall-clock hours into calendar weeks |
| `quality_factors` | `poc` 1.0, `demo` 1.4, `production-ready` 2.2 | Multiplier on block minutes |
| `external_dep_premiums` | 15 to 75 minutes per type | Connection probing per external dependency; unknown types get `default_external_dep_premium` (25) |
| `confidence_buffers` | 1.25 from N 15, 1.4 from N 5, else 1.5 | Widens the bands when a topic has few blocks |
| `mode`, `gap_minutes`, `min_block_minutes` | `gap`, 5, 1.0 | How transcripts become blocks |
| `topic_rules`, `tool_topics` | built in | Replace the classifier rules for your own stack |
| `calibration_tolerance`, `calibration_min_features`, `drift_min_n` | 0.2, 5, 15 | When calibrate.py calls a ratio off |

The defaults are my own settings. They are where calibration starts, not facts about your work.

## Documentation

The full guide lives in [`docs/`](docs/): [measuring your own codebase](docs/measuring.md), [from PRD to estimate](docs/prd-to-estimate.md), [re-measuring and calibrating](docs/calibration.md) and [examples from my measurements](docs/examples.md). To read it as a site, from the repository root:

```bash
pip install -r docs/requirements.txt
mkdocs serve
```

## Limitations

- **In-session time only.** The table measures time inside Claude Code sessions. Everything else is the overhead factor, and only calibration with total hours checks it.
- **Rule-based topics.** On my data roughly 70 to 80% of events get the right label. Fine for medians over many blocks, not for a topic with a dozen. Read the longest blocks the table lists.
- **One developer's defaults.** The topic names, block counts and factors come from my work, which is mostly Python. Change the rules and the guide when your stack differs.
- **Attention is not measured.** The parallel cap is a setting. Set it from how many features you really kept moving on past projects.

## Privacy

Everything stays on your machine. The scripts read `~/.claude/projects` and write to `~/.claude/estimator/`. Your generated table lists folder names and session ids under its longest-block examples: strip that section (`--examples 0`) before you share a table. The repo ships no data of yours; `benchmarks.example.md` holds only topic statistics of mine.

## License

MIT. See [`LICENSE`](../LICENSE).
