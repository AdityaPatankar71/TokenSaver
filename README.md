# TokenSaver

[![CI](https://github.com/AdityaPatankar71/TokenSaver/actions/workflows/ci.yml/badge.svg)](https://github.com/AdityaPatankar71/TokenSaver/actions/workflows/ci.yml)

One command to make Claude Code cheaper and more honest in any project.

![TokenSaver demo — install wiring graphify + an honesty layer into a project, then a scoped graph query](docs/demo.gif)

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

### Measured savings — on real codebases, with honest caveats

Methodology: clone real OSS Python repos, build the graph, and compare the token
cost of locating a feature. Token counts are `chars / 4`.

| repo | source files | read all source | read 3 relevant files | one scoped graph query |
|------|--------------|-----------------|-----------------------|------------------------|
| [click](https://github.com/pallets/click)        |  16 | ~98k tok  | ~45k tok | **~80 tok**  |
| [requests](https://github.com/psf/requests)      |  20 | ~54k tok  | ~26k tok | **~500 tok** |
| [flask](https://github.com/pallets/flask)        |  23 | ~84k tok  | ~25k tok | **~490 tok** |
| [rich](https://github.com/Textualize/rich)       | 109 | ~310k tok | ~42k tok | **~490 tok** |

**What's solid:** a scoped `graphify query` returns a bounded subgraph of roughly
**80–500 tokens regardless of repo size.** That replaces the grep-many-files
exploration Claude does on every cold session to *find* the relevant code — which
on these repos costs 25k–45k tokens. So the **exploration step gets ~95%+ cheaper.**

**What we will NOT claim:** that this is "95% off your whole session." The query is
a *navigation layer* — it tells Claude where code lives and how it connects, not the
full implementation. Claude still reads the specific function it edits. Real
total-session savings are smaller than the exploration number and depend on your
workflow (exploration-heavy work benefits most).

**Where it loses:** small repos (≲25 files). Exploration was already cheap, and the
honesty + graphify `CLAUDE.md` blocks add a fixed ~1–1.3k tokens per session that
never gets recovered. On a synthetic 8-file repo we measured a **net −60%** (it
costs more). Don't install TokenSaver on small repos.

**Bottom line:** big win on the re-exploration problem on medium/large codebases;
neutral-to-negative on small ones; not a magic whole-session multiplier. We report
measured numbers, not marketing multipliers.

## Install

From inside your project folder, one command:

```bash
curl -fsSL https://raw.githubusercontent.com/AdityaPatankar71/TokenSaver/main/install.sh | bash
```

Add output compression too:

```bash
curl -fsSL https://raw.githubusercontent.com/AdityaPatankar71/TokenSaver/main/install.sh | bash -s -- --with-caveman
```

The script clones itself to a temp dir and installs into your **current** directory — no manual clone needed.

> Piping a remote script to your shell runs code you haven't read. If you'd rather inspect it first, install manually:
>
> ```bash
> git clone https://github.com/AdityaPatankar71/TokenSaver /tmp/TokenSaver
> cd /path/to/your/project
> /tmp/TokenSaver/install.sh                 # graph + honesty
> /tmp/TokenSaver/install.sh --with-caveman  # also add output compression
> ```

Requires: `python3 >=3.10`, `git`, and `uv` or `pipx` recommended (the installer falls back to pip with a warning).

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

## Development

The merge logic (the part that must never clobber your config) is covered by tests:

```bash
pip install pytest
pytest -q
```

CI runs the tests on Python 3.10 + 3.12 and lints the shell scripts (`bash -n` + ShellCheck) on every push and PR.

## License

MIT — see [LICENSE](LICENSE).
