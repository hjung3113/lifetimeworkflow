# Phase 37 Verification — Capability Routing + Registry Lock

**Verified:** 2026-07-22 · **Scope:** phase 37 only (LANE-03, LANE-04).
**Not covered here:** the milestone-level audit, `.planning/STATE.md`, `ROADMAP.md`, `MILESTONES.md`
— the orchestrator owns milestone closeout and this document deliberately does not touch it.

**Commits:** `3875682` (planning) · `932aaf4` (LANE-03) · `5a2b5a3` (LANE-04) · `c4f1f18` (bounded
doc edit).

---

## 1. Goal-backward: did the phase deliver what it promised?

| # | Phase promise | Delivered | Evidence |
|---|---|---|---|
| SC-1 | Routing is by **declared capability**, not by hardcoded persona name | YES | `harness/capabilities.toml` declares 5 capabilities with per-capability allowlists; all 5 entries in `harness/disciplines.toml` name a `capability` and none names a persona. `test_every_declaration_names_a_declared_capability` asserts both. |
| SC-2 | Something **FAILS** when a task routes outside the allowlist | YES | §2 below — a live `TaskControlError` at `manager.transition()`, with the phase and revision proved unmoved, plus a positive control that flips it green. |
| SC-3 | A declaration that nothing enforces is not shipped | YES | The capability is validated at load (`undeclared capability` → `DisciplineError`), at record validation (per-record and per-seat), and by four `harness_lint` wiring gates each with a mutation proof. |
| SC-4 | The emitted skill surface **cannot drift** from its declaration | YES | §3 below — `registry.lock` + `--check` exit 1, gated both in-suite and as a CI job in the fan-in `needs` list. |
| SC-5 | Existing mechanisms reused, not rebuilt | YES | §5. Zero lines changed in `manager.transition()` / `phase_gate()`; the emitted-path column is read from `emit-manifest.json`; `caps.is_read_only` and `parse_frontmatter` reused as-is. |
| SC-6 | Nothing gated was written by an agent | YES | §6. No byte under `contracts/**`, `docs/adr/**`, `golden/**`, `docs/glossary.md`; no ledger row authored; `HARNESS_DEV_BYPASS` never set. |

---

## 2. LANE-03 — the out-of-allowlist route is REFUSED

**Command:**

```sh
uv run pytest "tools/task_control/tests/test_task_control.py::test_verify_is_refused_when_a_panel_seat_routes_outside_the_allowlist" -q
```

The test drives a real STRICT packet to `REVIEW` and writes a panel record that is otherwise
perfect — three **distinct** expert seats, a declared verdict, existing `outputs`. One thing differs:
the middle seat is filled by `python-engineer`, a real declared persona that is not on the
`adversarial-review` allowlist. `transition(..., "VERIFY", ...)` raises:

```
TaskControlError: missing required disciplines: adversarial-review-panel (panel seat security:
agent python-engineer is not allowed to serve capability adversarial-review
(allowlist: code-reviewer, explorer))
```

and `(after["phase"], after["revision"]) == (before["phase"], before["revision"])` proves **no state
was written**. The **positive control** in the same test rewrites only the seat's agent to an
allowlisted provider; the identical transition then returns `phase == "VERIFY"`. The refusal is
therefore caused by the route and by nothing else.

**One-line CLI form (run, output verbatim):**

```
$ uv run python -m tools.capability route adversarial-review python-engineer
REFUSED: agent python-engineer is not allowed to serve capability adversarial-review (allowlist: code-reviewer, explorer)
$ echo $?
3
```

**Also refused, as a distinct condition:** a record that never names an agent
(`test_an_unrouted_record_is_refused_like_an_absent_one`, message
`capability implementation requires a named agent, none given`). An unrecorded route must not read
the same as a permitted one.

**Enforced on resume too:** `phase_gate()` runs the same `missing_disciplines` check, so a fresh
session cannot inherit a green a fresh transition would have refused.

---

## 3. LANE-04 — the drifted skill surface is CAUGHT

**Command (run, output verbatim):**

```
$ uv run python -m tools.skill_registry --check
skill-registry: OK — 18 skill(s) match the committed lock.
$ sed -i '' 's/Use when a write is blocked or you need to reason/Use when a write is blocked or you want to reason/' harness/skills/gate-model/SKILL.md
$ uv run python -m tools.skill_registry --check

FAIL: the skill surface has DRIFTED from its declaration in harness/skills/registry.lock.
  gate-model: description changed (it is the skill's routing trigger)
  gate-model: source file changed: SKILL.md

If the change is intended, re-declare it so the move is deliberate and reviewable:

    uv run python -m tools.skill_registry --write

then commit the regenerated lock.
$ echo $?
1
```

