# Examples from my measurements

A limited selection from my own data: what a block of each kind of work takes me, what measuring it taught me, and two worked estimates. Everything here is measured on my own Claude Code transcripts or computed by the scripts from those measurements. None of it is a benchmark for your work. It shows what a table looks like and how to read one.

## Minutes per work block

These are the rows in `benchmarks.example.md`: 11 of the 16 topics in my table of 7 November 2026, measured across my own projects from February to November 2026, gap mode with a 5-minute gap and blocks under 1 minute left out.

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

What I read in it:

- **A block is small.** Medians run from 4.80 to 9.91 minutes. A feature in my topic-mix guide is 3 to 40 blocks, so the counting matters more than any single median.
- **The tail is long everywhere.** The p95 is 3.9 to 5.8 times the median. One number per topic would hide exactly the part that makes estimates fail.
- **The mean is not the median.** In my full table the mean block is 1.35 to 1.78 times the median block, computed from the total hours and N per topic. That is why the median band of a large feature runs low; see [why a band](prd-to-estimate.md#why-a-band-and-not-one-number).
- **Frontend work is the slowest per block** (median 9.91, p95 48.83). **Deployment has the shortest tail** (p95 23.49).
- **Debugging is not rare.** `bug_fix` has 1,922 blocks. Planning no debugging means planning to be surprised.

## Small samples lie

In May 2026 my table rested on 228 blocks. Six of its rows next to the same topics in November:

| Topic | May N | May median | November N | November median |
|---|---:|---:|---:|---:|
| python_test | 66 | 6.6 | 2550 | 7.79 |
| python_module | 57 | 7.8 | 2354 | 7.54 |
| documentation | 23 | 8.6 | 1990 | 6.34 |
| api_integration | 9 | 10.9 | 230 | 7.09 |
| frontend_work | 9 | 16.2 | 385 | 9.91 |
| bug_fix | 4 | 6.4 | 1922 | 5.76 |

`calibrate.py drift` on those two tables:

| Topic | Old N | New N | Old median | New median | Median ratio | p95 ratio | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| api_integration | 9 | 230 | 10.90 | 7.09 | 0.65 | 1.91 | small N |
| bug_fix | 4 | 1922 | 6.40 | 5.76 | 0.90 | 3.33 | small N |
| documentation | 23 | 1990 | 8.60 | 6.34 | 0.74 | 1.83 | drift |
| frontend_work | 9 | 385 | 16.20 | 9.91 | 0.61 | 0.87 | small N |
| python_module | 57 | 2354 | 7.80 | 7.54 | 0.97 | 1.26 | stable |
| python_test | 66 | 2550 | 6.60 | 7.79 | 1.18 | 1.76 | stable |

The rows with 57 and 66 blocks moved by 3% and 18%, inside the 20% tolerance. The two rows with 9 blocks moved by 35% and 39%. The p95s moved most of all: at N=4, the "p95" of `bug_fix` was little more than its longest block.

Two things changed at once between May and November, so this is not a clean drift measurement. The sample grew, and so did the method. In May I read only the large transcripts (500 KB and up) from six project folders. In November I read every transcript, interactive and headless, across several models. Blocks under a minute were left out. What it does show is the lesson I took from it: a median on nine blocks is a guess.

It shows in an estimate as well. The dashboard feature from worked estimate 2 below, computed on the May rows, comes out at 9.4 / 12.0 / 27.3 hours. On the November rows it is 6.0 / 11.8 / 27.3. The median band dropped by more than a third, because it leaned on a `frontend_work` median measured on nine blocks.

## What measuring taught me

- **Session span is not work.** One session I measured spanned 37.7 hours from first to last event, across two days. The two modules worked on in it had 147.5 and 91.2 active minutes.
- **Tool calls are not work blocks.** My first segmentation cut at every topic switch and found a `python_module` median of 0.20 minutes, across 2,322 blocks. Cutting on time only gave 228 blocks and a median of 7.8 minutes.
- **Automated runs pollute a table.** A scheduled job in one of my projects produced 1,583 `data_cleaning` blocks of about 5 seconds each. The one-minute minimum block length exists because of them.
- **A rule-based classifier is right often enough, not always.** My hand check of three samples of 10 events found 7 right, 1 ambiguous and 2 probably wrong.
- **Connections cost time before code does.** In one ingest task of 8.0 minutes, three connection routes to the same database failed before the approach changed. That is what the dependency premium stands for.

## Worked estimate 1: one feature

Adding a PDF extractor to an existing Python service. The spec (`examples/pdf-extractor.features.json`):

```json
{"feature_id": "pdf-extractor", "topic_blocks": {"parser_work": 3, "python_test": 4, "python_module": 2},
 "external_deps": [], "dependencies": [], "quality_target": "production-ready"}
```

The arithmetic for the median band, with the example table and the default settings:

| Step | Median | p75 | p95 |
|---|---:|---:|---:|
| Block minutes: 3 x parser_work + 4 x python_test + 2 x python_module | 66.22 | 127.61 | 291.87 |
| x quality 2.2, x overhead 1.4, x buffer 1.25 (lowest N is 1090) | 254.95 | 491.30 | 1123.70 |
| **Hours** | **4.2** | **8.2** | **18.7** |

One feature, so effort and wall-clock are the same. The median band of 4.2 hours is the base, 8.2 the likely outcome, and 18.7 the buffer for a feature that turns out hard throughout.

## Worked estimate 2: eight features with dependencies

A knowledge-base module: a vector index, two connectors, an embedding pipeline, a retrieval server, an evaluation loop, a dashboard and a deploy. The block counts are the lower end of each range in the topic-mix guide, every feature `production-ready`. I added an API-key dependency for the embedding API and for the retrieval server, and an OAuth dependency for one connector. The spec is `examples/knowledge-base.features.json`.

| ID | Topic blocks | Min N | Median h | p75 h | p95 h | Depends on |
|---|---|---:|---:|---:|---:|---|
| `schema` | database_setup x3, python_test x2 | 522 | 2.5 | 4.6 | 10.6 | - |
| `connector-oauth` | parser_work x4, api_integration x4, python_test x3, python_module x1 | 230 | 6.4 | 11.5 | 24.3 | schema |
| `connector-files` | parser_work x3, python_test x2 | 1090 | 2.3 | 4.4 | 9.9 | schema |
| `embedding` | python_module x4, python_test x3, api_integration x2 | 230 | 4.8 | 8.9 | 19.6 | schema |
| `retrieval-server` | python_module x4, python_test x3, documentation x1 | 1990 | 4.3 | 8.0 | 18.1 | embedding |
| `eval-loop` | python_module x4, python_test x3, documentation x1 | 1990 | 3.8 | 7.5 | 17.6 | retrieval-server |
| `dashboard` | frontend_work x5, python_test x3, api_integration x2, documentation x1 | 230 | 6.0 | 11.8 | 27.3 | retrieval-server |
| `deploy` | deployment x2, documentation x1 | 263 | 1.2 | 2.1 | 5.0 | eval-loop, dashboard, connector-oauth, connector-files |

Totals in hours, median / p75 / p95:

| | Median | p75 | p95 |
|---|---:|---:|---:|
| Effort (sum of all features) | 31.2 | 58.8 | 132.4 |
| Critical path (schema > embedding > retrieval-server > dashboard > deploy) | 18.7 | 35.4 | 80.6 |
| Wall-clock, one feature at a time | 31.2 | 58.8 | 132.4 |
| Wall-clock, at most two at once | 18.7 | 35.4 | 80.6 |
| Wall-clock, at most three at once | 18.7 | 35.4 | 80.6 |

What it says:

- **Effort and wall-clock differ by 1.67 times** on the median band. That is the gain from running features in parallel, and it costs no fewer hours of work.
- **Two slots are enough.** With two, the OAuth connector runs next to the embedding pipeline and the file connector next to the retrieval server, both off the critical path. A third slot finds nothing left to shorten.
- **The schedule matters.** Planning level by level (finish the three features after the schema before starting the retrieval server) gives 20.3 hours on the median band against 18.7 for the list schedule. The retrieval server would wait for the OAuth connector, which nothing on the critical path needs.
- **The OAuth connector and the dashboard drive the risk.** They have the widest bands (p95 24.3 and 27.3 hours). Both lean on `api_integration`, the topic with the fewest blocks in the table. The dashboard also leans on `frontend_work`, the topic with the longest tail.

## Rerun them yourself

From the `estimator/` folder:

```bash
python3 scripts/compute_estimate.py --features examples/pdf-extractor.features.json \
  --benchmarks benchmarks.example.md --project-name "PDF extractor"
python3 scripts/compute_estimate.py --features examples/knowledge-base.features.json \
  --benchmarks benchmarks.example.md --project-name "Knowledge base" --parallel-cap 2
```

Then run the same two specs against your own table, without `--benchmarks`. The difference between the two reports is the difference between my work and yours.
