#!/usr/bin/env bash
#
# TokenSaver uninstaller. Removes the honesty block from CLAUDE.md and unwinds
# graphify. Leaves your own CLAUDE.md content and unrelated settings untouched.
#
# Usage: ./uninstall.sh [PROJECT_DIR]   (defaults to current directory)
set -uo pipefail

PROJECT_DIR="${1:-$(pwd)}"
PY="$(command -v python3 || true)"
cd "$PROJECT_DIR" || { echo "cannot cd to $PROJECT_DIR" >&2; exit 1; }

# remove the honesty managed block (and nothing else)
if [ -n "$PY" ] && [ -f CLAUDE.md ]; then
  "$PY" - CLAUDE.md <<'PY'
import re, sys, pathlib
p = pathlib.Path(sys.argv[1])
t = p.read_text()
t = re.sub(
    r"\n*<!-- BEGIN: TokenSaver honesty layer -->.*?<!-- END: TokenSaver honesty layer -->\n*",
    "\n",
    t,
    flags=re.DOTALL,
)
p.write_text(t)
print("removed honesty block from CLAUDE.md")
PY
fi

# unwind graphify (removes its skill + graphify-out/)
if command -v graphify >/dev/null 2>&1; then
  graphify uninstall --purge >/dev/null 2>&1 || true
  echo "ran graphify uninstall --purge"
fi

echo "[TokenSaver] uninstalled. NOTE: refresh hooks in .claude/settings.json are left in place;"
echo "remove the entries pointing at tokensaver-refresh.sh by hand if you want them gone."
