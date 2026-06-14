# TokenSaver

One command to make Claude Code cheaper and more honest in any project.

It wires together three pieces:

| Piece | What it does | Whose code |
|-------|--------------|------------|
| **[Graphify](https://pypi.org/project/graphifyy/)** | Builds a queryable code graph so Claude fetches symbol→`file:line` pointers instead of re-reading whole files every session | not ours — we orchestrate it |
| **Honesty layer** | A CLAUDE.md block that stops Claude agreeing with you by default — it pushes back, cites or flags guesses, and won't fold under pressure | **ours** |
| **[caveman](https://github.com/JuliusBrussee/caveman)** *(optional)* | Compresses Claude's output to cut tokens | not ours — optional |

## Honest scope

This is an **orchestrator, not an engine.** The code graph is Graphify's; the output compression is caveman's. TokenSaver's own contribution is the **honesty layer** and a careful installer that composes all three into one project **without clobbering** your existing `CLAUDE.md` or `.claude/settings.json` (each tool owns a marked block).

## What problem it solves

Every new Claude session starts cold and re-explores your codebase, burning tokens re-reading files it read yesterday. The graph gives Claude a persistent map so it jumps straight to the relevant code.

### Measured savings — and where it does NOT help

Per-task retrieval cost, measured on synthetic repos (baseline = reading every source file; graph = `GRAPH_REPORT.md` + one scoped `graphify query`):

| repo size | read-all-files | graph | result |
|-----------|----------------|-------|--------|
| 8 files   | ~646 tok       | ~1035 | **−60% (costs more)** |
| 25 files  | ~2062 tok      | ~1489 | +28% |
| 60 files  | ~4985 tok      | ~1869 | +62% |
| 120 files | ~10053 tok     | ~2374 | +76% |
| 250 files | ~21265 tok     | ~4192 | +80% |

**Crossover is around 20–25 files. Below that, TokenSaver adds overhead — don't use it on small repos.** It pays off on medium/large codebases.

Two honest caveats:
- The baseline above is "read *every* file," the worst case. Real Claude greps and reads a few files, so **your real-world savings are lower** than this table and depend on how exploration-heavy your work is.
- There is a fixed per-session cost: the honesty + graphify CLAUDE.md blocks add ~1–1.3k input tokens every session. On small repos this tax is never recovered (hence the negative result above).

We report measured numbers, not marketing multipliers. No 90%+ claims.

## Install

```bash
git clone https://github.com/AdityaPatankar71/TokenSaver /tmp/TokenSaver
cd /path/to/your/project
/tmp/TokenSaver/install.sh                 # graph + honesty
/tmp/TokenSaver/install.sh --with-caveman  # also add output compression
```

Requires: `python3 >=3.10`, and `uv` or `pipx` recommended (the installer falls back to pip with a warning).

## What the installer touches

- `CLAUDE.md` — adds a `TokenSaver honesty layer` managed block (appends; never overwrites your content)
- `.claude/settings.json` — adds SessionStart (`startup`, `resume`) + PostToolUse refresh hooks (merges; skips if already present)
- Graphify's own files (`graphify-out/`, its Claude skill) via `graphify install --project`
- A git post-commit hook for auto-rebuild (only if the project is a git repo)

## How refresh stays automatic

- **SessionStart hook** (`startup`, `resume`) → `graphify update .` catches edits made outside Claude (git pull, other editor).
- **PostToolUse hook** (`Edit|Write|MultiEdit`) → `graphify update .` catches edits Claude makes mid-session.
- Both are cheap: Graphify's stat-index reparses only changed files (no full rebuild, no LLM).

## Uninstall

```bash
/tmp/TokenSaver/uninstall.sh
```

Removes the honesty block and unwinds Graphify. Refresh hooks in `settings.json` are left for you to remove by hand (so we never touch hooks you may have edited).

## License

MIT — see [LICENSE](LICENSE).
