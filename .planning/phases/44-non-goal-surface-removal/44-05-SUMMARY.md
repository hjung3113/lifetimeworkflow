---
phase: 44-non-goal-surface-removal
plan: 05
wave: 5
subsystem: golden-stack / commit-gate
tags: [CER-09, relocation, uv-workspace, ci, gen-04, ruff-ratchet]
requires: ["44-04"]
provides:
  - "golden stack resolving under examples/log-parser/ (runner, suite, case tree)"
  - "core plane free of golden/parity .NET resolution and of any golden_runner import"
  - "commit_gate composing two components (drift, polyglot)"
affects:
  - "tools/hooks/commit_gate.py"
  - "examples/log-parser/golden_runner/"
  - ".github/workflows/ci.yml"
  - "harness/commands/verify-work.md"
tech-stack:
  added: []
  patterns:
    - "instance root as a third sys.path entry in both conftests (existing sys.path.insert idiom)"
    - "ruamel round-trip with indent+preserve_quotes+width pinned before dump"
key-files:
  created: []
  modified:
    - "tools/hooks/commit_gate.py"
    - "tools/hooks/tests/test_commit_gate.py"
    - "examples/log-parser/golden_runner/ (relocated from tools/golden_runner/)"
    - "examples/log-parser/golden/sample/ (folded from root golden/sample/)"
    - "pyproject.toml, uv.lock"
    - ".github/workflows/ci.yml"
    - "harness/commands/verify-work.md, harness/skills/python-conventions/SKILL.md"
    - "tools/adoption_scan/tests/test_install_completeness.py"
    - "tools/harness_lint/tests/test_tests_are_isolatable.py"
decisions: [D-01, D-02, D-03, D-04, D-05, D-14, D-15, D-16, D-17, D-18, D-19]
metrics:
  commits: 2
  duration: single session
  completed: 2026-07-29
---

# Phase 44 Plan 05: Golden Stack Relocation Summary

The golden runner, its suite and the root `golden/` case tree now live under
`examples/log-parser/`; `commit_gate` lost the golden-parity component that made the core plane
depend on them. 31 example tests pass (14 + 17), the core suite is 880 green.

## Commits

| Hash | Message | `git diff --shortstat` |
|---|---|---|
| `fc69d10` | `refactor(44-05): delete commit_gate's golden-parity component` | 2 files changed, 18 insertions(+), 95 deletions(-) |
| `df4675c` | `refactor(44-05)!: relocate the golden stack into the instance overlay` | 29 files changed, 66 insertions(+), 147 deletions(-) |

Per-file breakdown of `fc69d10`: `commit_gate.py` 62 ±, `test_commit_gate.py` 51 ±.

## Measured Numbers

| Quantity | Value | Plan expectation |
|---|---|---|
| `uv.lock` diff | 1 insertion, 1 deletion | 1 line — matched |
| `examples/log-parser/tests` | 14 passed | 14 — matched |
| `examples/log-parser/golden_runner` | 17 passed | 17 — matched |
| Combined `examples/` leg | **31 passed** | 31 — matched |
| Core `uv run pytest -q` | 880 passed, 7 snapshots | — |
| `tools.ruff_baseline` | `ruff ratchet: 73 findings (baseline 84)` → `PASS — and findings went DOWN` | "measured 77"; observed **73** (see Deviations) |
| Resolved `gate.needs` | 10 | 10 — matched |
| `ci.yml` numstat | `4 4 .github/workflows/ci.yml` | single-digit each side — matched (plan measured 5/5) |
| `I001` regression from the import rewrite | 3, in `test_approve_gate` / `test_sample_loop` / `test_workspace_golden` | 3, those exact three files — matched |
| `F401` orphan from `check_golden` removal | 1 (`tempfile`), removed in `fc69d10` | matched |

## What Was Done

### Task 1 — `commit_gate`'s golden-parity component (`fc69d10`)

Removed the module-level import, `discover_golden_cases()`, `check_golden()`, the third element of
the composition list, and the orphaned `import tempfile`. `run_composition()` now composes
`check_drift()` and `check_polyglot()`.

Every self-describing line was corrected, including the two the plan flagged:

- the `APPROVAL_ENV` scope clause (was `…never weakens polyglot (§4.3-4.6) or golden
  (equivalence)`), now naming only the surviving polyglot component;
- `staged_files()`'s degradation claim (was `degrades to drift+golden rather than crashing`), which
  became **factually false** once the component was gone — now `degrades to the drift component
  alone`.

One further stale line the plan's surface table did not list was found and fixed:
`test_commit_gate.py:159`, a section comment reading `while polyglot/golden stay HARD`.

