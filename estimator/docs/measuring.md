# Measuring your own codebase

An estimate is only as good as the table behind it. This page covers how `refresh_topic_stats.py` builds that table from your own transcripts, which choices it makes, and how to check them.

```bash
python3 scripts/refresh_topic_stats.py                 # gap blocks, all transcripts
python3 scripts/refresh_topic_stats.py --mode turn     # prompt-to-stop blocks
python3 scripts/refresh_topic_stats.py --snapshot      # also keep a dated copy for drift checks
```

The table lands in `~/.claude/estimator/topic-statistics.md` (set `ESTIMATOR_HOME` to move it). `compute_estimate.py` reads it from there on every run.

## Where the data comes from

Claude Code writes one JSONL file per session under `~/.claude/projects/<encoded folder>/`, or under `$CLAUDE_CONFIG_DIR/projects` when you run with your own config dir. Subagents get their own files in a `subagents/` folder next to the session.

Every line is an event with a timestamp, a type, the session id and the working directory. Assistant lines carry the tool calls and their inputs: file paths, commands, the old and new text of an edit. User lines carry your prompts and the tool results.

That is enough to reconstruct when work happened and what it was about. The script reads the files and writes nothing next to them.

## From events to work blocks

### Why not the session span

The obvious measure is first event to last event. On my own data that number is useless. One session I measured spanned 37.7 hours from first to last event, across two days. The two modules worked on in it had 147.5 and 91.2 active minutes.

Idle time has to go. There are two ways to cut it out, and the script supports both.

### Gap mode (the default)

A block ends at every pause longer than `--gap-min` minutes (default 5) between two events of the same session. Its duration is last event minus first event.

```
prompt ── tool ── tool ── answer      (pause under 5 min)      prompt ── tool ── answer
└──────────────────────── one block, short pause counted ─────────────────────────────┘

answer      (pause over 5 min: block ends, pause not counted)      prompt ── ...
```

Gap mode is how I measured the rows in `benchmarks.example.md`, and the block counts in the topic-mix guide come from the same method. Use it when you want numbers you can compare with mine.

It has two side effects. A short pause in which you read the answer and type the next prompt counts as work. A single tool call that runs longer than the gap (a slow test suite) splits the block and drops the wait.

### Turn mode (prompt-to-stop)

A turn runs from a prompt to the last event before the next prompt: that is when Claude stopped. Turns separated by at most `--gap-min` minutes of idle form one block. The block's duration is the sum of its turns, so the idle between turns is not counted, however short.

```
prompt ─[ Claude works ]─ stop   idle   prompt ─[ Claude works ]─ stop
└─────── counted ───────┘       not     └─────── counted ───────┘
```

This is the definition timekeeper uses for active time. A long tool call stays inside its turn and counts. Use turn mode when you want your block totals to reconcile with timekeeper.

Do not mix the modes in one table. The script rebuilds its block store when you switch mode or gap, because every block depends on them. The exact behaviour of both modes is pinned down in `tests/test_workblocks.py`.

### The mistake I made first

My first version cut a new block at every topic switch as well as at every gap. That gave 2,322 blocks and a `python_module` median of 0.20 minutes: twelve seconds. Those were single tool calls, not work.

Cutting on time only and giving each block its dominant topic gave 228 blocks and a `python_module` median of 7.8 minutes on the same data. If your medians come out in seconds, you are measuring tool calls.

### Very short blocks and automated runs

Blocks shorter than `--min-block-min` (default 1.0 minute) are left out of the table. That filter exists because of automated jobs: in one of my projects, a scheduled job produced 1,583 `data_cleaning` blocks of about 5 seconds each. They were real transcripts and they would have dragged that topic's median down to nothing.

If you run Claude Code headless from scripts or CI, look at what those transcripts contain. Raise `--min-block-min` or point `--projects` at the folders that hold the work you want to estimate.

### Subagents

Subagent transcripts overlap their parent session in time: the parent waits while the subagent works. My numbers include them, because a subagent block is work of a kind. When you compare totals with timekeeper, pass `--skip-subagents`, or the same minutes count twice.

## Classifying blocks into topics

The classifier is rule-based. No model is called, so the same transcript always gives the same topics.

Per event, the first matching rule wins:

1. **Tool name.** A database tool from any MCP server: `*__apply_migration` is `database_setup`, `*__execute_sql` and `*__list_tables` are `database_query`.
2. **Ordered patterns** over the file paths and text of the event: `database_setup`, `database_query`, `python_test`, `frontend_work`, `parser_work`, `api_integration`, `data_cleaning`, `deployment`, `documentation`, `python_module`. The order matters: a test file is `python_test` before it can be `python_module`.
3. **An error** in the text (a traceback, `FAILED`, `Error:`) with no other match is `bug_fix`.
4. **Everything else** is `analysis_only`: reading, searching, talking.

Per block, the topic is the most frequent topic among its events, with `analysis_only` left out whenever any other topic occurs. Reading is scaffolding around the work. A block that only reads stays `analysis_only`.

### How accurate it is

