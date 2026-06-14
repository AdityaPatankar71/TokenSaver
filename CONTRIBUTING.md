# Contributing to TokenSaver

Thanks for helping. Please read this first — TokenSaver has a narrow scope and one hard invariant, and PRs that respect both get merged fast.

## Scope: this is an orchestrator, not an engine

TokenSaver wires three things into a project. Know which one a change belongs to:

| Concern | Lives in |
|---------|----------|
| Code graph: parsing, queries, incremental updates | **Upstream [Graphify](https://github.com/safishamsi/graphify)** — file issues there |
| Output compression / caveman behavior | **Upstream [caveman](https://github.com/JuliusBrussee/caveman)** — file issues there |
| The honesty layer, the installer, hook wiring, the merge logic | **Here** |

If your idea is "make the graph smarter" or "compress output differently," it's upstream, not here. What belongs here: the honesty rules, the one-command install/uninstall, how the three pieces compose without clobbering each other.

## The one invariant: never clobber user config

The installer edits files users already own (`CLAUDE.md`, `.claude/settings.json`). The merge logic in `lib/` exists so we **only ever touch our own managed block** and leave everything else byte-for-byte intact.

Any change to `lib/merge_block.py` or `lib/merge_settings.py` **must**:
- keep the existing tests green, and
- add a test for the new behavior, and
- preserve idempotency (running install twice changes nothing the second time).

A PR that can clobber user content will not be merged, no matter how useful the feature.

## Dev setup

```bash
git clone https://github.com/AdityaPatankar71/TokenSaver
cd TokenSaver
pip install pytest
pytest -q
```

## Before you open a PR

1. **Tests pass:** `pytest -q`
2. **Shell is clean:** `bash -n install.sh uninstall.sh hooks/*.sh` and, if you have it, `shellcheck -S warning install.sh uninstall.sh hooks/*.sh`
3. **CI is green** (it runs both of the above on Python 3.10 + 3.12).
4. **Installer stays idempotent and non-clobbering** — test it against a sample repo that already has a `CLAUDE.md` and a `.claude/settings.json` with the user's own hooks.

## Style

- Match the surrounding code. Bash stays POSIX-friendly and quoted; Python stays stdlib-only (no new dependencies in `lib/` — it must run anywhere Python 3.10+ does).
- Hooks must always `exit 0` so a graph hiccup never blocks Claude.
- Keep managed blocks wrapped in `<!-- BEGIN: ... -->` / `<!-- END: ... -->` markers with matching names.

## Honesty in docs

This project measures and reports real numbers. Do not add inflated savings claims to the README. If you change the benchmark, show your method and the actual figures — including where TokenSaver *loses* (small repos). Marketing multipliers ("99% fewer tokens!") will be removed.

## License

By contributing you agree your work is licensed under the repository's [MIT License](LICENSE).
