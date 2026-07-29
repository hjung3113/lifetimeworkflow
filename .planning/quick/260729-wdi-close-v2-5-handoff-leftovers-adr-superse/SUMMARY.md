---
quick_id: 260729-wdi
slug: close-v2-5-handoff-leftovers-adr-superse
date: 2026-07-29
status: complete
commits:
  - 19ff9e7  # docs: correct the advertised suite size from 982 to 881
key-findings:
  - "docs/adr/** is on CONSTITUTION_GLOBS — the ADR work is human-gated, same as docs/glossary.md. The handoff's framing of it as agent-authorable was wrong."
  - "D-14's two citation targets are both LIVE; only ADR-0008's Links section points at deleted code."
---

# Quick 260729-wdi — Close the v2.5 handoff leftovers

Closed the machine-actionable half of the four items PR #5 left open, and staged the human-gated
half as a copy-ready draft.

## What shipped — `19ff9e7`

The advertised suite size, corrected at all three sites: `README.md:12` (badge), `README.md:107`,
`README.ko.md:60`. All three sit in a `uv run pytest -q` context, and that suite now collects
**881**, measured with `uv run pytest -q --collect-only` rather than carried over from the handoff.
The instance leg's 14 tests are a separate `examples/log-parser/tests` invocation and are not what
these lines advertise.

Verified with a **negative** grep — `git grep -n '982' -- README.md README.ko.md` returns nothing
(exit 1). A positive count grep would have passed while a fourth site went unfixed; that failure
shape is the milestone's own recurring defect.

## The correction that changed this task's shape

The handoff, and my own first framing of it, treated the ADR work as agent-authorable and only the
glossary edit as human-gated. Measured: `tools/hooks/contract_guard.py:55` reads

```python
CONSTITUTION_GLOBS = ["contracts/**", "docs/adr/**", "docs/glossary.md"]
```

`docs/adr/**` is the **same** gate. Writing ADR-0013, updating ADR-0008's status header, or touching
`docs/adr/README.md` all require a human `GOLDEN_APPROVE_HUMAN`. So three of the four leftovers are
human-gated, not one.

Neither token was set and no bypass was attempted. `HARNESS_DEV_BYPASS` was refused on the same
ground Phase 45 refused it: bypassing a gate to tidy the plane that gate protects makes the gate
decorative.

## What was staged instead — `HUMAN-APPLY.md`

The full ADR-0013 body plus the exact edits for ADR-0008's two header lines, the ADR index row, and
the two `docs/glossary.md` replacements — all copy-ready, with the apply procedure. Drafting off the
plane is not a bypass: the gate still stands between the draft and `docs/adr/`.

## D-14, resolved as a finding

The handoff described "two accepted ADRs citing files this milestone made stale". Measured, both
citation targets are **live**:

- `docs/explanation/next-milestone-task-control-plane.md` — kept by Phase 45 under a HISTORICAL
  header naming ADR-0008 as the reason it survives.
- `harness/agents/templates/component-engineer.md` — kept and corrected in place; two live gates
  depend on it independently of ADR-0003.

So **ADR-0003 needs no correction** — its `:95` citation resolves and is accurate. The real dangling
references are in **ADR-0008's own Links section**, which names six paths that no longer exist
(`.workflow/`, `tools/task_packet/`, `tools/risk_router/`, `tools/task_control/`, `tools/evidence/`,
`tools/handoff/`) and is immutable. ADR-0013 clause (a) records that as historical text, and clause
(b) ratifies the keep-cited-targets rule Phase 45 followed without one.

## How the human-gated half landed

`apply.sh` was written for the owner to run, and the owner ran it. That is not a bypass: the
contract-guard hook gates the **agent's** Write/Edit tool, and the script sets neither
`GOLDEN_APPROVE_HUMAN` nor `HARNESS_DEV_BYPASS`. CODEOWNERS at the merge remains the ratification.

Each of the six replacements asserts its target occurs **exactly once** before anything is written;
the guard was mutation-tested both directions (a zero-match probe and a 40-match probe each abort),
and a failed preflight rolls the new ADR back via an `ERR` trap. Result: ADR-0008's body untouched
(two header lines only), glossary `:21` intact, 8 changed lines plus the new record.

Shipped in `145fb8b`; PR #6 green on all 11 CI jobs plus `gate`.

## All four items closed

| Item | Outcome |
|------|---------|
| README test counts | `19ff9e7` — 982 → 881 |
| ADR-0013 + ADR-0008 header + index row | `145fb8b` |
| `docs/glossary.md:20`, `:23` | `145fb8b` |
| D-24 CODEOWNERS residual | **accepted as a documented residual** (owner, 2026-07-29) — recorded in STATE.md Deferred Items |

D-24's rationale: `require_code_owner_reviews=true` cannot be satisfied in a solo repo (GitHub
forbids self-approval) without a second account, already declined at v2.3 RAT-5. Accepting matches
ADR-0012 (CI and the merge are the authority) and ADR-0013 clause (c) (no new enforcement).
Re-openable in v2.6 as a machine-side golden-diff check, now that the no-growth constraint has
closed.

`/gsd:complete-milestone` runs after PR #6 merges.