I checked three samples of 10 events by hand against their content. 7 of 10 were right, 1 was ambiguous (`analysis_only` against `python_module`) and 2 were probably wrong (`api_integration` against `python_module` for HTTP calls inside a Python file). So roughly 70 to 80% of events get the right label.

That is good enough for medians over hundreds of blocks, because the errors do not favour one topic. It is not good enough for a topic with a dozen blocks. Read those blocks yourself.

### Checking your own labels

The generated table ends with the longest blocks per topic, with folder, session and start time. Open a few of those sessions and count how many are what the label says. The longest blocks are where misclassified and idle-heavy blocks show up first, and they are what drives the p95.

### Adapting the rules to your stack

The default topics are the ones behind my table, and my work is mostly Python. A TypeScript or Go developer will see `python_module` stay empty and most work land in `documentation` or `analysis_only`.

Replace the rules in `~/.claude/estimator/config.json`. `topic_rules` is an ordered list of `[topic, regex]`; `tool_topics` is a list of `[tool-name regex, topic]`. Both replace the defaults when present.

```json
{
  "topic_rules": [
    ["database_setup", "(migrations/|CREATE\\s+TABLE|ALTER\\s+TABLE)"],
    ["ts_test", "(\\.test\\.tsx?$|\\.spec\\.tsx?$|vitest|jest)"],
    ["go_test", "_test\\.go$"],
    ["frontend_work", "(\\.tsx$|\\.jsx$|\\.css$)"],
    ["go_service", "\\.go$"],
    ["ts_module", "\\.ts$"],
    ["documentation", "(README\\.md|/docs/|\\.md$)"]
  ],
  "tool_topics": [["^mcp__.+__apply_migration$", "database_setup"]]
}
```

Whatever names you choose, use the same names in your topic-mix guide and your feature specs. The estimator matches them as plain strings.

## How many blocks before you trust a median

Few blocks give a median that moves a lot. Two facts from order statistics make that concrete, without any data of mine:

- **With 5 blocks**, the interval from your shortest to your longest block contains the true median only 94% of the time (1 minus 2 times 0.5 to the fifth). Your whole range is the uncertainty.
- **With 15 blocks**, a 96% interval for the median runs from your 4th to your 12th block. That is roughly the middle half of your data.

My own history shows the same. At N=9 my `frontend_work` median was 16.2 minutes. At N=385 it is 9.91. The [examples](examples.md#small-samples-lie) have the full comparison.

The estimator turns this into settings, all in the config:

| Lowest N among a feature's topics | Confidence buffer | Label |
|---|---:|---|
| 20 or more | 1.25 | high |
| 15 to 19 | 1.25 | medium |
| 10 to 14 | 1.4 | medium |
| 5 to 9 | 1.4 | low-medium |
| under 5 | 1.5, plus a warning in the report | low |

For a topic with a single block, I treat the median as discovery: plan two to four times the shown value and measure again after five or more blocks.

The p95 needs far more blocks than the median. It rests on the slowest 5% of blocks, and with 66 blocks that is about three of them. So the p95 of a topic settles long after its median does.

## Reading your table

| Column | What it tells you |
|---|---|
| N blocks | How much the row rests on. See the thresholds above. |
| Median min | The 50/50 point for one block. |
| Mean min | Above the median, because block times are right-skewed. A feature of many blocks totals close to blocks times mean. |
| p25, p75, p95 | The spread. A p95 above three times the median means a long tail: first-time work, debugging spirals or misclassified blocks. |
| Mean tool-calls, Mean errors | How busy a block is. Many errors per block marks the work that eats buffers. |
| Total hours | Where your time went. |
| Median lines, Min per 100 lines | Lines changed through Edit, MultiEdit and Write, generated files excluded. Edits through Bash are invisible. A sanity check for a band, not an estimate input: estimating minutes from lines would mean guessing the diff size first. |

You can keep hand-written notes under the generated table: put them in `~/.claude/estimator/topic-statistics-notes.md` and every refresh appends them.

## Cross-checking with timekeeper

[timekeeper](https://github.com/Vinix24/claude-code-toolkit/tree/main/timekeeper) measures active time with two hooks, prompt to stop, per working directory. Turn mode measures the same thing from the transcripts. On a period where the hooks were installed, the two should land close together:

```bash
python3 scripts/refresh_topic_stats.py --mode turn --skip-subagents --min-block-min 0 \
  --path ~/work/app --since 2026-10-01 --until 2026-10-01 --summary-json /tmp/day.json
python3 ../timekeeper/report.py --path ~/work/app --date 2026-10-01
```

Compare `minutes` in the JSON with the active hours in the report. A large difference usually means one of three things: the hooks were not installed for part of the period, sessions ran in a folder outside the path, or subagents were counted. timekeeper filters its time logs by local date and the refresh by UTC date, so near midnight expect small differences.

The cross-check runs in turn mode, while your main table may be in gap mode. Switching rebuilds the block store, so give the check its own data folder: `ESTIMATOR_HOME=/tmp/check python3 scripts/refresh_topic_stats.py --mode turn ...`.
