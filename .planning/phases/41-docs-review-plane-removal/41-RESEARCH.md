# Phase 41: Docs-Review Plane Removal - Research

**Researched:** 2026-07-27
**Domain:** Pure deletion — removing a self-verification plane (registry + guard + hook + CI job + emitted surfaces) from a contract-first polyglot harness
**Confidence:** HIGH (every claim below was verified against the tree at `/Users/hyojung/Desktop/2026/lifetimeworkflow` on 2026-07-27; no external libraries or alternatives are in scope)

## Summary

This is a subtractive-only phase: nothing is built, nothing is replaced. The plane being removed
has five parts — a data registry (`docs/doc-dependencies.toml`, 8 bindings), a human-authored
ledger (`docs/.docs-review-ledger.toml`), a Python guard package (`tools/docs_guard/`, verified
**6110 LOC** including its 8 test modules), a PreToolUse hook (`tools/hooks/ledger_guard.py` +
its opencode twin `harness/plugins/ledger-guard.ts`), and a CI job (`docs-guard`,
`.github/workflows/ci.yml:341-351`) wired into the fan-in `gate.needs` (`:381`, currently 12
entries). CONTEXT.md's D-01..D-17 already lock scope and ordering; this research's job is to
verify every path still exists where the ROADMAP says it does, and — more importantly — to widen
the import/consumer graph beyond the CONTEXT.md-named list, because two consumers were found
during this research that are **not named anywhere in CONTEXT.md, ROADMAP.md, or ADR-0012**, and
both will break at import time or drift silently if not touched in this phase.

**The two undocumented landmines, in order of severity:**

1. `tools/adoption_apply/apply.py:65` does `from tools.hooks.ledger_guard import
   REVIEW_LEDGER_GLOBS` at **module import time**, and defines a public `ReviewLedgerRefusal`
   exception class (`:72-79`) plus a ledger-glob check inside `refuse_unsafe_destination`
   (`:227-232`) and a catch clause in `apply_manifest` (`:453`). Deleting
   `tools/hooks/ledger_guard.py` without editing `apply.py` breaks `tools.adoption_apply` at
   import — which cascades into every test that imports it, and into `/adopt`.
2. `tools/adoption_apply/tests/test_constitution_refusal.py` contains an entire parametrized test
   class (`REVIEW_LEDGER_DESTINATIONS`, `LEDGER_ADJACENT_ALLOWED`, ~120 lines) that imports
   `tools.hooks.ledger_guard` directly (for `ledger_guard.decide(...)`) and asserts
   `apply.ReviewLedgerRefusal` behavior. This is a **different file** from the one CONTEXT.md
   already names (`test_docs_binding_proposal.py`) and is not mentioned anywhere in the phase's
   scope documents.

A third, quieter finding: the emitted `ledger_guard` PreToolUse hook group in `.claude/settings.json`
is **not** projected from a `harness/` source file the way commands/skills are (glob discovery) —
it is a hand-maintained Python literal inside `tools/harness_emit/merge.py`
(`HARNESS_SIGNATURES` tuple at `:88` and the hook-group dict at `:172-183`). Re-emitting after
deleting `harness/plugins/ledger-guard.ts` will **not** remove this group on its own; `merge.py`
itself must be edited.

**Primary recommendation:** treat this as a two-track deletion — (a) the CONTEXT.md-enumerated
plane (registry, ledger, guard, hook, command, skill, contracts, staleness queue, CI job), and (b)
the newly-found `adoption_apply` consumer edit (apply.py + test_constitution_refusal.py) and the
`merge.py` hand-maintained signature/dict edit — both are load-bearing, both are required for the
suite to go green, and neither expands scope: they are edits to code that *references* the deleted
surface, not new capability.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Docs-review registry/ledger removal | Constitution-adjacent data (`docs/`, `contracts/harness/docs/`) | — | Pure data/schema deletion; no runtime tier distinction applies (this is a dev-tooling repo, not a deployed app) |
| Guard package removal (`tools/docs_guard`) | Dev-tooling / CI (Python package) | — | Runs only in CI and local `uv run` invocations, never shipped to a product install |
| Hook removal (`ledger_guard` + `ledger-guard.ts`) | Claude Code runtime (PreToolUse) / opencode runtime (plugin) | Emitter (`tools/harness_emit/merge.py`) | Dual-runtime enforcement surface; the emitter is a THIRD tier that must also be edited because it hardcodes the hook wiring rather than deriving it |
| CI job + fan-in removal | CI / GitHub Actions | — | `.github/workflows/ci.yml` only; no application-tier effect |
| `adoption_apply` consumer edit | Dev-tooling (Python package, `tools/adoption_apply`) | — | Consumes `ledger_guard` as a library import, not via the hook path — a fourth, previously-undocumented tier touched by this deletion |

This phase touches no browser/frontend/API/database tier — it is entirely within the harness's own
dev-tooling and CI-configuration layer.

## Verified Deletion/Edit Inventory

All paths confirmed present on 2026-07-27 unless noted. Counts are `wc -l` / `find` outputs, not
estimates.

### DELETE (whole file/directory)

| Path | Verified state |
|---|---|
| `tools/docs_guard/` (10 non-test files + `tests/` with 9 files, incl. `__init__.py`) | 6110 LOC total across all `.py` files including tests — matches ROADMAP exactly |
| `docs/.docs-review-ledger.toml` | 4998 bytes, 90 lines per CONTEXT.md |
| `docs/doc-dependencies.toml` | 4856 bytes; `grep -c '^\[\[binding\]\]'` = **8** (mechanical count, matches D-09) |
| `docs/reference/doc-dependencies.md` | 1184 bytes, generated page |
| `contracts/harness/docs/doc-dependencies.schema.json` | only file in `contracts/harness/docs/` — directory becomes empty and should be removed too |
| `tools/hooks/ledger_guard.py` | 90 lines |
| `harness/plugins/ledger-guard.ts` | present, opencode adapter, execution-deferred per its own header comment |
| `harness/commands/docs-update.md` | present |
| `harness/skills/docs-upkeep/` (`SKILL.md`) | present |
| `tools/memory_regen/docs_staleness.py` | 233 LOC; imports `tools.docs_guard.guard.{DEFAULT_LEDGER_PATH,REPO_ROOT,classify}` at `:42` and `tools.docs_guard.impact.impact_map` / `tools.docs_guard.registry.DEFAULT_REGISTRY_PATH` at `:43-44` |
| `tools/memory_regen/tests/test_docs_staleness.py` | 273 lines |
| `tools/memory_regen/tests/test_inject_docs_pointer.py` | 186 lines |
| `tools/adoption_apply/tests/test_docs_binding_proposal.py` | present, imports the schema being deleted (`:56,120`) |

