---
phase: 26-deterministic-brownfield-inventory-mapping-v2-3-b
reviewed: 2026-07-19T12:50:03Z
depth: deep
files_reviewed: 22
files_reviewed_list:
  - tools/adoption_scan/__init__.py
  - tools/adoption_scan/__main__.py
  - tools/adoption_scan/cli.py
  - tools/adoption_scan/destinations.py
  - tools/adoption_scan/detect.py
  - tools/adoption_scan/plan.py
  - tools/adoption_scan/pyproject.toml
  - tools/adoption_scan/scan.py
  - tools/adoption_scan/tests/__init__.py
  - tools/adoption_scan/tests/conftest.py
  - tools/adoption_scan/tests/test_detect.py
  - tools/adoption_scan/tests/test_determinism.py
  - tools/adoption_scan/tests/test_dispositions.py
  - tools/adoption_scan/tests/test_inventory_determinism.py
  - tools/adoption_scan/tests/test_plan_classification.py
  - tools/adoption_scan/tests/test_readonly.py
  - tools/adoption_scan/tests/test_scan_exclusions.py
  - tools/adoption_scan/tests/test_schema_conformance.py
  - tools/adoption_scan/tests/test_snapshots.py
  - contracts/harness/adoption/inventory.schema.json
  - contracts/harness/adoption/manifest.schema.json
  - contracts/harness/adoption/plan.schema.json
findings:
  critical: 1
  warning: 3
  info: 2
  total: 6
status: fixed
fixed_at: 2026-07-19T13:15:00Z
fix_summary:
  CR-01: resolved
  WR-01: resolved
  WR-02: resolved
  WR-03: resolved
  IN-01: deferred
  IN-02: deferred
---

# Phase 26: Code Review Report

**Reviewed:** 2026-07-19T12:50:03Z
**Depth:** deep
**Files Reviewed:** 22 (plus cross-referenced `tools/harness_perms/resolver.py`, `tools/hooks/contract_guard.py`, `tools/harness_emit/manifest.py`, `contracts/harness/topology/relationship.schema.json`, `contracts/harness/task-control/gate-registry.json`)
**Status:** fixed (2026-07-19T13:15:00Z) — see "Fix Status" section below. `status: issues_found` at
review time; all BLOCKER + WARNING findings resolved post-review, repo owner deferred both INFOs.

## Summary

`tools/adoption_scan/{scan,detect}.py` (ADOPT-01) are sound: the read-only/confinement guarantee
holds (verified empirically — `pathlib.Path.rglob` and `git ls-files` both refuse to descend into
symlinked directories on this Python/git, so the only escape vector is a symlink leaf, which is
caught by `classify_exclusions` step 0 before any `open()`), secret patterns are read as data from
`gate-registry.json` (never duplicated), D-10 non-leak is enforced structurally (excluded entries
carry no `sha256`/excerpt field in the schema at all) and independently unit-tested, and the D-05
never-invented-authority guard for relationship candidates is structurally sound (a partial
candidate can never validate against `relationship.schema.json` because it omits the required
`authority` key).

However, **ADOPT-03's core disposition rule — the entire reason the manifest exists — is dead code
in the actual CLI/pipeline path.** `cli.py` (and the pipeline test helper in
`test_determinism.py::_pipeline_bytes`) build the "proposed content" hash map straight from the
scanned target's own `inventory["included"]`, keyed by the same relative path used as the catalog
`destination`. Since `destinations.disposition()` then re-reads and re-hashes that exact same file
from the same target tree to compare against that same hash, the comparison is a file against
itself: `preserve` fires trivially for every already-present, non-excluded destination, and
`conflict` can never fire through the real CLI. See CR-01 below — this is a BLOCKER because the
disposition manifest is the artifact Phase 27 uses to decide what is safe to auto-apply vs. what
requires human ratification; as shipped, it will systematically under-report conflicts.

Two further WARNINGs concern classification fidelity (all AGENTS.md files and all README files
in a repo are collapsed into one `surfaceRecord`/one question, losing per-file resolution the
CONTEXT explicitly calls out as required — "root + nested AGENTS destinations") and a fragile
generated-content heuristic (`"derived —"`) likely to false-positive on ordinary prose. See below
for details and file:line citations.

## Fix Status

Fixed post-review by `gsd-code-fixer`, 2026-07-19T13:15:00Z. Repo owner approved fixing the
BLOCKER and all three WARNINGs; both INFO findings were deliberately deferred (low-priority,
non-negotiable list did not require them).

