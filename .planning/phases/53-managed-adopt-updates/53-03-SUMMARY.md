---
phase: 53-managed-adopt-updates
plan: 03
status: complete
requirements: [MONO-12]
commits:
  - c00179c  feat(53-03): wire the update disposition into the apply cycle
  - 35d00db  test(53-03): end-to-end paired coverage for the update path
key-files:
  created:
    - tools/adoption_apply/tests/test_update_disposition.py
  modified:
    - tools/adoption_apply/apply.py
    - tools/adoption_apply/cli.py
    - tools/adoption_apply/tests/test_atomic_apply.py
    - tools/adoption_apply/tests/test_cli.py
    - tools/adoption_apply/tests/test_fixtures.py
completed: 2026-08-04
---

# 53-03 — The update disposition, wired into the apply cycle

Re-running `/adopt` against a target it already wrote now rewrites only the files whose harness
source actually moved, and leaves a human-edited file byte-identical.

## What was built

- **`update` publishes through the replace idiom**, not `atomic_create` — the target exists by
  definition on this path, so a link-based create would collide.
- **`conflict` is reported on stderr** and bucketed as its own outcome. It never replaces target
  bytes. No new artifact: the drafted `manifest.json` already carries a `disposition: "conflict"` row
  per diverged destination and IS the report. No `conflicts[]` array, no exit code by number.
- **The installed record covers every written destination**, marker-merge included, recording the
  bytes AS WRITTEN.

## The trap this plan existed to defuse

`cli.py` writes `harness/project.toml` as `payload + b"\n" + sidecar`. Comparing that destination
against the RAW `harness_proposed_hashes()` value means the post-splice bytes never equal the
proposed hash — `preserve` could never fire, and the new `update` step would fire on **every**
re-run. WR-08 would not die, it would **invert**: a permanent rewrite masquerading as a no-op.

Fixed as pinned: the sidecar is derived BEFORE `build_manifest`, and
`proposed_hashes["harness/project.toml"]` is overridden with the sha256 of the exact payload apply
will write. The splice expression is factored into one helper, `_spliced_project_toml`
(`cli.py:245`), whose two call sites (`cli.py:197`, `cli.py:300`) therefore cannot drift.

Independently re-verified by the orchestrator, not taken on the writer's word — removing the
override reproduces the inversion exactly:

```
applied=0 updated=1 unchanged=0 conflicts=0 skipped=0 refused=0
FAILED tools/adoption_apply/tests/test_update_disposition.py::test_project_toml_survives_reapply_as_preserve
```

Restored; `tools/adoption_apply` back to 122 passed.

## Mutation evidence

Nine mutations, each observed and reverted:

| Mutation | Observed |
|---|---|
| Remove the post-splice proposed-hash override | **RED** — `test_project_toml_survives_reapply_as_preserve` (`update != preserve`) — *re-run independently by the orchestrator* |
| `update` uses `atomic_create` | **RED** — `test_sc2_full_apply_cycle`, `CollisionError: target already exists` |
| Remove marker-merge installed hash | **RED** — `test_installed_record_covers_every_written_destination`, missing `AGENTS.md` |
| Bucket `conflict` as skipped | **RED** — `test_sc2_full_apply_cycle` |
| Remove the `update` classification | **RED** — `test_update_fires_when_the_harness_source_moves` (`conflict != update`) |
| Let `conflict` replace target bytes | **RED** — `test_target_divergence_conflicts_and_leaves_the_file_byte_unchanged` (`b'' != b'human edit\n'`) |
| Remove the stderr conflict print | **RED** — same test, missing `conflict destination=a-managed.txt` |
| Restrict payloads to create only | **RED** — `test_sidecar_is_spliced_on_the_update_path` |
| Make the installed-record write unconditional | **GREEN → replaced** (see below) |

## Deviation — a second vacuous plan test, replaced

The plan's no-op assertion compared **tree hashes**. An unconditional installed-record rewrite that
happens to produce identical bytes leaves the tree hash unchanged, so the mutation stayed GREEN: the
test could not distinguish "did not write" from "wrote the same bytes". Per the anti-vacuous rule it
was REPLACED rather than annotated — it now asserts on the writer call itself
(`call_count == 1`), and the re-mutation reds in `test_true_no_op_writes_nothing`. Identical bytes
hide a rewrite; a call count does not.

This is the second plan-test defect this phase (53-02's mutation (a) was the first), both surfaced by
actually running the mutations rather than assuming them.

## Verification (run by the orchestrator, unsandboxed)

- `uv run pytest -q` — **1071 passed** (the executor saw 1070 + 1 skipped; the skip was
  `git worktree add`, unavailable in its sandbox, and it runs here)
- `uv run python -m tools.ruff_baseline` — `67 findings (baseline 67) / PASS`
- `uv run python -m tools.contract_drift.drift` — exit 0
- `git diff --quiet -- contracts/` — clean; `find contracts -name '*.schema.json' | wc -l` — `6`
- Scope-cut guard: `grep -rn "conflicts.json\|source_sha256" tools/adoption_apply/ tools/adoption_scan/`
  — **no matches**; `_spliced_project_toml` defined once, called from exactly two sites

## Self-Check: PASSED

Plan 04 is unblocked: the full re-run cycle is wired and its no-op is proven stable rather than
assumed.
