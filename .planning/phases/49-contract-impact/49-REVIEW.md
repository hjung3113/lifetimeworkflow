---
phase: 49-contract-impact
reviewed: 2026-07-30T03:53:43Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - tools/contract_graph/impact.py
  - tools/contract_graph/tests/test_impact.py
  - tools/harness_lint/tests/test_commands.py
  - tools/harness_lint/tests/test_orchestrator_topology.py
  - tools/harness_emit/tests/test_coexist.py
  - harness/commands/impact.md
  - harness/agents/orchestrator.md
  - .opencode/command/impact.md (and .claude/commands/impact.md, generated projections)
findings:
  critical: 3
  warning: 4
  info: 2
  total: 9
status: issues_found
---

# Phase 49: Code Review Report

**Reviewed:** 2026-07-30T03:53:43Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

`impact.py` does compose (not re-derive) `direct`/`reverse`/`transitive` as claimed, and the
happy-path traversal tests are sound. But the one genuinely new piece of logic —
`_resolve_node`'s filename-to-contract-id derivation and its bare-node-id fallback — has two
provable correctness bugs (path-traversal collision, and false refusal on legitimately isolated
nodes), and the module's exit-code/`"searched"` refusal contract does not deliver what its own
docstring and `harness/commands/impact.md` promise. The extended "no second traversal engine"
structural test in `test_impact.py` is itself a textbook instance of this repo's known failure
mode ("checks that cannot fail"): it is provably evadable by a one-line variable alias, a
comprehension, or mutual recursion — none of which are exotic rewrites, they're the *first* thing
a future edit would plausibly do. All three are demonstrated below with runnable reproductions,
not speculation.

## Critical Issues

### CR-01: `_resolve_node` collides unrelated paths onto the same contract id (basename-only derivation)

**File:** `tools/contract_graph/impact.py:63`
**Issue:** `candidate_id = Path(contract_path).name.removesuffix(".schema.json")` derives the
contract id purely from the path's final filename component and discards the directory entirely.
Any path that merely *ends* in the correct leaf filename resolves identically to the real
contract path — including a wrong-directory typo, a `../../` traversal, or a completely
fabricated absolute path, as long as the last segment matches. Reproduced live:

```
real node: a bogus node: a
same result? True
```
for `report("contracts/sample/widget.schema.json", cfg=cfg)` vs.
`report("contracts/WRONG-DIR/../../etc/widget.schema.json", cfg=cfg)` — both resolve to node `a`
and return byte-identical `direct`/`reverse`/`transitive` payloads. Because this is the
`contract-change` route's PRE-EDIT evidence step (per `harness/commands/impact.md`), an engineer
who fat-fingers the directory of a contract path (or copy-pastes a stale/wrong path that happens
to share a filename with a real, unrelated contract) gets a fully-confident, "resolved" affected-set
report for the WRONG contract — with no signal that anything is amiss. This is exactly the
"dangerous failure mode" the module's own docstring warns against (collapsing a bad input into a
confident answer), just via a different mechanism than the one the docstring anticipated.
**Fix:** Resolve against the full path (e.g., match `contract_path` against the actual tracked
`contracts/**/<id>.schema.json` glob path, or require the relationship record to carry/validate a
directory-qualified contract location) instead of trusting the bare filename; at minimum, reject
paths containing `..` segments before deriving `candidate_id`.

### CR-02: Bare-node-id resolution silently fails for any legitimately isolated authority

**File:** `tools/contract_graph/impact.py:69-71`
**Issue:** The bare-node-id fallback tests `contract_path in adjacency or any(contract_path in deps
for deps in adjacency.values())`. But `compile_graph()` (`tools/contract_graph/compile.py`) only
ever inserts an authority into `adjacency` when it has at least one *resolved* dependent
(`if resolved_dependents: adjacency.setdefault(authority, [])`) — an authority whose relationship
has an empty `dependents` list (a legitimate, isolated node — exactly the shape
`test_refused_isolated_and_affected_reports_are_key_set_distinguishable` exercises) is NEVER a key
or a value in `adjacency`. Reproduced live: the same node "iso" resolves fine via its contract
path but is refused when addressed directly by its bare id:

```
via contract path: True
via bare node id: {'resolved': False, 'contract_path': 'iso', 'contract_id': 'iso', 'searched': 2}
```

Every test in `test_impact.py` that exercises the isolated case (`test_refused_isolated_and_
affected_reports_are_key_set_distinguishable`) goes through the contract-*path* branch, never the
bare-id branch, so this gap is untested and unnoticed. This directly contradicts the module's
stated intent that isolated-but-resolved and refused reports must be distinguishable by real
content, not by which addressing style happened to be used — `/impact iso` for a real, declared,
isolated component produces the identical refusal shape as `/impact totally-bogus-string`.
**Fix:** Resolve bare node ids against the declared component/member id sets (`components(cfg)` /
`members(cfg)`, or the full `relationships` authority list), not against `adjacency` membership,
which is a stricter and wrong proxy for "is a valid graph node."

