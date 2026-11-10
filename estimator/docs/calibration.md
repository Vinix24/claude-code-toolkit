# Re-measuring and calibrating

An estimate you never compare with the outcome teaches you nothing. This page closes the loop: record what a finished feature took, see which part of the estimate missed, and change only that part.

## The loop

1. **Record the estimate.** `compute_estimate.py` already did: every run writes a JSON record under `~/.claude/estimator/estimates/`, with the topic blocks, the factors, the bands and a hash of the benchmark table it used.
2. **Do the work.**
3. **Measure the actual.** Run the refresh filtered to that feature.
4. **Record the comparison.** `calibrate.py record` appends one line to `~/.claude/estimator/calibration.jsonl`.
5. **Read the report** once a few features are in, and change a factor only when the report says so.

## Measuring the actual

The same blocks, the same classifier, limited to the folder and the dates of the feature:

```bash
python3 scripts/refresh_topic_stats.py --path ~/work/app --since 2026-10-06 --until 2026-10-10 \
  --summary-json actual.json
```

Use the same mode and gap as your main table, or the comparison mixes two definitions. A filtered run does not overwrite your main table unless you pass `--out`.

The filter is only as exact as your folders. A feature built in its own worktree or folder is easy to measure. When two features share a folder and a week, the actual holds both: record them as one feature, or split them by date.

For the total, including the time outside sessions, take timekeeper's active hours for the same folder and dates and add the meetings and reviews from your calendar. Pass that as `--total-hours`. Without it the record covers in-session time only, which is still enough for most of the ratios.

## Recording

```bash
python3 scripts/calibrate.py record \
  --estimate ~/.claude/estimator/estimates/<date>-my-project.estimate.json \
  --feature crm-connector --actual actual.json --total-hours <hours>
```

It prints a table per topic and appends the record to the log.

## The ratios, and what each one is for

An estimate misses for one of three reasons. Each has its own ratio and its own fix.

| Ratio | Computed as | When it is off | What to change |
|---|---|---|---|
| **Blocks ratio** | actual blocks / planned blocks, per topic | You decomposed the feature wrong | The block counts in your topic-mix guide for that feature type, or the quality factor |
| **Per-block ratio** | actual median minutes / table median, per topic | Your blocks of that topic got slower or faster | Nothing in the config: refresh the table and check for drift |
| **Implied overhead** | total hours / in-session hours | The time outside sessions is not what you assumed | `overhead` in the config |

Planned blocks include the quality factor: two `python_test` blocks on a `production-ready` feature count as 4.4 planned blocks (2 times 2.2). That way a blocks ratio near 1.0 means both the counts and the quality factor were right.

The record holds three more numbers:

- **Session ratio:** actual in-session minutes against the median band without overhead. The overall hit or miss.
- **Band hit:** in which band the actual landed (`<= median`, `<= p75`, `<= p95` or `> p95`).
- **Unplanned share:** the part of the actual time spent on topics the estimate did not plan. `bug_fix` and `analysis_only` show up here. If this share is large, plan `bug_fix` blocks explicitly on risky features; my own guide reserves 15 to 25% of the total for it.

## When to change a factor

```bash
python3 scripts/calibrate.py report
```

The report gives the median of every ratio over all recorded features, per topic and per quality target, with a verdict:

- `too few`: fewer features than `calibration_min_features` (default 5). Do nothing yet.
- `keep`: the median ratio lies within 1 plus or minus `calibration_tolerance` (default 0.2).
- `raise` or `lower`: outside that range, over enough features.

Both defaults come from how I expect my own reruns to behave. Five data points is the minimum I trust a median on. And when I measure the same task again, I expect a clean task to vary by about 20% and a task with external dependencies by about 50%. If most of your features hit external APIs, run the report with `--tolerance 0.5`, or the verdicts react to noise.

How to change, once a verdict says so:

- **Quality factor:** multiply it by the median blocks ratio for that quality target. The report prints that ratio per target.
- **Overhead:** set it to the median implied overhead.
- **Block counts in your guide:** multiply the counts for that feature type by the topic's median blocks ratio.
- **Per-block ratio off:** refresh the table. The table is the measurement; do not correct it with a factor.

Never change a factor after one feature. One bad week is noise.

### The band hits are a test of the bands themselves

A calibrated median band is exceeded about half the time and a calibrated p75 band about a quarter of the time. That follows from what a median and a p75 are. If most of your features land above p75, your bands are too narrow: the confidence buffers are too small, or your decomposition leaves out work every time. If almost nothing exceeds the median, your bands are padded.

## Spotting drift

Your own speed changes: a new model, a different way of prompting, headless builders instead of interactive sessions, a new kind of project. The table follows when you refresh. To see how much it moved, keep dated snapshots and compare them:

```bash
python3 scripts/refresh_topic_stats.py --snapshot
python3 scripts/calibrate.py drift \
  --old ~/.claude/estimator/snapshots/topic-statistics-<date>.md \
  --new ~/.claude/estimator/topic-statistics.md
```

Per topic it prints both medians, the median ratio, the p95 ratio and a verdict:

- `drift`: both tables have at least `drift_min_n` blocks (default 15) and the median moved more than the tolerance.
- `small N`: one of the two rests on too few blocks. A move here is sample noise until proven otherwise.
- `stable`: within the tolerance.

The verdict looks at the median only. Watch the p95 ratio as well, but give it more blocks before you believe it.

Drift also comes from changing the method. Another mode, gap, minimum block length or classifier rule changes the table even when your work did not change. Compare snapshots made with the same settings, or note the change next to the snapshot.

The [examples](examples.md#small-samples-lie) show a real comparison between two of my own tables, from May and from November 2026.

### When to re-measure

- After a new model version becomes your default.
- After a clear change in how you prompt or run sessions.
- After every finished project, so N keeps growing.

The refresh is incremental, so re-measuring costs seconds after the first run. Keep a snapshot each time you plan to compare.
