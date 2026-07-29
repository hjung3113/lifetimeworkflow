---
phase: 26
slug: deterministic-brownfield-inventory-mapping-v2-3-b
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-19
---

# Phase 26 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `26-RESEARCH.md` § "Validation Architecture". `<pkg>` is the new tool package
> name, fixed by the planner (research recommends a purpose-built scanner package under `tools/`).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest `>=8.4,<9` (uv workspace) + syrupy 5.2.0 |
| **Config file** | root `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["libs/python", "tools"]`) — **plus a new `tools/<pkg>/tests/conftest.py`** for `sys.path` wiring (Wave 0) |
| **Quick run command** | `uv run pytest tools/<pkg> -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | quick ~5 s; full suite ~60 s (unchanged from Phase 24/25) |

**Contract gates (run at wave merge, not per task):**
- `uv run python -m tools.contract_drift.drift`
- `uv run python -m tools.docs_sync && uv run python -m tools.memory_regen.contracts_index && git diff --exit-code -- docs/reference .memory/derived/contracts-index.md`

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tools/<pkg> -q`
- **After every plan wave:** Run `uv run pytest -q` + `uv run python -m tools.contract_drift.drift`
- **Before `/gsd:verify-work`:** Full suite green + drift green + committed-derived fresh + `git diff --exit-code uv.lock` clean
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

Task IDs are assigned by the planner; the Requirement → automated-command mapping below is fixed
by research and MUST be preserved. Threat refs come from the PLAN `<threat_model>` blocks.

| Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|----------|-----------|-------------------|-------------|--------|
| ADOPT-01 | Target tree byte-unchanged after a scan (hash every fixture file before/after) | unit | `uv run pytest tools/<pkg>/tests/test_readonly.py -x` | ❌ W0 | ⬜ pending |
| ADOPT-01 | Scan confined — symlink escaping target root skipped + recorded | unit | `… tests/test_scan_exclusions.py::test_symlink_escape_excluded` | ❌ W0 | ⬜ pending |
| ADOPT-01 | Secret excluded by path (`.env`) | unit | `…::test_secret_path_excluded` | ❌ W0 | ⬜ pending |
| ADOPT-01 | Secret excluded by content pattern; matched bytes absent from artifact | unit | `…::test_secret_content_excluded_and_not_echoed` | ❌ W0 | ⬜ pending |
| ADOPT-01 | Binary excluded (NUL prefix) | unit | `…::test_binary_excluded` | ❌ W0 | ⬜ pending |
| ADOPT-01 | Vendored dir excluded (`node_modules/`) | unit | `…::test_vendored_excluded` | ❌ W0 | ⬜ pending |
| ADOPT-01 | Generated file excluded (`__pycache__` + `@generated` marker) | unit | `…::test_generated_excluded` | ❌ W0 | ⬜ pending |
| ADOPT-01 | Over-cap file excluded as `size-capped`, not read | unit | `…::test_size_cap` | ❌ W0 | ⬜ pending |
| ADOPT-01 | Evidence pointers carry `{path, sha256, size}`; paths repo-relative POSIX | unit | `…::test_evidence_pointer_shape` | ❌ W0 | ⬜ pending |
| ADOPT-01 | Language + manifest + doc/ADR/AGENTS/CODEOWNERS/CI surfaces detected | unit | `… tests/test_detect.py` | ❌ W0 | ⬜ pending |
| **SC-1** | Double run over the fixture is byte-identical | unit | `… tests/test_determinism.py::test_double_run_byte_identical` | ❌ W0 | ⬜ pending |
| **SC-1** | Seeded-shuffled enumeration order produces identical bytes | unit | `…::test_shuffled_enumeration_byte_identical` | ❌ W0 | ⬜ pending |
| **SC-1** | Committed syrupy snapshot of all three artifacts | snapshot | `… tests/test_snapshots.py` | ❌ W0 | ⬜ pending |
| ADOPT-02 | Every plan entry carries exactly one of observed/inferred/unknown | unit | `… tests/test_plan_classification.py::test_every_entry_classified` | ❌ W0 | ⬜ pending |
| ADOPT-02 | Ambiguous ownership yields a **question**, never an `authority` | unit | `…::test_unresolved_ownership_becomes_question` | ❌ W0 | ⬜ pending |
| ADOPT-02 | Question records satisfy the D-05 floor + deterministic ordering | unit | `…::test_question_shape_and_ordering` | ❌ W0 | ⬜ pending |
| ADOPT-02 | Relationship candidates validate against `topology/relationship.schema.json` | unit | `…::test_relationship_candidates_validate` | ❌ W0 | ⬜ pending |
| **ADOPT-03 / SC-3** | Every catalog destination resolves to exactly one disposition (totality) | unit | `… tests/test_dispositions.py::test_total` | ❌ W0 | ⬜ pending |
| ADOPT-03 | Each of the 6 dispositions exercised by ≥1 case | unit | `…::test_each_disposition_reachable` | ❌ W0 | ⬜ pending |
| ADOPT-03 | Constitution path is `human-ratification-required` even when the file exists | unit | `…::test_constitution_always_ratification` | ❌ W0 | ⬜ pending |
| ADOPT-03 | Hash-equal → `preserve`; hash-different → `conflict` | unit | `…::test_collision_rule` | ❌ W0 | ⬜ pending |
| ADOPT-03 | `marker-merge` only for root `AGENTS.md` / root `CLAUDE.md` / `.claude/settings.json` | unit | `…::test_marker_capable_set` | ❌ W0 | ⬜ pending |
| ADOPT-03 | GSD-owned lanes excluded (by predicate), not dispositioned | unit | `…::test_gsd_lanes_excluded` | ❌ W0 | ⬜ pending |
| D-01 | All three artifacts validate against their new schemas | unit | `… tests/test_schema_conformance.py` | ❌ W0 | ⬜ pending |
| D-01 | Drift gate green after rebaseline | gate | `uv run python -m tools.contract_drift.drift` | ✅ exists | ⬜ pending |
| D-01 | Committed-derived plane fresh | gate | `uv run python -m tools.docs_sync && uv run python -m tools.memory_regen.contracts_index && git diff --exit-code -- docs/reference .memory/derived/contracts-index.md` | ✅ exists | ⬜ pending |
| repo invariant | GEN-04 core→example guard still green | gate | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -q` | ✅ exists | ⬜ pending |
| repo invariant | `uv.lock` unchanged | gate | `uv sync --all-packages && git diff --exit-code uv.lock` | ✅ exists | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tools/<pkg>/pyproject.toml` — workspace member (else `uv sync --all-packages` fails)
- [ ] `tools/<pkg>/tests/__init__.py` + `conftest.py` — `sys.path` wiring, `parents[3]` (copy `tools/harness_config/tests/conftest.py`)
- [ ] `tools/<pkg>/tests/fixtures/minirepo/**` — the ONE synthetic target tree (D-06), embedding: secret file · secret content · binary · vendored dir · generated file · over-cap file · collision pair (hash-equal + hash-different) · ambiguous-evidence case · escaping symlink. **Domain-neutral vocabulary only** (no log-parser terms — GEN-04).
- [ ] All `test_*.py` files marked ❌ W0 above
- [ ] Framework install: **none** — pytest + syrupy already present

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Schema ratification on the constitution plane | D-01 | `contracts/` writes are refused to agents by design; ratification is merge-time CODEOWNERS review (machines gate, humans ratify) | Author schema → `uv run python -m tools.contract_hash.hash --write` (never hand-edit `contracts/.hashes/manifest.json`) → verify `uv run python -m tools.contract_drift.drift` green. Drift is **expected RED between those two steps**. In-session writes need a human `GOLDEN_APPROVE_HUMAN`. |

---

## Validation Sign-Off

- [ ] All tasks have an automated verify or a Wave 0 dependency
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all ❌ MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
