---
phase: 28-human-docs-registry-guard-derived-queue-v2-3-c
plan: 02
subsystem: infra
tags: [uv-workspace, digest, hashlib, tdd, docsup, docs-guard]

# Dependency graph
requires: []
provides:
  - "tools/docs_guard/ — the phase's single new uv workspace member (virtual, package = false, dependencies = []), registered in uv.lock with no other package's resolution moved"
  - "tools/docs_guard/__init__.py — the phase's FROZEN public surface (12 names mapped to digest/registry/ledger/guard/impact), so plans 28-03/04/05 add submodules only and never edit this file"
  - "tools/docs_guard/digest.py — resolve(selectors, root) -> sorted root-confined paths, compute(paths, root) -> 64-hex digest, MissingSourceError"
  - "tools/docs_guard/tests/conftest.py — the hermetic real-`git init` `docs_repo` fixture plan 28-04 reuses for its `git show HEAD:./<path>` path"
  - "tools/docs_guard/tests/test_digest.py::AMBIGUITY_CASES — the four-row adversarial table proving the D-03 divergence is load-bearing"
affects: [28-03, 28-04, 28-05, 28-08, docsup-02]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "interface-first frozen `__init__.py`: the whole phase's export surface is declared in wave 1 as a name -> submodule map, trading a transient within-phase `ModuleNotFoundError` for zero same-wave file conflicts"
    - "RED-against-the-precedent: the adversarial table is confirmed failing against a throwaway implementation of the algorithm being diverged FROM, not merely against absent code — the failure mode proved is 'digests are equal but must differ', which an absent-module error could never demonstrate"

key-files:
  created:
    - tools/docs_guard/pyproject.toml
    - tools/docs_guard/__init__.py
    - tools/docs_guard/__main__.py
    - tools/docs_guard/digest.py
    - tools/docs_guard/tests/__init__.py
    - tools/docs_guard/tests/conftest.py
    - tools/docs_guard/tests/test_digest.py
  modified:
    - uv.lock

key-decisions:
  - "`compute` takes an optional `root` and hashes each path's label RELATIVE to it. The plan's sketch wrote `path.as_posix()` unqualified; hashing an absolute label would make every ledger digest depend on the checkout location and fail in CI under a different absolute path. Treated as a correctness requirement (deviation Rule 2), not a signature change of intent — `root=None` still hashes the given path verbatim."
  - "A root-escape (selector or in-tree symlink pointing outside) RAISES rather than being silently skipped. `tools/contract_hash/hash.py:60-63` skips, which is right for a manifest builder; a review-obligation digest that silently drops a binding's file would UNDER-report staleness, so this fails closed. The divergence is stated in `_confine`'s docstring."
  - "The escape refusal raises plain `ValueError` rather than a new exception type, so the frozen `__init__.py` surface did not have to be widened after the fact. `MissingSourceError` is itself a `ValueError` subclass, so a caller catching `ValueError` handles both refusals uniformly."
  - "`resolve` returns a literal (non-glob) selector even when the file is absent, and lets `compute` refuse it. That is what carries the BROKEN signal to the guard — a glob matching nothing contributes nothing, but a named missing file is an error."

patterns-established:
  - "A new virtual uv member's test package must do its own repo-root `sys.path` wiring in `tests/conftest.py` (parents[3]); without it pytest cannot import `tools.<member>` at all — discovered as a collection error during the RED run."

requirements-completed: [DOCSUP-02]

# Metrics
tasks-completed: 2
duration: ~30m
completed: 2026-07-21
---

# Phase 28 Plan 02: docs_guard uv Member + Deterministic Digest Summary

Stood up `tools/docs_guard/` as the phase's one new uv member with a frozen, phase-complete public
interface, and landed `digest.py` — the interleaved path + per-file-digest algorithm that
deliberately diverges from `tools/adoption_apply/approval.py:57-63`, proven by a four-row adversarial
table that was RED against that precedent algorithm first.

## What Was Built

**The member.** `tools/docs_guard/pyproject.toml` mirrors `tools/adoption_scan/pyproject.toml`
field-for-field — `logparser-docs-guard`, `version = "0.0.0"`, `requires-python = ">=3.11"`,
`dependencies = []`, `[tool.uv] package = false`. The root `pyproject.toml` was NOT touched (D-17):
`members = ["libs/python", "tools/*"]` already globs it. `uv sync --all-packages` added exactly the
`logparser-docs-guard` members-list line plus its `source = { virtual = "tools/docs_guard" }` entry
— six inserted lines, zero deletions, no existing version pin moved.

