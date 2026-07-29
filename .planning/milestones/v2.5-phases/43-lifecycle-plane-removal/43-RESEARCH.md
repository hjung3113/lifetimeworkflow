# Phase 43: Lifecycle Plane Removal - Research

**Researched:** 2026-07-28
**Domain:** Whole-plane deletion in a contract-first polyglot monorepo harness (Python `tools/`
packages, `harness/` source, dual-emitted `.opencode/`+`.claude/` trees, JSON-Schema contracts, CI
fan-in)
**Confidence:** HIGH — every claim below is grepped/read against this working tree on
2026-07-28 (branch `claude/data-pipeline-harness-8aypct`), not inferred from training data.

## Summary

CER-07 deletes 8 mutually-referential `tools/` packages (7021 LOC), 6 of 7 task-control contracts,
4 commands, 1 hook, 5 discipline skills, 3 `harness/*.toml` declarations, `.workflow/tasks/`, and
the CI `lifecycle-eval` job. This is a pure deletion phase — no new tool, gate, abstraction, shim,
or dependency is in scope (CER-07's explicit "no residue package" clause, reinforced by the
milestone's binding constraint).

The deletion's real difficulty is not the 8 packages themselves (they die together, in one commit,
because a leaf-first order does not exist — D-04) but the **blast radius**: surviving artifacts that
invoke the dying plane and would ship broken if the packages simply vanished. CONTEXT.md D-01 names
five (four commands + the orchestrator agent). This research independently re-verified all five and
found **five more classes of surviving artifact** that D-01 does not name: (1) a `docs_sync`
`EXPECTED_PAGES` frozenset that will assert 5 now-deleted schema pages exist; (2) a `contract_hash`
`DATA_CONTRACT_PATHS` entry that must be edited (not left alone) while a sibling entry in the same
tuple must survive untouched; (3) two structural tests (`test_settings_coexist.py`,
`test_coexist.py`) that hardcode the `resume_gate` hook group and will assert a false positive after
the hook is dropped; (4) a hardcoded member-name literal in `test_tests_are_isolatable.py`'s
live-enumeration negative control that names `tools/lifecycle_eval/tests` by string; (5) the derived
`.memory/derived/contracts-index.md` (15→9 contracts) and `.memory/derived/repo-map.md`, which
regenerate automatically but must actually be regenerated in-commit or the committed-derived
(MAINT-02) plane goes stale, exactly as happened twice in Phase 41.

Two things this research confirms are **not** problems, despite superficially looking related:
`tools/contract_graph/tests/test_query.py`'s forbidden-import list (asserts query.py never imports
`tools.task_control`/`tools.evidence`/etc.) stays correct and requires no edit — it is a negative
assertion that remains true regardless of whether the named packages exist. And
`.claude/get-shit-done/workflows/execute-phase.md:158`'s `safe_resume_gate` step name is GSD's own
vendored workflow step, unrelated to this repo's `tools.hooks.resume_gate` — a naming coincidence,
not a coupling.

