---
phase: 28-human-docs-registry-guard-derived-queue-v2-3-c
reviewed: 2026-07-21T00:00:00Z
depth: deep
files_reviewed: 20
files_reviewed_list:
  - tools/docs_guard/__init__.py
  - tools/docs_guard/__main__.py
  - tools/docs_guard/cli.py
  - tools/docs_guard/digest.py
  - tools/docs_guard/guard.py
  - tools/docs_guard/impact.py
  - tools/docs_guard/ledger.py
  - tools/docs_guard/registry.py
  - tools/docs_guard/pyproject.toml
  - tools/docs_guard/tests/test_guard.py
  - tools/docs_guard/tests/test_ledger.py
  - tools/memory_regen/docs_staleness.py
  - tools/memory_regen/inject.py
  - tools/adoption_apply/apply.py
  - tools/adoption_apply/cli.py
  - tools/adoption_apply/tests/test_constitution_refusal.py
  - harness/permission-matrix.json
  - harness/commands/refresh-memory.md
  - contracts/harness/docs/doc-dependencies.schema.json
  - docs/doc-dependencies.toml
  - docs/adr/0010-human-docs-review-obligation-model.md
  - .github/workflows/ci.yml
findings:
  critical: 3
  warning: 4
  info: 3
  total: 10
status: issues_found
---

# Phase 28: Code Review Report

**Reviewed:** 2026-07-21
**Depth:** deep (cross-module, with executable mutation/bypass probes)
**Files Reviewed:** 20
**Status:** issues_found

## Summary

The digest algorithm (D-03), the registry validator (DOCSUP-01), the injector (D-11), `impact.py`
(D-12), and the adoption-apply write guard's *path-spelling* coverage all hold up under adversarial
probing. I could not find a spelling that reaches the ledger through
`refuse_unsafe_destination` — `./`, interior `.`, `..`, upper/mixed case, a symlinked file, and a
symlinked *directory* were all refused, while `docs/doc-dependencies.toml` and the four
prefix-adjacent names stayed writable. Deleting the second half of the `FRESH` condition reds three
tests, so that control has real coverage.

Three controls do **not** survive adversarial probing, and all three are instances of the
milestone's recurring defect — a control that is GREEN because no fixture supplies the input that
bypasses it:

1. **Drift suppression is a self-green bypass.** A brand-new binding self-blessed in the same
   change reports `ok=True` when one of its sources is a currently-drifted contract, because the
   suppression pass demotes `first_seen-unratified` from `fail` to `note`. Proven by execution.
2. **The `path_deny_globs` layer has no enforcer.** Layer 1 of ADR-0010's three-layer table is
   inert data: no hook consumes the full `path_deny_globs` union, and the emitter strips the key.
   The ordinary agent `Write`/`Edit` path is unguarded, and the test that "proves" the layer only
   asserts that data matches itself.
3. **`first_seen-unratified` keys on the binding *id* alone.** Repointing an already-ratified id at
   a different source/target pair reports `FRESH` with zero findings. Proven by execution.

Plus one ratchet asymmetry: `uncovered_max` is read from the **working tree**, not the committed
ledger — the exact hazard `guard.py:437-440` cites as the reason `binding_min` is not.

Pre-existing designed state (missing ledger, `broken-binding` findings, ADR-0010 `proposed`, seeded
bindings amber) is excluded per the brief, as is suite greenness.

## Critical Issues

### CR-01: Drift suppression demotes blocking coherence findings, producing a permanent self-green escape

**File:** `tools/docs_guard/guard.py:351-352`, `tools/docs_guard/guard.py:401-405`

**Issue:** The D-13 suppression pass demotes *every* `fail`-level finding whose `binding_id` is a
suppressed binding — including the three "this claim has never been established" reasons
(`first_seen-unratified`, `unverified-disposition`, `disposition-incoherent`, plus
`unknown-binding` and `superseding-adr-required`). Those are not downstream consequences of
contract drift; only `stale-digest` is, and only that one is named in the comment at
`guard.py:396-400`. Because `_sources_drifted` (step 2) is evaluated *before* the `FRESH` guard
(step 3), a binding whose source is a currently-drifted contract never reaches the self-green
closure at all, and the final `any(level == LEVEL_FAIL ...)` roll-up at `guard.py:444` sees only
the demoted `note`.

