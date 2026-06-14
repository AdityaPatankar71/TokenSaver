#!/usr/bin/env bash
#
# TokenSaver installer
# Wires three things into a project so Claude Code uses fewer tokens and pushes
# back honestly:
#   1. graphify  — code graph; Claude queries pointers instead of re-reading files
#   2. honesty   — anti-sycophancy CLAUDE.md block (this project's own contribution)
#   3. caveman   — output compression (optional, --with-caveman)
#
# Idempotent. Safe to re-run. Only edits managed blocks; never clobbers your config.
#
# Usage:
#   ./install.sh [PROJECT_DIR] [--with-caveman]
# Defaults PROJECT_DIR to the current directory.

set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"

# Self-bootstrap: when run via `curl ... | bash` (or anywhere our sibling files
# aren't sitting next to this script), clone the repo to a temp dir and re-exec
# from there. Lets users install with one command, no manual git clone. cwd is
# preserved across exec, so PROJECT_DIR still defaults to their project folder.
if [ ! -f "${REPO_DIR:-/nonexistent}/lib/merge_block.py" ] && [ -z "${TOKENSAVER_BOOTSTRAPPED:-}" ]; then
  command -v git >/dev/null 2>&1 || { echo "[TokenSaver] ERROR: git is required to bootstrap." >&2; exit 1; }
  _ts_tmp="$(mktemp -d)"
  echo "[TokenSaver] fetching TokenSaver into a temp dir..."
  git clone --depth 1 -q https://github.com/AdityaPatankar71/TokenSaver "$_ts_tmp/TokenSaver" \
    || { echo "[TokenSaver] ERROR: clone failed." >&2; exit 1; }
  export TOKENSAVER_BOOTSTRAPPED=1
  exec bash "$_ts_tmp/TokenSaver/install.sh" "$@"
fi

PROJECT_DIR=""
WITH_CAVEMAN=0
PY="$(command -v python3 || true)"

for arg in "$@"; do
  case "$arg" in
    --with-caveman) WITH_CAVEMAN=1 ;;
    -*) ;;  # ignore unknown flags
    *) PROJECT_DIR="$arg" ;;
  esac
done
[ -n "$PROJECT_DIR" ] || PROJECT_DIR="$(pwd)"

say()  { printf '\033[1m[TokenSaver]\033[0m %s\n' "$*"; }
warn() { printf '\033[33m[TokenSaver] WARN:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[31m[TokenSaver] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

# ---- preflight ----
[ -n "$PY" ] || die "python3 not found (graphify needs >=3.10)."
cd "$PROJECT_DIR" || die "cannot cd to $PROJECT_DIR"
say "target project: $PROJECT_DIR"

# ---- 1. ensure graphify is installed ----
if ! command -v graphify >/dev/null 2>&1; then
  if command -v uv >/dev/null 2>&1; then
    say "installing graphify via uv (recommended)..."
    uv tool install graphifyy || die "uv tool install graphifyy failed"
  elif command -v pipx >/dev/null 2>&1; then
    say "installing graphify via pipx..."
    pipx install graphifyy || die "pipx install graphifyy failed"
  else
    warn "no uv/pipx found; graphify docs discourage pip on mac/windows, but trying it."
    "$PY" -m pip install --user graphifyy || die "pip install graphifyy failed"
  fi
fi
command -v graphify >/dev/null 2>&1 || die "graphify not on PATH after install (check your PATH)."

# ---- 2. graphify's own claude wiring + initial graph ----
say "wiring graphify into Claude + building initial graph (AST, no LLM)..."
graphify install --project >/dev/null 2>&1 || warn "graphify install --project returned nonzero"
graphify update .          >/dev/null 2>&1 || warn "initial graph build returned nonzero"
if [ -d .git ]; then
  graphify hook install    >/dev/null 2>&1 || warn "graphify hook install returned nonzero (git post-commit auto-rebuild)"
fi

# ---- 3. honesty layer (managed block, never clobbers your CLAUDE.md) ----
say "injecting honesty layer into CLAUDE.md..."
"$PY" "$REPO_DIR/lib/merge_block.py" "CLAUDE.md" "$REPO_DIR/templates/CLAUDE.honesty.md" \
  || die "honesty block merge failed"

# ---- 4. incremental-refresh hooks (SessionStart + PostToolUse) ----
say "registering incremental-refresh hooks in .claude/settings.json..."
HOOK="$REPO_DIR/hooks/tokensaver-refresh.sh"
chmod +x "$HOOK" 2>/dev/null || true
FRAG="$(mktemp)"
sed "s|__LEAN_HOOK__|$HOOK|g" "$REPO_DIR/templates/settings.hooks.json" > "$FRAG"
"$PY" "$REPO_DIR/lib/merge_settings.py" ".claude/settings.json" "$FRAG" \
  || { rm -f "$FRAG"; die "settings merge failed"; }
rm -f "$FRAG"

# ---- 5. caveman (optional, off by default: pipes a remote script to bash) ----
if [ "$WITH_CAVEMAN" = 1 ]; then
  say "installing caveman output compression (remote script)..."
  curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash \
    || warn "caveman install failed (install it yourself from github.com/JuliusBrussee/caveman)"
else
  say "skipped caveman. re-run with --with-caveman to add output compression."
fi

say "done. open Claude in this project — graph + honesty active."
say "sanity check: graphify query \"how does X work\" --budget 500"