**Primary recommendation:** two waves, repair-then-delete (D-02), each task ending in
delete/edit → stage → commit → verify (D-12/D-13). Wave 1 repairs every surviving artifact (five
D-01 items + the five newly-found items above) so nothing on the surviving surface still names a
module Wave 2 deletes. Wave 2 deletes the 8 packages + contracts + commands + hook + skills +
declarations + `.workflow/tasks/` + CI job as one or more pathspec-scoped commits, then regenerates
the derived plane and rebaselines the contract-hash manifest in the same commits that caused the
staleness (Phase 41's precedent, not a separate sweep).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Task lifecycle state (task_control, task_packet, handoff, evidence) | DEV tooling (`tools/`) | — | In-session gate machinery for this checkout only; ADR-0012 names CI + the merge as the replacement authority — not re-homed, deleted |
| Risk routing / discipline enforcement (risk_router, discipline, capability) | DEV tooling (`tools/`) | `harness/*.toml` declarations | Declarative policy (toml) + pure-Python evaluator; both halves die together (D-08) |
| Resume-gate mutation guard | `.claude/settings.json` PreToolUse hook + opencode plugin | `tools/hooks/resume_gate.py` | Dual-runtime enforcement point; both the emitted hook group and its authored source must be removed via the `RETIRED_SIGNATURES` mechanism, not by hand-editing the emitted file |
| Session-context injection (activeContext pointer) | `tools/memory_regen/inject.py` (derived-plane assembler) | SessionStart hook (both runtimes) | Survives; only the active-TASK half of the same module is removed (D-11) |
| Contract hash/drift gate | `tools/contract_hash`, `tools/contract_drift` | `contracts/.hashes/manifest.json` | Owns `DATA_CONTRACT_PATHS`, a hand-maintained tuple that must be edited for `transitions.json` (removed) while leaving `gate-registry.json` (Phase 44) untouched |
| Derived docs (`docs/reference/*.md`) | `tools/docs_sync` | `tools/docs_sync/tests/test_docs_sync_determinism.py` `EXPECTED_PAGES` | Prune-then-write already deletes the orphaned pages on next run; the test's frozenset is a hand-maintained anti-drift literal that must shrink in the same commit or the render/prune tests fail |
| CI fan-in | `.github/workflows/ci.yml` `gate.needs` | — | 11→10 entries; verify via `ruamel.yaml`-resolved parse, never grep (D-10, Phase 41 D-14 precedent) |

## Standard Stack

Not applicable — this phase adds no new library, tool, or dependency (CER-07's binding constraint:
"no residue package"). Package Legitimacy Audit is skipped for the same reason (no external package
install in scope).

## Package Legitimacy Audit

**Not applicable.** This phase installs no external packages. It *removes* 8 first-party workspace
members from `uv.lock` (a `uv sync`/lock refresh, not a package install) and touches no
`pyproject.toml` dependency list. Per the Package Legitimacy Gate protocol, this section is
correctly omitted from enforcement — there is nothing to slopcheck.

## The Complete Blast Radius (core deliverable)

Verified 2026-07-28 by `grep -rnE "task_control|task_packet|risk_router|tools\.evidence|tools\.handoff|
tools\.discipline|tools\.capability|lifecycle_eval|resume_gate|resume-gate"` across
`harness/ .github/ AGENTS.md .memory/ libs/ examples/ .opencode/ .claude/ contracts/ docs/`, plus
targeted greps for `task-control` (hyphenated) and the 8 package names outside their own trees.

### Per-package importers/invokers outside the plane

| Package/hook | External referencers found | Classification |
|---|---|---|
| `tools.task_control` | `harness/commands/phase-gate.md:13,19,31` (CLI invocation); `harness/commands/discipline.md:48` (prose, "`tools.task_control` — `transition()` refuses…"); `.memory/derived/repo-map.md:6` (derived, symbol list) | **delete-with-the-plane** (phase-gate.md itself is deleted, D-06) except the repo-map line, which is **derived, auto-regenerates** |
| `tools.task_packet` | `harness/commands/intake.md:40` (CLI); `contracts/harness/task-control/transitions.json` (internal, deleted with contract) | **delete-with-the-plane** |
| `tools.risk_router` | `harness/commands/intake.md:31` (CLI); `harness/risk-policy.toml:25` (prose comment) | **delete-with-the-plane** |
| `tools.evidence` | `harness/commands/review.md:50-51` (CLI, `add-finding`); `harness/commands/verify-work.md:23` (CLI, `capture`); `tools/adoption_scan/scan.py:5` (docstring contrast only — CONTEXT.md's own D-specifics note) | `review.md`/`verify-work.md` = **must-repair-before-delete** (D-01); `scan.py` docstring = **prose-only, in-scope sweep this phase** (one sentence, not deferred — it names a module this phase deletes, unlike the Phase-44 `gate-registry.json` docstrings CONTEXT.md explicitly defers) |
| `tools.handoff` | `harness/commands/checkpoint.md:22,46`; `harness/commands/orient.md:23`; `harness/commands/handoff.md:13,15,20`; `tools/memory_regen/inject.py:16-22,137-167` (imports `HandoffError`, `packet_root_from_handoff`, `validate as validate_handoff`) | `checkpoint.md`/`orient.md` = **must-repair-before-delete** (D-01); `handoff.md` = **delete-with-the-plane** (it is one of the 4 deleted commands); `inject.py` = **must-repair-before-delete** — the whole `_active_task_pointer` function plus its 3-name import block must go (see dedicated section below) |
| `tools.discipline` | `harness/commands/discipline.md:12,22` (deleted command); 5 skills (`clarify`, `diagnose`, `domain-modeling`, `test-driven-change`, `adversarial-review-panel`) each invoke `tools.discipline`/`tools.capability` in their `SKILL.md` bodies | **delete-with-the-plane** — the 5 skills are themselves D-07's deletion target, so their internal invocations need no separate repair |
| `tools.capability` | `harness/agents/orchestrator.md:57-58,118` (routing step); same 5 skills as above | `orchestrator.md` = **must-repair-before-delete** (D-01); the 5 skills = **delete-with-the-plane** |
| `tools.lifecycle_eval` | `.github/workflows/ci.yml:233,235` (the job itself) | **delete-with-the-plane** (the whole `lifecycle-eval` job, D-10) |
| `tools.hooks.resume_gate` / `resume-gate.ts` | `harness/opencode.json:31` (authored plugin array); `harness/plugins/resume-gate.ts` (source, deleted); `tools/harness_emit/merge.py:88-94,143-199` (`HARNESS_SIGNATURES` + `HARNESS_HOOK_GROUPS`); `.claude/settings.json:155` (emitted, D-06); `tools/harness_emit/tests/test_coexist.py:184`; `tools/hooks/tests/test_settings_coexist.py:86`; `tools/harness_lint/workspace_check.py:22` (docstring prose only); `tools/harness_lint/tests/test_workspace_member_completeness.py:14` (docstring prose only) | **must-repair-before-delete**: `harness/opencode.json` (remove array entry), `merge.py` (move signature to `RETIRED_SIGNATURES`, remove group from `HARNESS_HOOK_GROUPS`), `test_coexist.py` + `test_settings_coexist.py` (drop the hardcoded resume_gate expectation). `workspace_check.py`/`test_workspace_member_completeness.py` prose mentions are **prose-only, cosmetic** — no assertion depends on the string, safe to leave for Phase 45 (CER-11) or fix opportunistically in the same commit |

### The five D-01 artifacts, independently re-verified (exact lines, 2026-07-28)

1. `harness/commands/checkpoint.md:22` — `uv run python -m tools.handoff generate ... && ... validate ... && ... activate ...`; also `:46` (validate again in the git-commit step).
2. `harness/commands/orient.md:23` — `uv run python -m tools.handoff resume --state-dir .memory/state --repo-root .`; line 46 (not independently checked here but named in D-01) routes to `/phase-gate`.
3. `harness/commands/review.md:50-51` — `python -m tools.evidence.capture add-finding`.
4. `harness/commands/verify-work.md:23` — `python -m tools.evidence.capture capture --task-dir <task-dir> --gate <gate> -- <existing argv>`.
5. `harness/agents/orchestrator.md:57-58` — `uv run python -m tools.capability list` / `route <capability> <agent>`; `:118` — the same command repeated in a routing table row.

All five confirmed present at the cited lines. Their emitted copies exist byte-identically at
`.opencode/{command,agent}/*.md` and `.claude/{commands,agents}/*.md` (10 more files total) — **do
not hand-edit these**; fix only `harness/**` and re-run `python -m tools.harness_emit` (D-14).

### Five additional blast-radius items D-01/CER-07 do NOT name (this research's highest-value find)

1. **`tools/docs_sync/tests/test_docs_sync_determinism.py:29-43`** — `EXPECTED_PAGES` frozenset
   contains `"attestation"`, `"evidence"`, `"handoff"`, `"state"`, `"task"` (5 of the 6 deleted
   `.schema.json` files — `transitions.json` is not `*.schema.json` so `docs_sync` never generated a
   page for it and no entry exists to remove). `docs/reference/{attestation,evidence,handoff,state,
   task}.md` exist today and `docs_sync.write()`'s prune-then-write will delete them automatically on
   next `/docs-sync` run — but the **test's hardcoded frozenset does not auto-shrink**; leaving it
   will fail `test_render_matches_committed_snapshot`/the page-count assertions the moment the schema
   files are gone. Mirrors the exact Phase-41 `test_contracts_index.py` staleness pattern (41-04
   Plan). **Must-repair-before/with-delete.**
2. **`tools/contract_hash/hash.py:29-33`** — `DATA_CONTRACT_PATHS` tuple:
   ```python
   DATA_CONTRACT_PATHS = (
       Path("harness/task-control/transitions.json"),
       Path("harness/task-control/gate-registry.json"),
       Path("harness/security/deny-domains.json"),
   )
   ```
   (paths are relative to `contracts/`'s parent, i.e. resolve to `contracts/harness/task-control/
   transitions.json` etc.) **This DOES need editing**: remove the `transitions.json` entry (deleted
   this phase). **Do NOT remove `gate-registry.json`** — CER-08/Phase 44 owns it explicitly; removing
   it here would silently drop it from the hash manifest a full phase before its file deletion,
   producing an undetected manifest/file mismatch. `deny-domains.json` is untouched (Phase 44).
3. **`tools/hooks/tests/test_settings_coexist.py:86`** — `_NEW_GATES` list includes
   `("PreToolUse", "tools.hooks.resume_gate", "Write|Edit|Bash")`, asserted present in the live
   `.claude/settings.json`. After the hook group is dropped this assertion becomes a false positive
   (asserts something removed still exists) — **must-repair**: delete this tuple entry.
4. **`tools/harness_emit/tests/test_coexist.py:184`** — a hardcoded `_SEED_SETTINGS` fixture (used by
   `test_seeded_settings_json_reproduced_byte_for_byte`) includes a full literal copy of the
   `resume_gate` PreToolUse group as part of the "already-live" settings.json shape the test seeds
   before running the emitter. Once `merge.py`'s `HARNESS_HOOK_GROUPS` no longer emits that group (and
   `RETIRED_SIGNATURES` drops it), this seed must be updated to match the new steady state — **must-
   repair** (the seed should reflect the settings.json shape *after* the phase lands, not mid-phase).
5. **`tools/harness_lint/tests/test_tests_are_isolatable.py:125`** — the negative-control loop:
   ```python
   for expected in ("tools/harness_lint/tests", "tools/lifecycle_eval/tests"):
       assert expected in found, ...
   ```
   hardcodes `"tools/lifecycle_eval/tests"` as a member the live-scan MUST enumerate. After deletion
   the directory is gone and `found` will never contain it — **must-repair**: replace that literal
   with a still-existing member directory that also uses the `tests/conftest.py` root-insertion idiom
   (the file's own docstring names `lifecycle_eval` and `harness_lint` as the two idiom-A examples;
   any other member with a wiring `tests/conftest.py` — confirm via
   `grep -l sys.path.insert tools/*/tests/conftest.py` at implementation time — is an equally valid
   replacement, or simply drop to a one-element tuple naming only `tools/harness_lint/tests`).
   Separately, `test_the_scan_finds_the_members_it_claims_to`'s `len(found) >= 10` threshold is safe:
   27 `tools/*/tests` dirs exist today, 8 are deleted, 19 remain — well above 10, **no change needed**
   to the threshold itself.

### Confirmed non-issues (verified, not just assumed safe)

- **`tools/contract_graph/tests/test_query.py:75-78`** — asserts `query.py`'s source text never
  contains the strings `"import tools.task_packet"`, `"import tools.evidence"`,
  `"import tools.task_control"`, `"import tools.handoff"` (a structural D-03 invariant: the query
  layer must never gain a task-evidence coupling). This assertion is true today and remains true
  after deletion — **no action needed**. Flagged in the task prompt as a risk to check; verified safe.
- **`.claude/get-shit-done/workflows/execute-phase.md:158`** — `<step name="safe_resume_gate">` is a
  GSD-vendored workflow step name (git-blamed to `b60729d "Add GSD (Get Shit Done) harness for Claude
  Code"`), semantically about resuming a plan after a crash, unrelated to this repo's
  `tools.hooks.resume_gate` PreToolUse hook. Coincidental naming only — **no action needed, and no
  scrubbing needed even in Phase 45** (it doesn't name the deleted surface, it names an unrelated GSD
  concept that happens to share a word).
- **`tools/adoption_scan/destinations.py:179`** (`_CATEGORY_GLOBS` includes `"tools/**/*"`) — this is
  a live glob, not a hardcoded package list; deleting the 8 directories just shrinks what the glob
  matches. **No repair needed** — this is exactly the self-adjusting behavior Phase 42's PROD-01 was
  designed to produce.
- **`AGENTS.md`'s managed command/skill index** (lines ~106-107) — lists `discipline, handoff,
  intake, phase-gate` among commands and `adversarial-review-panel, clarify, diagnose,
  domain-modeling, test-driven-change` among skills. This is inside the emitter's `<!-- BEGIN
  HARNESS-MANAGED -->` fence and is regenerated verbatim by `python -m tools.harness_emit` — **no
  hand-edit needed or permitted**.
- **`docs/adr/0008-task-control-plane-lifecycle.md`, `docs/adr/0011`, `docs/adr/0012`** — ADRs are
  append-only constitution-plane documents; they reference the plane by design (0008 originally
  proposed it, 0012 records the deletion intent). **Never edited** — this is not a gap, it's the
  convention.
- **`docs/how-to/task-lifecycle.md`, `docs/explanation/next-milestone-task-control-plane.md`** —
  fully stale prose after this phase, but named nowhere in a passing/failing test, so they do not
  block `uv run pytest -q` or any CI gate. Per CER-11/ROADMAP Phase 45 ("Prose that names a deleted
  surface is scrubbed"), these are **out of scope for Phase 43** — flagged below for Phase 45.

## Architecture Patterns

### Deletion sequencing (this phase has no runtime architecture of its own — it is a removal)

```
Wave 0 (verification only)
  └─ confirm current test/CI baseline (uv run pytest -q; note failure count, should be 0)

Wave 1 — REPAIR (nothing deletable is deleted yet; every surviving artifact stops invoking the plane)
  ├─ harness/commands/{checkpoint,orient,review,verify-work}.md  (D-01, D-03: remove the lifecycle
  │    step, no successor)
  ├─ harness/agents/orchestrator.md                              (D-01, D-03: route by declared
  │    topology/stage instead of tools.capability list)
  ├─ tools/memory_regen/inject.py                                (D-11: delete _active_task_pointer +
  │    its 3-symbol tools.handoff import + TASK_HEADER + assemble()'s "task" wiring; KEEP
  │    _active_context_pointer verbatim)
  ├─ tools/memory_regen/tests/test_inject_assembler.py           (delete the two active-task tests;
  │    keep the four pointer-survival tests)
  ├─ harness/opencode.json                                       (drop "harness/plugins/resume-gate.ts"
  │    from the plugin array)
  ├─ tools/harness_emit/merge.py                                 (move "tools.hooks.resume_gate" from
  │    HARNESS_SIGNATURES to RETIRED_SIGNATURES; delete its group from HARNESS_HOOK_GROUPS)
  ├─ tools/harness_emit/tests/test_coexist.py                    (update _SEED_SETTINGS to the
  │    post-deletion shape)
  ├─ tools/hooks/tests/test_settings_coexist.py                  (drop the resume_gate _NEW_GATES row)
  ├─ python -m tools.harness_emit                                (re-emit; propagates command/agent
  │    repairs + the dropped hook group into both runtime trees + AGENTS.md + emit-manifest.json)
  ├─ tools/adoption_scan/scan.py:5                                (sweep the one docstring sentence
  │    naming tools/evidence/capture.py)
  └─ VERIFY: uv run pytest -q — should be green (nothing deleted yet, only repaired); re-emit
       idempotent (second run empty diff)

Wave 2 — DELETE (the plane itself, contracts, declarations, state, CI — one unit per D-04)
  ├─ git rm -r tools/{task_control,task_packet,risk_router,evidence,handoff,discipline,capability,
  │    lifecycle_eval} tools/hooks/resume_gate.py harness/plugins/resume-gate.ts
  │    harness/commands/{intake,phase-gate,handoff,discipline}.md
  │    harness/skills/{clarify,diagnose,domain-modeling,test-driven-change,adversarial-review-panel}
  │    harness/{capabilities,disciplines,risk-policy}.toml .workflow/tasks
  ├─ python -m tools.harness_emit                                (propagates all deletions to both
  │    runtime trees, auto-prunes emit-manifest.json rows, AGENTS.md index)
  ├─ git rm contracts/harness/task-control/{attestation,evidence,handoff,state,task}.schema.json
  │    contracts/harness/task-control/transitions.json           (gate-registry.json SURVIVES)
  ├─ tools/contract_hash/hash.py                                 (remove the transitions.json
  │    DATA_CONTRACT_PATHS entry)
  ├─ uv run python -m tools.contract_hash.hash --write            (rebaseline manifest)
  ├─ tools/docs_sync/tests/test_docs_sync_determinism.py          (shrink EXPECTED_PAGES by 5)
  ├─ python -m tools.docs_sync                                    (prune the 5 orphaned reference pages)
  ├─ tools/harness_lint/caps.py                                   (EXPECTED_SKILLS: remove the 5
  │    discipline-skill entries)
  ├─ git rm tools/harness_lint/tests/{test_capability_wiring,test_discipline_wiring}.py
  ├─ tools/harness_lint/tests/test_tests_are_isolatable.py        (repair the hardcoded
  │    "tools/lifecycle_eval/tests" literal)
  ├─ .github/workflows/ci.yml                                     (delete the lifecycle-eval job block
  │    :221-235 and its gate.needs token)
  ├─ python -m tools.memory_regen.contracts_index && python -m tools.memory_regen.repo_map
  │    (regenerate .memory/derived/{contracts-index,repo-map}.md; regen the syrupy snapshots)
  ├─ uv lock (or `uv sync --all-packages`)                        (drop the 8 workspace members from
  │    uv.lock)
  └─ VERIFY: uv run pytest --collect-only -q (0 errors) → uv run pytest -q (green) →
       tools.contract_drift.drift (exit 0) → ruamel.yaml gate.needs parse (10 entries, no
       lifecycle-eval) → re-emit idempotent
```

### Recommended plan/task decomposition (Claude's Discretion per CONTEXT.md)

A repair wave then a deletion wave is the natural shape (matches CONTEXT.md's own discretion note).
Within Wave 2, consider two commits — (a) the 8 packages + hook + commands + skills + toml + state
dir + emitter re-run, (b) contracts + hash rebaseline + CI job + derived-plane regen + uv.lock —
mirroring Phase 41's Plan 03 (runtime surface) / Plan 04 (contract + CI) split, which the checker
already validated as a working pattern. `caps.py`'s `EXPECTED_SKILLS` edit must land in the SAME
commit as the skill deletion (D-07, Phase-41-proven hard-fail-before-write ordering) — it cannot be
its own commit sandwiched between skill deletion and re-emit.

### Anti-Patterns to Avoid

- **Deleting the plane before repairing the five (or ten) surviving artifacts.** Produces
  intermediate commits whose shipped commands crash (D-02's exact rejected alternative).
- **Hand-editing `.opencode/**` or `.claude/**`.** Every fix in this phase happens at `harness/**`
  (or `tools/**`/`contracts/**`/`.github/**` for non-emitted surfaces) followed by
  `python -m tools.harness_emit` (D-14).
- **Removing `gate-registry.json` or its `DATA_CONTRACT_PATHS` entry.** Explicitly Phase 44's; doing
  it here breaks CER-08's own scope and desynchronizes the two phases' commit history.
- **Treating `RETIRED_SIGNATURES` as a one-way ratchet.** Per D-06/Phase-41 precedent: add the
  signature, let the re-emit drop the group, then **empty the tuple again** in the same phase — it is
  not a running log of everything ever retired, it is a transient drop mechanism.
- **Grepping `gate.needs` instead of parsing it as YAML.** GitHub Actions `needs:` is a YAML list;
  Phase 41's own D-14 (`ruamel.yaml`) is the established, dependency-free verification idiom — reuse
  it, do not add PyYAML.

## Don't Hand-Roll

Not applicable in the "avoid building a custom solution" sense used by greenfield research — this
phase's Don't-Hand-Roll instruction is the inverse: **do not build a replacement for anything being
removed.** Explicitly out of scope per CER-07/CONTEXT.md: a minimal state manager, a lifecycle shim,
a deprecation wrapper, a new "does this still work" test that exercises the deleted CLI surface, or
any successor mechanism for the five repaired commands (D-03: "removing the lifecycle step, not
replacing it").

**Key insight:** the single hardest discipline in this phase is negative — resisting the urge to
leave a thin compatibility layer "just in case." CER-07's own language ("unreachable in the product
by construction — not a shim, not a stub, not a deprecation path") and the milestone's binding
constraint (surface may not grow without retiring at least as much) both forbid it.

## Common Pitfalls

### Pitfall 1: `RETIRED_SIGNATURES` alone does not drop a settings.json group without a second commit's worth of test repair
**What goes wrong:** Removing `"tools.hooks.resume_gate"` from `HARNESS_SIGNATURES` and adding it to
`RETIRED_SIGNATURES` correctly makes the *emitter* drop the group on re-emit — but
`test_settings_coexist.py` and `test_coexist.py` both hardcode the group's presence and will fail
red immediately after re-emit if left unrepaired.
**Why it happens:** The signature-set mechanism (Phase 41's own fix, `merge.py:105-112`) only
controls what the emitter *writes*; it does nothing about what the *test suite expects*.
**How to avoid:** Repair both test files in the same Wave-1 commit that flips the signature sets, so
`uv run pytest -q` stays green through Wave 1's own verify step.
**Warning signs:** `uv run pytest -q` red on `test_harness_gates_registered_with_expected_matcher`
or `test_seeded_settings_json_reproduced_byte_for_byte` right after a re-emit.

### Pitfall 2: `DATA_CONTRACT_PATHS` is a 3-tuple with mixed lifetime — editing the wrong entry
**What goes wrong:** `transitions.json` and `gate-registry.json` sit in the same
`DATA_CONTRACT_PATHS` tuple in `tools/contract_hash/hash.py`. It is easy to either (a) remove both
(wrongly claiming Phase 44's item early) or (b) remove neither (leaving a stale hash-manifest key
for a file that no longer exists, which fails `contract-drift` the moment the schema file is `git
rm`'d).
**Why it happens:** The tuple has no per-entry phase annotation in code; only CONTEXT.md's prose
(D-05) and this research record which entry belongs to which phase.
**How to avoid:** Remove exactly `Path("harness/task-control/transitions.json")`; leave
`Path("harness/task-control/gate-registry.json")` and `Path("harness/security/deny-domains.json")`
untouched. Verify with `uv run python -m tools.contract_hash.hash --write` followed by
`uv run python -m tools.contract_drift.drift` (must exit 0) in the same commit as the schema `git
rm`.

### Pitfall 3: Deleting `.workflow/tasks/` before the emitter/tests that reference `active-task.json`'s sibling paths are repaired
**What goes wrong:** `tools/memory_regen/inject.py`'s `_active_task_pointer` reads
`.memory/state/active-task.json` (not `.workflow/tasks/` directly) but resolves a `handoff_path`
field that points INTO `.workflow/tasks/<id>/handoffs/...`. If `.workflow/tasks/` is deleted before
`_active_task_pointer` itself is deleted, any live `.memory/state/active-task.json` pointer (there
isn't one committed today — verified absent) would resolve to a path that no longer exists, tripping
the function's own fail-closed `except` branch. Not a live risk today (no committed
`active-task.json`), but a reason `_active_task_pointer` must be deleted in Wave 1, before
`.workflow/tasks/` is deleted in Wave 2 — reversing the order is harmless here only because no
pointer file is currently committed; do not rely on that being true at execution time without
re-checking `git ls-files .memory/state/active-task.json`.
**How to avoid:** Confirm `git ls-files .memory/state/active-task.json` is empty before Wave 2;
delete the pointer-reading function in Wave 1 regardless (it's already required by D-11).

### Pitfall 4: `git ls-files`-dependent code reports the plane as "gone" only after commit, not after `git rm`
**What goes wrong:** `tools/adoption_scan/destinations.py:217`'s `_tracked_repo_files()` (feeding
the `"tools/**/*"` install-catalogue row) reads `git ls-files` — a staged-but-uncommitted deletion is
still tracked (git only drops a path from `ls-files` after a commit, or after `git rm --cached` with
no re-add). Any test asserting the catalogue no longer contains the 8 packages will be **red between
`git rm` and `git commit`**, and this is expected, not a bug (D-12's own documented reason for
delete → stage → commit → verify → amend-if-red, not delete → verify → commit).
**How to avoid:** Never pause to "check the tests" mid-git-rm before committing; the correct order is
commit first, verify second, per D-12/D-13 verbatim.
**Warning signs:** A confusing red immediately after `git rm` and before `git commit` that
disappears the instant the commit lands — this is D-12 working as designed, not a defect to
investigate.

### Pitfall 5: `EXPECTED_SKILLS`/`EXPECTED_PAGES`-style anti-drift frozensets hard-fail BEFORE any file is written
**What goes wrong:** (Recorded by Phase 41, reconfirmed applicable here.) The emitter's
`check_skill_set()` raises `HarnessEmitError` the instant `harness/skills/<name>/` is deleted but
`caps.py`'s `EXPECTED_SKILLS` still lists it — before writing a single output byte. The analogous
risk exists for `docs_sync`'s render/prune tests against `EXPECTED_PAGES` (not an emitter hard-fail,
but a test hard-fail at the same causal moment: schema deleted, frozenset not yet shrunk).
**How to avoid:** Edit `caps.py`'s `EXPECTED_SKILLS` in the SAME commit as the 5 skill deletions,
and `test_docs_sync_determinism.py`'s `EXPECTED_PAGES` in the SAME commit as the 5 (of 6) schema
deletions (`transitions.json` has no docs_sync page, so only 5 of 6 contracts affect this
frozenset).
**Warning signs:** `HarnessEmitError: skill set drift — missing [...]` on the first post-deletion
`python -m tools.harness_emit` run.

## Code Examples

### D-06's `RETIRED_SIGNATURES` mechanism (already built, Phase 41; use it, then empty it again)
```python
# tools/harness_emit/merge.py — current state (2026-07-28), RETIRED_SIGNATURES empty
HARNESS_SIGNATURES: tuple[str, ...] = (
    "tools.hooks.format_on_write",
    "tools.hooks.contract_guard",
    "tools.hooks.secret_scan",
    "tools.hooks.commit_gate",
    "tools.hooks.resume_gate",      # <-- REMOVE this line
)
RETIRED_SIGNATURES: tuple[str, ...] = ()   # <-- becomes ("tools.hooks.resume_gate",) for this
                                            #     phase's Wave-1 commit, then back to () once the
                                            #     re-emit has landed (Phase-41 pattern, D-06)
```
Also delete the `{"matcher": "Write|Edit|Bash", "hooks": [{"command": _GUARD_PREFIX +
"uv run python -m tools.hooks.resume_gate", ...}]}` dict from `HARNESS_HOOK_GROUPS["PreToolUse"]`
(currently the last entry in that list, `merge.py:189-198`).

### `inject.py`'s exact goes/stays split (D-11)
```python
# STAYS verbatim — tools/memory_regen/inject.py:120-134
def _active_context_pointer(state_dir: Path = STATE_DIR) -> str:
    ...  # unchanged

# GOES entirely — tools/memory_regen/inject.py:137-167 (the whole function)
def _active_task_pointer(state_dir: Path = STATE_DIR) -> str:
    ...

# Also remove, now-unused after the function above is deleted:
#   - "import json" (line 11 — only consumer was _active_task_pointer:143)
#   - the tools.handoff import block (lines 16-22)
#   - TASK_HEADER constant (line 43)
#   - in assemble(): the `task = _active_task_pointer(state_dir)` call (line 180), the
#     `("task", task)` tuple in `sections` (line 186), and the `"task"` token in the
#     never-drop exemption on line 197 (`name not in ("agreements", "banner", "drift", "task")`)
```

### Test-file split for `test_inject_assembler.py`
```python
# DELETE (whole-function, they test _active_task_pointer only):
#   test_malformed_active_task_is_fail_closed_and_capped   (line ~167)
#   test_absent_active_task_is_normal_no_task_session       (line ~179)
#
# KEEP verbatim — these are the D-11/SC-6 pointer-survival proof, already written:
#   test_pointer_is_progress_log_not_imperative     (~98)  — asserts "progress log" in ACTIVE_HEADER
#   test_updated_stamp_surfaced_verbatim             (~104)
#   test_absent_stamp_degrades_gracefully            (~112)
#   test_active_context_is_pointer_not_body          (~124) — the strongest survival assertion:
#       reads the real repo_root fixture's .memory/state/activeContext.md and asserts the payload
#       contains the LITERAL STRING ".memory/state/activeContext.md" (a pointer), never the file's
#       own body content.
```

## State of the Art

Not a "current best practice drifted" domain — this is a single-repo, single-commit-window removal.
The one relevant precedent is internal: Phase 41 (docs-review plane) is the immediately-prior
same-shape deletion in this same repo, and every mechanism this phase reuses
(`RETIRED_SIGNATURES`, `EXPECTED_SKILLS` pre-write hard-fail, contract + manifest same-commit
rebaseline, `ruamel.yaml`-resolved `gate.needs` verification, committed-derived-plane regen as an
in-scope consequence rather than a deferred sweep) was built and proven there, not invented here.

**Deprecated/outdated:** none — nothing in this phase's mechanism set predates Phase 41; there is no
older approach being replaced.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `tools/harness_lint/tests/test_tests_are_isolatable.py`'s replacement literal for `"tools/lifecycle_eval/tests"` should be another member using the `tests/conftest.py` root-insertion idiom, but this research did not exhaustively verify which of the 19 surviving members use that idiom vs. self-insertion | Blast Radius item 5 | Low — a `grep -l sys.path.insert tools/*/tests/conftest.py` at implementation time resolves this in seconds; worst case the tuple is simply narrowed to one element (`"tools/harness_lint/tests"`), which the test's own assertion logic accepts |
| A2 | The exact post-deletion `git diff --stat` LOC total (D-18, "expect ≳7021") was not computed here — only the 8 packages' 7021 LOC (already measured by CONTEXT.md) plus contracts/commands/skills/toml/CI/state-dir sizes, which this research did not sum | Ordering/Gate Mechanics | None — D-18 requires measuring at execution time from `git diff --stat`, not estimating in research; explicitly "measured, not estimated" per D-18 itself |

## Open Questions

1. **Does `tools/ruff_baseline/baseline.json` need a `--update` run after this deletion?**
   - What we know: the ratchet (`tools/ruff_baseline/ratchet.py`) may only SHRINK counts and fails
     only on growth or a newly-appearing rule code; deleting 7021+ LOC can only lower per-rule
     counts, never raise them, so the CI `lint` job will not go red from this deletion alone.
   - What's unclear: whether leaving a now-looser-than-necessary baseline is acceptable or whether
     hygiene calls for `uv run python -m tools.ruff_baseline --update` in the same phase.
   - Recommendation: optional, not required for D-16's done-condition ("ruff ratchet clean" only
     requires the gate to pass, which it will unconditionally here); leave for the executing plan's
     discretion, defaulting to running `--update` since it's a one-line low-risk hygiene commit.

## Environment Availability

Skipped — this phase has no external tool/service/runtime dependency. It uses only `git`, `uv`
(already bootstrapped per every prior phase in this milestone), and `python3` (for
`workspace_check.py`, already a CI/hook precondition). No new dependency is introduced (CER-07's
own constraint).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.x (pinned `<9`), stdlib `tomllib`/`json` for structural checks |
| Config file | `pyproject.toml:37-39` (`[tool.pytest.ini_options]`, `testpaths = ["libs/python", "tools"]`) |
| Quick run command | `uv run pytest --collect-only -q` (0 errors = no dangling import) |
| Full suite command | `uv run pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CER-07 (deletion completeness) | No importer of a deleted module remains | collection | `uv run pytest --collect-only -q` | ✅ (existing pytest infra) |
| CER-07 (contract set) | `contracts/harness/task-control/` holds only `gate-registry.json` | structural | `uv run python -m tools.contract_drift.drift` (exit 0) | ✅ `tools/contract_drift/drift.py` |
| CER-07 (skill/command anti-drift) | `caps.py` declares no deleted skill | unit | `uv run pytest tools/harness_lint -q` | ✅ `tools/harness_lint/tests/test_skills.py` (existing) |
| CER-07 (CI fan-in) | 10-entry `gate.needs`, no `lifecycle-eval` | structural, YAML-resolved | `uv run python -c "from ruamel.yaml import YAML; ..."` (D-10, mirrors Phase 41's D-14 one-liner) | ➖ ad hoc, no persistent test file (matches Phase 41 precedent, which also ran this as a task acceptance check, not a committed test) |
| CER-07 / D-11 (pointer survival) | `inject.py` still emits the activeContext pointer after the active-task removal | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py -q` | ✅ (`test_active_context_is_pointer_not_body` already exists, verified above) |
| CER-07 (emit-drift / re-emit clean) | Both runtime trees match a fresh re-emit | structural | `python -m tools.harness_emit && git diff --exit-code` (CI's own `emit-drift` job shape) | ✅ existing CI job |

### Sampling Rate
- **Per task commit:** `uv run pytest --collect-only -q` (fast: catches the dangling-import class of
  break immediately, before running the full suite)
- **Per wave merge:** `uv run pytest -q` (full suite)
- **Phase gate:** full suite green + `contract-drift` exit 0 + YAML-resolved `gate.needs` check +
  `emit-drift`/`stale-derived`/ruff-ratchet clean before `/gsd:verify-work`

### Wave 0 Gaps
None — existing test infrastructure (pytest, `tools/contract_drift`, `tools/harness_lint`,
`tools/docs_sync`'s determinism suite, `ruamel.yaml` for `gate.needs`) covers every phase
requirement. No new test framework, fixture, or conftest is needed; this phase edits/deletes
existing tests, it does not need new test infrastructure stood up first.

## Security Domain

`security_enforcement` is not set to `false` in `.planning/config.json` (absent = enabled per the
default), but this phase removes no authentication/authorization/input-validation/crypto surface —
it deletes an in-session task-lifecycle gate system, which ADR-0012 already reclassifies as ceremony
rather than security. No ASVS category applies to a pure deletion of internal dev-tooling state
machinery. `V6 Cryptography` is not implicated (this plane held no secrets/crypto — that is
`secret_scan`, explicitly out of scope, Phase 44). No new threat pattern is introduced because no new
code is written. This section is intentionally sparse because the phase is subtractive.

## Sources

### Primary (HIGH confidence — read/grepped directly against the working tree, 2026-07-28)
- `.planning/phases/43-lifecycle-plane-removal/43-CONTEXT.md` — locked decisions D-01..D-18
- `.planning/ROADMAP.md` §"Phase 43: Lifecycle Plane Removal" — scope, 8 success criteria
- `.planning/REQUIREMENTS.md` — CER-07, CER-08 boundary
- `docs/adr/0012-ci-and-merge-as-decision-authority.md` — full text read, clause (b) deletion
  enumeration cross-checked against this research's own findings
- `.planning/phases/41-docs-review-plane-removal/41-03-SUMMARY.md`,
  `41-04-SUMMARY.md` — the `RETIRED_SIGNATURES` mechanism, `EXPECTED_SKILLS` hard-fail,
  contract-deletion + manifest-rebaseline procedure, in-scope derived-plane regen precedent
- Direct reads: `tools/harness_emit/merge.py`, `tools/memory_regen/inject.py`,
  `tools/contract_hash/hash.py`, `tools/harness_lint/caps.py`,
  `tools/harness_lint/tests/{test_tests_are_isolatable,test_workspace_member_completeness,
  test_capability_wiring,test_discipline_wiring}.py`, `tools/hooks/tests/test_settings_coexist.py`,
  `tools/harness_emit/tests/test_coexist.py`, `tools/contract_graph/tests/test_query.py`,
  `tools/docs_sync/tests/test_docs_sync_determinism.py`, `tools/adoption_scan/destinations.py`,
  `.github/workflows/ci.yml`, `harness/opencode.json`, `pyproject.toml`, `uv.lock`
- Exhaustive `grep -rnE` scans (commands shown inline above) across
  `harness/ .github/ AGENTS.md .memory/ libs/ examples/ .opencode/ .claude/ contracts/ docs/`

### Secondary (MEDIUM confidence)
- None used — every claim traces to a direct read or grep of this working tree; no WebSearch was
  needed (this phase's domain is entirely internal to the repo, not a public library/API question).

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Blast radius (deliverable 1): HIGH — every finding traces to a specific `file:line` grepped 2026-07-28
- Repair specs (deliverable 2): HIGH — read the actual current source of every file requiring repair
- Deletion order / gate mechanics (deliverables 3-4): HIGH — mirrors a proven, already-executed
  Phase-41 procedure in this same repo, cross-checked against this phase's specific files
- `inject.py` line ranges (deliverable 5): HIGH — read verbatim, current line numbers as of 2026-07-28
- Validation Architecture (deliverable 6): HIGH — existing test infra confirmed present, no gaps
- Risks/landmines (deliverable 7): HIGH — the conftest/wiring-test risks named in the task prompt
  were individually verified (found real issues in 2 of them, confirmed 1 a non-issue); the
  gate-registry.json $ref risk was checked (no schema `$ref`s a deleted task-control schema — the 6
  task-control schemas are self-contained per D-11 in Phase 26's precedent of "zero cross-file $ref")

**Research date:** 2026-07-28
**Valid until:** Effectively permanent for the deletion mechanics (internal, not externally-versioned
information) — but re-verify all `file:line` citations immediately before planning if any other
phase or plan lands between this research and Phase 43 execution, since line numbers will shift.
