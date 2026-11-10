# From PRD to estimate

The judgment and the arithmetic are split on purpose. You (or Claude, through the skill) decide which features there are and how many blocks of which topic each takes. `compute_estimate.py` does the rest, so the same decomposition always gives the same numbers, and a later calibration can tell which half was wrong.

## 1. Features

A feature is a discrete deliverable that gets its own time budget: "OAuth connector for the CRM", "evaluation loop", "dashboard with three tabs". It should be small enough that you can say which kinds of work it needs, and large enough to finish on its own.

If the PRD names only a theme ("something with AI for sales"), there is nothing to estimate yet. Ask for three to five concrete features first.

## 2. Topic blocks

For each feature, count blocks per topic. A block is one stretch of continuous work on one kind of thing, the unit your table measures. `references/topic-mix-guide.md` holds my starting counts per feature type: a standard OAuth connector is 12 to 22 blocks, a dashboard with three to five tabs 11 to 20.

Write counts, never minutes. The minutes come from your table at run time. That is what lets a refreshed table improve every estimate you make afterwards.

```json
{
  "feature_id": "crm-connector",
  "feature_name": "CRM connector with OAuth",
  "topic_blocks": {"parser_work": 4, "api_integration": 5, "python_test": 3},
  "external_deps": ["oauth2"],
  "dependencies": ["schema"],
  "quality_target": "production-ready"
}
```

## 3. Quality target

The same feature as a proof of concept and as production code are different amounts of work. In my experience a production-ready version takes 2.5 to 4 times the blocks of a proof of concept.

The factors applied are smaller: `poc` 1.0, `demo` 1.4 and `production-ready` 2.2. The measured medians already mix all quality levels. They live in the config as `quality_factors`. Calibration tells you when yours are off.

## 4. External dependencies

Every external API, auth flow or non-public schema costs connection probing before a line of feature code works. One ingest task I measured took 8.0 minutes, and in it three connection routes to the same database failed before the approach changed. That probing is the time the premium stands for.

List each dependency in `external_deps`. The premium per type (15 minutes for an API key up to 75 for a streaming API) is in the topic-mix guide and in the config as `external_dep_premiums`. An unknown type gets the default of 25 minutes and a line in the risk flags.

## 5. Dependencies between features

`dependencies` lists the features that must finish before this one can start. The schema comes before the ingest pipelines, a stable backend before frontend integration. Leave it empty when a feature can start on day one.

The script refuses a dependency cycle and ignores a dependency on a feature that is not in the list, with a warning.

## 6. Run it

```bash
python3 scripts/compute_estimate.py --features my-features.json --project-name "My project" \
  --parallel-cap 3
```

Per feature and per band (median, p75 and p95):

```
minutes = (sum(blocks x topic minutes) x quality factor x extra factor + dependency premium)
          x overhead x confidence buffer
```

The report and a JSON record of the estimate go to `~/.claude/estimator/estimates/`. Keep the record: calibration compares against it.

## Why a band and not one number

A single number cannot be checked and cannot be defended. "70 hours" is wrong the moment the work takes longer, and nobody can tell whether that was bad luck or a bad estimate. A band says how much uncertainty there is, and calibration can test it: a well-set median band is exceeded about half the time, a p75 band about a quarter of the time.

The three bands also mean different things for a feature of many blocks, and that matters more than the labels suggest:

- **Median band.** Block times are right-skewed. In my full table, the mean block is 1.35 to 1.78 times the median block, depending on the topic. A feature of ten or twenty blocks totals close to blocks times the mean, so a sum of medians runs low. The confidence buffer lifts it somewhat, not all the way.
- **p75 band.** For a feature of many blocks this lands near the expected total. Treat it as the likely outcome.
- **p95 band.** Every block at its slow tail at once. That rarely happens by chance, but blocks within one feature are not independent: a hard feature is hard in all its blocks. Treat it as the planning buffer for a feature that turns out hard throughout.

The [PDF extractor example](examples.md#worked-estimate-1-one-feature) comes out at 4.2, 8.2 and 18.7 hours. The spread between those numbers is the information.

## The confidence buffer

The buffer comes from the lowest N among a feature's topics: 1.25 at 15 blocks or more, 1.4 from 5 to 14, 1.5 below 5 with a warning. A feature that leans on one thinly measured topic gets a wider band, and the report says which topic caused it. The thresholds are explained under [how many blocks before you trust a median](measuring.md#how-many-blocks-before-you-trust-a-median).

## Overhead

Your table only holds time inside Claude Code sessions. Meetings, demos, requirements, review outside a session and thinking away from the keyboard are not in it. `overhead` multiplies everything to cover that time.

I use 1.4 for client-facing work. Work without meetings or demos needs less. Do not guess for long: once you record total hours on a few finished features, `calibrate.py report` shows the overhead your work implies.

## Effort, critical path and wall-clock

Three different questions, three different numbers. The report gives all three per band.

| Number | Question | How it is computed |
|---|---|---|
| **Effort** | How many hours of work is this? | Sum of all features |
| **Critical path** | How fast could this go with unlimited parallel sessions? | Longest chain of dependencies |
| **Wall-clock** | How fast with the sessions I really run? | A schedule with at most `--parallel-cap` features in progress |

Effort is what you work and what you bill. Wall-clock is what the person waiting sees. Parallel sessions in separate worktrees shorten the wall-clock and leave the effort as it is.

The schedule is a list schedule. Whenever a slot is free, the ready feature with the longest chain still behind it starts first, so the critical path never waits behind a short side feature. A simpler plan that finishes every feature of one dependency level before the next level starts is easier to explain and wastes time: in the [knowledge-base example](examples.md#worked-estimate-2-eight-features-with-dependencies) it gives 20.3 hours where the list schedule gives 18.7.

`--parallel-cap` is how many features you really keep moving at once, not how many terminals you can open. A cap above the width of the dependency graph adds nothing: in the same example, two slots already reach the critical path and a third changes nothing. Your attention is the limit, so set the cap from what you actually ran on past projects.

`--hours-per-week` turns wall-clock hours into calendar weeks. Leave it out and the report stays in hours.

## What not to do

- **Pass on one number.** Always the band, with the median as the base and the p95 as the buffer.
- **Quote a speedup.** "Ten times faster than without AI" is not measured by any of this. Estimate in hours.
- **Forget dependencies.** An OAuth flow left out of `external_deps` is time the estimate does not have.
- **Mix effort and wall-clock.** A wall-clock in weeks and an effort in hours are different promises. Say which one you give.
- **Borrow a topic.** If the work has no topic in your table, say so in the estimate. A topic that looks close hides that you have no data.
