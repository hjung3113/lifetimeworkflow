---
phase: 07-single-source-dual-runtime-emitter
reviewed: 2026-07-12T09:00:00Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - tools/harness_emit/generate.py
  - tools/harness_emit/project_agent.py
  - tools/harness_emit/project_command.py
  - tools/harness_emit/project_skill.py
  - tools/harness_emit/permissions.py
  - tools/harness_emit/merge.py
  - tools/harness_emit/validate.py
  - tools/harness_emit/manifest.py
  - tools/harness_emit/__main__.py
  - tools/harness_emit/__init__.py
  - tools/harness_lint/caps.py
  - .github/workflows/ci.yml
findings:
  critical: 2
  warning: 5
  info: 4
  total: 11
status: issues_found
---

# Phase 07: Code Review Report

**Reviewed:** 2026-07-12T09:00:00Z
**Depth:** standard
**Files Reviewed:** 12
**Status:** issues_found

## Summary

Reviewed the single-source dual-runtime emitter (`tools/harness_emit/*`), its shared cap
constants (`tools/harness_lint/caps.py`), and the CI mirror workflow. The determinism/idempotency
discipline (fixed frontmatter key order, LF/no-BOM output, validate-then-write) is generally solid
and the `_confine` traversal guard is applied consistently on every *write* path. However, two
findings undermine invariants the project explicitly calls out as MUST-hold:

