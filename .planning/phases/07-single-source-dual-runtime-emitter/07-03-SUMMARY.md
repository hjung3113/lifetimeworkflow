---
phase: 07-single-source-dual-runtime-emitter
plan: 03
subsystem: infra
tags: [emitter, codegen, opencode, plugins, permission-matrix, jsonschema, determinism, syrupy]

# Dependency graph
requires:
  - phase: 07-single-source-dual-runtime-emitter
    plan: 01
    provides: emit spine (generate.emit/_confine/render, loud-fail validate, ownership manifest, emit-drift CI gate)
  - phase: 07-single-source-dual-runtime-emitter
    plan: 02
    provides: widen-by-projector pattern (project_*.py + validate case + discovery iterator + write block)
  - phase: 03-agents-commands-skills
    provides: harness/permission-matrix.json + tools.harness_perms.resolver.load_matrix (order-preserving) + harness/opencode.json + vendored subset schema
provides:
  - "tools/harness_emit/permissions.py — permission-matrix.json → opencode.json 15-key block (the one genuine transform) + deterministic bash-order-preserving serializer"
  - "generate.build_opencode_config — emitter-owned wholesale opencode.json (authored config + full 15-key permission block)"
  - "validate.check_opencode_config — jsonschema loud-fail + no-real-model-identifier gate"
  - "committed root opencode.json (full 15-key permission block, placeholder tiers only)"
  - "5 verbatim byte-copied .opencode/plugin/*.ts (never parsed/executed)"
affects: [AGENTS.md/CLAUDE.md/settings.json managed-block merge, opencode runtime wiring]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Verbatim byte-copy of untrusted-shaped .ts source (read_bytes/write_bytes) — never parsed/imported/executed at emit (D-01; Elevation mitigation T-07-04)"
    - "The one genuine transform (matrix → 15-key block) isolated in permissions.py; strip resolver-only keys (_note, path_deny_globs)"
    - "Sort keys for determinism EVERYWHERE except the bash glob object, which keeps authored *-first last-wins order (P3/T-07-06)"
    - "Emitter owns opencode.json wholesale: authored partial permission block replaced by the full 15-key block; build+validate before any write (loud-fail)"

key-files:
  created:
    - tools/harness_emit/permissions.py
    - tools/harness_emit/tests/test_opencode_config.py
    - opencode.json
  modified:
    - tools/harness_emit/generate.py
    - tools/harness_emit/validate.py
    - tools/harness_emit/tests/test_emit_determinism.py
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
    - tools/harness_emit/emit-manifest.json

key-decisions:
  - "opencode.json emitted at the REPO ROOT (opencode's documented project-config location, Open Question 1 resolution); emitter owns it wholesale via the manifest — no GSD conflict"
  - "Model-identity gate uses a placeholder-tier REGEX (provider/<tier>-tier) covering every model/*_model key, not equality to a single constant — model is provider/implementer-tier, small_model is provider/explorer-tier"
  - "dumps_config pre-sorts the structure recursively then json.dumps(indent=2) — never sort_keys=True (which would reorder the bash glob object and break last-wins)"

patterns-established:
  - "Plugins/config widen the 07-01 spine with a copy/build branch + a validate case + a write block — no new machinery (proven 4th time)"
  - "The one Elevation-risk surface (untrusted .ts at emit) mitigated by copy-never-execute, verified by cmp byte-identity with no interpreter invoked"

requirements-completed: [EMIT-01, EMIT-02]

# Metrics
duration: 10min
completed: 2026-07-12
---

# Phase 7 Plan 03: opencode Plugins + 15-Key Permission Config Emit Summary

**The opencode primary target is complete — the 5 harness `.ts` plugins are byte-verbatim-copied to `.opencode/plugin/` (never executed), and `harness/permission-matrix.json` is projected into an emitter-owned root `opencode.json` carrying the full 15-key `permission` block with `*`-first last-wins order intact, schema-validated with loud-fail and free of any real model identifier.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-07-12T07:59:00Z
- **Completed:** 2026-07-12T08:08:00Z
- **Tasks:** 2 (Task 2 ran RED → GREEN)
- **Files:** 3 created + 5 modified

## Accomplishments
- `iter_plugins` + an emit() copy branch write each `harness/plugins/*.ts` (5 files) byte-for-byte to `.opencode/plugin/<name>.ts` via `read_bytes`/`write_bytes` through a `_confine`d target — the TypeScript is NEVER parsed, transformed, imported, or executed at emit (D-01; T-07-04 Elevation mitigation). No Claude plugin target, no `.opencode/tool/` dir. `cmp` confirms all 5 copies are byte-identical to source.
- `permissions.build_permission_block` performs the emitter's ONE genuine transform: it projects the CONFIG-02 matrix into the exact 15 opencode `permission` keys, stripping the two resolver-only fields (`_note`, `path_deny_globs`); the `bash` sub-object keeps its authored `*`-first insertion order (last-wins, P3/T-07-06). Read via the order-preserving `tools.harness_perms.resolver.load_matrix` (one loader, no second parse).
- `permissions.dumps_config` serializes deterministically — recursively sort keys for byte-stability EXCEPT the `bash` glob object, which stays in authored order (sorting it would break last-wins).
- `generate.build_opencode_config` builds the emitter-owned root `opencode.json` = authored `harness/opencode.json` with its PARTIAL permission block REPLACED by the full 15-key block; every other authored key (model tiers, formatter, instructions, mcp, plugin) passes through verbatim.
- `validate.check_opencode_config` is a two-gate loud-fail run BEFORE any write: `jsonschema.validate` against the vendored subset schema (T-07-07 — malformed config aborts writing nothing) AND a placeholder-tier regex over every `model`/`*_model` key (T-07-03 — no real model identifier may leak).
- Committed the root `opencode.json` + plugin surface; widened the syrupy `.ambr` snapshot to pin the config transform; a second `python -m tools.harness_emit` reproduces `opencode.json` + `.opencode` byte-for-byte (emit-drift gate clean). Full non-example suite = 473 passed.

