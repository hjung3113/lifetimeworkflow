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

## Still open

| Item | Actor | Where |
|------|-------|-------|
| ADR-0013 + ADR-0008 header + index row | human token | `HUMAN-APPLY.md` §A-C |
| `docs/glossary.md:20`, `:23` | human token | `HUMAN-APPLY.md` §D |
| D-24 CODEOWNERS residual | human decision | `HUMAN-APPLY.md` tail |

`/gsd:complete-milestone` runs after these land.
