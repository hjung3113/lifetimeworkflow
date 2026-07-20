# Phase 28: Review Fixes

**Source review:** `28-REVIEW.md` (deep, 20 files, 3 critical / 4 warning / 3 info)
**Scope:** all 3 Criticals, all 4 Warnings, IN-01 and IN-02 fixed; IN-03 recorded as a residual.
**Method:** every fix got its adversarial row authored or repaired FIRST and shown RED against the
pre-fix code FOR THE STATED REASON. The verbatim failure is recorded per finding below. Where the
reviewer supplied an executed bypass (CR-01, CR-03, WR-01), the new row reproduces that exact output.

Nothing about the phase's designed pre-ratification state was altered: `docs/.docs-review-ledger.toml`
was NOT created, `python -m tools.docs_guard` still reports `broken-binding` and FAILED, and
ADR-0010 remains `Status: proposed`.

## ADR-0010 handling

Four findings were defects in the ADR's own text as much as in the code — the record described a
control that did not exist (CR-02), specified the demotion defect (CR-01), documented the id-only
history test (CR-03) and the one-sided ratchet property (WR-01). ADR-0010 is still `Status:
proposed` and unratified, so its text was **corrected in place** rather than superseded; that is
legitimate precisely because no human has ratified it yet. It was **NOT** flipped to `accepted`, and
no date or deciders were filled in.

`docs/adr/` and `contracts/` writes landed through the pre-set `HARNESS_DEV_BYPASS` dev path
(ADR-0007). `GOLDEN_APPROVE_HUMAN` was neither set nor forged. CODEOWNERS remains the merge gate.

## Review findings dispositioned

| ID | Disposition | Commit |
|----|-------------|--------|
| CR-01 | fixed | `86ecad5` |
| CR-02 | fixed — layer 1 made real | `ef793a8` |
| CR-03 | fixed | `2b504a6` |
| WR-01 | fixed | `d49bdc9` |
| WR-02 | fixed (both ends) | `d6a7f63` |
| WR-03 | fixed | `59870d9` |
| WR-04 | fixed | `d17e764` |
| IN-01 | fixed | `b329fce` |
| IN-02 | fixed | `1810085` |
| IN-03 | accepted as a residual — see below | — |

---

### CR-01 — drift suppression demoted blocking coherence findings

**Fixed.** Two independent halves, deliberately belt-and-braces:

- `SUPPRESSIBLE_REASONS = frozenset({REASON_STALE})` restricts the demotion pass to the one finding
  genuinely downstream of contract drift. Every reason in `BLOCKING_REASONS` is about WHO RATIFIED
  WHAT, which a drifted source has no bearing on.
- the `SUPPRESSED` branch gained `and not blocking_by_id.get(binding.id)`, so a binding carrying a
  blocking finding cannot reach that state at all and no reordering of the classifier re-opens it.

**RED evidence** (`test_self_blessed_binding_is_not_rescued_by_a_drifted_source`, pre-fix):

```
AssertionError: drift demoted a ratification-authority finding — the self-green escape is open
assert ['note'] == ['fail']
  At index 0 diff: 'note' != 'fail'
```

That is the reviewer's executed A2 probe (`findings: [('note', 'first_seen-unratified')]`). The
fixture is the reviewer's: empty committed ledger, brand-new binding plus a matching
`reviewed-no-change` row carrying its exact live digests, source drifted. `test_drifted_source_suppressed`
is the non-degradation control and stayed green throughout.

