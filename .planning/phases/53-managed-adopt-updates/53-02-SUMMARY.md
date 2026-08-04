---
phase: 53-managed-adopt-updates
plan: 02
status: complete
requirements: [MONO-12]
commits:
  - 5ed57e7  feat(53-02): distinguish a harness-side move from a target-side edit
  - c744e00  test(53-02): paired positive/negative coverage for every branch 53-02 added
key-files:
  created:
    - tools/adoption_apply/installed.py
    - tools/adoption_apply/tests/test_installed_record.py
  modified:
    - tools/adoption_scan/destinations.py
    - tools/adoption_scan/tests/test_dispositions.py
completed: 2026-08-04
---

# 53-02 — Classification: harness-side move vs target-side edit

`disposition()` gained step 7. When the target's current hash equals the recorded
`installed_sha256` and the recomputed harness payload hash now differs, the destination resolves to
`update` — the harness moved, nobody edited the target. `preserve` still wins ahead of it; a genuine
target-side edit still falls through to `conflict`.

## What was built

- **`tools/adoption_scan/destinations.py`** — `DISPOSITION_ENUM` grows to the contract's 7 values
  (parity machine-asserted, not assumed). `disposition(..., installed_sha=None)` adds the step-7
  branch. `build_manifest(..., installed=None)` threads one recorded hash per destination and copies
  the `installed[]` rows verbatim when non-empty, omitting the key entirely when empty.
  `destination_catalog()` skips `.harness/` — adopt's own bookkeeping is target state, never a
  self-referential destination.
- **`tools/adoption_apply/installed.py`** — the durable record. Reads, writes, and validates against
  `contracts/harness/adoption/manifest.schema.json` **at runtime**; the record shape is never copied
  into code. Validates on READ as well as write, so a tampered `installed_sha256` is refused rather
  than trusted (T-53-05). Every write is confined by `refuse_if_outside_root` (T-53-06). Exactly four
  public names, no CLI, no knowledge of dispositions.

Exactly one hash is stored. The source side is recomputed every run, so a second stored hash would
only go stale.

## Mutation evidence

Every new assertion was mutation-tested. Sixteen mutations were run; all observed **RED**, all
reverted. Two were re-run independently by the orchestrator after the fact rather than taken on the
writer's word:

| Mutation | Observed |
|---|---|
| `build_manifest`: `installed_hashes.get(destination)` → `.get(destination, existing_sha)` | **RED** — `test_build_manifest_unrecorded_divergence_conflicts_not_updates` (plus 2 CR-01 tests) |
| `disposition()`: delete the `return "update"` branch | **RED** — `test_update_is_reachable_when_the_recorded_hash_matches`, `test_build_manifest_threads_installed_records` |

Both restored; suite green again (25 passed) immediately after.

Also observed RED by the executor: removing the `.harness` catalog skip, removing read-side
validation, removing an `__all__` member, the absent-record return, write validation, path
confinement, adding a top-level `last_run_at`, adding a record-level `run_count`, inverting the
recorded-hash comparison, removing `update` from the enum, dropping the installed-hash threading,
omitting a non-empty `installed[]`, and emitting `installed: []` when it should be absent.

## Deviations

**Plan mutation (a) was itself defective — adjudicated and replaced.** The plan mandated deleting the
`installed_sha is not None` conjunct and required the "never fires" test to red. That mutation is
behaviour-preserving: by the time step 7 is reached, step 5 has already returned `create` for a
missing file and the `_existing_hash` fallback has filled `existing_sha` with a real 64-hex digest,
so `existing_sha == None` is unreachable. The executor proved it stays GREEN and stopped rather than
faking a red.

Per this plan's own acceptance rule ("any assertion whose mutation stays GREEN must be replaced, and
the replacement re-mutated"), it was replaced with the `build_manifest` mutation in the table above,
which attacks the same threat — **T-53-07: a destination with no recorded hash resolving to `update`
and being overwritten** — at the point where a missing record is genuinely reachable. The conjunct is
retained as defence in depth and carries a comment saying plainly that it is currently redundant, so
it is not mistaken for a load-bearing guard.

Second, smaller deviation: the plan's `installed[]`-omission test covered only `installed=None`; it
was extended to cover `installed=[]` as well, which is what the plan's prose actually requires.

## Verification (run by the orchestrator, unsandboxed)

- `uv run pytest -q` — **1061 passed** (the executor saw 1060 passed + 1 skipped; the skip was
  `git worktree add`, unavailable in its sandbox, and it runs here)
- `uv run python -m tools.ruff_baseline` — `67 findings (baseline 67) / PASS`
- `uv run python -m tools.contract_drift.drift` — exit 0
- `git diff --quiet -- contracts/` — clean; `find contracts -name '*.schema.json' | wc -l` — `6`
- Scope-cut guard: `grep -rn "conflicts.json\|source_sha256" tools/adoption_apply/ tools/adoption_scan/`
  — **no matches**

## Self-Check: PASSED

Plan 03 is unblocked: the classification layer can tell a harness-side move from a target-side edit,
and the record it depends on round-trips and refuses tampering.
