---
phase: 48-convention-profiles
fixed_at: 2026-07-30T01:02:30Z
review_path: .planning/phases/48-convention-profiles/48-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 6
skipped: 0
status: all_fixed
---

# Phase 48: Code Review Fix Report

**Fixed at:** 2026-07-30T01:02:30Z
**Source review:** .planning/phases/48-convention-profiles/48-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 6 (1 critical, 3 warning, 2 info — `fix_scope: all`)
- Fixed: 6
- Skipped: 0

## Fixed Issues

### CR-01: `_nearest_agents_md()` walks and crashes above the repo root

**Files modified:** `tools/harness_config/loader.py`, `tools/harness_config/tests/test_conventions_for.py`
**Commit:** `792d8b7`
**Applied fix:** `_nearest_agents_md()` now validates that `(_REPO_ROOT / dir_).resolve()` is
actually inside `_REPO_ROOT` (via `candidate.relative_to(_REPO_ROOT)`) BEFORE walking `.parents`,
raising a scoped `ValueError` naming the offending `dir_` when it escapes (relative traversal or
absolute path) instead of climbing to the filesystem root and crashing partway through with an
opaque `ValueError`. Non-existent-but-in-repo and empty-string `dir_` still resolve without error.
`conventions_for()` (the public entry point) propagates the same scoped `ValueError` sanely for a
malformed config `dir`.

Regression tests added: `test_nearest_agents_md_rejects_relative_traversal_escaping_repo_root`,
`test_nearest_agents_md_rejects_absolute_path_escaping_repo_root`,
`test_nearest_agents_md_tolerates_nonexistent_in_repo_dir`,
`test_nearest_agents_md_tolerates_empty_string_as_repo_root`,
`test_conventions_for_propagates_out_of_root_dir_as_scoped_value_error`.

Fails-before / passes-after evidence: ran a standalone pre-fix probe against the unmodified
function — both the `"../../etc"` and `"/etc"` cases silently returned `None` (no raise) rather
than the required `ValueError`. After the fix, both raise
`_nearest_agents_md: dir_='...' resolves outside the repo root (...) — refusing to walk above
_REPO_ROOT`. All 5 new tests pass; full `tools/harness_config/` suite (49 tests) green.

### WR-01: `package_facts.render()` resolves conventions from the pre-merge `dir`

