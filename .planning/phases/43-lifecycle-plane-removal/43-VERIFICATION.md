---
phase: 43-lifecycle-plane-removal
verified: 2026-07-28T00:00:00Z
status: passed
score: 8/8 success criteria verified
overrides_applied: 1
overrides:
  - must_have: "SC-1 — the ROADMAP's literal bare-token grep over tools/ harness/ contracts/ .github/ .claude/ .opencode/ returns nothing"
    reason: >-
      The literal command returns 11 matches, ALL of which fall inside the pre-declared
      <surviving_residue> table in 43-04-PLAN.md:357-387 (module-docstring history, one
      assertion-failure hint string, and four synthetic graph-input strings that are a
      NEGATIVE control — deleting them would delete the control). The criterion's INTENT
      ("no residue package … unreachable by construction") is verified independently and
      exactly: the executable-invocation sweep
      `grep -rnE "(python -m tools\.|from tools\.|import tools\.)(task_control|task_packet|risk_router|evidence|handoff|discipline|capability|lifecycle_eval)\b"`
      over the same six product-surface paths returns ZERO real invocations, and all 8
      package directories are gone. The literal wording is unsatisfiable-by-construction
      and should be reworded in the ROADMAP; see WARNING-1.
    accepted_by: "gsd-verifier (recorded for human ratification)"
    accepted_at: "2026-07-28T00:00:00Z"
re_verification:
  previous_status: none
  previous_score: n/a
deferred:
  - truth: "ROADMAP SC-1's implied CI-green half"
    addressed_in: "Milestone PR (out of phase scope)"
    evidence: >-
      .github/workflows/ci.yml triggers on `pull_request:` only and this repo opens one PR
      per milestone. CI cannot go green in-repo for a mid-milestone phase. All 11 CI jobs
      were re-run locally by this verifier with their exact `run:` commands; all exit 0.
  - truth: "docs/how-to/task-lifecycle.md, docs/explanation/task-lifecycle-shadow-metrics.md, docs/explanation/next-milestone-task-control-plane.md carry stale prose about the deleted plane"
    addressed_in: "Phase 45 (Projection Repair)"
    evidence: >-
      Human-owned Diátaxis docs; deliberately out of Phase 43's scope per D-01/D-18 and the
      43-04 <surviving_residue> scoping note. Confirmed present and stale (11 dead
      `uv run python -m tools.<deleted>` invocations in task-lifecycle.md alone).
human_verification: []
---

# Phase 43: Lifecycle Plane Removal — Verification Report

**Phase Goal:** Delete the task-control lifecycle plane whole — 8 `tools/` packages, its contracts,
its four commands, its hook, its five discipline skills, its three `harness/*.toml` declarations, its
`.workflow/tasks/` state directory, and its CI job. **No residue package**: a Python state manager
must be unreachable in the product by construction, not merely unused.

**Requirement:** CER-07
**Commits verified:** `f589a67..HEAD` (14 commits, `d38c18b` … `9db95ed`)
**Verified:** 2026-07-28
**Status:** passed (8/8, with 1 recorded deviation and 4 warnings)
**Re-verification:** No — initial verification

---

## Goal Achievement — Per-Criterion Verdict

