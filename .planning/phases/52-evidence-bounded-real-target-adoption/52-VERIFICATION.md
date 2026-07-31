---
phase: 52-evidence-bounded-real-target-adoption
verified: 2026-08-01T00:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
re_verification: null
---

# Phase 52: Evidence-Bounded Real-Target Adoption — Verification Report

**Phase Goal:** FeedbackOps receives the required adoption capabilities, with changes limited to
purpose-relevant failures proven by Phase 51
**Verified:** 2026-08-01
**Status:** passed
**Re-verification:** No — initial verification

Verification stance was adversarial: the starting hypothesis was that tasks completed and the goal
was missed. Every SUMMARY claim below was checked against a literal artifact, a live command, or a
mutation experiment. Four independent mutation experiments were run to falsify the phase's
"observed RED" claims.

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| SC-1 | `/adopt` discover → draft → apply completes against the isolated worktree while the original `develop` checkout stays byte-unchanged | ✓ VERIFIED | `evidence/apply/exit-code.txt` = `0`; `evidence/apply/stderr.txt` = `applied=154 skipped=86 refused=23`; `evidence/isolation/comparison.json` all four booleans `true` (`status_equal`, `head_equal`, `index_equal`, `untracked_set_equal`) plus the same four true in the `post_disposal` block. **Independently re-confirmed live at verification time** (not from the record): `/Users/hyojung/Desktop/2026/FeedbackOps` HEAD = `919d152a56ed096c0fdef12b9bfb892d6ef4ced6` and `git ls-files -s \| shasum -a 256` = `60f1e62025b36cbfea5a8e0fbc6a48de19c5c67a457a891d9270d9340532e726` — byte-identical to both the before and after digests recorded in `comparison.json`. |
| SC-2 | Inventory contains all five real workspace members | ✓ VERIFIED | Read from the artifact itself, not the comparison summary: `evidence/discover/inventory.json` → `candidate_process_boundaries` = exactly `.`, `apps/backend`, `apps/frontend`, `packages/shared`, `packages/ui` (5 entries, each with a real sha256+size); `manifests` = the matching 5 `package.json` paths; `excluded` contains `{"path": "docs/design-prototype/package.json", "excluded": "non-workspace-member"}`. `member-comparison.json` `members_equal_expected_five: true`. |
| SC-3 | Package facts contain the real `packages/shared` → `apps/frontend` and `apps/backend` edges | ✓ VERIFIED | `evidence/downstream/workspace-edge-comparison.json`: `both_runtime_edges_present: true`; `all_edges_from_target` contains `@fops/frontend → @fops/shared (runtime)` and `@fops/backend → @fops/shared (runtime)` (plus two further real edges). |
| SC-4 | Each adopted package resolves a nearest-wins convention profile containing lint and test commands | ✓ VERIFIED | `evidence/downstream/convention-comparison.json`: `all_js_packages_have_lint_and_test: true`; every one of the six per-package rows carries `lint: "pnpm run lint"` and `test: "pnpm run test"`; `config_source` is the **worktree's** `harness/project.toml`, not the harness checkout's. Backing code path re-verified by mutation (below). |
| SC-5 | Every change traces to a Phase-51 observation within purpose ①②③④ and has a regression test; no-change observations remain evidence-backed confirmations | ✓ VERIFIED | All 7 node ids cited in the trace ledger were **executed by the verifier**, not taken on the ledger's word: `uv run pytest -q <7 node ids>` → `7 passed in 0.56s`. Every one exists at the cited path. OBS-D-01/-03/-04 each terminate in a named repair + regression test; OBS-D-02 terminates in its lock-in test with zero code change. Four mutation experiments confirm the tests actually discriminate (below). |

**Score:** 5/5 truths verified

### Trace-Ledger Test Execution (SC-5, verifier-run)

