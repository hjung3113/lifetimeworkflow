---
quick_id: 260729-wdi
slug: close-v2-5-handoff-leftovers-adr-superse
date: 2026-07-29
status: in-progress
---

# Quick 260729-wdi — Close the v2.5 handoff leftovers

Milestone v2.5 merged at `858460f` (PR #5) with four human-gated items unresolved. This task closes
the machine-actionable half and stages the human-gated half so a token-holding session is a copy,
not an authoring job.

## Plane split (measured, not assumed)

`tools/hooks/contract_guard.py:55` — `CONSTITUTION_GLOBS = ["contracts/**", "docs/adr/**",
"docs/glossary.md"]`. `docs/adr/**` is the SAME gate as `docs/glossary.md`: a PreToolUse deny unless
a human sets `GOLDEN_APPROVE_HUMAN`. So the ADR work is human-gated too — correcting the assumption
that it was agent-authorable.

| Item | Path | Plane | Actor |
|------|------|-------|-------|
| README test counts | `README.md:12,107`, `README.ko.md:60` | ordinary | agent (this task) |
| ADR superseding 0008 | `docs/adr/0013-*.md` (new) | constitution | human token |
| ADR-0008 status header | `docs/adr/0008-task-control-plane-lifecycle.md:5,9` | constitution | human token |
| ADR index row | `docs/adr/README.md` | constitution | human token |
| Glossary `:20`, `:23` | `docs/glossary.md` | constitution | human token |
| D-24 CODEOWNERS | repo settings | — | human decision |

Drafting the ADR body into `.planning/quick/` is NOT a bypass: the draft lands off the plane, and
the gate still stands between the draft and `docs/adr/`.

## Task 1 — README test counts 982 → 881

**Measured, not copied:** `uv run pytest -q --collect-only` → `881 tests collected`. All three sites
sit in a `uv run pytest -q` context, so 881 is the right number for each (the instance leg's 14 is a
separate `examples/log-parser/tests` invocation and is not what these lines advertise).

- `README.md:12` — badge `tests-982%20passing` → `tests-881%20passing`
- `README.md:107` — `# 2. Run the full harness test suite  (982 passing)` → `(881 passing)`
- `README.ko.md:60` — `# 2. 전체 하네스 테스트 스위트 (982 통과)` → `(881 통과)`

Verify: `git grep -n '982' -- README.md README.ko.md` returns nothing.

**Assertion discipline (the milestone's own lesson):** this task adds no assertion, so there is
nothing to mutation-test. The verify above is a *negative* grep, which fails loudly if a site is
missed — the failure mode that a positive count grep would hide.

## Task 2 — Stage the human-gated constitution writes

Write `HUMAN-APPLY.md` in this task directory containing:

1. The full ADR-0013 body, ready to save verbatim as
   `docs/adr/0013-task-control-plane-retirement.md`.
2. The exact two-line header edit for ADR-0008 (`Status:`, `Superseded by:`), matching the
   precedent set by ADR-0001 and ADR-0010 when 0012 superseded them.
3. The `docs/adr/README.md` index row change (Status column `accepted` → `superseded by 0013`).
4. The two `docs/glossary.md` replacements quoted verbatim from `45-05-SUMMARY.md` (`:20`, `:23`),
   with the explicit do-not-touch list (`:13`, `:19`, `:21`).
5. The one-command apply procedure under `GOLDEN_APPROVE_HUMAN`.

## Out of scope

- Setting `GOLDEN_APPROVE_HUMAN` or using `HARNESS_DEV_BYPASS` — forbidden; a path around a gate is
  a reportable defect, never a shortcut.
- D-24 — a repo-settings decision, not a code change.
- `/gsd:complete-milestone` — runs after these land.
