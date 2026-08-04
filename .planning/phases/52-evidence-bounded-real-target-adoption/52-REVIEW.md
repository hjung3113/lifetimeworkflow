---
phase: 52-evidence-bounded-real-target-adoption
reviewed: 2026-08-01T00:00:00Z
depth: deep
files_reviewed: 6
files_reviewed_list:
  - tools/adoption_scan/detect.py
  - tools/adoption_scan/scan.py
  - tools/harness_config/loader.py
  - tools/adoption_apply/cli.py
  - tools/adoption_apply/apply.py
  - tools/adoption_apply/tests/test_atomic_apply.py
findings:
  critical: 3
  warning: 10
  info: 7
  total: 20
status: resolved
resolved: 2026-08-01T00:00:00Z
resolution:
  fixed: 12
  skipped: 7
  not_a_defect: 1
  commits:
    - 9fa201d
    - 56508c2
    - 1481655
---

# Phase 52: Code Review Report

**Reviewed:** 2026-08-01
**Depth:** deep (source read + call-chain trace + live execution of the changed code paths)
**Files Reviewed:** 6 production files (+ the one test file carrying a defective assertion)
**Status:** findings

## Summary

The three repairs are individually well-reasoned and the two highest-risk areas named in the
review brief hold up: **the lock fast path preserves mutual exclusion in the source**, **no unlink
of the sidecar was added (D-15 respected)**, and **the CR-01 confinement is airtight in code** —
target-derived bytes reach exactly one destination via an exact literal key match
(`cli.py:237`), never a prefix/glob, and no subprocess argv is ever built from target content.
`conventions_for()` correctly uses `lang.get("lint")` and the only call site is safe.

Three defects nonetheless block: an **environment integrity failure** (a divergent bytecode cache
that makes the marker-merge lock a *shared* lock at runtime and reds three tests), a **silent
inventory-scope collapse** whenever a real pnpm workspace manifest yields zero parsed globs, and a
**derived `[[languages]]` row that violates the harness's own SSOT gate contract**, hard-failing the
adopted target's CI. All three are reachable on real targets and were reproduced live, not inferred.

Because a `<structural_findings>` block was not supplied, this report contains narrative findings
only.

## Resolution (2026-08-01)

Fix pass against this report. Every fix carries a regression test whose mutation was applied,
RUN, observed RED, and reverted — the observed failure text is quoted in each commit message.
Suite 1023 -> 1047 passed. `contracts/` untouched, contract count still exactly 6,
`uv run python -m tools.contract_drift.drift` exit 0, `tools/adoption_scan/tests/__snapshots__/`
unmoved (`--snapshot-update` never run). NG-01 held: no new contract, skill, command, CI job or
gate.

| Finding | Disposition | Commit |
|---|---|---|
| CR-01 | **not a defect** | — |
| CR-02 | fixed | `9fa201d` |
| CR-03 | fixed | `56508c2` |
| WR-01 | fixed | `9fa201d` |
| WR-02 | fixed | `9fa201d` |
| WR-03 | fixed | `9fa201d` |
| WR-04 | fixed | `9fa201d` |
| WR-05 | fixed | `1481655` |
| WR-06 | fixed | `1481655` |
| WR-07 | fixed | `1481655` |
| WR-08 | **skipped** — docstring note only | `1481655` |
| WR-09 | fixed | `9fa201d` |
| WR-10 | fixed | `9fa201d` |
| IN-01..IN-05, IN-07 | **skipped** — outside the evidence-bounded scope fence | — |
| IN-06 | fixed (subsumed by CR-03) | `56508c2` |

**CR-01 — NOT A DEFECT, nothing was changed.** The `.pyc` recorded BOTH the source mtime and the
size identically, so CPython trusted stale bytecode; the divergence was produced by the verifier
agent's own mutation experiment swapping `LOCK_EX` -> `LOCK_SH` (both exactly 7 characters, so the
file size was preserved) and reverting inside the same mtime second, which defeats cache
invalidation. Purging every `__pycache__` outside `.venv` took the named subset from
`3 failed, 90 passed` to `93 passed`, and the full suite to 1023 passed on clean bytecode. There
is no source defect. The report's suggested `PYTHONDONTWRITEBYTECODE` / cache-busting mechanism
was deliberately NOT added — that would be new permanent surface for an environmental hazard
(NG-01).

