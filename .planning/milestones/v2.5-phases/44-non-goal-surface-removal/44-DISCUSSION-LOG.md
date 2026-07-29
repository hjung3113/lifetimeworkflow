# Phase 44: Non-Goal Surface Removal - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-29
**Phase:** 44-non-goal-surface-removal
**Mode:** `--auto --chain` — every question auto-resolved to the recommended option, no user prompts.
**Areas discussed:** Golden relocation mechanics, secret_scan removal depth, Contract deletion
fallout, `[pipeline]` removal breadth, Verification

`[--auto] Selected all gray areas: Golden relocation mechanics, secret_scan removal depth, Contract
deletion fallout, [pipeline] removal breadth, Verification.`

---

## Golden relocation mechanics (CER-09)

| Option | Description | Selected |
|--------|-------------|----------|
| Relocate to `examples/log-parser/golden_runner/`, add an explicit uv workspace member | Distinct top-level package name; no namespace collision; stays installable under `uv run` | ✓ |
| Relocate to `examples/log-parser/tools/golden_runner/`, keep the `tools.*` import path | Smallest import diff | |
| Leave the package in the core, move only `golden/` + commands + skills | Smallest diff overall | |

**Auto-selection:** `[auto] Golden relocation — Q: "Where does the package land and how does it stay
importable?" → Selected: "examples/log-parser/golden_runner/ + explicit workspace member"
(recommended default)`
**Notes:** **Live-tree finding that decided this:** root `pyproject.toml:34` declares
`members = ["libs/python", "tools/*"]` — root-scoped globs only, so anything under `examples/**` is
outside the workspace and stops being installed. Option 2 puts a second `tools/` directory under the
example, giving the `tools.*` namespace two roots; that resolves by `sys.path` order and would fail
differently in CI than locally — a bug class worth designing out rather than testing for. Option 3
fails CER-09's actual ground: `resolve_dotnet()` (`runner.py:78-85`) stays in the core, which
ADR-0002(b) forbids in its own words. Recorded risk: a moved package that is not a workspace member
still imports fine under a local `pytest` with `sys.path` manipulation while `uv run` resolves
nothing in CI — **verify with `uv run`**. Also recorded: `examples/log-parser/tests/conftest.py:3`
shows an earlier phase already moved these tests out of `tools/golden_runner/tests/`, so this
finishes a half-done migration rather than starting one.

---

## `secret_scan` removal depth (CER-08)

| Option | Description | Selected |
|--------|-------------|----------|
| Delete hook + plugin + signature + hook-group literal + prose, append to `RETIRED_SIGNATURES` | Nothing survives, and stale checkouts are actively repaired on re-emit | ✓ |
| Delete the hook, remove the signature, leave `RETIRED_SIGNATURES` alone | Smaller diff | |
| Replace with a lighter CI-side secret job | Keeps some detection | |

**Auto-selection:** `[auto] secret_scan depth — Q: "How much goes, and what happens to stale
checkouts?" → Selected: "Delete whole + append the tombstone" (recommended default)`
**Notes:** **Live-tree correction:** CER-08's prose implies a `tools/secret_scan/` package; there is
none. It is `tools/hooks/secret_scan.py` + its test + `harness/plugins/secret-scan.ts` + a
`HARNESS_SIGNATURES` entry (`merge.py:91`) + an emitted hook-group literal (`:180`) + prose at
`harness/commands/review.md:24`. Option 2 is the **exact defect Phase 43 shipped and had to fix
afterwards** (REVIEW.md CR-01, reproduced against the live emitter): a group whose command matches no
current signature is classified as human-owned and kept forever, so a stale checkout keeps invoking a
deleted module, the guard exits non-zero, and PreToolUse denies every Write/Edit/Bash with the repair
locked behind the outage. Option 3 is forbidden by CER-08's own words ("with no replacement CI job")
and by the binding constraint. Recorded separately: `tools/adoption_scan` owns its secret patterns
locally since Phase 42 (`scan.py:54,60`) and must be untouched.

---

## Contract deletion fallout (`deny-domains`, `gate-registry`)

| Option | Description | Selected |
|--------|-------------|----------|
| Delete both, repair every downstream literal in the same commit as its deletion | Follows the rule Phase 43 paid four verification passes to learn | ✓ |
| Delete both, sweep the downstream literals in a later cleanup commit | Smaller commits | |
| Delete `deny-domains` now, defer `gate-registry` again | Avoids re-touching `test_hash.py` | |