| ID | Severity | Status | Commit(s) |
|----|----------|--------|-----------|
| CR-01 | Critical | **resolved** | `ec2322b` |
| WR-01 | Warning | **resolved** | `517bec3`, `11fac25` |
| WR-02 | Warning | **resolved** | `f9a6624` |
| WR-03 | Warning | **resolved** | `ec2322b` (same commit as CR-01 — both fixes live in `destinations.py`'s disposition-resolution chain) |
| IN-01 | Info | deferred | — (redundant-but-harmless `SECRET_PATH_GLOBS` entry; not in fix scope) |
| IN-02 | Info | deferred | — (UX/quality dedup of overlapping `test-command` questions; not in fix scope) |

**CR-01** — `proposed_hashes` in `cli.py` (and the two test-helper duplicates in
`test_determinism.py`/`test_snapshots.py`) no longer derive "proposed" content from the scanned
target's own inventory. `destinations.harness_proposed_hash()`/`harness_proposed_hashes()` hash
THIS harness checkout's own file at each catalog destination's relative path instead — a source
genuinely independent of the target. A catalog row with no shippable template content in this
checkout (a fixture placeholder such as `harness/agents/widget-engineer.md`, or a per-instance file
such as `.workflow/tasks/T-0001/task.json`) now yields `proposed_sha=None`; since `None` can never
equal a real sha256 digest, an existing target file at that destination honestly resolves to
`conflict` (forces human review) rather than a silently-invented `preserve`. Verified end-to-end
through the real `cli.main()` pipeline (`test_cr01_conflict_reachable_through_real_cli`,
`test_cr01_repro_throwaway_junk_target`) and via the reviewer's own exact repro (see Verification
below) — `conflict` now fires.

**WR-01** — `detect.py::detect_documentation_surfaces` now emits one `surfaceRecord` per distinct
`AGENTS.md` path (root AND every nested one), `target` = the file's real path, not the fixed
literal `"AGENTS.md"`. `plan.py::classify` matches `agents-boundary` by filename
(`PurePosixPath(target).name == "AGENTS.md"`) instead of exact-string-equality, so every nested
AGENTS.md still resolves to its own `agents-boundary` proposal and its own question. README stays
intentionally coarse-grained per the review's own stated acceptable-alternative.

**WR-02** — `scan.py`'s `_GENERATED_MARKERS` no longer contains the bare `"derived —"` substring.
It is anchored to this repo's actual generator convention: every real `DERIVED_HEADER` in this
repo (`tools/docs_sync/generate.py`, `tools/memory_regen/{pointer_index,repo_map,contracts_index}.py`)
reads `"DERIVED — do not hand-edit ..."`, so the marker is now `"derived — do not"` — still catches
every real generated-file convention in this repo, no longer false-positives on ordinary prose
using the word "derived" followed by an em-dash (e.g. `.opencode/skill/two-plane-memory/SKILL.md`'s
"Gitignored-derived — `.memory/derived/...`"). D-06 fixture (case (e), `@generated` marker) was
never dependent on `"derived —"` and remains unaffected/unregressed.

**WR-03** — `destinations.disposition()`'s existing-file hash comparison no longer unconditionally
re-reads the target file via `_existing_hash()` in the real pipeline. `build_manifest()` now passes
an `existing_sha` hint sourced from the same scan's already-computed inventory: the already-hashed
`sha256` when the destination was `included` (no double I/O, respects the scan's size cap/binary
check), or a non-hex sentinel that can never match a real sha256 when the destination was
`excluded` (binary/oversized/secret/etc. — never re-opened). `_existing_hash()` remains as a
fallback only for a destination path the scan never encountered at all (rare for a correctly-wired
pipeline) and is reused for `harness_proposed_hash()`'s bounded, self-controlled reads of this
repo's own files.

### Verification (definition of done)

- **Full test suite:** `uv run pytest -q` → `1010 passed` (1003 baseline + 7 new regression tests
  added by the fixes: `test_harness_proposed_hash_independent_of_target`,
  `test_cr01_conflict_reachable_through_real_cli`, `test_cr01_repro_throwaway_junk_target`,
  `test_root_and_nested_agents_md_get_per_file_surface_records`,
  `test_nested_agents_md_gets_its_own_agents_boundary_proposal`,
  `test_derived_marker_does_not_false_positive_on_ordinary_prose`,
  `test_derived_marker_still_catches_real_generated_headers`). Tree clean.