Executed against the shipped code in a scratch repo (registry + ledger authored in one uncommitted
change, `newbinding` with a `reviewed-no-change` row carrying its exact live digests):

```
A1 no-drift  ok= False ['STALE_REQUIRED']            # correct — first_seen-unratified blocks
A2 drifted   ok= True  ['SUPPRESSED']                # BYPASS
   findings: [('note', 'first_seen-unratified')]
```

The escape is **permanent, not one-cycle**. The commit that CI would have failed is the commit that
lands the self-authored ledger row. Once landed, `previous_rows` contains the id, so the next run
reports `FRESH` unconditionally (probe C: `next-commit ok= True ['FRESH']`). Contract-drift being
red on that same commit does not help: the drift is resolved by a hash rebaseline in a *later*
commit, by which time the ledger row is already history.

This is the identical failure shape the phase brief describes — the control ships green because no
fixture combines a drifted source with an unratified row.

**Fix:** Restrict demotion to the reasons that are genuinely downstream of drift, and never demote
a ratification-authority finding:

```python
# guard.py — near BLOCKING_REASONS
SUPPRESSIBLE_REASONS: frozenset[str] = frozenset({REASON_STALE})

for finding in findings:
    if (
        finding["binding_id"] in suppressed_ids
        and finding["level"] == LEVEL_FAIL
        and finding["reason"] in SUPPRESSIBLE_REASONS
    ):
        finding["level"] = "note"
        finding["message"] += " (suppressed — contract-drift leading)"
```

and make `SUPPRESSED` unreachable for a binding carrying a blocking finding, so ordering cannot
re-open it:

```python
elif _sources_drifted(binding, root_path, drifted) and not blocking_by_id.get(binding.id):
```

Add the missing fixture row: drifted source × brand-new self-blessed row × `ok is False`.

---

### CR-02: The ledger's `path_deny_globs` entry is enforced by nothing — ADR-0010's layer 1 does not exist

**File:** `harness/permission-matrix.json:33`, `docs/adr/0010-human-docs-review-obligation-model.md:138`,
`tools/adoption_apply/tests/test_constitution_refusal.py:459-467`

**Issue:** ADR-0010's three-layer table claims `path_deny_globs` covers "the ordinary agent
`Write`/`Edit` tool path". Nothing reads that key for enforcement:

- `tools/hooks/contract_guard.py:43` deliberately reads only its own `CONSTITUTION_GLOBS`
  (`contracts/**`, `docs/adr/**`, `golden/**`) and documents at lines 16-20 that it must **not**
  read the full union.
- `tools/hooks/secret_scan.py:37` reads only `SECRET_PATH_GLOBS` (`*.env`, `**/*.env`), and its
  test docstring (`tools/hooks/tests/test_secret_scan.py:11`) says explicitly it does not deny the
  full `path_deny_globs`.
- `tools/harness_emit/permissions.py:23` lists `path_deny_globs` in `_RESOLVER_ONLY_KEYS` and
  **strips** it, so it never reaches the emitted `opencode.json` either.

`grep -rn "docs-review-ledger" harness/ .opencode/ .claude/` returns only the matrix data line and
its `_note`. Every *pre-existing* entry in `path_deny_globs` is separately re-declared inside a
hook; the new one is not, so it is the first inert entry in the file.

The test that is supposed to prove the layer,
`test_review_ledger_permission_matrix_denies_the_ledger`, asserts
`resolve_path(load_matrix()["path_deny_globs"], "docs/.docs-review-ledger.toml") == "deny"`. Its own
docstring claims this is "asserted through the resolver the hooks actually consume, not by
re-reading the JSON" — but no hook consumes that list, so the assertion reduces to "the glob I just
added matches the path I just added". It cannot fail while the control is absent, which is the
definition of vacuous coverage.

Net effect: the only real write-side control is `refuse_unsafe_destination`, which guards the
adoption-apply module only. A plain agent `Write` to `docs/.docs-review-ledger.toml` is
unobstructed — and it is that write, not an `/adopt` manifest, that CR-01 shows can be laundered
into permanent green.

**Fix:** Give the third domain a real PreToolUse enforcer, mirroring the existing two-hook shape:

