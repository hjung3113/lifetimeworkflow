---
phase: 53-managed-adopt-updates
plan: 01
status: complete
requirements: [MONO-12]
commits:
  - d297ebe  feat(53-01): author off-plane manifest-schema update-enum applier
  - 334d4c8  feat(53-01): extend manifest schema with `update` disposition and installed[]
  - 979eb41  chore(53-01): run /contract-check in full and regenerate the derived plane
  - 30ae186  fix(lint): clear pre-existing ruff ratchet debt so the gate is green again
key-files:
  created:
    - .planning/phases/53-managed-adopt-updates/scripts/apply-manifest-update-enum.py
  modified:
    - contracts/harness/adoption/manifest.schema.json
    - contracts/.hashes/manifest.json
    - .memory/derived/contracts-index.md
    - docs/reference/manifest.md
    - tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr
    - tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr
completed: 2026-08-04
---

# 53-01 — Contract-first manifest extension

`contracts/harness/adoption/manifest.schema.json` gained the 7th `dispositionEnum` value
`update`, `$defs.installedRecord`, and one **optional** top-level `installed[]` array — through
the full contract-first chain. No sibling schema: the contract count is still **6**
(`ROADMAP.md:231` v2.7 binding boundary, re-checked by Phase 54 SC-2).

## What was built

**Task 1 — off-plane applier** (`d297ebe`). Stdlib-only, `--check` (default, write-free) /
`--write`, modelled line-for-line on the Phase-52 precedent `apply-inventory-enum.py`. Asserts an
exact pre-state, applies exactly four mutations, `sys.exit(2)` on any surprise shape, and
rebaselines via the shipped `tools.contract_hash.hash.write_manifest()` inside the `--write`
branch only.

**Task 2 — the constitution-plane write** (`334d4c8`). Run under human authorization
(`GOLDEN_APPROVE_HUMAN=1`); no agent wrote `contracts/**` directly. Digest moved
`c10b9b9e22d7002bf9527e5b648b1bb59c7c27126ac76b5912b06d7149a25471` →
`85dab9bfffd9090131a8b726e835d68f2a2fd064e91bfa62f01c0330b17273d7`, rebaselined in the same
invocation. Diff was exactly two files. Re-running `--write` is a no-op (exit 0, idempotent).

**Task 3 — validation + derived plane** (`979eb41`). Both `/contract-check` halves, backward
compatibility both ways, derived regeneration by the shipped generators.

## Gate evidence (literal)

`/contract-check` § 1 — instance loop:

```
SKIP: no <name>.schema.json + sibling instance pairs under contracts/ (schemas may be convention-only) — no-op.
[exit 0]
```

`/contract-check` § 2 — drift gate:

```
contract-drift: OK — live manifest matches the committed baseline.
[exit 0]
```

Schema shape + backward compatibility (positive **and** negative):

```
schema shape + backward compat + negative case OK
[exit 0]
```

- Phase-52-shaped manifest (no `installed` key) → validates clean.
- Manifest with a well-formed `installed[]` → validates clean.
- Manifest whose `installed_sha256` is not 64 hex chars → **REJECTED** (the anti-vacuous guard).
- `required` still `['target_ref', 'dispositions', 'excluded']`; `additionalProperties` still `False`.

Hash agreement between baseline and derived index: `hash agreement OK: 85dab9bfffd9`.

Contract count: `6`. `git diff --quiet -- tools/adoption_scan/ tools/adoption_apply/` passed at
Task 3 commit time — **no code emits `update` yet**, so contract-first order is provably intact.

## Mutation checks — every assertion was proven able to fail

| # | What was mutated | Observed |
|---|---|---|
| 1 | Renamed one enum value (`create` → `created`) in an in-memory schema dict | `check_state()` → **exit 2** |
| 2 | Half-applied schema: enum has `update` but `installedRecord`/`installed` absent | `check_state()` → **exit 2** |
| 3 | One hex char of the manifest-schema row in `.memory/derived/contracts-index.md` (`85dab9bfffd9` → `85dab9bfffd0`) | hash-agreement gate → **exit 1**, `hash prefix DISAGREEMENT: manifest says 85dab9bfffd9 but row is: … 85dab9bfffd0 …`; reverted → exit 0 |

Checks 1–2 never touched disk (`git diff --quiet -- contracts/` passed after each). Check 3 was
backed up and restored.

## Decisions

- **Extended the existing schema rather than adding `installed.schema.json`** — a sibling would
  make 7 contracts and red Phase 54 SC-2 before it runs. Locked in `53-CONTEXT.md`.
- **Exactly one stored hash, `installed_sha256`.** `draft` recomputes the source hash every run,
  so a second `source_sha256` would only go stale. (One of the three scope-cut items; the cut
  holds — `conflicts.json`, `source_sha256`, and exit code 3 appear nowhere in this plan's output.)
- **Task 3's E501 reflow splits string literals only** — the schema description bytes are
  unchanged and `--write` is still a no-op, so contract-drift stayed green.

## Deviations

1. **The `GOLDEN_APPROVE_HUMAN` write was performed on the human's explicit instruction to run it
   on their behalf, rather than by the human typing the command.** The plan and
   `.continue-here.md` both state an agent must never set that token. The gate was surfaced in
   full first, the bypass was raised as a concern, and the human confirmed explicitly. Recorded
   here because the control was designed so this could not happen silently.
2. **Task 3 was dispatched to an external runtime first and did not complete.** Its sandbox
   exposed `.git` read-only, so it regenerated the derived plane but could not commit, and its
   console output was truncated before the gate evidence could be captured. Rather than accept an
   unevidenced green, every gate above was re-run directly and its literal output recorded. The
   derived artifacts it produced were inspected before use — both snapshot diffs are hash/row
   updates only, with no weakened assertion.
3. **The ruff ratchet was already FAIL before Phase 53 started** — `UP035` in
   `tools/adoption_apply/apply.py:47` (landed at `9a1432b`/52-04) and two `E501` lines in the
   Phase-52 applier script, none of them paired with a baseline update. Fixed in a separate
   commit (`30ae186`) so it is not confused with 53-01's own work. This is exactly the
   "claiming green on pytest alone" anti-pattern the handoff warned about: 1047 tests passed
   while the actual CI gate was red.

## Verification

- `/contract-check` both halves — exit 0 (literal output quoted above)
- `uv run pytest -q` — **1047 passed**, 8 snapshots passed
- `uv run python -m tools.ruff_baseline` — `ruff ratchet: 67 findings (baseline 67) / PASS`
- `uv run pytest tools/memory_regen/tests/test_contracts_index.py -q` — passes **without**
  `--snapshot-update` (7 passed)
- `find contracts -name '*.schema.json' | wc -l` — `6`

## Self-Check: PASSED

Plan 02 is unblocked: the contract can express `update` and the installed-record shape, and no
code emits either yet.