ADR-0010 clause 9 rewritten: it had specified the defect ("a suppressed binding's coherence findings
are demoted to note level").

---

### CR-02 — `path_deny_globs` had no enforcer; ADR-0010's layer 1 did not exist

**Fixed. Route taken: made layer 1 REAL rather than correcting the ADR downward.**

Why this route. Weakening the ADR was the fallback the brief allowed, but it was not necessary: the
layer is buildable in exactly the shape the other two deny domains already use, the emitter already
has a wiring seam for PreToolUse hooks in both runtimes, and the boundary the ADR describes is the
one the phase actually needs — CR-01 showed that an unguarded ledger write is what can be laundered
into permanent green. Removing the claim would have left that write unobstructed and merely stopped
saying so.

What landed:

- **`tools/hooks/ledger_guard.py`** — a new PreToolUse(`Write`|`Edit`) deny gate. It owns
  `REVIEW_LEDGER_GLOBS` as a THIRD, disjoint deny domain per ADR-0010 clause 3b — **not** folded
  into `CONSTITUTION_GLOBS` — and it honours **no** opt-out: neither `GOLDEN_APPROVE_HUMAN` (which
  authorizes constitution writes) nor the ADR-0007 `HARNESS_DEV_BYPASS`. No token legitimizes an
  agent-authored review disposition, so there is nothing for a session-scoped opt-out to express.
- **`tools/adoption_apply/apply.py`** now IMPORTS that constant instead of declaring a second copy,
  so the apply path and the tool path cannot disagree about what the ledger is.
- **Wiring**: `tools/harness_emit/merge.py` `HARNESS_SIGNATURES` + a `Write|Edit` PreToolUse group;
  `harness/plugins/ledger-guard.ts` is the authored-only opencode twin (same single enforcement
  contract, different envelope); both runtime trees re-emitted by `tools.harness_emit`.
- **Tests**: the vacuous matrix assertion is replaced by five that can fail —
  `decide()` driven with an absolute path asserts a deny; neither opt-out opens the gate; the
  registry and the four prefix-adjacent names stay writable; the three deny domains are pairwise
  disjoint; and the WIRING is asserted through `merge_settings`, the function the emitter runs. The
  matrix row is kept only as a consistency check against the hook, never as the proof.

**RED evidence.** First, that the control was absent at all:

```
$ git grep -n docs-review-ledger HEAD -- tools/hooks/ .opencode/ .claude/ harness/
HEAD:harness/permission-matrix.json:2:  "_note": ...
HEAD:harness/permission-matrix.json:33:    "docs/.docs-review-ledger.toml"
```

Only the data line and its own note — no enforcer anywhere, which is why the old assertion could not
fail. Second, that the new wiring test is live (wiring reverted, module kept):

```
AssertionError: ledger_guard is not wired into the emitted PreToolUse set — ADR-0010's layer 1 is inert
assert False
```

ADR-0010's layer table, clause 3b and Links now name the actual enforcer and record explicitly that
a `path_deny_globs` row is data, not a layer.

---

### CR-03 — `first_seen-unratified` keyed on the binding id alone

**Fixed.** The history test now keys on `(id, the binding's committed (sources, target) pair)`.

- `registry.identity_digest(sources, target)` hashes the SORTED selectors and the target with
  per-field labels — so `sources=["a"], target="b"` cannot collide with the swap, and a pure
  reordering of the selector list is correctly not a repoint.
- `ledger.previous_document` factors out the `git show HEAD:./<path>` shape so the previous
  committed REGISTRY is retrieved exactly as the previous committed ledger already was.
- `check_coherence` gained a **required** `repointed_ids` argument. It is required, not defaulted to
  empty, because an empty default would silently reinstate the id-only test in any caller that
  forgot it. Both the content-bound and the `updated` half consume it.

**Design choice, deliberately different from the review's first suggestion.** The reviewer proposed
adding a `binding_digest` COLUMN to `_ROW_KEYS`. The committed-registry comparison is equivalent in
strength — both make a repoint amber for exactly one commit cycle, identically to a new id — but it
leaves the ledger's DOCSUP-02 / clause-1 shape untouched, so a human ratifier still hand-writes only
the two content digests and never a third derived value. The ledger is a hand-authored, human-only
artifact; adding a column a human must compute is a real usability cost for no gain in strength. The
review's stated minimum-viable alternative (treat changed `(source_digest, target_digest)` as
unratified) was rejected outright: it would fail every legitimate `reviewed-no-change` re-review
after a source edit, which is the normal case.

