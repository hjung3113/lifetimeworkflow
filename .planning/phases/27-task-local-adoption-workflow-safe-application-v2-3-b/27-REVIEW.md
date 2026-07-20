---
phase: 27-task-local-adoption-workflow-safe-application-v2-3-b
reviewed: 2026-07-21T00:00:00Z
depth: standard
files_reviewed: 52
files_reviewed_list:
  - .claude/commands/adopt.md
  - .claude/skills/brownfield-adoption/SKILL.md
  - .memory/derived/contracts-index.md
  - .opencode/command/adopt.md
  - .opencode/skill/brownfield-adoption/SKILL.md
  - AGENTS.md
  - contracts/.hashes/manifest.json
  - contracts/harness/adoption/approval.schema.json
  - docs/reference/approval.md
  - harness/commands/adopt.md
  - harness/skills/brownfield-adoption/SKILL.md
  - tools/adoption_apply/__init__.py
  - tools/adoption_apply/__main__.py
  - tools/adoption_apply/apply.py
  - tools/adoption_apply/approval.py
  - tools/adoption_apply/batch.py
  - tools/adoption_apply/cli.py
  - tools/adoption_apply/pyproject.toml
  - tools/adoption_apply/tests/__init__.py
  - tools/adoption_apply/tests/conftest.py
  - tools/adoption_apply/tests/fixtures/client-server/member-a/AGENTS.md
  - tools/adoption_apply/tests/fixtures/client-server/member-a/contracts/.hashes/manifest.json
  - tools/adoption_apply/tests/fixtures/client-server/member-a/contracts/greeting.schema.json
  - tools/adoption_apply/tests/fixtures/client-server/member-a/golden/greeting-edge/expected/baseline.verified.tsv
  - tools/adoption_apply/tests/fixtures/client-server/member-a/golden/greeting-edge/input/seed.tsv
  - tools/adoption_apply/tests/fixtures/client-server/member-b/contracts/.hashes/manifest.json
  - tools/adoption_apply/tests/fixtures/client-server/member-b/contracts/greeting.schema.json
  - tools/adoption_apply/tests/fixtures/partial-collision-crlf/AGENTS.md
  - tools/adoption_apply/tests/fixtures/partial-collision-crlf/widget_a.py
  - tools/adoption_apply/tests/fixtures/partial-collision-crlf/widget_a_copy.py
  - tools/adoption_apply/tests/fixtures/partial-collision-crlf/widget_a_modified.py
  - tools/adoption_apply/tests/fixtures/partial-collision-crlf/widget_b.py
  - tools/adoption_apply/tests/fixtures/polyglot-single/AGENTS.md
  - tools/adoption_apply/tests/fixtures/polyglot-single/pyproject.toml
  - tools/adoption_apply/tests/fixtures/polyglot-single/widget_a.py
  - tools/adoption_apply/tests/fixtures/polyglot-single/widget_a_copy.py
  - tools/adoption_apply/tests/fixtures/polyglot-single/widget_b.py
  - tools/adoption_apply/tests/fixtures/polyglot-single/widget_b_modified.py
  - tools/adoption_apply/tests/test_approval_invalidation.py
  - tools/adoption_apply/tests/test_atomic_apply.py
  - tools/adoption_apply/tests/test_batch_layout.py
  - tools/adoption_apply/tests/test_cli.py
  - tools/adoption_apply/tests/test_constitution_refusal.py
  - tools/adoption_apply/tests/test_fixtures.py
  - tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr
  - tools/docs_sync/tests/test_docs_sync_determinism.py
  - tools/harness_emit/emit-manifest.json
  - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
  - tools/harness_emit/tests/test_coexist.py
  - tools/harness_lint/caps.py
  - tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr
  - uv.lock
findings:
  critical: 3
  warning: 4
  info: 2
  total: 9
status: issues_found
---

# Phase 27: Code Review Report

**Reviewed:** 2026-07-21
**Depth:** standard
**Files Reviewed:** 52
**Status:** issues_found

