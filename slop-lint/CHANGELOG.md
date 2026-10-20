# Changelog

## 1.0.0 (2026-10-20)

First public version.

- Deterministic linter for Dutch prose in three layers: a closed word list, comma
  structure and rhetorical frames. 25 rules, measured on a corpus of over 300,000 words.
- PostToolUse hook on Write and Edit: lints the file Claude just wrote and hands the
  findings back as context. Never blocks.
- Skill `slop-check` for on-demand checks. The skill folder is self-contained, so it can
  also be used without the rest of the plugin.
- Configuration in `.claude/slop-lint.json` (project) and `~/.claude/slop-lint.json`
  (user): switch rules off, add your own, set the scope, the word floor and a density
  threshold.
