#!/bin/bash
# Install the two Claude Code hooks and register them in ~/.claude/settings.json.
# Idempotent: safe to re-run. Backs up settings.json before editing.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_SRC="$REPO_DIR/hooks"
HOOKS_DST="$HOME/.claude/hooks"
SETTINGS="$HOME/.claude/settings.json"

command -v /usr/bin/jq >/dev/null 2>&1 || { echo "FOUT: jq vereist (/usr/bin/jq). Installeer jq."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "FOUT: python3 vereist."; exit 1; }

mkdir -p "$HOOKS_DST"
cp "$HOOKS_SRC/log-prompt-time.sh" "$HOOKS_DST/"
cp "$HOOKS_SRC/log-stop-time.sh" "$HOOKS_DST/"
chmod +x "$HOOKS_DST/log-prompt-time.sh" "$HOOKS_DST/log-stop-time.sh"
echo "[ok] hooks gekopieerd naar $HOOKS_DST"

[ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"
cp "$SETTINGS" "$SETTINGS.bak"

python3 - "$SETTINGS" "$HOOKS_DST" <<'PY'
import json, sys
settings_path, hooks_dst = sys.argv[1], sys.argv[2]
d = json.load(open(settings_path))
hooks = d.setdefault("hooks", {})

def ensure(event, cmd):
    arr = hooks.setdefault(event, [])
    if any(h.get("command") == cmd for blk in arr for h in blk.get("hooks", [])):
        return False
    arr.append({"matcher": "", "hooks": [{"type": "command", "command": cmd}]})
    return True

a = ensure("UserPromptSubmit", f"{hooks_dst}/log-prompt-time.sh")
b = ensure("Stop", f"{hooks_dst}/log-stop-time.sh")
json.dump(d, open(settings_path, "w"), indent=2, ensure_ascii=False)
open(settings_path, "a").write("\n")
print(f"[ok] UserPromptSubmit hook {'toegevoegd' if a else 'stond al geregistreerd'}")
print(f"[ok] Stop hook {'toegevoegd' if b else 'stond al geregistreerd'}")
PY

echo "[ok] settings.json bijgewerkt (backup: $SETTINGS.bak)"
echo
echo "Klaar. Hooks pakken vanaf een NIEUWE Claude Code-sessie."
echo "Rapport draaien:  python3 \"$REPO_DIR/report.py\" --path /pad/naar/map"
