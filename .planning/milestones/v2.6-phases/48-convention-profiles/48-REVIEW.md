---
phase: 48-convention-profiles
reviewed: 2026-07-30T00:54:03Z
depth: deep
files_reviewed: 7
files_reviewed_list:
  - tools/harness_config/loader.py
  - tools/harness_config/__init__.py
  - tools/harness_config/tests/test_conventions_for.py
  - tools/memory_regen/package_facts.py
  - tools/memory_regen/tests/test_package_facts.py
  - tools/harness_lint/tests/test_commands.py
  - harness/commands/component.md
findings:
  critical: 1
  warning: 3
  info: 2
  total: 6
status: issues_found
---

# Phase 48: Code Review Report

**Reviewed:** 2026-07-30T00:54:03Z
**Depth:** deep
**Files Reviewed:** 7
**Status:** issues_found

## Summary

Reviewed the MONO-05/MONO-06 convention-profile lookup (`conventions_for()` +
`_nearest_agents_md()`), its `package_facts.render()` consumer, and the associated tests/command
doc changes. Most of the layering work (`effective_packages()`/`conventions_for()` join, the
`"dir"`-key filter, the render section's determinism) is sound and matches its own docstrings.
However, `_nearest_agents_md()` — the one genuinely new filesystem-walking algorithm this phase
adds — does **not** actually honor its own documented "never inspects anything above the repo
root" guarantee. I reproduced a live, unhandled crash (`ValueError`) triggered by a relative
(`../..`) or absolute `dir` value, and confirmed the walk reads file-existence information from
outside the repository tree before crashing. This is a real, provable defect against a
security-relevant invariant the code explicitly claims to hold, not a hypothetical. No test in
this phase exercises this path — the "checks that cannot fail" pattern this repo watches for
shows up here as an untested claim rather than a tautological assertion.

Also flagged: a layering inconsistency in `package_facts.render()` (queries `conventions_for()`
with the pre-merge `dir`, not the effective/merged one), a `"dir"`-key filter in `conventions_for()`
that cannot distinguish "legitimately declared-only" from "malformed/missing dir" and silently
drops either, and two minor test/coverage gaps.

## Critical Issues

### CR-01: `_nearest_agents_md()` walks and crashes above the repo root, contradicting its documented invariant

**File:** `tools/harness_config/loader.py:257-276`

**Issue:** The docstring states the walk is "never inspects anything above the repo root" and
that it stops "once `_REPO_ROOT` itself has been checked". In fact the loop only breaks when a
probe happens to equal `_REPO_ROOT` exactly:

```python
candidate = (_REPO_ROOT / dir_).resolve()
search_path = [candidate, *candidate.parents]
for probe in search_path:
    if (probe / "AGENTS.md").is_file():
        return (
            probe.relative_to(_REPO_ROOT).as_posix() + "/AGENTS.md"
            if probe != _REPO_ROOT
            else "AGENTS.md"
        )
    if probe == _REPO_ROOT:
        break
```

If `candidate` ever resolves to a location that is not inside `_REPO_ROOT` at all, the walk never
hits the break condition and continues climbing `.parents` all the way to the filesystem root,
checking arbitrary ancestor directories for `AGENTS.md`. This happens in two concrete ways:

1. **Path-escaping `dir_`** (e.g. `"../../etc"`): `.resolve()` collapses the `..` segments and
   lands outside the repo.
2. **Absolute `dir_`** (e.g. `"/etc"`): `Path` join semantics mean `_REPO_ROOT / "/etc" == Path("/etc")`
   — the absolute right-hand operand silently discards `_REPO_ROOT` entirely (a well-known
   pathlib gotcha).

In both cases, if an `AGENTS.md` happens to exist above/outside the repo, the function then calls
`probe.relative_to(_REPO_ROOT)`, which raises an **unhandled `ValueError`** because `probe` is not
a subpath of `_REPO_ROOT`. I reproduced this live in this checkout:

```
$ uv run python -c "from tools.harness_config.loader import _nearest_agents_md; _nearest_agents_md('../../etc')"
...
ValueError: '/Users/hyojung' is not in the subpath of '/Users/hyojung/Desktop/2026/lifetimeworkflow' ...
```

(The crash was triggered by an unrelated `~/AGENTS.md` file that exists on this machine — proving
the walk left the repo tree, inspected an ancestor's file-existence, and then crashed instead of
returning `None` or raising a scoped error.) The same happens for an absolute `dir_` such as
`"/etc"`.

`owner["dir"]` (the value passed into `_nearest_agents_md`) is not attacker-controlled today — it
comes from `build_facts()` (always a safe git-relative path) or a human-authored
`[[components]]` entry in `harness/project.toml`. But it IS exactly the kind of value a config
typo (`dir = "../foo"`, or an accidentally-absolute path pasted into TOML) can produce, and the
function's own docstring makes an explicit safety claim that the code does not honor. No test in
`test_conventions_for.py` exercises a traversal or absolute `dir_` value, so this regressed
silently and will regress again.

**Fix:** Validate/normalize `dir_` before walking, and bound the walk defensively rather than by
optimistic equality:

```python
candidate = (_REPO_ROOT / dir_).resolve()
try:
    candidate.relative_to(_REPO_ROOT)
except ValueError:
    raise ValueError(f"_nearest_agents_md: {dir_!r} resolves outside the repo root")

for probe in (candidate, *candidate.parents):
    if probe == _REPO_ROOT.parent:  # never step above the root
        break
    if (probe / "AGENTS.md").is_file():
        return "AGENTS.md" if probe == _REPO_ROOT else probe.relative_to(_REPO_ROOT).as_posix() + "/AGENTS.md"
    if probe == _REPO_ROOT:
        break
return None
```

(Any equivalent fix works, as long as it fails closed on out-of-root `dir_` rather than walking
past the boundary and crashing.)

## Warnings

### WR-01: `package_facts.render()` resolves conventions from the pre-merge `dir`, not the effective/merged one

**File:** `tools/memory_regen/package_facts.py:307-308`

**Issue:** `render()` loops over the raw `facts["packages"]` (straight from `build_facts()`) and
calls `conventions_for(pkg["dir"], cfg=cfg, facts=facts)` for each. Internally, `conventions_for`
resolves the owner via `effective_packages(cfg, facts)`, which — per its own docstring — lets a
`[[components]]` entry with a matching `id` **overwrite** that package's `dir` field. If such an
override exists for a package that also appears in `facts["packages"]`, the render loop still
queries ownership using the package's *pre-override* directory, not the dir that
`effective_packages()` actually assigned it. The row rendered for that package could therefore
resolve to the wrong owner (or a stale profile) whenever a `[[components]]` entry relocates a
package's `dir`. No current `[[components]]` entry in `harness/project.toml` exercises this, and
no test covers it, so the gap is latent rather than currently observable.

**Fix:** Iterate over `effective_packages(cfg, facts)` (or at least resolve the profile via the
package's *merged* `dir`) rather than the raw `build_facts()` list, so the rendered profile always
matches the same layering `conventions_for()` itself uses.

### WR-02: The `"dir"`-key filter in `conventions_for()` cannot distinguish "declared-only" from "malformed"

**File:** `tools/harness_config/loader.py:303-307`

**Issue:**

```python
dir_pkgs = [p for p in pkgs if "dir" in p]
```

This is documented as filtering out declared-only `[[components]]` entries (which legitimately
lack a `dir`). But it applies uniformly to every record from `effective_packages()` — including a
*derived* package that is missing `dir` for any other reason (e.g. a future bug in
`build_facts()`, or a `[[components]]` override that sets `"dir": None` rather than omitting the
key entirely, which `PurePosixPath(None)` would then blow up on inside `owning_package` had this
filter not silently dropped it first). A record that should be surfaced as a data error is instead
silently excluded from ownership resolution, which can then make an unrelated ancestor package
"win" ownership of that path with no diagnostic. This masks the exact class of bug the "checks
that cannot fail" convention in this repo is meant to catch.

**Fix:** Narrow the filter to genuinely declared-only records (e.g. also require `"manifest" not
in p`, which only a base/derived package carries), or emit a stderr diagnostic when a record is
dropped for lacking `dir` so a malformed input is at least visible.

### WR-03: `test_command_count_is_stable`'s pinned literal has no linkage back to `EXPECTED_GOLDEN_ADJACENT`

**File:** `tools/harness_lint/tests/test_commands.py:63-70`

**Issue:** This is a legitimate, non-tautological gate (the `18` literal is independent of the
glob call it checks, confirmed by counting `harness/commands/*.md` directly — currently 18).
However, nothing ties the count to the six-name `EXPECTED_GOLDEN_ADJACENT` set or to any manifest
of the other twelve command names, so a future PR could delete `component.md` and add an unrelated
command in the same change, keeping the count at 18 while silently dropping a golden-adjacent
command — `test_golden_adjacent_commands_present` would still fail in that specific case, but a
swap between two *non*-golden-adjacent commands would pass both tests silently. This is a
lower-severity gap than a tautology, but worth strengthening given the module's explicit intent
("a durable, self-proving gate for future phases' 'N -> N' claims").

**Fix:** Consider asserting the full stable command-name set (not just the count and the
golden-adjacent subset), or add a comment explaining why a full-name assertion was deliberately
not chosen.

## Info

### IN-01: Synthetic `conventions_for()` fixtures are not fully hermetic for `agents_md`

**File:** `tools/harness_config/tests/test_conventions_for.py`, `tools/memory_regen/tests/test_package_facts.py`

**Issue:** The module docstring in `test_conventions_for.py` describes the synthetic fixtures as
"hermetic (no monkey-patching, no temp-file config)". That's true for `cfg`/`facts`, but
`_nearest_agents_md()` always walks the **real** repo filesystem rooted at `_REPO_ROOT` — it is
not injectable. In the `test_package_facts.py` snapshot fixture, synthetic package dirs like
`widget-app`/`widget-core` don't exist on disk, so every row's `agents_md` value resolves to the
real repo root's `AGENTS.md` purely because the fake directories don't exist and the walk falls
through — not because the test actually validated nested-AGENTS.md resolution for those packages.
The `_render_value(None)` branch for `agents_md` (`"(none)"`) is consequently never exercised by
any test in this phase, since in this repo the walk always eventually finds the real root
`AGENTS.md` (assuming it isn't also broken by CR-01's crash first).

**Fix:** Either make `_nearest_agents_md` injectable (accept an optional root override for tests)
or add an explicit code comment in the fixtures noting that `agents_md` values are coincidental
real-tree artifacts, not asserted synthetic behavior — and add one test that proves the `None`
(no-`AGENTS.md`-found) branch of `_render_value` actually renders `"(none)"`.

### IN-02: `effective_packages()`'s declared-only-component contract isn't directly exercised through `conventions_for()`

**File:** `tools/harness_config/loader.py:279-320`

**Issue:** `conventions_for()`'s docstring cites the `"dir"`-filter as handling "a declared-only
component (no `dir` key, see `effective_packages`'s Pitfall 1)", but no test in
`test_conventions_for.py` actually constructs a `[[components]]`-only (no matching facts package)
fixture and calls `conventions_for()` against it to prove the filter behaves as documented (as
opposed to just being read from the source). Given WR-02 above, a direct test would also catch a
future regression in the filter's scope.

**Fix:** Add a fixture combining one derived package and one declared-only `[[components]]` entry
(no `dir`), and assert `conventions_for()` resolves ownership to the derived package without
raising, to make the "Pitfall 1" claim falsifiable rather than asserted-by-docstring only.

---

_Reviewed: 2026-07-30T00:54:03Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
