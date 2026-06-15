#!/bin/bash
# Log every UserPromptSubmit timestamp + cwd + session_id to ~/.claude/prompt-times.jsonl
# Paired with stop-times.jsonl to compute ACTIVE work time (prompt -> stop).
INPUT=$(cat)
TS_UTC=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TS_LOCAL=$(date "+%Y-%m-%dT%H:%M:%S%z")
echo "$INPUT" | /usr/bin/jq -c --arg utc "$TS_UTC" --arg local "$TS_LOCAL" \
  '{ts_utc: $utc, ts_local: $local, session_id: .session_id, cwd: .cwd, event: "prompt"}' \
  >> ~/.claude/prompt-times.jsonl
exit 0
