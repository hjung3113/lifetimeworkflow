---
phase: 01-constitution-golden-core
plan: 05
subsystem: contracts
tags: [rfc8785, jcs, sha256, contract-drift, jsonschema, python, uv, pytest]

# Dependency graph
requires:
  - phase: 01-01
    provides: uv workspace + pinned rfc8785 0.1.4 / jsonschema 4.26.0 in the shared environment
  - phase: 01-02
    provides: contracts/**/*.schema.json incl. materialized format-conventions.schema.json (P14 target)
provides:
  - Python-only RFC 8785 (JCS) canonicalize + SHA-256 per-schema hasher (tools/contract_hash)
  - Committed per-file baseline manifest contracts/.hashes/manifest.json (5 schemas)
  - Contract-drift gate with breaking/non-breaking classification (tools/contract_drift + check.sh)
  - Proof (test_convention_mutation) that a §4-5 convention flip trips the gate exactly like a column reorder (P14)
affects: [phase-04-polyglot-linter, phase-05-ci, contract-change-workflow, golden-approve]

# Tech tracking
tech-stack:
  added: [rfc8785 0.1.4 (Python JCS canonicalizer)]
  patterns:
    - "Two-canonicalizer split: JCS on JSON contract text (Python-only) is separate from the §4-5 TSV comparator (Pitfall 1)"
    - "Never hand-roll canonicalization/hash: rfc8785.dumps + hashlib.sha256 only"
    - "Virtual uv workspace members (package=false) imported by module path; tests add repo root to sys.path"

key-files:
  created:
    - tools/contract_hash/hash.py
    - tools/contract_hash/__init__.py
    - tools/contract_hash/pyproject.toml
    - contracts/.hashes/manifest.json
    - tools/contract_drift/drift.py
    - tools/contract_drift/check.sh
    - tools/contract_drift/__init__.py
    - tools/contract_drift/pyproject.toml
    - tools/contract_drift/tests/test_convention_mutation.py
    - tools/contract_drift/tests/test_classify.py
  modified:
    - uv.lock

key-decisions:
  - "Manifest keys are repo-relative POSIX paths (contracts/...), computed relative to contracts_dir.parent so tmp-tree copies and the real repo yield identical keys"
  - "Classification is a pure schema-document diff (classify(old,new)); the gate fetches old content via `git show HEAD:<path>` (shell=False) when diffing a copied tmp tree"
  - "enum edits: additive superset = non-breaking, dropped/changed value = breaking; const change = breaking; removed/renamed property or dropped required field = breaking"

patterns-established:
  - "Contract-drift gate: recompute live JCS SHA-256 manifest, diff vs committed baseline, exit non-zero + classify on any divergence"
  - "Baseline update is human-gated: check.sh message directs to re-run the hasher AND pair a golden/ADR update (CODEOWNERS)"

requirements-completed: [CONTRACT-04]

# Metrics
duration: 18min
completed: 2026-07-08
---

# Phase 1 Plan 05: Contract-drift gate (RFC 8785 → SHA-256 manifest) Summary

**Python-only JCS (rfc8785) + SHA-256 per-schema manifest with a drift gate that trips on any unapproved `.schema.json` change — including §4-5 cross-cutting conventions (P14) — and classifies it breaking vs non-breaking.**

## Performance

- **Duration:** ~18 min
- **Completed:** 2026-07-08
- **Tasks:** 2 (both TDD)
- **Files modified:** 11 (10 created + uv.lock)

