---
phase: 29-docs-drive-loop-adoption-integration-closeout-v2-3-c
plan: 01
subsystem: docs_guard
tags: [DOCSUP-06, exclusions, contract-first, adversarial-table, tdd]
requires:
  - tools/hooks/contract_guard.py::CONSTITUTION_GLOBS
  - tools/adoption_scan/destinations.py::DERIVED_GLOBS
  - tools/docs_guard/registry.py::ADR_GLOBS, REPO_ROOT
  - tools/adoption_apply/apply.py::refuse_if_outside_root, PathEscapeError
  - tools/harness_perms::resolve_path
provides:
  - "tools.docs_guard.exclusions.exclusion_reason(target, root=REPO_ROOT) -> str | None"
  - "REASON_CONSTITUTION / REASON_DERIVED / REASON_ACCEPTED_ADR"
affects:
  - 29-03 (/docs-update carries ZERO glob literals and names this function instead)
tech-stack:
  added: []
  patterns:
    - "import-is-the-control: glob lists imported, never retyped; pinned by `is`-identity tests"
    - "classifier vs write-guard: `..` resolves-then-confines instead of being pre-rejected"
key-files:
  created:
    - tools/docs_guard/exclusions.py
    - tools/docs_guard/tests/test_exclusions.py
  modified:
    - tools/docs_guard/__init__.py
decisions:
  - "D-06 satisfied by code: the five exclusions are a pure function with per-class deletion proofs, not prose in a SKILL body"
  - "Accepted-ADR is classified path-shaped only; the `Status:` line is NOT re-read, because registry.py already refuses a non-accepted ADR as a binding target at load time"
  - "Escape/absolute targets raise PathEscapeError rather than returning None — an escape is malformed input, not 'no exclusion applies'"
metrics:
  tasks: 2
  commits: 2
  tests_added: 31
---

# Phase 29 Plan 01: DOCSUP-06 Structural Exclusions Summary

`exclusion_reason` — a pure, path-shaped classifier in `tools/docs_guard/exclusions.py` that
returns `accepted-adr` / `derived-plane` / `constitution-plane` / `None`, built entirely out of
glob lists **imported** from `contract_guard`, `destinations`, and `registry`, so deleting a glob
at its home turns named rows in the adversarial table RED repo-wide.

## What was built

| Task | Deliverable | Commit |
|------|-------------|--------|
| 1 | `tools/docs_guard/tests/test_exclusions.py` — 15-row `EXCLUSION_CASES` over 6 classes, 3 `is`-identity assertions, 3 per-class deletion proofs, symlink test | `784e76c` |
| 2 | `tools/docs_guard/exclusions.py` + the lazy re-export branch in `tools/docs_guard/__init__.py` | `d319309` |

### Table coverage (6 classes, 15 static rows + 1 symlink test)

- **contracts** ×4 spellings — plain, `./contracts/…`, `CONTRACTS/…`, `docs/../contracts/…`
- **golden** ×1
- **accepted ADR** ×2 (`docs/adr/0009-…`, `docs/adr/./0009-…`) — asserted `!= REASON_CONSTITUTION`
- **derived** ×4 — `docs/reference/manifest.md`, `.memory/derived/contracts-index.md`, and this
  phase's own emitted twins `.opencode/skill/docs-upkeep/SKILL.md`, `.claude/commands/docs-update.md`
- **escape** ×2 — `../../etc/passwd`, `/etc/passwd`; expectation is a raised `PathEscapeError`,
  with an explicit in-test `assert expected is not None`
- **negative controls** ×2 — `docs/how-to/task-lifecycle.md`, `harness/skills/brownfield-adoption/SKILL.md` → `None`
- **symlink** — a tmp `docs/innocent.md` resolving onto `contracts/**` → `REASON_CONSTITUTION`

### The three controls that make the "delete at the home" claim true

1. `exclusions.CONSTITUTION_GLOBS is contract_guard.CONSTITUTION_GLOBS`
2. `exclusions.DERIVED_GLOBS is destinations.DERIVED_GLOBS`
3. `exclusions.ADR_GLOBS is registry.ADR_GLOBS`

