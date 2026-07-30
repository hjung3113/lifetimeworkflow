---
phase: 49-contract-impact
fixed_at: 2026-07-30T04:08:53Z
review_path: .planning/phases/49-contract-impact/49-REVIEW.md
iteration: 1
findings_in_scope: 9
fixed: 8
skipped: 1
status: partial
---

# Phase 49: Code Review Fix Report

**Fixed at:** 2026-07-30T04:08:53Z
**Source review:** .planning/phases/49-contract-impact/49-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 9 (3 critical, 4 warning, 2 info)
- Fixed: 8
- Skipped: 1 (IN-02, explicitly deferred by the review itself and by this task's fix_scope)

## Fixed Issues

### CR-01: `_resolve_node` collides unrelated paths onto the same contract id

**Files modified:** `tools/contract_graph/impact.py`, `tools/contract_graph/tests/test_impact.py`
**Commit:** `772e1cb`
**Applied fix:** Added `_normalize_contract_path()` — rejects any absolute path or path containing
a `..` segment BEFORE a candidate contract id is ever derived from the filename. A traversal or
wrong-directory payload that merely ends in a real contract's filename can no longer resolve at all
(returns `resolved: False`, `contract_id: None`).
**Regression tests:** `test_traversal_path_is_refused_not_collided_onto_the_real_contract`,
`test_absolute_traversal_path_is_refused`, `test_multi_dot_contract_filename_resolves_by_full_suffix_strip`,
`test_contract_path_with_no_extension_derives_the_whole_filename_as_candidate_id`,
`test_empty_string_contract_path_is_refused`, `test_trailing_slash_contract_path_is_refused`.
**Fails-before/passes-after evidence:** ran the traversal/absolute-path tests against the pre-fix
`impact.py` (via `git show HEAD:...` before this commit) — both failed (`bogus["resolved"]` was
`True`, byte-identical to the real report). After the fix, all 6 tests pass; full
`test_impact.py` suite: 18/18 passed.

### CR-02: Bare-node-id resolution silently fails for any legitimately isolated authority

**Files modified:** `tools/contract_graph/impact.py`, `tools/contract_graph/tests/test_impact.py`
**Commit:** `772e1cb` (same commit as CR-01 — `_resolve_node`'s signature change is shared by both
fixes and could not be meaningfully split)
**Applied fix:** The bare-node-id fallback now checks membership in `components(cfg)` /
`members(cfg)` id sets, never `compile_graph()`'s `adjacency` (which omits every zero-dependent
authority by construction).
**Regression test:** `test_isolated_node_resolves_identically_via_bare_id_and_via_contract_path`.
**Fails-before/passes-after evidence:** against pre-fix `impact.py`, the isolated node ("iso")
resolved via its contract path but was refused via its bare id (`assert False is True` on
`via_bare_id["resolved"]`). After the fix, both addressing styles resolve identically.

### CR-03: Refusal (exit 1) and an unhandled crash are indistinguishable by exit code

**Files modified:** `tools/contract_graph/impact.py`, `harness/commands/impact.md`,
`.claude/commands/impact.md`, `.opencode/command/impact.md`,
`tools/contract_graph/tests/test_impact.py`,
`tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr`
**Commits:** `0126119` (fix + docs + re-emit), `8d4ce40` (snapshot follow-up)
**Applied fix:** `main()` now wraps `report()` in a `try/except Exception`, prints a diagnosable
message to stderr, and returns exit code `3` (distinct from refusal's `1` and usage-error's `2`).
Documented all four exit codes in `harness/commands/impact.md` and re-emitted both runtime trees
(`uv run python -m tools.harness_emit`); a second re-emit was confirmed a no-op. The emit-determinism
snapshot test required a `--snapshot-update` follow-up commit to pin the new doc prose.
**Regression test:** `test_main_exits_1_on_clean_refusal_and_3_on_internal_error_not_the_same_code`.
**Fails-before/passes-after evidence:** against pre-fix `impact.py`, a monkeypatched `report()` that
raises `ValueError` propagated uncaught out of `main()` (pytest reported the raw exception, not a
returned exit code). After the fix, the same scenario returns `3`, distinct from refusal's `1`.

### WR-01: The "no second traversal engine" structural check is evadable by trivial rewrites

