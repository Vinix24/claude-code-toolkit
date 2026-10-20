#!/bin/sh
# Shim between Claude Code and the slop-lint hook.
#
# A hook that exits 2 blocks the session, so this script never exits 2:
#   - CLAUDE_SLOP_LINT=off (exactly "off"): exit 0, nothing else happens.
#   - python is missing: one line on stderr, exit 1.
#   - the hook's own exit status 2 is mapped to 1; every other status passes through.
#
# SLOP_LINT_PYTHON picks the interpreter, for example a virtualenv that has
# python-docx so Word files are linted too. Default: python3 on PATH.

if [ "${CLAUDE_SLOP_LINT}" = "off" ]; then
  exit 0
fi

py="${SLOP_LINT_PYTHON:-python3}"
if ! command -v "$py" >/dev/null 2>&1; then
  echo "slop-lint: $py not found, hook skipped" >&2
  exit 1
fi

"$py" "$(dirname "$0")/post_write.py"
status=$?
if [ "$status" -eq 2 ]; then
  exit 1
fi
exit "$status"
