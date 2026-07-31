---
phase: 52
slug: evidence-bounded-real-target-adoption
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-31
---

# Phase 52 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `52-RESEARCH.md` § Validation Architecture. Real-target evidence (SC-1/SC-3/SC-4)
> is **confirmation, never a test dependency** — CONTEXT D-17.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.x (pinned `>=8.4,<9`, `pyproject.toml:16`) |
| **Config file** | root `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["libs/python", "tools"]`) |
| **Quick run command** | `uv run pytest tools/adoption_scan tools/harness_config tools/adoption_apply -q` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | quick ~seconds; full suite bounded by the existing `tools/` + `libs/python` suite |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tools/adoption_scan tools/harness_config tools/adoption_apply -q`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd:verify-work`:** Full suite must be green, **plus** `/contract-check` green (D-20 changes `inventory.schema.json`, so check-jsonschema + the RFC 8785 schema-hash drift gate must both pass with a paired golden update)
- **Max feedback latency:** < 60 seconds for the quick command

---

## Per-Task Verification Map

Task IDs are assigned by the planner; this map binds each success criterion and observation to its
proving signal. The executor fills `Task ID` as plans land.

| Task ID | Req / Obs | Behavior | Test Type | Automated Command | File Exists | Status |
|---------|-----------|----------|-----------|-------------------|-------------|--------|
| TBD | RTA-02 / OBS-D-01 | `pnpm-workspace.yaml` scopes the member set; a non-member manifest is excluded **and** recorded via the new `excluded` enum reason (D-20) | unit | `uv run pytest tools/adoption_scan/tests/test_detect.py -k pnpm -x` | ❌ W0 — new test + synthetic fixture | ⬜ pending |
| TBD | RTA-02 / D-10 | No-workspace-manifest path stays byte-identical (additive branch, not a replacement) | regression (existing) | `uv run pytest tools/adoption_scan/tests -q` | ✅ existing suite is the baseline | ⬜ pending |
| TBD | RTA-02 / D-20 | `inventory.schema.json` validates and the drift gate is satisfied with a paired golden update | contract gate | `/contract-check` (check-jsonschema + schema-hash) | ✅ gate exists | ⬜ pending |
| TBD | RTA-04 / OBS-D-03 | `conventions_for()` always returns a `lint` key, `None` when unset | unit | `uv run pytest tools/harness_config/tests/test_conventions_for.py -x` | ❌ W0 — extend (13 existing tests must stay green) | ⬜ pending |
| TBD | RTA-04 / OBS-D-03 | An adopted JS package's derived `[[languages]]` row carries real `lint`/`test` from the target's `package.json` scripts | unit | `uv run pytest tools/adoption_scan/tests -k draft -x` | ❌ W0 | ⬜ pending |
| TBD | OBS-D-04 | Apply leaves no *unlisted* artifact; `.NAME.lock` sidecars are declared/expected in phase-local comparison scope (D-21) | unit | `uv run pytest tools/adoption_apply/tests/test_atomic_apply.py -x` | ❌ W0 — extend at/after `:267` | ⬜ pending |
| TBD | OBS-D-04 / D-16 | A stale lock is reported on stderr, never silently reused | unit | `uv run pytest tools/adoption_apply/tests/test_atomic_apply.py -k stale_lock -x` | ❌ W0 | ⬜ pending |
| TBD | OBS-D-02 / D-18 | `packages/shared` → `apps/frontend` / `apps/backend` runtime edges resolve from `workspace:*` deps (lock-in; the OBS-03 refutation cannot silently regress) | unit | `uv run pytest tools/memory_regen/tests -k workspace_edge -x` (confirm the exact test dir before authoring) | ❌ W0 | ⬜ pending |
| TBD | GEN-04 | The core stays free of instance/example dependencies after the new fixture lands | guard (existing) | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -x` | ✅ existing guard | ⬜ pending |
| TBD | RTA-01 / RTA-03 | Real-target evidence: three-artifact byte-unchanged proof, discover→draft→apply exit codes, package-facts edges, resolved convention profiles | **non-CI evidence artifact** | phase-directory `evidence/` capture (argv · cwd · stdout · stderr · exit code), mirroring Phase 51's layout | N/A — not a repo test **by design** (D-17) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tools/adoption_scan/tests/` — a synthetic pnpm-workspace fixture (new, or an extension of
      `conftest.py`'s `tmp_minirepo`) carrying a `pnpm-workspace.yaml` plus one non-member manifest
      under a nested path. **Neutral vocabulary only** (widget/source/sink) — never FeedbackOps-specific
      naming, per GEN-04.
- [ ] `tools/harness_config/tests/test_conventions_for.py` — extend for the `lint` key (presence
      always, `None` default); all 13 existing tests stay green.
- [ ] `tools/adoption_apply/tests/test_atomic_apply.py` — extend for the lock-sidecar
      declared-as-known behavior and the stale-lock stderr report.
- [ ] OBS-D-02 lock-in test — site it alongside `package_facts.py`'s existing tests; confirm the
      existing test directory name before authoring.
- [ ] Framework install: **none** — pytest already present and pinned.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Full `/adopt` discover → draft → apply against a fresh isolated FeedbackOps worktree | RTA-01, RTA-03 | Depends on a real external repo at a live SHA; making it a test would bind the suite to a machine that has the target checked out — forbidden by D-17 | Create the detached worktree at `develop` HEAD (record the literal SHA), capture the three-artifact proof before **and** after, run the three stages independently, run the two downstream read-only observations, then dispose with `git worktree remove --force` and record the exit code |
| Byte-unchanged proof for the original `develop` checkout | RTA-01 (SC-1) | The target's `develop` advances from unrelated third-party work; equality must be *reasoned about*, not asserted blind | Compare `status --porcelain=v2 --untracked-files=all`, `rev-parse HEAD` + tracked-index digest, and the untracked path-**set** digest. Any HEAD/index delta must be attributed by reconstructing index digests from the target's commit trees and recorded **outside** the OBS-D namespace |

---

## Validation Sign-Off

- [ ] All tasks have an `<automated>` verify or a declared Wave 0 dependency
- [ ] Sampling continuity: no 3 consecutive tasks without an automated verify
- [ ] Wave 0 covers every ❌ reference above
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s for the quick command
- [ ] Every repaired observation (OBS-D-01, -03, -04) terminates in a regression test; OBS-D-02
      terminates in a lock-in test — SC-5 admits no third outcome
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