| OBS-D | Node id | Result |
| --- | --- | --- |
| OBS-D-01 | `tools/adoption_scan/tests/test_scan_exclusions.py::test_pnpm_non_member_manifest_excluded_and_absent_from_included_and_manifests` | PASS |
| OBS-D-01 | `tools/adoption_scan/tests/test_scan_exclusions.py::test_pnpm_workspace_exactly_five_members` | PASS |
| OBS-D-02 | `tools/memory_regen/tests/test_package_facts.py::test_workspace_star_dependency_edges_resolve_by_name` | PASS |
| OBS-D-03 | `tools/harness_config/tests/test_conventions_for.py::test_lint_value_is_read_from_the_matched_language_row_not_hardcoded` | PASS |
| OBS-D-03 | `tools/adoption_apply/tests/test_cli.py::test_end_to_end_pnpm_target_resolves_lint_and_test_through_real_config` | PASS |
| OBS-D-04 | `tools/adoption_apply/tests/test_atomic_apply.py::test_expected_lock_sidecars_matches_filesystem_after_every_marker_merge` | PASS |
| OBS-D-04 | `tools/adoption_apply/tests/test_atomic_apply.py::test_prior_run_lock_sidecar_is_reported_on_stderr` | PASS |

### Mutation Experiments (falsifying the "checks that cannot fail" hypothesis)

Each mutation was applied to a real source file, the test run, the result observed, and the file
byte-restored. `git status --porcelain` is clean afterwards.

| # | Mutation | Target test(s) | Observed |
| --- | --- | --- | --- |
| A | `apply.py`: `fcntl.LOCK_EX \| LOCK_NB` → `fcntl.LOCK_SH \| LOCK_NB` | `test_marker_merge_acquires_exclusive_flock` | RED (`AssertionError` at line 410) — the **widened bitmask assertion still discriminates a shared lock** |
| B | `scan.py`: short-circuit the workspace-scoping branch to `False` | `test_scan_exclusions.py` | RED ×3, incl. both SC-2 regression tests (`assert 'non-workspace-member' in set()`) |
| C | `loader.py`: `lang.get("lint")` → hardcoded `"pnpm run lint"` | `test_conventions_for.py` | RED ×2, incl. `test_lint_value_is_read_from_the_matched_language_row_not_hardcoded` |
| D | `detect.py`: delete the `".."` traversal-rejection guard | `test_detect.py` | RED — `test_workspace_member_traversal_glob_contributes_no_members`, exactly the 52-02 SUMMARY's claim |

