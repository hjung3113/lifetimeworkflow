---
phase: 28-human-docs-registry-guard-derived-queue-v2-3-c
plan: 09
subsystem: adoption-apply / permission-matrix
tags: [guard, docs-plane, self-green, path-deny, refusal]
requires:
  - tools/adoption_apply/apply.py::refuse_unsafe_destination (27.1 choke point)
  - tools/harness_perms::resolve_path (CONFIG-02 resolver)
provides:
  - tools/adoption_apply/apply.py::REVIEW_LEDGER_GLOBS
  - tools/adoption_apply/apply.py::ReviewLedgerRefusal
  - harness/permission-matrix.json::path_deny_globs[docs/.docs-review-ledger.toml]
affects:
  - tools/adoption_apply/cli.py (_cmd_apply except tuple)
  - plan 28-04 (first_seen-unratified — the third layer)
  - plan 28-08 (ADR-0010 ratifies the boundary this plan encodes)
tech-stack:
  added: []
  patterns: [parametrized adversarial-input table, single choke point, pure-data permission slot]
key-files:
  created: []
  modified:
    - tools/adoption_apply/tests/test_constitution_refusal.py
    - tools/adoption_apply/apply.py
    - tools/adoption_apply/cli.py
    - harness/permission-matrix.json
decisions:
  - "The review ledger is a THIRD path-deny domain, disjoint from constitution and secret — its own constant, its own exception, never a widening of CONSTITUTION_GLOBS"
  - "DENY, not ask: no token (not even GOLDEN_APPROVE_HUMAN) legitimizes an agent-authored ledger disposition"
  - "docs/doc-dependencies.toml stays agent-writable at both layers so DOCSUP-07 remains implementable"
metrics:
  tasks: 2
  commits: 2
requirements: [DOCSUP-02, DOCSUP-03]
---

# Phase 28 Plan 09: Ledger Write Guard Summary

`docs/.docs-review-ledger.toml` is now refused at the adoption-apply choke point via its own
`REVIEW_LEDGER_GLOBS` / `ReviewLedgerRefusal` pair and denied at the permission layer via
`path_deny_globs`, closing the docs-plane self-green hole on both write surfaces while leaving the
registry writable and `CONSTITUTION_GLOBS` untouched.

## What was built

**Task 1 — RED** (`05c06f4`). Two module-level tables appended to
`tools/adoption_apply/tests/test_constitution_refusal.py` (pure additions; 27.1 D-01 honoured — no
existing test function weakened, renamed, or deleted):

- `REVIEW_LEDGER_DESTINATIONS` — six rows, each carrying an `expected` field that pins which guard
  must fire: `plain`, `dot_slash_prefixed`, `interior_dot_segment`, `dotdot_resolving_onto_ledger`
  (expected `"any"` — already stopped by the 27.1 structural pre-check, so the row asserts only
  that it is refused), `upper_case`, `mixed_case`.
- `LEDGER_ADJACENT_ALLOWED` — the narrowness control: `docs/doc-dependencies.toml` (the registry,
  first row and the load-bearing one), an ordinary human doc, both prefix-adjacent names
  (`.docs-review-ledger.toml.bak`, `.docs-review-ledger-notes.md`) that a sloppy `startswith` glob
  would over-match, and a derived-plane path.
- Resolver assertions read the matrix through `tools.harness_perms.load_matrix` — the same loader
  the hooks use — rather than re-reading the JSON by path, so the test proves enforcement, not file
  content.

**Task 2 — GREEN** (`246fcac`). Three coordinated edits plus the emitter round-trip.

## RED evidence (ledger write-side hole)

`! uv run pytest tools/adoption_apply/tests/test_constitution_refusal.py -k review_ledger -q`
exited 0 (the inverted form succeeds only when the selection fails). Never piped into
`head`/`tail` — a pipeline reports the last command's status and would make the gate unfailable;
the output was redirected to a file instead.

