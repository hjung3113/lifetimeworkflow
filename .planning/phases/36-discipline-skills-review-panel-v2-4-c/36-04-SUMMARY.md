---
phase: 36-discipline-skills-review-panel-v2-4-c
plan: 04
subsystem: human docs + closeout
tags: [LANE-01, LANE-02, ADR-0010, human-gated, gate-fan-in]
requires:
  - tools/docs_guard (Phase 28/29)
  - the 36-01..03 implementation
provides:
  - the lifecycle how-to updated for the discipline refusal
  - two drafted review-ledger rows for a human to land
affects: []
tech-stack:
  added: []
  patterns: [bounded target edit, drafted-not-landed ledger row, honest reviewed-no-change]
key-files:
  created:
    - .planning/phases/36-discipline-skills-review-panel-v2-4-c/drafts/ledger-rows.md
  modified:
    - docs/how-to/task-lifecycle.md
decisions:
  - "docs/explanation/task-lifecycle-shadow-metrics.md was NOT edited. Reviewed against the router and runner changes; none of the five definitions is falsified, so reviewed-no-change is the honest disposition and manufacturing a diff would be the dishonest one."
  - "docs/.docs-review-ledger.toml was not written, and no GOLDEN_APPROVE_HUMAN or HARNESS_DEV_BYPASS token was set at any point in the phase."
  - ".planning/STATE.md was not edited; the proposed delta is reported below as text."
metrics:
  tasks: 3
  commits: 1
  tests_added: 0
---

# Phase 36 Plan 04: Docs + Closeout Summary

The new refusal is documented where a reader meets it, both human-gated items are drafted rather
than landed, and the gate fan-in was run for real.

## The bounded doc edit

`docs/how-to/task-lifecycle.md` gains one subsection under step 2 —
*"The lane's disciplines are refused, not suggested"* — covering: what each lane owes, the
`uv run python -m tools.discipline` invocation with its 0/1/3 routing, the verbatim
`FAIL: missing required disciplines: clarify` refusal, the `discipline: <id>` phase-gate refresh
reason, and what a record must contain (declared skill, phase, existing outputs, distinct panel
seats, findings that exist in `evidence.json`). It states plainly that no tool writes the record.

Nothing else in the document was touched, and no other document was edited.

## Human-gated: two ledger rows DRAFTED, not landed

`.planning/phases/36-discipline-skills-review-panel-v2-4-c/drafts/ledger-rows.md` carries both rows
with exact bytes, built from the shipped `tools/docs_guard/ledger.py::_ROW_KEYS`
(`{id, source_digest, target_digest, disposition}`), plus the command that recomputes the digests at
landing time and the reason each disposition is the one it is.

| Binding | Disposition | Why |
|---------|-------------|-----|
| `task-control-cli-howto` (required) | `updated` | the target genuinely changed; `updated` requires a target-digest delta versus the previous committed row, which this has (`fc10ff30f431…` → `da7694462b91…`) |
| `lifecycle-eval-shadow-metrics` (advisory) | `reviewed-no-change` | reviewed and unfalsified; `ceremony_count` counts user-visible events from the evaluator's event list, which is unchanged — discipline materialization emits no event |

`git diff --quiet -- docs/.docs-review-ledger.toml` → **ledger UNMODIFIED**. ADR-0010 §3b reserves a
ledger disposition to a human, and `first_seen-unratified` exists to catch a binding blessed in the
change that created it — the draft says so explicitly.

## Gate fan-in — actual output

| Gate | Command | Result |
|------|---------|--------|
| tests | `uv run pytest -q` | **1619 passed, 8 snapshots** (baseline 1543 → **+76**) |
| lint ratchet | `uv run python -m tools.ruff_baseline` | **exit 0** — 266 findings vs baseline 393 |
| contract drift | `uv run python -m tools.contract_drift.drift` | `OK — live manifest matches the committed baseline` (exit 0) |
| emit round-trip | `uv run python -m tools.harness_emit && git status --porcelain` | **empty** (untracked-visible) |
| structural gates | `uv run pytest tools/harness_lint -q` | 366 passed |
| docs obligations | `uv run python -m tools.docs_guard` | **exit 1**, see below |

### The docs-guard red, named

```
fail: stale-digest: binding task-control-cli-howto was reviewed at digests that no longer
      match the working tree
docs-guard: 8 binding(s); 7 uncovered human-authored document(s) (uncovered_max = 7)
```

This is the **known-red carried into the phase** (phase 34 moved a bound source digest and the
ledger row was never landed) — the lead's brief named it as not-mine. Phase 36 did not repair it and
did not write a ledger row. It *did* move the same binding further, by changing what the how-to
documents; the target was therefore updated and the row drafted, so the human's eventual review is
against a document that matches the code. The binding goes green when a human lands row 1.

The advisory `lifecycle-eval-shadow-metrics` binding is `STALE_ADVISORY` — a warning that never
flips the exit code — and row 2 discharges it.

## Proposed `.planning/STATE.md` delta (NOT applied)

`.planning/STATE.md` was not edited, per the brief. Proposed:

- `Phase 36: Discipline Skills + Adversarial Review Panel (v2.4 C)` → **Complete**, 4/4 plans,
  completed 2026-07-22.
- Requirements traceability: **LANE-01** and **LANE-02** → Complete.
- Carry forward, unchanged: `[STALE_REQUIRED] task-control-cli-howto` remains the repo's docs-guard
  red until a human lands the drafted rows; it now covers phase 36's edit as well as phase 34's.
- New carried item: the ruff ratchet has an **unclaimed free shrink** (393 → 266). The brief forbade
  `--update`, so the baseline still reads 393. A later phase can bank it in one command.

## Deviations from Plan

None. Task 1's second half resolved to "review, do not edit", which the plan named as the preferred
honest outcome rather than a deviation.

## Human-gated / carried

1. **Land the two ledger rows** — `.planning/.../drafts/ledger-rows.md`, digests recomputed at
   landing time. Human-only by ADR-0010 §3b.
2. **Unclaimed ruff ratchet** (393 → 266) — one command, deliberately not run here.