### EDIT (surviving file, remove specific content)

| Path | What must change | Evidence |
|---|---|---|
| `docs/doc-dependencies.toml` | remove all 8 `[[binding]]` rows **first** (D-09), before any tool deletion | 8 confirmed |
| `harness/permission-matrix.json` | remove `"docs/.docs-review-ledger.toml"` from `path_deny_globs` (`:34`); rewrite the `_note` prose at `:2` (currently ~1 paragraph describing the ledger as "a THIRD path-deny domain... Note it does NOT cover `docs/doc-dependencies.toml`") | confirmed both hits |
| `tools/harness_emit/merge.py` | remove `"tools.hooks.ledger_guard"` from `HARNESS_SIGNATURES` (`:88`, currently 6 entries) **and** delete the hook-group dict block (`:168-183`, the `{"matcher": "Write|Edit", "hooks": [...ledger_guard...]}` object) — **NOT** a `harness/` source file, hand-maintained Python inside the emitter tool itself | confirmed; comment at `:172` names a test (`test_ledger_guard_is_wired_into_pretooluse`) that does not actually exist under that name anywhere in the repo (grep returns zero hits) — likely a stale/aspirational reference; the real enforcing test is `tools/hooks/tests/test_settings_coexist.py::test_harness_gates_registered_with_expected_matcher` |
| `tools/adoption_apply/apply.py` | **UNDOCUMENTED CONSUMER.** Remove: the `from tools.hooks.ledger_guard import REVIEW_LEDGER_GLOBS` import (`:65`) and its 6-line docstring justification (`:55-63`); the `ReviewLedgerRefusal` exception class (`:72-79`); the ledger-glob check block inside `refuse_unsafe_destination` (`:227-232`, the `if resolve_path(REVIEW_LEDGER_GLOBS, ...) == "deny": raise ReviewLedgerRefusal(...)`); the `ReviewLedgerRefusal` half of the `except (ConstitutionRefusal, ReviewLedgerRefusal):` catch in `apply_manifest` (`:453`, becomes `except ConstitutionRefusal:`) | verified by direct read — this import is at module top-level, so leaving it breaks `import tools.adoption_apply.apply` entirely |
| `tools/adoption_apply/tests/test_constitution_refusal.py` | **UNDOCUMENTED CONSUMER.** Remove the `REVIEW_LEDGER_DESTINATIONS` parametrized list (~13 rows) and `LEDGER_ADJACENT_ALLOWED` list, `test_review_ledger_destination_is_refused`, `test_review_ledger_adjacent_destination_stays_allowed`, and `test_review_ledger_ordinary_tool_path_is_denied_by_a_real_hook` (imports `tools.hooks.ledger_guard` directly, `:...`). Two of the `LEDGER_ADJACENT_ALLOWED` rows (`docs/doc-dependencies.toml`, `docs/reference/doc-dependencies.md`) reference paths this phase also deletes — decide whether the remaining constitution-refusal narrowness tests still need those two paths as negative controls, or whether they can be dropped with the ledger class | verified by direct read; this is a distinct file from the already-named `test_docs_binding_proposal.py` |
| `tools/harness_lint/caps.py` | remove `"docs-upkeep"` from `EXPECTED_SKILLS` (`:151`, currently 18 entries → 17); trim the Phase-29 comment block (`:128-129`) | confirmed |
| `tools/harness_emit/tests/test_coexist.py` | the hardcoded command count **26 → 25** at `:67-68` (`test_all_26_commands_emit_to_both_trees`), plus its docstring's phase-by-phase progression comment (currently ends "...25 → 26" for `/discipline`; needs a `/docs-update` removal line inserted or the count narrative corrected) — also references `ledger-guard.ts`/`docs-upkeep` in its skill-count docstring (`:49`) | confirmed hardcoded `== 26` assertions |
| `tools/hooks/tests/test_settings_coexist.py` | remove the `("PreToolUse", "tools.hooks.ledger_guard", "Write|Edit")` row from `_NEW_GATES` (`:87-88`) | confirmed |
| `tools/harness_lint/tests/test_docs_update_wiring.py` | **whole file dies** (per ordering rule 8: a deleted `harness/` artifact's dedicated gate test dies in the same commit) — this is the DOCSUP-06 structural gate for exactly `harness/commands/docs-update.md` + `harness/skills/docs-upkeep/`, both deleted | confirmed; already named in D-13 |
| `tools/harness_lint/tests/test_tests_are_isolatable.py` | update its docstring example (`:19`, `"pytest tools/docs_guard ..."`) — cosmetic, no assertion logic depends on `docs_guard` existing (verify: no hardcoded path list references it structurally) | confirmed — comment-only per initial grep |
| `tools/docs_sync/tests/test_docs_sync_determinism.py` | remove `"doc-dependencies"` from `EXPECTED_PAGES` frozenset (`:33`, currently 14 entries → 13) | confirmed |
| `tools/harness_lint/tests/test_workspace_member_completeness.py` | **no `docs_guard` hit found** despite CONTEXT.md D-13 naming it — grep returned zero matches in this file. Re-verify at execution time; if the workspace-member-glob test has no docs_guard-specific assertion, it needs no edit and D-13's list is over-broad for this file (harmless to leave named — CI will simply pass unchanged) | **could not verify a required edit; flag for planner** |
| `AGENTS.md:106-107` (command/skill index lines) | **auto-repairs via re-emit — NOT a hand-edit.** These two lines are inside the `<!-- BEGIN HARNESS-MANAGED -->` fence (confirmed: the fence opens at line 104, the Commands/Skills lines are 106-107) that `tools.harness_emit.generate.emit()` splices on every run. D-13 lists this as an edit target; the correct action is "re-emit, do not hand-edit" | confirmed by direct read of `AGENTS.md:99-109` |
| `harness/skills/gate-model/SKILL.md` | trim docs-plane claims only (the skill survives; Phase 44 deletes it whole). Specific lines needing edit: the "review ledger" bullet (`~:43-47`), the `ledger_guard` row in its hook-surface table (`~:56`), and the numbered walkthrough's ledger mention (`~:80`) | confirmed all three locations by direct read |
| `.memory/README.md` | **CONTEXT.md/D-13 names this but no "third path-deny domain" sentence exists in this file** — grep found zero hits for `ledger`, `docs-review`, `docs_guard`, `third`, `domain` in `.memory/README.md`. The sentence CONTEXT.md is describing actually lives in `harness/permission-matrix.json:2` (`_note`) and `harness/skills/gate-model/SKILL.md`, both already listed separately. **This D-13 item appears to be a mis-citation; no `.memory/README.md` edit is needed** | verified — file is 69 lines, read in full, no match |
| `contracts/.hashes/manifest.json` | rebaseline: remove the `"contracts/harness/docs/doc-dependencies.schema.json"` key (line 6, one of the manifest's keys) via `uv run python -m tools.contract_hash.hash --write` (the module's actual CLI flag, confirmed at `tools/contract_hash/hash.py:93` `"--write"` argparse flag) — never hand-edit the JSON | confirmed exact key and CLI flag name |
| `.github/workflows/ci.yml` | delete the `docs-guard` job block (`:317-351`, including its 33-line comment header) and its token in the fan-in `needs:` list (`:381`, currently `[setup, lang-tests, contract-check, drift, golden, core-suite, lint, lifecycle-eval, emit-drift, stale-derived, docs-guard, workspace]` — 12 entries, `docs-guard` is the 11th) | confirmed exact line ranges and full needs list |
| `uv.lock` | remove the `logparser-docs-guard` virtual workspace member — confirmed at `uv.lock:20` (root member list) and `:309-311` (`name = "logparser-docs-guard"`, `source = { virtual = "tools/docs_guard" }`); refresh via `uv sync --all-packages` (Phase 40's exact precedent, `40-01-SUMMARY.md` V-5) | confirmed |

### NOT deleted (verify these survive unchanged)

- `tools/docs_sync/` + `/docs-sync` — a different generator (Diátaxis reference pages), only its
  determinism test's `EXPECTED_PAGES` set is trimmed by one entry (above).
- `docs/adr/0010-human-docs-review-obligation-model.md` — confirmed `Status: superseded by 0012`
  already recorded (Phase 39 landed this) — append-only, do not touch.
- `harness/skills/gate-model/` (the skill itself, trimmed not deleted — Phase 44 deletes it whole).
- `tools/discipline/__main__.py` and `tools/task_control/tests/test_task_control.py` — both contain
  a **prose-only** comment referencing "the `tools.docs_guard` convention" (0/1/3 exit-code
  mapping) as a design precedent. No import, no behavior dependency. Leave untouched; Phase 43
  territory if it ever needs touching.
- `tools/hooks/tests/test_contract_guard.py:330` — a negative-control test row listing
  `"docs/reference/doc-dependencies.md"` as a path that must NOT classify as constitution-plane.
  This is testing `contract_guard`'s classifier logic against a path *string*, not asserting the
  file exists — it remains a valid (if now slightly stale-looking) negative control after the file
  is deleted. Optional cleanup, not required for green.

## Import/Consumer Graph (grepped, classified)

Full sweep command run: `grep -rlE "docs_guard|docs-guard|docs-review-ledger|ledger_guard|docs-upkeep|docs-update|doc-dependencies" tools/ harness/ contracts/ docs/ .github/ .claude/ .opencode/ AGENTS.md .memory/ uv.lock pyproject.toml`

| Hit | Classification |
|---|---|
| `tools/docs_guard/**` (all 10 + 8 test files) | **delete** (the plane itself) |
| `tools/hooks/ledger_guard.py` | **delete** |
| `tools/memory_regen/docs_staleness.py` + 2 test files + `inject.py:82,217` | **delete** (D-03) |
| `tools/adoption_apply/tests/test_docs_binding_proposal.py` | **delete** (D-04, already named) |
| `tools/adoption_apply/apply.py` | **edit — undocumented consumer** (see above) |
| `tools/adoption_apply/tests/test_constitution_refusal.py` | **edit — undocumented consumer** (see above) |
| `harness/commands/docs-update.md`, `harness/skills/docs-upkeep/` | **delete** |
| `harness/plugins/ledger-guard.ts` | **delete** |
| `harness/permission-matrix.json` | **edit** (glob entry + `_note`) |
| `contracts/harness/docs/doc-dependencies.schema.json` | **delete** + rebaseline manifest |
| `docs/.docs-review-ledger.toml`, `docs/doc-dependencies.toml`, `docs/reference/doc-dependencies.md` | **delete** |
| `docs/adr/0010-*.md`, `0011-*.md`, `0012-*.md` | **exempt** (ADRs; 0010 already superseded, 0011/0012 merely cite the plane) |
| `.github/workflows/ci.yml` | **edit** (job + `needs` token) |
| `tools/harness_emit/emit-manifest.json` | **auto-repairs via re-emit** (prune-then-write; do not hand-edit — confirmed by Phase-7/STATE.md precedent) |
| `tools/harness_emit/merge.py` | **edit — hand-maintained emitter code**, not harness/ source (see above) |
| `tools/harness_lint/caps.py` | **edit** (`EXPECTED_SKILLS`) |
| `tools/harness_emit/tests/test_coexist.py` | **edit** (hardcoded command count) |
| `tools/hooks/tests/test_settings_coexist.py` | **edit** (`_NEW_GATES` row) |
| `tools/harness_lint/tests/test_docs_update_wiring.py` | **delete whole file** (ordering rule 8) |
| `tools/harness_lint/tests/test_tests_are_isolatable.py` | **edit, cosmetic** (docstring example) |
| `tools/harness_lint/tests/test_workspace_member_completeness.py` | **no hit found — re-verify, likely no-op** |
| `tools/docs_sync/tests/test_docs_sync_determinism.py` | **edit** (`EXPECTED_PAGES`) |
| `AGENTS.md:106-107` | **auto-repairs via re-emit** |
| `.memory/README.md` | **no hit found — D-13 item appears mis-cited, likely no-op** |
| `.memory/derived/contracts-index.md` | **auto-repairs** (derived plane, regenerated by `tools.memory_regen.contracts_index`, part of `stale-derived` gate) |
| `harness/skills/gate-model/SKILL.md` | **edit** (trim 3 locations, skill survives) |
| `contracts/harness/security/deny-domains.json` + schema + `docs/reference/deny-domains.md` | **out of scope — flagged below** |
| `tools/discipline/__main__.py`, `tools/task_control/tests/test_task_control.py` | **prose-only, exempt** |
| `tools/hooks/tests/test_contract_guard.py:330` | **prose/fixture-only, exempt** (optional cleanup) |
| `tools/harness_lint/workspace_check.py:22` | **prose-only** (docstring lists `ledger_guard` among hooks workspace_check.py protects against workspace-resolution failure cascades — describes general hook category, not a specific dependency; no edit required, this describes a class of hooks generically) |
| `tools/ruff_baseline/__main__.py`, `tools/ruff_baseline/pyproject.toml` | **comment-only mirror, D-13 says may keep or drop, no behavior rides on it** |
| `.claude/agents/gsd-doc-verifier.md`, `gsd-doc-writer.md`, `.claude/commands/gsd/*`, `.claude/get-shit-done/workflows/*`, `.claude/gsd-file-manifest.json` | **exempt — GSD's own surface**, unrelated "docs-update"/"docs" substring hits inside GSD's harness-external workflow tooling, not this repo's docs-review plane |
| `.claude/commands/docs-update.md`, `.claude/skills/docs-upkeep/SKILL.md`, `.opencode/command/docs-update.md`, `.opencode/plugin/ledger-guard.ts`, `.opencode/skill/docs-upkeep/SKILL.md`, `.claude/settings.json` (ledger_guard hook group) | **auto-repair via re-emit** — never hand-edit these trees |

## Out of scope — flagged for a later phase

- **`contracts/harness/security/deny-domains.json`** (Phase 44 / CER-08 territory) contains one
  inventory *record* naming `owner_module: "tools.hooks.ledger_guard"`,
  `globs: ["docs/.docs-review-ledger.toml"]`, and cites `tools/docs_guard/ledger.py:54` and
  `tools/hooks/ledger_guard.py:decide` as `location` fields. Its own schema description says
  explicitly "the instance it validates ENFORCES NOTHING... no hook imports the instance" — this
  is a documented-dead inventory file (per STATE.md Phase 30: "loader CUT — kept as inventory").
  After Phase 41, this record's `location` fields will point at deleted files. **Nothing reads or
  gates on this file** (confirmed by its own schema prose), so the staleness is harmless and
  costs nothing until Phase 44 deletes `deny-domains.*` outright. Do not touch it in Phase 41 —
  editing a file explicitly reserved for a later phase would be scope creep in the other direction.
- **`docs/reference/deny-domains.md`** — the generated reference page for the above; same
  reasoning, same deferral.
- **`gate-registry.json`** — grepped for a docs-related entry; none found. Not implicated.

## Safe Deletion Order

Reasons given per step; each step is a separate commit unless noted, honoring D-09 (unbind first)
and D-10/D-11 (delete → stage → commit → verify → amend-if-red, `git commit -- <pathspec>` with
`git diff --cached --name-only` inspected immediately before every commit).

1. **Unbind.** Edit `docs/doc-dependencies.toml` to remove all 8 `[[binding]]` rows. Delete
   `docs/.docs-review-ledger.toml`. Commit. *Why first:* D-09 — nothing downstream may reference a
   binding before its source registry is emptied; this also means when the guard package is
   deleted next, there is no dangling `[[binding]]` referencing a since-removed contract.
2. **Delete the guard package + its data files.** `tools/docs_guard/` (whole dir),
   `docs/doc-dependencies.toml` (now empty of bindings — delete the file itself),
   `docs/reference/doc-dependencies.md`. Commit.
3. **Delete the hook + emitter wiring.** `tools/hooks/ledger_guard.py`,
   `harness/plugins/ledger-guard.ts`; edit `harness/permission-matrix.json` (`path_deny_globs` +
   `_note`); edit `tools/harness_emit/merge.py` (`HARNESS_SIGNATURES` + hook-group dict). *Why
   here:* the hook must go before the CI job that runs tests importing it, and after the guard
   package (so nothing calls `tools.docs_guard` from inside the hook path — it never did, but
   ordering-by-dependency-direction is the safer default).
4. **Delete the runtime surface at source, then re-emit.** `harness/commands/docs-update.md`,
   `harness/skills/docs-upkeep/`; then run `python -m tools.harness_emit`. This single re-emit
   removes the emitted `.claude/`/`.opencode/` command+skill files, prunes
   `emit-manifest.json` rows, and (because of step 3's `merge.py` edit already landed) drops the
   `ledger_guard` hook group from `.claude/settings.json` and repairs the `AGENTS.md` managed
   block. Commit re-emit output as its own commit or fold into this step — Claude's discretion
   (CONTEXT.md).
5. **Delete the derived staleness queue.** `tools/memory_regen/docs_staleness.py` + its test +
   `inject.py:82,217` row + `test_inject_docs_pointer.py`. *Why after step 2:* this module imports
   `tools.docs_guard` (`:42-44`) — deleting it before the guard package would be backwards (it
   would still import a live package); deleting it after is also correct since import order
   doesn't matter for git history, but doing it right after the guard's own deletion keeps the
   "who imports the deleted package" fix adjacent to the deletion in the commit log.
6. **Delete the contract + rebaseline.** `contracts/harness/docs/doc-dependencies.schema.json` +
   rebaseline `contracts/.hashes/manifest.json` via `uv run python -m tools.contract_hash.hash
   --write` — **same commit**, per D-02/ordering rule (3): "every contract deletion... rebaselines
   the hash manifest in the same commit."
7. **Fix the undocumented `adoption_apply` consumer.** Edit `tools/adoption_apply/apply.py`
   (remove import, exception class, glob check, catch clause) and
   `tools/adoption_apply/tests/test_constitution_refusal.py` (remove the ledger test class).
   *Why here, not earlier:* this edit is independent of the hook/guard deletion in terms of file
   existence (it's a Python-level dependency, not a filesystem one) but logically belongs with
   "cutting every reference to `ledger_guard`" — doing it in the same wave as step 3 is equally
   valid; the only hard constraint is it must land before the final full-suite green check, since
   `tools.adoption_apply` fails to import while `tools/hooks/ledger_guard.py` is gone and this
   file still imports it.
8. **Delete the CI job + fan-in entry.** `.github/workflows/ci.yml:317-351` (job) and remove
   `docs-guard` from `:381`'s `needs:` list — same commit, per ordering rule (5). *Why last:* CI
   should stop referencing the job only once every local consumer of the deleted surface is
   already gone; deleting the job first while local tests still import `tools.docs_guard` would
   just hide the breakage from CI, not fix it.
9. **Prose + test sweep.** `tools/harness_lint/caps.py` (`EXPECTED_SKILLS`),
   `tools/harness_emit/tests/test_coexist.py` (count 26→25),
   `tools/hooks/tests/test_settings_coexist.py` (`_NEW_GATES` row), delete
   `tools/harness_lint/tests/test_docs_update_wiring.py` whole,
   `tools/docs_sync/tests/test_docs_sync_determinism.py` (`EXPECTED_PAGES`),
   `harness/skills/gate-model/SKILL.md` (trim 3 spots),
   `tools/harness_lint/tests/test_tests_are_isolatable.py` (cosmetic). Claude's discretion whether
   this is one task or folded into the deletion tasks above (CONTEXT.md explicitly defers this).
10. **Refresh `uv.lock`.** `uv sync --all-packages` (Phase 40's exact precedent) after the
    `tools/docs_guard/` directory is gone — the workspace member disappears via the `tools/*` glob,
    no `pyproject.toml` edit needed (mirrors Phase 40, `pyproject.toml:34` untouched).
11. **Final verification wave.** Full `uv run pytest -q`; residue grep sweep; `emit-drift`;
    `stale-derived`; `contract-drift`; `ruff-ratchet`; YAML-resolved `gate.needs` check (Phase 40's
    method — parse the YAML, don't grep the string).

**On D-10's carry-forward from Phase 40:** the exact three tests Phase 40 found red-until-committed
were adoption-catalog tests (`test_plan_classification.py::test_contract_candidate_matches_real_repo_schema_count`,
`test_scan_exclusions.py::test_ci_yml_false_positive_closed`,
`test_dispositions.py::test_catalog_invariant_to_untracked_local_state`) — all in
`tools/adoption_scan`, because `destinations.py:217` reads `git ls-files`. **This phase deletes far
more tracked files** (6110+233+90+92 LOC plus the registry/ledger/schema — a much larger tracked-file
delta than Phase 40's 611 LOC), so expect the same three tests red between "deleted on disk" and
"committed," possibly joined by any adoption-catalog test whose row-count fixture was tuned against
the pre-deletion file count (verify `destinations.py`'s catalog size assertions, if any, before
assuming exactly three). Apply the same delete → stage → commit → verify → amend-if-red discipline
per commit in the order above, not only at the very end.

## Gate Mechanics

| Gate | Exact command | What changes | Verified from |
|---|---|---|---|
| `docs-guard` CI job removal | delete `.github/workflows/ci.yml:317-351` | job disappears | direct read |
| fan-in `needs:` | resolve as YAML (e.g. `python3 -c "import yaml; ..."` or the project's existing Phase-40 method — **not grep**) — remove `docs-guard` token from the 12-entry list at `:381`, leaving 11 | one token removed, no reorder | direct read; Phase 40 precedent (`40-01-SUMMARY.md` V-3) |
| `contract-drift` rebaseline | `uv run python -m tools.contract_hash.hash --write` (confirmed exact flag name `--write`, `hash.py:93`) | removes the `contracts/harness/docs/doc-dependencies.schema.json` key from `contracts/.hashes/manifest.json` (currently at line 6) | direct read of `hash.py` + manifest |
| `emit-drift` / `stale-derived` | `python -m tools.harness_emit` then the CI's re-emit+diff step; separately `python -m tools.docs_sync && python -m tools.memory_regen.contracts_index` then diff | both must produce an empty diff after the deletions land and are re-emitted | Phase 9/40 precedent, `ci.yml` comment blocks |
| ruff ratchet | `uv run python -m tools.ruff_baseline` (module invoked directly, per Phase 40's V-9 `40-01-SUMMARY.md`) | baseline count **drops** (net LOC removed is large — deleted files carried lint findings too); a lower live count than the committed baseline still PASSes (ratchet only fails on *increase*) per the module's own semantics — **no rebaseline should be needed unless the live count is asserted `==` baseline rather than `<=`.** Verify `tools/ruff_baseline/ratchet.py`'s comparison operator before assuming a no-op; Phase 40's baseline was 245 and passed unchanged after an 611-LOC deletion, suggesting `<=` semantics, but confirm at execution time rather than trusting this inference | inferred from Phase 40's V-9 output ("245 findings (baseline 245) / PASS") plus module name; **not independently re-read in this research pass — flag for planner to grep `ratchet.py`'s comparison operator before writing the plan's acceptance criterion** |
| `uv.lock` refresh | `uv sync --all-packages` (exact command, Phase 40 precedent) | `logparser-docs-guard` member (confirmed name, `uv.lock:20,309-311`) disappears; no `pyproject.toml` edit (glob member) | direct read of `uv.lock` + Phase 40 summary |
| `contract_guard` / `ledger_guard` PreToolUse trigger on Bash `git rm` | n/a (no command — this is a negative finding) | **Neither hook fires on a Bash-tool `git rm` or Bash-invoked script write.** Both hooks are registered under `"matcher": "Write|Edit"` only (confirmed: `.claude/settings.json` PreToolUse groups for both `contract_guard` and `ledger_guard` show `"matcher": "Write|Edit"`, not `Bash`). `tools/adoption_apply/apply.py`'s own docstring independently confirms this design fact for `contract_guard`: "fires ONLY on Claude's own Write/Edit tool calls, never on a bare Python `os.replace()`". **Practical consequence for this phase:** deleting `contracts/harness/docs/doc-dependencies.schema.json` via `git rm` (Bash) does not trigger `contract_guard`; running `uv run python -m tools.contract_hash.hash --write` (Bash, invoking a Python script that calls `Path.write_text()`) to rebaseline `contracts/.hashes/manifest.json` also does not trigger it. **`HARNESS_DEV_BYPASS` is very likely NOT needed anywhere in this phase's execution**, unlike Phase 39 which used the Claude `Write` tool directly on `docs/adr/0012-*.md`. If a plan step ever uses the `Edit`/`Write` tool directly on a constitution-plane path (e.g., hand-editing `docs/doc-dependencies.toml`'s bindings — **not** constitution-plane, or `harness/permission-matrix.json` — also not constitution-plane), re-check `CONSTITUTION_GLOBS` before assuming a bypass is needed; none of this phase's edit targets are constitution-plane paths except the one schema file, which is deleted via `git rm`, not edited | confirmed via `.claude/settings.json` matcher inspection + `apply.py` docstring cross-check |

## Runtime State Inventory

Not applicable — this is a code/config/CI deletion phase, not a rename/refactor/migration phase.
No datastore, live external service, OS-registered task, secret, or build artifact carries the
`docs-guard` plane's name in a way that survives outside the git tree. **Confirmed nothing found**
in each category:

| Category | Items Found | Action Required |
|---|---|---|
| Stored data | None — the "ledger" and "registry" are git-tracked TOML files, not a runtime datastore | none |
| Live service config | None — no external service (n8n, Datadog, etc.) references this plane; it is CI-only | none |
| OS-registered state | None — no scheduled task, pm2 process, or launchd/systemd unit names this plane | none |
| Secrets/env vars | None — no env var or SOPS key references `docs_guard`/`ledger_guard`/`doc-dependencies` | none |
| Build artifacts | `uv.lock`'s `logparser-docs-guard` virtual member is the only "installed" artifact, and it is addressed above (refresh via `uv sync --all-packages`) | covered in Gate Mechanics |

## Common Pitfalls

### Pitfall 1: Assuming `emit-manifest.json` needs a hand-edit
**What goes wrong:** CONTEXT.md's D-12 phrasing ("Remove the corresponding rows from
`tools/harness_emit/emit-manifest.json`") reads like a manual edit instruction.
**Why it happens:** the file's rows do look like a static list at a glance.
**How to avoid:** it's prune-then-write, regenerated by `tools.harness_emit.generate.emit()` on
every run (confirmed by STATE.md's Phase-7 entry: "emit-manifest.json prune-then-write owns ONLY
harness paths... D-03"). Just delete the `harness/` source and re-emit; do not touch the JSON by
hand.
**Warning signs:** a diff that manually removes JSON array entries in the same commit as a
`harness/` deletion, with no `python -m tools.harness_emit` invocation logged.

### Pitfall 2: Missing the `tools/adoption_apply` import-time breakage
**What goes wrong:** deleting `tools/hooks/ledger_guard.py` alone breaks
`import tools.adoption_apply.apply` (module-level import at `apply.py:65`), which cascades into
every test importing that module — a much larger red-test blast radius than the docs_guard
package's own 8 test files.
**Why it happens:** the CONTEXT.md scope list and ADR-0012's clause (b) enumeration both describe
this plane's *emitted* surface (hook, command, skill) and its *own* tests, but neither traces the
Python import graph into `tools/adoption_apply`, which reuses `ledger_guard.REVIEW_LEDGER_GLOBS`
as data (a deliberate reuse pattern per its own docstring — "IMPORTED as DATA from the PreToolUse
gate that owns it... never re-declared").
**How to avoid:** grep for `from tools.hooks.ledger_guard import` (or `import
tools.hooks.ledger_guard`) across the whole tree before considering the hook deletion complete;
this research found exactly one hit outside the guard/hook/test files named in CONTEXT.md
(`tools/adoption_apply/apply.py:65`).
**Warning signs:** any test collection error mentioning `ModuleNotFoundError:
tools.hooks.ledger_guard` after the hook file is deleted.

### Pitfall 3: Treating the ruff ratchet as needing a rebaseline by default
**What goes wrong:** assuming ~6.3k LOC removed automatically requires
`tools/ruff_baseline/baseline.json` to be rewritten.
**Why it happens:** intuition says "the codebase shrank, so counts changed."
**How to avoid:** Phase 40 deleted 611 LOC and the ratchet stayed at its existing baseline (245)
with a PASS, per `40-01-SUMMARY.md` V-9 — suggesting the ratchet only fails on an *increase* past
baseline, not a change in either direction. **This was not independently re-verified in this
research pass** (see Gate Mechanics table) — the planner should grep `ratchet.py`'s comparison
operator (`<=` vs `==`) before writing an acceptance criterion that assumes either behavior.
**Warning signs:** a rebaseline commit for `ruff_baseline` with no accompanying explanation of why
the count moved in the direction it did.

### Pitfall 4: Deleting the CI job before the local consumers are gone
**What goes wrong:** removing `docs-guard` from `ci.yml` first can mask a still-broken local import
(`tools.adoption_apply`) because CI no longer runs the specific job that would have surfaced it —
but the fan-in `gate` job still runs `core-suite`/`lang-tests`, which DOES run the full
`uv run pytest`, so the breakage would still be caught, just misattributed to a different job name.
**Why it happens:** CI job boundaries don't align 1:1 with Python import boundaries — `docs-guard`
only directly runs `pytest tools/docs_guard tools/memory_regen/tests/test_docs_staleness.py`
(`ci.yml:351`), not the whole suite.
**How to avoid:** run `uv run pytest -q` locally (the full suite) before landing the CI job
deletion commit, not just the two paths the old job scoped to.
**Warning signs:** `docs-guard` job absent from `ci.yml` but `core-suite`/`lang-tests` newly red on
an unrelated-looking `ModuleNotFoundError`.

### Pitfall 5: Assuming the count in `test_coexist.py` is self-correcting
**What goes wrong:** `test_all_26_commands_emit_to_both_trees` hardcodes `== 26` as a literal
integer, not a computed count — it will not "notice" that `docs-update.md` is gone; it will simply
assert a now-wrong number and fail with a message like "expected 26 opencode commands, got 25,"
which is easy to misread as a bug in the emitter rather than an update needed to the test's literal.
**Why it happens:** the test is deliberately over-specified (anti-sprawl pattern — every prior
phase in STATE.md's history shows this same test's count being bumped by hand each time a command
is added).
**How to avoid:** update the literal to 25 in the same commit that deletes
`harness/commands/docs-update.md`.
**Warning signs:** a failing assertion whose message states an "expected N, got N-1" shape — this
IS the test working correctly, not a regression.

## Code Examples

No new code is written in this phase. The two concrete edits with load-bearing shape:

```python
# tools/adoption_apply/apply.py — BEFORE (import + exception + check + catch, current state)
from tools.hooks.ledger_guard import REVIEW_LEDGER_GLOBS

class ReviewLedgerRefusal(ValueError):
    """Raised when a destination resolves onto the human-review ledger. ..."""

# inside refuse_unsafe_destination(...):
if resolve_path(REVIEW_LEDGER_GLOBS, relative.lower()) == "deny":
    raise ReviewLedgerRefusal(...)
refuse_if_constitution(relative.lower())

# inside apply_manifest(...):
except (ConstitutionRefusal, ReviewLedgerRefusal):
    summary["refused"].append(destination)
    continue
```

```python
# tools/adoption_apply/apply.py — AFTER (all four ledger-specific pieces removed)
# (no ledger_guard import)
# (no ReviewLedgerRefusal class)

# inside refuse_unsafe_destination(...):
refuse_if_constitution(relative.lower())

# inside apply_manifest(...):
except ConstitutionRefusal:
    summary["refused"].append(destination)
    continue
```

```python
# tools/harness_emit/merge.py — HARNESS_SIGNATURES, BEFORE
HARNESS_SIGNATURES: tuple[str, ...] = (
    "tools.hooks.format_on_write",
    "tools.hooks.contract_guard",
    "tools.hooks.ledger_guard",     # <-- remove this line
    "tools.hooks.secret_scan",
    "tools.hooks.commit_gate",
    "tools.hooks.resume_gate",
)
```

## State of the Art

Not applicable — no library/framework version question in a pure-deletion phase. The one
"technique" question (rebaseline mechanics, emitter re-run, uv sync) is fully answered by Phase
40's already-measured precedent (`40-01-SUMMARY.md`), which this research treats as the template.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | `tools/ruff_baseline`'s comparison is `<=` (fail only on increase), inferred from Phase 40's unchanged-baseline PASS after a 611-LOC deletion, not independently re-read from `ratchet.py` in this research pass | Gate Mechanics / Pitfall 3 | If the comparison is actually `==`, the planner needs an explicit rebaseline task for `tools/ruff_baseline/baseline.json`; skipping it would red the gate unexpectedly |
| A2 | `tools/harness_lint/tests/test_workspace_member_completeness.py` needs no edit for this phase (grep found zero `docs_guard`/`ledger_guard`/`doc-dependencies` hits despite CONTEXT.md D-13 naming it) | Verified Deletion/Edit Inventory | Low — if a hit exists that this grep missed (e.g., a dynamically-constructed string), the test could red unexpectedly; low probability since the grep pattern was broad and case-sensitive-safe |
| A3 | `.memory/README.md` needs no edit (CONTEXT.md D-13 names it for the "third path-deny domain" sentence, but that sentence lives in `harness/permission-matrix.json` and `gate-model/SKILL.md`, not this file) | Verified Deletion/Edit Inventory | Low — cosmetic only; if wrong, a stale sentence survives in a non-gated prose file with no test enforcing its content |
| A4 | The comment-referenced test name `test_ledger_guard_is_wired_into_pretooluse` (in `merge.py:172`) is a stale/renamed reference and the actual enforcing test is `test_settings_coexist.py::test_harness_gates_registered_with_expected_matcher` | Verified Deletion/Edit Inventory | Low — if a test by that exact name exists elsewhere and this research's grep missed it, deleting `ledger_guard` without updating it would leave a dangling test reference; grep was repo-wide and returned only the one comment hit |

**Confirmation needed from planner/executor:** A1 should be resolved by reading
`tools/ruff_baseline/ratchet.py`'s comparison operator before the plan commits to "no rebaseline
needed" as an acceptance criterion.

## Open Questions

1. **Does `tools/ruff_baseline/ratchet.py` compare `<=` or `==` against `baseline.json`?**
   - What we know: Phase 40 removed 611 LOC and the ratchet passed unchanged (245/245).
   - What's unclear: whether that's because the comparison tolerates *any* count `<=` baseline, or
     because 611 LOC of that specific package happened to carry zero ruff findings (i.e., the
     baseline count didn't move because the deleted code wasn't contributing findings, not because
     the comparator is lenient).
   - Recommendation: read `ratchet.py` directly at plan time; if `==`, add an explicit rebaseline
     task using whatever `--write`-equivalent flag it exposes.

2. **Should `LEDGER_ADJACENT_ALLOWED`'s two doc-registry paths in
   `test_constitution_refusal.py` be deleted along with the ledger test class, or kept as
   negative controls proving those (now-nonexistent) paths still resolve outside the constitution
   plane?**
   - What we know: `docs/doc-dependencies.toml` and `docs/reference/doc-dependencies.md` are both
     being deleted in this phase; the test asserts they are NOT refused by
     `refuse_unsafe_destination`, which will remain trivially true (a nonexistent path resolves
     fine) but tests nothing meaningful once the files are gone.
   - What's unclear: whether the test author intended these two rows to be load-bearing beyond the
     ledger-adjacency check (they may also be guarding against a future accidental widening of
     `CONSTITUTION_GLOBS`, independent of the ledger).
   - Recommendation: delete both rows along with the `ReviewLedgerRefusal`-specific test class;
     if `CONSTITUTION_GLOBS` widening is a separate concern worth testing, it needs its own
     negative control against a path that still exists (e.g., `docs/how-to/task-lifecycle.md`,
     already present in the same list).

## Validation Architecture

`workflow.nyquist_validation` was not found explicitly set to `false` in `.planning/config.json`
(not read in this research pass, but absence defaults to enabled per the standard instructions) —
included per the default-enabled rule. For a **pure deletion phase**, "validated" means: the
residue sweep returns zero, every named gate command exits as expected, and the suite is green —
there is no new behavior to unit-test.

### Test Framework
| Property | Value |
|---|---|
| Framework | pytest (via `uv run pytest`), Python 3.11 |
| Config file | root `pyproject.toml` (uv workspace, `members = ["libs/python", "tools/*"]`) |
| Quick run command | `uv run pytest tools/adoption_apply tools/harness_lint tools/harness_emit tools/hooks tools/docs_sync tools/memory_regen -q` (the packages this phase touches) |
| Full suite command | `uv run pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|---|---|---|---|---|
| CER-05 | No human-authored ledger row required by any gate | structural/absence | `grep -rnE "docs_guard\|docs-guard\|docs-review-ledger\|ledger_guard\|docs-upkeep\|docs-update\|doc-dependencies" tools/ harness/ contracts/ docs/ .github/ .claude/ .opencode/ AGENTS.md .memory/README.md uv.lock` (must return empty outside `.planning/`) | integration | same command, exit-code check (`grep` exits 1 on no match) | ✅ existing shell, no new test file |
| CER-05 | No module imports `tools.docs_guard` | import-safety | `uv run pytest --collect-only -q` (a collection error surfaces any dangling import) | unit/collection | `uv run pytest --collect-only -q` | ✅ |
| CER-05 | CI fan-in gate green | integration | full `uv run pytest -q` + `emit-drift` + `stale-derived` + `contract-drift` + `ruff-ratchet` locally, then push and watch `gate` job | integration | (listed individually in Gate Mechanics table) | ✅ all pre-exist |

### Sampling Rate
- **Per task commit:** the touched package's own test module(s) (e.g., `uv run pytest
  tools/adoption_apply -q` after editing `apply.py`).
- **Per wave merge:** full `uv run pytest -q` plus the residue grep sweep.
- **Phase gate:** full suite green, all four structural gates (`emit-drift`, `stale-derived`,
  `contract-drift`, ruff ratchet) clean, before `/gsd:verify-work`.

### Wave 0 Gaps
None — every test file this phase touches already exists (this is deletion-only; no new test
infrastructure is created, per D-16 — no mutation-proof table is owed because nothing
control-shaped is being added).

## Security Domain

`security_enforcement` was not confirmed explicitly disabled in `.planning/config.json` (not read
this pass); included per the default-enabled rule, but this phase has **no security-relevant
surface**. It deletes a review-obligation gate and a path-deny hook; it adds no input-handling
code, no auth, no cryptography, no session state. The only "control" being removed
(`ledger_guard`'s deny) is explicitly a **non-security** control — a human-workflow-review gate,
not a threat mitigation — and its removal is the entire point of the milestone (ADR-0012, CER-05).
No ASVS category applies to a phase that deletes CI/hook configuration with no data-handling
change.

| ASVS Category | Applies | Standard Control |
|---|---|---|
| V2 Authentication | no | n/a |
| V3 Session Management | no | n/a |
| V4 Access Control | no | the `ledger_guard`/`contract_guard` PreToolUse deny is a dev-workflow gate, not an access-control boundary for the shipped product; its removal is in scope by design |
| V5 Input Validation | no | n/a — no new input path |
| V6 Cryptography | no | n/a |

No threat-pattern table applies — nothing in this phase processes untrusted input or exposes a new
attack surface; it removes CI configuration and Python tooling files.

## Sources

### Primary (HIGH confidence — verified directly against the tree, 2026-07-27)
- Direct `find`/`wc -l`/`grep`/`sed` reads of every path named above: `tools/docs_guard/**`,
  `tools/hooks/ledger_guard.py`, `harness/plugins/ledger-guard.ts`,
  `harness/permission-matrix.json`, `harness/commands/docs-update.md`,
  `harness/skills/docs-upkeep/SKILL.md`, `harness/skills/gate-model/SKILL.md`,
  `tools/memory_regen/{docs_staleness.py,inject.py}` + tests, `tools/adoption_apply/{apply.py,tests/*}`,
  `tools/harness_emit/{merge.py,emit-manifest.json,tests/test_coexist.py}`,
  `tools/harness_lint/{caps.py,tests/*}`, `tools/hooks/tests/{test_settings_coexist.py,test_contract_guard.py}`,
  `tools/docs_sync/tests/test_docs_sync_determinism.py`, `tools/contract_hash/hash.py`,
  `contracts/{.hashes/manifest.json,harness/docs/*,harness/security/*}`,
  `docs/{doc-dependencies.toml,.docs-review-ledger.toml,reference/*,adr/0010-*,adr/0012-*}`,
  `.github/workflows/ci.yml`, `uv.lock`, `pyproject.toml`, `AGENTS.md`, `.memory/README.md`,
  `.claude/settings.json`.
- `.planning/phases/40-self-gate-teardown/40-01-SUMMARY.md` — the deletion-ordering measurement
  (D-10's source) and the exact gate commands (`ruff_baseline`, `contract_drift`, `uv sync
  --all-packages`).
- `docs/adr/0012-ci-and-merge-as-decision-authority.md` — the authority cited instead of a new
  ADR; its clause (b) enumeration of Phase 41's targets, cross-checked against ROADMAP.md and
  matched exactly.
- `.planning/phases/41-docs-review-plane-removal/41-CONTEXT.md` — the locked D-01..D-17 decisions
  this research does not re-litigate.

### Secondary (MEDIUM confidence)
- None — no web search or external library research was applicable to this phase.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Deletion inventory: HIGH — every path verified present/absent by direct tool invocation, not
  inferred from documentation.
- Import/consumer graph: HIGH for the documented plane; HIGH-confidence NEW finding for
  `tools/adoption_apply` (verified by direct source read, not grep-alone) — flagged prominently
  since it is undocumented elsewhere.
- Gate mechanics: HIGH except the ruff-ratchet comparison operator (A1, flagged LOW/unverified —
  inferred from Phase 40's observed behavior, not read directly in this pass).
- Ordering: HIGH — directly derived from D-09/D-10/D-11 plus Phase 40's measured precedent.

**Research date:** 2026-07-27
**Valid until:** short-lived — this research is single-use for Phase 41's plan; re-verify file
states if execution is delayed more than a few days, since this is an actively-changing repo mid-
milestone.