**Files modified:** `tools/contract_graph/tests/test_impact.py`
**Commit:** `f85b0df`
**Applied fix:** Strengthened `_traversal_violations` to (a) resolve simple local aliases of an
adjacency-mentioning expression before the for-loop substring test, (b) treat every
`ast.comprehension` node the same as `ast.For`, and (c) detect any call-graph cycle among
module-level functions (mutual recursion), not just literal self-calls. Also added a **behavioural**
equivalence proof independent of AST shape entirely — asserts `report()`'s direct/reverse/transitive
payloads exactly match calling `query.py`'s functions directly, for every node in a multi-node
fixture.
**Regression tests:** `test_check_traps_a_variable_alias_evasion_stub`,
`test_check_traps_a_set_comprehension_evasion_stub`, `test_check_traps_a_mutual_recursion_evasion_stub`,
`test_report_affected_sets_exactly_match_query_functions_for_every_traversal_direction`.
**Fails-before/passes-after evidence:** re-ran the three evasion stubs against the original
(pre-strengthening) `_traversal_violations` function body — all three returned `[]` (no violation
detected), matching the review's exact reproductions. After strengthening, all three trip a
violation.

### WR-02: `"searched"` in the refusal payload is a bare count, not informative

**Files modified:** `tools/contract_graph/impact.py`, `tools/contract_graph/tests/test_impact.py`
**Commit:** `455271d`
**Applied fix:** `"searched"` is now the sorted list of contract ids actually checked
(`sorted({rel["contract"] for rel in relationships})`) instead of `len(relationships)`.
**Regression test:** `test_refusal_searched_field_names_the_contract_ids_actually_checked`.
**Fails-before/passes-after evidence:** against pre-fix `impact.py`, `result["searched"]` was `1`
(an int); the test asserting it equals `["widget"]` failed with `assert 1 == ['widget']`. After the
fix it passes.

### WR-03: `owning_package()`'s root-fallback is reachable with unvalidated CLI input

**Files modified:** `tools/contract_graph/impact.py`, `tools/contract_graph/tests/test_impact.py`
**Commit:** `772e1cb` (folded into the CR-01 commit — `safe_path` is CR-01's `_resolve_node` return
value plumbed straight through to gate this call, so splitting it into its own commit would have
meant temporarily re-introducing the exact vulnerability CR-01 closes)
**Applied fix:** `owning_package()` is now only ever called with `safe_path` (the CR-01-validated,
normalized path), and only when both `contract_id is not None and safe_path is not None`. Never the
raw, unvalidated `contract_path`.
**Regression test:** `test_contract_owner_is_null_for_a_traversal_path_never_root_fallback_attributed`.
**Fails-before/passes-after evidence:** against pre-fix `impact.py`, a traversal path with a
root-fallback-matching `facts` package resolved `True` with a non-null `contract_owner` (leaked
attribution); the test asserting `resolved is False` failed. After the fix, the traversal path is
refused before `owning_package()` is ever reached, so `contract_owner` never appears.

### WR-04: The `"dir"`-key adapter comment claims exact reuse but drops the diagnostic

**Files modified:** `tools/contract_graph/impact.py`, `tools/contract_graph/tests/test_impact.py`
**Commit:** `f1d462b`
**Applied fix:** Replicated `conventions_for()`'s stderr diagnostic for the malformed-record case
(a package record carrying `"manifest"` but no `"dir"`) at this call site too, so the comment's
"exact reuse" claim is true as written.
**Regression test:** `test_malformed_package_record_prints_the_same_stderr_diagnostic_as_conventions_for`.
**Fails-before/passes-after evidence:** against pre-fix `impact.py`, `capsys.readouterr().err` was
empty for the malformed-record fixture; the test asserting `"manifest" in captured.err` failed.
After the fix it passes.

### IN-01: `main()` silently ignores extra CLI arguments (fixed — cheap)

**Files modified:** `tools/contract_graph/impact.py`, `tools/contract_graph/tests/test_impact.py`
**Commit:** `2ceae0d`
**Applied fix:** `main()` now rejects `len(argv) != 1` with the same usage-error exit code (`2`) a
missing argument already returns, instead of silently reading only `argv[0]`.
**Regression test:** `test_main_rejects_extra_cli_arguments_with_a_usage_error`.
**Fails-before/passes-after evidence:** against pre-fix `impact.py`,
`main(["a", "b", "c"])` returned `1` (ran identically to `main(["a"])`, discarding `b`/`c`); the
test asserting it returns `2` failed. After the fix it passes.

## Skipped Issues

### IN-02: `$ARGUMENTS` interpolated into a double-quoted shell command with no escaping guarantees

