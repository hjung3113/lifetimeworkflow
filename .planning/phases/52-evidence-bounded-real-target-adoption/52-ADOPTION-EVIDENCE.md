# Phase 52 adoption evidence

## Reproducibility

Harness (as recorded before the real-target run, `evidence/metadata/harness.sha.txt`)
`93e92bed4d34fdfddaccf27dc8bde5408da13c65`; target `develop` HEAD re-read at run time (D-02,
`evidence/metadata/target.develop.sha.txt`) `919d152a56ed096c0fdef12b9bfb892d6ef4ced6` — the third
distinct SHA this milestone has cited (Phase 51 baseline `1d1c8ed`, the mid-milestone discussion
record `4f16525`, this run `919d152a`), all third-party movement on the target's own `develop`,
never a Phase-52 write. Target worktree
`/Users/hyojung/Desktop/2026/FeedbackOps-worktrees/v27-52-adoption` (disposed at the end of this
plan — see §Disposal result); original checkout `/Users/hyojung/Desktop/2026/FeedbackOps`
(read-only, `develop`); harness cwd `/Users/hyojung/Desktop/2026/lifetimeworkflow`. Live tool
versions are in `evidence/metadata/tool-versions.json`. Literal argv/cwd/stdout/stderr/exit
captures sit beside every JSON artifact under `evidence/`. Nonzero or blocked outcomes are
evidence, not something to retry into a different shape.

## Isolation and external drift

`evidence/isolation/comparison.json`: `status_equal: true`, `head_equal: true`, `index_equal:
true`, `untracked_set_equal: true` — the original checkout's `before.head.txt` and
`disposal/final.head.txt` are both literally `919d152a56ed096c0fdef12b9bfb892d6ef4ced6`, and
`before.index.sha256`/`after.index.sha256` are both literally
`60f1e62025b36cbfea5a8e0fbc6a48de19c5c67a457a891d9270d9340532e726`. Unlike Phase 51, `develop`
did not move during this plan's own window, so **no `external-drift.json` was needed** — the
conditional in the plan's `<action>` ("if `head_equal` or `index_equal` is false, attribute it")
did not trigger, and its absence is the correct outcome, not an omission. The residual honestly
disclosed: the untracked-set equality compares two empty-string SHA-256 digests
(`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`) both before and after, so it
has low discriminating power — the same caveat Phase 51 recorded.

## Success-criterion verdicts

| SC | Statement | Deciding artifact | Deciding value |
| --- | --- | --- | --- |
| SC-1 | A developer can complete `/adopt` discover → draft → apply against the isolated FeedbackOps worktree while the original `develop` checkout remains byte-unchanged. | `evidence/apply/exit-code.txt` (52-05); `evidence/isolation/comparison.json` (this plan) | Apply exit `0` (`applied=154 skipped=86 refused=23`, `52-05-SUMMARY.md`); `head_equal: true`, `index_equal: true`, `status_equal: true`, `untracked_set_equal: true` |
| SC-2 | The adoption inventory contains all five real workspace members: root, `packages/ui`, `packages/shared`, `apps/frontend`, `apps/backend`. | `evidence/discover/member-comparison.json` | `"members_equal_expected_five": true`, `"candidate_process_boundaries": [".", "apps/backend", "apps/frontend", "packages/shared", "packages/ui"]` |
| SC-3 | Generated package facts contain the real `packages/shared` dependency edges to both `apps/frontend` and `apps/backend`. | `evidence/downstream/workspace-edge-comparison.json` | `"both_runtime_edges_present": true`, `"edges": [{"from": "@fops/frontend", "to": "@fops/shared", "kind": "runtime"}, {"from": "@fops/backend", "to": "@fops/shared", "kind": "runtime"}]` |
| SC-4 | Each adopted package resolves a nearest-wins convention profile containing its lint and test commands. | `evidence/downstream/convention-comparison.json` | `"all_js_packages_have_lint_and_test": true` — every row's `lint` is the literal string `"pnpm run lint"` and `test` is `"pnpm run test"` (verbatim per-package values in the same file) |
| SC-5 | Every change made in this phase traces to a Phase 51 observation within purpose ①②③④ and has a regression test; observations requiring no change remain evidence-backed confirmations. | §OBS-D trace ledger, below | All four of OBS-D-01, OBS-D-02, OBS-D-03, OBS-D-04 terminate in a named, executed, passing pytest node id (§below) |

