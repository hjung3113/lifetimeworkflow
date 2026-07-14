---
phase: 11-multi-repo-workspace-v2-0
reviewed: 2026-07-14T00:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - tools/workspace_config/loader.py
  - tools/harness_lint/tests/test_workspace_config.py
  - tools/harness_lint/tests/test_core_no_workspace_member_dep.py
  - tools/workspace_config/tests/test_endpoints.py
  - tools/contract_drift/drift.py
  - tools/golden_runner/runner.py
  - .github/workflows/ci.yml
  - workspace.toml
findings:
  critical: 1
  warning: 4
  info: 1
  total: 6
status: issues_found
---

# Phase 11: Code Review Report

**Reviewed:** 2026-07-14T00:00:00Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

Reviewed the MREPO-01/03/04 multi-repo workspace slot: the `tools/workspace_config` stdlib loader,
the `workspace.toml` consistency gate, the generalized GEN-04 core→workspace-member guard, the
cross-repo `contract_drift.workspace_drift` gate, the widened `golden_runner._confine` allowlist,
and the CI `workspace` job wiring.

The three explicitly-flagged invariants mostly hold: `_confine` correctly *widens* (never removes)
the path-escape guard; `workspace_drift` correctly iterates each member's *own* baseline (never a
merged manifest) and resolves each edge's contract in its producer member; the CI job registers
`workspace` in `gate.needs`, uses a read-only token, and never interpolates event data.

However, tracing `workspace_drift` → `run_gate` → `_git_show` across module boundaries surfaces a
real correctness bug in the classification path (BLOCKER below): the breaking/non-breaking
classification silently degrades to "unknown" (or worse, could compare against an unrelated
same-named file) for every workspace-member schema change, because `_git_show` always queries `git
show HEAD:<rel>` from the top-level repo root, while `rel` for a member is relative to that
member's own root. No existing test catches this because the workspace-drift tests only assert
`ok is False`, never the reported classification. Also found: the GEN-04 twin's documented
`from=`/`to=`/`contract=` pointer-line exemption never actually matches the real inline-table edge
syntax used in `workspace.toml` (only `root=` lines match), a raw `KeyError` instead of a clear
assertion in one consistency-gate test, an unhandled `FileNotFoundError` for a member with no
baseline yet, and an inconsistent path-confinement trust boundary in `golden_runner.compare()`.

## Critical Issues

### CR-01: Workspace-member contract-drift classification silently wrong (`_git_show` cwd mismatch)

**File:** `tools/contract_drift/drift.py:116-132` (`_git_show`), `:150-158` (`run_gate` loop), exercised via `:170-229` (`workspace_drift`)

**Issue:** `build_manifest()` (in `tools/contract_hash/hash.py:43-60`) keys the manifest
`.parent`-relative to whatever `contracts_dir` is passed in — for a workspace member this is
relative to **that member's own root** (e.g. `"contracts/greeting.schema.json"` for
`tests/fixtures/workspace/member-a`), NOT relative to the top-level repo root. `workspace_drift()`
correctly calls `run_gate(contracts_dir=cdir, baseline_path=cdir/".hashes"/"manifest.json")` per
member (line 200) — the per-member baseline diff itself is correct.

But inside `run_gate`, for every `changed` key it calls `_git_show(rel)` (line 151), which always
does:

```python
proc = subprocess.run(["git", "show", f"HEAD:{rel_path}"], cwd=str(REPO_ROOT), ...)
```

`REPO_ROOT` here is the fixed top-level repo root imported from `tools.contract_hash.hash`
(`drift.py:26`) — never the member's own root. For a member schema, `rel_path` is
`"contracts/greeting.schema.json"` (relative to `tests/fixtures/workspace/member-a/`), but `git
show HEAD:contracts/greeting.schema.json` resolves against the **top-level** git tree. Verified
against the actual repo tree: the root only has `contracts/sample/greeting.schema.json` and
`contracts/normalization/format-conventions.schema.json` — there is no
`contracts/greeting.schema.json` at the top level — so `git show` fails, `_git_show` catches the
`CalledProcessError` and returns `None`, and `run_gate` falls through to `cls = "unknown"` (line
157) for every workspace-member drift, instead of the correct `"breaking"`/`"non-breaking"`
verdict. Worse, if a member's relative path *did* happen to collide with a real top-level path,
the classifier would silently diff against the **wrong** "old" schema and could report a breaking
change as non-breaking (or vice versa).

