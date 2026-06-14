"""Tests for lib/merge_block.py — the managed-block CLAUDE.md merger.

Invokes the script as a subprocess (same entry point users get) and asserts on
the resulting file: append, idempotency, in-place update, non-clobber, and
error on a malformed source.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "lib" / "merge_block.py"
HONESTY = REPO / "templates" / "CLAUDE.honesty.md"


def run(target, source):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(target), str(source)],
        capture_output=True, text=True,
    )


def write_block(path, name, body):
    path.write_text(f"<!-- BEGIN: {name} -->\n{body}\n<!-- END: {name} -->\n")
    return path


def test_appends_and_preserves_user_content(tmp_path):
    t = tmp_path / "CLAUDE.md"
    t.write_text("# My App\n\nkeep this line\n")
    r = run(t, HONESTY)
    assert r.returncode == 0, r.stderr
    out = t.read_text()
    assert "keep this line" in out
    assert "BEGIN: TokenSaver honesty layer" in out


def test_idempotent(tmp_path):
    t = tmp_path / "CLAUDE.md"
    t.write_text("# App\n")
    for _ in range(3):
        assert run(t, HONESTY).returncode == 0
    out = t.read_text()
    assert out.count("BEGIN: TokenSaver honesty layer") == 1
    assert out.count("END: TokenSaver honesty layer") == 1


def test_creates_file_if_missing(tmp_path):
    t = tmp_path / "sub" / "CLAUDE.md"
    assert run(t, HONESTY).returncode == 0
    assert t.exists()
    assert "BEGIN: TokenSaver honesty layer" in t.read_text()


def test_updates_block_in_place(tmp_path):
    t = tmp_path / "CLAUDE.md"
    t.write_text("# App\nuser line\n")
    src1 = write_block(tmp_path / "s1.md", "demo block", "VERSION ONE")
    src2 = write_block(tmp_path / "s2.md", "demo block", "VERSION TWO")
    run(t, src1)
    run(t, src2)
    out = t.read_text()
    assert out.count("BEGIN: demo block") == 1
    assert "VERSION TWO" in out
    assert "VERSION ONE" not in out
    assert "user line" in out


def test_missing_marker_errors(tmp_path):
    t = tmp_path / "CLAUDE.md"
    t.write_text("# App\n")
    bad = tmp_path / "bad.md"
    bad.write_text("no markers here\n")
    r = run(t, bad)
    assert r.returncode != 0
