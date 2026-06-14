## What & why

<!-- What does this change, and what problem does it solve? -->

## Scope check

- [ ] This belongs in TokenSaver (the orchestrator/honesty/install layer), not upstream in Graphify or caveman.

## The invariant

- [ ] The installer stays **idempotent** (running it twice changes nothing the second time).
- [ ] It does **not clobber** user content outside our managed block — tested against a repo that already has its own `CLAUDE.md` and `.claude/settings.json` hooks.

## Checks

- [ ] `pytest -q` passes.
- [ ] Added/updated tests for any change to `lib/` merge logic.
- [ ] `bash -n` (and `shellcheck` if available) clean on changed shell scripts.
- [ ] CI is green.
- [ ] No inflated savings claims added to docs; any benchmark change shows method + real numbers.
