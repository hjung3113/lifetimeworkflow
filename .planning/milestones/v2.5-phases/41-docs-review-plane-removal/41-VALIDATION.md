---
phase: 41
slug: docs-review-plane-removal
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-27
---

# Phase 41 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `41-RESEARCH.md` §"Validation Architecture". **Deletion-only phase:** "validated"
> means the residue sweep returns zero, every named gate exits as expected, and the suite is green.
> Per CONTEXT.md **D-16**, no mutation-proof / adversarial-input table is owed — nothing
> control-shaped is being added.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest via `uv run pytest` (uv workspace, `members = ["libs/python", "tools/*"]`) |
| **Config file** | root `pyproject.toml` |
| **Quick run command** | `uv run pytest tools/adoption_apply tools/harness_lint tools/harness_emit tools/hooks tools/docs_sync tools/memory_regen -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | quick ~30-60s · full ~3-5 min (1664 passed at Phase 40 close) |

---

## Sampling Rate

- **After every task commit:** the touched package's own tests (e.g. `uv run pytest tools/adoption_apply -q`
  after editing `apply.py`), plus `uv run pytest --collect-only -q` whenever a module is deleted —
  a stranded import surfaces as a collection error, not a test failure.
- **After every plan wave:** full `uv run pytest -q` **plus** the residue grep sweep.
- **Before `/gsd:verify-work`:** full suite green and all four structural gates clean
  (`emit-drift`, `stale-derived`, `contract-drift`, ruff ratchet).
- **Max feedback latency:** ~60s (quick) / ~5 min (full).
- **Ordering caveat (D-10):** run gates *after* `git add` + `git commit -- <pathspec>`, never before —
  `tools/adoption_scan/destinations.py:217` reads `git ls-files`, so a tracked deletion reds until
  staged and committed. A red before commit is expected, not a defect; amend if still red after.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| (unbind) | 01 | 1 | CER-05 | — | N/A | absence | `test ! -f docs/.docs-review-ledger.toml` | ✅ | ⬜ pending |
| (tool delete) | 01 | 1 | CER-05 | — | N/A | collection | `uv run pytest --collect-only -q` | ✅ | ⬜ pending |
| (consumer edits) | 01 | 1 | CER-05 | — | N/A | unit | `uv run pytest tools/adoption_apply tools/memory_regen tools/hooks -q` | ✅ | ⬜ pending |
| (contract removal) | 01 | 1 | CER-05 | — | N/A | gate | `python -m tools.contract_drift.drift` (exit 0 after rebaseline) | ✅ | ⬜ pending |
| (emit) | 01 | 1 | CER-05 | — | N/A | gate | `python -m tools.harness_emit && git status --porcelain` (empty) | ✅ | ⬜ pending |
| (CI job removal) | 01 | 1 | CER-05 | — | N/A | structural | YAML-resolve `gate.needs`; no dangling `docs-guard` | ✅ | ⬜ pending |
| (residue sweep) | 01 | last | CER-05 | — | N/A | integration | grep sweep below (must exit 1 = no match) | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Residue sweep (the phase's headline observable):**

```
grep -rnE "docs_guard|docs-guard|docs-review-ledger|ledger_guard|docs-upkeep|docs-update|doc-dependencies" \
  tools/ harness/ contracts/ docs/ .github/ .claude/ .opencode/ AGENTS.md .memory/README.md uv.lock
```

Expected: **exit 1, no output.** `.planning/**` history is exempt and is not rewritten.

**What a botched deletion looks like** (each is an observable, not a feeling):
- a dangling `docs-guard` entry in the CI fan-in `needs` → the `gate` job never becomes satisfiable;
- a stranded `from tools.docs_guard...` / `from tools.hooks.ledger_guard...` import → pytest
  **collection** error (research found `tools/adoption_apply/apply.py:65` does exactly this at module
  level, so it must be edited, not merely have its test deleted);
- a hand-edited `.opencode/` or `.claude/` file → `emit-drift` non-empty diff;
- a removed contract without a manifest rebaseline → `contract-drift` red.

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No new test file, fixture, or framework
install — this is deletion-only.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CI fan-in gate is green on the pushed branch | CER-05 (SC-1) | Only the real CI run proves the fan-in `needs` resolves and every remaining job passes; local gates cannot | Push the branch, open the Actions run, confirm the `gate` job is green with no skipped/dangling dependency |

---

## Validation Sign-Off

- [x] All tasks have an automated verify command (table above)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0: nothing owed
- [x] No watch-mode flags
- [x] Feedback latency < 60s (quick) / < 5 min (full)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