```
FFF.FFFFF.FF.....F......                                                 [100%]
...
11 failed, 13 passed, 37 deselected in 0.08s
```

Failures, each for its stated reason:

| Rows | Failure |
|------|---------|
| `test_review_ledger_destination_is_refused[plain, dot_slash_prefixed, interior_dot_segment, upper_case, mixed_case]` and the five matching `..._end_to_end` rows (10) | `AttributeError: module 'tools.adoption_apply.apply' has no attribute 'ReviewLedgerRefusal'` — the exception class did not exist |
| `test_review_ledger_permission_matrix_denies_the_ledger` (1) | `AssertionError: assert 'allow' == 'deny'` for `docs/.docs-review-ledger.toml`. **That assertion IS the hole, stated as a test** |

The 13 pre-fix passes pin the baselines the fix must not disturb: five
`LEDGER_ADJACENT_ALLOWED` rows (including `docs/doc-dependencies.toml`) green against unmodified
code — the "did not over-refuse" baseline; five existing `path_deny_globs` entries still resolving
`deny`; the registry-writable resolver row; and both `dotdot_resolving_onto_ledger` rows, already
refused by the 27.1 `..`-segment pre-check.

## Why BOTH edits were required

Neither closes the hole alone, and each covers a surface the other cannot reach:

- **`refuse_unsafe_destination` (apply.py)** guards only the **adoption-apply write path**. It
  covers Phase 29's `/adopt` writing through a manifest. A plain agent `Write`/`Edit` tool call
  never enters this module, so this edit alone leaves the ordinary path wide open.
- **`path_deny_globs` (permission-matrix.json)** is what the CONFIG-02 resolver — and through it
  the Phase-4 hooks — consults on the **ordinary agent tool path**. It does not run inside a bare
  `python -m tools.adoption_apply apply` invocation, which is exactly why 27.1 duplicated the
  constitution check in-process to begin with.
- **Plan 28-04's `first_seen-unratified`** is the third layer: a write that somehow slips past both
  still cannot produce green.

## Design points

`REVIEW_LEDGER_GLOBS` is its own module constant and `ReviewLedgerRefusal` its own `ValueError`
subclass, explicitly **not** a subclass of `ConstitutionRefusal`; the tests assert
`not isinstance(exc, ConstitutionRefusal)`. Conflating them would teach an operator to reach for
`GOLDEN_APPROVE_HUMAN`, which authorizes constitution writes and must never be understood to
authorize a ledger disposition — there is no token that makes an agent-authored disposition
legitimate, which is precisely how this domain differs from the constitution plane.

The refusal branch sits inside the existing choke point and reuses the same `relative.lower()`
value the constitution check consumes, through the same `tools.harness_perms.resolve_path` — one
normalization for two disjoint domains, and no sixth `_confine` spelling added to the repo.

`apply_manifest` buckets `ReviewLedgerRefusal` into `summary["refused"]` alongside
`ConstitutionRefusal`: it is a refusal, not a fault, so a single refused destination reports rather
than aborting the batch. `cli.py::_cmd_apply`'s except tuple gained it too, mapping to the existing
exit 1 and the existing `tools.adoption_apply apply: {exc}` stderr shape — no new exit code, no new
message shape.

`CONSTITUTION_GLOBS`, `contract_guard.py`, and `GOLDEN_APPROVE_HUMAN` semantics are untouched. The
`contract_guard.py:16-20` disjoint-domain invariant remains literally true: the ledger is a third
domain alongside constitution and secret, not a member of either. The matrix `_note` was extended
with one clause saying exactly that, and naming the registry as deliberately excluded.

## Case-sensitivity residual

None — the case variants are genuinely refused, not merely asserted as-is. `resolve_path` is
`fnmatchcase` (case-**sensitive**), but the choke point classifies `relative.lower()`, so
`DOCS/.DOCS-REVIEW-LEDGER.TOML` and `docs/.Docs-Review-Ledger.toml` both fold onto the glob and
raise. Confirmed live: both rows are green post-fix. This matches the existing
`refuse_if_constitution(relative.lower())` posture exactly rather than inventing a new case rule.

