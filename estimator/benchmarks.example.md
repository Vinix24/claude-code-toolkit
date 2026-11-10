# Example benchmarks: one developer's measured work blocks

These are my measurements, not yours. I took them from my own Claude Code transcripts. They are here so the estimator runs on day one and so you can see what a benchmark table looks like.

Replace them as soon as you can. Run `scripts/refresh_topic_stats.py` on your own transcripts and the estimator picks up your table instead of this one. Your stack, your prompting style and your models give different numbers, and an estimate is only as good as the table behind it.

## How these rows were measured

- **Source:** my Claude Code transcripts from February to November 2026, measured across my own projects. Interactive and headless sessions, a mix of models.
- **Blocks:** `gap` mode. A block ends at every pause longer than 5 minutes between two transcript events. Blocks shorter than 1 minute are left out.
- **Topic:** the dominant topic among a block's events, from the rule-based classifier in `scripts/workblocks.py`. My private copy of those rules held a few names specific to my own setup; the public rules are the generic form.
- **Table date:** generated on 7 November 2026.
- **Selection:** 11 of the 16 topics in that table, and 5 of its 11 columns. Left out: `analysis_only` (reading and searching, never planned as work) and four topics with a single block each.

## Minutes per work block

| Topic | N blocks | Median min | p75 | p95 |
|---|---:|---:|---:|---:|
| python_test | 2550 | 7.79 | 14.64 | 31.47 |
| python_module | 2354 | 7.54 | 15.19 | 37.17 |
| documentation | 1990 | 6.34 | 12.91 | 31.49 |
| bug_fix | 1922 | 5.76 | 11.99 | 33.35 |
| parser_work | 1090 | 6.66 | 12.89 | 30.55 |
| database_query | 582 | 7.41 | 13.49 | 31.99 |
| database_setup | 522 | 7.68 | 14.27 | 34.29 |
| frontend_work | 385 | 9.91 | 19.84 | 48.83 |
| deployment | 263 | 6.05 | 9.80 | 23.49 |
| data_cleaning | 241 | 4.80 | 10.30 | 27.92 |
| api_integration | 230 | 7.09 | 13.71 | 27.71 |

## Reading it

- A block is a stretch of continuous work on one topic, not a task. The medians here run from 4.80 to 9.91 minutes; a feature is many blocks.
- The p95 is 3.9 to 5.8 times the median, depending on the topic. That tail is where estimates go wrong, which is why the estimator reports bands.
- `frontend_work` has both the longest median (9.91 min) and the widest tail (48.83 min at p95).
- The minutes are time inside Claude Code sessions with idle left out. Meetings, reviews and thinking away from the keyboard are not in them: the `overhead` factor covers those.