### CR-03: Refusal (exit 1) and an unhandled crash are indistinguishable by exit code

**File:** `tools/contract_graph/impact.py:180-182`
**Issue:** `main()` calls `report(argv[0])` with no exception handling. Any exception raised by
`load_project()`, `effective_relationships()` (which raises `ValueError` on the three D-05
malformed-config failure modes), `compile_graph()`, etc. propagates unhandled out of `main()`,
and an uncaught exception at the top of a `python -m` invocation exits with status **1** — the
exact same code `main()` returns for a clean, resolved-`False` refusal. Reproduced live: a
`report()` that raises `ValueError("boom")` still produces `exit 1`, identical to
`definitely-not-a-real-node`'s clean refusal (`refusal exit=1`). Because `harness/commands/
impact.md` documents this as a scripted evidence step consumed by the `contract-change` route
("non-zero exit... names what was searched"), a caller parsing exit codes cannot tell "your
contract doesn't resolve" from "the config is malformed / the tool crashed" — the latter needs a
completely different remediation (fix `harness/project.toml`, not re-check the contract path).
**Fix:** Wrap the `report()` call in `main()` in a targeted `try/except` for the exceptions its
dependencies document (at minimum `ValueError`), print a diagnosable message to stderr, and return
a THIRD, distinct exit code (e.g. `3`) so refusal, missing-argument, and crash are three different
signals.

## Warnings

### WR-01: The extended "no second traversal engine" structural check is evadable by trivial, unremarkable rewrites

**File:** `tools/contract_graph/tests/test_impact.py:115-148`
**Issue:** `_traversal_violations` is the guardrail meant to keep a future edit from re-implementing
traversal inside `impact.py` instead of calling `direct`/`reverse`/`transitive`. It is mutation-
tested against exactly two synthetic stubs (a `while`-frontier and a `for node in graph['adjacency']`
loop) and passes against both — but the check's shapes are narrow enough that three unremarkable
rewrites of the SAME violation evade it entirely, reproduced live against the actual
`_traversal_violations` function (not a hypothetical):
1. **Variable-alias evasion** — `adj = graph["adjacency"]; for node in adj: ...` — the "for-over-
   adjacency" rule only string-matches `"adjacency" in ast.unparse(node.iter)`; aliasing the dict to
   any other name (which is completely ordinary Python style) makes the substring vanish.
   `_traversal_violations(...)` → `[]`.
2. **Comprehension evasion** — `{n for n in graph["adjacency"]}` is an `ast.SetComp`, not an
   `ast.For`, so the for-loop rule never even inspects it. `_traversal_violations(...)` → `[]`.
3. **Mutual-recursion evasion** — two module-level helpers that call each other
   (`_walk_a` calls `_walk_b`, `_walk_b` calls `_walk_a`) implement a hand-rolled recursive walk
   with neither function calling itself by its own name, so the self-recursion rule (`node.func.id
   == fn.name`) never fires. `_traversal_violations(...)` → `[]`.

All three reproductions are included verbatim in this review's working notes and were run against
the actual `test_impact.py` helper, not a paraphrase. The test's own docstring (lines 17-20) frames
this as "extended... to ALSO catch a for-over-adjacency re-implementation... not just a while-shaped
one" and claims mutation-testing proves "the check itself is not a check that cannot fail" — but
mutation-testing against exactly the two shapes the check was designed to catch does not establish
that other equally-ordinary shapes are covered, and three are demonstrably not. This is the repo's
documented signature defect (a guardrail whose promise exceeds what it actually enforces).
**Fix:** Either narrow the claim (docstring should say "catches only literal `while`/`for-over-
adjacency-by-name`/self-recursion-by-name shapes, not a general re-implementation detector") or
strengthen the check (e.g., resolve simple aliases via a lightweight def-use pass before the
substring test, treat all `ast.comprehension` nodes the same as `ast.For`, and detect any
call-graph cycle among module-level functions rather than only literal self-calls).

### WR-02: `"searched"` in the refusal payload is a bare count, not "what was searched" — and cannot distinguish a typo from a tracked-but-unwired contract

**File:** `tools/contract_graph/impact.py:106-111`
**Issue:** The refusal shape returns `"searched": len(relationships)` — a single integer, constant
for a given `cfg` regardless of which `contract_path` was passed. Both `harness/commands/impact.md`
("a clean refusal... that names what was searched") and `impact.py`'s own module docstring frame
this as informative, but it is the same number whether the input was a wildly bogus string, an
honest typo one character off from a real contract, or a contract that IS tracked under
`contracts/**/*.schema.json` but simply has no relationship record naming it yet (a legitimate,
common pre-wiring state). All three refuse identically with the same `searched` count and no list
of near-misses or candidate ids — the field's name overpromises what it delivers.
**Fix:** Either rename the field to something honest (`"relationships_checked"`) or make it
actually informative — e.g. include the `candidate_id` derived and/or the list of tracked schema
ids near-miss-matched, so the `contract-change` route (and the human reading its evidence block)
can tell "this contract does not exist" from "this contract exists but isn't wired into the graph
yet," which call for very different next steps.

### WR-03: `owning_package()`'s "root always encloses" fallback is now reachable with fully unvalidated CLI input

**File:** `tools/contract_graph/impact.py:134-138`
**Issue:** `contract_owner = owning_package(dir_pkgs, contract_path)` passes the raw, unsanitized
`contract_path` argument (which may be an absolute path, a `../` traversal, or any other string —
see CR-01) straight into `owning_package()`, whose documented behavior is that the `dir == "."`
root package encloses EVERY path, including `/etc/passwd` or `../../whatever`
(`PurePosixPath(...).parts` sliced against an empty tuple always matches). This is `ownership.py`'s
own documented, ratified behavior from Phase 48 — not a new defect in that module — but `impact.py`
is a new, more exposed caller: it is invoked directly from a shell macro
(`!`uv run python -m tools.contract_graph.impact "$ARGUMENTS"`) with a free-text CLI argument, so a
bogus or malicious-looking path now silently attributes ownership to the root package rather than
surfacing "this isn't a real contract path" — compounding CR-01/CR-02's refusal-quality gaps with a
misleading non-`null` `contract_owner` in the resolved-but-wrong case.
**Fix:** Validate that `contract_path` is actually a path under a tracked `contracts/` directory
(or a bare node id) before treating a "resolved" report's `contract_owner` as meaningful; consider
surfacing when `contract_owner` was attributed purely by the root-package fallback vs. a genuine
nested-package match.

