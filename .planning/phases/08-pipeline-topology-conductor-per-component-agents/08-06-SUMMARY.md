---
phase: 08-pipeline-topology-conductor-per-component-agents
plan: 06
subsystem: phase-closeout-guards-and-constitution
tags: [pipeline-topology, persona-anti-sprawl, conductor, GEN-04, ADR, constitution-plane, PIPE-06]
requires:
  - tools/harness_lint/tests/test_agents.py (EXPECTED_PERSONAS 4-member gate + is_read_only idiom)
  - harness/agents/orchestrator.md (evolved conductor — mode:primary, topology routing signal)
  - docs/adr/0002-general-template-de-specialization.md (MADR shape + constitution-plane banner to mirror)
  - human GOLDEN_APPROVE_HUMAN ratification (orchestrator checkpoint approval)
provides:
  - "test_single_primary_carries_conductor_signal — persona anti-sprawl extended to the conductor role (one mode:primary carrying a stage/component/topology signal; EXPECTED_PERSONAS stays 4)"
  - "ADR-0003 — constitution-plane record of the pipeline-topology pure-DATA slot + instance-overlay decision (generic-default-in-core, concrete-topology-in-example), GEN-04 as primary driver"
  - "Green full-guard closeout across BOTH legs (core suite + instance leg)"
affects:
  - "Phase 8 CLOSED (6/6) — PIPE-01..06 satisfied"
  - "Future instances: ADR-0003 is the auditable why for putting a concrete topology under examples/ rather than core"
tech-stack:
  added: []
  patterns:
    - "Anti-sprawl gate extended by asserting the single mode:primary persona carries the conductor routing signal — no new frozenset, no second primary"
    - "Constitution-plane ADR mirrors ADR-0002 MADR sections verbatim; lands via human GOLDEN_APPROVE_HUMAN (agent drafts, human ratifies)"
    - "Phase gate = BOTH legs (uv run pytest core + uv run pytest examples/log-parser/tests) since the instance leg is off root testpaths"
key-files:
  created:
    - docs/adr/0003-pipeline-topology-slot-and-instance-overlay.md
  modified:
    - tools/harness_lint/tests/test_agents.py
    - docs/adr/README.md
decisions:
  - "The conductor-signal assertion targets whichever persona is mode:primary (not a hardcoded name) and checks description+body for topology/stage/component/pipeline — proving the routing role landed on the one primary without growing EXPECTED_PERSONAS"
  - "ADR-0003 names GEN-04 as the PRIMARY decision driver: domain edge-contract tokens (standard-log, equipment-progress) are guard-flagged under core roots, so the concrete topology MUST live under examples/ (never scanned) — the only layout that holds the core→example boundary green"
  - "ADR text lives under docs/ (not a GEN-04-scanned core root) so it may name the domain components; no domain tokens were introduced into any harness/ or tools/ file"
metrics:
  duration: 12min
  tasks: 2
  files: 3
  completed: 2026-07-11
---

# Phase 08 Plan 06: Phase Closeout — Full-Guard Suite + ADR-0003 Summary

PIPE-06 closeout: proved the guards were *extended*, not just the features added. Added one assertion
that the persona anti-sprawl gate now also pins the **conductor role** onto the single primary
orchestrator (no second primary, `EXPECTED_PERSONAS` stays 4), ran the whole guard surface as one
suite across BOTH the core suite and the instance leg (both green), and recorded the one architectural
decision this phase locked — the pipeline-topology pure-DATA slot + instance-overlay — as **ADR-0003**
on the constitution plane, landed via the human `GOLDEN_APPROVE_HUMAN` ratification gate.

## What Was Built

**Task 1 — full-guard closeout suite, both legs green (`0532d5a`)**
- `tools/harness_lint/tests/test_agents.py`: added `test_single_primary_carries_conductor_signal` — a
  single non-parametrized assertion that exactly one `mode: primary` persona exists and that its
  authored description + body carries at least one conductor routing signal
  (`_CONDUCTOR_SIGNAL_TOKENS = ("topology", "stage", "component", "pipeline")`). This extends the
  persona anti-sprawl gate to the conductor role. `EXPECTED_PERSONAS` is untouched — it stays the
  4-member frozenset `{orchestrator, python-engineer, code-reviewer, explorer}` (a second
  `mode: primary` would still fail `test_expected_personas_present_no_sprawl`).
- Ran the whole guard surface as the phase gate — topology consistency
  (`test_pipeline_config.py`), template anti-sprawl (`test_agent_templates.py`), persona gate
  (`test_agents.py`), skills(9) gate (`test_skills.py`), GEN-04 (`test_core_no_example_dep.py`) —
  plus the full core suite and the instance leg. No contract/schema file changed this phase (only a
  test), so no derived-memory regeneration was required.

