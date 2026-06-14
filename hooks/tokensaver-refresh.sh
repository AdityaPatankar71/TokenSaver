#!/usr/bin/env bash
# TokenSaver: incremental code-graph refresh.
#
# Wired into Claude Code as a SessionStart hook (matchers: startup, resume — to
# catch edits made outside the session: git pull, other editor, teammate commits)
# and a PostToolUse hook on Edit/Write (catches edits Claude makes mid-session).
# Both run the same cheap command — graphify's stat-index means only changed files
# are reparsed, so this is ~0.2s on a small repo and stays cheap on big ones (no
# full rebuild, no LLM).
#
# Always exits 0 so a graph hiccup never blocks Claude.
set -uo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$ROOT" 2>/dev/null || exit 0
command -v graphify >/dev/null 2>&1 || exit 0

graphify update . >/dev/null 2>&1 || true
exit 0