## Summary

The phase delivers `tools/adoption_apply/{batch,apply,approval,cli}.py`, a new human-ratification
approval contract, three end-to-end fixtures, and a single `/adopt` command + `brownfield-adoption`
skill emitted to both runtimes. The atomic-write primitives (`atomic_create`/`_atomic_replace`),
the batch CAS layout, the approval binding tuple's own internal logic, and the fixture-driven
end-to-end tests are well constructed and match their stated contracts.

However, the phase's own stated centerpiece — "apply.py's constitution refusal is a structural,
in-process precondition that does not depend on any hook, because no hook fires for a bare Python
process" — does not hold up under adversarial input. Two independent structural gaps let a
crafted or corrupted `manifest.json` defeat exactly the protections this phase claims to add, and a
third gap means the human-ratification gate this phase spent an entire plan (27-04) building is
never actually consulted before a write happens. All three are proven concretely below (bypass
demonstrated, not merely reasoned about), and none is covered by any existing test — `apply.py`'s
own test suite proves the *narrow* cases (`refuse_if_constitution` on a literal `contracts/x.json`
string) but never a traversal/absolute/case variant, and never proves `apply` refuses to run without
a promoted approval, despite the skill's own doc text ("...only then is the batch safely applied to
the target").

## Critical Issues

### CR-01: `apply.py`'s constitution-plane refusal is bypassed by a `..`-traversal or case-variant destination string

**File:** `tools/adoption_apply/apply.py:74-84`
**Issue:** `refuse_if_constitution(destination)` passes the raw manifest `destination` string
straight into `resolve_path(CONSTITUTION_GLOBS, destination)`, which is `fnmatchcase` glob
matching with **no path normalization** (no `os.path.normpath`/`Path(...).resolve()` first). A
destination string containing a `..` segment that still lands inside `contracts/`/`docs/adr/`/
`golden/` once resolved on disk bypasses the glob (verified):

```python
>>> from fnmatch import fnmatchcase
>>> fnmatchcase("a/../contracts/x.json", "contracts/**")
False                                    # not denied — but on disk:
>>> from pathlib import Path
>>> Path("/tmp/target") / "a/../contracts/x.json"
PosixPath('/tmp/target/a/../contracts/x.json')   # os.link/os.replace will resolve this INTO contracts/
```

A case-variant (`CONTRACTS/x.json`) is likewise not denied by `fnmatchcase` (case-sensitive by
design), which matters because macOS's default APFS is case-insensitive — `CONTRACTS/x.json` and
`contracts/x.json` are the *same file on disk* on this repo's own target platform.

This is the exact opposite of the module's own docstring claim: *"apply.py therefore duplicates the
constitution-plane check as an explicit, structural, in-process precondition… called at the START of
apply_disposition, before any open()/os.link()/os.replace() call."* The precondition is structural
against a literal string, not against the path the filesystem will actually resolve — which is
precisely the gap the sibling control `refuse_if_outside_root` (line 87) gets right (it calls
`Path.resolve()` before comparing). `refuse_if_constitution` never does the equivalent.

This matters because `apply.py`'s own docstring states its threat model is exactly a caller with
"NO Claude hook anywhere in the loop" reading an arbitrary `manifest.json` — i.e., a manifest whose
`destination` field is not guaranteed to have come from `destinations.destination_catalog()`'s
sanitized enumeration (see CR-02 below: `cli.py`'s `apply` subcommand reads `manifest.json` off disk
with no integrity binding back to the drafted/approved batch at all).