```python
# tools/hooks/ledger_guard.py (new) — third disjoint domain, NO token bypass
REVIEW_LEDGER_GLOBS = ["docs/.docs-review-ledger.toml"]

def decide(file_path: str) -> dict | None:
    rel = repo_relative(file_path)
    if not rel or resolve_path(REVIEW_LEDGER_GLOBS, rel.lower()) != "deny":
        return None
    return emit_deny(
        f"ledger-guard: '{file_path}' is the human-review ledger — only a human may author a "
        "review disposition. GOLDEN_APPROVE_HUMAN does NOT apply."
    )
```

Import that constant into `apply.py` rather than declaring a second copy, wire the hook into the
emitted PreToolUse set for both runtimes, and replace the vacuous matrix test with one that drives
the hook's `decide()` with an absolute path and asserts a deny. Until the enforcer exists,
ADR-0010's table row is a false claim and should not stand.

---

### CR-03: `first_seen-unratified` keys on the binding id only — repointing a ratified id is silently FRESH

**File:** `tools/docs_guard/ledger.py:363`, `tools/docs_guard/ledger.py:73`

**Issue:** `_check_content_bound` returns green as soon as `row.id in previous_rows`. A ledger row
(`_ROW_KEYS = {"id", "source_digest", "target_digest", "disposition"}`) records **no** identity of
*what* was reviewed beyond the id, and the content-bound branch never compares against the previous
row's digests. So an id that has been ratified once carries its ratification to whatever the
registry later says that id means.

Executed: binding `b1` ratified against `src/a.py` → `docs/hard.md`, committed. Then the registry
is repointed to `src/b.py` → `docs/easy.md` and the ledger digests rewritten to the new live values
in the same uncommitted change:

```
B0 baseline  ok= True
B1 repointed ok= True ['FRESH'] []      # zero findings
```

The registry is agent-writable by design (DOCSUP-07), so this needs only an agent-authored registry
edit plus the ledger write that CR-02 leaves unguarded. It is the "renamed id" attack the brief
names, in the form the tests do not cover: a *renamed* id is caught (new id, absent from
`previous_rows`); a *repointed* id is not.