- **Contract drift:** `uv run python -m tools.contract_drift.drift` → `contract-drift: OK — live
  manifest matches the committed baseline.` (no schema/contract touched by these fixes).
- **CR-01 repro (verbatim, re-run against the fixed code):** a throwaway target with a junk
  `pyproject.toml` + junk `.gitignore` bearing no resemblance to the harness template, scanned via
  `uv run python -m tools.adoption_scan --target <dir> --out <outdir>`, now reports:
  ```
  .gitignore     -> conflict
  pyproject.toml -> conflict
  any conflict? True
  ```
  (previously both `preserve`, `any conflict? False`).
- **Determinism:** the CLI was run twice into separate output directories over the same target;
  `manifest.json` bytes were identical across both runs (`diff` empty).
- **Read-only:** the throwaway target directory's files carry no mtime change after two scans
  (`find <target> -newer <target>/.gitignore` empty).
- **Snapshot update:** `tools/adoption_scan/tests/__snapshots__/test_snapshots.ambr` updated —
  `git diff` confirmed exactly two hunks changed (`.github/workflows/ci.yml` and `pyproject.toml`
  in the manifest section, both `preserve` -> `conflict`, matching the fixture's genuinely-differing
  content vs. this harness's own template content at those paths), no unrelated hunks swept in.
- **Constitution plane:** no write to `contracts/`, `docs/adr/`, or `golden/`; `GOLDEN_APPROVE_HUMAN`
  was never set or fabricated.

## Critical Issues

### CR-01: Disposition manifest's collision rule (`preserve` vs `conflict`) is unreachable through the real CLI — the manifest self-compares every already-present file to itself

**File:** `tools/adoption_scan/cli.py:73-74`, `tools/adoption_scan/destinations.py:260-286`, also duplicated in `tools/adoption_scan/tests/test_determinism.py:31-32`

**Issue:** D-03/D-04 require: "content-equal → `preserve`, content-different → `conflict`." The
`proposed_sha` that `disposition()` compares against is supposed to represent *what the harness
would write* at a given destination. Instead:

```python
# cli.py:73
proposed_hashes = {entry["path"]: entry["sha256"] for entry in inventory["included"]}
# ...
manifest_doc = destinations.build_manifest(inventory, target_resolved, proposed_hashes)
```

`inventory["included"]` is built entirely from files inside the **scanned target** (`scan.py`'s
`build_inventory`) — there is no second, harness-side content source anywhere in this pipeline.
When `destinations.disposition()` runs its step 6/7:

```python
# destinations.py:281-286
existing = Path(target_root) / rel
if not existing.exists():
    return "create"
if _existing_hash(existing) == proposed_sha:
    return "preserve"
return "conflict"
```

`target_root` is the same scanned target, and `proposed_sha = proposed_hashes.get(rel)` was itself
derived from hashing that same file during the scan. For every catalog `destination` that
coincides with a path the target already has (and that path was not excluded, e.g. `pyproject.toml`
row 36, `.gitignore` row 39, `.github/CODEOWNERS` row 33, `.github/workflows/ci.yml` row 34,
`workspace.toml` row 17, `harness/opencode.json` row 20), the code is comparing a file's hash to
itself — mathematically guaranteed equal — so `disposition()` **always** returns `preserve` for
that row, never `conflict`, regardless of what the harness's own template content at that
destination actually looks like. `conflict` is only reachable when the target's file exists but
was *excluded* from the scan (binary/secret/vendored/oversize) — a narrow, incidental case, not the
"content differs" case the rule exists to catch.

This defeats the entire purpose of the collision rule for the realistic, common rows (any
top-level config/manifest file a target repo already has under the same name a harness destination
uses). A brownfield target's own, unrelated `pyproject.toml`/`.gitignore`/CI workflow will always be
reported `preserve` (safe no-op) even though installing the harness's actual template content there
would in fact overwrite/collide with it. Since Phase 27 (per `26-03-SUMMARY.md` "Integration
Points") consumes this manifest to drive "safe-apply" and the constitution-plane refusal, a
mis-reported `preserve` where a real `conflict` exists means Phase 27 could silently treat an
overwrite-worthy file as already-safe.

Note the unit tests in `test_dispositions.py` never catch this because they call
`destinations.disposition()` directly with hand-constructed `proposed_sha` values (e.g.
`test_collision_rule` deliberately hashes a *different* file, `widget_a_modified.py`, as the
"proposed" content) — they never exercise the real `cli.py`/`_pipeline_bytes` wiring that produces
`proposed_hashes` from the target's own scan. `test_all_three_artifacts_validate` only checks
schema conformance, not semantic correctness, so this bug is fully hidden from the test suite.

**Fix:** The "proposed" content for a destination must come from a source independent of the
scanned target — e.g. the harness's own repo content at that same relative path
(`_REPO_ROOT / destination`, when it exists), or an explicit, harness-supplied content/hash map
passed into `build_manifest()`. At minimum, `proposed_hashes` must never be derived from
`inventory["included"]` keyed by the *same* path used as the destination for hash comparison
purposes — that construction is definitionally self-referential. A minimal fix:

```python
# destinations.py — read the harness's OWN template content for a destination, not the target's.
def _harness_proposed_hash(destination: str) -> str | None:
    candidate = _REPO_ROOT / destination
    if not candidate.is_file():
        return None
    return _existing_hash(candidate)
```
and wire `build_manifest()` to call this instead of accepting a `proposed_hashes` map built from
the scanned target. Add a regression test that plants a target file with *different* content than
the harness's real file at the same relative path (e.g. a target `.gitignore` with different
contents than this repo's own `.gitignore`) and asserts `disposition()` returns `conflict` through
the real `cli.main()` invocation — not just through a hand-fed `disposition()` call.

## Warnings

### WR-01: All `AGENTS.md` files (root + every nested one) collapse into a single surface/proposal/question, losing per-file resolution the phase context requires

**File:** `tools/adoption_scan/detect.py:118-143` (`detect_documentation_surfaces`), consumed by `tools/adoption_scan/plan.py:138-148`

**Issue:** `detect_documentation_surfaces` builds ONE `surfaceRecord` for ALL files named
`AGENTS.md` anywhere in the target (`target="AGENTS.md"`, a fixed literal label, not a path) and
similarly ONE record for ALL `README`/`README.md` files repo-wide:

```python
agents_entries = [entry for entry in included if PurePosixPath(entry["path"]).name == "AGENTS.md"]
if agents_entries:
    records.append(_surface("AGENTS.md", agents_entries, "observed"))
```

`plan.classify()` then emits exactly one `agents-boundary` proposal (`id="agents-boundary/AGENTS.md"`)
whose `evidence` is the union of every AGENTS.md file in the target, and `generate_questions()`
emits exactly one question ("Is the existing AGENTS.md at 'AGENTS.md' nearest-wins-correct?") for
all of them combined. `26-CONTEXT.md`'s canonical_refs explicitly calls out that "the manifest
proposes root/nested AGENTS destinations" and ADOPT-02 requires "every proposed ... AGENTS
boundary classified ... with source evidence" — nearest-wins AGENTS.md semantics are inherently
per-directory (a root AGENTS.md and `libs/python/AGENTS.md` are different boundaries with
potentially different answers), so a target with N nested AGENTS.md files gets exactly one
lumped, unresolvable-per-file question instead of N. Same collapse applies to README.

**Fix:** Emit one `surfaceRecord` per distinct AGENTS.md path (`target=entry["path"]`, not the
fixed string `"AGENTS.md"`), so each nested AGENTS.md gets its own proposal/question with its own
evidence pointer. README can stay coarse-grained if that is an intentional design choice, but
AGENTS.md boundaries should not be merged given the explicit nearest-wins semantics this repo
already documents.

### WR-02: `_GENERATED_MARKERS` includes the overly broad heuristic `"derived —"`, likely to false-positive on ordinary human-authored prose

**File:** `tools/adoption_scan/scan.py:81`, `scan.py:236-240`

**Issue:** `_GENERATED_MARKERS = ("@generated", "auto-generated", "derived —")` is checked
case-insensitively as a substring anywhere in the first 2048 bytes of any text file under the size
cap. Unlike `"@generated"` or the repomix banner strings (rare, specific, deliberately
machine-authored markers), `"derived —"` is just the common word "derived" followed by an
em-dash — a pattern that occurs in ordinary prose documentation completely unrelated to
machine-generation. This repo's own docs already use this exact phrasing non-generically, e.g.
`.opencode/skill/two-plane-memory/SKILL.md:40`: `"**Gitignored-derived — `.memory/derived/...`**"`.
Any brownfield target whose README/docs happen to use similar phrasing within the first 2 KiB will
be silently excluded from the inventory as `"generated"`, with no error or warning surfaced — a
correctness regression for a heuristic that was added ad hoc beyond the plan's literal spec (see
`26-02-SUMMARY.md` Deviation 1) to satisfy one narrow fixture case, not sourced from
26-RESEARCH.md's documented marker list.

**Fix:** Narrow the marker to the pattern the fixture and research actually require (e.g. a
line-anchored `"# @generated"`/`"// @generated"` style check, or drop `"derived —"` entirely and
rely on `"@generated"`/`"auto-generated"` plus the D-08 banner markers, which are already
sufficiently specific). If a third marker is genuinely needed, anchor it more precisely (e.g.
require it as the first line, mirroring the `(e)` fixture's actual shape: `"# @generated"` at file
start) rather than an unanchored substring match.

### WR-03: `destinations._existing_hash()` bypasses `scan.py`'s exclusion machinery entirely — reads and hashes any existing file at a catalog destination with no size cap, no binary check, independent of how the scanner classified that same path

**File:** `tools/adoption_scan/destinations.py:252-257`, `destinations.py:284`

**Issue:** `disposition()`'s hash-equality step re-reads `target_root / rel` directly off disk via
`_existing_hash()`, completely independent of `classify_exclusions()` — there is no size cap, no
binary/NUL check, and no re-use of the already-computed hash from the inventory when one exists
(the inventory's `included[].sha256` for the same path, when present, is silently ignored in favor
of a second independent read). This is not currently exploitable as an information leak (only a
sha256 digest is used internally and never emitted into the manifest — `dispositionRecord` never
populates `evidence`), but it is a correctness/robustness gap: an oversized or binary file that
happens to sit at one of the 40 catalog destination paths in the target is hashed unconditionally,
in contrast to every other read in this codebase which is explicitly bounded and cap-aware. It also
duplicates the hash computation `scan._file_hash()` already performed for the same file when it
was `included`, doing the I/O twice with two different implementations that must be kept in sync.

**Fix:** When `rel` is present in `inventory["included"]`, reuse that entry's `sha256` directly
instead of re-reading the file; only fall back to `_existing_hash()` for destinations that are not
part of the already-scanned `included` set (which, given CR-01's fix, should be rare/never for a
correctly-wired pipeline). This also closes the redundant-I/O and cap-bypass gap in one change.

## Info

### IN-01: `SECRET_PATH_GLOBS` contains a redundant entry — `"*.env"` already matches nested paths under `fnmatch` semantics, making `"**/*.env"` dead weight

**File:** `tools/adoption_scan/scan.py:54`

**Issue:** `resolve_path()` (`tools/harness_perms/resolver.py:52-54`) uses `fnmatchcase`, whose `*`
matches any sequence of characters including `/` (fnmatch has no path-aware `**` semantics the way
`pathlib.glob`/`git` do). This means `"*.env"` alone already matches `"sink/.env"`, `"a/b/c/.env"`,
etc., making the explicit `"**/*.env"` entry redundant (it matches an identical, strictly smaller
set of strings than `"*.env"` already covers). Not a functional bug — just noise that could mislead
a future maintainer into believing `fnmatch`-based path matching has real recursive-glob semantics
it does not have.

**Fix:** Drop `"**/*.env"` from `SECRET_PATH_GLOBS`, or add a one-line comment noting `fnmatch`'s
`*` already spans path separators so `**` adds nothing here (to prevent a future contributor from
"fixing" the apparent gap by adding more `**/` variants of every other glob).

### IN-02: `ci_surfaces` and `test_surfaces` can each independently ask "which command is canonical" for the same target repo, with no de-duplication across the two signal sources

**File:** `tools/adoption_scan/plan.py:150-170`

**Issue:** A target with both a `.github/workflows/*.yml` CI surface and a `tests/test_*.py` test
surface produces two separate `test-command` proposals/questions (`target=".github/workflows"` and
`target="tests"`), each asking a variant of "what is the canonical test command." This is
functionally correct (distinct targets, distinct stable ids, no schema violation) but is a minor
UX/quality gap for Phase 27's human-ratification consumers, who will see two overlapping questions
about what is effectively one canonical-test-command decision.

**Fix:** Consider consolidating CI-surface and test-surface signal into one `test-command` proposal
per repo (or per detected component root) when both fire, so Phase 27 surfaces one question instead
of two near-duplicates. Not required for correctness; low priority.

---

_Reviewed: 2026-07-19T12:50:03Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
