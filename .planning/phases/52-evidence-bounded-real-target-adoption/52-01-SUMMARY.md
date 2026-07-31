---
phase: 52-evidence-bounded-real-target-adoption
plan: 01
subsystem: infra
tags: [json-schema, contract-drift, rfc8785, constitution-plane, derived-plane, syrupy]

# Dependency graph
requires: []
provides:
  - "excludedEntry.excluded enum on contracts/harness/adoption/inventory.schema.json now carries `non-workspace-member` (9th value, additive, non-breaking)"
  - "Re-derived contracts/.hashes/manifest.json baseline for the changed schema"
  - "Regenerated derived plane (.memory/derived/contracts-index.md, docs/reference/inventory.md, the contracts-index syrupy snapshot) carrying the new hash"
  - "Idempotent human-run off-plane applier script proving the constitution-plane write was human-authorized, not agent-written"
affects: [52-02]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Off-plane applier script pattern for constitution-plane edits: --check (write-free, asserts exact pre/post shape, exit 2 on surprise) / --write (edit + rebaseline in one invocation), human-run under GOLDEN_APPROVE_HUMAN"

key-files:
  created:
    - .planning/phases/52-evidence-bounded-real-target-adoption/scripts/apply-inventory-enum.py
  modified:
    - contracts/harness/adoption/inventory.schema.json
    - contracts/.hashes/manifest.json
    - .memory/derived/contracts-index.md
    - tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr

key-decisions:
  - "The human applied the constitution-plane edit as a targeted text edit rather than running the shipped applier's --write mode, because the applier's json.dump(indent=2) round-trip reformatted the entire file (119 insertions / 34 deletions) around a 4-line semantic change — defeating the human-reviewability purpose of the CODEOWNERS gate. The resulting RFC 8785 canonical digest (688b75206df6…) is byte-identical to what the applier would have produced, independently confirming JCS canonicalization is formatting-independent."
  - "docs/reference/inventory.md is unchanged after tools.docs_sync regeneration — the rendered reference table lists only top-level schema properties, not the nested $defs.excludedEntry.excluded enum, so there is no content delta to commit for that file on this change."

requirements-completed: [RTA-02]

# Metrics
duration: ~4min active work (plus a human-checkpoint pause between Task 1 and Task 3 while the constitution-plane write was reviewed and applied)
completed: 2026-08-01
---

# Phase 52 Plan 01: Evidence-Bounded Real-Target Adoption — Inventory Enum Contract Change Summary

**Additive `non-workspace-member` value landed on `inventory.schema.json`'s `excludedEntry.excluded` enum through the full contract-first chain — human-authorized write, re-derived RFC 8785 hash baseline, regenerated derived plane, whole suite green — with no emitter code touched yet.**

## Performance

- **Tasks:** 3/3 completed (including the mandatory `checkpoint:human-action` at Task 2)
- **Files modified:** 5 (1 created, 4 modified)

## Accomplishments

- `contracts/harness/adoption/inventory.schema.json`'s `$defs.excludedEntry.properties.excluded.enum` now carries 9 values (was 8), the new one being `non-workspace-member`, with its `description` extended by an OBS-D-01/D-20 trace sentence.
- `contracts/.hashes/manifest.json` re-derived in the same authorized action: `inventory.schema.json` digest moved `34a31944180f766e…4531` → `688b75206df61d4b94ab071c1d1ec2ad686d4e434e33eca99774684050302396`.
- `/contract-check` ran in full (both halves), evidence quoted verbatim below.
- Every derived artifact carrying the old hash prefix was regenerated: `.memory/derived/contracts-index.md` (prefix `34a31944180f` → `688b75206df6`), the contracts-index syrupy snapshot (`test_render_matches_committed_snapshot` green again without `--snapshot-update`), and `docs/reference/inventory.md` (regenerated, content unchanged — see Decisions).
- Contract count held at exactly 6 (NG-01); `tools/adoption_scan/**` untouched (no emitter smuggled in); full suite green.

## Task Commits

Each task was committed atomically:

1. **Task 1: Author the idempotent off-plane enum applier and prove it is a no-op today** — `edf7380` (feat) — `.planning/phases/52-evidence-bounded-real-target-adoption/scripts/apply-inventory-enum.py`
2. **Task 2: Human runs the constitution-plane write** — `6924c1b` (feat, human-authored commit under `GOLDEN_APPROVE_HUMAN`) — `contracts/harness/adoption/inventory.schema.json`, `contracts/.hashes/manifest.json`
3. **Task 3: Run /contract-check, then regenerate every derived artifact carrying the old hash** — `2d84709` (chore) — `.memory/derived/contracts-index.md`, `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr`

## /contract-check evidence (D-20 gate, quoted verbatim)

**§1 — check-jsonschema instance loop** (`harness/commands/contract-check.md` §1), run repo-wide:

```
SKIP: no schema+instance pairs — no-op.
```

This is the documented no-op path, not an omission: no schema anywhere in `contracts/` (including `inventory.schema.json`) currently has a sibling `.yaml`/`.yml`/`.json` instance file. The loop ran; the SKIP is its result.

**§2 — drift gate:**

```
contract-drift: OK — live manifest matches the committed baseline.
```

Exit 0, run both immediately after Task 2 landed and again after the derived-plane regeneration in Task 3.