### WR-04: The `"dir"`-key adapter comment claims exact replication but drops the malformed-record diagnostic `conventions_for()` pairs it with

**File:** `tools/contract_graph/impact.py:128-130`
**Issue:** The comment says: `# ADAPTER: reuse the exact "dir"-key filter conventions_for() applies
(loader.py:330-338)`. But `conventions_for()` (`tools/harness_config/loader.py:330-338`) does not
apply the filter alone — it pairs `"dir" in p` with an explicit stderr print for the case `"dir"
not in p and "manifest" in p`, added deliberately per that file's own comment ("WR-02 (48-REVIEW.md):
... The latter must not be silently dropped with no trace — surface it on stderr so a data bug
stays visible"). `impact.py` copies only the filter line (`dir_pkgs = [p for p in pkgs if "dir" in
p]`) and drops the diagnostic entirely, so the exact malformed-record case Phase 48's review called
out as needing visibility is now silently swallowed again in this new call site — the "exact"
claim in the comment is false as written.
**Fix:** Either replicate the stderr diagnostic here too, or update the comment to state precisely
which part of `conventions_for()`'s adapter was reused and which (the diagnostic) was deliberately
dropped and why.

## Info

### IN-01: `main()` silently ignores extra CLI arguments

**File:** `tools/contract_graph/impact.py:180`
**Issue:** `report(argv[0])` only ever reads the first argument; `python -m
tools.contract_graph.impact a b c` runs identically to passing just `a`, with `b`/`c` silently
discarded — no usage error, no warning. For a scripted evidence step this can mask a caller bug
(e.g. an unintended shell-splitting of an unquoted path with a space in it).
**Fix:** Reject (usage error, exit 2) when `len(argv) > 1`, or explicitly document that only the
first token is consumed.

### IN-02: `$ARGUMENTS` is interpolated into a double-quoted shell command with no escaping guarantees

**File:** `harness/commands/impact.md:23`
**Issue:** `!`uv run python -m tools.contract_graph.impact "$ARGUMENTS"`` places raw, user-supplied
text inside double quotes. This is consistent with several other existing harness commands (e.g.
`agree.md`, `adopt.md`) — not a regression introduced by this phase — but a `contract_path`
containing a literal `"` or `` ` `` or `$(...)` sequence could still break out of the intended
quoting depending on how the underlying macro-expansion substitutes `$ARGUMENTS` before shell
execution. Noted for completeness since this phase adds a new instance of the pattern; not scored
as a phase-49-introduced defect.
**Fix:** If the harness ever hardens command-argument handling repo-wide, `/impact` should be
included in that pass; no action required specific to this phase.

---

_Reviewed: 2026-07-30T03:53:43Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
