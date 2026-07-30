---
phase: 49-contract-impact
verified: 2026-07-30T00:00:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
---

# Phase 49: Contract Impact Verification Report

**Phase Goal:** Turn the `contract-change` route's *Repository evidence* step from a raw inline
one-liner into one named command, `/impact <contract>`, answering "what does changing this
contract reach?" over both the compiled contract graph and the Phase-47 package facts.

**Verified:** 2026-07-30
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1 — `/impact` reports affected contracts (direct/reverse/transitive) and affected packages | VERIFIED | `tools/contract_graph/impact.py:76-162` `report()` composes `direct/reverse/transitive` and `affected_packages`; `tools/contract_graph/tests/test_impact.py::test_report_composes_direct_reverse_transitive_not_rederived` asserts `report()["direct"] == direct(graph, "a")` etc. (byte equality, not just presence) and `test_affected_packages_include_a_matching_facts_entry` proves package composition against a synthetic multi-node fixture. Live-tree run is degenerate (see note below) — fixtures are the load-bearing evidence, exactly as CONTEXT.md mandates ("Fixtures are mandatory"). |
| 2 | SC2 — no second traversal engine | VERIFIED | Read `impact.py` in full: it imports and calls `direct()`, `reverse()`, `transitive()` by name (lines 39, 113-115) and contains no `while`, no `for … in … adjacency`, no local recursive helper. `test_impact_module_calls_the_three_query_functions_and_defines_no_second_engine` asserts this via AST walk (`ast.While`, `ast.For` over an "adjacency"-mentioning iterable, self-calling `FunctionDef`). Mutation-tested: `test_check_traps_a_while_frontier_stub` and `test_check_traps_a_for_over_adjacency_stub` prove the checker itself trips on synthetic violation stubs — not a check-that-cannot-fail. All three shapes (while, for-over-adjacency, local recursion) are covered by the AST walk; ran the checker against a hand-mutated string locally to confirm it is live, not decorative. |
| 3 | SC3 — nothing injected; no CI/hook references `/impact` | VERIFIED | `git diff efe6be8..HEAD -- tools/memory_regen/inject.py .github/workflows/ci.yml` is empty (confirmed directly, exit 0, no output). `grep -rn impact .github/workflows/` and `grep -rn "/impact" tools/memory_regen/` both empty. `uv run pytest tools/memory_regen/tests/test_inject_determinism.py` — 7 passed, 1 snapshot passed, file unmodified since base. |
| 4 | SC4 — route names `/impact`, one-liner gone, 5-subsection structure intact, emit round-trip clean | VERIFIED | `harness/agents/orchestrator.md:274-293` — Repository evidence block invokes `` /impact <path/to/contract.schema.json> `` , the old `uv run python -c "..."` one-liner for this route is gone (the three *other* routes' pre-existing one-liners are untouched — out of this phase's scope, confirmed by reading CONTEXT.md's edit-site note). New structural test `tools/harness_lint/tests/test_orchestrator_topology.py::test_every_route_carries_all_five_subsections_in_order` parses all four `## Route:` sections and asserts all five subsection headers appear in order; mutation-verified locally (stripped `**Stop condition**` from a route body → check correctly flags it as missing). `uv run python -m tools.harness_emit` followed by `git status --porcelain` produced zero diff — round-trip is byte-clean. |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tools/contract_graph/impact.py` | `report()`/`main()`, composition only, min 60 lines | VERIFIED | 187 lines; `report()` L76-162, `main()` L165-186; no independent traversal (AST-checked). |
| `tools/contract_graph/tests/test_impact.py` | behavior + structural tests, min 80 lines | VERIFIED | 251 lines, 5 behavior groups, all fixture-based (domain-neutral a/b/c/d/widget), 2 mutation-test stubs. |
| `harness/commands/impact.md` | thin macro | VERIFIED | 24 lines: frontmatter + one prose paragraph + single `!` shell invocation. No embedded logic. |
| `harness/agents/orchestrator.md` (edit) | Repository evidence block names `/impact` | VERIFIED | L274-293, confirmed above. |
| `.opencode/command/impact.md`, `.claude/commands/impact.md` | emitted, not hand-edited | VERIFIED | Present; `harness_emit` re-run produces zero diff against committed trees. |
| `tools/harness_lint/tests/test_commands.py` (edit) | count 18→19, name set includes `impact` | VERIFIED | L101 `assert len(_command_files()) == 19`; `EXPECTED_COMMAND_NAMES` includes `impact` (test passes; `harness/commands/` has 19 files incl. `impact.md`). |
| `tools/harness_emit/tests/test_coexist.py` (edit) | 18→19 bump, narrative updated | VERIFIED | L59, L76-77 assert 19 in both emitted trees. |
| `tools/harness_lint/tests/test_orchestrator_topology.py` (new) | five-subsection structural gate | VERIFIED | New file, mutation-verified live above. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `tools/contract_graph/impact.py` | `tools/contract_graph/query.py` (`direct`/`reverse`/`transitive`) | import + direct call | WIRED | L39 import, L113-115 calls; equality-tested against direct calls in `test_impact.py`. |
| `tools/contract_graph/impact.py` | `tools/contract_graph/ownership.py` (`owning_package`) | import + call | WIRED | L38 import, L136 call inside try/except; `ownership.py` itself byte-unchanged since base (`git diff efe6be8..HEAD -- tools/contract_graph/ownership.py` empty). |
| `harness/commands/impact.md` | `tools/contract_graph/impact.py` | shell invocation | WIRED | `uv run python -m tools.contract_graph.impact "$ARGUMENTS"` (L23). |
| `harness/agents/orchestrator.md` (`contract-change` route) | `harness/commands/impact.md` | named command reference | WIRED | Route step 2 + Repository evidence block name `/impact` explicitly. |
| `tools.harness_emit` | `.opencode/`, `.claude/` | emit projection | WIRED | Re-run produces zero diff; 73 artifacts emitted including `impact.md` to both trees. |

### Investigated: orchestrator's live-tree "identical output" observation

Reproduced directly (not trusting the pasted transcript):

```
$ uv run python -m tools.contract_graph.impact contracts/sample/greeting.schema.json; echo $?
{"contract_id": "greeting", "contract_path": "...", "resolved": false, "searched": 0}
1
$ uv run python -m tools.contract_graph.impact contracts/nope/does-not-exist.schema.json; echo $?
{"contract_id": "does-not-exist", "contract_path": "...", "resolved": false, "searched": 0}
1
```

Two corrections to the observation as given:
- **Exit code is 1 on both, not 0.** `main()` (`impact.py:182`) returns `0 if result["resolved"] else 1`; both invocations return `"resolved": false`, so both exit non-zero. The claim that a refusal exits 0 is not reproducible on this checkout — verified twice, redirected to files, `$?` checked immediately after each call.
- **`searched: 0` is a global fact, not a per-contract one.** `_resolve_node` scans `effective_relationships()`, and the live `[contract_graph]` table has zero rows (Phase 44's CER-08 removed the core `[pipeline]` edges — this predates and is out of scope for Phase 49, and is explicitly called out in `49-CONTEXT.md`'s "Resolved after research": *"The live graph is EMPTY on this checkout … All 6 tracked contracts therefore resolve to 'no declared edges' today. Fixtures are mandatory."*). Because `len(relationships) == 0` regardless of input, a real-but-unwired contract and a typo'd path are indeed indistinguishable **today**, on **this** checkout.

**Judgment: acceptable-as-designed, not a gap — for the specific danger CONTEXT.md names.** The
locked decision's actual concern is *"collapsing 'could not resolve your contract' into 'resolved,
nothing affected'"* — i.e., refused vs. resolved-but-isolated must never share a shape, because the
isolated shape reads as a safe "go ahead." That distinction is real and tested: `test_impact.py::
test_refused_isolated_and_affected_reports_are_key_set_distinguishable` proves refused has a
different key set than isolated/affected, using a populated fixture (`iso` node, zero edges) next
to a genuinely typo'd path — and both this test and a live rerun confirm neither case ever returns
`"resolved": true` when it shouldn't. Both the real contract and the nonexistent one correctly
refuse (never a false "nothing affected" success), and `searched: 0` truthfully reports the current,
degenerate state of the graph rather than fabricating a per-contract signal it doesn't have.

What CONTEXT.md does **not** require — and what remains a genuine, narrower limitation worth
flagging — is filesystem-existence checking: `/impact` never stats the path, so once the graph is
populated, a real-but-unwired contract and a garbage path would *still* both search the same N
relationship records and both refuse identically (this was verified by constructing the `iso`/
`does-not-exist` pair against the same populated fixture in the test above — both correctly refuse,
but nothing in the refusal shape says *which* of the two problems occurred). This is a legitimate
UX sharpening for a future phase (a `Path.exists()` check ahead of the relationship scan would
resolve it cheaply) but it was never a locked must-have of Phase 49, is not required by MONO-08/
MONO-09, and does not violate the specific "no empty success" guarantee CONTEXT.md locks in. Not
filed as a gap; noted here for visibility.

### Anti-Patterns Found

None. Scanned all phase-touched files (`impact.py`, `test_impact.py`, `impact.md`,
`orchestrator.md`, `test_orchestrator_topology.py`, `test_commands.py`, `test_coexist.py`) for
`TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER`, empty-return stubs, and hardcoded-empty props —
zero matches.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| MONO-08 | 49-01, 49-02 | `/impact <contract>` reports affected contracts and packages | SATISFIED | `report()` composition verified above; command wired into orchestrator route. |
| MONO-09 | 49-02 | `/impact` runs on demand only — no injection, no gate, no CI job | SATISFIED | Injector diff empty, no CI/hook reference, no gate added (grep confirms). |

No orphaned requirements found for Phase 49 in `.planning/REQUIREMENTS.md`.

### Surface / Hardcoded-Count Sweep

`grep -rn` for stray `18`-command literals across `tools/harness_lint/tests/`,
`tools/harness_emit/tests/`, `tools/memory_regen/tests/` found only narrative/historical mentions
(the count's own change-history prose in `test_coexist.py`, unrelated `T-03-18` skill-anti-sprawl
tags, unrelated dates) — no remaining executable assertion pinned at `18`. `test_command_count_is_
stable` and `test_command_names_are_stable` both assert `19`.

### Full Suite

`uv run pytest -q` — 951 passed, 8 snapshots passed, 0 failures.
`uv run pytest -q -k core_no_example_dep` (GEN-04) — 18 passed.
`uv run python -m tools.harness_emit` then `git status --porcelain` — empty (byte-clean round-trip).

### Human Verification Required

None. All must-haves are machine-verifiable and were verified directly against the live tree, not
inferred from SUMMARY.md.

### Gaps Summary

None. All four roadmap success criteria (SC1-SC4) and both requirements (MONO-08, MONO-09) are
verified against the live codebase, not SUMMARY claims. The orchestrator's flagged observation
(real vs. nonexistent contract producing identical refusal output) was investigated directly:
reproduced, the exit-code-0 portion of the claim does not hold (both exit 1), and the shape-
collapse danger CONTEXT.md specifically locks against (refused silently reading as "nothing
affected") does not occur — refused and isolated/affected have provably different key sets, tested
under mutation. The remaining ambiguity (typo vs. tracked-but-unwired both refusing identically) is
a real but narrower limitation, outside this phase's locked scope, and is noted above rather than
filed as a gap.

---

_Verified: 2026-07-30_
_Verifier: Claude (gsd-verifier)_
