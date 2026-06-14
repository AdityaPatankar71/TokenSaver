#!/usr/bin/env python3
"""Merge Claude Code hook entries into .claude/settings.json without clobbering.

Usage: merge_settings.py <settings.json> <fragment.json>

Adds the hook entries from <fragment.json> into <settings.json>. An entry is
skipped if any of its commands is already registered for that event, so the
script is idempotent (safe to re-run). All existing keys and hooks are
preserved.
"""
import json
import sys
import pathlib


def load(path):
    p = pathlib.Path(path)
    if p.exists() and p.read_text().strip():
        return json.loads(p.read_text())
    return {}


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: merge_settings.py <settings.json> <fragment.json>")

    target_path = pathlib.Path(sys.argv[1])
    data = load(target_path)
    fragment = json.loads(pathlib.Path(sys.argv[2]).read_text())

    hooks = data.setdefault("hooks", {})
    for event, entries in fragment.get("hooks", {}).items():
        bucket = hooks.setdefault(event, [])
        existing_cmds = {
            h.get("command")
            for entry in bucket
            for h in entry.get("hooks", [])
        }
        for entry in entries:
            cmds = [h.get("command") for h in entry.get("hooks", [])]
            if any(c in existing_cmds for c in cmds):
                continue  # already installed
            bucket.append(entry)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"merged hooks into {target_path}")


if __name__ == "__main__":
    main()
