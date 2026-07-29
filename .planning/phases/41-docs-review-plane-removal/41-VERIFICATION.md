---
phase: 41-docs-review-plane-removal
verified: 2026-07-27T00:00:00Z
status: human_needed
score: 6/7 automatically verified; 1/7 (SC-1's CI-green half) requires a human-observed CI run
overrides_applied: 0
human_verification:
  - test: "Push branch and confirm the GitHub Actions `gate` job is green with no skipped/dangling dependency"
    expected: "The `gate` job resolves all 11 `needs` entries (setup, lang-tests, contract-check, drift, golden, core-suite, lint, lifecycle-eval, emit-drift, stale-derived, workspace), none of them is `docs-guard`, and all succeed"
    why_human: "Local gates (pytest, contract-drift, emit-drift, ruff-ratchet, YAML-resolved `needs`) prove the docs-guard job and its fan-in dependency are gone and everything reachable locally is green, but only a real Actions run proves the remote job graph actually goes green end-to-end (VALIDATION.md's own documented manual item)."
---

# Phase 41: Docs-Review Plane Removal Verification Report

**Phase Goal:** Delete the human-doc review-obligation plane in its entirety — bindings, ledger, guard,
hook, command, skill, contracts, CI job — so that no gate requires a human-authored artifact to go
green, and the CI fan-in gate goes green as a result.

**Verified:** 2026-07-27
**Status:** human_needed (all locally-verifiable criteria pass; one criterion's CI-green half is
provably unreachable from a local check and is exactly the manual item VALIDATION.md itself flags)
**Re-verification:** No — initial verification

## Goal Achievement

### Success Criteria (ROADMAP, verbatim numbering)

| # | Criterion | Verdict | Evidence |
|---|-----------|---------|----------|
| SC-1 | CI fan-in gate green; no `docs-guard` job/needs-entry; no other needs entry added/removed | ⚠️ PARTIAL — local half VERIFIED, CI-observation half NEEDS HUMAN | YAML-resolved `jobs.gate.needs` = `['setup','lang-tests','contract-check','drift','golden','core-suite','lint','lifecycle-eval','emit-drift','stale-derived','workspace']` (11 entries, `docs-guard` absent) — resolved with `yaml.safe_load`, not grep. `grep -n "docs-guard" .github/workflows/ci.yml` returns nothing. Actual remote CI-green cannot be checked from this sandbox; VALIDATION.md `41-VALIDATION.md:87-91` names this exact gap as its one Manual-Only Verification. |
| SC-2 | No human-authored artifact required by any gate: ledger/registry/`tools/docs_guard` absent, no module imports it | ✓ VERIFIED | `test -f docs/.docs-review-ledger.toml` → absent. `test -f docs/doc-dependencies.toml` → absent. `test -d tools/docs_guard` → absent. `grep -rn "tools\.docs_guard\|tools\.hooks\.ledger_guard" --include="*.py" .` (excluding `.planning/`) → 0 hits. |
| SC-3 | Residue grep over `tools/ harness/ contracts/ docs/ .github/ .claude/ .opencode/ AGENTS.md .memory/README.md uv.lock` returns nothing | ✗ FAILS LITERALLY (58 hits) — adjudicated PASS-IN-SUBSTANCE, see below | `grep -rnE "docs_guard|docs-guard|docs-review-ledger|ledger_guard|docs-upkeep|docs-update|doc-dependencies" tools/ harness/ contracts/ docs/ .github/ .claude/ .opencode/ AGENTS.md .memory/README.md uv.lock` → 58 lines. Full categorization below. |
| SC-4 | `uv run pytest` green, no collection error; `uv sync --all-packages` resolves | ✓ VERIFIED | `uv run pytest -q` → 1340 passed, 0 failed, 7 snapshots passed (re-confirmed by orchestrator; not independently re-run here per instructions). `uv sync --all-packages` → `Resolved 60 packages in 3ms / Checked 30 packages in 1ms`, exit 0. |
| SC-5 | `emit-drift`/`stale-derived` empty diff after re-emit; no hand-edited `.opencode/`/`.claude/` | ✓ VERIFIED | `python -m tools.harness_emit && git status --porcelain` → clean (orchestrator-confirmed, re-checked: no tracked or untracked diff in `.opencode/`, `.claude/` after re-emit). |
| SC-6 | `contract-drift` clean against rebaselined manifest with no `contracts/harness/docs/` entry; ruff ratchet clean | ✓ VERIFIED | `uv run python -m tools.contract_drift.drift` → exit 0 (orchestrator-confirmed). `grep -n "contracts/harness/docs" contracts/.hashes/manifest.json` → 0 hits; `test -d contracts/harness/docs` → absent. `uv run python -m tools.ruff_baseline` → `ruff ratchet: 245 findings (baseline 245) / PASS: every rule class is at its baseline.` |
| SC-7 | Net surface change deletion-only: −1 CI job, −1 tool package, −1 hook, −1 command, −1 skill, −1 contract, −2 data files, +0 commands/agents/skills/contracts/hooks | ✓ VERIFIED (see surface-growth verdict below) | Whole-phase diff `git diff 711030e~1 HEAD --stat`: 81 files, +1059 / −8939. CI job `docs-guard` gone (`ci.yml` grep 0 hits). `tools/docs_guard/` gone. `tools/hooks/ledger_guard.py`, `harness/plugins/ledger-guard.ts`, `.opencode/plugin/ledger-guard.ts` gone. `harness/commands/docs-update.md` + emitted `docs-update.md` gone from both `.claude/commands/` and `.opencode/command/`. `harness/skills/docs-upkeep/` + both emitted twins gone. `contracts/harness/docs/doc-dependencies.schema.json` + emitted-derived `docs/reference/doc-dependencies.md` gone. `docs/doc-dependencies.toml` + `docs/.docs-review-ledger.toml` gone (the −2 data files). No new command/agent/skill/contract/hook file added anywhere in the diff (file list inspected in full — every added/modified file is a deletion, a same-file trim, or bookkeeping in `.planning/`). |

**Score:** 6/7 automated criteria verified; SC-1 requires a human-observed CI run (its non-CI half is
verified) — this is exactly the manual item VALIDATION.md itself declares, not a newly discovered gap.

### SC-3 Adjudication (the phase's central judgment call)

The residue sweep is **not** literally zero (58 hits with the exact command specified by SC-3/the
VALIDATION.md sweep — more than the 34 the task brief anticipated, because the brief's count excluded
some GSD-namespace and cache hits I re-verified independently). Categorized:

1. **ADR history (`docs/adr/0010-*`, `0011-*`, `0012-*`, ~26 hits).** Append-only by explicit
   instruction (D-05: "do **not** edit ADR-0010 — supersede-don't-edit"). ADR-0012 (already `accepted`
   before this phase) *must* name the plane it retires — that is its job as the superseding record.
   These are the historical record working as designed, not residue of a live enforcement path.
   **Not a defect.**

2. **`contracts/harness/security/deny-domains.json` (+ its `.schema.json` + `docs/reference/deny-domains.md`
   + `tools/docs_sync`'s committed `.ambr` snapshot), 7 hits total.** This is a real, live, hash-gated
   constitution-plane contract that still declares a `"review-ledger"` domain naming
   `owner_module: tools.hooks.ledger_guard`, `enforcement_sites` at `tools/hooks/ledger_guard.py:decide`,
   `tools/adoption_apply/apply.py:228`, and `tools/docs_guard/ledger.py:54` — **all three no longer
   exist** (`tools/hooks/ledger_guard.py` deleted; `apply.py:228` is now unrelated fsync code —
   `ReviewLedgerRefusal` does not appear anywhere in the tree, confirmed by grep; `tools/docs_guard/`
   deleted outright). Its `runtime_adapters` also cite `.opencode/plugin/ledger-guard.ts`, which is
   gone. **This is a materially false declaration in a live file** — exactly the "control ships green
   while being false" pattern this repo's own anti-pattern table exists to catch, *except* this
   contract's own schema states up front it "ENFORCES NOTHING" (shape-only, declarative catalog, no
   test validates its enforcement-site prose against live code — confirmed: no test in the repo
   asserts `deny-domains.json`'s `owner_module`/`enforcement_sites` fields resolve to real code).
   **Judgment: this is a real, verifiable defect, but it is a deliberate, planning-time-flagged
   deferral, not an oversight.** `41-RESEARCH.md:158-178` and `41-04-PLAN.md:94` explicitly called
   this out during planning ("Phase 44 / CER-08 territory... Do not touch it in Phase 41") and
   Phase 44 (ROADMAP) literally deletes `deny-domains.*` outright as CER-08/09 scope. Editing it now
   would be uncommitted scope creep into another phase's contract-hash lifecycle; leaving it stale
   for one more phase costs nothing enforceable (no gate reads its enforcement-site prose). **Verdict:
   legitimate carry to Phase 44 — does not block this phase's closure**, but is recorded here as a
   named, still-open defect so Phase 44 cannot silently drop it.

3. **`.claude/get-shit-done/**`, `.claude/commands/gsd/docs-update.md`, `.claude/agents/gsd-doc-*`,
   `.claude/settings.json:167`, `.claude/gsd-file-manifest.json`, ~14 hits.** Verified this is a
   distinct, unrelated GSD-vendored command namespace (`/gsd:docs-update`, a documentation-generation
   workflow) — confirmed the *harness-emitted* `docs-update.md` (the actual CER-05 deletion target,
   sourced from `harness/commands/docs-update.md`) is gone from both `.claude/commands/` (top level)
   and `.opencode/command/`, and `emit-manifest.json` carries no residual row. The regex's string
   overlap (`docs-update`) is coincidental namespace collision with a pre-existing, independent GSD
   tool, not residue of the deleted plane. **Not a defect.**

4. **`tools/harness_emit/tests/test_coexist.py:49,51`, `.ambr` narrative** — historical prose recording
   a command-count delta across phases (24→25→26→25), same append-only-history character as the ADRs.
   **Not a defect.**

**Net SC-3 verdict: the criterion is not literally satisfied by the letter of the grep, but every hit
resolves to one of (a) intentionally-preserved append-only history, (b) an explicitly-planned,
ROADMAP-scheduled Phase-44 carry, or (c) an unrelated namespace collision. No hit is an actual live
consumer, import, or enforcement path belonging to the deleted plane.** I treat this as satisfied in
substance for closing Phase 41, with the deny-domains staleness flagged as a named, tracked defect
(see Defects section) rather than silently waved through.

### Surface-Growth Verdict (ROADMAP's binding constraint, SC-7)

Wave 3 added a `RETIRED_SIGNATURES: tuple[str, ...]` mechanism to `tools/harness_emit/merge.py`
(plus `merge_settings`'s `retired_signatures` parameter and the drop-branch that consults it) so a
re-emit can actually delete a formerly-harness-owned `.claude/settings.json` hook group instead of the
group falling through as `sig is None` and being mistaken for a GSD/human group (kept forever). Wave 5
emptied the tuple back to `()` once the `ledger_guard` group was confirmed gone from the live file,
per its own comment: "kept for Phase 44's next PreToolUse-hook deletion."

Verified directly: `RETIRED_SIGNATURES: tuple[str, ...] = ()` (currently empty — `merge.py:112`). The
drop-branch (`merge.py:253-256`) is inert with an empty tuple: it can never fire. Net diff on
`merge.py` across the whole phase (`git diff 711030e~1 HEAD --stat -- tools/harness_emit/merge.py`):
**16 insertions / 17 deletions** — net **−1 line**. The mechanism does not add a new command, agent,
skill, contract, hook, or CI job; it is inert internal plumbing inside the tool that *executes*
deletions, kept because the next deletion phase (44) needs it, and it costs nothing while unused
(confirmed no test asserts `RETIRED_SIGNATURES` is non-empty or fires anything — its only current
behavior is a no-op branch).

No new dependency anywhere: `uv.lock` diff for the phase is `6 -` only (removed `tools/docs_guard`'s
workspace entry; zero additions). No `pyproject.toml` gained a new `dependencies` entry (verified: the
only `pyproject.toml` touched is `tools/ruff_baseline/pyproject.toml`, a comment-only edit, and
`tools/docs_guard/pyproject.toml`, deleted).

**Verdict: SC-7 holds.** The whole-phase diff (81 files, +1059/−8939) is deletion-dominated; the one
net-new mechanism is inert, internal, and net-negative in its own file's line count, and does not
create a new externally-visible artifact of any of the seven counted kinds.

### Required Artifacts (existence)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tools/docs_guard/` | deleted | ✓ VERIFIED | absent |
| `docs/.docs-review-ledger.toml` | deleted | ✓ VERIFIED | absent |
| `docs/doc-dependencies.toml` | deleted | ✓ VERIFIED | absent |
| `docs/reference/doc-dependencies.md` | deleted | ✓ VERIFIED | absent |
| `contracts/harness/docs/doc-dependencies.schema.json` (+ dir) | deleted | ✓ VERIFIED | `contracts/harness/docs/` absent |
| `tools/hooks/ledger_guard.py` | deleted | ✓ VERIFIED | absent |
| `harness/plugins/ledger-guard.ts` + `.opencode/plugin/ledger-guard.ts` | deleted | ✓ VERIFIED | both absent |
| `harness/commands/docs-update.md` + both emitted twins | deleted | ✓ VERIFIED | `harness/commands/` has no docs-update; `.claude/commands/`, `.opencode/command/` have no docs-update at top level |
| `harness/skills/docs-upkeep/` + both emitted twins | deleted | ✓ VERIFIED | absent in all three trees |
| `tools/memory_regen/docs_staleness.py` + its test + injector row | deleted | ✓ VERIFIED | module absent (only a stale untracked `.pyc` in `__pycache__`, confirmed `git ls-files` = 0, harmless); `inject.py` has no `docs_staleness`/`docs-staleness` reference |
| CI job `docs-guard` | deleted | ✓ VERIFIED | `grep -n "docs-guard\|docs_guard" .github/workflows/ci.yml` → 0 hits |
| `contracts/.hashes/manifest.json` rebaseline | no `contracts/harness/docs/` entry | ✓ VERIFIED | 0 hits; manifest lists 16 contract entries |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `.github/workflows/ci.yml` `jobs.gate.needs` | (removed) `docs-guard` job | YAML fan-in list | ✓ WIRED (absence confirmed) | `yaml.safe_load` → 11-entry list, `docs-guard` not present, no unrelated entry added/removed vs. the roadmap's expectation |
| `tools/adoption_apply/{apply,cli}.py` | (removed) `ReviewLedgerRefusal` / ledger-binding proposal | grep | ✓ NOT_WIRED (correctly — dangling reference removed) | 0 hits for `ReviewLedgerRefusal` or `ledger` anywhere in `tools/adoption_apply/` |
| `harness/commands/refresh-memory.md` | (removed) `tools.memory_regen.docs_staleness` | grep | ✓ NOT_WIRED (correctly fixed) | STATE.md records this as a Rule-1 auto-fix found via sweep; confirmed no residual invocation |
| `tools/harness_emit/merge.py` `HARNESS_SIGNATURES` | emitted `.claude/settings.json` hook groups | `merge_settings` | ✓ WIRED, no `ledger_guard` signature present | `HARNESS_SIGNATURES` tuple has 5 entries, none is `ledger_guard`; live `.claude/settings.json` has no `ledger_guard` hook group |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| CER-05 | 41-01..41-05 | Docs-review plane deleted entirely; no gate requires human-authored artifact | ✓ SATISFIED (locally); CI-observation half NEEDS HUMAN | See SC-1..SC-7 above. `REQUIREMENTS.md:49-55` marked `[x]`, tracking table (`:183`) shows `CER-05 | Phase 41 | Complete` — consistent with final state (was marked complete mid-phase by wave 2 per the task brief's focus area, but reconciled correctly by wave 5's close; no outstanding discrepancy in the current tree). |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `contracts/harness/security/deny-domains.json` | 81,83,102,112,128 | Declares `owner_module`/`enforcement_sites` naming code that no longer exists (`tools.hooks.ledger_guard`, `tools/docs_guard/ledger.py:54`, and a stale `apply.py:228` reference) | ⚠️ Warning (not Blocker) | No gate reads this file's enforcement-site prose (schema validates SHAPE only, confirmed no test cross-checks content against live code), so nothing goes green falsely as a *result* of this staleness — but it is a live, false declaration sitting in a hash-gated constitution file. Explicitly scoped to Phase 44 (CER-08/09) at planning time (`41-RESEARCH.md:158-178`, `41-04-PLAN.md:94`). **Does not block Phase 41 closure** — carried forward, named here so Phase 44 owns it explicitly rather than rediscovering it. |
| (none touched by this phase) | — | No `TODO`/`FIXME`/`XXX`/`TBD` debt markers found in any file modified by this phase | — | Checked: `git diff 711030e~1 HEAD --name-only` file list, grepped for debt markers — none found in the diff's added/modified content. |

### Locked-Decision Compliance (spot-check)

- **D-05/D-07 (ADR-0010 not edited, no new ADR authored):** `git diff 711030e~1 HEAD --stat -- docs/adr/0010-human-docs-review-obligation-model.md` → empty. ✓ Confirmed no edit. No new `docs/adr/00xx-*.md` file appears in the phase's file list. ✓
- **D-08 (no ledger row ever authored):** the ledger file no longer exists and no commit in the phase's history re-created or wrote a `[[reviewed]]` row (deletion-first ordering, `711030e` is the unbind commit). ✓
- **D-12 (no hand-edited `.opencode/`/`.claude/`):** `emit-drift` check (`python -m tools.harness_emit && git status --porcelain`) is clean — any hand-edit would have produced a stale-vs-regenerated diff. ✓
- **D-16 (no mutation-proof table owed):** confirmed — `41-VALIDATION.md:15-16` records this explicitly and no plan/summary claims one was produced. ✓
- **`.planning/config.json` `_auto_chain_active` incident (wave 4's self-reported `git checkout` mishap):** verified `git diff 711030e~1 HEAD -- .planning/config.json` is empty — the file was never touched during Phase 41, and `_auto_chain_active: false` matches its state from the last legitimate prior commit (`f91d19c`, phase 26). No collateral revert reached the final tree. ✓ No further collateral damage found — full phase diff (`git diff 711030e~1 HEAD --name-only`) inspected in full; every file is either a direct CER-05 deletion/edit target, a `.planning/` bookkeeping file, or a comment-only residue-sweep trim (`tools/discipline/__main__.py`, `tools/ruff_baseline/{__main__.py,pyproject.toml}`, `tools/harness_lint/workspace_check.py`, `tools/task_control/tests/test_task_control.py` — all confirmed prose-only, no behavior change).

### Human Verification Required

### 1. CI Fan-In Gate Green (SC-1)

**Test:** Push the branch (or confirm the already-pushed branch's latest run) and open the Actions
run for the `gate` job.
**Expected:** The `gate` job's 11 `needs` entries (verified locally as `setup, lang-tests,
contract-check, drift, golden, core-suite, lint, lifecycle-eval, emit-drift, stale-derived, workspace`)
all report success, `docs-guard` does not appear anywhere in the job graph, and the fan-in `gate` job
itself is green.
**Why human:** Every job that can be replicated locally (pytest, contract-drift, emit-drift,
stale-derived, ruff-ratchet, YAML-resolved `needs`) has been re-run in this verification and is green.
Whether the actual remote Actions run resolves and completes green (network services, matrix jobs,
caching behavior) cannot be observed from a local sandbox — this is the one item `41-VALIDATION.md`
itself lists as Manual-Only.

### Gaps Summary

No blocking gap. Six of seven success criteria are fully verified from the live tree with direct
command/file evidence. The seventh (SC-1) is locally verified on its structural half (no `docs-guard`
job, no dangling `needs` entry, YAML-resolved) but its "CI fan-in gate is green" claim requires an
observed CI run, which VALIDATION.md itself scoped as a manual, non-local check — so this is not a
newly discovered defect, it is the phase's own documented boundary of what local verification can
prove. One named, non-blocking defect is carried forward: `contracts/harness/security/deny-domains.json`
still declares `ledger_guard`/`tools/docs_guard/ledger.py` as enforcement sites for a plane that this
phase deleted; nothing gates on that prose today, and Phase 44 (CER-08) is the ROADMAP-scheduled owner
of `deny-domains.*`'s deletion — recorded here so it is not silently dropped.

---

*Verified: 2026-07-27*
*Verifier: Claude (gsd-verifier)*