1. `is_read_only()` — the function enforcing the read-only invariant for `code-reviewer`/`explorer`
   — can be silently bypassed if `permission.bash` is authored as a per-pattern object (the exact
   shape used elsewhere in this same codebase, e.g. `harness/opencode.json`'s own `permission.bash`)
   rather than a scalar. This is the authorization-gap class of bug the review brief specifically
   asks to hunt for.
2. `manifest.prune_then_write()` deletes files derived from a previously-committed JSON manifest
   without ever routing the delete target through `_confine` (or any other traversal check) — every
   *write* in this codebase is `_confine`d, but the *delete* path is not, breaking the "no traversal
   outside the harness lane" invariant (T-07-01) for the one operation in this module that actually
   removes files from disk.

Several further inconsistencies were found (validators that check length against differently-folded
text than what's emitted, an anti-drift guard that no-ops on the empty-set case, a shallow/non-
recursive model-identifier leak scan, and an unvalidated pass-through of extra permission-matrix
keys into committed `opencode.json`). None of the `.github/workflows/ci.yml` job definitions showed
event-data interpolation or other injection surface; that file is otherwise clean.

## Critical Issues

### CR-01: `is_read_only()` read-only invariant is bypassed by a nested `permission.bash` object

**File:** `tools/harness_lint/caps.py:71-83`
**Issue:** `is_read_only()` is the sole gate (`check_agent` + `check_projections` in
`tools/harness_emit/validate.py`) that stops a `READ_ONLY_PERSONAS` agent (`code-reviewer`,
`explorer`) from gaining write/shell access. It checks each of `edit`/`bash`/`write` like this:

```python
for key in ("edit", "bash", "write"):
    if str(perm.get(key, "deny")) == "allow":
        return False
```

`permission.bash` is documented elsewhere in this exact codebase (see
`project_agent.py`'s own docstring: *"the `permission.bash` sub-object keeps its AUTHORED
insertion order"*, and the real shape in `harness/opencode.json`) as **legitimately being an
object**, e.g. `{"*": "allow", "rm -rf*": "deny"}`, not just a scalar. If an author (or a bad
merge) sets `permission: {bash: {"*": "allow"}}` on `code-reviewer` or `explorer`, `perm.get("bash",
"deny")` returns that dict, `str({...})` never equals the literal string `"allow"`, the loop never
triggers, and `is_read_only()` returns `True` — silently certifying a persona as read-only while it
actually has unrestricted shell access. This defeats the exact invariant `check_projections` exists
to protect (EITHER-projection guard, T-07's core security property for these two personas).
**Fix:**
```python
def _bash_effectively_allows(perm: dict) -> bool:
    bash = perm.get("bash", "deny")
    if isinstance(bash, dict):
        # last-wins, "*"-first: any pattern resolving to "allow" grants shell (be conservative —
        # flag the read-only violation if ANY value is "allow", not just the last one).
        return any(str(v) == "allow" for v in bash.values())
    return str(bash) == "allow"

def is_read_only(fm: dict) -> bool:
    perm = _permission(fm)
    if _bash_effectively_allows(perm):
        return False
    for key in ("edit", "write"):
        if str(perm.get(key, "deny")) == "allow":
            return False
    tools = str(fm.get("tools", ""))
    return not any(tok in tools for tok in _WRITE_TOOL_TOKENS)
```

### CR-02: `manifest.prune_then_write()` deletes files without path confinement

**File:** `tools/harness_emit/manifest.py:48-75` (unlink at line 69)
**Issue:** Every *write* in this emitter is routed through `generate._confine()` before touching
disk (T-07-01: "no traversal outside the harness lane"). The *delete* path in
`prune_then_write()` is not:

```python
for rel in load_manifest(manifest_path):
    if rel in current_set or is_gsd_owned(rel):
        continue
    stale = root / rel
    if stale.exists():
        stale.unlink()
```

`rel` comes from a previously-committed `emit-manifest.json` `"paths"` array, joined directly onto
`root` with no call to `_confine` (or even `.resolve()` + parents check). `Path.exists()`/
`Path.unlink()` do **not** normalize `..` segments away — they resolve at the OS level — so an entry
like `"../../.ssh/authorized_keys"` (from a corrupted manifest, a bad merge conflict resolution, or
a manifest edited outside the emitter's own `_rel()` writer) would be deleted, entirely outside the
`.opencode/`/`.claude/`/`opencode.json`/`AGENTS.md`/`CLAUDE.md` harness lane this module is
documented to own. Every other delete-adjacent surface in this codebase treats "resolve + confine
before touching the filesystem" as non-negotiable; this is the one gap.
**Fix:**
```python
def prune_then_write(written: list[Path], manifest_path: str | Path, root: Path) -> Path:
    root = Path(root).resolve()
    current = sorted(_rel(p, root) for p in written)
    current_set = set(current)

    for rel in load_manifest(manifest_path):
        if rel in current_set or is_gsd_owned(rel):
            continue
        stale = (root / rel).resolve()
        if root != stale and root not in stale.parents:
            continue  # refuse to delete outside the harness lane — loud silence, not a crash
        if stale.exists():
            stale.unlink()
    ...
```

## Warnings

### WR-01: `check_agent` measures description length against un-folded text, inconsistent with what is actually emitted

**File:** `tools/harness_emit/validate.py:63-70`
**Issue:** `check_agent` computes `desc = str(fm.get("description", "")).strip()` and caps that
raw length at `_DESC_MAX`. But `generate._emit_scalar` folds the description
(`_dquote(_fold(text))`) before writing it, and `check_command`/`check_skill` both validate against
the *folded* length (`_fold(fm.get("description", ""))`). Folding only ever shrinks length, so this
is not exploitable as an emitted-cap bypass, but it is an inconsistent, overly-conservative check
that can loud-fail a perfectly valid agent (e.g. one authored with a literal block scalar containing
extra blank lines) purely because the validator measures something different from what is emitted.
**Fix:** Use `_fold` for the agent description check too, matching `check_command`/`check_skill`:
```python
desc = _fold(fm.get("description", ""))
```

### WR-02: Skill anti-sprawl guard (`check_skill_set`) silently no-ops on an empty skill set

**File:** `tools/harness_emit/generate.py:356-362`
**Issue:**
```python
skills = iter_skills(harness_dir / "skills")
for name, fm, body, skill_dir in skills:
    ...
if skills:  # anti-drift: the emitted set must equal EXPECTED_SKILLS exactly (real tree = 9)
    validate.check_skill_set({name for name, _, _, _ in skills})
```
`check_skill_set` exists specifically to guarantee the discovered skill directories equal
`EXPECTED_SKILLS` exactly (9, no more/fewer). Gating the call behind `if skills:` means that if
`harness/skills/` is ever emptied out (accidental `rm -rf`, a bad rebase, a misconfigured
`harness_dir`), the check is skipped entirely rather than failing loud on "0 skills, expected 9" —
exactly the regression this guard is meant to catch.
**Fix:** Call `check_skill_set` unconditionally:
```python
validate.check_skill_set({name for name, _, _, _ in skills})
```

### WR-03: `check_opencode_config`'s model-identifier leak scan is shallow (top-level keys only)

**File:** `tools/harness_emit/validate.py:215-222`
**Issue:**
```python
for key, value in config.items():
    if key == "model" or key.endswith("_model"):
        if not _PLACEHOLDER_MODEL_RE.match(str(value)):
            _fail(...)
```
This only inspects top-level keys of the emitted `opencode.json`. The vendored subset schema
(`harness/opencode.config.schema.json`) declares `"additionalProperties": true`, explicitly
permitting future keys (e.g. per-agent config nested under `"agent": {"<name>": {"model": "..."}}`,
which is a real opencode.json shape, or a model reference nested inside `"mcp"`). A real provider
model identifier introduced anywhere other than a top-level `model`/`*_model` key would pass this
check and be emitted uncaught, defeating the model-identity constraint (T-07-03) this function is
supposed to guarantee.
**Fix:** Recurse into nested dicts/lists when scanning for `model`/`*_model` keys, e.g.:
```python
def _walk_model_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if k == "model" or k.endswith("_model"):
                yield p, v
            yield from _walk_model_keys(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_model_keys(v, f"{path}[{i}]")

for key, value in _walk_model_keys(config):
    if not _PLACEHOLDER_MODEL_RE.match(str(value)):
        _fail(f"opencode.json {key}={value!r} is not a placeholder tier token ...")
```

### WR-04: `build_permission_block` doesn't validate the merged block against the 15 valid permission keys

**File:** `tools/harness_emit/permissions.py:26-33`
**Issue:** `build_permission_block` only strips the two known resolver-only fields (`_note`,
`path_deny_globs`) — it never asserts that what remains is exactly the 15 valid opencode permission
keys (`ALLOWED_PERMISSION_KEYS` / `VALID_PERMISSION_KEYS` already exist in `caps.py` for this exact
purpose and are used by `validate.check_agent`, but never applied here). A typo'd key in
`harness/permission-matrix.json` (e.g. `"eidt"` instead of `"edit"`) would pass straight through
into the committed `opencode.json`. `check_opencode_config`'s schema doesn't close this gap either —
the nested `"permission"` object in `harness/opencode.config.schema.json` has no
`additionalProperties: false`, so a stray key isn't caught by schema validation.
**Fix:**
```python
def build_permission_block(matrix: dict) -> dict:
    block = {k: v for k, v in matrix.items() if k not in _RESOLVER_ONLY_KEYS}
    from tools.harness_lint.caps import VALID_PERMISSION_KEYS
    extra = set(block) - VALID_PERMISSION_KEYS
    if extra:
        raise ValueError(f"permission-matrix.json has invalid/unknown key(s): {sorted(extra)}")
    return block
```

### WR-05: `_PLAIN_VALUE` frontmatter serializer doesn't guard against YAML-ambiguous plain scalars

**File:** `tools/harness_emit/generate.py:75, 93-103`
**Issue:** `_emit_scalar` emits a value unquoted whenever it matches `_PLAIN_VALUE`
(`^[A-Za-z0-9][A-Za-z0-9 _./,*+-]*$`), for every frontmatter key except `description` (which is
always folded+quoted). This regex has no allowlist/denylist for YAML 1.1-reserved plain-scalar
tokens (`null`, `true`, `false`, `yes`, `no`, `on`, `off`, or a bare-numeric-looking string). None of
today's controlled vocabularies (`mode`, `model`, `agent` slugs, `tools` lists) happen to collide,
but nothing in the serializer prevents a future frontmatter value from silently round-tripping as
the wrong YAML type (e.g. a hypothetical `agent: no` would parse back as boolean `False`, not the
string `"no"`). This is a latent correctness bug class in a module whose entire purpose is
byte-exact, type-preserving re-serialization.
**Fix:** Explicitly quote a value matching YAML's reserved-word set regardless of `_PLAIN_VALUE`:
```python
_YAML_RESERVED = {"null", "~", "true", "false", "yes", "no", "on", "off"}
...
if text.lower() in _YAML_RESERVED or (_PLAIN_VALUE.match(text) and text[0].isdigit()):
    return _dquote(text)
```

## Info

### IN-01: `GSD_SIGNATURES` is declared but never used

**File:** `tools/harness_emit/merge.py:97-102`
**Issue:** `GSD_SIGNATURES` is documented as "defensive" and "makes the coexistence invariant
explicit" but is never referenced by `merge_settings` or anything else in the module — it's dead
code that could silently drift from reality (e.g. a new GSD hook signature added elsewhere) without
any code depending on it to notice.
**Fix:** Either wire it into an explicit assertion (e.g. warn/fail if a "GSD" group's command
unexpectedly also matches a harness signature) or remove it and fold the intent into a comment.

### IN-02: `_canonicalize`'s "preserve `bash` order" rule matches by bare key name, not by path

**File:** `tools/harness_emit/permissions.py:36-54` (line 47)
**Issue:** `if key == "bash" and isinstance(value, dict):` matches *any* dict-valued key literally
named `"bash"` anywhere in the config tree, not specifically `permission.bash`. Currently harmless
(no other `"bash"` key exists in `harness/opencode.json`), but it's a loose, path-unaware coupling
that would silently change behavior (skip sorting) if a future unrelated key happened to be named
`bash` (e.g. inside `mcp` server config).
**Fix:** Match on path (`permission.bash`) rather than bare key name, or pass the traversal context
explicitly instead of relying on a magic key name.

### IN-03: `prune_then_write` leaves empty directories behind after pruning stale files

**File:** `tools/harness_emit/manifest.py:64-69`
**Issue:** When a skill (or its `references/` subtree) is removed from `harness/`, the individual
stale files are unlinked, but the now-empty parent directories (e.g.
`.opencode/skill/<removed-name>/`) are never cleaned up. Cosmetic, but it means a renamed/removed
skill leaves an empty directory turd in the emitted tree indefinitely.
**Fix:** After the unlink loop, walk the pruned paths' parent directories bottom-up and `rmdir()`
any that are now empty (guarded by the same GSD-exclusion / root-confinement check as CR-02's fix).

### IN-04: Agent anti-sprawl invariant (`EXPECTED_PERSONAS`) is enforced only by a structural lint test, not by the emit-time validator — asymmetric with skills

**File:** `tools/harness_lint/caps.py:54`; absent from `tools/harness_emit/validate.py`
**Issue:** `EXPECTED_SKILLS` has a matching emit-time gate (`validate.check_skill_set`, called from
`generate.emit`). `EXPECTED_PERSONAS` has no equivalent — it's only checked by
`tools/harness_lint/tests/test_agents.py`, a separate structural-lint suite. Both are still covered
by CI (the `core-suite` job runs the full `pytest` suite), so this isn't an enforcement gap in
practice, but it's an inconsistent design: one artifact type (skills) gets its anti-drift check
inlined into the loud-fail emit path, the other (agents) relies entirely on a separate test suite
running in CI, which is a weaker guarantee for anyone invoking `python -m tools.harness_emit`
directly outside CI.
**Fix:** Add a `validate.check_agent_set` mirroring `check_skill_set`, called from `generate.emit`
alongside the per-agent loop, for parity with the skill path.

---

_Reviewed: 2026-07-12T09:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