## OBS-D trace ledger (SC-5, D-19)

Every observation below terminates in either a repair-plus-regression-test or a written
evidence-backed confirmation. Each cited node id was executed directly
(`uv run pytest -q <node id>`) before being recorded here — all seven passed.

| OBS-D id | Purpose tag | Disposition | Code change(s) | Terminating test(s) | Real-target evidence |
| --- | --- | --- | --- | --- | --- |
| OBS-D-01 | ② PROPOSAL ONLY (non-workspace-member manifest enumerated) | repaired | `tools/adoption_scan/detect.py` (`parse_pnpm_workspace_globs`, `is_workspace_member`); `tools/adoption_scan/scan.py` (`build_inventory` scoping) — 52-02 | `tools/adoption_scan/tests/test_scan_exclusions.py::test_pnpm_non_member_manifest_excluded_and_absent_from_included_and_manifests` (PASS); `tools/adoption_scan/tests/test_scan_exclusions.py::test_pnpm_workspace_exactly_five_members` (PASS) | `evidence/discover/inventory.json` + `evidence/discover/member-comparison.json`: `docs/design-prototype/package.json` recorded `"excluded": "non-workspace-member"`, five real members enumerated |
| OBS-D-02 | ② PROPOSAL ONLY (`workspace:*` edge resolution) | no-change-evidence-backed (lock-in test, D-18) | none — `tools/adoption_scan/detect.py:273` confirmed correct and left untouched; only a lock-in test added (52-04) | `tools/memory_regen/tests/test_package_facts.py::test_workspace_star_dependency_edges_resolve_by_name` (PASS) | `evidence/downstream/workspace-edge-comparison.json`: both `@fops/frontend → @fops/shared` and `@fops/backend → @fops/shared` runtime edges present on the real target |
| OBS-D-03 | ① PROPOSAL ONLY (convention profile shape + JS commands) | repaired | `tools/harness_config/loader.py` (`conventions_for()` permanent `lint` key) — 52-03; `tools/adoption_apply/cli.py` (`derive_language_rows()`, draft-time sidecar, apply-time splice) — 52-03 | `tools/harness_config/tests/test_conventions_for.py::test_lint_value_is_read_from_the_matched_language_row_not_hardcoded` (PASS); `tools/adoption_apply/tests/test_cli.py::test_end_to_end_pnpm_target_resolves_lint_and_test_through_real_config` (PASS) | `evidence/downstream/conventions.json` + `convention-comparison.json`: every real-target JS package's profile has a non-null `lint` (`"pnpm run lint"`) and `test` (`"pnpm run test"`), read from `<WORKTREE>/harness/project.toml` |
| OBS-D-04 | ④ PROPOSAL ONLY (apply leaves unlisted lock sidecars) | repaired | `tools/adoption_apply/apply.py` (`lock_sidecar_for()`, `expected_lock_sidecars()`, `HARNESS_MANAGED_LOCK_SIDECARS`, non-blocking-first flock + conditional stderr report) — 52-04 | `tools/adoption_apply/tests/test_atomic_apply.py::test_expected_lock_sidecars_matches_filesystem_after_every_marker_merge` (PASS); `tools/adoption_apply/tests/test_atomic_apply.py::test_prior_run_lock_sidecar_is_reported_on_stderr` (PASS) | `evidence/apply/worktree.changed-paths.json` (52-05): `matches: true`; `.AGENTS.md.lock`, `.CLAUDE.md.lock`, `.claude/.settings.json.lock` land in `expected_lock_sidecars` and are absent from `unexpected_paths` |

**OBS-03 (refuted, restated for completeness — no Phase-52 budget spent).** Phase 51 refuted the
hypothesis that pnpm `workspace:*` dependency strings break resolution
(`51-BASELINE-EVIDENCE.md` §OBS-03 verdict, `"result": "refuted"`). `tools/adoption_scan/detect.py:273`
discards version strings and matches by package name, which is *why* the hypothesis was refuted;
Phase 52 repaired nothing there, and OBS-D-02's lock-in test above exists precisely so that
refutation cannot silently regress. Zero Phase-52 budget was spent "fixing" `workspace:*`
resolution.

## Scope-fence statement