`GOLDEN_APPROVE_HUMAN` and its four ratification tests are untouched and green. The scoped
identifier grep (`golden-parity|golden_runner|check_golden|discover_golden_cases|GOLDEN_DIR|run_golden_case`)
returns nothing; all six surviving case-insensitive `golden` hits in `commit_gate.py` are
`GOLDEN_APPROVE_HUMAN` references.

The plan's "all 15 tests are coupled" is confirmed and the mechanism is precise: the `_dotnet_absent`
helper did `monkeypatch.setattr(commit_gate, "resolve_dotnet", …)`, which raises `AttributeError`
once the name no longer exists on the module. Deleting the helper and its 15 call sites (two of them
inside the two deleted tests) was the whole repair. The file went 21 tests → 19.

### Task 2 — the relocation (`df4675c`)

The chained single invocation (`git mv` → `members` edit via inline `python3` → `uv lock
--upgrade-package logparser-golden-runner` → `uv sync --all-packages`) ran clean end-to-end, exit 0,
`uv.lock | 2 +-`. No intermediate state where uv could not resolve.

All four path anchors corrected: `runner.py` `REPO_ROOT` `parents[2] → parents[3]` (the T-06-02
confinement root), `runner.py` `GOLDEN_DIR` → `Path(__file__).resolve().parents[1] / "golden"` with
an inline comment explaining the deliberate decoupling from `REPO_ROOT`, and both
`parents[3] → parents[4]` in `golden_runner/tests/conftest.py` and `test_workspace_golden.py`. Every
`parents[` in the moved tree was re-derived by hand and the depths asserted directly.

11 imports rewritten; instance root added as a third `sys.path` entry in both conftests. Also
repointed the stale module-path prose in the instance plane: `runner.py`'s CLI docstring,
`runner.py`'s `golden_dir` docstring (which named `REPO_ROOT/golden`, now `:data:GOLDEN_DIR`), and
the two `pyproject.toml` comments.

CI: both jobs repointed, the `:155` comment line rewritten, the step name changed to
`Golden — runner identity (converter-agnostic)`. Both golden steps now point into the instance
(D-05); the job and its `setup-dotnet` step stay, so `gate.needs` is still 10.

`verify-work.md`: golden section deleted, `description` golden clause dropped, "five gates" → "four
gates", "All five" → "All four", section 5 renumbered to 4. Line numbers had indeed shifted from the
plan's citation and were re-derived before editing.