**The frozen interface.** `__init__.py` uses the PEP 562 lazy `__getattr__` idiom from
`tools/harness_config/__init__.py`, but backed by a `_SUBMODULE_OF` name → submodule map naming all
twelve exports of the whole phase: `compute`/`resolve`/`MissingSourceError` (digest, this plan),
`load_registry`/`RegistryError` (28-03), `load_ledger`/`previous_ledger`/`check_coherence`/
`LedgerError` (28-04), `classify`/`STATES` (guard) and `impact_ids` (impact) (28-05). The docstring
records that accessing a name whose submodule has not landed raises `ModuleNotFoundError` — a
transient, within-phase condition, and the deliberate price of keeping the wave conflict-free.
`__main__.py` defers its `cli` import inside `main()` for the same reason.

**The fixture.** `tests/conftest.py` provides `docs_repo`: a `tmp_path`-rooted real `git init` repo
with one commit over a seed tree (`docs/a.md`, `docs/nested/b.md`, `src/one.py`). Identity is passed
per-invocation via `-c user.email=... -c user.name=... -c commit.gpgsign=false` on fixed argv with
`shell=False`, so no global git config is read or written. It `pytest.skip`s with an explicit reason
when the `git` binary is absent — never a silent pass.

**The digest.** `resolve(selectors, root)` expands globs (literal selectors pass through even when
absent), drops directories, dedupes, resolve-then-confines, and returns the set sorted by POSIX
path. `compute(paths, root)` re-sorts defensively, then per path feeds the hash:

    label(path).encode("utf-8") + b"\n" + sha256(path.read_bytes()).hexdigest().encode("ascii") + b"\n"

`MissingSourceError` (a `ValueError`) is raised for any absent path, which is what lets the guard
classify `BROKEN` instead of reporting `FRESH` (research Q3). No §4.3-4.6 normalization runs before
hashing (D-03).

## RED evidence

`AMBIGUITY_CASES` and every property test were authored first, then run against a throwaway
`digest.py` whose `compute` was `approval.py:57-63` verbatim in shape (`digest.update(path.read_bytes())`
in a loop — no path, no separator). `resolve` was already the real one, isolating the RED to the
hashing algorithm.