The tree was restored and `--check` returned to `OK` (the working tree is clean; `git status` is
empty for `harness/skills/`).

**Why this is not `emit-drift` restated.** `emit-drift` re-runs the emitter and diffs; it re-derives
its expectation from the source it is checking, so it is blind by construction to a change in what
that source *declares*. The description edit above re-emits cleanly to both runtime trees and passes
`emit-drift` green. Two further escapes have the same property and their own mutation proofs:

```sh
uv run pytest tools/skill_registry -q -k "description_rewrite or new_reference_file or half_emitted"
```

**Gated twice:** the `registry-lock` CI job (`.github/workflows/ci.yml:294`) is in the fan-in
`needs` list (`:410`), and `tools/harness_lint/tests/test_skill_registry_lock.py` runs the same
comparison inside `uv run pytest`, so drift is caught before push as well as at the fan-in.

---

## 4. Gate fan-in — measured, not asserted

| Gate | Command | Result |
|---|---|---|
| Full suite | `uv run pytest -q` | **1683 passed / 8 snapshots** (baseline 1621 / 8; +62). Three runs at final HEAD: two clean, one with a single unrelated flake — see below. |
| `tools/capability` isolated | `uv run pytest tools/capability` | 21 passed |
| `tools/skill_registry` isolated | `uv run pytest tools/skill_registry` | 20 passed |
| Ruff ratchet | `uv run python -m tools.ruff_baseline` | `245 findings (baseline 245)` — **exit 0**. Baseline was lowered 266 → 245 via `--update` after findings went DOWN; never raised. |
| Contract drift | `uv run python -m tools.contract_drift.drift` | `OK — live manifest matches the committed baseline` — exit 0 |
| Registry lock | `uv run python -m tools.skill_registry --check` | `OK — 18 skill(s) match the committed lock` — exit 0 |
| Workspace | `python3 tools/harness_lint/workspace_check.py` | `OK — every globbed Python member has a pyproject.toml` — exit 0 |
| Emit round-trip | `uv run python -m tools.harness_emit` then `git status --porcelain` | No tracked modification; only this phase's uncommitted planning artifacts were listed |

The isolated runs matter and were run **alone**, not inferred from the full suite:
`test_tests_are_isolatable.py` exists because a member's tests can be green under one invocation and
red under the one CI actually uses.

### One observed flake, disclosed rather than re-run until green

One of the three full-suite runs at final HEAD reported
`FAILED tools/memory_ui/tests/test_server.py::test_post_body_is_size_bounded`
(1 failed, 1682 passed — the same 1683 total). It is recorded here rather than quietly dropped.

What was checked before calling it a flake, not a regression:

- **Not reproducible.** The test alone passes; `uv run pytest tools/memory_ui` passed **5/5**
  consecutive runs; the other two full-suite runs at the same HEAD passed it.
- **No causal path.** It binds an ephemeral localhost port (`server.make_server(0)`) and asserts an
  over-large POST is refused with 413. Phase 37 touched no HTTP surface, nothing under
  `tools/memory_ui`, and nothing it imports. The failure mode of a real-socket test under a loaded
  machine is a connection/timing error, not a changed assertion.

**Not repaired here.** It is pre-existing test-suite flakiness in another package, outside this
phase's scope, and silently stabilizing someone else's test inside a closeout would hide it. It is
surfaced for the milestone owner to decide on.

### Known-red, not this phase's, not repaired

`uv run python -m tools.docs_guard` exits **1** with exactly two bindings, the same two the phase
inherited:

```
[STALE_ADVISORY] lifecycle-eval-shadow-metrics
[STALE_REQUIRED] task-control-cli-howto
```

The set is **unchanged** — this phase introduced no new stale binding. Both are awaiting a human
ledger row (ADR-0010 §3b). See §6.

---

## 5. Reused vs built

**Reused, unchanged — no line edited:**
`manager.transition()` and `phase_gate()` (the refusal already existed; only the definition of
"missing" widened) · the phase-36 discipline record shape and defect-list idiom ·
`caps.EXPECTED_PERSONAS` / `caps.is_read_only` (both runtime representations, per-glob-dict aware) ·
`tools.harness_emit.manifest.load_manifest` and its determinism contract ·
`tools.harness_lint.parse_frontmatter` · `project_skill.iter_reference_files`' traversal defence ·
the `fan-out-synthesize` substrate for panel seats · the `emit-drift` job shape and message
discipline · `test_discipline_wiring.py`'s copy-never-the-real-file mutation idiom.

