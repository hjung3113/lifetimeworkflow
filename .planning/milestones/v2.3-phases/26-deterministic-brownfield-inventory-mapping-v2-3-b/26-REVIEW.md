---
phase: 26-deterministic-brownfield-inventory-mapping-v2-3-b
reviewed: 2026-07-19T16:35:26Z
depth: standard
files_reviewed: 18
files_reviewed_list:
  - tools/adoption_scan/destinations.py
  - tools/adoption_scan/detect.py
  - tools/adoption_scan/plan.py
  - tools/adoption_scan/scan.py
  - tools/adoption_scan/tests/conftest.py
  - tools/adoption_scan/tests/test_detect.py
  - tools/adoption_scan/tests/test_dispositions.py
  - tools/adoption_scan/tests/test_plan_classification.py
  - tools/adoption_scan/tests/__snapshots__/test_snapshots.ambr
  - contracts/harness/adoption/inventory.schema.json
  - contracts/harness/adoption/plan.schema.json
  - contracts/.hashes/manifest.json
  - docs/reference/inventory.md
  - docs/reference/plan.md
  - .memory/derived/contracts-index.md
  - tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr
  - tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr
findings:
  critical: 3
  warning: 11
  info: 4
  total: 18
status: issues_found
---

# Phase 26: Code Review Report (GAP-CLOSURE scope)

**Reviewed:** 2026-07-19T16:35:26Z
**Depth:** standard
**Files Reviewed:** 18
**Status:** issues_found

## Scope

This report **replaces** the previous `26-REVIEW.md` and is scoped to the phase-26
**gap-closure** work only — plans **26-04, 26-05, 26-06**, commits `45f9c1f..22b7342`
(`45f9c1f`, `61c2959`, `d488c79`, `eda1fdd`, `2058a2e`, `57db1ac`, `9c87a2b`, plus the three
`docs(26-0x)` summary commits). The prior report covered plans 26-01..03; its CR-01 / WR-01..03
findings were already resolved and are **not** re-litigated here (their fix commentary in
`destinations.py` is, however, itself a finding — see WR-09).

## Summary

The gap-closure work does what it set out to do on the surface: `inventory.schema.json` grew
`schema_surfaces` + `codeowners_surfaces` (staged optional → required), `detect.py` populates both,
`plan.py` wires the `codeowners-ownership` question, and `destination_catalog()` was rewritten from
a curated 40-row sample into a rule-derived enumeration. Contract-first hygiene at HEAD is clean:
`contracts/.hashes/manifest.json` recomputes byte-identical against
`tools.contract_hash.hash.build_manifest()`, and `docs/reference/{inventory,plan}.md`,
`.memory/derived/contracts-index.md`, and both `docs_sync`/`memory_regen` `.ambr` snapshots are
consistent with the schema text. The 58-test `tools/adoption_scan` suite passes **on this
developer's working tree**.

That last qualifier is the problem. The central design decision of plan 26-06 — deriving the
authoritative destination catalog from a live `Path.glob()` of the harness checkout, then freezing
the result into a committed 1859-line syrupy snapshot — makes the test suite a function of the
*untracked, gitignored* state of the working tree. I reproduced a clean `git clone` at `22b7342`:
the catalog yields **341** rows there versus the **344** baked into
`tools/adoption_scan/tests/__snapshots__/test_snapshots.ambr`. The CI `core-suite` job
(`actions/checkout` → `uv sync` → `uv run pytest`, `.github/workflows/ci.yml:170-178`) runs exactly
that clean-checkout shape. This is a hard red, not a theoretical risk (CR-01), and the same
mechanism makes the snapshot break on essentially any future file added anywhere under
`contracts/`, `docs/`, `harness/`, `.opencode/`, `.claude/`, or `.github/workflows/` (CR-02).

