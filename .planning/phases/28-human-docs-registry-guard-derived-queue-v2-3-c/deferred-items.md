# Phase 28 — deferred items (out of scope for the discovering plan)

## DEF-28-01 — GEN-04 breach in plan 28-05's shipped `tools/docs_guard`

**Discovered by:** plan 28-07, Task 1 (its automated gate is
`uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -q`).

**Status at discovery:** already RED at `HEAD`, introduced by `6db057c feat(28-05): five-state docs
guard with read-only ratchets and drift suppression`. Not caused by 28-07 — the GEN-04 scanner reads
only git-tracked files under `tools/`, `harness/`, `libs/`, and 28-07's only artifact
(`docs/doc-dependencies.toml`) is under `docs/` and carries zero instance-tree tokens.

**Offending lines:**

```
tools/docs_guard/guard.py:97          — a comment naming the instance tree literally
tools/docs_guard/tests/test_guard.py:476  — a fixture path under the instance tree
tools/docs_guard/tests/test_guard.py:486  — the same fixture path
```

**Why deferred rather than auto-fixed:** the files belong to plan 28-05, not 28-07. `guard.py:97`'s
comment is deliberate documentation of the `_EXCLUDED_TOP_LEVEL` rationale and
`test_guard.py`'s rows are the fixture that PROVES the instance tree is excluded from `HUMAN_CORPUS`
— rewording either is a 28-05 design decision, and editing another plan's shipped tests while wave 4
is in flight risks a conflict with plan 28-08's fan-in.

**Suggested remedy (for 28-08 or a follow-up):** the scanner already exempts its own file as a
negative control; the equivalent seam for a legitimately-required literal is either an explicit
exemption for `tools/docs_guard/tests/**` fixtures, or spelling the fixture path through a
constructed constant rather than an inline literal. `guard.py:97`'s comment can simply drop the
literal path and say "the instance tree" (which is what 28-07 did in its own registry comment).
