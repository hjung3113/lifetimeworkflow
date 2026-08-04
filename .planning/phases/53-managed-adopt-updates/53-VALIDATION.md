---
phase: 53
slug: managed-adopt-updates
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-01
---

# Phase 53 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
>
> **Scope note (2026-08-01):** `53-RESEARCH.md`'s Validation Architecture was written BEFORE the
> CONTEXT.md scope cut. Three of its rows are deliberately absent here — the `conflicts.json`
> artifact, the `source_sha256` field, and the exit-code-3 test — because those were cut as
> outside MONO-12. **`53-CONTEXT.md` wins over `53-RESEARCH.md` on any scope question.**

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (repo-wide; root `testpaths` covers `tools/` + `libs/python`) |
| **Config file** | root `pyproject.toml` (existing — no new config) |
| **Quick run command** | `uv run pytest tools/adoption_scan tools/adoption_apply -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~15s quick · ~4min full |

---

## Sampling Rate

- **After every task commit:** `uv run pytest tools/adoption_scan tools/adoption_apply -q`
- **After every plan wave:** `uv run pytest -q`
- **Before `/gsd:verify-work`:** full suite green **AND** the real-target re-run evidence file
  written (CONTEXT.md "Proof & surface budget" — fixtures alone are insufficient for this phase)
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

| Req | Behavior | Test Type | Automated Command | File Exists |
|-----|----------|-----------|-------------------|-------------|
| MONO-12 / SC-1 | Every destination written by apply appears in `installed.json`; nothing skipped/refused does | unit | `pytest tools/adoption_apply/tests/test_installed_record.py -x` | ❌ W0 |
| MONO-12 / SC-1 | Round-trip: record written by apply is re-readable and schema-valid on the next draft | unit | `pytest tools/adoption_apply/tests/test_installed_record.py -x` | ❌ W0 |
| MONO-12 / SC-2a | Second draft+apply with nothing changed → `applied=0 updated=0 unchanged=N`, zero target bytes written, `installed.json` byte-unchanged | unit + tree-hash | `pytest tools/adoption_apply/tests/test_update_disposition.py -x` | ❌ W0 |
| MONO-12 / SC-2b **(positive case — anti-vacuous guard)** | Harness source moves between draft 1 and draft 2 → destination flips to `update`, file is rewritten, recorded hash advances | unit | `pytest tools/adoption_apply/tests/test_update_disposition.py -x` | ❌ W0 |
| MONO-12 / SC-3 | Target-side edit after apply 1 → same destination resolves `conflict` on draft 2; target file byte-identical after apply 2; stderr names the destination + both hashes | unit | `pytest tools/adoption_apply/tests/test_update_disposition.py -x` | ❌ W0 |
| MONO-12 (safety) | A destination with **no** recorded `installed_sha` can NEVER resolve to `update`, for any combination of `existing_sha`/`proposed_sha` | unit, **mutation-tested** | `pytest tools/adoption_scan/tests/test_dispositions.py -x` | ❌ W0 |
| MONO-12 (totality) | `disposition()` remains total over the widened 7-value enum; `apply_disposition` dispatches all 7 | unit | `pytest tools/adoption_scan/tests/test_dispositions.py::test_total -x` | ✅ exists (extend) |
| WR-08 closure | `harness/project.toml`'s **post-splice** bytes are what gets recorded, so a re-adopt of an unchanged target does NOT resolve it to `conflict` | integration | `pytest tools/adoption_apply/tests/test_cli.py -x` | ✅ exists (extend) |
| WR-07 closure | The derived-languages sidecar is spliced on the `update` path too — the "not a create destination, NOT spliced" warning does not become permanent | integration | `pytest tools/adoption_apply/tests/test_cli.py -x` | ✅ exists (extend) |
| Catalog isolation | `.harness/adoption/installed.json` never appears as a `destination_catalog()` row (no self-referential disposition) | unit | `pytest tools/adoption_scan/tests/test_dispositions.py -x` | ❌ W0 |
| Contract | Extended `manifest.schema.json` validates a document carrying `installed[]`; still validates every existing Phase-52 manifest unchanged (optional array = backward compatible) | unit | `pytest tools/adoption_scan/tests -q` | ✅ exists (extend) |
| Real-target proof | One re-run against a freshly provisioned FeedbackOps worktree reproduces SC-1/2/3 with literal captured values | scripted, evidence-recorded | phase-local script (see Wave 0) | ❌ W0 |

---

## Wave 0 Requirements

- [ ] **Constitution-plane script** — `.planning/phases/53-managed-adopt-updates/scripts/`,
      modeled on the existing `apply-inventory-enum.py` precedent. Carries the exact
      `manifest.schema.json` edit (7th enum value `update` + optional `installed[]` array) plus
      the paired hash/baseline regeneration. **Human runs it** — an agent may not write
      `contracts/`. This is a hard sequencing gate: no code depending on the `update` value can
      land before this runs.
- [ ] `tools/adoption_apply/tests/test_installed_record.py` — SC-1 + round-trip +
      no-op-does-not-rewrite.
- [ ] `tools/adoption_apply/tests/test_update_disposition.py` — SC-2a, SC-2b, SC-3.
- [ ] Phase-local real-target script under `.planning/phases/53-managed-adopt-updates/scripts/`,
      mirroring Phase 52's `compare-worktree-writes.py` (D-21) placement. **Phase-local, not a
      `tools/` module** — so it does not count against NG-01's governed-surface budget, per
      Phase 52's own precedent.
- [ ] **Mutation-test evidence** for every new or edited assertion, recorded in the plan summary.

---

## Anti-Vacuous Test Requirements (BLOCKING)

This repo's signature defect is checks that cannot fail, and this phase is unusually exposed to
it: a suite that tests only the **no-op** passes even if the `update` branch is deleted entirely.
Both `53-RESEARCH.md` Pitfall 5 and Phase 52's own CR-03 (three self-caught vacuous tests) name
this exact failure mode.

Therefore, for each success criterion, a **paired positive and negative** assertion is required —
a no-op assertion alone is not acceptable evidence:

| SC | Negative (thing does not happen) | Positive (thing DOES happen) |
|----|----------------------------------|------------------------------|
| SC-2 | unchanged source → no write | changed source → `update` fires, bytes change, hash advances |
| SC-3 | diverged file → byte-unchanged | diverged file → `conflict` classified AND reported on stderr |
| Safety | no recorded hash → never `update` | recorded hash matching target → `update` reachable |

Each new assertion must be **mutation-tested**: break the logic it guards, confirm the test reds,
restore, record the result in the plan's summary. An assertion whose mutation stays green is not
a check.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Instructions |
|----------|-------------|------------|--------------|
| `contracts/harness/adoption/manifest.schema.json` edit | MONO-12 | Constitution plane — `contract_guard` refuses agent writes; CODEOWNERS gates it | Human reviews and runs the Wave-0 off-plane script, then confirms `python -m tools.contract_drift` is clean and the contract count is still 6 |
| Real-target re-run on FeedbackOps | MONO-12 SC-1/2/3 | Requires provisioning a worktree of a third-party repo; the original `develop` checkout must stay byte-unchanged | Follow the Phase-52 provisioning/disposal sequence; capture before/after proofs; write the evidence file |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or a named Wave 0 dependency
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Every SC has BOTH a positive and a negative assertion (anti-vacuous table above)
- [ ] Every new/edited assertion mutation-tested, result recorded
- [ ] Contract count still 6 after the constitution-plane script runs
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