Separately, the two contracts touched this phase now contradict each other on evidence cardinality:
`inventory.schema.json` explicitly permits `surfaceRecord.evidence` to be empty ("May be empty for
an unknown/absent surface"), while `plan.schema.json` requires `minItems: 1` on both
`proposalRecord.evidence` and `questionRecord.evidence`. A schema-valid inventory therefore makes
`cli.main()` exit 1 with no artifacts written (CR-03, reproduced).

The GEN-04 workaround asked about in the review brief is **correct at the letter but wrong at the
intent**: `_INSTANCE_DIR_NAME = "examples"` plus `"examples" + "/"` in the test file evade the guard's
`_PATH_TOKENS = ("examples/", ...)` substring scan rather than being exempted by it, and they
hardcode a value that `harness/project.toml`'s `[instance] root` slot (currently `""`) is supposed to
own. See WR-01.

---

## Critical Issues

### CR-01: Committed snapshot encodes three gitignored files — `test_artifacts_match_committed_snapshot` fails on any clean checkout (CI red)

**File:** `tools/adoption_scan/destinations.py:182-216`, `tools/adoption_scan/tests/__snapshots__/test_snapshots.ambr:673-685`

**Issue:** `destination_catalog()` enumerates the live filesystem with no reference to git tracking
state. `_CATEGORY_GLOBS` includes `.memory/derived/**/*`, but `.gitignore:20-25` ignores
`.memory/derived/*` with a single re-include for `contracts-index.md`. On this working tree the
generated `.memory/derived/{pointer-index.json, pointer-index.md, repo-map.md}` exist, so they were
captured into the committed snapshot at `9c87a2b`.

Reproduced against a clean clone of `22b7342`:

```
clean-checkout catalog rows: 341        (working tree: 344)
in snapshot but missing from clean catalog:
  ['.memory/derived/pointer-index.json',
   '.memory/derived/pointer-index.md',
   '.memory/derived/repo-map.md']
```

CI `core-suite` (`.github/workflows/ci.yml:170-178`) is `actions/checkout@v7` →
`uv sync --all-packages` → `uv run pytest`, with no `tools.memory_regen` step. The manifest section
of the snapshot will therefore differ by three `dispositions[]` entries and the test fails. This is
the exact "derived files are machine-generated and must not be hand-carried" invariant the project's
two-plane rule exists to prevent, inverted: an ignored derived artifact has been frozen into a
committed test baseline.

**Fix:** Do not let untracked/ignored content into the catalog. Scope the enumeration to
git-tracked files (the repo already uses this idiom in
`tools/harness_lint/tests/test_core_no_example_dep.py::_tracked_core_files`), or at minimum apply an
explicit ignore-aware filter:

```python
import subprocess

def _tracked() -> frozenset[str]:
    proc = subprocess.run(
        ["git", "-C", str(_REPO_ROOT), "ls-files"],
        capture_output=True, check=False, shell=False,
    )
    if proc.returncode != 0:
        return frozenset()  # caller falls back to unfiltered glob
    return frozenset(proc.stdout.decode("utf-8", "surrogateescape").splitlines())

# inside destination_catalog(), after computing `destination`:
if tracked and destination not in tracked:
    continue
```

Then regenerate the snapshot (`--snapshot-update`) and confirm the row count matches a fresh clone.

---

### CR-02: The committed snapshot pins 344 live repo paths — every future harness file add/remove reds the suite

**File:** `tools/adoption_scan/tests/test_snapshots.py:11-26`, `tools/adoption_scan/tests/__snapshots__/test_snapshots.ambr` (1859 lines, 344 `"destination"` entries)

**Issue:** `test_artifacts_match_committed_snapshot` renders `build_manifest(...)` over the *live*
`destination_catalog()` and asserts byte-equality against a committed baseline. Current composition:
`.claude` 143, `harness` 56, `.opencode` 48, `docs` 31, `tools` 25, `contracts` 15, `.memory` 9,
`libs` 7, `golden` 4. Adding a single how-to page, a new ADR, one emitted `.opencode/` artifact, or
one new schema mechanically breaks this test in a phase that has nothing to do with adoption
scanning. The snapshot was intended (per its own docstring) as an "anti-`git diff`-trap determinism
proof" over the **D-06 synthetic mini-repo fixture**; commit `9c87a2b` (+1277 lines) silently
converted it into a whole-repo inventory assertion. Note also that `2058a2e` changed the catalog and
left the snapshot stale for two commits — the suite was already red mid-phase.

**Fix:** Split the concerns. Keep the fixture-derived snapshot (inventory + plan, and a manifest
computed over a **small fixed** catalog injected for the test) as the determinism proof, and assert
the live catalog only through the structural/property tests that already exist
(`test_catalog_covers_real_contract_schemas`, `test_catalog_covers_real_nested_agents_md`,
`test_workflow_tasks_excluded`, `test_catalog_deterministic_across_calls`). Concretely, give
`build_manifest` an injectable catalog:

```python
def build_manifest(inventory, target_root, proposed_hashes, *, catalog=None) -> dict:
    rows = destination_catalog() if catalog is None else catalog
    ...
```

and have the snapshot test pass a fixed, hand-listed `catalog` so the baseline is stable under
unrelated repo growth.

---

### CR-03: `inventory.schema.json` and `plan.schema.json` disagree on evidence cardinality — a schema-valid inventory hard-fails the CLI

**File:** `contracts/harness/adoption/inventory.schema.json:185-190`, `contracts/harness/adoption/plan.schema.json:70-74` and `:170-173`, `tools/adoption_scan/plan.py:140-193`

**Issue:** `inventory.schema.json`'s `surfaceRecord.evidence` is declared `"minItems": 0` with the
description *"May be empty for an unknown/absent surface."* — an explicitly sanctioned shape.
`plan.py::classify` copies `entry["evidence"]` verbatim into a `proposalRecord`, and
`generate_questions` copies it again into a `questionRecord`; both of those defs require
`"minItems": 1`. Reproduced:

```python
inv = {"target_ref": "x", "codeowners_surfaces":
       [{"target": ".github/CODEOWNERS", "classification": "observed", "evidence": []}]}
Draft202012Validator(plan_schema).iter_errors(plan.build_plan(inv))
# -> ['[] should be non-empty', '[] should be non-empty']
```

Through `cli.main()` that path returns exit code 1 with the message
`adoption_scan: plan.json failed schema validation: [] should be non-empty` and **no artifacts
written at all** — inventory and manifest are discarded too, because validation runs before any
write. This is latent only because today's `detect.py` returns `[]` (no record) rather than a record
with empty evidence; the gap-closure commits added two new surface producers against a contract that
permits the failing shape. The contract is the single source of truth here, so the contradiction is a
contract defect, not merely a code one.

**Fix:** Pick one and make both contracts agree. Preferred (matches actual producer behavior — a
surface with no evidence is never emitted):

```json
"evidence": {
  "type": "array",
  "minItems": 1,
  "items": { "$ref": "#/$defs/evidenceRef" },
  "description": "Evidence pointers into already-hashed includedEntry records; a surface with no evidence is not emitted."
}
```

in `inventory.schema.json`'s `surfaceRecord`. Rebaseline `contracts/.hashes/manifest.json`, rerun
`tools.docs_sync` + `tools.memory_regen.contracts_index`, and refresh both derived `.ambr`
snapshots in the same commit (see WR-10). Add a regression test asserting
`build_plan(inventory)` validates for every surface array permitted by the inventory schema.

---

## Warnings

### WR-01: GEN-04 instance exclusion hardcodes `"examples"` and evades the guard instead of using the sanctioned `[instance] root` slot

**File:** `tools/adoption_scan/destinations.py:173-179` and `:211`, `tools/adoption_scan/tests/test_dispositions.py:188` and `:221`

**Issue:** The guard (`tools/harness_lint/tests/test_core_no_example_dep.py`) forbids the literal
substring `"examples/"` in core files, and exempts exactly one thing: the `root =` / `persona =` /
`test_paths =` pointer lines in `harness/project.toml` (ADR-0002 (c)). `destinations.py` instead
splits the token (`_INSTANCE_DIR_NAME = "examples"`, matched against `parts[0]`) and the test does
`instance_prefix = "examples" + "/"`. That is token evasion: the guard's scan passes, but the file
now carries an unmanaged hardcode of an instance-root name that the harness explicitly models as
configurable data. `harness/project.toml` currently declares `[instance] root = ""`, and its comment
states a downstream project "overrides `root`". For any vendored harness whose instance root is not
literally `examples`, `destination_catalog()` will enumerate that instance's tree into the core
destination catalog — a runtime GEN-04 violation with no test that would catch it. The correctness of
the workaround therefore depends on a value the config says may change.

**Fix:** Read the sanctioned slot instead of hardcoding, via the existing loader:

```python
from tools.harness_config.loader import load_project_config  # or the equivalent accessor

def _instance_root_segment() -> str | None:
    root = (load_project_config().instance_root or "").strip("/")
    return root.split("/", 1)[0] if root else None
```

and skip `parts[0] == _instance_root_segment()`. Keep the literal-free property by construction
(the token comes from data, not source). Add a test that a configured non-`examples` instance root
is excluded.

### WR-02: `destination_catalog()` has no vendored/cache denylist — `**/pyproject.toml` and `**/AGENTS.md` descend into `.venv`, `node_modules`, `__pycache__`

**File:** `tools/adoption_scan/destinations.py:127-167`, `:200-216`

**Issue:** `scan.py` carefully maintains `_VENDOR_SEGMENTS` / `_GENERATED_SEGMENTS`
(`scan.py:57-75`) precisely because a naive walk picks up dependency trees. `destinations.py`, added
in the same phase, reuses none of it: the two `**/` globs walk the entire checkout. CI runs
`uv sync --all-packages` — creating `.venv/` **inside the repo** — before `uv run pytest`. Today
`find .venv -name pyproject.toml` returns 0 hits, so the catalog is accidentally clean; that is
dependency-version luck, and a single wheel that ships a `pyproject.toml` in `site-packages` would
inject rows into the "authoritative harness destination catalog" and break the snapshot.

**Fix:** Reuse the existing constants rather than re-deriving them:

```python
from tools.adoption_scan.scan import _GENERATED_SEGMENTS, _VENDOR_SEGMENTS

_SKIP_SEGMENTS = _VENDOR_SEGMENTS | _GENERATED_SEGMENTS

# in destination_catalog(), after `parts = destination.split("/")`:
if any(seg in _SKIP_SEGMENTS for seg in parts):
    continue
```

(If CR-01 is fixed by restricting to git-tracked files, this becomes belt-and-suspenders — keep it
anyway, since the git path falls back to an unfiltered glob when git is unavailable.)

### WR-03: The catalog installs 25 workspace-member `pyproject.toml` files with none of their source

**File:** `tools/adoption_scan/destinations.py:162-163`

**Issue:** `"pyproject.toml"` + `"**/pyproject.toml"` drag in 25 rows — `pyproject.toml`,
`libs/python/pyproject.toml`, and 23 `tools/<pkg>/pyproject.toml`. The catalog is documented as
"every REAL file in THIS harness checkout matching one of the named destination categories", i.e.
what the template would install into a brownfield target. But no `tools/**/*.py` category exists, so
the catalog proposes writing 23 uv workspace-member manifests whose packages do not exist at the
destination — a target that accepted the whole catalog would get a `workspace.toml` +
`pyproject.toml` set that cannot resolve. Either the tool packages belong in the catalog with their
sources, or their manifests do not belong at all.

**Fix:** Replace the blanket `**/pyproject.toml` with the intended categories, e.g.
`"tools/**/*"` + `"libs/python/**/*"` if tool source really is part of the shipped template, or drop
the nested pattern and keep only the root `pyproject.toml` + `workspace.toml` if it is not. Document
the decision in the module docstring next to the `.workflow/tasks/**` exclusion rationale.

### WR-04: Symlink resolution flattens destinations — the emitted path is the link target, not the enumerated path

**File:** `tools/adoption_scan/destinations.py:201-214`

**Issue:** The loop resolves each candidate (`resolved = candidate.resolve()`) and derives
`destination = resolved.relative_to(root_resolved)`. For an in-repo symlink (e.g.
`docs/how-to/x.md -> ../explanation/x.md`), the catalog emits the *target's* path, not the path that
was actually enumerated — and two links to one file dedup to a single row. `disposition()` and the
Phase-27 apply step would then operate on a path the harness does not actually ship at. The confined
walk idiom copied from `repo_map.py` uses `resolve()` only for the containment *check*; this code
also uses it for the *identity*, which is the divergence.

**Fix:** Check containment with `resolved`, but derive the destination from the enumerated path:

```python
resolved = candidate.resolve()
if root_resolved != resolved and root_resolved not in resolved.parents:
    continue
destination = candidate.relative_to(_REPO_ROOT).as_posix()
```

### WR-05: `schema_surfaces` is detected but never consumed — the `contract-candidate` proposal/question kind stays permanently unreachable

**File:** `tools/adoption_scan/detect.py:185-202`, `tools/adoption_scan/plan.py:35-44`, `:98-196`

**Issue:** Plan 26-05's stated purpose was ADOPT-01 surface coverage, and it correctly closed the
`codeowners-ownership` dead branch (`test_codeowners_ownership_question_fires` even calls out that
the kind was "permanently unreachable until this plan fed it a real inventory signal"). The
identically-shaped `schema_surfaces` gap was left open: `classify()` walks `manifests`,
`candidate_process_boundaries`, `documentation_surfaces`, `ci_surfaces`, `test_surfaces`,
`codeowners_surfaces` — but not `schema_surfaces`. `_QUESTION_KIND_BY_PROPOSAL_KIND["contract-candidate"]`
and `_GROUP_BY_QUESTION_KIND["contract-candidate"]` are therefore dead map entries, and the
`contract-candidate` values in `plan.schema.json`'s two enums are unreachable. Secondarily, the
detector lumps every contract schema into ONE record with the literal target
`"contracts/**/*.schema.json"`, which contradicts the per-path treatment the same phase applied to
`AGENTS.md` for exactly the same "each file is its own decision" reason.

**Fix:** Mirror the codeowners wiring, per schema file:

```python
for entry in inventory.get("schema_surfaces", []):
    for ref in entry["evidence"]:
        proposals.append({
            "id": f"contract-candidate/{ref['path']}",
            "kind": "contract-candidate",
            "classification": "unknown",   # whether a schema is a TRACKED contract is a human call
            "target": ref["path"],
            "evidence": [ref],
        })
```

If leaving it unwired is deliberate (deferred to Phase 27), say so explicitly in the `plan.py`
docstring and add a test asserting the intentional absence — otherwise the dead enum entries read as
an oversight.

### WR-06: `detect_codeowners_surfaces` only recognizes `.github/CODEOWNERS` — misses the two other locations GitHub honors

**File:** `tools/adoption_scan/detect.py:205-218`

**Issue:** The matcher is an exact-path equality against `.github/CODEOWNERS`. GitHub resolves
CODEOWNERS from `CODEOWNERS`, `.github/CODEOWNERS`, **or** `docs/CODEOWNERS`. A brownfield target
using either of the other two locations produces an empty `codeowners_surfaces` array, and
`plan.py` then emits no `codeowners-ownership` question — silently reporting "no ownership surface"
for a repo that has one. Since `codeowners-ownership` is in `_BLOCKING_KINDS`, the miss removes a
blocking pre-apply question, which is the failure direction that actually matters.

**Fix:**

```python
_CODEOWNERS_PATHS = frozenset({"CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS"})

codeowners_entries = [e for e in included if e["path"] in _CODEOWNERS_PATHS]
# emit one surfaceRecord per found path (same per-file rationale as AGENTS.md, WR-01 of the prior review)
```

### WR-07: `detect_test_surfaces` only matches a top-level `tests/` directory

**File:** `tools/adoption_scan/detect.py:169-182`

**Issue:** `PurePosixPath(path).parts[:1] == ("tests",)` recognizes only a repo-root `tests/`. This
very repo's tests all live at `tools/<pkg>/tests/test_*.py` and `libs/python/normalize/tests/`, so
running the scanner against the harness itself would report **no test surface** — and `test-command`
proposals/questions would never fire. Pre-existing (26-02) but directly adjacent to the "surface
coverage" gap the gap-closure plans set out to close, and the same phase established the per-path
precedent needed to fix it.

**Fix:** Match any `tests` path segment and group per test-root directory:

```python
by_root: dict[str, list[dict]] = {}
for entry in included:
    parts = PurePosixPath(entry["path"]).parts
    if "tests" not in parts or not PurePosixPath(entry["path"]).name.startswith("test_"):
        continue
    idx = parts.index("tests")
    by_root.setdefault("/".join(parts[: idx + 1]), []).append(entry)
return [_surface(root, by_root[root], "observed") for root in sorted(by_root)]
```

### WR-08: Plan-numbered changelog prose baked into a gated contract and rendered into user-facing derived docs

**File:** `contracts/harness/adoption/inventory.schema.json:5`, propagated to `docs/reference/inventory.md:7` and `tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr:11`

**Issue:** The contract `description` ends with:

> "`schema_surfaces` and `codeowners_surfaces` are REQUIRED as of this revision — Plan 26-05's
> detect.py wiring populates both on every scan.py run, closing the staged-optional window opened by
> Plan 26-04."

The constitution plane is the durable, CODEOWNERS-gated definition of the artifact; internal plan
numbers and a description of a two-commit staging window are planning-artifact history, not contract
semantics. Because `docs_sync` copies the description verbatim, this text is now the first paragraph
a reader of the public reference page sees, and it is frozen into a golden snapshot — so removing it
later costs a schema-hash rebaseline plus two snapshot updates. Every hash-bearing change to this
sentence also churns the constitution plane for no semantic reason.

**Fix:** Reduce the description to what the artifact *is* ("...both surface arrays are always
present; an absent surface is an empty array"), and move the 26-04/26-05 staging narrative to the
plan summaries / an ADR where change history belongs. Rebaseline hash + derived plane in the same
commit.

### WR-09: Stale and history-laden docstrings in `destinations.py`

**File:** `tools/adoption_scan/destinations.py:1-63`, `:303-315`

**Issue:** Two problems. (a) `build_manifest`'s docstring still reads *"Assemble the
`manifest.schema.json`-conformant document over the **40-row catalog**"* — the whole point of
`2058a2e` was that the catalog is no longer 40 rows (it is 344 here and varies per checkout). A
stale count in the docstring of the function that consumes the catalog is exactly the kind of
comment that misleads the next reader. (b) The 63-line module docstring is largely a narrative of
prior-review fixes ("CR-01 fix (26-REVIEW.md): ...", "WR-03 fix (26-REVIEW.md): ..."), and
`disposition`/`harness_proposed_hash` repeat it. Review-ticket archaeology belongs in commit
messages and the phase artifacts; in source it decays into false context the moment the referenced
review is superseded — as it is by this very report.

**Fix:** Change "the 40-row catalog" to "the rule-derived catalog (`destination_catalog()`)". Strip
the `CR-01 fix` / `WR-03 fix` framing and keep only the still-true invariants they encode ("proposed
content is always sourced from this checkout, never from the scanned target"; "the existing-file
hash is reused from the inventory and never re-read").

### WR-10: Contract, hash, and derived-plane updates are not atomic per commit — intermediate commits are red and bisect-hostile

**File:** commits `d488c79`, `2058a2e` (vs `eda1fdd`, `9c87a2b`)

**Issue:** `d488c79` changed `contracts/harness/adoption/inventory.schema.json` (optional →
required) **and** `contracts/.hashes/manifest.json`, but not `docs/reference/inventory.md`,
`.memory/derived/contracts-index.md`, or the two derived `.ambr` snapshots — those landed one commit
later in `eda1fdd`. Likewise `2058a2e` rewrote `destination_catalog()` without refreshing
`test_snapshots.ambr`, which came two commits later in `9c87a2b`. HEAD is consistent (verified:
`build_manifest()` recomputes byte-identical to the committed manifest), but the project's own rule
is that a contract change is *paired* with its hash and derived regeneration — the stale-derived and
snapshot gates would fail on those intermediate commits, and `git bisect` over this range is
unreliable.

**Fix:** Squash schema + hash + `docs_sync` + `memory_regen` + affected snapshots into a single
commit per contract change. If the phase workflow forces separate task commits, add a
pre-push/CI-on-range check so an intermediate red state is at least visible.

### WR-11: `test_total` proves less than its name and docstring claim

**File:** `tools/adoption_scan/tests/test_dispositions.py:27-37`

**Issue:**

```python
catalog = destinations.destination_catalog()
assert len(catalog) > 100
for row in catalog:
    result = destinations.disposition(row["destination"], tmp_path, proposed_sha=None)
    if result is None:
        continue
    assert result in destinations.DISPOSITION_ENUM
```

`> 100` is an unexplained magic number that is simultaneously too loose (it would pass with a catalog
that lost 70% of its rows) and coupled to repo size. More importantly, the `continue` on `None` means
a regression in `is_gsd_owned` that made *every* row return `None` would leave the loop body never
executing and the test still green — the opposite of a totality proof. The module docstring
advertises this test as the proof of ADOPT-03 totality.

**Fix:** Assert the partition explicitly:

```python
results = [destinations.disposition(r["destination"], tmp_path, None) for r in catalog]
dispositioned = [r for r in results if r is not None]
excluded = [r for r in results if r is None]
assert dispositioned, "at least one row must resolve to a disposition"
assert len(dispositioned) + len(excluded) == len(catalog)
assert set(dispositioned) <= set(destinations.DISPOSITION_ENUM)
assert len(catalog) >= _MIN_CATALOG_ROWS  # named constant with a comment on why
```

---

## Info

### IN-01: Incorrect `# noqa: F401` on an imported symbol that IS used

**File:** `tools/adoption_scan/destinations.py:72`
**Issue:** `from tools.hooks.contract_guard import CONSTITUTION_GLOBS  # noqa: F401 (re-exported for callers)` —
the symbol is used directly at line 286 (`resolve_path(CONSTITUTION_GLOBS, rel)`), so the suppression
is both unnecessary and its comment is false. `ruff check --select RUF100` confirms: *"Remove unused
`noqa` directive"* (not caught by the default rule set).
**Fix:** Delete the `# noqa` comment; optionally enable `RUF100` in the ruff config so dead
suppressions cannot accumulate.

### IN-02: Unreachable `except UnicodeDecodeError` in `enumerate_target`

**File:** `tools/adoption_scan/scan.py:150-158`
**Issue:** `proc.stdout.decode("utf-8", "surrogateescape")` cannot raise `UnicodeDecodeError` — that
is the entire point of the `surrogateescape` handler — so the `except UnicodeDecodeError: names = None`
branch and the subsequent `if names is not None` guard are dead. The module docstring nonetheless
lists "decode error" as a fallback trigger.
**Fix:** Drop the try/except and the `None` sentinel, or switch to `decode("utf-8")` if a strict
decode really is intended (in which case the fallback becomes live).

### IN-03: `_EXCLUDED_PREFIX` structural skip is unreachable

**File:** `tools/adoption_scan/destinations.py:169-171`, `:209-210`
**Issue:** No pattern in `_CATEGORY_GLOBS` can produce a path under `.workflow/tasks/`, so the guard
never fires. It is documented as intentional belt-and-suspenders, which is defensible, but
`test_workflow_tasks_excluded` asserts a property that is vacuously true and gives false confidence
that the guard is exercised.
**Fix:** Keep the guard, but make the test meaningful — e.g. assert
`destination_catalog` filters a synthetic `.workflow/tasks/...` path by unit-testing the predicate
directly, so a future refactor that drops the check turns the test red.

### IN-04: Machine-derived `contracts/.hashes/manifest.json` resolves to `human-ratification-required`

**File:** `tools/adoption_scan/destinations.py:286-289`
**Issue:** `contracts/.hashes/manifest.json` is enumerated by `contracts/**/*` and, because step 2
(constitution) precedes step 3 (derived), resolves to `human-ratification-required`. It is in fact a
machine-regenerated artifact (`tools.contract_hash`), the same category as `docs/reference/**`.
Asking a human to ratify a recomputable hash file is defensible as a gate, but it is an undocumented
consequence of the step ordering rather than a stated decision.
**Fix:** Either add `contracts/.hashes/**` to `DERIVED_GLOBS` with an ordering exception, or state
in the `disposition` docstring that the hash manifest is deliberately routed to ratification because
it *is* the contract-drift gate.

---

_Reviewed: 2026-07-19T16:35:26Z_
_Reviewer: gsd-code-reviewer_
_Depth: standard_