| # | Success Criterion | Verdict | Evidence (executed, not read) |
|---|---|---|---|
| 1 | 8 package dirs gone; residue grep returns nothing | ✓ PASSED (deviation) | All 8 dirs absent; 56 files deleted under them. Literal grep returns 11 matches, all inside the pre-declared `<surviving_residue>` table. **Executable-invocation sweep returns ZERO** across `tools/ harness/ contracts/ .github/ .claude/ .opencode/`. Hyphenated `task-control` sweep (the Phase-42 miss) also run — every hit is a legitimate `gate-registry.json` reference or negative control. See override. |
| 2 | `uv run pytest --collect-only -q` exits 0, zero collection errors | ✓ VERIFIED | `982 tests collected in 0.23s`, no errors, exit 0. |
| 3 | `contracts/harness/task-control/` holds only `gate-registry.json`; drift exits 0 | ✓ VERIFIED | `ls` → `gate-registry.json` only. 6 contracts deleted (`attestation`, `evidence`, `handoff`, `state`, `task`, `transitions`). `uv run python -m tools.contract_drift.drift` → `contract-drift: OK — live manifest matches the committed baseline.` exit 0. |
| 4 | `test_capability_wiring.py` gone with `capabilities.toml`; `caps.py` names no deleted skill/command | ✓ VERIFIED | `tools/harness_lint/tests/` has no `test_capability_wiring.py` or `test_discipline_wiring.py`. `harness/*.toml` = `project.toml` only. `EXPECTED_SKILLS` (caps.py:132-147) = the 12 survivors, none deleted. Only residual mention in caps.py is a comment at `:129` recording the removal. |
| 5 | No `lifecycle-eval` job; YAML-resolved fan-in `needs` = 10, nothing else added/removed | ✓ VERIFIED | ruamel resolve: `needs` = `['setup','lang-tests','contract-check','drift','golden','core-suite','lint','emit-drift','stale-derived','workspace']` — **10**. `'lifecycle-eval' in d['jobs']` → `False`. Job list = the 10 + `gate`. |
| 6 | `inject.py` drops the active-task block, KEEPS the activeContext pointer — asserted by a test | ✓ VERIFIED | Diff removes `TASK_HEADER`, `_active_task_pointer()`, the `("task", task)` section and its non-droppable exemption; `_active_context_pointer()` and `("active", …)` survive. **Runtime proof:** `uv run python -m tools.memory_regen.inject` last line = `## Progress log (pointer)` / `.memory/state/activeContext.md — … [updated: 2026-07-16]`. **Test is non-vacuous:** `test_active_context_is_pointer_not_body` (test_inject_assembler.py:124-131) asserts the pointer path IS in the payload AND the live-body marker `## In flight` IS in the body AND is NOT in the payload — the middle conjunct is the vacuity guard. 20/20 pass. |
| 7 | Suite green; emit-drift, stale-derived, contract-drift, ruff ratchet clean; `uv.lock` refreshed | ✓ VERIFIED (1 warning) | `uv run pytest -q` → **982 passed, 7 snapshots**. emit-drift: `python -m tools.harness_emit && git diff --exit-code --stat` → exit 0, no diff. stale-derived: `docs_sync && memory_regen.contracts_index && git diff --exit-code` → exit 0. contract-drift exit 0. ruff ratchet exit 0 (`84 findings, baseline 245 — PASS`). `uv.lock` modified; sweep for all 8 deleted members in `uv.lock` + `pyproject.toml` → zero hits. `workspace_check.py` → OK. See WARNING-3 on the un-rebaselined ratchet. |
| 8 | Deletion-only: −8 pkgs, −6 contracts, −4 cmds, −1 hook, −5 skills, −3 decls, −1 CI job, **+0** | ✓ VERIFIED | `git diff f589a67..HEAD --diff-filter=A --name-only` outside `.planning/` → **empty**. 8 dirs gone; 6 contracts gone; emitted commands 25→**21** in both trees; emitted skills = 12 in both trees; `tools/hooks/resume_gate.py` + `harness/plugins/resume-gate.ts` gone and no `resume_gate` reference survives in `.claude/settings.json`, `.opencode/`, or `merge.py`; `RETIRED_SIGNATURES` correctly re-emptied to `()` (merge.py:111); `.workflow/` does not exist. |

**Score: 8/8.**

---

## Structural Gates — Re-Run by the Verifier

| Gate | Command | Result | Exit |
|---|---|---|---|
| collect | `uv run pytest --collect-only -q` | 982 collected, 0 errors | 0 |
| core-suite | `uv run pytest -q` | 982 passed, 7 snapshots | 0 |
| contract-drift | `uv run python -m tools.contract_drift.drift` | live manifest == baseline | 0 |
| ruff ratchet | `uv run python -m tools.ruff_baseline` | 84 findings vs baseline 245 — PASS | 0 |
| emit-drift | `uv run python -m tools.harness_emit` then `git diff --exit-code` | **no diff** — committed emitted trees byte-match what the source produces | 0 |
| stale-derived | `uv run python -m tools.docs_sync && … memory_regen.contracts_index` then `git diff --exit-code` | no diff | 0 |
| workspace | `python3 tools/harness_lint/workspace_check.py` | OK | 0 |

Working tree is clean after all seven runs (`git status --short` empty).

---

## D-01 — The Five Surviving Artifacts (coherence, not grep)

Each was read as a full diff against `f589a67`, checking that what remains is a runnable procedure
and not a document with a hole.

