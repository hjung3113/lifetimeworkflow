# Landing instructions — phase 30-01 deny-domain registry

**This is a constitution-plane change and it requires your own hands.** Writes under `contracts/**`
are DENIED to an agent by `tools/hooks/contract_guard.py` (`CONSTITUTION_GLOBS`, line 53). The two
files below were drafted, validated, and left outside `contracts/`. Nothing in this directory has
been written into `contracts/`, no `GOLDEN_APPROVE_HUMAN` or `HARNESS_DEV_BYPASS` was set, and
nothing was committed.

## 1. Destinations

| Draft (this directory) | Destination |
|---|---|
| `deny-domains.schema.json` | `contracts/harness/security/deny-domains.schema.json` |
| `deny-domains.json` | `contracts/harness/security/deny-domains.json` |

`contracts/harness/security/` does not exist yet — the copy step creates it.

## 2. Landing sequence

Run from the repo root. Everything through step 8 must land as **one commit**: a half-landed state
reds the `drift` job (`.github/workflows/ci.yml:133`) or `stale-derived` (`ci.yml:227`).

```sh
D=.planning/phases/30-deny-domain-registry-v2-4-a/drafts

# 1. Place the pair (your hands — the agent write path is denied here).
mkdir -p contracts/harness/security
cp "$D/deny-domains.schema.json" contracts/harness/security/deny-domains.schema.json
cp "$D/deny-domains.json"        contracts/harness/security/deny-domains.json

# 2. Register the INSTANCE as a data contract. The .schema.json half is auto-globbed by
#    SCHEMA_GLOB; the .json instance is not, so without this the drift gate never sees it.
#    Edit tools/contract_hash/hash.py:30-33 so DATA_CONTRACT_PATHS reads:
#
#        DATA_CONTRACT_PATHS = (
#            Path("harness/task-control/transitions.json"),
#            Path("harness/task-control/gate-registry.json"),
#            Path("harness/security/deny-domains.json"),
#        )
#
#    Do NOT edit tools/contract_hash/tests/test_hash.py — hash.py:58 only counts entries that
#    exist under the tmp tree, so a third entry leaves that assertion green.

# 3. Rebaseline the RFC 8785 hash manifest — by the tool, never by hand.
uv run python -m tools.contract_hash.hash --write
git diff --stat contracts/.hashes/manifest.json     # expect exactly TWO added entries, none moved

# 4. Drift gate.
uv run python -m tools.contract_drift.drift          # exit 0

# 5. The CI contract-check pairing, run locally first.
uv run check-jsonschema \
  --schemafile contracts/harness/security/deny-domains.schema.json \
  contracts/harness/security/deny-domains.json

# 6. Derived reference page (machine-owned; never hand-edit the result).
uv run python -m tools.docs_sync                     # creates docs/reference/deny-domains.md

# 7. Derived contracts index.
uv run python -m tools.memory_regen.contracts_index  # two new rows, kind `other`, owner `TBD`

# 8. BOTH syrupy snapshots move — regenerate, never hand-edit .ambr.
uv run pytest tools/memory_regen/tests/test_contracts_index.py \
              tools/docs_sync/tests/test_docs_sync_determinism.py -q --snapshot-update
uv run pytest tools/memory_regen tools/docs_sync tools/contract_hash tools/contract_drift -q
```

## 3. What each generated artifact should change

| Artifact | Expected change |
|---|---|
| `contracts/.hashes/manifest.json` | exactly two ADDED entries (schema + instance); no existing hash moves |
| `docs/reference/deny-domains.md` | new file, first line is the `docs_sync` DERIVED header |
| `.memory/derived/contracts-index.md` | two new rows, kind `other`, owner `TBD` (do NOT add a `KIND` entry to prettify it) |
| `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr` | regenerated to match the two new rows |
| `tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr` | regenerated — the snapshot renders every real `*.schema.json`, so a new schema moves it |
| CI `contract-check` (`ci.yml:108-127`) | its VISIBLE SKIP line (`ci.yml:121-123`) disappears; a real `check-jsonschema` line replaces it. This is the first `<base>.schema.json` + `<base>.json` pair in the repo — intended, not a regression |

**Nine files, not seven.** `30-01-PLAN.md`'s `files_modified` omits
`tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr` — see the discrepancy list
below — so the plan's "`git status --porcelain` shows exactly the seven files" criterion should be
read as eight (seven + that snapshot). `tools/adoption_scan/tests/__snapshots__/test_snapshots.ambr`
is NOT affected: that test builds its manifest over a hand-listed fixed catalog (CR-02), not the
live `destination_catalog()`.

## 4. Review checklist before you commit

1. `git diff --cached --stat` — the eight files above and nothing else. In particular no
   `tools/hooks/**` (this phase edits no hook) and no `tools/contract_hash/tests/**`.
2. Compare by eye against the live constants:
   `contract_guard.py:53` ↔ the `constitution` globs; `secret_scan.py:37` ↔ the `secret` globs;
   `ledger_guard.py:48` ↔ the `review-ledger` globs.
3. `bypasses` is `[]` for BOTH `secret` and `review-ledger`, and the key is PRESENT.
4. Every domain's `uncovered_tool_surfaces` contains `"Bash"`.
5. Three separate records with three separate `owner_constant`s; the `_note` states the hooks stay
   the source of truth and that no hook imports this file.
6. No timestamp, no reviewer identity, no model identifier.
7. `grep -rn "deny.domains" tools/hooks/` returns nothing.

## 5. One acceptance criterion in the plan cannot pass as written

`30-01-PLAN.md:271` asks that `grep -rniE 'claude|gpt|opus|sonnet|anthropic' contracts/harness/security/`
return nothing. It cannot: the same plan (§1a) requires the `runtime` enum
`["claude","opencode"]`, and the Claude-side `runtime_adapters` entry names `.claude/settings.json`.
A **runtime** name is not a model identifier. Use a model-identifier-specific grep instead:

```sh
grep -rniE 'gpt|opus|sonnet|haiku|anthropic|claude-[0-9]' contracts/harness/security/   # empty
```

Run against the drafts, that returns nothing.
