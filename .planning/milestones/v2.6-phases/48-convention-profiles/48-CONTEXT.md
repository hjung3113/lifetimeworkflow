# Phase 48: Convention Profiles - Context

**Gathered:** 2026-07-30
**Status:** Ready for planning
**Mode:** Smart discuss (autonomous) — 3 areas, all accepted as recommended

<domain>
## Phase Boundary

Deliver nearest-wins per-package convention data: asking "which conventions apply here?" from any
path returns the enclosing package's profile, and from a path with no enclosing package returns the
repo-wide default. Lint/test commands are **derived** from the existing `[[languages]]` slot, never
restated in a profile. `/component` populates a profile for a new package inside its existing
step 2.

**No new command** (live count 18 → 18), no new gate, no new CI job, nothing injected into
SessionStart.

Out of the boundary: convention *enforcement* (a gate), prose-rule generation competing with
`AGENTS.md`, and `/impact` (Phase 49).

</domain>

<decisions>
## Implementation Decisions

### Profile representation
- Profiles are **derived**, not authored: each is a join of the Phase-47 package facts
  (`tools/memory_regen/package_facts.py` → `.memory/derived/package-facts.md`) with the
  `[[languages]]` rows in `harness/project.toml`. No new per-package file exists to drift.
- The query surface is a function in `tools/harness_config` (e.g. `conventions_for(path)`) that both
  agents and `/component` call. **No new command.**
- The repo-wide default is the **root package's record** (the root `pyproject.toml`), not a
  separately hand-written default block.
- Profile fields: package id, package dir, language, the inherited test and format commands, the
  language's `bash_scope`, and a **pointer** to the nearest `AGENTS.md`.

### Nearest-wins semantics
- Resolution **reuses** `tools/contract_graph/ownership.py`'s `owning_package()` segment-based
  nearest-enclosing-package lookup. No second path matcher is written.
- A path with no enclosing package returns the repo-wide default, explicitly marked as the default
  (so a caller can tell "default" from "this package happens to match the default").
- The nested-case proof uses a **real** nested pair — `libs/python` inside the root package — where
  the inner answer differs from the enclosing one. Fixtures may supplement, not replace, this.
- A package whose language is absent from `[[languages]]` yields a profile that reports the language
  with **no commands** rather than raising. A missing toolchain declaration is a gap to report, not
  a crash.

### `/component` integration & surface discipline
- The profile is populated **inside step 2**, after the self-sufficient `AGENTS.md` write. The
  mandated order stays structure → AGENTS.md → tests; no step 4 is added.
- Step 2's action is: regenerate the derived profile data and assert the new package now resolves.
  It does not write a per-package profile file.
- The derived artifact is **committed** and rides the **existing** `stale-derived` CI job, exactly
  as `.memory/derived/package-facts.md` does — no new job, no new gate.
- The profile **points at** the nearest `AGENTS.md` and never copies its prose. Two sources that
  could disagree is the failure mode being avoided.

### Resolved after research (2026-07-30)
- **Extend the existing artifact, do not add a sibling.** The convention profiles become additional
  section(s) of `.memory/derived/package-facts.md` via `package_facts.py`'s `build_facts()` /
  `render()`. That costs **zero** `ci.yml` diff and zero `.gitignore` diff — a second artifact would
  mean re-widening the `stale-derived` job again, which is exactly the growth this milestone forbids.
- **`conventions_for()` takes a repo-relative path**, mirroring `owning_package()`'s own contract.
- **An adapter filter is required before calling `owning_package()`.** `effective_packages()` can
  return declared-only `[[components]]` entries that carry no `"dir"` key (true of both live configs
  today), and `owning_package()` indexes `"dir"` — so filter to records that have a `dir` before
  resolving. Do NOT add the filter inside `ownership.py`; keep that function untouched.