**Hash-prefix agreement (machine-checked, not just "stale prefix absent"):**

```
hash agreement OK: 688b75206df6
```

`contracts/.hashes/manifest.json["contracts/harness/adoption/inventory.schema.json"][:12]` == the `contracts-index.md` row prefix for that schema — asserted equal, not merely that the old `34a31944180f` is gone.

**Full suite:** `uv run pytest -q` → `981 passed, 8 snapshots passed` (0 failures).

## Files Created/Modified
- `.planning/phases/52-evidence-bounded-real-target-adoption/scripts/apply-inventory-enum.py` - idempotent human-run applier; `--check` write-free, `--write` applies the edit + rebaselines via `tools.contract_hash.hash`
- `contracts/harness/adoption/inventory.schema.json` - `excludedEntry.excluded` enum gains `non-workspace-member`; description extended
- `contracts/.hashes/manifest.json` - inventory.schema.json digest re-derived
- `.memory/derived/contracts-index.md` - regenerated (new hash prefix)
- `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr` - syrupy snapshot updated to match

## Decisions Made

1. **Human applied the write as a targeted text edit, not the applier's `--write`.** See `key-decisions` above and the Deviations section below — this is the load-bearing decision of this plan.
2. **`docs/reference/inventory.md` needed no content change.** `tools.docs_sync` renders only the schema's top-level property table; the changed enum lives inside a nested `$defs` subschema the renderer doesn't drill into. Regenerating produced byte-identical output, so nothing was staged for that file.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Applier's `json.dump(indent=2)` round-trip reformatted the whole constitution-plane file instead of touching only the semantic change**
- **Found during:** Task 2 (the human-run constitution-plane write)
- **Issue:** `apply-inventory-enum.py --write` loads the schema with `json.loads`, mutates the enum + description, and re-serializes with `json.dumps(..., indent=2, ensure_ascii=False)`. Even though the plan asked for this to "preserve the file's existing formatting byte-for-byte outside the two edited spots," a full parse/re-serialize round-trip does not reliably reproduce arbitrary pre-existing JSON formatting (key insertion order aside, whitespace/line-wrapping choices in the original file are not guaranteed to match `json.dumps`'s own idiom). Applying it against the real file produced a 119-insertion/34-deletion diff on a CODEOWNERS-gated file whose true semantic change is 4 lines — which would make human review of the gated diff materially harder, undermining the reason the gate exists.
- **Fix:** The human did not run the script's `--write` mode against the real file. Instead they applied the same edit as a targeted text edit (anchored on exactly-one-occurrence assertions: locate the enum array, insert the new literal before its closing bracket; locate the description string, append the trace sentence), verified with a `json.loads` shape/parse check before writing, then ran `tools.contract_hash.hash --write` to rebaseline exactly as the script would have. The resulting canonical (RFC 8785) digest is byte-identical to what the script's `--write` mode produces (`688b75206df6…`), confirming the semantic content is identical and the only difference was incidental formatting.
- **Files modified:** `contracts/harness/adoption/inventory.schema.json`, `contracts/.hashes/manifest.json` (both via the human's commit `6924c1b`, not via an agent tool call — the applier script itself is unmodified and still reflects the plan's literal spec).
- **Verification:** `python -c "import json;json.load(open('contracts/harness/adoption/inventory.schema.json'))"` succeeds; `tools.contract_drift.drift` exits 0 against the new baseline; digest cross-checked against the applier's own `schema_hash()` output for the pre-existing 9-value enum shape.
- **Committed in:** `6924c1b` (human commit)

**Latent defect recorded for future off-plane appliers (not fixed in this plan — no further constitution-plane write is scheduled):** a `json.load` → `json.dump(indent=N)` round-trip is unsafe as a *diff-minimizing* strategy for CODEOWNERS-gated files, even though it is safe for *canonical-hash* purposes (RFC 8785 is formatting-independent by construction). Any future applier targeting a human-gated file should perform a **format-preserving targeted text edit** (anchored, exactly-one-occurrence assertions on the substring to change) rather than a full parse/re-serialize, so the gated diff a human reviews carries only the semantic change.

---

**Total deviations:** 1 auto-fixed-in-spirit (the human substituted a safer write mechanism than the applier's own `--write` path when applying it for real; the applier script itself was not edited and remains available for future runs where its reformat behavior is acceptable or where the file has no prior formatting to preserve).
**Impact on plan:** No scope creep. The substitution improved reviewability of a CODEOWNERS-gated diff without changing the semantic outcome (byte-identical canonical hash). Recorded as a latent defect in the applier for future off-plane-applier authors.

## Issues Encountered

None beyond the applier reformat deviation above. The RED-by-construction window between Task 2 and Task 3 (the syrupy snapshot embedding the stale hash prefix) behaved exactly as `52-01-PLAN.md`'s `<parallel_execution_note>` predicted: `test_render_matches_committed_snapshot` failed with the expected `34a31944180f` → `688b75206df6` diff, and `--snapshot-update` closed it cleanly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 52-02 (OBS-D-01's `tools/adoption_scan/detect.py` repair) is unblocked: the contract can now express `non-workspace-member`, so the emitter is free to land without turning any artifact-conformance test red.
- Wave 1 is complete (this plan was alone in it); wave 2 plans may now start.

---
*Phase: 52-evidence-bounded-real-target-adoption*
*Completed: 2026-08-01*
