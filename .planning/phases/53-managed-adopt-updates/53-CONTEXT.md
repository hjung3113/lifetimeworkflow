# Phase 53: Managed Adopt Updates - Context

**Gathered:** 2026-08-01
**Status:** Ready for planning
**Mode:** Smart discuss (autonomous) — 4 grey areas, all accepted as recommended

<domain>
## Phase Boundary

Re-running `/adopt` against an already-adopted target manages the files it previously installed
instead of reinstalling or blanket-conflicting them. Delivers three observable behaviors
(MONO-12, carried from v2.6 phase 50b where it was BLOCKED on the absence of a real
multi-package target — Phases 51/52 have since supplied one):

1. A durable record naming **every file `/adopt` manages** in a given target.
2. A re-run that **updates** managed files whose harness-source content changed, and is an
   **observable no-op** when neither source nor target has changed.
3. A **target-side divergence** in a managed file produces a **conflict report** and leaves that
   file **byte-unchanged**.

**NOT this phase:** removing installed files (uninstall/prune), interactive conflict resolution
or merge assistance, adopting a second target, any new command/skill/sub-verb (NG-01 — Phase 54
is a surface-*shrink* phase), and the deferred B-model gRPC boundary.

</domain>

<decisions>
## Implementation Decisions

### Managed-file record (SC-1)

- The record of adopt-managed files lives **in the target tree** at
  `.harness/adoption/installed.json`. A re-run happens from a fresh batch directory in a new
  session, so the task-local batch dir under `.workflow/tasks/**` cannot carry it; the target is
  the only durable anchor.
- **[SUPERSEDED 2026-08-01]** ~~Its contract is a **new sibling schema**,
  `contracts/harness/adoption/installed.schema.json`.~~ The stated rationale — "leaves the
  drafted-manifest contract's RFC 8785 hash untouched" — is **void**: Area 2's `update` enum
  value changes that hash regardless, so separation bought nothing.
- **Its contract EXTENDS the existing `contracts/harness/adoption/manifest.schema.json`** with
  ONE new **optional** top-level array, `installed[]`. No new contract file is created.
  **Why:** `.planning/ROADMAP.md:229` binds the whole v2.7 milestone to "contracts 6 … do not
  increase", and Phase 54's SC-2 (`ROADMAP.md:313`) re-checks "no greater than … 6 contracts".
  A sibling schema would make 7 and red Phase 54 before it runs. Retiring
  `contracts/sample/greeting.schema.json` to make room was priced and rejected — it is
  load-bearing across ~10 test modules and fixture trees.
- Each managed entry records exactly: `destination`, `installed_sha256` (the bytes **as actually
  written**, post-splice), and `batch_id`.
  **[SCOPE-CUT 2026-08-01]** An earlier draft of this decision also stored `source_sha256`.
  Dropped as unnecessary: `draft` already recomputes the harness source hash every run
  (`destinations.harness_proposed_hashes()`) and already reconstructs the full payload including
  the derived splice, so "did the source move?" is answered by comparing the **recomputed
  payload hash** against the recorded `installed_sha256`. Storing a second hash adds a field
  that can go stale and answers nothing the recomputation does not. One stored hash.
- The `contracts/` edit (one file: the enum value plus the one optional array) is
  **constitution-plane** and therefore human-gated: prepare an **off-plane script** carrying the
  exact content and let the human run it. Never write `contracts/` or `docs/adr/` directly —
  `contract_guard` refuses it, and the repo's established pattern is script-then-human-runs.

### Re-run semantics (SC-2)

