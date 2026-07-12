---
phase: 07-single-source-dual-runtime-emitter
plan: 02
subsystem: infra
tags: [emitter, codegen, opencode, claude-code, commands, skills, references, coexistence, syrupy]

# Dependency graph
requires:
  - phase: 07-single-source-dual-runtime-emitter
    plan: 01
    provides: emit spine (generate.emit/_confine/render, project_agent pattern, loud-fail validate, ownership manifest, emit-drift CI gate)
  - phase: 03-agents-commands-skills
    provides: dual-representation harness/commands + harness/skills source + tools.harness_lint.caps (skill caps + EXPECTED_SKILLS) + test_commands/test_skills shape rules
provides:
  - "tools/harness_emit/project_command.py — command projection (opencode keeps description/agent/subtask; Claude keeps description only)"
  - "tools/harness_emit/project_skill.py — skill projection (identical both runtimes) + references/** byte-copy enumeration"
  - "validate.check_command / check_skill / check_skill_set — emit-time loud-fail cap/shape gates for commands + skills"
  - "committed .opencode/{command,skill}/** + .claude/{commands,skills}/** harness slice (machine-written, CI-verified)"
  - "test_coexist.py — GSD command non-collision proof (.claude/commands/*.md disjoint from .claude/commands/gsd/**)"
affects: [plugins verbatim-copy, opencode.json config emit, AGENTS.md/CLAUDE.md/settings.json managed-block merge]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Widen-by-projector: each new artifact type adds a project_*.py branch + a validate case + a discovery iterator + a write block — no new machinery (07-01 spine reused verbatim)"
    - "Validate-ALL-then-write-ALL across every artifact type, so a cap/shape violation anywhere aborts the whole emit having written nothing"
    - "references/** copied byte-for-byte (read_bytes/write_bytes, NO normalization) through _confine'd targets — symlink-safe sorted-glob discovery (T-07-01)"
    - "Skill divergence = None: to_opencode == to_claude (name+description); the Mapping-Table divergence cell is empty for skills"

key-files:
  created:
    - tools/harness_emit/project_command.py
    - tools/harness_emit/project_skill.py
    - tools/harness_emit/tests/test_coexist.py
  modified:
    - tools/harness_emit/generate.py
    - tools/harness_emit/validate.py
    - tools/harness_emit/tests/test_mapping.py
    - tools/harness_emit/tests/test_validators.py
    - tools/harness_emit/tests/test_emit_determinism.py
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
    - tools/harness_emit/emit-manifest.json

key-decisions:
  - "render_agent renamed to the artifact-neutral render_markdown with a back-compat alias — the serializer was never agent-specific, so commands/skills reuse it under an honest name"
  - "check_skill_set (EXPECTED_SKILLS anti-drift) runs ONLY when skills are discovered, so a synthetic single-artifact test harness does not spuriously trip the 9-skill pin; the real tree always has 9"
  - "Command description cap enforced at emit-time (not only agent slug/subtask) for parity with agents/skills — over-cap FAILS, never truncates (T-07-05)"

patterns-established:
  - "emit() collects a per-type projection PLAN (validate) before ANY write, then writes agents → commands → skills in one pass so loud-fail leaves nothing partial"
  - "iter_skills returns the skill source dir so the emitter can locate references/ without a second discovery"

requirements-completed: [EMIT-01, EMIT-02]

# Metrics
duration: 9min
completed: 2026-07-12
---

# Phase 7 Plan 02: Commands + Skills Emit Widening Summary

**The 17 harness commands and 9 harness skills now compile from the runtime-neutral `harness/` source into byte-faithful `.opencode/{command,skill}/**` + `.claude/{commands,skills}/**` trees — commands get per-runtime shape (opencode keeps agent/subtask, Claude keeps description only), skills get identical shape plus byte-for-byte `references/` copies, both under the same loud-fail validators and emit-drift gate the agents already ride.**

## Performance

- **Duration:** ~9 min
- **Started:** 2026-07-12T07:47:09Z
- **Completed:** 2026-07-12T07:56:32Z
- **Tasks:** 2 (each RED → GREEN)
- **Files:** 3 created + 7 modified + 56 emitted artifacts (34 command `.md` + 18 skill `SKILL.md` + 4 `references/` files)

## Accomplishments
- Built `project_command.py`: `to_opencode` keeps `description/agent/subtask`; `to_claude` keeps `description` only (drops `agent`+`subtask` — no Claude equivalent). The `` !`shell` `` + `$ARGUMENTS` body is shared verbatim.
- Built `project_skill.py`: `name`+`description` kept identically for both runtimes (divergence None); `iter_reference_files` enumerates `references/**` sorted + symlink-safe for the byte-copy.
- Added emit-time validators `check_command`, `check_skill`, `check_skill_set` importing every cap from `tools.harness_lint.caps` — over-cap name/description raise (never truncate); a >500-line skill body only WARNS (D-07) and still emits; the emitted skill set is pinned to `EXPECTED_SKILLS` (9).
- Refactored `emit()` into validate-ALL-then-write-ALL across agents + commands + skills, so a violation anywhere aborts having written nothing. `references/**` is copied byte-for-byte through `_confine`d targets to BOTH trees.
- `test_coexist.py` proves the harness command surface is top-level `.claude/commands/*.md`, provably DISJOINT from `.claude/commands/gsd/**`; a seeded `gsd/` fixture survives an emit byte-unchanged and is never enumerated by the manifest.
- Committed the emitted command + skill surface; a second `python -m tools.harness_emit` reproduces every file byte-for-byte (emit-drift gate clean over the full documented path set).

