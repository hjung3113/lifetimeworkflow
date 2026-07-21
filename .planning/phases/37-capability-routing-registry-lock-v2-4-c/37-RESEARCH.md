# Phase 37 Research — Capability Routing + Registry Lock

**Date:** 2026-07-22
**Method:** repository inventory only. No web research: both requirements are about *this* harness's
own declarations, and every mechanism they need is already shipped somewhere in the tree. The
research question was therefore "what already does this, and where is the seam" — not "what library".

## 1. Inventory — what exists, and what each thing already enforces

| Asset | What it already does | Reuse verdict |
|---|---|---|
| `tools/discipline/check.py` | Loads declarations, decides owed-vs-satisfied, produces a **defect list** per record. Pure; no repo mutation. | **REUSE** — capability routing is one more defect class, not a new decision engine. |
| `tools/task_control/manager.py:440` | `missing_disciplines(...)` → `TaskControlError("missing required disciplines: ...")`, before any state write. | **REUSE unchanged** — the refusal already exists at the choke point. |
| `tools/task_control/phase_gate.py:93` | Same check on a RESUMED phase, so a fresh session cannot inherit a green a transition would have refused. | **REUSE unchanged.** |
| `tools/harness_lint/caps.py` | `EXPECTED_PERSONAS`, `READ_ONLY_PERSONAS`, `is_read_only(fm)` (checks BOTH the opencode permission matrix, per-glob-dict aware, AND the Claude `tools` string), `EXPECTED_SKILLS`. | **REUSE** — the allowlist's read-only obligation and its persona vocabulary both come from here. Restating either would be a second source of truth. |
| `tools/harness_emit/manifest.py` | `load_manifest()` over the committed owned-path set; `prune_then_write()` with a documented determinism contract (`sort_keys=True, indent=2`, trailing LF). | **REUSE** — the lock's emitted-path column is a filter over this manifest, and the lock's serialization copies the determinism contract. |
| `tools/harness_emit/emit-manifest.json` | 119 lines; every `.claude/skills/**` + `.opencode/skill/**` path the emitter owns. | **REUSE as data.** |
| `.github/workflows/ci.yml` `emit-drift` (:237) / `drift` / `stale-derived` | Three shipped recompute-then-compare gates, each its own job, each with an actionable failure message naming the fix command. | **COPY the shape** for `registry-lock`. |
| `tools/harness_lint/tests/test_discipline_wiring.py` | Bidirectional wiring lint + mutation proofs that operate on a **copy**, never the real files. | **COPY the shape** for the two new lints. |
| `tools/contract_hash/hash.py` | RFC 8785 JCS canonicalization + SHA-256, for JSON **documents**. | **DO NOT reuse** for the lock: skill sources are Markdown. Raw-byte SHA-256 is correct and keeps `contract_hash` the sole owner of JSON canonicalization. |
| `tools/risk_router/router.py` `_validate_core_policy` | Per-key **monotone superset** across the four lanes. | **DO NOT extend** — see §3. |
| `tools/risk_router/overlay.schema.json` | Precedent that a tool-local JSON Schema need not be constitution plane. | Precedent cited; `record.schema.json` already follows it. |

Net: **nothing in this phase needs a new engine.** Two new declaration files, two thin pure
libraries over them, three lints, one CI job.

## 2. Why the allowlist is per-capability and not per-lane

`_validate_core_policy` requires each lane's `required_*` list to be a **superset** of the lane
below it. That is right for obligations (a stricter lane owes more) and exactly wrong for an
allowlist (a stricter lane should permit *fewer* agents). Adding `agent_allowlist` to
`[lanes.*]` would therefore either (a) be validated in the wrong direction, silently, or (b) force
the validator to grow a per-key direction flag — a change to the shipped monotone invariant, in a
phase that is supposed to be closing debt rather than opening it.

Declaring the allowlist on the **capability** sidesteps this entirely: narrowing is expressed by
requiring a *stricter capability*, and the lane matrix keeps one meaning for all of its keys.

## 3. Where an out-of-allowlist route can actually be REFUSED

A "routing decision" in this harness is not a runtime event — there is no live dispatcher to
intercept (`harness/commands/pipeline.md`: "there is no live runtime"). The only place a routing
claim is *recorded* is the phase-36 discipline record, and its panel section already carries a
per-seat `expert` id. Phase 36's own deferred list names this as 37's job:

> "Capability-neutral routing for the panel seats (a seat is currently a prompt role, not a declared
> capability) — Phase 37, LANE-03."

So the enforcement path is:

```
harness/disciplines.toml   [discipline.X].capability = "adversarial-review"
harness/capabilities.toml  [capability.adversarial-review].providers = [...]   ← the ALLOWLIST
<task>/discipline/X.json   { "panel": { "reviews": [ { "agent": "...", ... } ] } }
        ↓ tools/discipline/check.py validate_record → defect
        ↓ missing_disciplines() non-empty
        ↓ tools/task_control/manager.py transition() → TaskControlError   ← the REFUSAL
```

Every arrow already exists except the first defect. That is the whole of LANE-03's enforcement.

## 4. What `registry.lock` catches that `emit-drift` does not

`emit-drift` re-runs the emitter and diffs. It answers *"is the emitted tree a faithful projection
of the current source?"*. It is blind, by construction, to a change in what the source **declares**,
because it re-derives the expected output from that same source. Three concrete escapes:

1. **Description rewrite.** A skill's `description` is its routing trigger. Editing it changes which
   requests reach the skill; re-emit propagates the edit to both trees and `emit-drift` is green.
2. **A new `references/` file.** `iter_reference_files` discovers the subtree by glob, so a new file
   is emitted and manifested with no declaration moving.
3. **Half-emitted surface.** If a skill ends up present in one runtime lane and not the other, the
   re-emit is still self-consistent; only a declaration of the expected **pair** catches it.

`EXPECTED_SKILLS` (`caps.py`) catches add/remove of a skill *name* and nothing else. The lock closes
the remaining surface: per skill, the description digest, every authored source file's digest, the
emitted path set in both runtimes, and the discipline ids that name it (which also lands phase 36's
second deferred item, "a `registry.lock` covering the discipline↔skill mapping").

## 5. Constraints that shaped the plans

- **No contract byte moves.** `contracts/**`, `docs/adr/**`, `golden/**`, `docs/glossary.md` are
  denied to this agent and the denial is correct. Nothing in the design needs them: the discipline
  requirement is read from live harness data (phase-36 D-02), and `record.schema.json` is tool-local.
- **`HARNESS_DEV_BYPASS` is not used.** That bypass produced RAT-4.
- **A new `tools/<name>/` gets its `pyproject.toml` in the same step** as its first module, or every
  `uv` invocation in the repo fails and takes the hooks with it. Bare-python3 escape hatch:
  `python3 tools/harness_lint/workspace_check.py`.
- **Isolatable tests.** `tools/harness_lint/tests/test_tests_are_isolatable.py` requires each new
  member's `tests/` to put the repo root on `sys.path`; verify with `uv run pytest tools/<pkg>`
  **alone**, not only via the full suite.
- **Emit round-trip.** Any `harness/` edit must re-emit to both trees with a clean porcelain.
- **Ruff baseline** only ratchets down.

## 6. Open questions carried into the plans

None blocking. Two judgement calls are recorded as CONTEXT decisions rather than research findings:
which capability vocabulary to seed (D-05/D-07) and whether the lock covers commands/agents too
(deferred — the requirement named skills).
</content>