- **The real nested pair proves nesting, not command divergence.** `libs/python` is genuinely nested
  inside the root package, but both are `python` (one `[[languages]]` row), so their test/format
  commands are identical. Criterion 1's "inner differs from enclosing" must therefore key on package
  id / dir / nearest-`AGENTS.md` (both `libs/python/AGENTS.md` and root `AGENTS.md` exist). A
  synthetic two-language fixture additionally proves the commands-differ case — the real pair alone
  would leave that untested.
- **MONO-06's falsifiable proof uses the repo's existing pure-function idiom**: pass synthetic
  `cfg` / `facts` dicts straight into the function (as `tools/harness_config/tests/
  test_effective_packages.py` already does). No monkeypatching, no temp-file config.
- **The 18 → 18 command count has no existing assertion.** `test_commands.py` is glob/subset-driven
  only. Add a durable count-stability test rather than relying on a one-time manual measurement.

### Claude's Discretion
- Whether the derived profile data is a separate artifact or additional section(s) of the existing
  package-facts artifact — pick whichever keeps the committed-derived set smaller while still
  regenerating byte-identically.
- Exact function/module naming and the field spelling in the rendered output.
- Test layout and which fixture cases supplement the real nested-pair proof.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/memory_regen/package_facts.py` — `discover_manifests()`, `build_facts()`, `render()`,
  `write()`, `main()`; the committed artifact `.memory/derived/package-facts.md` lists every package
  with manifest path, dir, language and intra-repo edges (Phase 47).
- `tools/contract_graph/ownership.py` — `owning_package()`, a pure segment-based
  nearest-enclosing-package lookup with a root fallback; stdlib-only, no graph coupling.
- `tools/harness_config/loader.py` — `load_project()`, `languages()`, `components()`,
  `effective_packages()` (Phase 47's override layering), `language_bash_scopes()`.
- `harness/project.toml` `[[languages]]` — owns `id`, `bash_scope`, `test`, `format`, `test_paths`
  (and `sdk_bootstrap`/`persona` where applicable). The single source for commands.
- `harness/commands/component.md` (35 lines) — the mandated order: structure → self-sufficient
  AGENTS.md → tests, with the order stated as an enforced guard.

### Established Patterns
- Derived plane: generated under `tools/`, never hand-edited, `DERIVED — do not hand-edit
  (<generator>)` header, no timestamps, byte-identical on regeneration, freshness on the existing
  `stale-derived` job.
- Config is pure DATA; consistency is enforced by `tools/harness_lint` tests, not codegen.
- GEN-04: nothing under `tools/`, `harness/`, `libs/` may name or path-reference an instance
  (`examples/`) — tests, comments and docstrings included.
- Nearest-wins `AGENTS.md` prose shipped in Phase 2; 7 files tracked, 3 of them adoption fixtures.

### Integration Points
- `harness/commands/component.md` step 2 is the write path for new packages.
- `stale-derived` job (`.github/workflows/ci.yml:271`) already regenerates `docs/reference`,
  `.memory/derived/contracts-index.md` and `.memory/derived/package-facts.md`.
- Emitter: any edit to `harness/commands/component.md` must be re-emitted to both runtime trees via
  `tools.harness_emit`; the generated `.opencode/` and `.claude/` trees are never hand-edited.

</code_context>

<specifics>
## Specific Ideas

- MONO-06's proof must be falsifiable in the strong form: change a command in `[[languages]]`,
  regenerate, and observe every affected profile's reported command change **with no profile
  edited**. A test that merely asserts a profile contains a string equal to the config value it was
  copied from would be a check that cannot fail.
- Command count must be measured before and after: 18 → 18.

</specifics>

<deferred>
## Deferred Ideas

- A convention-enforcement gate (e.g. failing CI when a package's actual commands diverge) — adding
  a gate contradicts the v2.6 no-growth constraint.
- Generating per-package prose from the profile — would create a second source competing with
  `AGENTS.md`.

</deferred>
