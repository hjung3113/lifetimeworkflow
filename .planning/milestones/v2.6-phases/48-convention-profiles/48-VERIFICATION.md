---
phase: 48-convention-profiles
verified: 2026-07-30T00:00:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
---

# Phase 48: Convention Profiles Verification Report

**Phase Goal:** An agent working anywhere in the tree can ask "which conventions apply here?" and
get the nearest-wins answer — the enclosing package's profile, not the repo-wide default — without
any profile restating a lint or test command the language config already owns.
**Verified:** 2026-07-30
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth (Roadmap SC) | Status | Evidence |
|---|-------|--------|----------|
| 1 | Nearest-wins: path inside a package → that package's profile; path with no enclosing package → explicitly-marked repo-wide default; demonstrated on a nested case where the inner answer differs from the enclosing one | ✓ VERIFIED | `conventions_for()` at `tools/harness_config/loader.py:279-320` joins `effective_packages()` + `owning_package()` (unmodified, `git diff --stat -- tools/contract_graph/ownership.py` empty). Real nested pair `libs/python` (inner) vs root (outer) resolve to different `package`/`dir`/`agents_md` (`libs/python/AGENTS.md` vs `AGENTS.md`), verified live: `.memory/derived/package-facts.md:49-50` shows `logparser-normalize` → `libs/python/AGENTS.md`, `default=false` vs `logparser-harness` → `AGENTS.md`, `default=true`. Because both are `python`, `test`/`format` are correctly identical on the real pair (not a false negative) — a supplementary synthetic two-language fixture (`test_synthetic_two_language_nested_pair_commands_differ`) independently proves the commands-differ case. Both real-tree and synthetic tests pass (`uv run pytest tools/harness_config/tests/test_conventions_for.py -q` → 5 passed). |
| 2 | A profile never restates a lint/test command literal — commands come from `[[languages]]`, editing the language config changes every affected profile with no profile edited | ✓ VERIFIED | `conventions_for()` looks up `test`/`format`/`bash_scope` live from `languages(cfg)` (loader.py:309-317) — no literal stored anywhere. `test_editing_language_command_changes_every_affected_profile_with_no_profile_edit` holds `facts` constant and varies only `cfg["languages"][0]["test"]` between `"OLD"`/`"NEW"`, asserting both a root and nested profile change accordingly with zero profile-authoring code touched. **Mutation-verified** (documented in 48-01-SUMMARY.md): flipping the final assertion to expect `"OLD"` under `cfg_v2` produced a real `AssertionError: 'NEW' == 'OLD'` — the test is not a "check that cannot fail." `package_facts.render()` (`tools/memory_regen/package_facts.py:258-320`) sources every rendered command cell via a live call to `conventions_for()`, never a literal — extended `test_real_tree_render_structure` independently proves the derived artifact reflects this (in-memory only, per GEN-04). |
| 3 | `/component` step 2 produces a convention profile for the new package, inside the existing structure → AGENTS.md → tests order, no step 4 | ✓ VERIFIED | `harness/commands/component.md` diff against base commit shows only step 2's bullet and the Guard section extended (regenerate `package-facts.md` + assert `conventions_for()` resolution) — step 1 and step 3 text untouched, still exactly 3 numbered steps (`grep -c "^[0-9]\." component.md` → 3, `grep -ci "step 4"` → 0). Both projections re-emitted byte-clean: `uv run python -m tools.harness_emit` run live during verification produced a clean `git status --short .opencode .claude` (idempotent, zero further diff) — the emitted `.opencode/command/component.md` / `.claude/commands/component.md` carry the identical step-2 text (differences are only the pre-existing emitter frontmatter transform, not content drift). |
| 4 | Command count unchanged (18), no gate/CI job added | ✓ VERIFIED | `ls harness/commands/*.md \| wc -l` → 18 (live, re-measured). `test_command_count_is_stable()` (`tools/harness_lint/tests/test_commands.py:63-70`) asserts `len(_command_files()) == 18` using the file's pre-existing glob helper (not a second glob) — this is a deliberate pin, not a circular/self-referential test; mutation-proved in 48-03-SUMMARY.md (throwaway 19th file → real `assert 19 == 18` failure, then reverted). `git diff 4e5c1ff..HEAD -- .github/workflows/ci.yml .gitignore` is empty (re-verified live, 0 lines). |