Mutations A and D directly falsify-tested the two SUMMARY claims flagged for scrutiny (the widened
bitmask assertion, and 52-02's replaced negative controls). Both claims hold.

**Deviation #3 adjudicated (assertion widening did NOT weaken the proof).** The pre-existing
assertion `call.args[1] == fcntl.LOCK_EX` became `call.args[1] & fcntl.LOCK_EX == fcntl.LOCK_EX`.
This still rejects `LOCK_SH` (`1 & 2 == 0`), proven by mutation A. The only property it stopped
proving — that the acquisition is *blocking* — is separately covered by
`test_held_lock_still_blocks_and_emits_no_prior_run_report`, which drives the real concurrency
observer. The widening is compensated, not a loss of coverage.

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `contracts/harness/adoption/inventory.schema.json` | `non-workspace-member` enum member + description | ✓ VERIFIED | Diff is exactly the enum addition + description extension; 4-line semantic change |
| `contracts/.hashes/manifest.json` | rebaselined hash `688b75206df6…` | ✓ VERIFIED | `34a31944…` → `688b75206df61d4b94ab071c1d1ec2ad686d4e434e33eca99774684050302396`; `uv run python -m tools.contract_drift.drift` exits `0` (`contract-drift: OK`) |
| `.memory/derived/contracts-index.md` + contracts-index snapshot | regenerated to new prefix | ✓ VERIFIED | Commit `2d84709` updates both; full suite green including `test_render_matches_committed_snapshot` |
| `tools/adoption_scan/detect.py` | `PNPM_WORKSPACE_MANIFEST`, `parse_pnpm_workspace_globs`, `is_workspace_member` | ✓ VERIFIED | Substantive (93 insertions, **0 deletions**), filesystem-free, wired from `scan.build_inventory` |
| `tools/adoption_scan/scan.py` | workspace scoping in `build_inventory` | ✓ VERIFIED | Additive branch; `classify_exclusions` ordering preserved verbatim; mutation B proves it is load-bearing |
| `tools/harness_config/loader.py` | permanent `lint` key on `conventions_for()` | ✓ VERIFIED | `"lint": lang.get("lint") if lang else None`; mutation C proves it reads the row |
| `tools/adoption_apply/cli.py` | `derive_language_rows()`, draft sidecar, apply splice | ✓ VERIFIED | Splice guard is the exact literal `"harness/project.toml"`; real run emitted `evidence/draft/languages.toml` and the splice line on stderr |
| `tools/adoption_apply/apply.py` | `lock_sidecar_for`, `expected_lock_sidecars`, `HARNESS_MANAGED_LOCK_SIDECARS`, NB-first flock + report | ✓ VERIFIED | `HARNESS_MANAGED_LOCK_SIDECARS` derived from imported `MARKER_CAPABLE`, never retyped; on-disk `rglob` cross-check test present |
| `evidence/**` (discover, draft, apply, isolation, downstream, disposal, metadata) | literal argv/cwd/stdout/stderr/exit + JSON | ✓ VERIFIED | Present and internally consistent for every stage |
| `52-ADOPTION-EVIDENCE.md` | phase record + SC-5 trace ledger | ✓ VERIFIED | Contains all five SC verdicts with deciding artifact + deciding value, the OBS-D ledger, the scope fence, the three Phase-53 consequences, and the disposal result |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `scan.build_inventory` | `detect.is_workspace_member` | direct call under the `workspace_globs is not None` branch | ✓ WIRED | Mutation B turns the SC-2 regression tests RED |
| `cli._cmd_draft` | `derive_language_rows` | root `package.json` read when `pnpm-workspace.yaml` present | ✓ WIRED | `evidence/draft/languages.toml` exists with the derived row |
| `cli._cmd_apply` | `harness/project.toml` payload | sidecar byte-append | ✓ WIRED | `evidence/apply/stderr.txt` contains the literal `spliced … into harness/project.toml payload` line |
| `conventions_for` | worktree `harness/project.toml` | `[[languages]]` row match | ✓ WIRED | `convention-comparison.json` `config_source` points at the worktree file |
| `apply.HARNESS_MANAGED_LOCK_SIDECARS` | Plan-05 comparison allowlist | import | ✓ WIRED | `worktree.changed-paths.json` `expected_lock_sidecars` = the three sidecars; `matches: true` |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
| --- | --- | --- | --- | --- |
| `evidence/discover/inventory.json` | `candidate_process_boundaries` | live `git ls-files` walk of the real worktree at `919d152a` | Yes — 5 real paths with real sha256/size | ✓ FLOWING |
| `evidence/downstream/package-facts.json` | package/edge list | real target manifests | Yes — 6 packages, 4 real edges | ✓ FLOWING |
| `evidence/downstream/conventions.json` | per-package profile | worktree `harness/project.toml` after the splice | Yes — non-null lint/test per package | ✓ FLOWING |
| `evidence/apply/worktree.changed-paths.json` | `changed_paths` | real post-apply worktree status | Yes — 156 real paths, `unexpected_paths: []` | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Suite does not depend on the real target existing (D-17) | `ls -d …/FeedbackOps-worktrees/v27-52-adoption` then `uv run pytest -q` | worktree **absent**; `1023 passed, 8 snapshots passed in 14.27s` | ✓ PASS |
| Contract-first: hash baseline matches live schemas | `uv run python -m tools.contract_drift.drift` | `contract-drift: OK — live manifest matches the committed baseline.` exit `0` | ✓ PASS |
| NG-01 contract count | `find contracts -name '*.schema.json' \| wc -l` | `6` (inventory, manifest, plan, relationship, format-conventions, greeting) | ✓ PASS |
| NG-01 command/skill count | `ls harness/commands \| wc -l`; `ls harness/skills \| wc -l` | `19`, `8` | ✓ PASS |
| NG-01 CI jobs / gates unchanged | `git diff --stat 7a19fb9..HEAD -- .github/ harness/` | **empty** — no CI or harness-surface change in the entire phase | ✓ PASS |
| Worktree actually disposed | `git -C …/FeedbackOps worktree list` | only `/Users/hyojung/Desktop/2026/FeedbackOps  919d152 [develop]` | ✓ PASS |
| Original checkout byte-unchanged (live, independent) | `git rev-parse HEAD` + `git ls-files -s \| shasum -a 256` | `919d152a…` / `60f1e620…` — identical to recorded before **and** after digests | ✓ PASS |

### Scope-Fence Verification

| Fence | Check | Result |
| --- | --- | --- |
| OBS-03 refuted → `_dependencies_from_package_json` byte-unchanged | extracted the function body at `7a19fb9` and at `HEAD` and compared | **IDENTICAL** (955 bytes both) |
| No repair outside OBS-D-01/-03/-04 | `git diff --numstat` on `detect.py` | 93 insertions, **0 deletions** — nothing existing was rewritten |
| D-21: no write to target `.gitignore` | scan `changed_paths` for `gitignore` | **NONE** |
| D-15: sidecars never unlinked | `grep unlink tools/adoption_apply/apply.py` | only the two pre-existing temp-file `os.unlink` calls in the atomic-publish helpers; no sidecar unlink |
| D-09: no non-pnpm workspace formats | `_MANIFEST_KIND_BY_NAME` / new code | no npm/yarn `workspaces`, Cargo, or uv workspace handling added |

### Requirements Coverage

| Requirement | Source plan(s) | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| RTA-01 | 52-05, 52-06 | Developer can run `/adopt` against the isolated FeedbackOps worktree, original checkout unchanged | ✓ SATISFIED | SC-1 evidence + live independent re-confirmation |
| RTA-02 | 52-01, 52-02, 52-05 | discover enumerates the five real pnpm workspace members | ✓ SATISFIED | SC-2 evidence + mutation B |
| RTA-03 | 52-04, 52-06 | package facts produce the real inter-package dependency edges | ✓ SATISFIED | SC-3 evidence + OBS-D-02 lock-in test |
| RTA-04 | 52-03, 52-06 | each package resolves a nearest-wins convention profile with lint/test | ✓ SATISFIED | SC-4 evidence + mutations C |
| OBS-02 | 52-02, 52-03, 52-04, 52-06 | purpose ①②③④ observed defects are repaired or evidence-backed-confirmed | ✓ SATISFIED | OBS-D trace ledger, all 7 node ids executed PASS |
| NG-01 (Phase-54-owned, enforced here as a hard constraint) | — | no growth in commands/skills/contracts/CI jobs/gates | ✓ SATISFIED | 19 / 8 / 6; `.github/` and `harness/` diffs empty |

**Orphaned requirements:** none. All five phase-assigned IDs (RTA-01..04, OBS-02) are claimed by at
least one plan's frontmatter, and no additional ID is mapped to Phase 52 in `REQUIREMENTS.md`
(NG-01 maps to Phase 54).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| all phase-changed `tools/**/*.py` and `contracts/**` | — | `TBD` / `FIXME` / `XXX` debt markers | — | **NONE FOUND** — the debt-marker gate passes clean |
| `.planning/ROADMAP.md` | 287 | Phase-52 plan-listing title reads *"report a **stale** one on stderr"* | ℹ️ Info | The implemented behavior is deliberately provenance-only, never staleness (D-15/D-16, W-3). The stale wording survives only in the pre-execution ROADMAP plan title; the emitted message, every test name, `apply.py`'s comments, and `52-ADOPTION-EVIDENCE.md` §W-3 all say "prior run" and explicitly disclaim staleness. Verified by grep: the word "stale" appears nowhere in `apply.py`'s new code, in any Phase-52 test name, or in the phase record's claim sentences. Not a gap; noted so a Phase-53 reader of the ROADMAP title does not infer a working staleness signal. |

### Recorded Deviations — Disclosure Check

All five flagged deviations were verified as **disclosed, not concealed**. Disclosure is not treated
as a defect.

| # | Deviation | Disclosed where | Verdict |
| --- | --- | --- | --- |
| 1 | 52-01 constitution-plane write applied as a format-preserving text edit, not the applier's `json.dump` round-trip | `52-01-SUMMARY.md` key-decisions + §Deviations (lines 32, 104–123), incl. the latent-defect note for future appliers | ✓ Disclosed. Canonical digest is `688b75206df6…` either way — confirmed by `drift` exiting 0 against the committed baseline. The 4-line diff is what a CODEOWNERS reviewer actually sees. Correct call. |
| 2 | 52-02 replaced two structurally unreachable negative controls | `52-02-SUMMARY.md` key-decisions line 38 + §Deviations lines 95–105 | ✓ Disclosed, and the replacements are real: mutation D confirms the segment-count-matched traversal case goes RED when the guard is removed. |
| 3 | 52-04 widened a pre-existing assertion to a bitmask check | `52-04-SUMMARY.md`; inline comment at `test_atomic_apply.py:406-408` | ✓ Disclosed **and adjudicated** — mutation A proves the widened assertion still rejects `LOCK_SH`; blocking-ness is covered by a separate concurrency test. No weakening. |
| 4 | Spliced `harness/project.toml` will classify `conflict` on a Phase-53 re-run | `52-03-SUMMARY.md`, quoted verbatim in `52-ADOPTION-EVIDENCE.md` §Scope-fence (W-10) | ✓ Disclosed with an explicit instruction to Phase 53 to treat it as expected. |
| 5 | D-16 report means provenance, not staleness | `52-04-SUMMARY.md`, `apply.py:339-341` comment, `52-ADOPTION-EVIDENCE.md` §W-3 | ✓ Disclosed. Grep confirms no code message, test name, or record sentence claims staleness. Only residual is the ROADMAP plan title above (Info). |

### The `build_facts` six-vs-five Complication — Honesty Check

This was the specific place the record could have manufactured a false five-way agreement. It did
not. `evidence/downstream/member-comparison.json` records `build_facts_count: 6`,
`six_packages_one_non_member: true`, names `docs/design-prototype` as the extra, and carries an
explicit `note` stating that `discover_manifests` (`package_facts.py:93-114`) is an **unscoped**
path, that Phase 52 deliberately adds no scoping there (D-07), that six is the expected behavior of
an unscoped path, and that **SC-2 is decided by the inventory, not by this file**.
`52-ADOPTION-EVIDENCE.md` §W-5 repeats this verbatim. Verified independently: the six IDs appear in
`package-facts.json`, and `convention-comparison.json`'s six rows include the `docs/design-prototype`
UUID-named package. Correct, honest reporting.

### Human Verification Required

None. Every deciding value was re-derived by the verifier from a literal artifact, a live command,
or an independent read of the real target repository. No `<verify><human-check>` blocks were
deferred by any Phase-52 plan.

### Gaps Summary

No gaps. All five ROADMAP success criteria are satisfied by artifacts the verifier read directly
rather than by SUMMARY prose. The three highest-risk claims were attacked specifically and all
survived:

1. **SC-5's ledger** — every cited pytest node id exists and passes when run by the verifier, and
   four mutation experiments confirm the tests fail when the behavior they guard is removed. The
   ledger is not a paper trail.
2. **The widened bitmask assertion (deviation #3)** — mutation A proves it still rejects a shared
   lock; the property it stopped proving is covered elsewhere.
3. **The six-vs-five complication** — the record reports six honestly and names the correct
   deciding artifact rather than manufacturing agreement.

Hard constraints all hold: the contract count is exactly 6, commands 19 and skills 8, `.github/` and
`harness/` are byte-unchanged across the whole phase, `_dependencies_from_package_json` is
byte-identical (OBS-03 stays refuted and unrepaired), no `.gitignore` write, no sidecar unlink, and
the full suite passes (1023) on a machine where the target worktree no longer exists — satisfying
D-17 by construction rather than by assertion.

The one item worth carrying forward is informational, not a gap: `ROADMAP.md:287`'s plan title still
says "stale", which the implementation deliberately does not provide. Phase 53 should read
`52-ADOPTION-EVIDENCE.md` §W-3, not the ROADMAP title.

---

_Verified: 2026-08-01_
_Verifier: gsd-verifier (goal-backward, FORCE stance)_

---

## Post-verification addendum (orchestrator, 2026-08-01)

This report was produced BEFORE the code-review fix pass (`9fa201d`, `56508c2`, `1481655`).
Recorded so the ordering is not left implicit:

- **CR-01 was an environment artifact, not a source defect.** A stale `tools/adoption_apply/__pycache__/apply.cpython-311.pyc` recorded mtime AND size identical to its source, so CPython trusted it. Root cause: this verification pass's own mutation experiment swapped `LOCK_EX` -> `LOCK_SH` (both exactly 7 characters, so size was preserved) and reverted within the same mtime second, defeating cache invalidation. Purging `__pycache__` took `tools/adoption_apply/tests` from `3 failed, 90 passed` to `93 passed`. No source change was made or needed.
- **CR-02 / CR-03 were real defects in this phase's own new code** and were fixed with regression tests observed RED. Neither invalidates the SC evidence captured in 52-05/52-06: CR-02 only changes behavior for pnpm manifest shapes the real target does not have (flow-style `packages: [...]`, settings-only, empty body — FeedbackOps uses the list form), and CR-03 only affects a derived `[[languages]]` row's shape for targets declaring no `test` script.
- **Suite after fixes: 1047 passed** (was 1023 at verification time). Contract count 6, drift gate exit 0, adoption snapshots unmoved.

The 5/5 verdict above stands.
