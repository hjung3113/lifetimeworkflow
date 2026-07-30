---
phase: 03-agents-commands-skills
plan: 02
subsystem: config
tags: [opencode, json-schema, jsonschema, frontmatter, ruamel-yaml, uv-workspace, harness-lint]

# Dependency graph
requires:
  - phase: 02-context-memory
    provides: harness/plugins/session-inject.ts (Phase-2 injector wired into opencode.json.plugin)
  - phase: 03-agents-commands-skills (03-01)
    provides: harness/permission-matrix.json (bash last-wins ordering mirrored into opencode.json default block)
provides:
  - "harness/opencode.json — CONFIG-01 runtime config (placeholder model tiers, instructions pointers, ruff+dotnet formatter, empty mcp, last-wins permission default, session-inject plugin wiring)"
  - "harness/opencode.config.schema.json — vendored Draft 2020-12 subset schema for the hermetic structural gate"
  - "tools/harness_lint/frontmatter.py — shared parse_frontmatter(md_text)->(dict,body) reused by Plans 03/04/05"
  - "tools/harness_lint/tests/test_opencode_json.py — jsonschema validation + CONFIG-01 key presence"
affects: [03-03, 03-04, 03-05, phase-6-emitter]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Vendored subset JSON-Schema as a hermetic validation aid (never fetch opencode.ai)"
    - "Shared frontmatter parser (one impl, ruamel.yaml safe loader) instead of per-validator string slicing"
    - "Virtual uv member with package=false + PEP-562 lazy re-export (namespace-package collection-safe)"

key-files:
  created:
    - harness/opencode.json
    - harness/opencode.config.schema.json
    - tools/harness_lint/__init__.py
    - tools/harness_lint/frontmatter.py
    - tools/harness_lint/pyproject.toml
    - tools/harness_lint/tests/__init__.py
    - tools/harness_lint/tests/test_opencode_json.py
  modified:
    - uv.lock

key-decisions:
  - "opencode.json model/small_model carry PLACEHOLDER tier tokens (provider/implementer-tier, provider/explorer-tier) — no real model IDs (model-identity constraint); small_model key name A1-deferred to Phase 6"
  - "Vendored subset schema uses additionalProperties:true so unknown/future opencode keys never fail the gate; only CONFIG-01 keys are required"
  - "parse_frontmatter uses the already-resolved ruamel.yaml (safe loader) — pyyaml is absent and was NOT added; CRLF-normalized fence scan"
  - "uv.lock change is the member registration entry ONLY — zero new external packages (T-03-SC honored)"

patterns-established:
  - "Hermetic structural gate: jsonschema.validate(authored config, vendored subset schema) with no network"
  - "harness_lint as the shared structural-validation member; frontmatter parser is the reuse seam for downstream agent/command/skill lints"

requirements-completed: [CONFIG-01]

# Metrics
duration: 9min
completed: 2026-07-08
---

# Phase 3 Plan 02: opencode.json + vendored subset schema + harness_lint foundation Summary

**Authored `harness/opencode.json` (placeholder model tiers, AGENTS.md instruction pointers, ruff+dotnet formatter, last-wins permission default, session-inject plugin wiring) validated hermetically against a hand-authored vendored Draft-2020-12 subset schema, plus the shared `parse_frontmatter` parser and its uv member that every downstream structural lint reuses.**

## Performance

- **Duration:** ~9 min
- **Completed:** 2026-07-08
- **Tasks:** 2
- **Files modified:** 8 (7 created + uv.lock)

## Accomplishments
- CONFIG-01 satisfied: `harness/opencode.json` defines model tiering, instructions glob, formatter, MCP wiring, coarse last-wins permission default, and registers the Phase-2 session-inject plugin — carrying only placeholder tier tokens (no real model ID).
- Hermetic structural gate: `harness/opencode.config.schema.json` (vendored subset, `additionalProperties:true`) + `test_opencode_json.py` prove opencode.json validates against the subset with no network (T-03-05/T-03-08).
- Shared `tools/harness_lint/frontmatter.py::parse_frontmatter` — the single YAML-frontmatter reader Plans 03/04/05 import; handles flat, nested, no-fence, and CRLF inputs via the already-locked ruamel.yaml safe loader.
- `tools/harness_lint/` stood up as a virtual uv member (package=false, zero external deps); `uv sync --all-packages` green, uv.lock gained only the member entry.

## Task Commits

1. **Task 1: Author opencode.json + vendored subset schema** - `8b1b83d` (feat)
2. **Task 2 (RED): structural gate for opencode.json** - `eb541be` (test)
3. **Task 2 (GREEN): harness_lint foundation — frontmatter parser + gate** - `5f38ae2` (feat)

**Plan metadata:** _(final docs commit — this summary + STATE.md + ROADMAP.md)_

## Files Created/Modified
- `harness/opencode.json` - CONFIG-01 runtime config (model/small_model placeholders, instructions pointers, formatter, empty mcp, permission default, plugin wiring)
- `harness/opencode.config.schema.json` - vendored Draft-2020-12 subset schema (hermetic validation aid, not the runtime schema)
- `tools/harness_lint/frontmatter.py` - shared `parse_frontmatter(md_text) -> (dict, body)` (ruamel.yaml safe loader)
- `tools/harness_lint/__init__.py` - PEP-562 lazy re-export of parse_frontmatter (collection-safe)
- `tools/harness_lint/pyproject.toml` - virtual uv member (package=false, no external deps)
- `tools/harness_lint/tests/test_opencode_json.py` - jsonschema validation + CONFIG-01 key + placeholder-only assertions
- `tools/harness_lint/tests/__init__.py` - test package marker
- `uv.lock` - added `logparser-harness-lint` virtual member entry (no new external packages)

## Decisions Made
- Placeholder-only model tokens with a JSON `_note` flagging the A1 (`small_model` key name) and A6 (injector hook names) Phase-6 re-verification points — no code comment, honoring model-identity + deferral constraints.
- Subset schema requires only CONFIG-01 keys with `additionalProperties:true`, and models `permission.bash` as `oneOf` (coarse string OR glob object) so both shapes validate.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Initial ruff run flagged two E501 long lines in the test file (assert messages); reformatted with multi-line asserts + `ruff format`. No behavior change; caught before the GREEN commit.
- `uv.lock` changed on `uv sync --all-packages`; inspected the diff to confirm it is solely the new virtual-member registration (no third-party package added) — T-03-SC upheld.

## TDD Gate Compliance
Task 2 followed RED→GREEN: `test(03-02)` commit `eb541be` (fails at collection — member unregistered) precedes `feat(03-02)` commit `5f38ae2` (green). No REFACTOR commit needed.

## Next Phase Readiness
- `parse_frontmatter` is the ready reuse seam for Plans 03-03/04/05 (agent/command/skill frontmatter lints).
- `harness_lint` member registered; downstream plans add test files without re-touching uv.lock.
- opencode.json plugin/hook names remain MEDIUM-confidence (A6) — re-verify before Phase-6 emit/live-load.

---
*Phase: 03-agents-commands-skills*
*Completed: 2026-07-08*

## Self-Check: PASSED

All 7 created files + this SUMMARY exist on disk; all 3 task commits (8b1b83d, eb541be, 5f38ae2) present in git history.