**Score:** 4/4 truths verified (all four Roadmap Success Criteria + MONO-05/06/07)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tools/harness_config/loader.py` | `conventions_for()` + `_nearest_agents_md()` | ✓ VERIFIED | Present at lines 257 and 279; substantive (41-line docstring + join logic), wired (imported by `package_facts.py` and exercised by 5 tests + real-tree checks). |
| `tools/harness_config/__init__.py` | `conventions_for` exported via PEP 562 | ✓ VERIFIED | `"conventions_for"` present in `__all__`, alphabetically placed; `__getattr__` dispatch unmodified (generic, no per-symbol branch needed). |
| `tools/harness_config/tests/test_conventions_for.py` | 5 tests proving nearest-wins/default + falsifiable command-inheritance | ✓ VERIFIED | 5 test functions present, all pass (`uv run pytest tools/harness_config/tests/test_conventions_for.py -q` → 5 passed), no monkeypatch/temp-file/`examples/` literals (grep confirms 0 hits for both). |
| `tools/memory_regen/package_facts.py` | `render()` extended with `## Convention Profiles`, sourced via `conventions_for()` | ✓ VERIFIED | Section present once (`grep -c "## Convention Profiles"` → 1 in both source and rendered artifact); `cfg: dict \| None = None` additive param confirmed; pre-existing determinism/backward-compat tests pass unmodified. |
| `.memory/derived/package-facts.md` | Committed artifact carries the new section | ✓ VERIFIED | Section present with 23 package rows; byte-identical on delete + regenerate (sha256 `0dc0a5a0...` matched live, both before and after regeneration in this verification session). |
| `harness/commands/component.md` | Step 2 extended with profile-regen directive | ✓ VERIFIED | Confirmed via diff against base commit — additive only, order preserved. |
| `.opencode/command/component.md`, `.claude/commands/component.md` | Re-emitted projections | ✓ VERIFIED | Live re-emit during verification produced zero diff (already in sync, idempotent). |
| `tools/harness_lint/tests/test_commands.py` | `test_command_count_is_stable` pinning 18 | ✓ VERIFIED | Present, passes, mutation-documented as falsifiable. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `conventions_for()` | `owning_package()` (`tools/contract_graph/ownership.py`) | module-level import, direct call, no reimplementation | ✓ WIRED | `grep -n "from tools.contract_graph import owning_package" tools/harness_config/loader.py` → exactly 1 line; `ownership.py` byte-unchanged since base commit. |
| `conventions_for()` | `[[languages]]` (`harness/project.toml`) | `languages(cfg)` lookup by `owner["language"]` | ✓ WIRED | Confirmed at loader.py:309; verified live via the mutation-tested falsifiable unit test. |
| `package_facts.render()` | `conventions_for()` | lazy in-function import, one call per package | ✓ WIRED | `render()` calls `conventions_for(pkg["dir"], cfg=cfg, facts=facts)` per package row (package_facts.py:308); the derived artifact's Convention Profiles table reflects the live join. |
| `harness/commands/component.md` (source) | `.opencode/`/`.claude/` projections | `tools.harness_emit` re-emit | ✓ WIRED | Live re-emit run produces zero diff — projections already reflect the source edit; idempotency confirmed. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| MONO-05 | 48-01, 48-02 | Nearest-wins convention lookup | ✓ SATISFIED | `conventions_for()` + derived-artifact rendering, both verified above. |
| MONO-06 | 48-01, 48-02 | Commands derived, never restated | ✓ SATISFIED | Falsifiable mutation-proven test + live-read render path. |
| MONO-07 | 48-03 | `/component` step 2 populates profile, no new command | ✓ SATISFIED | Step 2 extension + 18-count regression test, both verified. |

No orphaned requirements — REQUIREMENTS.md maps only MONO-05/06/07 to Phase 48, all three claimed across the three plans.

### Anti-Patterns Found

None. Scanned all files modified by this phase (`loader.py`, `__init__.py`, `test_conventions_for.py`, `package_facts.py`, `test_package_facts.py`, `component.md`, `test_commands.py`) for `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER`/empty-return stubs. Two incidental hits on the word "placeholder" in unrelated pre-existing prose (`package_facts.py:97` docstring note, `component.md:33` describing a Python test-scaffold convention predating this phase) — neither is a debt marker introduced by this phase, neither flows to a stubbed implementation.

### Special Scrutiny — Checks That Cannot Fail

Sampled and mutation-verified per this repo's signature-defect pattern:
- `test_editing_language_command_changes_every_affected_profile_with_no_profile_edit` — mutation-checked in 48-01-SUMMARY.md, confirmed to fail when the expected value is wrong.
- `test_real_tree_render_structure`'s new nested-wins assertions — mutation-checked in 48-02-SUMMARY.md (comparing a row against itself made the assertion trivially true; comparing the two distinct rows is what actually proves nesting — the correct form was kept).
- `test_command_count_is_stable` — mutation-checked in 48-03-SUMMARY.md via a real throwaway 19th command file, confirmed `assert 19 == 18` failure.
- The real-tree nested pair test (`test_real_nested_pair_libs_python_vs_root_differ_on_package_and_agents_md`) correctly asserts `inner["test"] == outer["test"]` (equality, not difference) because both packages share the `python` language row — this was verified NOT to be a tautology: the test also asserts `inner["dir"] != outer["dir"]`, `inner["agents_md"] != outer["agents_md"]`, and `inner["package"] != outer["package"]`, which would fail if resolution were broken (e.g. both collapsing to the default). The commands-differ case is independently covered by a separate synthetic test, so no coverage gap exists.
- `test_command_count_is_stable` pins a hardcoded literal (`== 18`) rather than recomputing dynamically — reviewed and judged NOT circular: it reuses the file's existing `_command_files()` glob (not a second glob) but compares against a manually-set constant, which is the correct pattern for a growth-pinning regression (a self-computing count could never fail on legitimate growth without deliberate maintainer action).

No tautological, self-comparing, or existence-only assertions found among the phase's new/edited assertions.

### Human Verification Required

None. All four success criteria are mechanically verifiable and were verified against live command execution in this session (test suite, re-emit, hash comparison, diff against base commit) — not merely against SUMMARY.md claims.

### Gaps Summary

None. All four ROADMAP.md Success Criteria (SC1–SC4) and all three requirements (MONO-05, MONO-06,
MONO-07) are verified against the actual codebase, independent of SUMMARY.md narrative: `conventions_for()` implements nearest-wins reusing `owning_package()` unmodified; commands are proven live-derived via a mutation-tested falsifiable test; `/component` step 2 is extended additively with no step 4; the command count is pinned at 18 with a mutation-proven regression test; `ci.yml`/`.gitignore` are byte-unchanged (re-verified live); `.memory/derived/package-facts.md` regenerates byte-identically; GEN-04's core-no-example-dependency test passes (18 passed); the full repository suite (923 tests) passes green.

---

_Verified: 2026-07-30_
_Verifier: Claude (gsd-verifier)_
