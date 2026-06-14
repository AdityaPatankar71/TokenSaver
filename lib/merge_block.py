#!/usr/bin/env python3
"""Idempotent managed-block merge into a markdown file.

Usage: merge_block.py <target_md> <source_block_md>

The source file must contain a matching pair of
<!-- BEGIN: NAME --> / <!-- END: NAME --> markers.

If the target already contains a block with the same NAME, it is replaced
in place. Otherwise the block is appended. Content outside the markers is
never touched. This is what lets TokenSaver, graphify, and caveman each own
a block in the same CLAUDE.md without clobbering one another or the user's
own notes.
"""
import re
import sys
import pathlib


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: merge_block.py <target_md> <source_block_md>")

    target = pathlib.Path(sys.argv[1])
    source = pathlib.Path(sys.argv[2]).read_text()

    m = re.search(r"<!-- BEGIN: (.+?) -->", source)
    if not m:
        sys.exit("source block has no '<!-- BEGIN: NAME -->' marker")
    name = m.group(1)

    begin = re.escape(f"<!-- BEGIN: {name} -->")
    end = re.escape(f"<!-- END: {name} -->")
    block = source.strip()

    existing = target.read_text() if target.exists() else ""
    pattern = re.compile(begin + r".*?" + end, re.DOTALL)

    if pattern.search(existing):
        new = pattern.sub(lambda _: block, existing)
        action = "updated"
    else:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        if existing and not existing.endswith("\n\n"):
            existing += "\n"
        new = existing + block + "\n"
        action = "added"

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(new)
    print(f"{action} block '{name}' in {target}")


if __name__ == "__main__":
    main()