**Fix:**
```python
def refuse_if_constitution(destination: str, target_root: str | Path | None = None) -> None:
    # Normalize the same way refuse_if_outside_root does — compare the RESOLVED, target-relative
    # path, never the raw string.
    normalized = Path(destination).as_posix()
    if target_root is not None:
        resolved_rel = (Path(target_root) / destination).resolve().relative_to(
            Path(target_root).resolve()
        ).as_posix()
        normalized = resolved_rel
    if resolve_path(CONSTITUTION_GLOBS, normalized.lower()) == "deny":  # or a case-normalizing resolver
        raise ConstitutionRefusal(...)
```
At minimum: reject any `destination` containing a `..` path segment or an absolute-path prefix
outright (defense in depth, independent of the glob), and normalize case before the glob compare
(or document/accept that this control assumes a case-sensitive filesystem and enforce that
assumption structurally, e.g. by refusing on any glob-matching case-insensitive collision).

---

### CR-02: `apply.py` performs no destination confinement — an absolute-path or `..`-traversal `destination` writes outside `target_root` entirely

**File:** `tools/adoption_apply/apply.py:213` (`target_path = Path(target_root) / destination`), `188-237` (`apply_disposition`)
**Issue:** `refuse_if_outside_root` (line 87) exists and is correctly resolved-path-based, but it is
**only ever called from `cli.py`'s `draft` subcommand** (`cli.py:113`) to confine
`inventory.json`/`plan.json`/`manifest.json` writes to the batch root. It is never called anywhere
in the `apply` write path. `apply_disposition` builds `target_path = Path(target_root) / destination`
and passes it straight to `atomic_create`/`_apply_marker_merge` with no check that the result is
still inside `target_root`.

Because `Path.__truediv__` discards the left operand entirely when the right operand is absolute,
and silently walks through `..` segments when the operating system later resolves the path for
`os.link`/`os.replace`, a `destination` value of `"/etc/cron.d/evil"` or
`"../../../../home/user/.ssh/authorized_keys"` in `manifest.json` is applied **outside
`target_root`, with no refusal at all** — verified:

```python
>>> Path("/tmp/target") / "/etc/passwd"
PosixPath('/etc/passwd')          # target_root silently discarded
```

`json schema` for `manifest.schema.json`'s `dispositionRecord.destination` only requires
`{"type": "string", "minLength": 1}` — it does not forbid `..` or an absolute-path value, so this
is not caught upstream either. `cli.py`'s `apply` subcommand (`cli.py:138-177`) reads
`manifest.json` from disk and passes it to `apply_manifest` with zero schema re-validation (`draft`
validates before writing; `apply` never does), so a manifest tampered with after drafting — by a
bug, a compromised intermediate process, or a hand-edited batch artifact — is trusted verbatim.

`refuse_if_outside_root`'s own docstring even names the scope gap explicitly: *"confines
discovery/draft-mode writes… to a given task artifact root"* — apply-mode writes are conspicuously
absent from that sentence.

**Fix:** In `apply_disposition`, resolve `target_path` and confine it to `target_root` the same way
`refuse_if_outside_root` already does for draft mode, before any write:
```python
target_path = Path(target_root) / destination
refuse_if_outside_root(target_path, target_root)   # NEW — apply-mode confinement, not just draft
```
And/or validate `manifest.json` against `manifest.schema.json` at the top of `cli.py::_cmd_apply`
before iterating `manifest["dispositions"]`, mirroring what `_cmd_draft` already does for its three
artifacts.

---

### CR-03: `apply` never checks `approval.check_valid()` — the ADOPT-06 human-ratification gate is entirely decoupled from the write path

**File:** `tools/adoption_apply/cli.py:138-177` (`_cmd_apply`), `tools/adoption_apply/apply.py:240-278` (`apply_manifest`)
**Issue:** Nothing in `cli.py`'s `apply` subcommand, nor in `apply.apply_manifest`/`apply_disposition`,
ever calls `tools.adoption_apply.approval.check_valid`. `check_valid` is imported and exercised only
by its own unit test (`tests/test_approval_invalidation.py`) — `grep -rn check_valid
tools/adoption_apply/` shows zero references from any of `apply.py`, `batch.py`, or `cli.py`. `cli.py`
does not even import `check_valid` (it imports `AdoptionApprovalRefused` and `promote`, but not
`check_valid`).