**Files modified:** `tools/memory_regen/package_facts.py`, `tools/memory_regen/tests/test_package_facts.py`, `tools/memory_regen/tests/__snapshots__/test_package_facts.ambr`, `.memory/derived/package-facts.md`
**Commit:** `3184cca`
**Applied fix:** `render()`'s Convention Profiles loop now iterates `effective_packages(cfg,
facts)` (the merged/effective record set) instead of the raw `facts["packages"]` list, and skips
records with no `"dir"` key (declared-only `[[components]]` entries), mirroring
`conventions_for()`'s own adapter filter. This means a `[[components]]` override that relocates a
package's `dir` is now correctly reflected in that package's rendered profile row.

Regression tests added: `test_render_convention_profile_uses_effective_dir_not_pre_merge_dir`,
`test_render_skips_declared_only_component_with_no_dir`.

Fails-before / passes-after evidence: constructed a fixture with a `widget` package whose
`[[components]]` entry relocates `dir` to `widget/relocated`. Pre-fix: the rendered row
incorrectly resolved to `package=root, dir=., default=true` (falling back to the root package,
since the pre-merge `dir="widget"` doesn't even enclose `widget/relocated`). Post-fix: the row
correctly resolves to `package=widget, dir=widget/relocated, default=false`. Both new tests pass;
the committed snapshot and the real `.memory/derived/package-facts.md` artifact were regenerated
(row order in the Convention Profiles section changed from manifest-sorted to id-sorted — matching
`effective_packages()`'s own sort key; no data content change) and a second regeneration was
confirmed byte-identical (`sha256` match). Full `tools/memory_regen/` suite (99 tests, after `uv
sync --all-packages --all-extras` to restore the worktree's tree-sitter/networkx dev deps) green.

### WR-02: The `"dir"`-key filter cannot distinguish "declared-only" from "malformed"

**Files modified:** `tools/harness_config/loader.py`, `tools/harness_config/tests/test_conventions_for.py`
**Commit:** `7047776`
**Applied fix:** `conventions_for()` now scans `effective_packages()`'s output before filtering
and prints a scoped stderr diagnostic (naming the offending package id) for any record that has a
`"manifest"` key (i.e. came from `build_facts()` or a component overriding one) but is missing
`"dir"` — the signature of a malformed record rather than a legitimate declared-only component
(which has neither `"manifest"` nor `"dir"`). The record is still excluded from ownership
resolution afterward (unchanged behavior for the real cases in the repo); only the diagnostic is
new.

Regression tests added: `test_malformed_component_missing_dir_but_has_manifest_is_reported_on_stderr`,
`test_legitimate_declared_only_component_produces_no_stderr_warning`.

Fails-before / passes-after evidence: pre-fix, `capsys.readouterr().err` was empty for the
malformed-record fixture (no diagnostic at all). Post-fix, stderr contains both `"malformed"` and
`"no 'dir'"`. Verified via `git stash` isolating the source change: with the loader.py edit
stashed, the malformed-record test failed (`AssertionError: assert 'malformed' in ''`) while the
legitimate-declared-only test still passed — confirming the fix (not the test) drives the new
behavior. Both live configs (core + example instance) still load with zero edits and zero
diagnostic noise for their real declared-only components.

### WR-03: `test_command_count_is_stable` has no linkage to the actual command-name set

**Files modified:** `tools/harness_lint/tests/test_commands.py`
**Commit:** `102a1de`
**Applied fix:** Added `EXPECTED_COMMAND_NAMES` (the full 18-name frozenset) and a new
`test_command_names_are_stable` test asserting the observed `{p.stem for p in _command_files()}`
equals it exactly, reporting added/removed names on mismatch. `test_command_count_is_stable` is
left in place unchanged (still a useful cheap first-line signal); the new test is the strengthened
gate.

Fails-before / passes-after evidence: simulated a same-count rename swap in a scratch copy of the
worktree (`mv harness/commands/verify-work.md harness/commands/renamed-command.md`, a
non-golden-adjacent name). Ran the three relevant tests: `test_command_count_is_stable` and
`test_golden_adjacent_commands_present` both PASSED silently (exactly the gap the finding
describes), while the new `test_command_names_are_stable` FAILED with
`command name set drifted: added=['renamed-command'], removed=['verify-work']`. Reverted the
simulation; the real (unmodified) command set passes all three tests. Full
`tools/harness_lint/tests/test_commands.py` suite (76 tests) green.

### IN-01: Synthetic fixtures are not fully hermetic for `agents_md`

**Files modified:** `tools/memory_regen/tests/test_package_facts.py`
**Commit:** `99ea349`
**Applied fix:** Chose the documented, low-risk option over making `_nearest_agents_md`
injectable (which would touch the CR-01-hardened production function's signature). Added
`test_render_value_none_branch_renders_none_literal`, a direct unit test proving
`_render_value(None) == "(none)"` (the branch no synthetic fixture exercises coincidentally,
since the walk always falls through to the real root `AGENTS.md`), plus a module-docstring note
explicitly flagging that `agents_md` values in the synthetic fixtures are coincidental real-tree
artifacts, not asserted synthetic behavior.

### IN-02: `effective_packages()`'s declared-only-component contract isn't directly exercised

**Files modified:** `tools/harness_config/tests/test_conventions_for.py`
**Commit:** `99ea349`
**Applied fix:** Added `test_declared_only_component_alongside_derived_package_resolves_to_derived_owner`
— a fixture combining one derived package (`root`, `dir="."`) and one declared-only
`[[components]]` entry (`declared-only`, no `dir`) — asserting `conventions_for()` resolves
ownership to the derived package without raising, making the "Pitfall 1" docstring claim
falsifiable rather than asserted-by-comment only.

## Skipped Issues

None — all six in-scope findings were fixed.

## Verification Summary

- Full suite: `uv run pytest -q` — 935 passed (run inside the isolated fix worktree after
  `uv sync --all-packages --all-extras` restored dev-only extras missing from the fresh worktree
  venv; no test skipped or xfailed).
- `uv run python -m tools.harness_emit` — 71 artifacts re-emitted, tree clean afterward (no diff).
- `git diff --stat` against the pre-fix commit for `.github/workflows/ci.yml` and `.gitignore` —
  empty (zero diff, per constraints).
- Command count: 18 -> 18 (no new command; `EXPECTED_COMMAND_NAMES` pins the same 18 names).
- GEN-04 gate (`tools/harness_lint/tests/test_core_no_example_dep.py`) — 18 passed; no literal
  `examples/` path introduced under `tools/`, `harness/`, `libs/`.
- `.memory/derived/package-facts.md` — regenerated once (WR-01's fix legitimately changed
  Convention Profiles row order to id-sorted, matching `effective_packages()`); confirmed a
  second regeneration is byte-identical (`sha256` match).
- `tools/contract_graph/ownership.py` — untouched (verified: no diff against pre-fix commit).

---

_Fixed: 2026-07-30T01:02:30Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