**File:** `harness/commands/impact.md:23`
**Reason:** The review itself explicitly scopes this as "not a regression introduced by this
phase... not scored as a phase-49-introduced defect" and its own Fix note says "no action required
specific to this phase." The task's `<fix_scope>` names this exact finding as out of scope ("The
`$ARGUMENTS` quoting note is pre-existing and out of scope unless trivially safe to improve") and
the pattern is shared identically by several other existing harness commands (`agree.md`,
`adopt.md`) — a `/impact`-only fix would diverge from the repo-wide pattern rather than harden it.
Left for a future repo-wide command-argument-handling hardening pass, as the review itself
recommends.

## Final CLI Demonstration

Run against `contracts/sample/greeting.schema.json` (the repo's one real contract), a typo'd path,
and a `../` traversal path, on the live checkout (whose `contract_graph` table is empty per
49-CONTEXT.md's documented "live graph is EMPTY on this checkout" fact — every real contract
therefore refuses today, which is the correct/expected clean-refusal behavior, not a bug):

```
$ uv run python -m tools.contract_graph.impact "contracts/sample/greeting.schema.json"
{
  "contract_id": "greeting",
  "contract_path": "contracts/sample/greeting.schema.json",
  "resolved": false,
  "searched": []
}
exit=1

$ uv run python -m tools.contract_graph.impact "contracts/sample/gretting.schema.json"
{
  "contract_id": "gretting",
  "contract_path": "contracts/sample/gretting.schema.json",
  "resolved": false,
  "searched": []
}
exit=1

$ uv run python -m tools.contract_graph.impact "contracts/WRONG-DIR/../../contracts/sample/greeting.schema.json"
{
  "contract_id": null,
  "contract_path": "contracts/WRONG-DIR/../../contracts/sample/greeting.schema.json",
  "resolved": false,
  "searched": []
}
exit=1
```

Note the traversal case's `contract_id: null` versus the typo case's `contract_id: "gretting"` —
CR-01's fix refuses the traversal path so early that no candidate id is ever derived from it,
visibly distinguishing "your path escapes containment" from "your path just doesn't match anything."

Supplementary demonstration against a synthetic wired relationship (to show the anti-collision
effect concretely, since the live graph has no relationships to collide against):

```python
cfg = {
    "components": [{"id": "a", "produces": ["widget"], "consumes": [], "language": "py"}],
    "languages": [{"id": "py", "persona": "harness/agents/py-engineer.md"}],
    "contract_graph": {"relationships": [
        {"id": "r1", "contract": "widget", "authority": "a", "dependents": []}
    ]},
}
report("contracts/sample/widget.schema.json", cfg=cfg)
# -> resolved: True, node: "a"
report("contracts/WRONG-DIR/../../etc/widget.schema.json", cfg=cfg)
# -> resolved: False, contract_id: None   (pre-fix: resolved True, node "a" — byte-identical collision)
```

## Verification Evidence

- `uv run pytest -q` (full suite, both `tree-sitter`/`networkx` deps synced via `uv sync
  --all-packages`): **967 passed**, 0 failed.
- `uv run python -m tools.harness_emit` re-run twice: second run produced **zero diff** — the
  projection is a stable fixpoint.
- `git diff --stat HEAD -- .github/workflows/ci.yml tools/memory_regen/inject.py`: **empty** (zero
  diff on both protected files).
- GEN-04 scan (`examples/` literal): no hits in any modified file
  (`tools/contract_graph/impact.py`, `tools/contract_graph/tests/test_impact.py`,
  `harness/commands/impact.md`).
- `tools/harness_lint/tests/test_core_no_example_dep.py` + `test_commands.py`: 97/97 passed —
  command surface stays at 19, no core/example-dependency introduced.
- `tools/harness_emit/tests/test_emit_determinism.ambr` snapshot updated in a dedicated follow-up
  commit (`8d4ce40`) to pin the new `/impact` exit-code documentation prose emitted into both
  `.opencode/command/impact.md` and `.claude/commands/impact.md`.

## Commits (in order)

1. `772e1cb` — fix(49): CR-01/CR-02/WR-03 harden impact contract-path resolution
2. `0126119` — fix(49): CR-03 give impact refusal and internal-error distinct exit codes
3. `f85b0df` — fix(49): WR-01 strengthen no-second-engine check + add behavioural proof
4. `455271d` — fix(49): WR-02 make the refusal "searched" field actually informative
5. `f1d462b` — fix(49): WR-04 replicate conventions_for()'s malformed-package diagnostic
6. `2ceae0d` — fix(49): IN-01 reject extra CLI arguments as a usage error
7. `8d4ce40` — docs(49): update emit-determinism snapshot for /impact exit-code docs

---

_Fixed: 2026-07-30T04:08:53Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
