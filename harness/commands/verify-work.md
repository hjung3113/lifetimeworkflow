---
description: >-
  Use before handing off or committing a unit of work — runs the in-session composite gate: lint,
  full tests, contract validation + drift, and derived freshness. Invoke as the pre-handoff
  self-verify, distinct from Phase-6 CI (non-session) and /checkpoint (state persistence).
agent: orchestrator
subtask: true
---

# /verify-work — in-session pre-handoff composite gate

The one command that proves a unit of work is safe to hand off *within the session*, before the
non-bypassable Phase-6 CI mirror runs. It composes the existing gate macros — it adds no new checks.
Distinct from:

- **Phase-6 CI** — the non-session, non-bypassable mirror on the PR (config-derived matrix). This
  command is its in-session preview; it does not replace it.
- **`/checkpoint`** — persists `.memory/state/` so work survives the container. Orthogonal: verify
  proves correctness, checkpoint saves context.

Run the four gates in order; stop at the first hard failure and fix before proceeding.

## 1. Lint + format + polyglot boundary (`/lint`)

!`ruff check . && ruff format --check . && { fail=0; files=$(git ls-files '*.tsv'); if [ -n "$files" ]; then for f in $files; do uv run python -m tools.polyglot_lint.lint "$f" || fail=1; done; fi; [ "$fail" -eq 0 ] || { echo 'FAIL: polyglot §4.3-4.6'; exit 1; }; echo 'lint OK'; }`

## 2. Full test suite (`/test`)

!`uv run pytest`

## 3. Contract validation + drift gate (`/contract-check`)

!`uv run python -m tools.contract_drift.drift`

## 4. Derived freshness (mirror of the CI stale-derived gate) — presence-safe

Regenerates the committed-derived set (`docs/reference/**` + `contracts-index.md`) and fails if the
tree is stale — the in-session preview of the CI `stale-derived` gate. Invokes ONLY the existing
generators (D-06); it never re-implements derivation. **Presence-safe:** a bare tree with no
contracts regenerates to the same bytes, so `git add -A` + `git diff --cached --exit-code` sees no
change and exits 0. Uses `git add -A` (not bare `git diff`) so a NEW untracked page is caught too.

!`uv run python -m tools.docs_sync && uv run python -m tools.memory_regen.contracts_index && git add -A -- docs/reference .memory/derived/contracts-index.md && git diff --cached --exit-code -- docs/reference .memory/derived/contracts-index.md || { echo 'FAIL: derived plane stale or a generator errored — commit the regenerated docs/reference + contracts-index (or run /refresh-memory)'; exit 1; }`

## Notes

- All four must be green before handoff. The .NET side of lint/test is presence-gated (announced
  skip when the SDK is absent — BOOT-01 egress deferral), so this stays runnable in-container.
- Green here is a *preview*, not a substitute for CI + human ratification of any constitution-plane
  change.
