# claude-code-toolkit

Small, composable, local-first tools for [Claude Code](https://claude.com/claude-code). Each lives in its own folder of the [repository](https://github.com/Vinix24/claude-code-toolkit), works on its own and ships with its own README. No telemetry, nothing leaves your machine.

This site covers two of them, the ones that measure time:

| Tool | What it does |
|---|---|
| [Timekeeper](timekeeper.md) | Measures *active* work time per session (prompt to stop, idle excluded), plus token usage and API-equivalent cost per working directory. |
| [Estimator](estimator/index.md) | Turns your own transcripts into minutes per work block, a PRD into hour bands and a wall-clock time, and finished work into calibration of the next estimate. |

They fit together. Timekeeper says how long a folder of work took. The estimator says how long the next one will take, and uses the same prompt-to-stop definition when you ask it to.

The other tools in the repository are described in its [README](https://github.com/Vinix24/claude-code-toolkit#tools).