Residual worth naming: this case-folding lives **only** in the `apply.py` choke point. The
permission-layer `resolve_path(path_deny_globs, ...)` call made by the hooks is case-sensitive, so
a case-variant spelling on the ordinary agent tool path is denied only if the caller lowers the
path first. That is pre-existing resolver behaviour shared with `contracts/**` / `golden/**`, not a
regression this plan introduces, and changing it would alter the constitution plane's semantics —
out of this plan's scope. Flagged for plan 28-08's ADR-0010 to record.

## Deviations from Plan

**1. [Rule 3 — plan premise corrected] The emitter round-trip produced no diff, and that is correct.**
- **Found during:** Task 2.
- **Plan stated:** editing `harness/permission-matrix.json` requires a `tools.harness_emit`
  round-trip to `opencode.json` + `.claude/settings.json` "or the `emit-drift` CI job (ci.yml:203)
  fails".
- **Actual:** `tools/harness_emit/permissions.py:23` defines
  `_RESOLVER_ONLY_KEYS = ("_note", "path_deny_globs")` and
  `build_permission_block` **strips** both — they are resolver-only data that never reaches an
  emitted runtime config. Neither of this plan's two matrix edits (`_note` prose, `path_deny_globs`
  entry) can therefore move an emitted byte.
- **Handling:** the round-trip was run anyway as the plan directed;
  `git diff --stat -- opencode.json .claude/settings.json` and
  `git status --porcelain -- .opencode .claude opencode.json` were both empty, and a second
  `generate` left `git diff --exit-code -- .opencode .claude opencode.json` clean (exit 0), so
  `emit-drift` passes. No emitted file was hand-edited. `tools/harness_emit` (including its
  determinism snapshot) and `tools/harness_lint/tests/test_opencode_json.py` were run and pass.

**2. [Documented conflict in the plan itself] `grep -c 'docs-review-ledger' harness/permission-matrix.json` is 2, not 1.**
- The plan's acceptance criterion asked for 1; the plan's own action text instructed "Extend the
  file's `_note` with one clause naming the ledger as a third path-deny domain". Both cannot hold.
- **Resolved toward the action text** — the `_note` clause is the load-bearing instruction (it is
  what stops the next reader folding the ledger into constitution or secret), and the criterion's
  intent (exactly one *glob*) is met: `path_deny_globs` contains exactly one ledger entry, asserted
  programmatically:
  `['contracts/**', 'docs/adr/**', 'golden/**', '*.env', '**/*.env', 'docs/.docs-review-ledger.toml']`.

**3. [Scope note] `cli.py` is not in the plan frontmatter's `files_modified` but is required by its action text.**
- Task 2 step 4 explicitly says "Add it to `cli.py::_cmd_apply`'s except tuple as well". Followed
  the action text; the frontmatter list is the incomplete one.