Concretely: `python -m tools.adoption_apply apply --task-dir <t> --batch-id <b> --target <tgt>`
succeeds and writes files whether or not `promote` was ever run for that batch, whether or not
`approval.json` exists at all, and whether or not a prior approval has since been invalidated by a
draft/task-revision/git-ref change. The only gate `apply` enforces is the per-destination
constitution-plane refusal (itself bypassable — CR-01) — there is no batch-level "has a human
ratified this?" check anywhere in the apply path.

This directly contradicts the phase's own documentation. `harness/skills/brownfield-adoption/SKILL.md`
Stage 5 states: *"a human reviews and decides, promotion ratifies those decisions, and **only then**
is the batch safely applied to the target"* — but the code makes no such ordering a requirement;
"only then" describes the advertised *workflow*, not an enforced *precondition*. `27-04-PLAN.md`/
`27-04-SUMMARY.md` frame `approval.py` as "the ADOPT-06 human-ratification gate (refuse-by-default
promotion)" — but a gate that nothing downstream consults is not a gate on `apply`, only a gate on
whether `approval.json` gets written. An agent (or any bare CLI/CI caller — the exact threat model
`apply.py`'s own docstring names) can skip `promote` entirely and apply a batch's dispositions
directly.

**Fix:** `_cmd_apply` (and/or `apply_manifest` itself) should require `approval.check_valid(task_dir,
batch_id, repo_root) is True` before applying any disposition, refusing (mirroring the `promote`
exit-3 idiom, e.g. exit 4) when no valid approval exists for the batch being applied:
```python
from tools.adoption_apply.approval import check_valid

def _cmd_apply(args):
    ...
    if not check_valid(args.task_dir, args.batch_id, _REPO_ROOT):
        print(f"tools.adoption_apply apply: no valid human approval for batch "
              f"'{args.batch_id}' — run 'promote' first.", file=sys.stderr)
        return 4
    ...
```
Add a test proving `apply` refuses when no `approval.json` exists, and when an existing approval is
stale (draft/task-revision/git-ref changed since promotion) — the exact scenarios
`test_approval_invalidation.py` already proves at the `check_valid` unit level, but which nothing
proves are actually *enforced* by the CLI's `apply` verb.

## Warnings

### WR-01: `_apply_marker_merge` performs an unlocked read-modify-write — concurrent `apply` invocations against the same marker-capable destination can race

**File:** `tools/adoption_apply/apply.py:166-185`
**Issue:** Unlike `batch.py`'s `update_status` (which takes an `fcntl.flock(LOCK_EX)` before its
CAS read-modify-write), `_apply_marker_merge` reads `target_path`'s existing text, merges it in
Python, and writes it back via `_atomic_replace` with no lock held across the read+merge+write. Two
concurrent `apply` runs against the same target's `AGENTS.md`/`CLAUDE.md`/`.claude/settings.json`
(e.g., two batches applied in parallel, or a retry racing a still-in-flight first attempt) can both
read the same "before" state and one write clobbers the other's merge, silently losing content —
`_atomic_replace`'s atomicity guarantees only that the final bytes land durably, not that the merge
computed against them was based on the latest state.
**Fix:** Take the same `fcntl.flock` idiom `batch.py`/`tools.task_control.manager` already use,
scoped to the target file (or the batch), around the read-merge-write sequence in
`_apply_marker_merge`.

### WR-02: `approval.check_valid` raises instead of returning `False` when a draft artifact is missing

**File:** `tools/adoption_apply/approval.py:172-187`, `57-63` (`_recompute_draft_hash`)
**Issue:** `check_valid`'s docstring promises "no partial credit — any single mismatch returns
`False`," but `_recompute_draft_hash` calls `path.read_bytes()` unconditionally for each of the 3
fixed draft filenames; if `inventory.json`/`plan.json`/`manifest.json` has been deleted or the batch
directory is otherwise incomplete, this raises `FileNotFoundError` rather than returning `False`,
propagating out of `check_valid` as an uncaught exception. A caller (once CR-03 is fixed and this
function is actually wired into `apply`) that doesn't specifically catch `FileNotFoundError` will
crash instead of getting a clean refusal.
**Fix:** Wrap the read loop and return `False` on `FileNotFoundError`/`OSError`, consistent with the
"any mismatch → False" contract already promised in the docstring.

