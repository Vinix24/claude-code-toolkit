# claude-code-toolkit

Small, composable, local-first tools for [Claude Code](https://claude.com/claude-code). Each lives in its own folder, is independently usable, and ships with its own README. No telemetry, nothing leaves your machine.

## Tools

| Tool | What it does |
|------|--------------|
| [`timekeeper/`](timekeeper/) | Measure *active* work time per session (prompt-to-stop, idle excluded), plus token usage and API-equivalent cost per working directory. Two hooks + one reporting script. |
| [`context-rotation/`](context-rotation/) | Measures how full a Claude Code session's context is, warns before it degrades, and carries a checked handover into a fresh session after /clear. |
| [`slop-lint/`](slop-lint/) | Deterministic linter for AI tics in Dutch prose. Lints every text file Claude writes and hands the findings back; a skill runs the same check on demand, also in Claude Desktop. |
| [`codex-image/`](codex-image/) | Sends image prompts to OpenAI through your own Codex CLI login and prepares blog/LinkedIn PNGs, with a local archive and daily cap. |

More tools land here over time. Each folder is self-contained: read its README, run its installer.

## Philosophy

- **Local-first.** Tools read and write under `~/.claude/` and your local transcripts. Nothing is sent anywhere.
- **Composable.** Each tool does one thing and is usable on its own.
- **Honest numbers.** Where a tool reports cost, it labels it as the API-equivalent (list rates), not your subscription bill.

## Install

Per tool. For example:

```bash
git clone https://github.com/Vinix24/claude-code-toolkit
cd claude-code-toolkit/timekeeper
./install.sh
```

## License

MIT. See [`LICENSE`](LICENSE).