## Task Commits

Each task ran RED → GREEN as separate commits (TDD gate compliance):

1. **Task 1 RED — command projection + GSD non-collision tests** — `8dc3537` (test)
2. **Task 1 GREEN — command projector + 17-command surface** — `6180859` (feat)
3. **Task 2 RED — skill projection + references + cap tests** — `7519bc2` (test)
4. **Task 2 GREEN — skill projector + references byte-copy + 9-skill surface** — `16e2c9d` (feat)

**Plan metadata:** see final `docs(07-02)` commit.

## Files Created/Modified
- `tools/harness_emit/project_command.py` — command frontmatter projection (opencode vs Claude key selection; verbatim values).
- `tools/harness_emit/project_skill.py` — skill projection (identical both runtimes) + `iter_reference_files` (sorted, symlink-safe, confinement defense-in-depth).
- `tools/harness_emit/validate.py` — added `check_command`, `check_skill`, `check_skill_set` + a `_fold` helper for description length parity with the emitted output.
- `tools/harness_emit/generate.py` — `iter_commands`/`iter_skills` discovery; `render_agent` → `render_markdown` (+ alias); `emit()` widened to agents + commands + skills with `references/**` byte-copy; `main()` message updated.
- `tools/harness_emit/tests/test_coexist.py` — GSD command non-collision + 17-command dual-tree assertions.
- `tools/harness_emit/tests/{test_mapping,test_validators,test_emit_determinism}.py` — command/skill projection shapes, over-cap-aborts + body-warn, references byte-copy + `EXPECTED_SKILLS` anti-drift, widened snapshot.
- `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` — widened to the projected command + skill tree.
- `.opencode/{command,skill}/**` + `.claude/{commands,skills}/**` — emitted harness slice.
- `tools/harness_emit/emit-manifest.json` — ownership manifest now enumerating agents + commands + skills + reference files.

## Decisions Made
- **`render_agent` → `render_markdown` (with alias):** the serializer only ever consumed a projected frontmatter dict + a body; it was never agent-specific. Commands and skills reuse it under an honest generic name, and `render_agent = render_markdown` preserves the 07-01 import used by the determinism test.
- **`check_skill_set` is guarded by `if skills:`** in `emit()` so the anti-drift 9-skill pin fires on the real tree (always 9) but does not spuriously trip a synthetic single-artifact test harness (`test_validators` injects one agent, no skills). Agent validation runs first regardless, so the loud-fail tests still fail for the intended reason.
- **Command description cap enforced at emit-time** for parity with agents/skills (the structural lint `test_commands` did not cap it) — over-cap FAILS, never truncates (T-07-05). This is a Rule-2 correctness addition, not scope creep.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical validation] Command description cap added to `check_command`**
- **Found during:** Task 1 (validate.check_command)
- **Issue:** The plan named only "agent well-formed slug + subtask boolean" for the command validator, but the T-07-05 no-truncation invariant applies to every artifact carrying a `description`. A command with a >1024-char description would have emitted silently.
- **Fix:** `check_command` folds then length-checks the description (loud-fail, never truncate) in addition to the agent-slug + subtask-boolean checks.
- **Files modified:** tools/harness_emit/validate.py
- **Verification:** command emit stays green; parity with `check_agent`/`check_skill` desc caps.
- **Committed in:** `6180859` (Task 1 GREEN)

---

**Total deviations:** 1 auto-fixed (Rule 2, correctness parity). No architectural changes, no authentication gates.
**Impact on plan:** none beyond a stronger command validator; both tasks landed as written.

## Issues Encountered
- Several new docstring/comment lines tripped ruff `E501` (100-col) after the PostToolUse formatter; all were shortened. Every newly-authored line is ruff-clean.
- No PyYAML in the workspace (repo standardizes on ruamel) — not needed here; frontmatter is read via the shared `parse_frontmatter`.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- The widening pattern is proven twice (agents → commands → skills): the remaining surfaces (plugins verbatim-copy, `opencode.json` config, and the `AGENTS.md`/`CLAUDE.md`/`settings.json` managed-block merges) only ADD a projector/copy branch + a validate case + a write block.
- **Note for the managed-block wave:** `.claude/settings.json` / `AGENTS.md` / `CLAUDE.md` must reproduce the Phase-2/4 hand-wired hooks byte-for-byte (do not double-wire) — see 07-RESEARCH Regime B and `test_hook_wiring.py`.
- The `emit-drift` CI job already diffs the full documented path set (agents + commands + skills now non-empty), so the command/skill trees are covered without a CI change.

## Self-Check: PASSED

All created files verified present on disk (`project_command.py`, `project_skill.py`, `test_coexist.py`); all four task commits (`8dc3537`, `6180859`, `7519bc2`, `16e2c9d`) verified in git history. `uv run pytest tools/harness_emit` = 22 passed; full suite = 463 passed. Re-emit produces a clean `git diff` over `.opencode` / `.claude/{agents,commands,skills}` / `emit-manifest.json`. `references/**` confirmed byte-identical to source via `cmp` in both trees.

---
*Phase: 07-single-source-dual-runtime-emitter*
*Completed: 2026-07-12*