- "Update" is expressed as a **7th `dispositionEnum` value, `update`**, fired when the target's
  current hash **equals** the recorded `installed_sha256` **and** the recomputed harness payload
  hash now differs. Reusing `create` with replace semantics was rejected: it would destroy `apply.py`'s
  "never silently overwrite" invariant (`atomic_create`'s `os.link` collision check), which is
  the module's core safety property. This is a manifest-contract change and carries a paired
  golden update through the contract-drift gate.
- A no-op re-run is **observable**: zero bytes written into the target, proven by a before/after
  tree hash of the target (the Phase-52 `scripts/compare-worktree-writes.py` idiom, D-21), plus
  a summary line of the shape `applied=0 updated=0 unchanged=N conflicts=0`. A log-only claim
  is not acceptable evidence.
- A no-op **does not rewrite** `installed.json`. The record is content-derived only — **no
  timestamps, no run counters**. A `last_run_at` field would make the no-op unobservable by
  construction, defeating SC-2's own criterion.
- `harness/project.toml`'s derived-`[[languages]]` splice records its **post-splice bytes** as
  `installed_sha256`. WR-08 (52-REVIEW.md — the permanently-`conflict` project.toml, explicitly
  deferred to this phase) therefore dies as a side effect rather than needing separate work.

### Divergence & conflict report (SC-3)

- Divergence test: `sha256(target file) != recorded installed_sha256` → a **target-side edit** →
  disposition `conflict`, and the file is left **byte-unchanged**. Comparing against the source
  hash instead cannot tell who changed what and was rejected.
- **The conflict report is the drafted `manifest.json` itself** — it already carries a
  `disposition: "conflict"` row per diverged destination, is already schema-validated, and is
  already written batch-locally under `refuse_if_outside_root`. Apply adds a **stderr summary**
  naming each diverged destination with its recorded and current hash.
  **[SCOPE-CUT 2026-08-01]** An earlier draft added a separate `conflicts.json` artifact and a
  `conflicts[]` contract array. Dropped: it restates what `dispositions[]` already says, and
  MONO-12 SC-3 asks for "a conflict report", which the manifest is. No new file, no second
  contract array.
- **[SCOPE-CUT 2026-08-01]** An earlier draft assigned conflicts a **distinct exit code 3**.
  Dropped: no MONO-12 success criterion mentions exit codes, and no caller reads adoption-apply's
  exit code by number today. Existing 0/1/2 semantics stay untouched. Revisit only if a real CI
  gate needs it.
- A conflict **never aborts** the run. All safe rows keep applying; conflicts accumulate and are
  reported at the end.

### Proof & surface budget

- Proof level: **fixture tests covering all three success criteria**, plus **one real re-run**
  against a freshly provisioned FeedbackOps worktree — matching the Phase 51/52 evidence
  discipline (real-target observation before the claim is trusted).
- **No new commands or skills.** `/adopt apply` gains behavior in place. NG-01 holds and
  Phase 54 (Surface Budget Closeout) must not inherit new surface from this phase.
- `.harness/adoption/installed.json` is **not** a destination-catalog row — it is adopt's own
  bookkeeping and is excluded structurally, in the same spirit as `.workflow/tasks/**`. A
  self-referential disposition on the record would be incoherent.
- Every new or edited assertion is **mutation-tested** (break the logic, confirm the test reds).
  This repo's signature defect is checks that cannot fail; new gate assertions are exactly where
  it recurs.

### Claude's Discretion

- Exact module placement of the record reader/writer (new `tools/adoption_apply/installed.py`
  vs. extending `apply.py`), the internal function signatures, and the exact wording of the
  stderr conflict summary.
- Plan decomposition and commit granularity, subject to the constitution-plane script gate above
  landing before any code that depends on the new enum value.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- `tools/adoption_scan/destinations.py::disposition()` — the total, ordered 7-step rule chain
  (gsd-owned → constitution → derived → marker-capable → create → preserve → conflict). The
  `update` branch inserts between steps 6 and 7, and the existing `existing_sha` hint parameter
  (WR-03) is already the seam for feeding it a recorded hash.
- `tools/adoption_scan/destinations.py::harness_proposed_hashes()` — already produces
  `{destination: source_sha256}` from the harness checkout, independent of the target (CR-01).
  This is what makes storing a second hash unnecessary — the source side is recomputed every
  run, so only the installed side needs to be remembered.
- `tools/adoption_apply/apply.py::atomic_create` / `_atomic_replace` — the two durable-write
  idioms (mkstemp in-dir → write/flush/fsync → link-or-replace → dir fsync). An `update`
  disposition uses `_atomic_replace`; `create` keeps the collision-checking `os.link` path.
- `tools/adoption_apply/apply.py::refuse_unsafe_destination` — the single choke point for
  constitution/confinement/directory-shape refusal. Every new write path routes through it
  unchanged; do not add a second gate.
- `tools/adoption_apply/batch.py` — task-local batch layout, content-derived `batch_id`, and the
  CAS-guarded `update_status` idiom (`fcntl.flock` + revision check). `batch_id` is the field
  the installed record cites.
- `tools/adoption_apply/cli.py::_validate` / `_load_schema` — the Draft 2020-12 validation
  helper the new `installed`/`conflicts` documents reuse verbatim.
- `examples`/Phase-52 `scripts/compare-worktree-writes.py` (D-21) — the before/after target-tree
  comparison that supplies SC-2's no-op proof and SC-3's byte-unchanged proof.

### Established Patterns

- **Contract-first**: `contracts/` is the single source of truth; the RFC 8785 canonical hash
  gate (`tools/contract_drift`) reds on a schema change without a paired golden update. The
  enum change must land with its golden.
- **Refuse, don't guess**: `harness_proposed_hash()` returns `None` when the harness has no
  template at a destination, and `None` can never equal a real sha256, forcing the safe
  `conflict` outcome. The `update` branch must preserve this property — a missing recorded hash
  must never resolve to `update`.
- **Two-plane memory**: `contracts/`, `docs/adr/`, `golden/` are human-gated; derived artifacts
  are regenerated, never hand-edited.
- **Never re-derive shared data**: `CONSTITUTION_GLOBS`, `MARKER_CAPABLE`, `DISPOSITION_ENUM`,
  `is_gsd_owned` are imported from their one authoritative module, never retyped.

### Integration Points

- `contracts/harness/adoption/manifest.schema.json` — `$defs.dispositionEnum` gains `update`.
  Its docstring's "exactly these 6 values" wording, and
  `tools/adoption_scan/tests/test_dispositions.py::test_total`, both need the paired change.
- `tools/adoption_scan/destinations.py` — `DISPOSITION_ENUM` tuple and `disposition()`'s chain.
- `tools/adoption_apply/apply.py` — `apply_disposition`'s branch table (currently total over 6
  values, falling through to `skipped`) and `apply_manifest`'s summary buckets, which gain
  `updated` and `conflicts`.
