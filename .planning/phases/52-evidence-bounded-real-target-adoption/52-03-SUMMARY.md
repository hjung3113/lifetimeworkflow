---
phase: 52-evidence-bounded-real-target-adoption
plan: 03
subsystem: infra
tags: [python, toml, pnpm, harness-config, adoption-apply, nearest-wins]

# Dependency graph
requires:
  - phase: 52-01
    provides: "contracts/harness/adoption/inventory.schema.json non-workspace-member enum (unrelated to this plan's scope; wave-1 dependency only)"
provides:
  - "conventions_for() returns a permanent `lint` key (None when unconfigured, a real value when configured) for every resolved package"
  - "derive_language_rows(): pure, filesystem-free derivation of a [[languages]] TOML row from a target's own package.json scripts"
  - "tools.adoption_apply.cli draft-time languages.toml sidecar write + apply-time splice into the harness/project.toml payload — the one sanctioned CR-01 exception (D-12)"
  - "Repo-local end-to-end proof: a synthetic pnpm target resolves non-null lint/test through the real draft->apply->conventions_for path"
affects: [52-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Draft-time derivation + batch-local sidecar + apply-time splice: the one sanctioned, narrowly-scoped exception to the CR-01 'harness bytes only' invariant, guarded on an exact literal destination string rather than a prefix/glob."
    - "Mutation-then-revert-in-place verification: apply a scratch mutation directly in the working tree, run the target test, observe red, restore via saved backup — used three times in this plan (Task 1's lint-value guard, Task 2's key-set guard, Task 3's splice-guard widening x2)."

key-files:
  created: []
  modified:
    - tools/harness_config/loader.py
    - tools/harness_config/tests/test_conventions_for.py
    - tools/adoption_apply/cli.py
    - tools/adoption_apply/tests/conftest.py
    - tools/adoption_apply/tests/test_cli.py

key-decisions:
  - "The rendered [[languages]] sidecar emits ALL FIVE keys (id/bash_scope/lint/test/format) unconditionally, with empty string for an undeclared script, because conventions_for() reads test/format/bash_scope by subscript against a matched row — a partially-shaped row would KeyError downstream (Pitfall 3, per <interfaces>)."
  - "Script VALUES are never read into the derived row or executed — only the fixed literal 'pnpm run <key>' keyed by allowlisted script NAMES (lint/test/format) is emitted (T-52-07)."
  - "The splice guard is the exact literal destination string 'harness/project.toml', not a prefix or glob — verified by two independent scratch mutations (widen to all `create` payloads; widen to also touch block_bodies) that each reds a different half of the leak-detection test."

requirements-completed: [RTA-04, OBS-02]

# Metrics
duration: ~50min active work (single continuous session, no checkpoints)
completed: 2026-08-01
---

# Phase 52 Plan 03: Evidence-Bounded Real-Target Adoption — Convention-Profile `lint` Key + Target-Derived JS Commands Summary

**`conventions_for()` now returns a permanent `lint` key, and an adopted pnpm target's JavaScript lint/test commands are derived from that target's own `package.json` scripts at draft time and spliced into the applied `harness/project.toml` — proven end to end by a repo-local synthetic-target test, with the Phase-53 re-run consequence recorded rather than left to be rediscovered.**

## Performance

- **Tasks:** 3/3 completed
- **Files modified:** 5 (0 created, 5 modified)

## Accomplishments

- `conventions_for()` (`tools/harness_config/loader.py:297`) returns exactly 9 keys for every resolved package now, including `lint` — read via `lang.get("lint")` (never a subscript, since this repo's own `dotnet`/`python` rows declare no `lint` key). All 13 pre-existing tests stay green as written; 4 new tests cover the full key-set shape, the `.get()`-safety, a live-config value read, and the no-matching-row all-`None` case.
- `derive_language_rows()` (`tools/adoption_apply/cli.py`) is a pure, filesystem-free function: given a target's `package.json` text, it renders one `[[languages]]` TOML table (`id="javascript"`, `bash_scope="pnpm *"`, `lint`/`test`/`format`) sourced from the target's OWN declared `scripts` object — never a harness-side hardcoded default. Only script NAMES are read (allowlisted to `lint`/`test`/`format`); script VALUES never flow into the row or get executed.
- `_cmd_draft` writes the derived row to `batch_root/languages.toml` (through the same `refuse_if_outside_root` confinement the three draft artifacts already use) only when the target declares itself a pnpm workspace (`pnpm-workspace.yaml` + root `package.json`); writes nothing otherwise.
- `_cmd_apply` appends that sidecar to the `"harness/project.toml"` payload ONLY — guarded on the exact literal destination string — after the payload-assembly loop. Every other destination, including all three `MARKER_CAPABLE` marker-merge destinations, stays the harness's own checkout bytes verbatim.
- A repo-local end-to-end test drives the real CLI (`draft` then `apply`) against a synthetic `tmp_pnpm_target` fixture, then resolves the profile through the TARGET's OWN `harness/project.toml` and `build_facts(repo_root=target)` — never this repo's config — and asserts `profile["lint"] == "pnpm run lint"` and `profile["test"] == "pnpm run test"`. This is the repo-local SC-4 proof; it needs no external repository.
- The W-10 Phase-53 consequence is recorded (see below), not silently absorbed.
- No contract impact: `contracts/` and `harness/project.toml` (this repo's own copy) are both untouched; `uv run python -m tools.contract_drift.drift` exits 0 throughout.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add the permanent `lint` key to conventions_for()** - `07e1e2f` (feat)
2. **Task 2: Derive a [[languages]] row from the target's package.json scripts at draft time** - `bdaa48a` (feat)
3. **Task 3: Splice the derived row into the applied harness/project.toml and prove the profile resolves end to end** - `e7e7178` (feat)

## Files Created/Modified

- `tools/harness_config/loader.py` - `conventions_for()` gains the permanent `"lint": lang.get("lint") if lang else None` key, docstring updated
- `tools/harness_config/tests/test_conventions_for.py` - 4 new tests: full key-set shape (matched + unmatched language), `.get()`-safety against a lint-less row, live-config value read, no-matching-row all-`None`
- `tools/adoption_apply/cli.py` - `derive_language_rows()` + 4 module constants; draft-time sidecar write in `_cmd_draft`; apply-time splice in `_cmd_apply`
- `tools/adoption_apply/tests/conftest.py` - new `tmp_pnpm_target` fixture (root + `apps/widget-app` + `packages/widget-shared`, `pnpm-workspace.yaml`, root `package.json` with `lint`/`test` scripts; neutral vocabulary, GEN-04)
- `tools/adoption_apply/tests/test_cli.py` - 12 new tests across Tasks 2/3: `derive_language_rows()` unit tests (shape, exact key set, no value-leakage, malformed/no-scripts/non-object inputs), draft-time sidecar-write vs. no-write, end-to-end profile resolution, no-sidecar byte-identity, and the splice leak-detection pair

## Decisions Made

1. **All five `[[languages]]` row keys are emitted unconditionally** (empty string for an undeclared script) rather than only the keys the target happens to declare — required because `conventions_for()` reads `test`/`format`/`bash_scope` by subscript against a matched row; a partially-shaped row would `KeyError` downstream the first time a JS package with only a `lint` script (no `test`) resolved its profile.
2. **Script values are read-never-executed, keyed by an allowlist of exactly three names** (`lint`/`test`/`format`) — the derived command is always the fixed literal `"pnpm run <key>"`, never a copy of the target's own script string, closing T-52-07 (hostile-scripts tampering).
3. **The splice guard is an exact literal destination-string check**, not a prefix/glob — proven load-bearing by two independent scratch mutations (see Mutation Evidence below), each of which reds a different one of the two leak-detection assertions.

## Mutation Evidence (checks-that-cannot-fail guard)

This repo's signature defect is a check that cannot fail. Three mutations were applied directly in the working tree (via a saved `.py` backup), the target test was observed red, then the file was restored byte-for-byte from the backup and the full suite re-confirmed green before committing.

**1. Task 1 — hardcoding `"lint": None` in `conventions_for()`'s return dict** (guards
`test_lint_value_is_read_from_the_matched_language_row_not_hardcoded`):
```
>       assert profile["lint"] == "ruff check"
E       AssertionError: assert None == 'ruff check'
tools/harness_config/tests/test_conventions_for.py:252: AssertionError
```

**2. Task 2 — dropping `"format"` from `_DERIVED_SCRIPT_KEYS`** (guards
`test_derive_language_rows_emits_exact_key_set`):
```
>       assert set(row.keys()) == {"id", "bash_scope", "test", "format", "lint"}
E       AssertionError: assert {'bash_scope'...lint', 'test'} == {'bash_scope'...lint', 'test'}
E         Extra items in the right set:
E         'format'
tools/adoption_apply/tests/test_cli.py:460: AssertionError
```

**3a. Task 3 — widening the splice guard from the literal `"harness/project.toml"` to every `create`-disposition payload** (reds the byte-equality half of `test_splice_never_touches_any_other_destination`):
```
>           assert applied_path.read_bytes() == cli_module._harness_payload(destination), destination
E           AssertionError: .github/CODEOWNERS
E           assert b'# CODEOWNER...format = ""\n' == b'# CODEOWNER... @hjung3113\n'
tools/adoption_apply/tests/test_cli.py:674: AssertionError
```

**3b. Task 3 — widening the splice to also touch `block_bodies["AGENTS.md"]`** (reds the marker-merge literal-absence half of the SAME test, independent of 3a):
```
>               assert literal not in content, f"{marker_destination} leaked {literal!r}"
E               AssertionError: AGENTS.md leaked 'pnpm run lint'
tools/adoption_apply/tests/test_cli.py:687: AssertionError
```

Each mutation was reverted from the saved backup, and `git diff --stat` confirmed the working tree returned to exactly the intended Task-N edit before the commit.

## W-10 — Recorded Phase-53 Consequence (mandatory, no code change)

**The splice is intentional (D-12), and it means a Phase-53 managed re-run will classify `harness/project.toml` as `conflict`, not as the observable no-op Phase 53's SC-2 assumes.** After `apply`, the target's `harness/project.toml` bytes = harness checkout bytes + the derived `languages.toml` sidecar, so its digest is no longer among `destinations.harness_proposed_hashes()`'s entries — verified directly in `test_end_to_end_pnpm_target_resolves_lint_and_test_through_real_config` (`applied_digest != proposed.get("harness/project.toml")`). MONO-12 re-run/update semantics own the resolution of that "one destination looks like a conflict even though it's an intentional install" case; this is a recorded consequence of a locked decision (D-12), not a Phase-52 defect. 52-06 Task 3 carries the same statement into the phase record's scope-fence section.

## Deviations from Plan

None - plan executed exactly as written. All `<behavior>` bullets across the three tasks have a corresponding test; all `<acceptance_criteria>` mutation-observation requirements were satisfied with quoted red output (above); no architectural changes were needed; the `<parallel_execution_note>`'s cross-plan fences passed trivially throughout since 52-04 had not yet started in this serialized (non-worktree) execution.

## Issues Encountered

- The initial `sidecar_literals` set for the leak-detection test included the bare string `"[[languages]]"`, which false-positived against `CLAUDE.md`'s own unrelated prose (a sentence mentioning `[[languages]]` tables in passing). Narrowed to distinctive, sidecar-specific literals (`"pnpm run lint"`, `'bash_scope = "pnpm *"'`, the provenance comment) — not a plan deviation, just a test-authoring correction made before the task's first commit.
- `test_cli_draft_against_non_pnpm_target_writes_no_languages_sidecar`'s original exact-set assertion missed `status.json` (written by `create_or_resume_batch` alongside the three draft artifacts) — corrected to a `<=` containment check plus an explicit `"languages.toml" not in names` assertion before the task's first commit.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 52-06 (phase record) can cite this plan's W-10 statement verbatim in its scope-fence section.
- The remaining wave-2 sibling, 52-04, has not yet run in this serialized (non-worktree) execution; its files (`tools/adoption_apply/apply.py`, `tools/adoption_apply/tests/test_atomic_apply.py`, `tools/memory_regen/**`) were confirmed untouched by this plan's own commits (post-commit range-fence re-run: empty output).
- Full suite green: `uv run pytest -q` → 997 passed, 8 snapshots passed.

---
*Phase: 52-evidence-bounded-real-target-adoption*
*Completed: 2026-08-01*

## Self-Check: PASSED

All claimed files exist (this summary) and all four claimed commit hashes (`07e1e2f`, `bdaa48a`,
`e7e7178`, `4683595`) are present in `git log --oneline --all`.