## Task Commits

1. **Task 1: Verbatim `.ts` plugin copy to `.opencode/plugin/`** — `4648121` (feat)
2. **Task 2 RED — opencode.json config + permission-block tests** — `567c952` (test)
3. **Task 2 GREEN — permission-matrix → 15-key block + schema loud-fail** — `f89b1e4` (feat)

**Plan metadata:** see final `docs(07-03)` commit.

## Files Created/Modified
- `tools/harness_emit/permissions.py` — `build_permission_block` (matrix → 15 keys, strip resolver-only data), `_canonicalize` (sort-except-bash), `dumps_config` (deterministic JSON + trailing LF).
- `tools/harness_emit/generate.py` — `iter_plugins`, plugin byte-copy branch, `build_opencode_config`, config build+validate up front + root `opencode.json` write; updated main() message.
- `tools/harness_emit/validate.py` — `check_opencode_config` (jsonschema subset validation + placeholder-tier model gate) + `_PLACEHOLDER_MODEL_RE`.
- `tools/harness_emit/tests/test_opencode_config.py` — 15-key/no-resolver-key projection, `*`-first bash order, schema-invalid + real-model-id raise, emitted + committed root config shape, determinism.
- `tools/harness_emit/tests/test_emit_determinism.py` + `__snapshots__/test_emit_determinism.ambr` — snapshot widened to the serialized `opencode.json` config transform.
- `opencode.json` — emitted root config: full 15-key permission block, `*`-first bash, placeholder tiers only.
- `tools/harness_emit/emit-manifest.json` — ownership manifest now enumerating the 5 plugins + root `opencode.json`.

## Decisions Made
- **Root `opencode.json` location (Open Question 1):** emitted at the repo root — opencode's documented project-config path. The emitter owns it wholesale via the manifest, so there is no GSD/hand-authored conflict; the authored `harness/opencode.json` remains the single source it is built from.
- **Placeholder-tier regex over equality:** `caps.PLACEHOLDER_MODEL` is a single constant (`provider/explorer-tier`), but `opencode.json` carries two distinct tiers (`model=provider/implementer-tier`, `small_model=provider/explorer-tier`). The model-identity gate therefore matches `^provider/<tier>-tier$` across every `model`/`*_model` key rather than equality to one token — still refuses any real provider identifier (T-07-03).
- **Determinism via pre-sort, not `sort_keys=True`:** `json.dumps(sort_keys=True)` would reorder the `bash` glob object and break `*`-first last-wins. `dumps_config` recursively rebuilds the structure with sorted keys but preserves the authored order of any `bash` mapping, then dumps with `sort_keys=False`.

## Deviations from Plan

None - plan executed exactly as written. The plan's `files_modified` listed `.opencode/plugin/` and `opencode.json` as created outputs and `test_mapping.py` among the touched tests; the config assertions landed in the dedicated `test_opencode_config.py` (as the plan's action step directs) rather than `test_mapping.py`, and `test_emit_determinism.py` was the snapshot-widening site — both within the plan's stated intent.

## Issues Encountered
- Several new docstring/comment lines tripped ruff `E501` (100-col) after authoring; all were shortened. Every newly-authored line is ruff-clean (`ruff check tools/harness_emit/` → all checks passed).

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- The opencode primary surface is now fully emitted (agents + commands + skills + plugins + `opencode.json`). The remaining Wave surface is the `AGENTS.md`/`CLAUDE.md`/`.claude/settings.json` managed-block MERGES, which must reproduce the Phase-2/4 hand-wired hooks byte-for-byte (do not double-wire) — see 07-RESEARCH Regime B and `test_hook_wiring.py`.
- The `emit-drift` CI job already diffs `opencode.json` + `.opencode` in its documented path set (now non-empty for plugins + config), so this surface is covered without a CI change.

## Self-Check: PASSED

All created files verified present on disk (`permissions.py`, `test_opencode_config.py`, `opencode.json`); all three task commits (`4648121`, `567c952`, `f89b1e4`) verified in git history. TDD gate satisfied (RED `567c952` → GREEN `f89b1e4`). Re-emit produces a clean `git diff` over `opencode.json` + `.opencode`; `cmp` confirms all 5 plugin copies byte-identical to source.

---
*Phase: 07-single-source-dual-runtime-emitter*
*Completed: 2026-07-12*