Deliberately NOT done in this phase: no write to the target's `.gitignore` (D-21 — no safe merge
primitive exists against an existing target `.gitignore` today); no unlinking of any `.lock`
sidecar (D-15); no non-pnpm workspace format support (npm/yarn `workspaces`, Cargo, uv — D-09);
no new contract, command, skill, CI job, or gate (NG-01) — the contract count is still exactly
**6** (`find contracts -name '*.schema.json' | wc -l` → `6`), and the harness's emitted
command/skill counts (19 commands, 8 skills per `AGENTS.md`'s Harness-Emitted Runtime Surface
block) did not grow; the Phase-51 `sk-proj-…`/`sk-ant-api03-…` secret-scan gap remains
recorded-only and untouched.

This section also carries three consequences a Phase-53 re-run would otherwise rediscover as
defects, rather than as known, recorded outcomes of locked Phase-52 decisions:

- **`harness/project.toml` re-run classification (W-10).** Per `52-03-SUMMARY.md`, quoted
  verbatim: *"The splice is intentional (D-12), and it means a Phase-53 managed re-run will
  classify `harness/project.toml` as `conflict`, not as the observable no-op Phase 53's SC-2
  assumes. After `apply`, the target's `harness/project.toml` bytes = harness checkout bytes +
  the derived `languages.toml` sidecar, so its digest is no longer among
  `destinations.harness_proposed_hashes()`'s entries ... MONO-12 re-run/update semantics own the
  resolution of that 'one destination looks like a conflict even though it's an intentional
  install' case; this is a recorded consequence of a locked decision (D-12), not a Phase-52
  defect."* Phase 53 must treat this ONE destination's `conflict` classification as expected,
  not as a regression to chase.

- **The prior-run lock-sidecar report is provenance, not staleness (W-3).** Because D-15 forbids
  unlinking the sidecar, `_apply_marker_merge`'s `pre_existed` predicate is true on every run
  after the first and therefore cannot distinguish a normal re-run from a crash-interrupted one
  (`52-04-SUMMARY.md`: *"the prior-run report cannot distinguish a normal re-run from a
  crash-interrupted one, and this is a deliberate scope boundary (NG-01), not an oversight"*).
  Phase 53 inherits this as a known, documented gap — it must never be treated as a working
  staleness signal.

- **`build_facts` is unscoped (W-5).** `tools.memory_regen.package_facts.discover_manifests`
  (`package_facts.py:93-114`) enumerates via `git ls-files` + `detect.detect_manifests` with no
  workspace-glob scoping. On the real target it reports **six** packages —
  `evidence/downstream/package-facts.json` names all six, and
  `evidence/downstream/member-comparison.json` records `"six_packages_one_non_member": true`,
  with `docs/design-prototype` as the expected extra. Workspace scoping lives only in
  `scan.build_inventory` (D-07); extending it into `discover_manifests` was out of scope for
  Phase 52 and remains unbuilt. SC-2's deciding artifact is the inventory
  (`evidence/discover/member-comparison.json`), not this path; SC-3's two required runtime edges
  are unaffected by the extra package's presence.

**Model-identifier guard, confirmed firing (B-2).** A scratch line naming a well-known LLM vendor
and model-family term was appended to a copy of this file and piped through the mandated
strip-then-match check (the plan's `<verify>` block: strip mandated artifact-name substrings
first, then case-insensitive-match the remainder against a small set of model-vendor/model-family
terms). The check fired against the scratch line (a match was found, non-zero grep exit as the
guard's own `&& exit 1` branch expects), the scratch line was then removed, and the check against
the real, unmodified file passed clean (no match) — confirming the guard both catches a genuine
identifier and does not false-positive on this file's own required `.CLAUDE.md.lock` /
`.claude/.settings.json.lock` / `.claude/settings.json` mentions.

## Disposal result

`git -C /Users/hyojung/Desktop/2026/FeedbackOps worktree remove --force
/Users/hyojung/Desktop/2026/FeedbackOps-worktrees/v27-52-adoption` (`evidence/disposal/argv.txt`)
exited `0` (`evidence/disposal/exit-code.txt`), with empty stdout/stderr. The final worktree list
(`evidence/disposal/final.worktree-list.txt`) contains only the original checkout:
`/Users/hyojung/Desktop/2026/FeedbackOps  919d152 [develop]`. Post-disposal comparison
(`evidence/isolation/comparison.json`'s `post_disposal` block) shows all four booleans true —
`status_equal`, `head_equal`, `index_equal`, `untracked_set_equal` — the original checkout is
unmodified both immediately after the run and after disposal.