**Fix:** Bind the ratification to the reviewed pair, not just the name. Add a `binding_digest`
column to `_ROW_KEYS` — a digest over the binding's sorted `sources` + `target` selectors — and
require that a content-bound row's `binding_digest` equal the previous committed row's, otherwise
emit `first_seen-unratified` (the binding's *meaning* has never been ratified). A shape change to
the ledger is a constitution-plane-adjacent human edit, so it is cheapest to land before any real
ledger is authored — which is now, since `docs/.docs-review-ledger.toml` does not yet exist.

Minimum viable alternative if the shape must stay fixed: treat a row whose `(source_digest,
target_digest)` pair differs from the previous committed row's as unratified for content-bound
dispositions — `reviewed-no-change` asserting *changed* digests relative to history is incoherent
on its face.

## Warnings

### WR-01: `uncovered_max` is read from the working-tree ledger, not the committed one

**File:** `tools/docs_guard/guard.py:410` (`coverage` originates at `guard.py:297` →
`load_ledger(ledger)`), contrast `tools/docs_guard/ledger.py:443` and `guard.py:437-440`

**Issue:** `guard.py:437-440` states the rule for `binding_min` — "reading it from the working tree
would let the same edit that deletes a binding also lower the bar" — and `_check_binding_count`
correctly reads `previous.get("coverage", {}).get("binding_min")`. `uncovered_max` does the
opposite: it comes from the freshly-parsed working-tree ledger, so the same uncommitted edit that
drops a document out of coverage can raise the ceiling. ADR-0010:207 documents the committed-source
property for `binding_min` only, so the asymmetry is undisclosed rather than accepted.

Executed (committed `uncovered_max = 0`, two uncovered docs):

```
baseline                ok= False
wt-raised uncovered_max ok= True {'live': 2, 'max': 99, ...}
```

"The guard never writes it" (ADR-0010:196) is true but not the property that matters — the threat
is an agent *editing* it, which CR-02 shows is unobstructed.

**Fix:** Read the threshold the same way `binding_min` is read, falling back to the working-tree
value only when history is unreadable:

```python
committed_max = (previous or {}).get("coverage", {}).get("uncovered_max")
uncovered_max = committed_max if isinstance(committed_max, int) else coverage.get("uncovered_max")
```

and add the paired case: committed `0`, working tree `99`, expect `ok is False`.

---

### WR-02: A registry `target` containing a newline injects fabricated rows into the derived queue and inflates the SessionStart pointer

**File:** `tools/memory_regen/docs_staleness.py:134-137`, `tools/memory_regen/inject.py:98`,
`contracts/harness/docs/doc-dependencies.schema.json` (`target` has `minLength` only, no `pattern`)

**Issue:** `render()` interpolates `target` into a markdown table cell with no escaping, and the
schema constrains `id` with `^[a-z0-9]+(-[a-z0-9]+)*$` but leaves `target` an unconstrained string.
TOML multi-line basic strings permit newlines, and the registry is agent-writable by design. The
injector's row count (`inject.py:98`) counts lines beginning `"| "` and subtracts 2, so injected
lines are counted as real obligations.

Executed with one binding whose `target` is a multi-line string containing a forged table row: the
queue rendered a `FAKE` row and the pointer reported `2 human doc(s) need review` for a registry
holding one binding.

**Fix:** Constrain the target in the schema — `"pattern": "^[^\\\\s]+$"` or at minimum forbid
newline and `|` — and defensively escape/reject in `render()`:

```python
if any(ch in value for ch in ("\n", "\r", "|")):
    raise RegistryError(f"binding {rid!r} target contains a forbidden character")
```

Note the schema is constitution-plane, so this pairs with a hash rebaseline.

---

### WR-03: `cli.main()`'s documented exit-code contract can be escaped by a traceback from `impact_ids`

**File:** `tools/docs_guard/cli.py:205-224`, `tools/docs_guard/impact.py:88-89`

**Issue:** The module docstring pins exits to 0/1/3 and `cli.py:212-215` states "a clean one-line
diagnostic, never a traceback: exit 3 is a DOCUMENTED failure mode, and a traceback here would be
an undocumented one." But only `classify()` is inside the `try`. `render(result)` at `cli.py:219`
calls `impact_ids(entry["sources"])` with `cfg=None` for every binding, which reaches
`effective_relationships(None)` and `compile_graph(None)` — both read the live
`harness/project.toml` and both raise on a malformed or contradictory config (duplicate
contract→authority claim). That surfaces as a raw traceback and an undocumented exit code from the
CI job added at `.github/workflows/ci.yml:288`.

**Fix:** Move `render` inside the `try`, or catch config errors around the impact computation and
degrade to empty impact — the `NEVER FABRICATE` posture at `impact.py:74-82` already establishes
that an empty impact list is the correct degraded answer.

---

### WR-04: `docs_staleness.main()` runs the full classification twice, and the printed count can disagree with the file it just wrote

**File:** `tools/memory_regen/docs_staleness.py:171-172`

**Issue:** `main()` calls `write()` (which calls `rows()` → `classify()` → a `git ls-files`
subprocess, a full corpus walk, and a full contract-manifest rebuild via `_default_drift_gate`) and
then calls `rows()` a *second* time purely to print a count. Besides doubling the cost of every
`/refresh-memory`, the second run re-reads the tree, so the number printed to the operator is not
necessarily the number in the file that was written.

**Fix:** Compute once and reuse:

```python
queue_rows = rows()
out = write_rows(out_path, queue_rows)   # or have write() return (path, rows)
print(f"wrote {out.relative_to(_REPO_ROOT)} ({len(queue_rows)} binding(s) needing review)")
```

## Info

### IN-01: A live model identifier is committed as a test fixture

**File:** `tools/docs_guard/tests/test_ledger.py:545`

**Issue:** The negative fixture for `_MODEL_IDENTIFIER_RE` is the literal string
`"claude-opus-4-8"` — a real, current model identifier committed into a repo artifact.
`CLAUDE.md`'s non-negotiable ("커밋·PR·코드 코멘트 등 레포 산출물에 모델 식별자 미포함") reads on
the artifact, not on the author's intent, and the detector's own docstring at line 558 already
lists the shapes in prose without needing a live id in executable data.

**Fix:** Use a shape-matching but non-existent id: `"claude-opus-0-0"`.

---

### IN-02: A backslash-spelled destination bypasses the ledger classification (Windows-relevant only)

**File:** `tools/adoption_apply/apply.py:169` vs `apply.py:215-220`

**Issue:** Line 169 normalizes `\` → `/` for the `..`-segment check, but the deny classification at
line 215 uses `target_path.relative_to(resolved_root).as_posix()`, which on POSIX preserves a
literal backslash. `refuse_unsafe_destination("docs\\.docs-review-ledger.toml", root)` is ALLOWED
and returns a path to a file literally named `docs\.docs-review-ledger.toml`. Harmless on the
supported ubuntu CI (it is a different file), but on Windows that spelling *is* the ledger. The
existing `REVIEW_LEDGER_DESTINATIONS` table covers `./`, interior `.`, `..`, and case, but not
this one.

**Fix:** Include `destination.replace("\\", "/")` in the normalization that feeds the
classification, and add a `backslash_separator` row to the parametrized table.

---

### IN-03: The contract graph is recompiled once per binding in the report path

**File:** `tools/docs_guard/cli.py:169`, `tools/memory_regen/docs_staleness.py:100`

**Issue:** `impact_ids` documents "The graph is compiled ONCE per call, never once per path" — but
both callers invoke it inside a per-binding loop, so the graph is compiled once per *binding*. With
the 8 seeded bindings that is 8 compilations per report. Correctness is unaffected (the result is
deterministic), and this is noted only because the docstring's claim reads as a whole-report
guarantee that the call sites do not honor.

**Fix:** Hoist a single `compile_graph(cfg)` / `effective_relationships(cfg)` pair and pass it in,
or add a small memo keyed on `id(cfg)`.

---

## Verified sound (probed, no finding)

- **Digest (D-03)** — interleaved `path\n` + per-file `sha256\n`; labels relative to `root`
  (`digest.py:109-122`); `_confine` raises on a root escape including via an in-tree symlink
  (`digest.py:44-57`); zero-expansion and missing files map to BROKEN, never to a well-formed
  digest (`guard.py:177-213`).
- **Write-guard path spellings (28-09)** — refused: plain, `./`-prefixed, interior `.`,
  `a/../docs/...` (as `PathEscapeError`), upper-case, mixed-case, a symlinked *file* aliasing the
  ledger, and a symlinked *directory* (`docs2/`) reaching it. Allowed, correctly:
  `docs/doc-dependencies.toml` and all four prefix-adjacent names — DOCSUP-07 is not broken.
  `ReviewLedgerRefusal` is correctly not a `ConstitutionRefusal` subclass.
- **`FRESH` requires both halves** — deleting `and not blocking_by_id.get(binding.id)`
  (`guard.py:362`) reds 3 tests, including two `first_seen_never_fresh` rows.
- **`binding_min` independence (D-06)** — read from the previous committed ledger
  (`ledger.py:443`), and a binding whose target lies outside `HUMAN_CORPUS` is genuinely invisible
  to `uncovered_max`, so the second ratchet is necessary. Neither `guard.py` nor `ledger.py`
  contains any filesystem write.
- **Injector (D-11)** — never-drop tuple unchanged at `inject.py:225`; budget still `4000`
  (`inject.py:197`); `derived_dir` is a parameter (`inject.py:80`); the pointer reads the rendered
  file and never recomputes `classify` (`inject.py:92-95`).
- **Suppression scope (D-13)** — the demotion loop keys on `binding_id`, so an *unrelated*
  binding's staleness finding is not swallowed; drift findings are not restated (only the path half
  of each tuple crosses at `guard.py:241`); a drifted contract does not by itself flip the exit code.
  (The scope defect is CR-01, which is same-binding, not cross-binding.)
- **`impact.py` (D-12)** — returns `[]` for an untracked source; never fabricates; `reverse()`
  unused.
- **Byte hygiene / determinism** — no CRLF, no BOM in any changed file; no wall-clock, calendar, or
  human identity in any committed artifact; `.memory/derived/docs-staleness.md` is gitignored and
  correctly excluded from `stale-derived`.
- **GEN-04** — no `examples/` reference in `tools/docs_guard/`, `docs_staleness.py`, or
  `docs/doc-dependencies.toml`; the registry comment restates the rule.
- **`tools/docs_guard/__init__.py`** — frozen surface intact, lazy PEP-562 re-export unchanged.

---

_Reviewed: 2026-07-21_
_Reviewer: gsd-code-reviewer_
_Depth: deep_