**Task 2 — ADR-0003 recorded on the constitution plane (`ec5a01f`)**
- `docs/adr/0003-pipeline-topology-slot-and-instance-overlay.md` (new): mirrors ADR-0002's MADR 4.x
  structure and constitution-plane banner (`plane: constitution`, Status: accepted, Date: 2026-07-10,
  Deciders: Phase 8 planning, Complements: ADR-0002). Records the decision: the pipeline topology is a
  pure-DATA slot (`[[components]]` + `[pipeline]`) whose GENERIC default (source/sink/sample-record)
  lives in core `harness/project.toml`, while the CONCRETE per-instance topology (the log-parser
  parser→converter→scheduler→collector chain with domain edge contracts `standard-log`,
  `equipment-progress`) lives in the `examples/log-parser/project.toml` overlay. GEN-04 is stated as
  the **primary decision driver** (domain contract tokens are guard-flagged under core roots, so
  keeping the concrete topology under `examples/` — never scanned — is the only GEN-04-green layout).
  Consequences: the conductor is the evolved single-primary orchestrator (no new tier); the instance
  topology gate runs only in the example leg.
- `docs/adr/README.md`: appended the ADR-0003 row to the Index table (append-only, no rows removed).
- Landed via `GOLDEN_APPROVE_HUMAN` exported inline on the commit — the human ratification granted via
  the orchestrator checkpoint. Agent drafted; human ratified. Not self-approved.

## Verification

- `uv run pytest tools/harness_lint/tests/test_agents.py -x` → **20 passed** (was 19; the new
  non-parametrized conductor-signal assertion is collected; `EXPECTED_PERSONAS` still 4).
- `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py test_pipeline_config.py test_agent_templates.py test_skills.py -x` → **68 passed** (GEN-04 + topology + template + skills gates green together).
- `uv run pytest` (full core suite) → **440 passed, 3 snapshots passed** — Phase 7 emit surface unaffected.
- `uv run pytest examples/log-parser/tests -x` → **9 passed, 2 skipped** — the 2 skips are the expected
  `.NET` egress-blocked golden-spawn cases (BOOT-01), NOT failures.
- `test -f docs/adr/0003-*.md && grep -q "plane: constitution" …` → OK.

## Deviations from Plan

None — plan executed exactly as written. Task 2 is authored as `checkpoint:human-action`; the human
ratification was granted ahead of execution via the orchestrator checkpoint (AskUserQuestion →
approve), so the ADR was drafted and landed with the `GOLDEN_APPROVE_HUMAN` marker exported on the
commit rather than pausing for a fresh approval.

## must_haves Truth Check

- GEN-04 no-dependency guard + persona anti-sprawl both green with the conductor signal in place;
  `EXPECTED_PERSONAS` stays exactly 4, conductor is the evolved orchestrator (no new primary) — YES.
- Topology-slot consistency gate + template anti-sprawl gate + skills(9) + command/referential gates
  all pass together as one closeout suite — YES (68 passed in the sampled gate group; full core 440).
- Full core suite AND instance leg BOTH green; Phase 7 emit surface unaffected — YES (440 / 9+2skip).
- ADR-0003 records the topology-slot + instance-overlay decision on the constitution plane and lands
  via the human `GOLDEN_APPROVE_HUMAN` gate — YES.

## Threat Register Check

- T-8-03 (Repudiation / Elevation — constitution write) — mitigated: ADR-0003 drafted by agent,
  ratified by human via checkpoint; landed with the `GOLDEN_APPROVE_HUMAN` token, never self-blessed,
  never `--no-verify`.
- T-8-04 (Info Disclosure — model identifiers) — mitigated: no model IDs anywhere; only the
  `provider/*-tier` placeholders remain (`test_no_real_model_identifier` in the green core suite).
- T-8-02 (Tampering — boundary erosion) — mitigated: GEN-04 guard green through closeout; ADR text
  lives under `docs/` (not a scanned core root), and no domain tokens were added to `harness/` or
  `tools/`.
- T-8-08 (Spoofing — second primary) — mitigated: `EXPECTED_PERSONAS` stays 4; the new assertion
  proves exactly one `mode: primary` persona carries the conductor signal.
- T-8-SC (Supply chain) — N/A: zero external package installs this phase.

## Anti-Sprawl

The new assertion adds no new `EXPECTED_*` set and does not grow `EXPECTED_PERSONAS` — it reads the
existing persona files and asserts on the single `mode: primary` one. ADR-0003 is an append-only
constitution record (index row added, none removed). No pinned-set update was required.

## Known Stubs

None — the assertion is concrete (targets the actual primary persona and its authored text) and
ADR-0003 is a complete MADR record with all sections filled.

## Self-Check: PASSED

- FOUND: docs/adr/0003-pipeline-topology-slot-and-instance-overlay.md
- FOUND: tools/harness_lint/tests/test_agents.py (conductor-signal assertion)
- FOUND: docs/adr/README.md (ADR-0003 index row)
- FOUND commit 0532d5a (Task 1)
- FOUND commit ec5a01f (Task 2)