**4. [Repo-state — cross-plan commit contamination] Commit `05c06f4` carries seven files this plan does not own.**
- **Found:** flagged by the team lead after the fact.
- **What landed:** `05c06f4` contains `tools/adoption_apply/tests/test_constitution_refusal.py`
  (this plan's) **plus** `exec-28-01`'s entire constitution-plane set —
  `contracts/harness/docs/doc-dependencies.schema.json`, `contracts/.hashes/manifest.json`,
  `docs/reference/doc-dependencies.md`, `.memory/derived/contracts-index.md`,
  `tools/docs_sync/tests/test_docs_sync_determinism.py` and its `.ambr`, and
  `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr`.
- **Mechanism (matters for the fix):** the `git add` was already pathspec-limited to the single
  test file. The contamination came from the **index**, not from the add — `exec-28-01` had staged
  those seven files in the shared working tree and not yet committed, and `git commit` publishes
  the whole index regardless of what the immediately preceding `add` named. A pathspec-limited
  `git add` therefore does **not** prevent this; only `git commit -- <pathspec>` (or inspecting
  `git diff --cached --name-only` before committing) does.
- **Ruling (team lead):** history stays as-is. All seven landed atomically, so `drift` /
  `stale-derived` can never observe a half-landed constitution plane; un-mixing would need a
  destructive `reset --soft` racy against live siblings. Not attempted.
- **Remediation applied for the rest of this run:** every subsequent commit used an explicit
  pathspec. Verified clean: `246fcac` = 3 files (`apply.py`, `cli.py`, `permission-matrix.json`),
  `7879292` = 1 file (this SUMMARY). Only `05c06f4` is mixed.
- **Cross-referenced in** `28-01-SUMMARY.md`.

## Deferred Issues (out of scope — logged, not fixed)

- `harness/skills/gate-model/SKILL.md:17-21` says "These are the `path_deny_globs` in
  `harness/permission-matrix.json`" while listing only the three constitution trees. That prose was
  already imprecise before this plan (it omitted `*.env` / `**/*.env`) and is now one entry further
  behind. Correcting it means editing a harness skill source, re-emitting, and updating the
  `test_emit_determinism` syrupy snapshot — none of which this plan owns, and the snapshot is a
  collision surface with sibling wave-1 plans. **Recommend folding into plan 28-08 alongside
  ADR-0010.**
- `uv run ruff check tools/adoption_apply` reports two pre-existing `I001` import-sort findings on
  `apply.py:39` and `cli.py:29`. `git diff HEAD -- tools/adoption_apply/apply.py` shows **zero**
  import-line changes, and `cli.py`'s import block is likewise untouched — these predate this plan.
  `tools/` as a whole reports 422 ruff findings and CI runs no ruff job, so this is not a gate.
  The one file where an import WAS added, `test_constitution_refusal.py`, is ruff-clean.

## Gate results

| Gate | Result |
|------|--------|
| `uv run pytest tools/adoption_apply tools/harness_lint/tests/test_opencode_json.py -q` | **128 passed** |
| Widened to `+ tools/harness_emit tools/harness_perms` | **209 passed**, 1 snapshot passed |
| Second `generate` → `git diff --exit-code -- .opencode .claude opencode.json` | **clean (exit 0)** |
| `git diff --stat tools/hooks/contract_guard.py` | **empty** — `CONSTITUTION_GLOBS` not widened |
| ledger entries in `path_deny_globs` array | **1** |
| `git status --porcelain contracts uv.lock` | **empty** |
| `git diff --diff-filter=D --name-only` per commit | **empty** — no deletions |

`git status --porcelain tools/docs_guard` is **not** empty
(`M tools/docs_guard/tests/conftest.py`, `?? tools/docs_guard/digest.py`,
`?? tools/docs_guard/tests/test_digest.py`). That is `exec-28-02`'s in-flight work in the same
wave, not this plan's regression — untouched and unwaited-on, per the wave-1 protocol. The full
suite was deliberately NOT run in flight; the fan-in belongs to plan 28-08.

## Success Criteria

- [x] `docs/.docs-review-ledger.toml` refused at the adoption-apply choke point and denied at the
      permission layer, in every spelling the table covers.
- [x] `docs/doc-dependencies.toml` remains writable at both layers — DOCSUP-07 stays implementable.
- [x] Own constant, own exception type; `CONSTITUTION_GLOBS` and `GOLDEN_APPROVE_HUMAN` semantics
      untouched; disjoint-domain invariant holds.
- [x] Emitter round-trip closed (no-op by construction — see Deviation 1).

## Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 | `05c06f4` | `test(28-09): add review-ledger refusal table and its must-stay-allowed control` |
| 2 | `246fcac` | `feat(28-09): refuse review-ledger writes at the choke point and the permission layer` |

## Self-Check: PASSED

All four modified files present; both commit hashes resolve in `git log --all`. No BOM, LF-only.
