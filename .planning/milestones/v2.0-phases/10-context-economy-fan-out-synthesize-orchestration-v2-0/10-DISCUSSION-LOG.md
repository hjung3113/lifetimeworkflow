# Phase 10: Context-Economy Fan-out/Synthesize Orchestration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-13
**Phase:** 10-Context-Economy Fan-out/Synthesize Orchestration
**Mode:** `--auto --chain` (autonomous discussion; recommended option selected per area)
**Areas discussed:** Deliverable form, Dispatch/runtime-neutrality, Fan-out worker persona, Synthesize owner, Return contract (ECON-02), Delegate-vs-inline guide (ECON-03)

---

## Deliverable form (ECON-01)

| Option | Description | Selected |
|--------|-------------|----------|
| Skill only | Reusable workflow, no dedicated entry command | |
| Command only | `/fan-out-synthesize` macro, no progressive-disclosure skill | |
| Both skill + command | Skill = reusable workflow; thin command = human/CI entry point | ✓ |

**Choice:** Both — skill + command (D-01/D-02).
**Notes:** Mirrors the Phase-9 both-command-and-agent shipping pattern and the existing skill+command pairing; ECON-01 requires the workflow be usable by BOTH a human and the conductor.

---

## Dispatch mechanism & runtime-neutrality (ECON-01)

| Option | Description | Selected |
|--------|-------------|----------|
| Bespoke dispatch tool/engine | New runtime tool that fans out subagents | |
| Procedural skill on existing Task affordance | Skill documents the procedure; orchestrator dispatches via its existing `task`/`Task` tool | ✓ |

**Choice:** Runtime-neutral procedural skill on the existing Task affordance (D-03/D-04).
**Notes:** v2.0 non-negotiable is reuse-not-rebuild. `deep-research`/`Workflow` are shape inspiration only, never a deployed-harness runtime dependency.

---

## Fan-out worker persona (ECON-01)

| Option | Description | Selected |
|--------|-------------|----------|
| New dedicated analyst persona | A 6th persona that returns schema-bounded summaries | |
| Reuse read-only `explorer` | Existing read-only worker; return contract enforced by prompt | ✓ |

**Choice:** Reuse `explorer`; `EXPECTED_PERSONAS` stays 5 (D-05).
**Notes:** Persona anti-sprawl gate. A dedicated persona is a deferred idea only if explorer's scope proves insufficient.

---

## Synthesize step owner (ECON-01)

| Option | Description | Selected |
|--------|-------------|----------|
| New synthesizer persona | Dedicated agent that merges the recovered summaries | |
| Primary orchestrator/conductor | The conductor (already `task: allow`, sole planner) synthesizes | ✓ |

**Choice:** Orchestrator synthesizes; no new persona (D-06).
**Notes:** One shared workflow, not two — matches ECON-01 and anti-sprawl.

---

## Return contract — location & form (ECON-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Under domain `contracts/` plane | JSON Schema in the CODEOWNERS-gated constitution plane | |
| Harness-authored schema reference | Domain-neutral JSON Schema co-located with the skill (`references/` byte-copy) | ✓ |
| Prose-only convention | No machine schema, just body prose | |

**Choice:** Harness-authored, domain-neutral schema reference beside the skill (D-07/D-08/D-09).
**Notes:** Honors "schema-bounded" + contract-first without polluting the instance data plane or tripping the domain drift gate (GEN-04). The return is an ephemeral runtime value — a schema the subagent conforms to, not a CI-diff-gated file.

---

## Delegate-vs-inline guide — form & wiring (ECON-03)

| Option | Description | Selected |
|--------|-------------|----------|
| Orchestrator prose only | Heuristic buried in the persona body | |
| Dedicated `context-budget` skill + wiring | Progressive-disclosure skill wired into orchestrator + `/orient` | ✓ |

**Choice:** Dedicated `context-budget` skill, wired into BOTH the orchestrator and `/orient` (D-10/D-11).
**Notes:** ECON-03 names both integration points; matches how `gate-model`/`two-plane-memory` are surfaced. Makes the routing decision observable and repeatable.

---

## Claude's Discretion

- Exact skill/command file names (recommended: `fan-out-synthesize`, `/fan-out-synthesize`, `context-budget`).
- Precise JSON-Schema field set of the return contract and its reference-file layout.
- Whether to add a lightweight conformance validator (optional, not a gate requirement).

## Deferred Ideas

- Dedicated analyst/summarizer persona (only if explorer proves insufficient).
- CI-gated / persisted fan-out artifacts (the return stays ephemeral this phase).
- Cross-repo fan-out / workspace-level synthesis (Phase 11 / MREPO).
