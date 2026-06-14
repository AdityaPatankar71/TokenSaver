"""Tests for lib/merge_settings.py — the .claude/settings.json hook merger.

Asserts hooks are added, user config is preserved, the merge is idempotent,
both SessionStart matchers land, and a missing file is created.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "lib" / "merge_settings.py"

FRAGMENT = {
    "hooks": {
        "SessionStart": [
            {"matcher": "startup", "hooks": [{"type": "command", "command": "/x/refresh.sh"}]},
            {"matcher": "resume", "hooks": [{"type": "command", "command": "/x/refresh.sh"}]},
        ],
        "PostToolUse": [
            {"matcher": "Edit|Write", "hooks": [{"type": "command", "command": "/x/refresh.sh"}]},
        ],
    }
}


def run(target, fragment):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(target), str(fragment)],
        capture_output=True, text=True,
    )


def write_frag(tmp_path):
    f = tmp_path / "frag.json"
    f.write_text(json.dumps(FRAGMENT))
    return f


def test_adds_to_empty(tmp_path):
    t = tmp_path / "settings.json"
    r = run(t, write_frag(tmp_path))
    assert r.returncode == 0, r.stderr
    d = json.loads(t.read_text())
    matchers = [e["matcher"] for e in d["hooks"]["SessionStart"]]
    assert "startup" in matchers and "resume" in matchers
    assert d["hooks"]["PostToolUse"][0]["matcher"] == "Edit|Write"


def test_preserves_user_config(tmp_path):
    t = tmp_path / "settings.json"
    t.write_text(json.dumps({
        "model": "opus",
        "hooks": {"PostToolUse": [
            {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo guard"}]}
        ]},
    }))
    run(t, write_frag(tmp_path))
    d = json.loads(t.read_text())
    assert d["model"] == "opus"
    cmds = [h["command"] for e in d["hooks"]["PostToolUse"] for h in e["hooks"]]
    assert "echo guard" in cmds  # user hook kept
    assert "/x/refresh.sh" in cmds  # ours added alongside


def test_idempotent(tmp_path):
    t = tmp_path / "settings.json"
    frag = write_frag(tmp_path)
    for _ in range(3):
        run(t, frag)
    d = json.loads(t.read_text())
    n = sum(
        1
        for e in d["hooks"]["SessionStart"] + d["hooks"]["PostToolUse"]
        for h in e["hooks"]
        if h["command"] == "/x/refresh.sh"
    )
    assert n == 3  # startup + resume + posttooluse, no duplicates


def test_creates_file_if_missing(tmp_path):
    t = tmp_path / "nested" / "settings.json"
    assert run(t, write_frag(tmp_path)).returncode == 0
    assert t.exists()
