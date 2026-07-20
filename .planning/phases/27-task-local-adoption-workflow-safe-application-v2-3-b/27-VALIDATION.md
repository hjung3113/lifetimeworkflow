---
phase: 27
slug: task-local-adoption-workflow-safe-application-v2-3-b
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-21
---

# Phase 27 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `27-RESEARCH.md` § Validation Architecture (authoritative — this file is the
> execution-facing projection of it).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest `>=8.4,<9` (uv workspace) + syrupy 5.2.0 — same as Phase 26 |
| **Config file** | root `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths` already includes `tools`) + a new `tools/adoption_apply/tests/conftest.py` (Wave 0) copying `tools/adoption_scan/tests/conftest.py`'s `sys.path` wiring |
| **Quick run command** | `uv run pytest tools/adoption_apply -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~10s quick · ~90s full |

**No new package.** `uv.lock` must be unchanged at phase end.

---

## Sampling Rate

- **After every task commit:** `uv run pytest tools/adoption_apply -q`
- **After every plan wave:** `uv run pytest -q` + `uv run python -m tools.contract_drift.drift` + `uv run python -m tools.harness_emit.generate && git diff --exit-code -- .opencode .claude`
- **Before `/gsd:verify-work`:** full suite green + contract-drift green + emit-drift green + GEN-04 green
- **Max feedback latency:** 10 seconds (quick), 90 seconds (full)

---

## Per-Task Verification Map

*Task IDs are filled by the planner; the Req/Behavior/Command columns are locked by RESEARCH.md.*

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | — | ADOPT-04 | — | Batch created under `.workflow/tasks/<id>/artifacts/adoption/<batch>/`; two `discover` runs against an unchanged ref resume the same batch | unit | `uv run pytest tools/adoption_apply/tests/test_batch_layout.py::test_resume_safely -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | — | ADOPT-04 | — | Batch state flows through the existing CAS `_cas_write` — a stale `expected_revision` is rejected like any other task mutation | unit | `…test_batch_layout.py::test_batch_uses_existing_cas` | ❌ W0 | ⬜ pending |
| TBD | TBD | — | ADOPT-05 | T-27-path | Discovery/draft mode never writes outside the task artifact root (escape attempt refused) | unit | `…test_atomic_apply.py::test_draft_confined_to_artifact_root` | ❌ W0 | ⬜ pending |
| TBD | TBD | — | ADOPT-05 | T-27-const | `apply.py` refuses every `contracts/` / `docs/adr/` / `golden/` destination **before any filesystem write** — spy proves zero `open()`/`os.link()` for a refused destination | unit | `…test_constitution_refusal.py::test_refuses_before_mutation` | ❌ W0 | ⬜ pending |
| TBD | TBD | — | ADOPT-05 | — | Second `apply` against an unchanged target is a no-op — target bytes identical before/after | unit | `…test_atomic_apply.py::test_idempotent_reapply` | ❌ W0 | ⬜ pending |
| TBD | TBD | — | ADOPT-05 | T-27-drift | A `create` whose target changed after draft-time is refused, not silently applied | unit | `…test_atomic_apply.py::test_concurrent_drift_refused` | ❌ W0 | ⬜ pending |
| TBD | TBD | — | ADOPT-05 | — | Marker-merge for the 3 `MARKER_CAPABLE` destinations reuses `harness_emit.merge` and is idempotent | unit | `…test_atomic_apply.py::test_marker_merge_idempotent` | ❌ W0 | ⬜ pending |
| TBD | TBD | — | ADOPT-06 | T-27-selfapprove | Approval refused (exit 3) without explicit `--approve` + human confirmation value, mirroring `/golden-approve` | unit | `…test_approval_invalidation.py::test_refused_without_human_confirmation` | ❌ W0 | ⬜ pending |
| TBD | TBD | — | ADOPT-06 | — | Approval invalidated when ONLY the draft hash changes | unit | `…::test_invalidated_on_draft_change` | ❌ W0 | ⬜ pending |
| TBD | TBD | — | ADOPT-06 | — | Approval invalidated when ONLY the task revision changes | unit | `…::test_invalidated_on_revision_change` | ❌ W0 | ⬜ pending |
| TBD | TBD | — | ADOPT-06 | — | Approval invalidated when ONLY the git ref changes | unit | `…::test_invalidated_on_ref_change` | ❌ W0 | ⬜ pending |
| TBD | TBD | — | **SC-1** | — | Full resume cycle: batch resumes safely; changed draft/ref/revision invalidates approval | integration | `…test_approval_invalidation.py::test_sc1_full_resume_cycle` | ❌ W0 | ⬜ pending |
| TBD | TBD | — | **SC-2** | — | Constitution destinations refused before mutation; non-constitution apply atomic/collision-safe/idempotent | integration | `…test_atomic_apply.py::test_sc2_full_apply_cycle` | ❌ W0 | ⬜ pending |
| TBD | TBD | — | **SC-3** | — | 3 fixtures (polyglot single-repo, 2-repo client/server, partial/collision incl. CRLF/BOM) pass end-to-end | integration/snapshot | `uv run pytest tools/adoption_apply/tests/test_fixtures.py -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | — | ADOPT-07 | — | `/adopt` command + `brownfield-adoption` skill structurally valid (frontmatter, routing description) | unit | `uv run pytest tools/harness_lint/tests/test_commands.py tools/harness_lint/tests/test_skills.py -q` | ✅ | ⬜ pending |
| TBD | TBD | — | ADOPT-07 | T-27-exec | No arbitrary command execution — `apply.py`/`batch.py`/`approval.py` never `subprocess.run` an argv derived from manifest/draft content | unit | `…test_atomic_apply.py::test_no_arbitrary_command_execution` | ❌ W0 | ⬜ pending |
| TBD | TBD | — | **SC-4** | — | `/adopt` + skill round-trip byte-identical to both runtimes; no new persona, no model id | gate | `uv run python -m tools.harness_emit.generate && git diff --exit-code -- .opencode .claude` | ✅ | ⬜ pending |
| TBD | TBD | — | ADOPT-07 | — | GEN-04 core→example independence still green after new fixtures/tools | gate | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -q` | ✅ | ⬜ pending |
| TBD | TBD | — | D-01 (contract) | — | New `approval.schema.json` validates; drift gate green after rebaseline | gate | `uv run python -m tools.contract_drift.drift` | ✅ | ⬜ pending |
| TBD | TBD | — | repo invariant | — | Committed-derived plane fresh | gate | `uv run python -m tools.docs_sync && uv run python -m tools.memory_regen.contracts_index && git diff --exit-code -- docs/reference .memory/derived/contracts-index.md` | ✅ | ⬜ pending |
| TBD | TBD | — | repo invariant | — | `uv.lock` unchanged (no new package) | gate | `uv sync --all-packages && git diff --exit-code uv.lock` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tools/adoption_apply/pyproject.toml` — new uv workspace member (otherwise `uv sync --all-packages` fails)
- [ ] `tools/adoption_apply/tests/__init__.py` + `conftest.py` — copy `tools/adoption_scan/tests/conftest.py`'s `sys.path` wiring pattern
- [ ] **Read `tools/adoption_scan/tests/fixtures/minirepo/**` in full** plus `tests/fixtures/workspace/{member-a,member-b}/**` before deciding new-vs-extend for each of the 3 fixtures (RESEARCH.md flagged this as its own MEDIUM-confidence gap — do not skip)
- [ ] `tools/adoption_apply/tests/fixtures/{polyglot-single,client-server,partial-collision-crlf}/**` — the 3 SC-3 fixtures, domain-neutral (GEN-04)
- [ ] All `test_*.py` files marked ❌ above
- [ ] `contracts/harness/adoption/approval.schema.json` — new schema, human-ratified, paired with `contracts/.hashes/manifest.json` rebaseline in one atomic commit
- [ ] Framework install: **none** — pytest / syrupy / jsonschema already present

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Human ratification of `approval.schema.json` + hash rebaseline | ADOPT-06 / D-01 | Constitution plane is human-gated — machines gate, humans ratify; an agent must not self-bless a new contract | Blocking `checkpoint:human-verify` task; reviewer confirms the new schema + manifest diff before the atomic commit lands |
| Promotion decisions for proposed contract / golden / ADR / relationship-authority / conflict / unknown items | ADOPT-06 | These are judgement calls the workflow must *require a human for* — automating them would defeat the requirement | The `/adopt` promotion path must refuse to self-approve; verified by `test_refused_without_human_confirmation` plus reviewer inspection |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