### WR-03: `manifest.schema.json`'s `destination` field has no path-shape constraint

**File:** `contracts/harness/adoption/manifest.schema.json` (`dispositionRecord.destination`, `evidenceRef.path`)
**Issue:** `destination`/`path` are `{"type": "string", "minLength": 1}` only — the schema's own
description says "a repo-relative POSIX path," but nothing enforces that: an absolute path or a
`..`-containing path validates successfully. This is the upstream contract gap that lets CR-01/CR-02
manifest content pass schema validation undetected.
**Fix:** Add a `"pattern"` (e.g. `^(?!/)(?!.*\\.\\./)(?!.*/\\.\\./).+$` or equivalent) forbidding a
leading `/` and any `..` path segment, in both `dispositionRecord.destination` and
`excludedDestinationRecord.destination`/`evidenceRef.path`. This is a `contracts/` change and
therefore CODEOWNERS/human-ratified per this repo's own constitution-plane rule — flagged here for
the record, not to be auto-fixed by an agent.

### WR-04: `cli.py`'s `apply` subcommand never re-validates `manifest.json` against its schema before use

**File:** `tools/adoption_apply/cli.py:138-159`
**Issue:** `_cmd_draft` validates all three artifacts against their schemas before writing
(`cli.py:99-107`), but `_cmd_apply` reads `manifest.json` back with a bare `json.loads` and no
schema check. Combined with WR-03/CR-02, this means a malformed or tampered manifest is trusted at
the one place it's actually acted upon. Even independent of the security angle, a manifest missing a
required key (e.g. `"disposition"`) will surface as an unhandled `KeyError` traceback rather than the
clean, actionable stderr message the rest of `cli.py` provides for its other failure modes.
**Fix:** Call `_validate("manifest", manifest)` at the top of `_cmd_apply`, same idiom as `_cmd_draft`,
before dispatching to `apply_manifest`.

## Info

### IN-01: `apply.py` docstring's security claim is broader than what the code currently proves

**File:** `tools/adoption_apply/apply.py:1-37`
**Issue:** The module docstring asserts the constitution refusal and root confinement are "explicit,
structural" controls proven independent of any hook — true of the code *paths that exist*, but
overstated given CR-01/CR-02/CR-03. Once those are fixed, worth revisiting the docstring's claims
against the strengthened implementation so the prose doesn't outrun what's actually enforced again
in a future change.
**Fix:** No code change; a documentation accuracy pass alongside the CR-01..03 fixes.

### IN-02: `_recompute_draft_hash` hashes files in a fixed order but never validates their `sha256`/schema shape

**File:** `tools/adoption_apply/approval.py:57-63`
**Issue:** The draft-hash binding is a raw `sha256` over concatenated file bytes — correct for
detecting *any* byte-level change, but it doesn't distinguish "the manifest changed in a way the
human already re-reviewed" from "the manifest changed to something structurally invalid" (e.g. an
absolute-path destination per CR-02/WR-03) — the hash binding alone doesn't imply the bound content
was ever schema-valid. Not a bug per se (the hash's job is drift detection, not validation), but
worth noting alongside CR-03: even once `check_valid` is wired into `apply`, it only proves the
manifest is *unchanged since promotion*, not that the promoted manifest itself was safe (that's
`_cmd_draft`'s validation's job, currently not repeated at promote time either).
**Fix:** Consider validating `manifest.json` against schema inside `approval.promote` as well, not
only in `_cmd_draft`, so a promoted approval is bound to a manifest that was schema-valid at
promotion time too.

## Structural Findings (fallow)

None provided for this review — no `<structural_findings>` block was supplied.

---

_Reviewed: 2026-07-21_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
