# claude-code-toolkit

Small, composable, local-first tools for [Claude Code](https://claude.com/claude-code). Each lives in its own folder, is independently usable, and ships with its own README. No telemetry. Of the scripts, only `php-lek-check` makes a network request, to your own site. Skills such as `reverse-engineer` let Claude search the web with its own tools. Everything a tool hands to Claude, such as linter findings, a handover or a check result, becomes part of your Claude session, like anything else you type there.

## Tools

| Tool | What it does |
|------|--------------|
| [`timekeeper/`](timekeeper/) | Measure *active* work time per session (prompt-to-stop, idle excluded), plus token usage and API-equivalent cost per working directory. Two hooks + one reporting script. |
| [`context-rotation/`](context-rotation/) | Measures how full a Claude Code session's context is, warns before it degrades, and carries a checked handover into a fresh session after /clear. |
| [`slop-lint/`](slop-lint/) | Deterministic linter for AI tics in Dutch prose. Lints every text file Claude writes and hands the findings back; a skill runs the same check on demand, also in Claude Desktop. |
| [`context-meter/`](context-meter/) | One line above the prompt that shows how full the context is, in the bands of the context-rotation guard: green, yellow and red. |
| [`php-lek-check/`](php-lek-check/) | Dutch check for website owners on PHP2Shell: reads the PHP signals your own site shows and writes a message for your host. Its README opens with that message, because for most owners the message is all they need. It fetches one page of your own site and follows at most five redirects on the same host. |
| [`reverse-engineer/`](reverse-engineer/) | Dutch skill that helps you build what a LinkedIn post promises or asks for. Chooses the form first, from a paste prompt to "just buy it", and names the hard part, the time and what self-build does not do. Ships with a paste prompt for ChatGPT and Claude in the browser. |
| [`onder-de-motorkap/`](onder-de-motorkap/) | Dutch skill that explains what each part of an AI build does and why, also for someone else's tool. Every statement is labelled seen, inferred or unknown. Ships with a paste prompt. |

More tools land here over time. Each folder is self-contained: read its README, run its installer.

## DIY

Each folder under [`diy/`](diy/) is the ready-made version of one DIY blog on [vincentvandeth.nl](https://vincentvandeth.nl/blog). The blog explains how to build it yourself; the folder is for whoever would rather not. Its README links to the blog. Two of them install as a plugin: `briefing-presentaties` and `linkedin-redactie`.

## Philosophy

- **Local-first.** The scripts read and write under `~/.claude/`, your local transcripts and your own project folder. None of them has its own server or telemetry. `php-lek-check` only requests your own site. What a hook or skill shows Claude goes into your Claude session, and the paste prompts run in the Claude or ChatGPT you already use.
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
