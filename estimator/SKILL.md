---
name: estimator
description: Estimate effort hours and wall-clock time for a PRD or feature list from the user's own measured Claude Code work blocks. Use when the user asks "how long will this take", "estimate this PRD", "how many hours is this", "time estimate", "lead time", "can you size this", or shares a PRD, scope document or feature list and wants an hour band. It decomposes features into topic blocks and applies the measured median, p75 and p95 minutes per block. It reports effort (summed hours) and wall-clock (critical path with a parallel cap). Use it instead of estimating freehand.
argument-hint: "[PRD file or feature list]"
---

# Estimator: from a PRD to hour bands and wall-clock time

The numbers come from the user's own benchmark table: minutes per work block per topic, measured from their Claude Code transcripts. You do the judgment (which features, which topics, how many blocks). The scripts do the arithmetic, so the same decomposition always gives the same estimate.

The scripts live in this skill's folder: `${CLAUDE_SKILL_DIR}/scripts/`. Pure Python 3, standard library only.

## 1. Get the features

- Read the PRD from the file the user names, or from the text they paste.
- List the discrete deliverables. A feature is a piece of work that gets its own time budget: "OAuth connector for the CRM", "evaluation loop", "dashboard with three tabs".
- No feature list, only a theme ("something with AI")? Do not estimate. Ask for three to five concrete features first.

## 2. Decompose each feature

Map every feature to topic blocks with `${CLAUDE_SKILL_DIR}/references/topic-mix-guide.md`. Write the specs as a JSON array to a file next to where the user works, or under `$TMPDIR`:

```json
[
  {
    "feature_id": "crm-connector",
    "feature_name": "CRM connector with OAuth",
    "topic_blocks": {"parser_work": 4, "api_integration": 5, "python_test": 3},
    "external_deps": ["oauth2"],
    "dependencies": ["schema"],
    "quality_target": "production-ready",
    "extra_factor": 1.0
  }
]
```

- `feature_id`: unique kebab-case id, used for dependencies.
- `topic_blocks`: topic name to number of blocks. Topic names must match the benchmark table.
- `external_deps`: one entry per external API, auth flow or non-public schema; each adds connection-probing minutes.
- `dependencies`: ids of features that must finish before this one can start.
- `quality_target`: `poc`, `demo` or `production-ready`.
- `extra_factor`: optional, for a legacy codebase or another known slowdown. Leave it out when nothing is known.

## 3. Refresh the measurements, then compute

Refresh first. It is incremental and reads only transcripts that changed since the last run:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/refresh_topic_stats.py"
```

Show its first output line (transcripts read, unchanged, blocks in store) so the user sees how large and how fresh the basis is. Then compute:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/compute_estimate.py" \
  --features <specs.json> --project-name "<name>" --parallel-cap 3
```

- The benchmark table is resolved in this order: `--benchmarks`, the `benchmarks` key in `~/.claude/estimator/config.json`, `~/.claude/estimator/topic-statistics.md`, and last the bundled example. When the report says it used the example, tell the user plainly: these are someone else's numbers.
- `--overhead`, `--parallel-cap` and `--hours-per-week` override the config for one run.
- The script writes a markdown report and a JSON record under `~/.claude/estimator/estimates/`. Keep the JSON: it is what calibration compares against later.

## 4. Show the report

Show the full report. Then say in two or three sentences what drives the estimate: the critical path, the features with the widest band and every risk flag (low N, unknown topic, external dependencies, example benchmarks).

## 5. After the work: calibrate

When a feature is done, measure what it took and compare:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/refresh_topic_stats.py" \
  --path <feature folder> --since <start date> --until <end date> --summary-json actual.json
python3 "${CLAUDE_SKILL_DIR}/scripts/calibrate.py" record \
  --estimate <estimate.json> --feature <feature_id> --actual actual.json [--total-hours <h>]
python3 "${CLAUDE_SKILL_DIR}/scripts/calibrate.py" report
```

Explain which ratio is off and what that means: blocks ratio (the decomposition), per-block ratio (a stale table), implied overhead (the overhead factor). Do not change a factor before the report has five features for it.

## Rules

1. **Never one number.** Always the band: median as the base, p75 as the likely outcome, p95 as the planning buffer.
2. **Effort and wall-clock are different numbers.** Effort is the sum of all features. Wall-clock follows the critical path and the parallel cap. Report both and say which is which.
3. **External dependencies go in the spec.** Every OAuth flow or unknown API costs connection probing before code works.
4. **Flag low N.** A topic with few measured blocks gets a wider buffer and a line in the risk flags. Repeat that line to the user.
5. **No speedup claims.** Estimate in hours. A ratio against "a developer without AI" is not measured here and does not belong in the answer.
6. **Do not invent numbers.** Every minute comes from the benchmark table or the config. If a feature needs work the table has no topic for, say so instead of borrowing a topic that looks close.

## Ask instead of guessing

- A feature's topic mix is unclear from the PRD.
- The quality target is unclear: proof of concept against production is a 2 to 4 times difference in blocks.
- The dependencies between features are not stated.
- The work happens in a legacy codebase you know nothing about: ask what `extra_factor` the user wants.

## Files

- `scripts/compute_estimate.py`: bands, critical path, capped schedule, report and JSON record.
- `scripts/refresh_topic_stats.py`: transcripts to work blocks to the benchmark table; filtered runs give actuals.
- `scripts/calibrate.py`: estimate against actual, verdicts per factor, drift between two tables.
- `scripts/workblocks.py`, `scripts/estimator_config.py`: block segmentation, classifier, settings.
- `references/topic-mix-guide.md`: from a feature to topic blocks.
- `benchmarks.example.md`: one developer's measured rows, the fallback until the user has a table of their own.