| Artifact | Verdict | Finding |
|---|---|---|
| `harness/commands/checkpoint.md` | ✓ COHERENT | Steps renumbered 1–2 with no gap; the surviving `git add` / `git commit` pair is a complete, self-consistent two-file publication flow; the closing Note was rewritten from "when there is no active task, preserve the existing two-file flow" to "the two-file flow is the whole flow" — the conditional was resolved, not left dangling. |
| `harness/commands/orient.md` | ✓ COHERENT | The resume-barrier section deleted and headings renumbered 1–3; the read-order list renumbered 1–4 with the HANDOFF entry removed and no orphan cross-reference to it. Both surviving `!` commands are live and runnable (verified by running the injector). |
| `harness/commands/review.md` | ✓ COHERENT | A trailing paragraph removed. The document now ends on "…separation of duties is the point." — a complete closing sentence, with the `/review` → `/verify-work` loop intact. |
| `harness/commands/verify-work.md` | ✓ COHERENT | An interstitial paragraph removed between "Run the five gates in order…" and "## 1. Lint…". The five numbered gates and their order are untouched, which was the stated invariant. |
| `harness/agents/orchestrator.md` | ✓ COHERENT | The heaviest repair: routing rewritten from three dimensions (capability → stage → language) to two (stage → language), procedure renumbered 1–7 with no gap, the routing table's three capability rows removed or rewritten to name the persona directly, and the "registry wins" authority sentence re-pointed at `project.toml` rather than deleted. Zero occurrences of `capability`/`capabilities.toml` remain in the emitted copies. No step references a deleted command or module. |

---

## Structural-Absence Sweep (both spellings)

**Underscore form** — `task_control|task_packet|risk_router|tools\.evidence|tools\.handoff|tools\.discipline|tools\.capability|lifecycle_eval`
over `tools/ harness/ contracts/ .github/ .claude/ .opencode/`: 11 matches, **all** in the plan's
`<surviving_residue>` table —

- `tools/harness_lint/tests/test_tests_are_isolatable.py:19,23,26,27,33,108` — module-docstring history + one hint string (table row 1)
- `tools/contract_graph/tests/test_query.py:75-78` — synthetic graph-input strings feeding the negative control at `:72` (table row 3)
- `tools/harness_config/tests/test_relationship_schema.py:3` — one docstring sentence (table row 4)

**Hyphen form** — `task-control` over the same paths plus `AGENTS.md README.md README.ko.md .memory/`:
14 matches, all legitimate — 8 are `contracts/harness/task-control/gate-registry.json` references
(Phase 44's file, correctly retained: `contract_hash/hash.py:31`, its tests, `adoption_scan`
docstrings, `contracts/.hashes/manifest.json`, the derived contracts-index + its `.ambr` snapshot),
4 are narrative/negative-control prose (`contract_graph/query.py:19`, `test_query.py:10,72`,
`test_coexist.py:46`, `docs_sync` test comment), and 2 are README lines discussed below.

`AGENTS.md` is clean. `.memory/derived/` carries only the gate-registry row (derived, regenerated
byte-identically by this verifier).

---

## Warnings — Not Blocking, But Real

**WARNING-1 (BOOKKEEPING / CONTRACT WORDING) — ROADMAP SC-1 is unsatisfiable as literally written.**
The bare-token grep can never return empty while the negative-control fixture in
`tools/contract_graph/tests/test_query.py:75-78` exists — and that fixture must exist, because
deleting it deletes the assertion that `query.py` imports nothing from the task-control plane. The
criterion should be reworded to the executable-invocation form this verifier actually ran. Left as
written it invites either a permanent false red or a hand-waive that also waives the real check.

**WARNING-2 (DEFECT INTRODUCED BY THIS PHASE) — broken internal anchor in `README.ko.md`.**
Commit `c92c869` deleted the `## v2.2 — Adaptive Task Control Plane` section (present at
`f589a67:README.ko.md:51`) but left the table-of-contents link at `README.ko.md:11`:
`[v2.2 Task Control Plane](#v22--adaptive-task-control-plane)`. That anchor now resolves to nothing.
`README.md` has no equivalent problem — its v2.2 material was converted in place into a
`<details>` block marked "shipped, removed in v2.5" (`README.md:198`) and its TOC never linked it.
No gate covers internal-anchor integrity, which is why this survived.

**WARNING-3 (GATE SLACK) — the ruff ratchet was not rebaselined after a 12,383-line deletion.**
`baseline 245` vs `found 84`. The gate passes, so SC-7 holds, but the ratchet now tolerates 161
new findings before it fires. The tool itself printed the remedy:
`uv run python -m tools.ruff_baseline --update`. Not run in this phase.

