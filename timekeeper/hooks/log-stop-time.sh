#!/bin/bash
# Log every Stop (turn-end) timestamp + cwd + session_id to ~/.claude/stop-times.jsonl
# Active work time = sum of (Stop - UserPromptSubmit) per turn: counts tool-call
# and generation time, excludes idle between turns.
INPUT=$(cat)
TS_UTC=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TS_LOCAL=$(date "+%Y-%m-%dT%H:%M:%S%z")
echo "$INPUT" | /usr/bin/jq -c --arg utc "$TS_UTC" --arg local "$TS_LOCAL" \
  '{ts_utc: $utc, ts_local: $local, session_id: .session_id, cwd: .cwd, event: "stop"}' \
  >> ~/.claude/stop-times.jsonl
exit 0