Floor lowered 12 → 11 with a GEN-04-safe rationale ("relocated out of the core tree into the
instance overlay"); the isolatability docstring's `pytest tools/golden_runner` citation removed.
`test_core_no_example_dep.py` passes — the forbidden path token was never written into a core-plane
file.

## Deviations from Plan

**1. [Rule 3 — Blocking] `ruamel.yaml` line-wraps long scalars at the default `width`; `yaml.width` had to be set.**

- **Found during:** Task 2 step 9.
- **Issue:** With exactly the mandated `yaml.indent(mapping=2, sequence=4, offset=2)` and
  `yaml.preserve_quotes = True`, the first dump produced **19 insertions / 9 deletions**, not the
  measured 5/5. The de-indentation the plan warned about was correctly suppressed, but ruamel's
  default `width` (80) re-folded four pre-existing long scalars in unrelated jobs — the `setup`
  job's `Sync workspace` step name and the `drift` job's example-manifest `run:` string — across
  multiple lines. 19 is not single-digit, so the plan's own stop condition tripped.
- **Fix:** Applied the plan's prescribed remedy verbatim — `git checkout -- .github/workflows/ci.yml`
  (explicit single path), then redid the edit with `yaml.width = 4096` added to the same
  configuration block. Result: **4 insertions / 4 deletions**, touching only the three intended
  strings and the one comment line.
- **Why this is a completion, not a change of approach:** the plan's instruction is "configure the
  round-trip indentation before dumping" with the stated goal of a single-digit diff; `width` is the
  third knob of the same round-trip configuration and was simply not enumerated. No criterion was
  relaxed — the delivered diff is *smaller* than the plan's own measurement.
- **Files modified:** `.github/workflows/ci.yml`. **Commit:** `df4675c`.

**2. Observed ruff total is 73, not the plan's "measured 77".**

Not a deviation in behavior — the ratchet exits 0, no rule class is above baseline, and the only
tracked class (`E501`) reads `baseline 84 -> found 73`. 73 was already the count at the wave-4
handoff (the brief states `73 findings (baseline 84)`), so this wave neither raised nor lowered it;
the plan's 77 appears to be a mid-replay reading. Per instruction, no `--update` was run.

**3. `test_dispositions.py::test_catalog_invariant_to_untracked_local_state` is red pre-commit, green post-commit.**

Expected and not a defect. The test builds a detached worktree at `HEAD` and compares its
destination catalog against the live tree; with the relocation staged but uncommitted, `HEAD` still
carries `golden/README.md` and `tools/golden_runner/*` so the two catalogs necessarily differ. It
passes immediately after `df4675c`. Recorded because it makes any *pre-commit* full-suite run of a
move-shaped commit look red by construction — a future executor should not chase it.

## Things the Plan Did Not Anticipate

**1. A stale test *name* survives the floor edit.** `test_install_completeness.py`'s floor assertion
lives in a function named `test_discovers_at_least_twelve_modules`, which now asserts `>= 11`. The
plan enumerated the assertion, the interpolated message and the docstring, but not the function
name. It was left as-is rather than renamed, because renaming was outside the plan's stated scope
and the plan's instruction was to follow it literally. **This is the same stale-self-description
defect class the milestone was convened to remove** and should be picked up by plan 06 or Phase 45
(CER-11) — the rename is mechanical and has no callers.

**2. The `:155` CI comment needed rewording, not just repointing.** It read `step 1 — root identity
golden (converter-agnostic, .NET-free) via pytest tools/golden_runner`. Since D-05 collapses both
golden steps into the instance, the path clause was dropped rather than repointed: `step 1 — the
golden runner's own suite (converter-agnostic, .NET-free)`. This keeps the comment true without
duplicating a path that the `run:` line below it already carries.

## Consequence to Record (Task 2 step 7) — isolatability-gate coverage loss

`tools/harness_lint/tests/test_tests_are_isolatable.py::_members_needing_wiring()` globs
`tools/*/tests`. The relocated package no longer matches that glob, so **the golden runner's suite
has permanently dropped out of the isolatability gate**. Nothing is broken today: the relocated
suite runs standalone green (`uv run pytest examples/log-parser/golden_runner` → **17 passed**),
because its own `tests/conftest.py` inserts the repo root, the instance root and `libs/python` onto
`sys.path` before any import. The property the gate checks still holds; only the automated proof of
it is gone.

**Not repaired here by design** — widening the glob to cover the instance overlay would be surface
growth against SC-8, and it would put an instance path into a core-plane gate, which is exactly what
GEN-04 forbids. Plan 06 should record this as a consequence of CER-09 rather than as an open defect.

## Threat Mitigations Applied

| Threat | Disposition | Evidence |
|---|---|---|
| T-44-13 (`REPO_ROOT` narrowing the confinement allowlist) | mitigated | `parents[3]`; asserted `REPO_ROOT == repo root` |
| T-44-24 (`GOLDEN_DIR` resolving to the deleted directory) | mitigated | instance-anchored `parents[1]`; asserted; 31 passed |
| T-44-14 (declared-but-absent workspace member disarming every guard) | mitigated | move-then-declare ordering in one invocation; never entered the bad state |
| T-44-25 (`I001` 0→3, `F401` 0→1 reddening the ratchet) | mitigated | both cleaned inside their own commits; ratchet 0 |
| T-44-26 (GEN-04 tripping on rationale prose) | mitigated | token-free phrasing; `test_core_no_example_dep.py` green |
| T-44-16 / T-44-28 (stale claimed controls) | mitigated | `verify-work.md` golden block deleted + 4 self-refs corrected; `commit_gate.py:52,81` corrected |
| T-44-29 (whole-file `ci.yml` rewrite) | mitigated | 4/4 diff; numstat cap asserted |
| T-44-15 (folded goldens move `deny` → `allow` under `contract_guard`) | **accepted** | merge-time CODEOWNERS `/examples/*/golden/` holds; in-session gate lost, as recorded |

## Residual

.NET SDK 10 is absent locally. The `require_dotnet` golden cases **SKIP** cleanly and the converter
spawn path is exercised **only** in CI's `golden` job. Local verification of `df4675c` does not prove
the spawn path. Stated rather than claimed away.

## Deliberately Out of Scope (Phase 45 / CER-11)

The ~17 remaining prose/path spellings of `tools/golden_runner` — `AGENTS.md:66-67` (deferred by this
plan's own Q3 finding), `README.md:119`, `tools/docs_sync/generate.py:14`,
`tools/hooks/contract_guard.py:56`, `tools/hooks/format_on_write.py:36`, two `conftest.py:3`
docstrings and 5 `pyproject.toml` comments. The absence gate was kept scoped to the import form, as
the plan directs. `AGENTS.md` was not touched outside the emitter-managed markers.

## Self-Check: PASSED

- `examples/log-parser/golden_runner/pyproject.toml` — FOUND (contains `logparser-golden-runner`)
- `examples/log-parser/golden/sample/` — FOUND
- `tools/golden_runner` — absent (verified)
- root `golden/` — absent (verified)
- `pyproject.toml` `members` contains `examples/log-parser/golden_runner` — verified
- Commit `fc69d10` — FOUND
- Commit `df4675c` — FOUND
- `git status --porcelain` empty after both commits — verified
</content>
</invoke>
