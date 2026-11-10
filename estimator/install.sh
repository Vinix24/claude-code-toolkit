#!/bin/bash
# Install the estimator skill into the Claude Code skills folder.
# Safe to re-run: it replaces the skill's own files and leaves your data in ~/.claude/estimator alone.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
DST="$CONFIG_DIR/skills/estimator"
DATA="${ESTIMATOR_HOME:-$HOME/.claude/estimator}"

command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 is required."; exit 1; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' \
  || { echo "ERROR: python3 3.9 or newer is required."; exit 1; }

mkdir -p "$DST/scripts" "$DST/references" "$DATA"
cp "$HERE/SKILL.md" "$HERE/benchmarks.example.md" "$DST/"
cp "$HERE/references/topic-mix-guide.md" "$DST/references/"
cp "$HERE"/scripts/*.py "$DST/scripts/"
chmod +x "$DST"/scripts/compute_estimate.py "$DST"/scripts/refresh_topic_stats.py "$DST"/scripts/calibrate.py
echo "[ok] skill installed in $DST"
echo "[ok] data folder: $DATA"
echo
echo "Next: build your own benchmark table from your transcripts (the first run reads them all):"
echo "  python3 \"$DST/scripts/refresh_topic_stats.py\""
echo "Then ask Claude Code to estimate a PRD; the skill picks up $DATA/topic-statistics.md."
