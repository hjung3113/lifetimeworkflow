---
phase: 52
slug: evidence-bounded-real-target-adoption
status: active
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-31
reconciled: 2026-07-31
---

# Phase 52 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `52-RESEARCH.md` § Validation Architecture, then **reconciled against the six
> committed `52-0N-PLAN.md` files** — every `Task ID` below is a real task in a real plan.
> Real-target evidence (SC-1/SC-3/SC-4) is **confirmation, never a test dependency** — CONTEXT D-17.

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

## Wave Map and the Shared-Tree Constraint

`.planning/config.json` sets `parallelization: true` with `workflow.use_worktrees: false` — same-wave
plans execute **concurrently in one working tree**. That fact governs which gate runs where.

| Wave | Plans | Full-suite `uv run pytest -q`? | Why |
|------|-------|-------------------------------|-----|
| 1 | 52-01 | **yes** (Task 3) | Alone in its wave. Between its Task 2 (schema + hash land) and Task 3 (derived regen), `tools/memory_regen/tests/test_contracts_index.py` is RED *by construction*; isolating the wave closes that window instead of exporting it to a sibling. |
| 2 | 52-03, 52-04 | **no — subtree gates only** | Two concurrent `tdd="true"` plans in one tree; each would otherwise observe the other's transient RED and be tempted to weaken an assertion. Cross-plan fences here are **commit-scoped** (`git show --name-only --format= HEAD`), never `git diff` on a sibling's file. |
| 3 | 52-02 | **yes** (Task 3) | Alone in its wave — the phase's single authoritative full-suite gate, run after every repair has landed. |
| 4 | 52-05 | n/a (evidence run) | Asserts `git diff --quiet -- tools/ harness/ contracts/`: no code changes. |
| 5 | 52-06 | **yes** (Task 3) | Phase close: full suite + drift gate green. |

**Standing rule for executors:** a red outside your plan's own `files_modified` in a shared wave is
not yours to fix. Re-run after the sibling's next commit. Never weaken, skip, or `xfail` an
assertion to clear a sibling-caused red — that is precisely how this repo produced the WR-07 defect
(`tools/adoption_apply/tests/test_atomic_apply.py:265-270`: a sidecar-existence assertion that still
held after `fcntl.flock` was deleted).

---

## Sampling Rate

- **After every task commit:** `uv run pytest <this plan's own test paths> -q`
- **After every plan wave:** `uv run pytest` — but only in waves 1, 3 and 5 (see the table above);
  in wave 2 the equivalent signal is each plan's subtree gate, and the full suite is picked up by
  52-02 in wave 3
- **Before `/gsd:verify-work`:** full suite green **plus** `/contract-check` green — both halves, the
  check-jsonschema instance loop AND the RFC 8785 schema-hash drift gate (D-20 changes
  `inventory.schema.json`, so a paired golden update is mandatory). 52-01 Task 3 runs the command in
  full and quotes its literal output, including the documented `SKIP: … no-op.` line for the
  instance loop (`inventory.schema.json` has no sibling instance file).
- **Max feedback latency:** < 60 seconds for the quick command

---

## Per-Task Verification Map

Every `Task ID` below names a real task in a committed plan. `❌ W0` means the test/fixture does not
exist yet and is created **in-task** by that plan's `tdd="true"` task — the RED step precedes the
implementation, so no separate Wave-0 plan is required.