**RED evidence** (`test_repointing_a_ratified_binding_is_not_fresh`, pre-fix):

```
AssertionError: a repointed binding inherited its earlier ratification
assert 'FRESH' != 'FRESH'
 +  where 'FRESH' = _state_of({... 'findings': [], 'ok': True, ...}, 'b1')
```

`'findings': []` and `'ok': True` reproduce the reviewer's executed `B1 repointed ok=True ['FRESH'] []`.
Non-degradation control `test_reordering_selectors_is_not_a_repoint` was green pre-fix and stays green.

ADR-0010 clauses 3b and 4 rewritten: they had documented the id-only test.

---

### WR-01 — `uncovered_max` read from the working tree

**Fixed.** The enforced ceiling is the previous COMMITTED one, symmetric with `binding_min`. The
working-tree value is consulted only when there is no committed ledger at all, where it can add a
constraint but never relax one.

**RED evidence** (`test_uncovered_max_comes_from_the_committed_ledger`, pre-fix):

```
AssertionError: the enforced ceiling must be the COMMITTED one
assert 99 == 0
```

which is the reviewer's `wt-raised uncovered_max ok= True {'live': 2, 'max': 99, ...}`. The paired
non-degradation control (`test_uncovered_max_falls_back_to_the_working_tree_without_history`) pins
that a fresh checkout is not silently un-ratcheted.

ADR-0010 clause 5 now states the committed-source property for BOTH ratchets.

---

### WR-02 — a newline in a registry `target` forged derived-queue rows

**Fixed at both ends**, as the review asked.

- **Schema** (constitution plane): `"pattern": "^[^\\u0000-\\u001F\\u007F|]+$"` on `target` and on
  each `sources` item — C0/DEL control characters and the markdown table separator.
- **`tools.docs_guard.registry`**: the same rule restated, ordered BEFORE the shape pass. Not
  redundancy for its own sake: a raw jsonschema `pattern` failure prints the REGEX, and the reason a
  path may not contain a newline (a forged queue row, an inflated SessionStart count) is not
  recoverable from a regex. Class F is the new adversarial table; the offending character is named,
  never echoed.
- **`docs_staleness.render`**: every cell escaped visibly, backslash-first so the escapes are not
  themselves re-escaped. A renderer that can be made to emit a forged row is a renderer bug
  regardless of who validated its input, and this generator's output is COUNTED by `inject.py`, not
  read.

Landed as ONE atomic constitution-plane commit per D-18: schema + `hash --write` rebaseline +
`contracts_index` + the syrupy snapshot. `docs_sync` was re-run and produced no change (the
generated reference page does not render field descriptions).

**RED evidence:** six registry rows `Failed: DID NOT RAISE <class RegistryError>`
(`target_newline`, `target_carriage_return`, `target_pipe`, `target_tab`, `source_newline`,
`source_pipe`), and on the render side one binding produced a forged row plus a leaked separator:

```
AssertionError: a cell separator leaked into the row:
  '| alpha-required | docs/a.md | FAKE | x | BROKEN | required | updated | (none) |'
assert 9 == 7
```

---

### WR-03 — a config error escaped `cli.main()`'s 0/1/3 contract

**Fixed.** The impact map is computed in `main()` behind a containment that degrades to an empty map
— `impact.py`'s already-established NEVER FABRICATE answer for an unmappable set — and states the
degradation on stderr rather than silently dropping the column. Passing the map into `render()` also
removes the per-binding `impact_ids` call from the report path.

**RED evidence:** the stub raise (the duplicate-authority `ValueError`, at exactly the call site
`cli.py:219 -> cli.py:169`) propagated straight out of `main()` with a traceback and no exit code.

---

### WR-04 — `docs_staleness.main()` classified twice