`is`, not `==` (Phase 28 CR-02 verbatim): a monkeypatch proof alone shows only that a module
attribute is *read*; a locally retyped list would keep every monkeypatch green. The deletion proofs
are the complement — each patches the attribute **its own class actually reads**
(`CONSTITUTION_GLOBS` / `DERIVED_GLOBS` / `ADR_GLOBS`) because `registry.py:55` binds `ADR_GLOBS`
at *import* time by slicing `CONSTITUTION_GLOBS`, so a single combined proof could not pass.

## RED evidence (task 1, run PLAIN — never an inverted `! uv run pytest` gate)

`uv run pytest tools/docs_guard/tests/test_exclusions.py -x -q` against pre-fix code, verbatim
first failure line:

```
E   ImportError: cannot import name 'exclusions' from 'tools.docs_guard' (/Users/hyojung/orca/lifetimeworkflow/tools/docs_guard/__init__.py)
```

Collection-time import error naming `tools.docs_guard.exclusions` — RED for the stated reason
(the module did not exist). No unrelated error appeared, so the test file was not adjusted.

## Gate results

| Gate | Result |
|------|--------|
| `uv run pytest tools/docs_guard/tests/test_exclusions.py -q` | **31 passed** |
| Full docs_guard suite (explicit file list, see note) | **210 passed** |
| `uv run ruff check` on the three touched files | clean |
| `uv run ruff format --check` | already formatted |
| `grep -v '^#' exclusions.py \| grep -c 'contracts/\*\*'` | **0** (no retyped glob) |
| `grep -v '^#' exclusions.py \| grep -c 'docs/reference/\*\*'` | **0** |
| `git diff --check` | clean |

**Test-selection note (W-1):** the plan's `<verification>` names `uv run pytest tools/docs_guard -q`,
but plan 29-02 runs in the same wave and owns an in-flight
`tools/docs_guard/tests/test_selfgreen_end_to_end.py`. A package-wide selection would collect that
sibling's transient state, and neither plan may be judged on the other's. The equivalent coverage
was obtained by naming every currently-owned file explicitly:
`test_exclusions.py test_registry.py test_digest.py test_guard.py test_impact.py test_ledger.py test_report.py`
→ 210 passed. Passes reported alongside the RED run also prove collection succeeded.

## Deviations from Plan

None — the plan (as revised after plan-check) executed exactly as written. Two cosmetic in-task
edits: two docstring lines were rewrapped to satisfy `E501` before the task-2 commit.

## Design notes worth carrying

- **Classifier ≠ write guard.** `refuse_unsafe_destination` pre-rejects any literal `..` segment
  *before* resolving. This function deliberately does not: it returns `str | None` and cannot both
  raise and classify, and `docs/../contracts/x` is a legal spelling of a constitution path that
  must classify. Confinement is unweakened — `refuse_if_outside_root` runs on the **resolved** path.
- **Return value, not exception, for refusal.** An exception would force call sites into
  `try`/`except` and invite one to swallow it. The single asymmetry (escape/absolute → raise) is
  documented in the module docstring.
- **No content I/O.** The ADR class is decided from the path alone; `registry.py` already refuses a
  non-accepted ADR as a binding target at load time, so re-reading `Status:` here would make a path
  predicate impure for no added control. Stated in the docstring with that citation.
- **Layering.** `contract_guard` and the matrix `path_deny_globs` remain the runtime write-side
  backstops; this module is the decision layer.

## Known Stubs

None.

## Threat Flags

None — zero new dependencies, no new network/auth/file-write surface. The module performs
read-only path resolution and adds no write path.

## Self-Check: PASSED

- `tools/docs_guard/exclusions.py` — FOUND
- `tools/docs_guard/tests/test_exclusions.py` — FOUND
- `tools/docs_guard/__init__.py` — FOUND (modified)
- commit `784e76c` — FOUND
- commit `d319309` — FOUND