- `tools/adoption_apply/cli.py::_cmd_apply` — reads the target's installed record before
  applying, writes it after, and prints the stderr conflict summary. Exit codes unchanged.
- `harness/commands/adopt.md` and the `brownfield-adoption` skill — documentation only; the
  re-run-is-update behavior must be described without adding a sub-verb.

</code_context>

<specifics>
## Specific Ideas

- 52-CONTEXT/52-REVIEW's **WR-08** is a written, dated hand-off to this phase: the applied
  `harness/project.toml` bytes are `harness_payload + b"\n" + sidecar_bytes`, so
  `sha256(existing) != proposed_sha` forever, `preserve` can never fire again, and nothing
  records that the divergence is harness-derived rather than a human edit. Recording
  `installed_sha256` as the post-splice bytes is the named fix.
- 52-CONTEXT/52-REVIEW's **WR-07** is the adjacent symptom: `payloads` is populated only for
  `create` dispositions, so on any re-adoption the derived languages sidecar is silently ignored
  (currently it prints a warning). The `update` path must carry the splice too, or the warning
  becomes permanent.
- MONO-12's three success criteria are **unchanged from v2.6 phase 50b**. What was missing then
  was a real multi-package target, not code — Phases 51/52 supplied it, so the criteria are met
  against reality this time, not a fixture alone.

</specifics>

<deferred>
## Deferred Ideas

- **Uninstall / prune** — removing a managed file that has dropped out of the harness catalog.
  Real, but a separate verb and separate risk profile; not required by MONO-12.
- **Interactive conflict resolution / three-way merge assistance** — the phase reports conflicts
  and stops there by design.
- **Lock-sidecar staleness probe** — recorded owner pid + liveness, or mtime vs. run start.
  Explicitly unbuilt in Phase 52 (NG-01: no observation behind it); still no observation.
- **Multi-target adoption bookkeeping** — one record per target only.

</deferred>
