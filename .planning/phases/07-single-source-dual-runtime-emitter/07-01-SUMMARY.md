---
phase: 07-single-source-dual-runtime-emitter
plan: 01
subsystem: infra
tags: [emitter, codegen, opencode, claude-code, drift-gate, determinism, uv-workspace, syrupy]

# Dependency graph
requires:
  - phase: 03-agents-commands-skills
    provides: dual-representation harness/agents/*.md source + tools.harness_lint.parse_frontmatter + agent/skill cap gates
  - phase: 06-ci-gates
    provides: contract_drift re-emit/compare archetype + config-derived CI fan-in gate
provides:
  - "tools/harness_emit — the single-source dual-runtime emit spine (agent projector + loud-fail validator + ownership manifest)"
  - "tools/harness_lint/caps.py — extracted shared cap constants + is_read_only (single source of truth for lints AND emitter)"
  - "committed .opencode/agent/** + .claude/agents/** harness agent slice (machine-written, CI-verified)"
  - "emit-drift CI job wired into the non-bypassable gate.needs fan-in"
affects: [commands emit, skills emit, plugins verbatim-copy, opencode.json config emit, AGENTS.md/CLAUDE.md/settings.json managed-block merge]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Emit spine cloned from tools/docs_sync determinism discipline (fixed ordered frontmatter, LF/no-BOM, no timestamps, byte-identical delete+regenerate)"
    - "Loud-fail validate-then-write: run cap/shape gate on source AND both projections before any write; raise HarnessEmitError writing nothing (never truncate)"
    - "Ownership manifest prune-then-write with gsd-* / GSD-lane exclusion (D-03 coexistence)"
    - "Re-emit-diff drift gate (git diff --exit-code) extending the contract_drift CI archetype"

key-files:
  created:
    - tools/harness_emit/generate.py
    - tools/harness_emit/project_agent.py
    - tools/harness_emit/validate.py
    - tools/harness_emit/manifest.py
    - tools/harness_lint/caps.py
    - tools/harness_emit/emit-manifest.json
  modified:
    - tools/harness_lint/tests/test_agents.py
    - tools/harness_lint/tests/test_skills.py
    - .github/workflows/ci.yml

key-decisions:
  - "DERIVED marker emitted as a YAML comment on line 2 (inside the fence), not the file's first line, so agent frontmatter still loads (first line stays ---)"
  - "READ_ONLY_PERSONAS extracted into caps.py so the emitter can enforce the read-only invariant without duplicating the persona set"
  - "Emitted artifacts + emit-manifest.json are tracked (committed), machine-written CI-verified derivatives — not a two-plane violation (D-02)"

patterns-established:
  - "Fully-parameterized emit(harness_dir, opencode_dir, claude_dir, manifest_path, root) so tests drive isolated tmp source+target trees"
  - "Function-local import of HarnessEmitError in validate/manifest breaks the generate<->validate cycle"

requirements-completed: [EMIT-01, EMIT-02]

# Metrics
duration: 24min
completed: 2026-07-12
---

# Phase 7 Plan 01: Agent-First Emit Walking Skeleton Summary

**The 4 harness agents now compile from one runtime-neutral `harness/agents/` source into byte-faithful `.opencode/agent/**` + `.claude/agents/**` trees through the full pipeline — frontmatter projection, loud-fail validators, ownership manifest, committed output, and a non-bypassable `emit-drift` CI gate.**

## Performance

- **Duration:** ~24 min
- **Started:** 2026-07-12T07:20:12Z
- **Completed:** 2026-07-12T07:44:00Z
- **Tasks:** 3
- **Files modified:** 20 (13 created + 4 emitted agents + 3 modified)

## Accomplishments
- Extracted the agent/skill cap constants + `is_read_only` into `tools/harness_lint/caps.py` as a single source of truth shared by the structural lints AND the new emit-time validators; existing 186-test lint suite stayed green with values unchanged.
- Built `tools/harness_emit/` (virtual uv member) with the docs_sync determinism spine: `_confine` traversal guard, fixed-ordered deterministic frontmatter serializer (LF/no-BOM, `permission.bash` kept in authored last-wins order), agent projector (`to_opencode` keeps mode+permission, `to_claude` keeps tools), loud-fail validator, and prune-then-write ownership manifest.
- Committed the emitted agent slice; a second `python -m tools.harness_emit` reproduces every file byte-for-byte (drift gate clean).
- Added the `emit-drift` CI job (re-emit + `git diff --exit-code` over the full documented path set) and wired it into `gate.needs`.

## Task Commits

Each task was committed atomically (TDD RED → GREEN → gate):

1. **Task 1: Wave-0 infra + extract caps + failing tests (RED)** - `97695bc` (test)
2. **Task 2: Emit spine + projector + validator + manifest (GREEN)** - `eb5436a` (feat)
3. **Task 3: Validator/manifest tests + emit-drift CI + committed surface** - `8c872be` (feat)

**Plan metadata:** see final `docs(07-01)` commit.

## Files Created/Modified
- `tools/harness_emit/generate.py` - Emit spine: REPO_ROOT anchor, HarnessEmitError, verbatim `_confine`, deterministic frontmatter serializer, `iter_agents`, `emit()`, `main()`.
- `tools/harness_emit/project_agent.py` - `to_opencode` / `to_claude` frontmatter projections (D-04 sole divergence point).
- `tools/harness_emit/validate.py` - Loud-fail cap/shape gate importing `tools.harness_lint.caps`.
- `tools/harness_emit/manifest.py` - Prune-then-write ownership manifest with gsd-* exclusion.
- `tools/harness_lint/caps.py` - Extracted shared cap constants + `is_read_only`.
- `tools/harness_emit/{__init__,__main__,pyproject}.py|.toml` + `tests/{conftest,test_mapping,test_emit_determinism,test_validators,test_manifest}.py` + committed `__snapshots__/test_emit_determinism.ambr`.
- `.opencode/agent/{orchestrator,python-engineer,code-reviewer,explorer}.md` + `.claude/agents/{same}.md` - emitted harness slice.
- `tools/harness_emit/emit-manifest.json` - committed ownership manifest.
- `.github/workflows/ci.yml` - `emit-drift` job + `gate.needs` entry.
- `tools/harness_lint/tests/{test_agents,test_skills}.py` - re-pointed to import caps from `caps.py`.

## Decisions Made
- **DERIVED marker placement:** emitted as a YAML comment on the second line (inside the `---` fence) rather than the file's first line, because an agent file's first line MUST be `---` for the runtime frontmatter parsers (and `parse_frontmatter`) to load it. A leading HTML comment would break loadability. This is a reasoned adaptation of the docs_sync "first-line marker" pattern for frontmatter-bearing files.
- **READ_ONLY_PERSONAS extracted to caps.py:** needed so the emitter's validator can enforce that a read-only persona (code-reviewer/explorer) stays read-only in the source AND both projections without re-declaring the persona set. Re-imported by `test_agents.py` with the value unchanged.
- **Cycle break:** `validate.py`/`manifest.py` import `HarnessEmitError` via a function-local import so `generate.py` can import them at module top without a circular import (keeps ruff E402 happy).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] DERIVED marker moved off the first line for frontmatter loadability**
- **Found during:** Task 2 (render_agent implementation)
- **Issue:** The plan/docs_sync pattern places the DERIVED "do not hand-edit" HTML comment as the file's FIRST line. For agent `.md` files this breaks frontmatter detection — `parse_frontmatter` (and the opencode/Claude loaders) require the first line to be `---`, so a leading comment yields an empty frontmatter and an unloadable agent.
- **Fix:** Emit the marker as a YAML comment (`# generated by tools.harness_emit — do not hand-edit`) on line 2, immediately inside the opening fence. First line stays `---`; the marker is still at the top of every generated file and is machine-checkable.
- **Files modified:** tools/harness_emit/generate.py
- **Verification:** `parse_frontmatter` round-trips the emitted files; opencode/Claude shape assertions pass; determinism snapshot committed.
- **Committed in:** `eb5436a` (Task 2 commit)

**2. [Rule 3 - Blocking] READ_ONLY_PERSONAS added to caps extraction**
- **Found during:** Task 2 (validate.py)
- **Issue:** The plan's extraction list omitted `READ_ONLY_PERSONAS`, but the emit-time read-only-invariant check needs it to know which personas must stay read-only.
- **Fix:** Added `READ_ONLY_PERSONAS` to `caps.py` (value unchanged) and re-imported it in `test_agents.py`.
- **Files modified:** tools/harness_lint/caps.py, tools/harness_lint/tests/test_agents.py
- **Verification:** lint suite green (186 passed); read-only mutation test raises HarnessEmitError.
- **Committed in:** `97695bc` / `eb5436a`

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking). Also removed a transient `__snapshots__/.gitkeep` (committed in Task 1 to make the empty dir trackable) once the real `.ambr` landed in Task 3 — intentional, documented.
**Impact on plan:** Both auto-fixes necessary for correctness. No scope creep — Wave-1 stayed agents-only (D-05).

## Issues Encountered
- PyYAML is absent from the workspace (repo standardizes on ruamel); the plan's `import yaml` verify snippet was run via `ruamel.yaml` instead. Result identical: `emit-drift` present in `jobs` and in `gate.needs`.
- Pre-existing E501 long lines in `test_agents.py`/`test_skills.py` docstrings are out of scope (present before this plan) and were left untouched; all newly-authored code is ruff-clean.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- The emit spine is established: later waves (commands → skills → plugins → opencode.json → managed-block merges) only ADD a projector branch, not new machinery. The `emit-drift` job already diffs the full documented path set, so those paths are pre-covered (empty diff until emitted).
- **Note for Wave-B:** `.claude/settings.json`/`AGENTS.md`/`CLAUDE.md` managed-block merge must reproduce the Phase-2/4 hand-wired hooks byte-for-byte (do not double-wire) — see 07-RESEARCH Regime B and `test_hook_wiring.py`.

## Self-Check: PASSED

All created files verified present on disk; all three task commits (`97695bc`, `eb5436a`, `8c872be`) verified in git history. Re-emit produces a clean `git diff` over the emit-drift path set.

---
*Phase: 07-single-source-dual-runtime-emitter*
*Completed: 2026-07-12*