**Fixed.** `write_rows()` is split out as the pure publish half; `write()` keeps its behaviour;
`main()` computes the rows once and reports from them. `write()`'s `queue_path` default is
late-bound to `QUEUE_PATH` so the module constant stays the single source of the destination, and
the `relative_to` label degrades instead of raising for an out-of-repo path.

**RED evidence:** with a stub whose first classification returns one obligation and every later one
returns none —

```
AssertionError: classification ran 2 time(s); main() must compute it once
...
Captured stdout: wrote .memory/derived/docs-staleness.md (0 binding(s) needing review)
```

— printing `0` over a file rendered from one row, which is the disagreement the finding describes.

---

### IN-01 — a live model identifier committed as a test fixture

**Fixed.** The `_MODEL_IDENTIFIER_RE` negative fixture now uses a shape-matching but non-existent id.
The detector is anchored on vendor+model SHAPE, so coverage is unchanged. The repo rule reads on the
artifact, not on the author's intent.

**RED evidence:** `grep -rn` over `tools/ docs/ harness/ contracts/` returned exactly one live
identifier, at the cited line; after the fix it returns none.

---

### IN-02 — a backslash-spelled destination bypassed the ledger classification

**Fixed.** The classification now folds `\` to `/` exactly as the `..`-segment pre-check already did,
so both halves see one normalization. A `backslash_separator` row joins the parametrized spelling
table; the prefix-adjacent narrowness control is unchanged and green.

**RED evidence:** `Failed: DID NOT RAISE <class ReviewLedgerRefusal>` on the new row, in both the
direct and the end-to-end parametrization.

---

### IN-03 — the contract graph is recompiled once per binding

**Accepted as a residual, not fixed.** Rationale:

- Correctness is unaffected — the reviewer says so, and the result is deterministic.
- WR-03's fix moved the report-path calls out of `render()` into a single comprehension in `main()`,
  so the call site is now one place instead of two, but the graph is still compiled once per
  binding.
- Closing it properly means changing `impact.py`'s public signature (to accept a pre-compiled graph
  and relationship list) or adding an `id(cfg)`-keyed memo. The signature change ripples into
  `docs_staleness.rows`, `cli`, and three test modules; the memo introduces cached state into a
  module whose docstring makes a point of being pure. Neither is a trivially safe change to make
  inside a review-fix pass, and both deserve their own adversarial row for the cache-invalidation
  case.

The docstring's "compiled ONCE per call" claim is accurate as written — it is a per-CALL guarantee,
and only reads as a whole-report guarantee. The gap is the call sites, and closing it is a
performance change with an API blast radius. Carried forward.

## Residuals carried forward

- **IN-03** — graph recompiled once per binding in both report paths (above).
- **`harness/skills/gate-model/SKILL.md`'s `path_deny_globs` prose** still lists only the three
  constitution trees, omitting `*.env` and the ledger. Deliberately untouched here for the reason
  ADR-0010 already records: that file is the TARGET of the `gate-model-permission-surface` binding,
  so editing it would move a target digest the human ratification of this phase's ledger is being
  asked to sign. It is a Phase-29 `/docs-update` item — the loop this model exists to drive. The
  entry now needs to name `ledger_guard` as well.
- **`tools/hooks/secret_scan.py:44-47`** still hardcodes its pattern list rather than reading the
  contract. Carried forward unchanged from 26.2 / 27.1 / 27.2.

## Gates

| Gate | Result |
|------|--------|
| `uv run pytest -q` | 1412 passed, 8 snapshots passed |
| `python -m tools.contract_drift.drift` | OK — live manifest matches the committed baseline |
| `uv run pytest tools/harness_lint -q` | 300 passed |
| `python -m tools.harness_emit` + `git status --porcelain` | 96 artifacts emitted, tree clean |
| `python -m tools.docs_guard` | FAILED with `broken-binding` — the designed pre-ratification state, unchanged |
