---
phase: 5.7
slug: lifecycle-completeness
status: ready
created: 2026-07-09
---

# Phase 5.7 — Validation Strategy

> Pure authored-surface addition (skills/commands/1 persona-template + 1 persona augmentation) +
> in-wave guard-set updates. ZERO new external packages. No constitution plane touched → **no
> `GOLDEN_APPROVE_HUMAN` token anywhere**. Phase-wide invariant: the non-example `uv run pytest`
> stays GREEN and the GEN-04/GEN-05 core-prose guard reads 0 domain tokens on new assets.

## Test Infrastructure
| Property | Value |
|---|---|
| Framework | pytest `>=8.4,<9` via `uv run pytest` |
| Guard suite | `uv run pytest tools/harness_lint -x -q` |
| Full suite | `uv run pytest` (keep Phases 1–5.5 green) |
| Prose guard | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -x -q` |

## Sampling Rate
- **After every asset added:** `uv run pytest tools/harness_lint -x -q`.
- **After each wave:** full `uv run pytest` (non-example).
- **Phase gate:** full suite green + `git grep -nE '설비|wafer|equipment|standard-log|correction-rules|dotnet-engineer|dotnet-conventions|normalization-catalog|pipeline-patterns|libs/dotnet' -- harness/ | (expect only pre-existing/none)` + manual demo of the 7 success criteria (057-CONTEXT `<specifics>`).

## Success criteria (structural, no runtime) — 057-CONTEXT `<specifics>`
1. `/contract-check` exists; `new-contract-rule` + CLAUDE.md dead link resolved; runs schema validation.
2. `golden-debug` skill carries the 7-axis decision tree + red-golden procedure.
3. `polyglot-boundary` skill is the single §4.3–4.6 source of truth.
4. Engineer template → a new-language persona is derivable (not hand-authored from scratch).
5. `/new-normalization-rule` de-domained (`/new-contract-rule`); prose guard clean.
6. Each MISSING lifecycle stage (onboard/plan/review/integrate) has an executable asset.
7. Non-example suite green with `EXPECTED_SKILLS` updated (4 → 8).

## Per-wave gate
- **Wave 1 gate:** `EXPECTED_SKILLS` includes `golden-debug`, `polyglot-boundary`; new commands resolve to real personas; suite green.
- **Wave 2 gate:** `EXPECTED_SKILLS` includes `gate-model`, `two-plane-memory`; `/orient`,`/review`,`/verify-work` resolve; orchestrator still valid persona; suite green.