**Auto-selection:** `[auto] Contract fallout — Q: "When are the downstream literals repaired?" →
Selected: "Same commit as the deletion" (recommended default)`
**Notes:** Known downstream surfaces: `DATA_CONTRACT_PATHS` (`hash.py:32,33`), the hash manifest,
`docs_sync`'s `EXPECTED_PAGES`, `docs/reference/deny-domains.md`, `test_contract_guard.py:330`, and
two syrupy snapshots. Option 2 is precisely the pattern that produced twelve blockers in Phase 43 —
three of which would have left the phase red across multiple commits including at its own
authorization gate. Option 3 defers a collision that has already been deferred once (Phase 43's
recorded CER-07/CER-08 split) and buys nothing. **Free win recorded:** deleting `deny-domains.*`
self-clears two long-carried stale declarations — `ledger_guard` (a hook deleted in Phase 41) at
`deny-domains.json:81,102`, and `tools.deny_domains.registry` at the schema's `:5,77`, a module that
has never existed at all.

---

## `[pipeline]` removal breadth

| Option | Description | Selected |
|--------|-------------|----------|
| Remove the slot, its loader passthrough, `/pipeline`, `pipeline-map`, and `/component`'s second Mandated-order section | Matches CER-08 exactly; `[[components]]` and the contract-graph seam survive | ✓ |
| Also remove `[[components]]` and `tools/contract_graph` | "Topology" removed wholesale | |
| Keep the slot as inert data, delete only the command and skill | Smallest diff | |

**Auto-selection:** `[auto] Pipeline breadth — Q: "How much of the topology goes?" → Selected:
"Slot + loader + command + skill + /component's second half" (recommended default)`
**Notes:** **Ambiguity resolved by reading, not by guessing:** `component.md` has TWO sections titled
"Mandated order". `:15-30` (structure → per-package AGENTS.md → test harness) is the ① mechanism
CER-08 says survives; `:37-66` (derive the component agent, register the topology slot, keep the
consistency gate green) plus its `## Guard — component binding` at `:68` is the half that goes.
CER-08's "steps 1–3 survive" names the first section. Option 2 exceeds CER-08 and would break the
TOPO-02 `[contract_graph.relationships]` seam, whose `effective_relationships()` lowers the linear
edge on demand. Option 3 leaves a data slot with no reader — the "inert residue" the milestone's
no-residue posture rejects. Recorded as the phase's widest blast radius: eight
`tools/harness_lint/tests/*` read the topology.

---

## Verification

| Option | Description | Selected |
|--------|-------------|----------|
| Per-commit green + extend the Phase-43 stale-checkout assertion + YAML-resolved CI checks | Mechanical; proves the property, not the diff | ✓ |
| Structural greps + a full-suite run at phase end | Cheaper | |
| Add a CI job asserting the emitted hook set matches the signature set | A new gate — forbidden | |

**Auto-selection:** `[auto] Verification — Q: "What proves the phase done?" → Selected: "Per-commit
green + extended stale-checkout assertion + YAML-resolved CI" (recommended default)`
**Notes:** Option 2 is what Phase 43 started with, and a scratch-clone commit replay later falsified
its per-commit greenness claim after three reading-based passes had accepted it — the lesson is that
end-of-phase green says nothing about intermediate commits. Option 3 is surface growth and the
binding constraint answers it with NO; the equivalent coverage already exists as
`test_retired_signature_group_is_dropped_from_a_stale_checkout`, so this phase **extends** a test
rather than adding a gate. No mutation-proof table is owed (D-20): the phase removes a gate and adds
no control.

## Claude's Discretion

- Plan/task decomposition and wave count; CER-08's deletions and CER-09's relocation are largely
  independent, and the relocation is the long pole.
- Whether contract deletions ride with their package deletions or take their own commit.
- The exact new package name under `examples/log-parser/`.

## Deferred Ideas

- Projection repair (`caps.py`, `emit-manifest.json`, `HARNESS_SIGNATURES`, `docs/reference/**`,
  `AGENTS.md`, `.memory/derived/**`) → Phase 45 (CER-10/CER-11).
- Stale prose in six human-owned `docs/` files → Phase 45, carried out of Phase 43's review.
- ADR-0008 supersession → Phase 45 or a human call at milestone close; needs a NEW ADR under the
  repo's supersede-don't-edit convention.
- Phase 43's ROADMAP SC-1 wording, which as written can never pass → correct rather than hand-waive.