This defeats the entire purpose of CONTRACT-04's classification (the human-facing signal that
tells a reviewer whether an unapproved schema drift is safe to rebaseline) for exactly the new
capability this phase adds — cross-repo workspace members. The pass/fail *gate* (drift detected:
yes/no) still works because it's driven by the raw hash diff, not by `_git_show`; only the
reported classification is wrong. No existing test catches this:
`tools/contract_drift/tests/test_workspace_drift.py::test_per_member_drift_is_detected` only
asserts `result["members"]["m"]["ok"] is False`, never inspects `mres["drifted"][i][2]` (the
classification). `tools/contract_drift/tests/test_cli_flags.py` has the same gap for the
pre-existing `--contracts-dir` non-root flag (only checks exit code 0/1, never classification), so
this same bug already silently affects the example-manifest drift job in `ci.yml:135` too — this
phase's `workspace_drift()` just makes the latent defect load-bearing for a brand-new feature.

**Fix:** Thread the correct git-diff root into `_git_show` (or drop `git show` entirely in favor of
comparing against the previous manifest's hash without trying to recover old content when the
`contracts_dir` isn't the top-level tree). Minimal fix — pass the resolved base dir through:

```python
def _git_show(rel_path: str, cwd: Path = REPO_ROOT) -> dict | None:
    try:
        proc = subprocess.run(
            ["git", "show", f"HEAD:{rel_path}"],
            cwd=str(cwd),
            capture_output=True, check=True, shell=False,
        )
        return json.loads(proc.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError, OSError):
        return None

# in run_gate:
base = Path(contracts_dir).resolve().parent
for rel in delta["changed"]:
    old = _git_show(rel, cwd=base)
    ...
```
Also add an assertion in `test_workspace_drift.py`/`test_cli_flags.py` that a mutated member/
non-root schema is classified `"breaking"`/`"non-breaking"` (not `"unknown"`), so this regresses
loudly next time.

## Warnings

### WR-01: GEN-04 pointer-line exemption never matches the real edge syntax it claims to exempt

**File:** `tools/harness_lint/tests/test_core_no_workspace_member_dep.py:53, 87-91, 144-149`

**Issue:** `_WORKSPACE_POINTER_LINE = re.compile(r"\s*(root|from|to|contract)\s*=")` is matched via
`.match()`, which anchors at position 0 (after leading whitespace). The docstring (lines 15-18,
43-53) claims this exempts the `root =` / `from =` / `to =` / `contract =` edge-pointer lines in
`workspace.toml`. But the real `workspace.toml` declares edges as a **single-line inline table**:

```toml
edges = [
  { from = "member-a:emit", to = "member-b:ingest", contract = "greeting" },
]
```

The `from =`/`to =`/`contract =` tokens are preceded by `{ ` — never the first token on the
line — so `_WORKSPACE_POINTER_LINE.match(line)` never matches this line; only the standalone
`root = "..."` member-declaration lines actually match. The unit tests that claim to prove this
exemption (`test_workspace_root_pointer_is_exempt`, `test_negative_control_flags_nonexempt_workspace_leak`)
only construct synthetic single-key lines (`f'root = "{marker}"'`, `f'member = "{marker}"'`) and
never exercise the real inline-table format, so they pass while giving false confidence that the
`from=`/`to=`/`contract=` exemption works. It currently causes no production failure only because
`workspace.toml` lives at the repo root and is never included in the `_CORE_ROOTS` (`tools`,
`harness`, `libs`) `git ls-files` sweep — but the exemption logic itself is dead/incorrect relative
to its documented purpose, and would false-flag the legitimate edge line the moment this guard (or
a copy of it) is ever pointed at `workspace.toml` directly.

**Fix:** Either match the pointer keys anywhere on the line (not just as the first token), e.g.:

```python
_WORKSPACE_POINTER_LINE = re.compile(r"(?:^|[{,]\s*)(root|from|to|contract)\s*=")
```

or add a unit test that exercises the actual inline-table edge line verbatim (e.g. reading the real
line from `workspace.toml` via `Path("workspace.toml").read_text()` rather than a synthetic
standalone-key string) so the exemption is proven against real syntax, not just a stand-in.

### WR-02: `test_edge_contracts_tracked_in_producer` raises a raw `KeyError` instead of a clear assertion

**File:** `tools/harness_lint/tests/test_workspace_config.py:89-91`

**Issue:**
```python
producer_id, _stage = split_endpoint(edge["from"])
producer_root = _REPO_ROOT / by_id[producer_id]["root"]
```
If `edge["from"]` is a bare stage (no `:` — `split_endpoint` returns `producer_id=None`) or names
an undeclared member, `by_id[producer_id]` raises an unhandled `KeyError` with an unhelpful default
traceback (`KeyError: None`) instead of a clear, diagnosable assertion. This is inconsistent with
the sibling test `test_edge_endpoints_name_declared_members` (which asserts with a descriptive
message) and with the production code in `drift.py::workspace_drift` (line 209:
`producer_root = by_id.get(producer_id)`, which handles the missing case gracefully and reports a
clean reason). The suite still fails loud overall (the sibling test catches the same malformed edge
first), but this specific test degrades the diagnostic quality on a genuinely malformed manifest.

**Fix:**
```python
assert producer_id in by_id, (
    f"edge {edge!r}: `from` endpoint {edge['from']!r} resolves to producer "
    f"{producer_id!r}, which is not a declared member"
)
producer_root = _REPO_ROOT / by_id[producer_id]["root"]
```

### WR-03: `workspace_drift()` crashes with an unhandled `FileNotFoundError` for a member with no baseline yet

**File:** `tools/contract_drift/drift.py:197-203` (call site), `:34-36` (`load_baseline`)

**Issue:** `workspace_drift()` calls `run_gate(contracts_dir=cdir, baseline_path=cdir / ".hashes" /
"manifest.json")` for every declared member with no existence check. `load_baseline()` does
`Path(baseline_path).read_text(...)` directly — if a member is added to `workspace.toml` before its
own `contracts/.hashes/manifest.json` baseline has ever been written (a very plausible onboarding
sequence for a new member repo), this raises an unhandled `FileNotFoundError` instead of a clear,
actionable gate message (contrast with the guidance the root CLI prints on drift, `drift.py:317-320`).

**Fix:** Wrap the per-member `run_gate` call and surface a clear message, e.g.:
```python
if not (cdir / ".hashes" / "manifest.json").exists():
    member_results[mid] = {"ok": False, "drifted": [(str(cdir), "missing-baseline", "unknown")]}
    continue
```

### WR-04: `golden_runner.compare()` reads the verified baseline path without going through `_confine`

**File:** `tools/golden_runner/runner.py:116-144`

**Issue:** `run_identity_converter` (lines 161-162) and `run_converter` (lines 189-190) both
confine `seed`/`out_path` via `_confine()` before touching the filesystem. `compare()`, however,
reads `verified_path(case, golden_dir).read_bytes()` (line 126) directly with no confinement check
at all. `case` is CLI-controlled (`args.case` in `main()`, line 291→294) and is concatenated
unsanitized into `case_dir(case, golden_dir) / "expected" / "baseline.verified.tsv"` — a `case`
value containing `../` segments is never rejected here, unlike the converter I/O paths in the same
module. This is a real inconsistency in the confinement guard's trust boundary within a file this
phase specifically hardens (`_confine`'s `allowed_roots` widening).

**Fix:** Route the baseline read through `_confine` too, e.g. `_confine(verified_path(case,
golden_dir)).read_bytes()`, so every filesystem touch in this module goes through the same guard.

## Info

### IN-01: No validation against a degenerate (empty-string) member `root`

**File:** `tools/workspace_config/loader.py`, `tools/harness_lint/tests/test_core_no_workspace_member_dep.py:56-63, 94-106`

**Issue:** Nothing rejects `[[members]] root = ""` in `workspace.toml` (an empty root would resolve
to `REPO_ROOT` itself and pass `test_each_member_root_exists`, since `_REPO_ROOT / "" == _REPO_ROOT`
exists). If that were ever configured, `_member_roots()` would include `""` as a marker, and
`_scan_lines`'s `any(marker in line for marker in roots)` check would match **every** line in every
core file (an empty string is a substring of everything), making the GEN-04 guard fail
universally. Currently harmless (no committed member has an empty root), but there is no guard
against it.

**Fix:** Have the consistency gate (`test_workspace_config.py`) additionally assert every member
`root` is a non-empty, non-`"."` relative path.

---

_Reviewed: 2026-07-14T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