## Accomplishments
- `tools/contract_hash`: `schema_hash(path)` returns a stable SHA-256 over `rfc8785.dumps(json)`; `build_manifest()` globs `contracts/**/*.schema.json` (confined to the subtree); `--write` emits the committed baseline `contracts/.hashes/manifest.json` (5 schemas, incl. `format-conventions.schema.json`).
- `tools/contract_drift`: `run_gate()` recomputes the live manifest, diffs vs baseline, and classifies each drifted schema; `check.sh` is the CLI gate (exit 0 when live == baseline, non-zero listing drifted files + classification).
- P14 closed: `test_convention_mutation` flips `bom` false→true on a tmp copy, proving the JCS hash bumps and the gate trips — exactly like a column reorder.
- Breaking/non-breaking classification per the seed change_policy, covered by `test_classify` (7 cases).
- 10 tests green; `bash tools/contract_drift/check.sh` exits 0 on the unchanged committed tree; end-to-end trip verified (exit 1, "breaking") then restored.

## Task Commits

1. **Task 1: JCS hasher + generated baseline manifest** - `d470478` (feat)
2. **Task 2: Drift gate + breaking/non-breaking classification + tests** - `42e40a1` (feat, TDD RED→GREEN)

_TDD note: Task 2 tests were written and confirmed RED (ModuleNotFoundError) before `drift.py` was implemented to GREEN. Task 1 has no dedicated pytest file (its verification is the inline `--write` + manifest-assert CLI per the plan), so it is a single feat commit._

## Files Created/Modified
- `tools/contract_hash/hash.py` - `schema_hash` (JCS + SHA-256), `build_manifest`, `write_manifest`, `--write` CLI
- `tools/contract_hash/pyproject.toml` / `__init__.py` - virtual uv workspace member
- `contracts/.hashes/manifest.json` - GENERATED per-file JCS SHA-256 baseline (5 schemas)
- `tools/contract_drift/drift.py` - `diff_manifests`, `classify`, `run_gate`, `_git_show` (shell=False), CLI
- `tools/contract_drift/check.sh` - gate CLI entry
- `tools/contract_drift/pyproject.toml` / `__init__.py` - virtual uv workspace member
- `tools/contract_drift/tests/test_convention_mutation.py` - P14 demo (convention flip trips gate)
- `tools/contract_drift/tests/test_classify.py` - breaking vs non-breaking cases
- `uv.lock` - registered the two new workspace members

## Decisions Made
- Manifest keys computed relative to `contracts_dir.parent`, so a `shutil.copytree`'d tmp tree and the real repo produce identical `contracts/...` keys (lets tests reuse the committed baseline directly).
- `classify(old, new)` is a standalone pure function (indexes const/enum/required/property-presence recursively) so nested convention consts (e.g. `float_compare.tolerance`) and top-level `bom` are both covered; the gate obtains `old` via `git show HEAD:<path>`.
- enum widening = non-breaking (subset check), enum narrowing/const change = breaking, aligning with the seed change_policy ("신규 케이스 추가 = non-breaking; 기존 기대출력 변경 = breaking").

## Deviations from Plan

None - plan executed exactly as written. (Ruff flagged import ordering in `test_convention_mutation.py`; reordered the two imports to satisfy `ruff check` before committing — a formatting fix within the task, not a scope change.)

## Issues Encountered
None. rfc8785 0.1.4 and jsonschema were already installed via the Plan 01 uv lockfile (no blocked network). No .NET involved (JCS is Python-only, Pitfall 1).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Contract-drift gate is locally runnable (`bash tools/contract_drift/check.sh`); Phase 5 (CI-01) can wire it into the polyglot matrix + pre-commit as-is.
- The `classify` function and manifest are reusable by the Phase 4 polyglot linter and the `/golden-approve` / contract-change workflow.
- Baseline updates remain human-gated (machines gate, humans ratify) — the gate output directs contributors to pair a hasher `--write` with a golden/ADR change under CODEOWNERS.

## Self-Check: PASSED

All 11 created files present; both task commits (`d470478`, `42e40a1`) found in git history. `uv run pytest tools/contract_drift/tests -x` → 10 passed; `bash tools/contract_drift/check.sh` → exit 0.

---
*Phase: 01-constitution-golden-core*
*Completed: 2026-07-08*