| Task ID | Req / Obs | Behavior | Test Type | Automated Command | File Exists | Status |
|---------|-----------|----------|-----------|-------------------|-------------|--------|
| 52-01-T1 | RTA-02 / D-20 | The off-plane applier is write-free in `--check` and refuses an unexpected schema shape (exit 2) | script guard | `uv run python .planning/phases/52-evidence-bounded-real-target-adoption/scripts/apply-inventory-enum.py --check && git diff --quiet -- contracts/` | ❌ W0 — script created in-task | ⬜ pending |
| 52-01-T2 | RTA-02 / D-20 | The constitution-plane write lands exactly two files and moves the `inventory.schema.json` digest | human-gated diff assertion | `git diff --name-only -- contracts/` + `find contracts -name '*.schema.json' \| wc -l` = 6 | ✅ files exist | ⬜ pending |
| 52-01-T3 | RTA-02 / D-20 | `inventory.schema.json` validates and the drift gate is satisfied with a paired golden update | contract gate | `/contract-check` — the check-jsonschema instance loop **and** `uv run python -m tools.contract_drift.drift` | ✅ gate exists | ⬜ pending |
| 52-02-T1 | RTA-02 / OBS-D-01 | pnpm `packages:` globs parse; membership predicate rejects absolute and `..` globs; malformed text degrades to `[]` | unit | `uv run pytest tools/adoption_scan/tests/test_detect.py -q -k "pnpm or workspace_member"` | ❌ W0 — new tests, created in-task | ⬜ pending |
| 52-02-T1 | OBS-03 (REFUTED) pin | `_dependencies_from_package_json` is byte-unchanged — source digest equals the plan-time pin `36f3253f152f5b0b7b475499a56bfe9f84128bb89ec8a7c72af5642dc12e76b6` | source guard | the `ast.get_source_segment` + SHA-256 check embedded in 52-02 Task 1's `<verify>` | ❌ W0 — guard created in-task | ⬜ pending |
| 52-02-T2 | RTA-02 / D-17 | A neutral synthetic pnpm-workspace fixture exists and `tmp_minirepo` is untouched | fixture + regression | `uv run pytest tools/adoption_scan/tests -q` (incl. `test_snapshots.py` without `--snapshot-update`) | ❌ W0 — fixture created in-task | ⬜ pending |
| 52-02-T2 | GEN-04 | The core stays free of instance/example dependencies after the new fixture lands | guard (existing) | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -x` | ✅ existing guard | ⬜ pending |
| 52-02-T3 | RTA-02 / OBS-D-01 / D-20 | `pnpm-workspace.yaml` scopes the member set to the five declared members; the non-member manifest is excluded **and** recorded with the new `excluded` enum reason; security precedence survives | unit | `uv run pytest tools/adoption_scan/tests/test_scan_exclusions.py tools/adoption_scan/tests/test_schema_conformance.py -x` | ❌ W0 — new tests, created in-task | ⬜ pending |
| 52-02-T3 | RTA-02 / D-10 | The no-workspace-manifest path stays byte-identical (additive branch, not a replacement) | regression (existing) | `uv run pytest tools/adoption_scan/tests/test_snapshots.py tools/adoption_scan/tests/test_inventory_determinism.py -q` + `git diff --quiet -- tools/adoption_scan/tests/__snapshots__/` | ✅ existing suite is the baseline | ⬜ pending |
| 52-03-T1 | RTA-04 / OBS-D-03 / D-11 | `conventions_for()` always returns a `lint` key, `None` when unset; the 13 existing tests stay green | unit | `uv run pytest tools/harness_config/tests/test_conventions_for.py -x` | ❌ W0 — extend, in-task | ⬜ pending |
| 52-03-T2 | RTA-04 / OBS-D-03 / D-12 | `derive_language_rows` emits the full `{id,bash_scope,test,format,lint}` key set from the target's own script KEYS; no script VALUE is copied | unit | `uv run pytest tools/adoption_apply/tests/test_cli.py -x -k derive_language_rows` | ❌ W0 — new tests + `tmp_pnpm_target` fixture, in-task | ⬜ pending |
| 52-03-T3 | RTA-04 / SC-4 | After a real draft→apply, an adopted JS package's derived `[[languages]]` row yields non-null `lint`/`test` resolved from the TARGET's own emitted `harness/project.toml` | end-to-end (repo-local) | `uv run pytest tools/adoption_apply/tests/test_cli.py -x -k end_to_end` | ❌ W0 — in-task | ⬜ pending |
| 52-03-T3 | CR-01 leak scope | Every non-`harness/project.toml` **create**-disposition destination byte-equals `_harness_payload`; no `MARKER_CAPABLE` destination contains any sidecar literal | unit | `uv run pytest tools/adoption_apply/tests/test_cli.py -x -k leak` | ❌ W0 — in-task | ⬜ pending |
| 52-04-T1 | OBS-D-04 / D-15 / D-21 | The `.NAME.lock` sidecars are declared in code and the declaration EQUALS what `_apply_marker_merge` actually writes (`rglob("*.lock")` filesystem comparison) | unit | `uv run pytest tools/adoption_apply/tests/test_atomic_apply.py -x -k sidecar` | ❌ W0 — extend at/after `:267`, in-task | ⬜ pending |
| 52-04-T2 | OBS-D-04 / D-16 | A lock sidecar **from a prior run** is reported on stderr, never silently reused; a first-ever run is silent. Scope-honest: this is provenance, NOT staleness (D-15 forbids unlinking, so the predicate cannot distinguish a normal re-run from a crash) | unit | `uv run pytest tools/adoption_apply/tests/test_atomic_apply.py -x -k prior_run_lock_sidecar` | ❌ W0 — in-task | ⬜ pending |
| 52-04-T3 | OBS-D-02 / D-18 | `packages/shared` → `apps/frontend` / `apps/backend` runtime edges resolve from `workspace:*` deps (lock-in; the OBS-03 refutation cannot silently regress) | unit | `uv run pytest tools/memory_regen/tests/test_package_facts.py -x -k workspace_star` | ❌ W0 — in-task | ⬜ pending |
| 52-05-T1 · T2 · T3 | RTA-01 / RTA-02 | Real-target evidence: isolation before-proof, fresh detached worktree at the run-time `develop` HEAD, discover→draft→apply captures, five-member verdict, apply-write comparison with `matches` | **non-CI evidence artifact** | phase-directory `evidence/` capture (argv · cwd · stdout · stderr · exit code), mirroring Phase 51's layout | N/A — not a repo test **by design** (D-17) | ⬜ pending |
| 52-06-T1 · T2 | RTA-03 / RTA-04 | Target-explicit package facts (two runtime edges) and per-package convention profiles (non-null `lint`/`test`); original-checkout after-proof with drift attribution; disposal | **non-CI evidence artifact** | `evidence/downstream/*.json` + `evidence/isolation/comparison.json` + `evidence/disposal/*` | N/A — by design (D-17) | ⬜ pending |
| 52-06-T3 | SC-5 / D-19 | Every OBS-D observation terminates in a repair-plus-regression-test or an evidence-backed confirmation, each cited by a RUNNABLE pytest node id | phase record + gate | `uv run pytest -q` + `uv run python -m tools.contract_drift.drift` + `uv run pytest <each cited node id>` | ✅ gates exist | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

All Wave-0 artifacts are created **in-plan, before the consuming task** — creation always precedes
consumption in task order within the same plan, so no separate Wave-0 plan exists or is needed. Note
that not every creating task is a `tdd="true"` task: `52-02-T2` (the `tmp_pnpm_workspace` fixture)
and `52-01-T1` (the applier script) are plain `type="auto"` tasks whose output is consumed by a
LATER task in the same plan; the `tdd="true"` cases additionally have the RED step precede the
implementation inside a single task. Either way the ordering guarantee holds, so `wave_0_complete:
true` stands. Each box below names the task that owns it.

- [x] `tools/adoption_scan/tests/conftest.py` — `tmp_pnpm_workspace`, a SECOND synthetic fixture
      carrying `pnpm-workspace.yaml` plus one non-member manifest under a nested path, with
      `tmp_minirepo` left byte-identical so its committed snapshot still proves D-10. **Neutral
      vocabulary only** (widget/source/sink), per GEN-04. → **52-02-T2**
- [x] `tools/adoption_scan/tests/test_detect.py` + `test_scan_exclusions.py` — the pnpm parser,
      membership-predicate and scoping tests, incl. traversal/absolute-glob negative controls.
      → **52-02-T1**, **52-02-T3**
- [x] `tools/harness_config/tests/test_conventions_for.py` — extend for the `lint` key (presence
      always, `None` default, real value when a row declares one); all 13 existing tests stay green.
      → **52-03-T1**
- [x] `tools/adoption_apply/tests/conftest.py` — `tmp_pnpm_target`, and `test_cli.py` — the
      `derive_language_rows`, sidecar-write, splice and end-to-end profile tests. → **52-03-T2**,
      **52-03-T3**
- [x] `tools/adoption_apply/tests/test_atomic_apply.py` — extend for the sidecar-declaration
      filesystem-agreement test and the prior-run-sidecar stderr report plus its negative control.
      → **52-04-T1**, **52-04-T2**
- [x] OBS-D-02 lock-in test — sited in `tools/memory_regen/tests/test_package_facts.py`, alongside
      `package_facts.py`'s existing tests (directory confirmed). → **52-04-T3**
- [x] Framework install: **none** — pytest already present and pinned.

---

## Mutation-Check Ledger (this repo's signature defect)

Every new or edited assertion in this phase must be proven capable of failing. The bar is
**observed RED**: apply the mutation in a scratch checkout, run the test, observe the failure,
revert, and quote the literal failure output in the plan's SUMMARY. A mutation expectation recorded
only as a code comment does not count — `test_atomic_apply.py:265-270` documents an assertion that
still held with `fcntl.flock` deleted.

| Task ID | Mutation to apply | Test that must go RED |
|---------|-------------------|-----------------------|
| 52-01-T1 | Rename one value in the schema's expected 8-value pre-state | applier exits 2, not 0 |
| 52-02-T1 | Reflow or rename a local inside `_dependencies_from_package_json` | the source-digest pin |
| 52-02-T1 | Delete the traversal/absolute-glob rejection; delete the parser's try/except | the two negative-control tests |
| 52-02-T3 | Swap the non-member branch ahead of `classify_exclusions` | the security-precedence test |
| 52-03-T1 | Hardcode `"lint": None` in the loader | the injected-`cfg` `lint = "ruff check"` test |
| 52-03-T2 | Drop any key from the rendered `[[languages]]` table | the exact-key-set (Pitfall-3) test |
| 52-03-T3 | Widen the splice guard beyond the literal `"harness/project.toml"` | the create-disposition byte-equality test **and** the marker-merge no-sidecar-literal test |
| 52-04-T1 | Drop the leading dot from `lock_sidecar_for`'s formula | the `rglob("*.lock")` filesystem-agreement test |
| 52-04-T2 | Make the report unconditional (drop the `pre_existed` guard) | the fresh-run negative control |
| 52-04-T3 | Make `_dependencies_from_package_json` skip `workspace:`-prefixed versions | the workspace-edge lock-in test |
| 52-06-T3 | Append a scratch line containing a model identifier | the (name-stripped) model-identifier check exits 1 |

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Full `/adopt` discover → draft → apply against a fresh isolated FeedbackOps worktree | RTA-01, RTA-03 | Depends on a real external repo at a live SHA; making it a test would bind the suite to a machine that has the target checked out — forbidden by D-17 | Create the detached worktree at `develop` HEAD (record the literal SHA), capture the three-artifact proof before **and** after, run the three stages independently, run the two downstream read-only observations, then dispose with `git worktree remove --force` and record the exit code |
| Byte-unchanged proof for the original `develop` checkout | RTA-01 (SC-1) | The target's `develop` advances from unrelated third-party work; equality must be *reasoned about*, not asserted blind | Compare `status --porcelain=v2 --untracked-files=all`, `rev-parse HEAD` + tracked-index digest, and the untracked path-**set** digest. Any HEAD/index delta must be attributed by reconstructing index digests from the target's commit trees and recorded **outside** the OBS-D namespace |
| Constitution-plane write to `contracts/harness/adoption/inventory.schema.json` | RTA-02 (D-20) | `tools/hooks/contract_guard.py` denies agent writes under `contracts/**` unless `GOLDEN_APPROVE_HUMAN` is set, and an agent must never set or fabricate that token | 52-01-T2 is a `checkpoint:human-action`: the human runs the reviewed off-plane applier with `GOLDEN_APPROVE_HUMAN=1`, then confirms the diff is exactly two files and the contract count is still 6 |

---

## Known Limitations Carried Forward (record, do not "fix")

| Limitation | Owner | Why it is not closed here |
|------------|-------|---------------------------|
| The prior-run lock-sidecar report is **provenance, not staleness** — D-15 forbids unlinking, so the predicate is true on every run after the first | 52-04-T2 | A real staleness probe (recorded owner pid + liveness, or mtime vs run start) is new machinery with no observation behind it — NG-01 forbids speculative surface. Recorded for Phase 53. |
| After the D-12 splice, the target's `harness/project.toml` no longer matches `destinations.harness_proposed_hashes()`, so a Phase-53 re-run classifies it `conflict` rather than an observable no-op | 52-03-T3 (recorded), 52-06-T3 (carried into the phase record) | Resolving it requires MONO-12 re-run/update semantics, deferred to Phase 53 by 52-CONTEXT.md. |
| `build_facts` → `discover_manifests` is **unscoped** (`git ls-files`, no workspace globs) and reports six packages on the real target | 52-06-T1 | Workspace scoping lives in `scan.build_inventory` per D-07; extending it into `discover_manifests` exceeds this phase's scope. SC-2 is decided by the inventory. |
| `/contract-check`'s check-jsonschema half is a documented no-op for `inventory.schema.json` (no sibling instance file) | 52-01-T3 | Presence-safe by design. Real instance conformance for the new enum value is asserted by `tools/adoption_scan/tests/test_schema_conformance.py` (52-02-T3). |

---

## Validation Sign-Off

- [x] All tasks have an `<automated>` verify or a declared Wave 0 dependency — all 18 tasks across
      the six plans carry `<automated>`
- [x] Sampling continuity: no 3 consecutive tasks without an automated verify
- [x] Wave 0 covers every ❌ reference above, each bound to the owning task id
- [x] No watch-mode flags
- [x] Feedback latency < 60s for the quick command
- [x] Every repaired observation (OBS-D-01, -03, -04) terminates in a regression test; OBS-D-02
      terminates in a lock-in test — SC-5 admits no third outcome
- [x] Every new or edited assertion has an entry in the Mutation-Check Ledger with an observed-RED
      requirement
- [x] Wave assignment is safe for `parallelization: true` + `use_worktrees: false`: no same-wave
      plans share a `files_modified` entry, no plan asserts working-tree cleanliness of a
      concurrent sibling's file, and the full-suite gate runs only in single-plan waves
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved — reconciled against `52-01-PLAN.md` … `52-06-PLAN.md` on 2026-07-31.