**Built:** `harness/capabilities.toml` · `tools/capability/` · `tools/skill_registry/` ·
`harness/skills/registry.lock` · one new defect class in `validate_record` · the `capability`
declaration key · the `agent` record field (root + per seat) · `test_capability_wiring.py` ·
`test_skill_registry_lock.py` · the `registry-lock` CI job.

**Explicitly not built:** a routing runtime, a second dispatcher, a parallel drift mechanism, a
second frontmatter parser, a second emit-layout computation, a second JSON canonicalizer
(`tools/contract_hash` stays the sole owner; skill sources are Markdown and take raw-byte SHA-256).

---

## 6. Human-gated artifacts drafted, and what was refused

**Drafted, not authored — `.planning/phases/37-*/drafts/ledger-rows.md`:**

Two `docs/.docs-review-ledger.toml` rows, with their digests computed at phase-37 HEAD and a
recompute snippet for landing time. They **supersede** the phase-36 drafts, because phase 37 moved
both bindings again and a row landed with a stale digest is refused:

1. `task-control-cli-howto` — `disposition = "updated"`. The three bound **sources** are untouched
   by this phase (source digest byte-identical to the phase-36 draft); only the **target** moved,
   because of the bounded edit in `c4f1f18`.
2. `lifecycle-eval-shadow-metrics` — `disposition = "reviewed-no-change"`. The source digest moved
   (`tools/lifecycle_eval/runner.py` now resolves a record's agent from the allowlist). The review
   is written out so it can be disagreed with, including the one metric worth arguing about
   (`gate_failure_reason`: the new refusal is a new *message* under the existing
   `missing required disciplines` category, not a new category). The target was **not** edited —
   manufacturing a diff to look diligent would be the dishonest option.

**Refused, with reasons:**

| Refused | Reason |
|---|---|
| Writing any `docs/.docs-review-ledger.toml` row | ADR-0010 §3b — a ledger disposition is human-only. Drafted instead. |
| Writing to `contracts/**` | Constitution plane, contract-guard denies it and the denial is correct. The design was shaped so **no contract byte needed to move**: the requirement is read from live harness data, and `record.schema.json` is tool-local (precedent `tools/risk_router/overlay.schema.json`). |
| Writing an ADR | `docs/adr/**` is gated, and no ratified decision is contradicted or extended (CONTEXT D-13). If a reviewer disagrees, the escalation is a NEW ADR in a later phase, never an edit to an accepted one. |
| Using `HARNESS_DEV_BYPASS` | That bypass produced RAT-4, the debt this milestone is discharging. Never set at any point in this phase. |
| Repairing the two known-red docs-guard bindings | Not this phase's; their human rows were already pending. Redrafted with current digests rather than force-landed. |
| Touching `.planning/STATE.md` / `ROADMAP.md` / `MILESTONES.md` or writing the milestone audit | The orchestrator owns milestone closeout. |

---

## 7. Deviations from the plans

1. **The emit-determinism syrupy snapshot was updated** (`--snapshot-update`) because the
   orchestrator persona genuinely changed. The snapshot doing its job, not a bypass; the change is
   visible in the committed `.ambr` diff.
2. **The bounded edit to `docs/how-to/task-lifecycle.md` was made** even though its bound sources
   were untouched by this phase, and even though it invalidates the phase-36 drafted target digest.
   Reason: the how-to tells an agent what to write into a discipline record, and after LANE-03 that
   record needs an `agent`. Leaving it would have had a human ratify a document the code no longer
   matches. The cost is one redrafted row, disclosed in the drafts file.
3. **Plan 37-02 T2's contingency did not trigger** — the emitter ignores `harness/skills/registry.lock`
   (verified by re-emitting: porcelain empty), so the lock stayed at the planned path rather than
   moving to `harness/registry.lock`.

## 8. Residual risk

- The capability registry is core-only; an `examples/**` instance cannot yet add its own persona to
  an allowlist. Recorded as deferred (CONTEXT), not silently omitted.
- Routing is enforced where a routing decision is **recorded** — the discipline record. A step that
  records no routing claim is still unconstrained. That is the honest limit of a harness with no live
  dispatcher, and widening it would mean inventing one.
- The command and agent surfaces are not locked the way skills are. The mechanism generalizes; the
  requirement named skills only.