**WARNING-4 (GATE HOLE) — nothing validates `python -m tools.X` references inside `docs/`.**
`tools/adoption_scan/tests/test_install_completeness.py::_discover_module_refs` regex-walks
`harness/commands/**`, `harness/skills/**` and `.github/workflows/*.yml` only. `docs/` is outside
its globs, which is exactly why `docs/how-to/task-lifecycle.md` can carry 11 invocations of deleted
modules with the full suite green. This is the mechanism, not just the instance.

**Informational** — the assertion-failure hint at `test_tests_are_isolatable.py:108` still tells a
future developer to "copy `lifecycle_eval`'s" conftest, a package that no longer exists. Accepted by
the plan's residue table (row 1 names `:108` explicitly), recorded here because it is the one
residue site that is user-facing rather than pure narrative.

---

## What the Phase Did NOT Achieve

1. **CI-green cannot be demonstrated in-repo.** `ci.yml` triggers on `pull_request:` only and this
   repo opens one PR per milestone. Mitigated, not solved: this verifier executed all 11 jobs'
   `run:` commands locally and every one exits 0.
2. **Three human-owned docs still describe the deleted plane** — `docs/how-to/task-lifecycle.md`
   (11 dead `uv run python -m tools.<deleted>` commands — a how-to whose every step now fails),
   `docs/explanation/task-lifecycle-shadow-metrics.md`, `docs/explanation/next-milestone-task-control-plane.md`.
   Deliberate, carried to Phase 45. **Larger than the three named:** `docs/how-to/README.md` and
   `docs/adr/README.md` index them, and `docs/explanation/agent-workflow-skillset-design-guide.md`
   also carries plane prose. (`docs/adr/0008-task-control-plane-lifecycle.md` is correctly untouched —
   ADRs are append-only.)
3. **Phase bookkeeping not closed.** `.planning/ROADMAP.md`'s Progress table still reads
   `43. Lifecycle Plane Removal | v2.5 | 0/5 | Planned | -`, and `.planning/REQUIREMENTS.md:71`
   leaves CER-07 unchecked with `:186` reading `Not started`. Both contradict the landed work.
4. **`README.ko.md` TOC anchor left dangling** (WARNING-2).
5. **ruff baseline not re-recorded** (WARNING-3).

---

## Follow-Up Phase Must Absorb

| # | Item | Suggested owner |
|---|---|---|
| 1 | Rewrite the three Phase-45 docs (or delete them) — `docs/how-to/task-lifecycle.md` first, it is executable-looking and 100% dead | Phase 45 |
| 2 | Sweep `docs/how-to/README.md`, `docs/adr/README.md`, `docs/explanation/agent-workflow-skillset-design-guide.md` — the three docs above are not the whole set | Phase 45 |
| 3 | Fix the dangling `#v22--adaptive-task-control-plane` TOC anchor in `README.ko.md:11` | Phase 45 (or a quick fix) |
| 4 | `uv run python -m tools.ruff_baseline --update` — close 161 findings of ratchet slack | Phase 44 or 45 |
| 5 | Extend `_discover_module_refs`'s globs to cover `docs/**/*.md`, or add an equivalent dead-invocation gate, so item 1's failure class cannot recur silently | Phase 45/46 |
| 6 | Reword ROADMAP SC-1 into the executable-invocation form, and mark Phase 43 complete in the ROADMAP Progress table + tick CER-07 in REQUIREMENTS.md | Phase closeout |
| 7 | Optional: retire the `lifecycle_eval` hint string at `test_tests_are_isolatable.py:108` | Any |

---

## Gaps Summary

No must-have failed. All 8 ROADMAP success criteria are satisfied against the live tree, verified by
execution rather than reading: the 8 packages, 6 contracts, 4 commands, 1 hook, 5 skills, 3
declarations, the state directory and the CI job are gone; nothing was added outside `.planning/`;
the plane is unreachable by construction (zero executable invocations anywhere in the product
surface); the four structural gates and the full 982-test suite are green; and the emitted `.opencode/`
and `.claude/` trees provably match what `tools.harness_emit` regenerates from source.

The single deviation is SC-1's literal wording, which is unsatisfiable by construction and was
pre-declared and measured in `43-04-PLAN.md`'s `<surviving_residue>` table before execution. The
open items are all downstream prose, bookkeeping, or gate-tightening — none of them re-admits the
deleted plane into the product.

---

_Verified: 2026-07-28_
_Verifier: gsd-verifier_