**CR-02 — fixed, plus flow-style support.** `[]` from `parse_pnpm_workspace_globs` now degrades to
the D-10 unchanged path (`workspace_globs` stays `None`) instead of meaning "this workspace
declares zero members". Flow-style `packages: [...]` is now parsed; it is a legitimate common pnpm
shape that previously hit the same mis-scoping wearing a different hat. Hand-rolled,
filesystem-free, no new external dependency (both module invariants held).

**CR-03 — fixed by omission, with the decision traced to what actually ships.** No row is emitted
at all when the target declares no `test` script; `lint`/`format` are omitted rather than blanked;
`conventions_for` is now `.get`-tolerant for `test`/`format`/`bash_scope`, matching the `lint`
treatment D-11 established. Findings 2-4 of CR-03 were traced and are **not reachable in an
adopted target**: `destinations._SKIP_SEGMENTS` excludes every `tools/**` path with a `tests`
segment, so `tools/harness_lint/tests/test_language_config.py` — which holds the `persona`
subscript, the `test_paths` check and the `bash_scope` set-equality check — is absent from the
destination catalog (verified against the live 363-row catalog). Only finding 1, the shipped
`.github/workflows/ci.yml` `setup` job, is a real break, and it is the one the fix is keyed to.
That is also what makes omitting `persona`/`test_paths` honest rather than a shortcut: neither is
derivable from a `package.json` at all, and no shipped consumer reads them.
`bash_scope = "pnpm *"` is retained: the divergence from the target's copied
`harness/permission-matrix.json` degrades pnpm commands to the matrix's `*: ask` catch-all, which
is safe-by-default, and adding `pnpm *` to the matrix would red THIS repo's own set-equality gate
(this repo's `project.toml` declares no javascript language).

**WR-08 — skipped.** Recording the splice as provenance the drafter can recognise requires a new
field on the disposition record, i.e. an edit to `contracts/harness/adoption/manifest.schema.json`
— the constitution plane, human-gated and closed for this phase. The review's own stated minimum
(note the consequence in the module docstring so Phase 53 does not rediscover it) is what landed.

**Info findings — skipped, deliberately.** IN-01 (redundant exception tuple), IN-02 (report
verbosity), IN-03 (retyped filename literal), IN-04 (`lock_sidecar_for("")` precondition), IN-05
(export with no in-tree consumer) and IN-07 (widen the derived convention-profile table) are all
either cosmetic or would grow surface / derived-plane output for no observed failure. None was
fixed merely to close it. IN-06 needed no separate work — CR-03's omission fix is exactly its
stated remedy.

**Checks that could not fail, caught during this pass.** Three of the fixer's own first-draft
tests were rewritten only after their mutation came back GREEN, not before: the CR-03 CI-gate test
(originally asserted against a `package.json` declaring both `lint` and `test`, which the
pre-repair code satisfied — now parametrized over the no-`test` shapes that are the actual
defect); the `conventions_for` test (originally supplied a `test` key, so reverting that one
`.get` to a subscript still passed — a second bare-row case now covers it); and the WR-02
case-sensitivity test (`posixpath.normcase` is the identity function, so the obvious assertion
passes with `fnmatch` too on every platform this repo runs on — it now monkeypatches a
lowercasing normcase to reproduce `ntpath.normcase`). Separately, the fixer's own mutation harness
initially mis-attributed three loader mutations to a single key because of stale `__pycache__` —
the same hazard class as CR-01; it now runs pytest under `-B`, after which each mutation
attributed to its own key (`KeyError: 'test'` / `'format'` / `'bash_scope'`).

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Divergent bytecode cache executes `LOCK_SH` — marker-merge mutual exclusion is broken at runtime, and three tests are red

**File:** `tools/adoption_apply/__pycache__/apply.cpython-311.pyc` (vs. `tools/adoption_apply/apply.py:350`)

**Issue:** The working tree's compiled cache for `apply.py` does **not** match the source it claims
to compile. Source line 350 reads `fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)`; the
loaded bytecode loads `LOCK_SH | LOCK_NB` (flags `5`, not `6`):

```
$ uv run python -c "import dis; from tools.adoption_apply import apply; dis.dis(apply._apply_marker_merge)"
   306 LOAD_ATTR   10 (LOCK_SH)      # source says LOCK_EX
   328 LOAD_ATTR   11 (LOCK_NB)
```

`LOCK_SH` is a *shared* lock: two concurrent applies both acquire it and both enter the
read-merge-write critical section. Reproduced: `max_concurrent=2`, and the read-modify-write of
`AGENTS.md` / `CLAUDE.md` / `.claude/settings.json` is a lost-update race — the exact WR-01 defect
the lock exists to prevent.

This cannot be ordinary staleness. The `.pyc` header's recorded source mtime **and** size match
`apply.py` byte-for-byte (`mtime=1785521263 size=24660`), so CPython trusts it and never
recompiles; a normal edit would have invalidated it. `__pycache__/` is gitignored, so
`git status` is clean and the divergence is invisible to every repo-level check.

Consequence for this phase's evidence: any verification, self-check, or SC-2/SC-3/SC-4 observation
run on this machine executed *this* bytecode, not the reviewed source. Proof both ways:

```
$ uv run pytest tools/adoption_{scan,apply}/tests tools/harness_config/tests tools/memory_regen/tests -q
3 failed, 361 passed        # test_concurrent_marker_merge_does_not_lose_writes,
                            # test_marker_merge_acquires_exclusive_flock,
                            # test_held_lock_still_blocks_and_emits_no_prior_run_report

$ PYTHONPYCACHEPREFIX=/tmp/fresh uv run pytest <same> -q
364 passed                  # source is correct; the cache is not
```

**Fix:** Purge and re-verify before anything else, then make the class of failure impossible to
hide:

```bash
find . -name '__pycache__' -type d -prune -exec rm -rf {} +
uv run pytest -q                       # must be 364 passed
# and in CI / the SessionStart bootstrap:
export PYTHONDONTWRITEBYTECODE=1       # or PYTHONPYCACHEPREFIX to an ephemeral dir
```

Re-run the phase's SC-2/SC-3/SC-4 captures afterwards; the current evidence set is not trustworthy
until the suite is green against freshly compiled bytecode.

---

### CR-02: A pnpm workspace manifest that parses to zero globs silently deletes every non-root manifest from the inventory

**File:** `tools/adoption_scan/scan.py:339-349` (with `tools/adoption_scan/detect.py:83-111`)

**Issue:** `workspace_globs` is set to whatever `parse_pnpm_workspace_globs()` returns, including
`[]`. `is_workspace_member()` then returns `False` for every directory except `"."`, so **every
manifest outside the target root is excluded as `non-workspace-member`** — silently, under an
exclusion reason that reads like a deliberate decision.

The parser returns `[]` for at least three shapes that occur in real pnpm repos:

| `pnpm-workspace.yaml` content | parsed globs | resulting inventory |
|---|---|---|
| `packages: ["apps/*", "packages/*"]` (flow-style — valid YAML) | `[]` | only `package.json` survives |
| `onlyBuiltDependencies:\n  - esbuild` (pnpm 10 settings file) | `[]` | only `package.json` survives |
| `packages:` with an empty/misindented body | `[]` | only `package.json` survives |

Reproduced live against a 4-manifest synthetic target:

```
flow-style | globs= []
   manifests: ['package.json']
   non-member excl: ['apps/a/package.json', 'packages/b/package.json', 'packages/b/deep/package.json']
```

This directly defeats the repair's own stated goal (D-07: "the inventory itself must be right"),
and it propagates: `plan.json` and `manifest.json` are built from this inventory, so the adoption
proceeds against a target the harness believes has one package.

The code also contradicts its own documented contract. `detect.py:80-81` claims "a hostile manifest
downgrades scoping to the D-10 unchanged path, never crashes the run" — returning `[]` does the
opposite of downgrading to D-10. The adjacent `OSError` branch (`scan.py:346-347`) *does* degrade
correctly by leaving `workspace_globs` as `None`, which is strong evidence this is an oversight
rather than a design choice.

**Fix:** Treat "no globs parsed" as "no workspace scoping", matching the `OSError` branch:

```python
        if workspace_manifest_text is not None:
            parsed = detect.parse_pnpm_workspace_globs(workspace_manifest_text)
            # A manifest we could not extract any glob from must degrade to the D-10 unchanged
            # path — never to "the workspace has exactly one member".
            if parsed:
                workspace_globs = parsed
            else:
                print(
                    f"scan: {detect.PNPM_WORKSPACE_MANIFEST} declared no parsable 'packages:' "
                    "globs — workspace scoping disabled for this target (D-10 path)",
                    file=sys.stderr,
                )
```

Add regression tests for all three shapes above; none currently exists (`test_detect.py:281-284`
covers the parser's `[]` return but nothing covers what `build_inventory` then does with it).

---

### CR-03: The derived `[[languages]]` row violates the harness's own project-config contract and hard-fails the adopted target's CI

**File:** `tools/adoption_apply/cli.py:93-96`

**Issue:** `derive_language_rows` emits `""` for any of `lint`/`test`/`format` the target does not
declare, and emits no `persona` and no `test_paths` at all. Rendered for a target whose
`package.json` has `lint` but no `test` (extremely common):

```toml
[[languages]]
id = "javascript"
bash_scope = "pnpm *"
lint = "pnpm run lint"
test = ""
format = ""
```

The apply cycle also installs `tools/**/*` and `.github/workflows/**/*` into the target
(`destinations.py:_CATEGORY_GLOBS`), so the target inherits the gates that read this file:

1. `.github/workflows/ci.yml:62-68` — the `setup` job calls `sys.exit(...)` when any
   `[[languages]]` entry has an empty `id` or `test`. **The adopted target's CI cannot start.**
2. `tools/harness_lint/tests/test_language_config.py:50` — `lang["persona"]` is an unguarded
   subscript; the javascript row raises `KeyError`.
3. `test_language_config.py:44` — `_matrix_language_allow_scopes() == language_bash_scopes(...)`
   fails, because `"pnpm *"` is now in the config but not in the copied
   `harness/permission-matrix.json`.
4. `test_each_configured_language_has_test_paths` fails (`test_paths` absent).

So the D-12 repair ships the target a config its own SSOT gate rejects. This is the phase's
primary deliverable, and the failure is reachable in the exact scenario the phase ran.

**Fix:** Never emit an empty required key; omit optional ones, and pair the `bash_scope` with a
matrix entry (or drop `bash_scope` until the matrix side is handled):

```python
    lines = [
        _DERIVED_PROVENANCE_COMMENT,
        "[[languages]]",
        f'id = "{_DERIVED_LANGUAGE_ID}"',
    ]
    for key in _DERIVED_SCRIPT_KEYS:
        if key in scripts:                       # omit, never ""
            lines.append(f'{key} = "pnpm run {key}"')
    if "test" not in scripts:                    # CI's one hard requirement
        return None                              # nothing safe to derive
```

`conventions_for()` no longer forces the `""` workaround for `lint` (it uses `.get`); apply the
same `.get` treatment to `test`/`format` in `loader.py:349-350` if omission is preferred over `""`
for those too. Add a test that runs the target's own `test_language_config.py` gates against a
spliced `harness/project.toml`.

## Warnings

### WR-01: `**` globs match only one directory level, silently dropping nested members

**File:** `tools/adoption_scan/detect.py:137`

**Issue:** `if len(glob_parts) != len(directory_parts): continue` makes `packages/**` a
single-segment match. pnpm's own documented example uses `packages/**` to mean any depth.
Reproduced: with `packages: ["packages/**"]`, `packages/b/package.json` is a member but
`packages/b/deep/package.json` is excluded as `non-workspace-member`. The docstring documents the
segment-count rule but never mentions that this makes `**` wrong.

**Fix:** Special-case a trailing `**` (match any remaining depth) and a mid-path `**`, or delegate
to `PurePosixPath.full_match` (3.13+) / a small recursive matcher. At minimum, detect a `**`
segment and fall back to the D-10 unchanged path with a stderr note rather than under-matching
silently.

### WR-02: `fnmatch.fnmatch` makes workspace membership platform-dependent

**File:** `tools/adoption_scan/detect.py:140`

**Issue:** `fnmatch.fnmatch` applies `os.path.normcase` to both operands, so membership is
case-insensitive on Windows and case-sensitive on POSIX. The same target then produces two
different `inventory.json` files, breaking this module's byte-determinism invariant
(`scan.py:31-33`) — the same class of cross-OS ambiguity `apply.py:194-198` explicitly refuses to
tolerate for the deny domain.

**Fix:** Use `fnmatch.fnmatchcase(actual, pattern)`.

### WR-03: pnpm negation globs are treated as positive membership patterns

**File:** `tools/adoption_scan/detect.py:131-142`

**Issue:** pnpm supports `- '!packages/legacy'` to exclude a directory matched by an earlier glob.
The parser stores `!packages/legacy` as an ordinary glob and the matcher never interprets `!`.
Verified: `is_workspace_member("packages/legacy", ["packages/*", "!packages/legacy"])` returns
`True` — the exclusion is silently ignored, so the inventory over-includes relative to what pnpm
considers a member. Less damaging than CR-02 (over- not under-inclusion) but equally silent, and
undocumented anywhere in the parser or matcher docstrings.

**Fix:** Either honour negation (partition globs into positive/negative, require a positive match
and no negative match) or explicitly reject a `!`-prefixed glob and degrade that target to the
D-10 path with a stderr note. Do not silently reinterpret it.

### WR-04: `pnpm-workspace.yaml` is read unconfined and unbounded

**File:** `tools/adoption_scan/scan.py:341-345`

**Issue:** Two departures from this module's own discipline, on a file from an untrusted target:

- `workspace_manifest_path.is_file()` follows symlinks. A `pnpm-workspace.yaml` symlinked outside
  the target root is happily opened and read — while `classify_exclusions` (`scan.py:216-223`)
  refuses to even `stat()` through an escaping symlink. No content leaks into the artifact (only
  match patterns are derived), so impact is bounded, but the confinement posture is inconsistent.
- `read_text()` is unbounded. Every other read in this module is capped
  (`_CONTENT_PREFIX_BYTES`, `max_bytes`); a multi-GB `pnpm-workspace.yaml` is loaded whole.

**Fix:**

```python
    if workspace_manifest_path.is_file() and _confined(workspace_manifest_path, target):
        try:
            with workspace_manifest_path.open("rb") as fh:
                raw = fh.read(_CONTENT_PREFIX_BYTES)
            workspace_manifest_text = raw.decode("utf-8", "replace")
        except OSError:
            workspace_manifest_text = None
```

### WR-05: `test_held_lock_still_blocks_and_emits_no_prior_run_report` asserts only half of what it claims

**File:** `tools/adoption_apply/tests/test_atomic_apply.py:494-498`

**Issue:** The test name and docstring promise "no prior-run report is emitted for a genuinely
held lock (T-52-12)", but the body only calls `_assert_mutual_exclusion`. It never captures or
asserts on stderr, so the second half of the claim is untested — the repo's documented signature
defect (a check that cannot fail).

Worse, the unasserted property is not actually guaranteed. In
`_observe_marker_merge_concurrency` the second racer takes the *fast* path (and therefore emits
the prior-run line) whenever the first racer has already released. That is exactly what happened
during this review — the failing run's captured stderr contains
`apply: lock sidecar from a prior run at .../.AGENTS.md.lock`. Had the assertion been written, it
would be flaky.

**Fix:** Either add a `capsys` assertion with a deterministically held lock (hold the flock from a
separate fd in the test body, assert the report is absent, then release), or rename the test to
what it verifies. Do not leave a promise in the name that the body does not keep.

### WR-06: `_cmd_draft` crashes with a traceback on a non-UTF-8 target `package.json`, after three artifacts are already written

**File:** `tools/adoption_apply/cli.py:171`

**Issue:** `root_manifest.read_text(encoding="utf-8")` raises `UnicodeDecodeError` (or `OSError`)
on target-controlled content. Every other failure in `_cmd_draft` returns a clean exit code (1/2);
this one escapes `main()` as an unhandled traceback, and it happens *after* `inventory.json`,
`plan.json`, and `manifest.json` have been written — leaving a batch that looks drafted but has no
sidecar and no error record.

**Fix:**

```python
        try:
            manifest_text = root_manifest.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"tools.adoption_apply draft: unreadable target package.json: {exc}",
                  file=sys.stderr)
            manifest_text = None
        derived = derive_language_rows(manifest_text) if manifest_text is not None else None
```

### WR-07: The derived-languages splice silently no-ops when `harness/project.toml` is not a `create` destination

**File:** `tools/adoption_apply/cli.py:237`

**Issue:** `if "harness/project.toml" in payloads and sidecar_path.is_file()` — `payloads` is
populated only for `create` dispositions (`cli.py:226-227`). If the target already has a
`harness/project.toml`, the disposition is `preserve` or `conflict`, so the sidecar is silently
ignored: the D-12 repair does nothing and says nothing. Reachable on every re-adoption and on any
target that already carries a harness config — i.e. the whole Phase-53 update scenario.

**Fix:** Emit a diagnostic when the sidecar exists but the splice is skipped:

```python
    elif sidecar_path.is_file():
        print("tools.adoption_apply apply: derived languages sidecar present but "
              "harness/project.toml is not a 'create' destination — NOT spliced "
              "(OBS-D-03 / D-12)", file=sys.stderr)
```

### WR-08: The splice makes `harness/project.toml` permanently `conflict` on every subsequent draft

**File:** `tools/adoption_apply/cli.py:239` (with `tools/adoption_scan/destinations.py` `disposition()` steps 6-7)

**Issue:** The applied bytes are `harness_payload + b"\n" + sidecar_bytes`, so
`sha256(existing) != proposed_sha` on the next draft. Step 6 (`preserve`) can never fire again;
step 7 classifies it `conflict` forever. Nothing in the manifest or the target records that the
divergence is harness-derived rather than a human edit, so the human resolving the conflict has no
way to tell. This is a direct, foreseeable obstruction to Phase 53's re-run-as-update semantics.

**Fix:** Record the derived splice as provenance the drafter can recognise — e.g. include the
spliced payload's hash in the batch (`languages.toml.sha256` or a `derived` field on the
disposition record) and have `disposition()` compare against `proposed_sha` **or** the recorded
post-splice hash. At minimum, note the consequence in the module docstring so Phase 53 does not
rediscover it.

### WR-09: `except Exception` in the glob parser swallows every error and discards partial results

**File:** `tools/adoption_scan/detect.py:110-111`

**Issue:** The bare handler wraps the entire loop, so any exception — including a genuine
programming error introduced later — yields `[]`, which under CR-02 means "workspace with exactly
one member". It also discards globs already parsed before the failure. The only behaviour the
tests pin is the `None`-input case (`test_detect.py:288`), which a narrow `except AttributeError`
would satisfy equally.

**Fix:** Narrow to the input-shape errors actually expected (`AttributeError`, `TypeError`,
`UnicodeError`), and once CR-02 is fixed the degrade target becomes "no scoping", which is safe.

### WR-10: The re-validation guard in the membership branch is fail-open

**File:** `tools/adoption_scan/scan.py:375-380`

**Issue:** `if _confined(candidate, target) and not detect.is_workspace_member(...)`. When
`_confined` returns `False` the candidate falls through to `included.append(...)` and is **hashed
and recorded** — a confinement guard whose failure mode is "include it anyway". The comment sells
it as a traversal guard (T-52-03); it is the opposite shape. The path is effectively unreachable
today (`classify_exclusions` already rejects escaping symlinks), which is why this is a WARNING and
not a BLOCKER, but a defense-in-depth check must fail closed or it is not one.

**Fix:**

```python
                if not _confined(candidate, target):
                    excluded.append({"path": rel, "size": candidate.lstat().st_size,
                                     "excluded": "symlink-escape"})
                    continue
                if not detect.is_workspace_member(manifest_dir, workspace_globs):
                    ...
```

## Info

### IN-01: Redundant and over-broad exception tuple on the fast path

**File:** `tools/adoption_apply/apply.py:357`
**Issue:** `except (BlockingIOError, OSError)` — `BlockingIOError` is a subclass of `OSError`, so
the tuple is redundant. More substantively it conflates "someone holds the lock" (`EWOULDBLOCK`)
with "this filesystem does not support flock" (`ENOLCK`/`EOPNOTSUPP`, common on some network
mounts); the latter falls into the blocking acquire, which raises the same error uncaught and
escapes `_cmd_apply`'s exception tuple as a raw traceback.
**Fix:** `except BlockingIOError:` for the contention path, and let a genuine `OSError` surface
with a named message.

### IN-02: The prior-run report is really a "sidecar exists" report

**File:** `tools/adoption_apply/apply.py:347,351-356`
**Issue:** `pre_existed` is true on every run after the first, so a normal repeat apply prints
three stderr lines about "a prior run". The docstring is honest that this is provenance rather than
staleness, but once Phase 53 lands re-run-as-update this becomes permanent noise on the happy path.
There is also a benign TOCTOU between `exists()` and `open()`.
**Fix:** Consider gating the report behind a `--verbose` flag, or reporting only when the sidecar's
mtime predates the current run's start.

### IN-03: `"pnpm-workspace.yaml"` retyped instead of reusing the new constant

**File:** `tools/adoption_apply/cli.py:168`
**Issue:** `detect.PNPM_WORKSPACE_MANIFEST` was introduced this phase precisely so the filename
lives in one place; `cli.py` hardcodes the literal, against the module-wide "never retyped" idiom
(`scan.py:284-292`).
**Fix:** `from tools.adoption_scan import detect` and use `target / detect.PNPM_WORKSPACE_MANIFEST`.

### IN-04: `lock_sidecar_for("")` raises an unnamed `ValueError`

**File:** `tools/adoption_apply/apply.py:301-302`
**Issue:** `PurePosixPath("").with_name(...)` raises `ValueError: PurePosixPath('.') has an empty
name`. Unreachable through `expected_lock_sidecars` (every member of `MARKER_CAPABLE` is
well-formed), so informational only, but the function is public and documented as a pure naming
rule.
**Fix:** Guard the empty/`.`/`..` names and raise a named error, or document the precondition.

### IN-05: `HARNESS_MANAGED_LOCK_SIDECARS` has no in-tree consumer

**File:** `tools/adoption_apply/apply.py:322`
**Issue:** The frozenset is referenced only by its own test. The comment says Plan 05's comparison
imports it, but the phase-local (D-21) comparison lives in the plan's scripts, so the production
export is currently dead weight from the library's perspective.
**Fix:** Either have `.planning/phases/52-.../scripts/` import it (making the claim true) or note
in the comment that the sole consumer is phase-local and off-tree.

### IN-06: `conventions_for()["lint"]` can return `""`, contradicting the documented contract

**File:** `tools/harness_config/loader.py:312-313` with `tools/adoption_apply/cli.py:94`
**Issue:** The docstring promises `None` when the row declares no lint command; the derived row
writes `lint = ""`, so the resolved profile carries `""`. Falsy, so no consumer breaks today, but
the D-11 shape contract now has two "absent" spellings.
**Fix:** Covered by CR-03's omission fix.

### IN-07: The derived convention-profile table was not widened with `lint`

**File:** `tools/memory_regen/package_facts.py:303-334`
**Issue:** D-11 added a permanent key to the profile, but the `## Convention Profiles` table still
renders only `test|format|bash_scope`. Not a defect (the derived plane is regenerated and its
snapshot is consistent), but the shape change is invisible to the two-plane memory readers who are
the profile's main audience.
**Fix:** Add a `lint` column and regenerate the derived plane.

---

## Explicitly verified as correct (no finding)

These were the review brief's named risks; each was traced and cleared:

- **No unlink of the lock sidecar.** `apply.py` contains no `unlink`/`remove` against `lock_path`;
  `test_expected_lock_sidecars_matches_filesystem_after_every_marker_merge` asserts persistence
  against the real filesystem. D-15 is respected.
- **Mutual exclusion in the source is sound.** `LOCK_EX|LOCK_NB` → on failure a blocking `LOCK_EX`
  on the *same* fd; there is no interleaving in which both callers proceed, and the fallback path
  correctly suppresses the prior-run report. (The runtime violation is CR-01's cache, not the code.)
- **CR-01 confinement is airtight in code, not just in tests.** The only target-derived bytes are
  `derive_language_rows`'s output, which contains no target content at all — script *values* are
  never copied, only fixed `"pnpm run <key>"` literals keyed by allowlisted names. The splice is
  gated on the exact literal `"harness/project.toml"` (`cli.py:237`), never a prefix or glob, so
  no derived byte can reach `AGENTS.md`, `CLAUDE.md`, `.claude/settings.json`, or any other
  `create` destination. No `subprocess` is constructed anywhere in `apply.py`/`cli.py` from
  manifest or draft content.
- **Glob traversal guards work.** Absolute globs and any `..` segment contribute no members
  (`detect.py:132-136`), and no path outside the target root is ever read or recorded — confirmed
  by execution against an escaping-glob fixture with a real sibling directory outside the root.
- **`lint` is read with `.get`.** `loader.py:354` uses `lang.get("lint")`; `conventions_for` is the
  only reader of the key and no other call site subscripts it. This repo's lint-less
  `python`/`dotnet` rows resolve to `None` without raising.

---

_Reviewed: 2026-08-01_
_Reviewer: gsd-code-reviewer_
_Depth: deep_