Command (inverted form — exits 0 only when the selection FAILS; never piped, so the exit status is
pytest's own):

    ! uv run pytest tools/docs_guard/tests/test_digest.py -k ambiguity -q

Verbatim output (assertion bodies elided only where the four blocks repeat the identical source
listing; every failure line and both digests are reproduced exactly):

```
FFFF                                                                     [100%]
=================================== FAILURES ===================================
_______________ test_ambiguity_case_is_distinguished[byte_move] ________________

case = 'byte_move', tree_a = {'a.md': b'xy', 'b.md': b'z'}
tree_b = {'a.md': b'x', 'b.md': b'yz'}

        digest_a = _digest_of_tree(tmp_path / f"{case}_a", tree_a)
        digest_b = _digest_of_tree(tmp_path / f"{case}_b", tree_b)

>       assert digest_a != digest_b, (
            f"{case}: digests are equal but must differ — raw-byte concatenation "
            f"(approval.py:57-63) cannot see this change on a variable selector-expanded set"
        )
E       AssertionError: byte_move: digests are equal but must differ — raw-byte concatenation (approval.py:57-63) cannot see this change on a variable selector-expanded set
E       assert '3608bca1e44ea6c4d268eb6db02260269892c0b42b86bbf1e77a6fa16c3c9282' != '3608bca1e44ea6c4d268eb6db02260269892c0b42b86bbf1e77a6fa16c3c9282'

tools/docs_guard/tests/test_digest.py:65: AssertionError
____________ test_ambiguity_case_is_distinguished[empty_file_added] ____________

case = 'empty_file_added', tree_a = {'a.md': b'x'}
tree_b = {'a.md': b'x', 'b.md': b''}

E       AssertionError: empty_file_added: digests are equal but must differ — raw-byte concatenation (approval.py:57-63) cannot see this change on a variable selector-expanded set
E       assert '2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881' != '2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881'

tools/docs_guard/tests/test_digest.py:65: AssertionError
______________ test_ambiguity_case_is_distinguished[rename_only] _______________

case = 'rename_only', tree_a = {'a.md': b'x'}, tree_b = {'b.md': b'x'}

E       AssertionError: rename_only: digests are equal but must differ — raw-byte concatenation (approval.py:57-63) cannot see this change on a variable selector-expanded set
E       assert '2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881' != '2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881'

tools/docs_guard/tests/test_digest.py:65: AssertionError
___________ test_ambiguity_case_is_distinguished[split_across_files] ___________

case = 'split_across_files', tree_a = {'a.md': b'', 'b.md': b'xy'}
tree_b = {'a.md': b'xy', 'b.md': b''}

E       AssertionError: split_across_files: digests are equal but must differ — raw-byte concatenation (approval.py:57-63) cannot see this change on a variable selector-expanded set
E       assert '769a4e6d0003189c7e96c5d9b7e810a0d11c3a12832527ec94b0f86d277f51ca' != '769a4e6d0003189c7e96c5d9b7e810a0d11c3a12832527ec94b0f86d277f51ca'

tools/docs_guard/tests/test_digest.py:65: AssertionError
=========================== short test summary import ==========================
FAILED tools/docs_guard/tests/test_digest.py::test_ambiguity_case_is_distinguished[byte_move]
FAILED tools/docs_guard/tests/test_digest.py::test_ambiguity_case_is_distinguished[empty_file_added]
FAILED tools/docs_guard/tests/test_digest.py::test_ambiguity_case_is_distinguished[rename_only]
FAILED tools/docs_guard/tests/test_digest.py::test_ambiguity_case_is_distinguished[split_across_files]
4 failed, 8 deselected in 0.03s
```

Read the assertion lines, not just the FAILED count: **all four rows failed because the two digests
are byte-identical** (`assert 'X' != 'X'`), which is exactly the ambiguity the divergence exists to
remove — not a collection, import, or fixture error. Note also that `rename_only` and
`empty_file_added` produced the SAME digest as each other (`2d7116…`), and both equal
`sha256(b"x")` — the precedent algorithm cannot distinguish those two mutations from one another
either.

After replacing `compute` with the real algorithm, the same command GREENs:

```
....                                                                     [100%]
4 passed, 8 deselected in 0.01s
```

### A first RED attempt that did NOT count

The very first run of the inverted command exited 0, but for the wrong reason:

```
E   ModuleNotFoundError: No module named 'tools'
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

A collection error is not RED evidence — the inverted `!` would have happily accepted it. Fixed by
adding the repo-root `sys.path` wiring every virtual uv member's test conftest needs, and the RED
was re-run to the output above. Recorded here because accepting that first exit-0 would have been
precisely the anti-pattern this phase's fence exists to catch.

## Why the divergence is recorded in code, twice

Both mandatory comments are present in `digest.py` and are the point of the module:

1. **Above the hashing loop** (`digest.py`, the `── D-03: this DELIBERATELY diverges …` block):
   names `tools/adoption_apply/approval.py:57-63`, states that raw concatenation is safe THERE only
   because its input is the fixed 3-element `_DRAFT_FILES` tuple, lists the four mutations it cannot
   see on a variable selector-expanded set, names `AMBIGUITY_CASES` as the proof, and ends with
   "Do NOT 'simplify' this back toward the precedent."
2. **The no-normalization rationale** appears in the module docstring AND in `compute`'s own
   docstring: the digest is what a human ratifies in the ledger, so it must agree with `git diff`;
   `format-on-write` + `polyglot_lint` already hold the tree at LF / no-BOM, so a CRLF-only re-save
   is a real change and must not be silently absorbed.

## Gate Results

| Gate | Command | Result |
|------|---------|--------|
| Member registers, resolution stable | `uv sync --all-packages`; `git diff uv.lock` | PASS — "Resolved 58 packages"; 6 insertions, 0 deletions, only the `logparser-docs-guard` members line + virtual entry |
| Package imports, surface complete | `uv run python -c "import tools.docs_guard as d; print(sorted(d.__all__))"` | PASS — 12 names |
| Suite | `uv run pytest tools/docs_guard -q` | PASS — 12 passed |
| Ambiguity table GREEN | `uv run pytest tools/docs_guard/tests/test_digest.py -k ambiguity -q` | PASS — 4 passed, 8 deselected |
| No wall-clock / float in the digest | `grep -n 'datetime\|time\.\|float(' tools/docs_guard/digest.py` | PASS — no match (exit 1) |
| Root pyproject untouched (D-17) | `git status --porcelain pyproject.toml` | PASS — empty |
| Constitution/derived planes untouched | `git status --porcelain contracts docs/reference .memory/derived` | PASS — clean at commit time (see Concurrency below) |
| Lint + format | `uv run ruff check tools/docs_guard`; `ruff format --check` | PASS |
| Types | `uv run pyright tools/docs_guard` | PASS — 0 errors |
| No deletions in either commit | `git diff --diff-filter=D --name-only HEAD~1 HEAD` | PASS — empty for both |

The full suite, drift, emit and GEN-04 were deliberately NOT run as in-flight gates — plan 28-01 was
staging a constitution-plane commit in the same wave and 28-09 was editing `tools/adoption_apply/`.
That fan-in belongs to plan 28-08.

## Concurrency observations (not this plan's changes)

Mid-execution, `git status --porcelain contracts docs/reference .memory/derived` showed
`M .memory/derived/contracts-index.md`, `M contracts/.hashes/manifest.json`,
`?? contracts/harness/docs/`, `?? docs/reference/doc-dependencies.md` — plan 28-01's wave-1
constitution-plane work in flight. Nothing was staged, modified, or waited on; 28-01 committed it
independently and the tree was clean by this plan's final commit. `tools/adoption_apply/` (28-09)
was never read for write or touched.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing repo-root `sys.path` wiring in `tests/conftest.py`**
- **Found during:** Task 2, first RED run
- **Issue:** `from tools.docs_guard.digest import ...` raised `ModuleNotFoundError: No module named 'tools'` and pytest aborted at collection. docs_guard is a *virtual* member — it is never pip-installed, so nothing puts the repo root on `sys.path`. The first inverted RED command exited 0 on this error, which would have been false RED evidence.
- **Fix:** Added the `parents[3]` repo-root `sys.path.insert` block to `tools/docs_guard/tests/conftest.py`, mirroring `tools/adoption_scan/tests/conftest.py:26-28`, with a docstring line explaining why a virtual member needs it. RED then re-run and confirmed for the correct reason.
- **Files modified:** `tools/docs_guard/tests/conftest.py`
- **Commit:** `2dee9bb`

### Deliberate design choices beyond the plan's letter

**2. [Rule 2 - Correctness] `compute` takes `root` and hashes a RELATIVE label**
- **Issue:** The plan's algorithm sketch wrote `h.update(path.as_posix().encode("utf-8"))` against paths produced by `resolve`, which returns ABSOLUTE resolved paths. Hashing an absolute label makes the digest depend on the checkout location — every ledger digest committed from a developer machine would mismatch in CI, and `tmp_path`-based tests could never compare two trees at all.
- **Fix:** `compute(paths, root=None)`; when `root` is given each path is labelled relative to it. `root=None` preserves the plan's literal behaviour (label = the path as given). Documented in `compute`'s docstring.
- **Files modified:** `tools/docs_guard/digest.py`
- **Commit:** `c50f150`

**3. [Rule 2 - Security posture] Root-escape RAISES rather than skipping**
- **Issue:** `hash.py:60-63`, the cited model, silently `continue`s past an escaping symlink. For a manifest builder that is correct. For a review-obligation digest it is not: silently dropping a binding's file makes the digest stable across a real change and UNDER-reports staleness — a false-FRESH, the exact failure T-28-08 exists to prevent.
- **Fix:** `_confine` raises `ValueError` naming both the selector and the resolved target, before any `read_bytes()`. Rationale recorded in its docstring so the divergence from `hash.py` is not "fixed" either. `test_resolve_refuses_escape` and `test_resolve_refuses_symlink_pointing_outside` cover both shapes.
- **Files modified:** `tools/docs_guard/digest.py`
- **Commit:** `c50f150`

No architectural (Rule 4) decisions arose. No authentication gates. No package installs — the module
is stdlib-only (`hashlib`, `pathlib`, `subprocess` in the fixture), so the Package Legitimacy Gate
remained not-applicable as 28-RESEARCH.md recorded.

## Known Stubs

`tools/docs_guard/__init__.py` intentionally exports nine names whose submodules
(`registry`, `ledger`, `guard`, `impact`) do not exist yet, and `__main__.py` imports a `cli` module
that does not exist yet. These are **not** stubs in the misleading-value sense — nothing returns an
empty or placeholder value; access raises `ModuleNotFoundError` loudly. The surface is frozen in
wave 1 by explicit plan design (`must_haves` truth 2) so plans 28-03/04/05 add files without editing
this one. Resolved by: 28-03 (`registry`), 28-04 (`ledger`), 28-05 (`guard`, `impact`, `cli`).

## Threat Flags

None. The plan's `<threat_model>` covers every surface this plan introduced: T-28-06 (digest
ambiguity) is mitigated by the interleaved algorithm + `AMBIGUITY_CASES`; T-28-07 (path escape) by
`_confine`, raising rather than skipping; T-28-08 (missing source hashed as empty) by
`MissingSourceError`; T-28-09 (lock drift) by `dependencies = []` + the verified 6-line `uv.lock`
diff. No new network endpoint, auth path, or schema was introduced.

## Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 | `b32ce44` | `feat(28-02): scaffold tools/docs_guard uv member with frozen public surface` |
| 2 (RED) | `2dee9bb` | `test(28-02): add failing AMBIGUITY_CASES table for the docs_guard digest` |
| 2 (GREEN) | `c50f150` | `feat(28-02): implement the interleaved path+per-file-digest algorithm` |

No REFACTOR commit — the GREEN implementation needed no cleanup pass.
