# Phase 9: Self-Maintaining Derived Artifacts + Curator (v2.0 α) - Research

**Researched:** 2026-07-13
**Domain:** Self-maintaining derived-artifact plane — a read-mostly `curator` persona + CI "stale-derived" diff gate + local `/refresh-memory` wired over the EXISTING `tools/memory_regen` + `tools/docs_sync` generators and the Phase-7 emitter.
**Confidence:** HIGH (all reuse targets read directly from the live tree; no external dependencies)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Committed + PR-gated derived set = **`docs/reference/**` + `contracts-index`**. `docs/reference/**` is already committed; `contracts-index` **flips gitignored-derived → committed-derived** so the stale-derived gate can guard it.
- **D-02:** `repo-map` **stays gitignored / session-ephemeral** (SessionStart inject path), NOT committed, NOT gated (PageRank churn = noise).
- **D-03:** Planner resolves the exact tracked path for the now-committed `contracts-index` (today under gitignored `.memory/derived/`) and the paired `.gitignore` amendment (lines 17-19 ignore `.memory/derived/`). Two-plane invariant holds via machine-write + CI-verify (not human edits).
- **D-04:** Ship **both** `/refresh-memory` (entry point for humans, CI, `/verify-work`) **and** a read-mostly `curator` agent persona (delegatable by orchestrator/conductor).
- **D-05:** Curator write boundary = **derived paths only** (`docs/reference/**`, `contracts-index`, `.memory/derived/**`); **hard-deny** writes to constitution (`contracts/`, `docs/adr/`, `golden/`), source, any non-derived path. Derived from the read-only persona template (cf. `code-reviewer`/`explorer`); no constitution/golden write affordance.
- **D-06:** Curator regenerates ONLY by invoking existing tools (`tools/memory_regen` + `/docs-sync`) — never its own derivation logic, never hand-edits a derived artifact.
- **D-07:** Separate `stale-derived` CI job, mirroring Phase-7 `emit-drift`: regenerate committed-derived set + `git diff --exit-code`, fail on any diff. Kept distinct from `emit-drift`.
- **D-08:** On failure, print an **actionable, copy-pasteable fix message** (the exact local command to run, then commit).
- **D-09:** **No on-write memory hook.** Freshness = local `/refresh-memory` + PR/CI `stale-derived` gate. `format-on-write` already covers the cheap on-write class; SessionStart inject already refreshes session-derived. No heavy per-commit local regen.
- **D-10:** `/verify-work` incorporates the freshness check — runs the full regen set locally + diffs, catching drift pre-handoff (mirrors how it already composes lint + tests + contract-drift + golden).
- **D-11:** New `curator` agent + any new command/hook MUST round-trip the Phase-7 emitter to **both** runtimes (opencode primary, Claude secondary) from `harness/` source, carry **no model identifier**, keep the core example-independent (GEN-04 guard green).

### Claude's Discretion

- Exact CI job wiring, command file layout, and the precise tracked path for the flipped `contracts-index` are implementation details for the planner/researcher — the decisions above fix the WHAT and boundaries, not the file-level HOW.

### Deferred Ideas (OUT OF SCOPE)

- **Committing/gating `repo-map`** — deliberately NOT gated now (PageRank churn). Revisit only with a churn-tolerant (order-insensitive/set-based) diff.
- Fan-out/synthesize orchestration → Phase 10 (ECON). Multi-repo workspace → Phase 11 (MREPO).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MAINT-01 | `curator` agent — read-mostly, sole "derived freshness" owner; regenerates only, never hand-edits (reuses `tools/memory_regen`, `/docs-sync`, two-plane-memory) | New `harness/agents/curator.md` derived from the read-only persona shape (§Standard Stack, §Pattern 1); write boundary enforced by the global `path_deny_globs` constitution deny (§Architecture) |
| MAINT-02 | CI "stale-derived" gate — regenerate committed-derived set on PR, FAIL on diff (mirror Phase-7 re-emit-diff). Which artifacts are committed-vs-session = plan-time KEY DECISION (resolved by D-01/D-02) | New `stale-derived` job in `.github/workflows/ci.yml` cloning the `emit-drift` job shape (§Pattern 2); untracked-file + prune pitfalls flagged (§Common Pitfalls P1/P2) |
| MAINT-03 | Hook posture — cheap on-write refresh only; heavy regen deferred to PR/CI (no per-commit heavy hook) | No new on-write hook (D-09); reuse existing `format-on-write` + SessionStart inject; validation asserts absence (§Validation) |
| MAINT-04 | `/refresh-memory` (or curator invocation) — run full regen set locally pre-handoff so `/verify-work` includes a freshness check | New `harness/commands/refresh-memory.md` (macro over generators, §Pattern 3) + a freshness step spliced into `harness/commands/verify-work.md` (§Pattern 4) |
</phase_requirements>

## Summary

This is a **thin-layer, reuse-not-rebuild** phase. Every generator it needs already exists and is deterministic: `tools/memory_regen/contracts_index.py` (contracts-index), `tools/docs_sync/generate.py` (docs/reference), `tools/memory_regen/repo_map.py` (repo-map, stays session-only), and `tools/memory_regen/inject.py` (SessionStart payload). The Phase-7 emitter (`tools/harness_emit`) already projects any new `harness/agents/*.md` + `harness/commands/*.md` to both runtimes with loud-fail validators, and the Phase-6 CI already carries an `emit-drift` job whose regenerate→`git diff --exit-code`→fail-on-diff shape is the exact template for the new `stale-derived` job. The phase adds four thin things: (1) a `curator` persona, (2) a `/refresh-memory` command, (3) a `stale-derived` CI job, (4) a freshness step in `/verify-work` — plus the D-03 flip of `contracts-index` from gitignored to committed.

Two concrete unknowns are resolved here. **The `contracts-index` tracked path:** keep the generator's `INDEX_PATH` unchanged at `.memory/derived/contracts-index.md` and amend `.gitignore` to `.memory/derived/*` + `!.memory/derived/contracts-index.md` — the minimal-blast-radius option because `inject.py` reads that exact path and needs no change, while `repo-map.md` stays ignored (git's "cannot re-include a file under an excluded directory" rule forces `/*` not `/`). **The emitter registration:** `curator.md` drops into `harness/agents/` (auto-discovered by the non-recursive `iter_agents` glob) and `refresh-memory.md` into `harness/commands/` (auto-discovered by `iter_commands`); the only source-of-truth edit is bumping `EXPECTED_PERSONAS` 4→5 in `tools/harness_lint/caps.py`, then re-emitting to regenerate `emit-manifest.json` + both runtime trees.

**One critical pre-existing hazard blocks a green gate:** the committed `docs/reference/` is currently OUT OF SYNC with root `contracts/`. It carries four orphaned domain pages (`correction-rules.md`, `equipment-master.md`, `equipment-progress.md`, `standard-log.md` — left behind by the Phase-5 domain move to `examples/`) and is MISSING `greeting.md`. A `stale-derived` gate would red immediately on today's tree. Wave 0 must reconcile this (delete orphans, commit `greeting.md`) AND `docs_sync` needs a prune step so a deleted contract's page is removed, not orphaned. See §Common Pitfalls P1/P2.

**Primary recommendation:** Author `curator.md` + `refresh-memory.md` in `harness/`, bump `EXPECTED_PERSONAS`, re-emit; add a `docs_sync` prune-then-write; reconcile `docs/reference/` in Wave 0; then add a `stale-derived` CI job that regenerates the committed-derived set and fails on any diff **including untracked/new files** (`git add -A` + `git diff --cached --exit-code`, NOT bare `git diff`), and splice the same regen+diff into `/verify-work`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Derived regeneration (contracts-index, docs/reference, repo-map) | Generators (`tools/memory_regen`, `tools/docs_sync`) | — | Derivation logic already exists and is deterministic; curator/command NEVER re-implement it (D-06) |
| "Derived freshness" ownership / delegation | Agent persona (`harness/agents/curator.md`) | Command (`/refresh-memory`) | Curator is a read-mostly invoker; the command is the runtime-independent entry point (D-04) |
| Freshness enforcement at merge | CI (`.github/workflows/ci.yml` → `stale-derived` job) | — | Machine-write + CI-verify satisfies derived-never-hand-edited (MAINT-02); non-bypassable |
| Freshness enforcement pre-handoff (local) | Command (`/verify-work` freshness step, `/refresh-memory`) | — | Catches drift in-session before CI (D-10) |
| Curator write-boundary (derived-only, constitution-deny) | Permission data (`harness/permission-matrix.json` `path_deny_globs`) + contract-guard hook | Persona frontmatter (advisory) | opencode `edit` is not path-globbable, so path denies are global data enforced by the Phase-4 hook (D-05) |
| Dual-runtime projection of curator + command | Emitter (`tools/harness_emit`) | Caps SSOT (`tools/harness_lint/caps.py`) | Single-source → both runtimes, loud-fail validators, no model id (D-11) |
| Session-derived refresh on open (repo-map) | SessionStart inject (`inject.py` + Claude hook / opencode plugin) | — | Already refreshes session-derived; no on-write hook needed (D-02/D-09) |

## Standard Stack

**No new external packages.** This phase composes existing internal modules and the existing pinned toolchain. `[VERIFIED: repo tree]` — every module below was read directly from the working tree this session.

### Core (existing modules the curator/command/gate wire over)
| Module / Path | Purpose | Reuse role | Provenance |
|---------------|---------|------------|------------|
| `tools/memory_regen/contracts_index.py` | contracts-index generator (reuses `contract_hash` + `contract_drift`); `INDEX_PATH = .memory/derived/contracts-index.md` | The artifact that FLIPS to committed (D-01/D-03); invoked verbatim by curator/`/refresh-memory` | `[VERIFIED: repo tree]` |
| `tools/docs_sync/generate.py` | `contracts/**/*.schema.json` → `docs/reference/<name>.md`; deterministic, `_confine`d, one page per schema | Regenerates the already-committed `docs/reference/**` half of the gated set; **needs a prune step added** (P2) | `[VERIFIED: repo tree]` |
| `tools/memory_regen/repo_map.py` | tree-sitter → networkx PageRank → `.memory/derived/repo-map.md` | Stays session-ephemeral (D-02); run by `/refresh-memory` locally but NOT gated | `[VERIFIED: repo tree]` |
| `tools/memory_regen/inject.py` | SessionStart payload assembler; reads `.memory/derived/contracts-index.md` head | Unchanged if the flip keeps `INDEX_PATH` (argues for the gitignore-negation path option) | `[VERIFIED: repo tree]` |
| `tools/harness_emit/` (`generate.py`, `validate.py`, `project_agent.py`, `project_command.py`, `manifest.py`) | Single-source → dual-runtime emitter; `iter_agents`/`iter_commands` auto-discover `harness/agents/*.md` + `harness/commands/*.md` | Projects `curator.md` + `refresh-memory.md` to both trees; prune-then-writes `emit-manifest.json` | `[VERIFIED: repo tree]` |
| `tools/harness_lint/caps.py` | SSOT for `EXPECTED_PERSONAS`, `EXPECTED_SKILLS`, `READ_ONLY_PERSONAS`, cap constants, `is_read_only()` | Bump `EXPECTED_PERSONAS` 4→5 to admit `curator` (single edit lands in lints + emit validators) | `[VERIFIED: repo tree]` |
| `harness/permission-matrix.json` | 15-key permission + `path_deny_globs` (`contracts/**`, `docs/adr/**`, `golden/**`, `*.env`) | Curator's constitution write-deny is ALREADY enforced globally here — no per-persona path glob needed | `[VERIFIED: repo tree]` |
| `.github/workflows/ci.yml` (`emit-drift` job, lines 179-189) | Re-emit → `git diff --exit-code -- <paths>` fail-on-diff | The exact clone target for the new `stale-derived` job (D-07) | `[VERIFIED: repo tree]` |

### Supporting (personas/commands the curator + command derive from)
| Source | Role model for | Notes |
|--------|----------------|-------|
| `harness/agents/code-reviewer.md`, `harness/agents/explorer.md` | Read-mostly persona shape (D-05) | Dual-representation frontmatter (opencode `permission:` + Claude `tools:`); curator differs by ALLOWING `edit`/`bash` (needs to write derived + run generators) so it is NOT in `READ_ONLY_PERSONAS` |
| `harness/commands/orient.md` | `/refresh-memory` shape (D-04) | Already runs `repo_map` + `contracts_index` + `inject`; `/refresh-memory` is the superset that ALSO runs `docs_sync` |
| `harness/commands/docs-sync.md`, `harness/commands/verify-work.md` | `/docs-sync` macro + the `/verify-work` composite gate to splice into (D-10) | `verify-work.md` already composes lint+test+contract-drift+golden as numbered `!`shell`` steps |
| `harness/skills/two-plane-memory/SKILL.md` | The plane semantics the curator honors | Must be updated: `contracts-index` moves from "gitignored" to a new "committed-derived (machine-write + CI-verify)" sub-tier |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `.gitignore` `.memory/derived/*` + `!…contracts-index.md` (keep `INDEX_PATH`) | Move `INDEX_PATH` to a tracked path (e.g. `.memory/contracts-index.md`) | Moving the path forces edits to `inject.py`, the determinism test, and the two-plane skill; the negation keeps `inject.py` untouched. **Recommend negation** (minimal blast radius). See §Pitfall P3 for the git re-include gotcha. |
| Curator as a real emitted persona in `harness/agents/` | Curator as a `harness/agents/templates/` scaffold (like `component-engineer`) | Templates are fill-in scaffolds, NOT emitted personas; curator is a concrete delegatable agent → belongs in `harness/agents/` and bumps `EXPECTED_PERSONAS`. |
| Add prune to `docs_sync` generator | Let the `stale-derived` gate delete orphans | Putting prune in the generator makes "delete a contract → its page disappears" a first-class deterministic behavior the local `/refresh-memory` also gets; a gate-only prune is invisible locally. **Recommend generator prune.** |

**Installation:** None. `uv sync --all-packages` already resolves every module (all are in-repo uv members). No `npm view` / `pip index` needed — zero external packages added.

## Package Legitimacy Audit

**Not applicable — this phase installs no external packages.** All reuse targets are in-repo uv workspace members (`tools/*`, `libs/python`) already present and locked in `uv.lock`. No registry lookup, slopcheck, or postinstall audit required.

## Architecture Patterns

### System Architecture Diagram

```
                      contracts/**/*.schema.json  (constitution plane — human-owned, gated)
                                  │
              ┌───────────────────┼────────────────────────┐
              ▼                   ▼                          ▼
   contract_hash / drift   docs_sync.generate         (session only)
              │                   │                    repo_map (tree-sitter→PageRank)
              ▼                   ▼                          │
   contracts_index.py     docs/reference/<name>.md           ▼
   .memory/derived/          (COMMITTED-derived)     .memory/derived/repo-map.md
   contracts-index.md                                 (GITIGNORED — D-02, NOT gated)
   (FLIPS → COMMITTED-derived, D-01/D-03)                    │
              │                   │                          ▼
              └─────────┬─────────┘                   inject.assemble() → SessionStart payload
                        │  = committed-derived set (the GATED scope)
       ┌────────────────┼─────────────────────────────────┐
       ▼                ▼                                   ▼
  curator agent   /refresh-memory (local)            CI stale-derived job (PR)
  (read-mostly    regen full set → diff              regen committed-derived set
   invoker,       (pre-handoff, D-4/D-10)            → `git add -A` + `git diff --cached
   derived-only            │                            --exit-code` → FAIL on any diff
   D-05/D-06)              ▼                            + actionable message (D-07/D-08)
       │           /verify-work step 5                        │
       │           (freshness check)                          ▼
       └──────────── all authored in harness/ ────────► emitter → .opencode/ + .claude/
                     (curator.md, refresh-memory.md)   (D-11: both runtimes, no model id,
                                                         GEN-04 core stays example-free)
```

The committed-derived set (`docs/reference/**` + `contracts-index`) is the EXACT scope of the `stale-derived` diff gate; the gitignored `repo-map` is outside it. Keep the two in lockstep (anything committed-derived is gated; anything gitignored-derived is not — §Specifics).

### Recommended Source Layout (additions only)
```
harness/
├── agents/
│   └── curator.md              # NEW — read-mostly persona (dual-representation frontmatter)
├── commands/
│   └── refresh-memory.md       # NEW — macro over the full regen set (agent: curator)
├── commands/verify-work.md     # EDIT — splice a "freshness" numbered step (D-10)
├── permission-matrix.json      # (unchanged — path_deny_globs already denies constitution)
└── skills/two-plane-memory/SKILL.md   # EDIT — add committed-derived sub-tier

tools/
├── harness_lint/caps.py        # EDIT — EXPECTED_PERSONAS 4→5 (add "curator")
└── docs_sync/generate.py       # EDIT — add prune-then-write (delete orphaned pages)

.github/workflows/ci.yml        # EDIT — add `stale-derived` job + add to `gate.needs`
.gitignore                      # EDIT — `.memory/derived/*` + `!…contracts-index.md`
docs/reference/                 # WAVE 0 — delete 4 orphan pages, commit greeting.md
```

### Pattern 1: Read-mostly persona with a narrow write affordance
**What:** Author `curator.md` on the `code-reviewer`/`explorer` shape but grant the minimum needed to write derived + run generators.
**When to use:** MAINT-01 curator persona.
**Example (authored source — dual-representation frontmatter):**
```markdown
---
name: curator
description: >-
  Use to refresh the derived plane — regenerates repo-map, contracts-index, and docs/reference
  by invoking tools/memory_regen + /docs-sync, then diffs. Writes ONLY derived paths; never edits
  a contract, ADR, golden baseline, or source. Delegatable owner of derived freshness.
mode: subagent
permission:
  read: allow
  edit: allow        # needed to write the derived set; constitution is denied globally via path_deny_globs
  bash: allow        # needed to run `uv run python -m tools.memory_regen.* / tools.docs_sync`
  write: deny
# NOTE: no `model:` key, or exactly the placeholder tier — no real model id (D-11 / T-07-03)
tools: Read, Grep, Glob, Edit, Bash
---
```
- **Boundary source of truth:** `harness/permission-matrix.json` `path_deny_globs` already denies `contracts/**`, `docs/adr/**`, `golden/**`, `*.env` for ALL personas (the Phase-4 contract-guard hook enforces it). The curator inherits that deny — its "derived-only" boundary is a fact of the global data, not a per-persona glob (opencode's `edit` key is not path-globbable; matrix `_note` confirms). `[CITED: harness/permission-matrix.json line 2 _note]`
- **NOT read-only:** curator is deliberately excluded from `READ_ONLY_PERSONAS` (it writes derived). `is_read_only()` (caps.py) will return False — correct.

### Pattern 2: `stale-derived` CI job (clone of `emit-drift`)
**What:** A separate job that regenerates the committed-derived set and fails on any diff.
**When to use:** MAINT-02 / D-07.
**Example (mirror of ci.yml `emit-drift`, lines 179-189, with the untracked-file fix):**
```yaml
  stale-derived:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7.0.0
      - uses: astral-sh/setup-uv@v8.3.2
      - name: Sync workspace (all packages)
        run: uv sync --all-packages
      - name: Regenerate the committed-derived set
        run: |
          uv run python -m tools.docs_sync
          uv run python -m tools.memory_regen.contracts_index
      - name: Fail on any stale-derived drift (tracked mods AND new/untracked pages)
        run: |
          git add -A -- docs/reference .memory/derived/contracts-index.md
          if ! git diff --cached --exit-code -- docs/reference .memory/derived/contracts-index.md; then
            echo "::error::Derived plane is STALE. Run locally then commit:"
            echo "    /refresh-memory   (or: uv run python -m tools.docs_sync && uv run python -m tools.memory_regen.contracts_index)"
            echo "    git add docs/reference .memory/derived/contracts-index.md && git commit"
            exit 1
          fi
```
- **Add `stale-derived` to `gate.needs`** (ci.yml line 198) so the fan-in gate covers it.
- **Why `git add -A` + `git diff --cached`, not bare `git diff`:** a NEWLY-created page (e.g. `greeting.md` today) is untracked and bare `git diff --exit-code` does NOT see it — the gate would pass while the tree is stale (§Pitfall P1). The `emit-drift` job avoids this only because its outputs are all already tracked; the derived set is not (yet).

### Pattern 3: `/refresh-memory` — macro over the full regen set (no new logic)
**What:** Thin command (like `/orient` + `docs_sync`) that shells out to the generators.
**When to use:** MAINT-04 / D-04.
**Example (authored source):**
```markdown
---
description: >-
  Use before handoff to refresh the derived plane — regenerates repo-map, contracts-index, and
  docs/reference by invoking the existing generators, then leaves the tree ready to commit. The
  local counterpart of the CI stale-derived gate.
agent: curator
subtask: true
---
# /refresh-memory — regenerate the full derived set locally

## 1. Session-derived (gitignored — free to rebuild)
!`uv run python -m tools.memory_regen.repo_map`

## 2. Committed-derived (the gated set — commit after)
!`uv run python -m tools.docs_sync && uv run python -m tools.memory_regen.contracts_index`

## 3. Refresh the SessionStart payload
!`uv run python -m tools.memory_regen.inject`
```
- Auto-discovered by `iter_commands` (non-recursive `harness/commands/*.md` glob). `project_command` keeps `agent`+`subtask` for opencode, drops them for Claude. `[VERIFIED: repo tree — project_command.py]`
- `check_command` (validate.py) requires `agent` to be a well-formed slug → `curator` qualifies.

### Pattern 4: Splice a freshness step into `/verify-work`
**What:** Add a numbered step to `harness/commands/verify-work.md` that runs the committed-derived regen and diffs — mirroring the local half of the CI gate.
**When to use:** MAINT-04 / D-10.
**Example (new step appended to the existing 4):**
```markdown
## 5. Derived freshness (mirror of the CI stale-derived gate)
!`uv run python -m tools.docs_sync && uv run python -m tools.memory_regen.contracts_index; git add -A -- docs/reference .memory/derived/contracts-index.md; git diff --cached --exit-code -- docs/reference .memory/derived/contracts-index.md || { echo 'FAIL: derived plane stale — commit the regenerated docs/reference + contracts-index'; exit 1; }`
```
- Keep it presence-safe/announced like the existing `/golden` step so a bare template with no contracts still exits 0.

### Anti-Patterns to Avoid
- **Curator with its own derivation logic** — D-06 forbids it; the curator ONLY invokes `tools/memory_regen` + `/docs-sync`. A second index/hash impl could silently disagree with the drift gate (the exact reason `contracts_index.py` reuses `contract_hash`/`contract_drift`).
- **Gating `repo-map`** — D-02: PageRank ranking churns on unrelated edits → the gate would red on noise. Keep it gitignored/session-only.
- **A heavy per-commit / on-write memory hook** — D-09/MAINT-03: regeneration is deferred to PR/CI + local `/refresh-memory`; the on-write path stays `format-on-write`-cheap.
- **Bare `git diff --exit-code` for a set that can gain NEW files** — misses untracked pages (P1).
- **Moving `contracts-index` to a tracked path without updating `inject.py`** — `inject._contracts_summary` reads `.memory/derived/contracts-index.md` by that exact path.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Regenerate contracts-index | A new index/hash walker | `tools.memory_regen.contracts_index` (reuses `contract_hash`+`contract_drift`) | A second hash impl silently diverges from the drift gate (drift laundering) |
| Regenerate reference docs | A new schema→markdown renderer | `tools.docs_sync` | Deterministic, `_confine`d, DERIVED-marked, snapshot-tested already |
| Project curator/command to runtimes | A hand-written `.opencode/`+`.claude/` copy | `tools.harness_emit` (`python -m tools.harness_emit`) | Loud-fail validators, byte-identical re-emit, manifest ownership, no-model-id gate |
| Fail-on-diff CI gate | A bespoke comparison script | Clone the `emit-drift` job (regenerate → `git diff --cached --exit-code`) | Proven Phase-7 pattern; consistent contributor UX |
| Enforce curator's constitution write-deny | A per-persona path allow/deny list | Existing `path_deny_globs` + Phase-4 contract-guard hook | Global data already denies `contracts/**`/`docs/adr/**`/`golden/**` for every persona |

**Key insight:** The only genuinely NEW code in this phase is (a) a `docs_sync` prune step and (b) YAML/markdown authoring. Everything else is composition of Phase 1-8 machinery.

## Runtime State Inventory

> Included because D-01/D-03 flip an artifact from gitignored to committed (a state-boundary change). Scope is repo-local; no external datastores.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `contracts-index` currently written to gitignored `.memory/derived/contracts-index.md`. No external DB/datastore holds it. | Code: flip `.gitignore` so this file is tracked (keep `INDEX_PATH`), then commit the generated file. Wave 0 must generate + commit it once. |
| Live service config | None — verified: no external service (n8n/Datadog/etc.) references this repo's derived plane. The only "live config" is `.github/workflows/ci.yml` (in git). | Add `stale-derived` job + add to `gate.needs` (in-git edit). |
| OS-registered state | None — verified: no Task Scheduler / pm2 / systemd registration references derived artifacts. | None. |
| Secrets/env vars | `GOLDEN_APPROVE_HUMAN` (constitution ratification token) is unrelated to the derived plane; curator never touches constitution so never needs it. `path_deny_globs` also denies `*.env`. | None. |
| Build artifacts | `tools/harness_emit/emit-manifest.json` (tracked) lists every emitted path; it is prune-then-written by the emitter and MUST be regenerated + committed after adding curator + refresh-memory. Stale `docs/reference/` domain pages (4 files) are orphaned build artifacts. | Re-emit → commit `emit-manifest.json` + both runtime trees. Wave 0: delete the 4 orphan pages, commit `greeting.md`. |

**The canonical question — after every file is updated, what still holds the old string/state?** Answer: only the developer's existing local clone would still gitignore `contracts-index.md`; a `git rm --cached` is not needed (it was never tracked), just add + commit. No cache/registration outside the repo.

## Common Pitfalls

### Pitfall P1: Bare `git diff` misses newly-created derived files
**What goes wrong:** The `emit-drift` job uses `git diff --exit-code -- <paths>`, which only sees modifications to TRACKED files. A brand-new derived page (e.g. `greeting.md`, currently untracked) is invisible → the gate passes while the tree is stale.
**Why it happens:** The committed-derived set can GAIN files (a new contract → a new page); `emit-drift`'s outputs are all pre-tracked, so it never hit this.
**How to avoid:** `git add -A -- <paths>` then `git diff --cached --exit-code -- <paths>` (or check `git status --porcelain -- <paths>`).
**Warning signs:** Gate green but `docs/reference/` missing a page for a known schema.

### Pitfall P2: `docs_sync` never prunes orphaned pages
**What goes wrong:** `docs_sync.write()` writes one page per CURRENT schema but never deletes pages for REMOVED schemas. Today `docs/reference/` holds four orphans (`correction-rules.md`, `equipment-master.md`, `equipment-progress.md`, `standard-log.md`) from the Phase-5 domain move — they persist forever and a "delete a contract" change won't surface a diff. `[VERIFIED: repo tree — ran `python -m tools.docs_sync`; 2 pages written, 4 orphans untouched]`
**Why it happens:** The generator has no prune-then-write (unlike `tools.harness_emit.manifest.prune_then_write`).
**How to avoid:** Add prune-then-write to `docs_sync`: enumerate `<name>.md` pages under `docs/reference/`, delete any whose `<name>` is not in the current schema set (preserve `README.md`). Wave 0 deletes today's 4 orphans + commits `greeting.md` so the baseline is clean.
**Warning signs:** `stale-derived` gate red on first run listing the 4 domain pages / missing greeting.

### Pitfall P3: git cannot re-include a file under an excluded directory
**What goes wrong:** Naively adding `!.memory/derived/contracts-index.md` under the existing `.memory/derived/` rule does nothing — git ignores the whole directory and "it is not possible to re-include a file if a parent directory of that file is excluded." `[CITED: git-scm gitignore docs]`
**Why it happens:** `.memory/derived/` (trailing slash) excludes the directory itself, blocking descent.
**How to avoid:** Change the rule to exclude CONTENTS not the directory: `.memory/derived/*` then `!.memory/derived/contracts-index.md`. `repo-map.md` stays ignored via `*`; `contracts-index.md` is re-included.
**Warning signs:** `git check-ignore .memory/derived/contracts-index.md` still reports it ignored after the amendment.

### Pitfall P4: `EXPECTED_PERSONAS` anti-sprawl gate reds on the new persona
**What goes wrong:** `test_agents.py` asserts the discovered persona set `== EXPECTED_PERSONAS` (currently exactly 4). Dropping `curator.md` into `harness/agents/` without editing `caps.py` reds the suite.
**Why it happens:** Deliberate anti-sprawl gate (P8) — a new persona is a conscious decision, not an accident.
**How to avoid:** Bump `EXPECTED_PERSONAS` 4→5 in `tools/harness_lint/caps.py` (single SSOT; the emit validator imports it). Keep `READ_ONLY_PERSONAS` unchanged (curator is not read-only). The single-primary gate stays satisfied (curator is `mode: subagent`, orchestrator remains the sole primary). `[VERIFIED: repo tree — caps.py:54, test_agents.py:60]`
**Warning signs:** `test_agents` / emit `check_agent` failing with "persona set drift".

### Pitfall P5: A real model identifier or example token leaks into the emitted curator
**What goes wrong:** Emitter loud-fails if a persona/command carries a real `model:` value (must be `provider/<tier>-tier` placeholder) or the GEN-04 guard reds if any core file names an example.
**Why it happens:** D-11 non-negotiables (no model id, core stays example-free).
**How to avoid:** Omit `model:` (or use the placeholder tier). Keep `curator.md`/`refresh-memory.md` domain-neutral — no `examples/`, `equipment`, `standard-log`, `dotnet-engineer`, etc. (the GEN-04 `_PROSE_TOKENS` list). `[VERIFIED: repo tree — validate.check_agent, test_core_no_example_dep.py]`
**Warning signs:** `HarnessEmitError` on model id; `test_core_has_no_example_dependency` offenders list.

### Pitfall P6: Non-deterministic derived output flaps the gate
**What goes wrong:** Any timestamp/float/unsorted output makes regenerate→diff red spuriously.
**Why it happens:** The gate demands byte-identical regeneration.
**How to avoid:** Reuse the generators UNCHANGED — they are already timestamp-free, sorted, and snapshot-proven (`contracts_index.render`, `docs_sync.render`). Do not add any new rendering. If prune is added to `docs_sync`, ensure deterministic ordering of deletes (no effect on output bytes, but keep the write path stable).
**Warning signs:** `stale-derived` red with a diff showing only reordering/whitespace.

## Code Examples

### Verify the current `.gitignore` amendment works
```bash
# Source: repo tree (.gitignore line 19 today: ".memory/derived/")
# After amending to ".memory/derived/*" + "!.memory/derived/contracts-index.md":
git check-ignore .memory/derived/repo-map.md          # expect: still ignored (prints path)
git check-ignore .memory/derived/contracts-index.md   # expect: NOT ignored (empty, exit 1)
```

### Regenerate + re-emit sequence (what Wave 0 / the gate run)
```bash
# Source: repo tree — verified module entrypoints
uv run python -m tools.docs_sync                       # docs/reference/*.md (add prune)
uv run python -m tools.memory_regen.contracts_index    # .memory/derived/contracts-index.md
uv run python -m tools.harness_emit                    # re-emit both runtime trees + manifest
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `contracts-index` gitignored, proven only by a committed syrupy snapshot | `contracts-index` committed-derived, proven by the `stale-derived` `git diff` gate | This phase (D-01/D-03) | The snapshot test can stay, but the gate becomes the primary freshness signal |
| `docs_sync` writes-only (no prune) | `docs_sync` prune-then-write | This phase (P2) | Deleted contracts' pages are removed, not orphaned |
| Freshness "advised" by two-plane-memory prose | Freshness ENFORCED by CI gate + `/verify-work` step | This phase (MAINT-02/04) | Machine-gate replaces tribal "remember to regen" |

**Deprecated/outdated:** The four `docs/reference/` domain pages (`correction-rules`, `equipment-master`, `equipment-progress`, `standard-log`) are stale artifacts of the pre-Phase-5 tree — delete in Wave 0.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The gitignore-negation path option (keep `INDEX_PATH`, amend `.gitignore`) is preferred over moving the file to a tracked path | Standard Stack / Alternatives | LOW — both work; negation minimizes edits. If the team prefers a non-`derived/` tracked location, `inject.py` + the determinism test + two-plane skill must also change. This is a Claude's-Discretion call (D-03) — surface to planner. |
| A2 | Adding a command does NOT trip an exact-count gate | Pitfall P4 / Validation | LOW — `test_commands.py` uses a SUBSET check (`EXPECTED_GOLDEN_ADJACENT - names`), not exact equality, so `refresh-memory` won't red it. `[VERIFIED: repo tree — test_commands.py:42,59]` Confirm no other exact command-count assertion exists at plan time. |
| A3 | `docs/reference/**` is the full committed-derived docs scope (root only; example instances have no `docs/reference/` today) | Architecture / Pattern 2 | LOW — verified `examples/log-parser/docs/reference/` does not exist. If an instance later needs its own reference sync, the gate scope widens (future phase). |
| A4 | The curator needs `edit: allow` + `bash: allow` (not read-only) to write derived + run generators | Pattern 1 | LOW — writing `docs/reference/` and running `uv`/`python` both require these; constitution stays denied via `path_deny_globs`. If the team wants curator to delegate writes to an engineer instead, revisit. |

## Open Questions

1. **Exact tracked path for `contracts-index` (D-03).**
   - What we know: keeping `INDEX_PATH` + `.gitignore` `.memory/derived/*` negation is lowest-blast-radius (`inject.py` untouched).
   - What's unclear: whether the team prefers the committed-derived artifact to live under `.memory/derived/` (co-located with session-derived, split by gitignore) or at a visibly-tracked path outside `derived/`.
   - Recommendation: go with the negation option; document the committed-derived sub-tier in the `two-plane-memory` skill so the "why is one file in derived/ tracked" is explicit.

2. **Should `/refresh-memory` regenerate `repo-map` (session-only) too?**
   - What we know: `/orient` already regenerates repo-map + contracts-index + inject; repo-map is NOT gated (D-02).
   - What's unclear: whether "full regen set" (MAINT-04) includes the ungated repo-map.
   - Recommendation: YES — `/refresh-memory` runs repo-map (local convenience) but the CI gate + `/verify-work` diff step cover ONLY the committed-derived set (docs/reference + contracts-index). Local runs everything; the gate guards only what's committed.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | All generator/emitter invocations | ✓ | present (workspace resolves) | — |
| Python 3 + tree-sitter/networkx (pinned) | `repo_map` (session-only) | ✓ | pinned in uv.lock (02-01) | repo-map is session-only; not gated |
| git | `stale-derived` gate + `emit-drift` | ✓ | repo is a git repo | — |
| .NET 10 SDK | NOT needed by this phase | ✗ | — | Irrelevant — derived generators are pure-Python; golden/.NET is out of scope here |

**Missing dependencies with no fallback:** None — the phase is Python + git + YAML only.
**Missing dependencies with fallback:** .NET absence is irrelevant to derived-artifact regeneration.

## Validation Architecture

> `workflow.nyquist_validation: true` in `.planning/config.json` — section included.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (uv workspace; root `testpaths = tools/ + libs/python`) |
| Config file | `pyproject.toml` (root) + per-member `pyproject.toml` |
| Quick run command | `uv run pytest tools/harness_emit tools/harness_lint tools/docs_sync tools/memory_regen -x` |
| Full suite command | `uv run pytest` (non-example core suite) |
| Phase gate | Full core suite green + `stale-derived`/`emit-drift`/GEN-04 jobs green before `/verify-work` |

### Success Criterion / Requirement → Test Map
| Signal | Behavior | Type | Automated Command / Assertion | Exists? |
|--------|----------|------|-------------------------------|---------|
| SC1 / MAINT-01 | `curator` persona exists, read-mostly, derived-only | unit | `test_agents.py`: `EXPECTED_PERSONAS == {…, "curator"}`; assert curator NOT in `READ_ONLY_PERSONAS`; assert constitution paths in `path_deny_globs` | ❌ Wave 0 (bump caps + add assertion) |
| SC1 / D-06 | Curator body invokes ONLY existing tools (no new derivation) | unit | New test scanning `harness/agents/curator.md` + `refresh-memory.md` bodies reference only `tools.memory_regen`/`tools.docs_sync` module paths | ❌ Wave 0 |
| SC2 / MAINT-02 | `stale-derived` job regenerates + fails on diff | ci-assert + unit | CI job present in `ci.yml` and in `gate.needs`; negative-control test: mutate a committed page → `git diff --cached --exit-code` fails; clean tree → passes | ❌ Wave 0 |
| SC2 / P2 | `docs_sync` prunes orphaned pages | unit | `test_docs_sync_*`: create a stray `docs/reference/x.md` with no schema → `write()` removes it; `README.md` preserved | ❌ Wave 0 (new prune test) |
| SC3 / MAINT-03 | No new heavy on-write memory hook | unit | Test asserting `.claude/settings.json` hook groups + `harness/plugins/*.ts` contain NO `memory_regen`/`docs_sync` invocation on Pre/PostToolUse write path | ❌ Wave 0 |
| SC4 / MAINT-04 | `/refresh-memory` exists + `/verify-work` includes freshness | unit | `test_commands`/emit: `refresh-memory` discovered + emitted; `verify-work.md` body contains the regen+diff freshness step | ❌ Wave 0 |
| SC5 / D-11 | Emitter round-trips curator + command to both runtimes, no model id | unit | `test_emit_determinism.py`: re-emit byte-identical; `emit-manifest.json` lists `.opencode/agent/curator.md`, `.claude/agents/curator.md`, both command paths; `check_agent` no-model-id | partial (framework exists) ❌ update manifest expectations |
| SC5 / GEN-04 | Core stays example-independent | unit | `test_core_no_example_dep.py` green (curator/command carry no example/domain token) | ✅ exists (must stay green) |
| Determinism | Regenerated derived set byte-identical | ci-assert | `stale-derived` empty diff on a freshly-regenerated clean tree | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tools/harness_emit tools/harness_lint tools/docs_sync tools/memory_regen -x`
- **Per wave merge:** `uv run pytest` (full core suite) + `uv run python -m tools.harness_emit && git diff --exit-code -- .opencode .claude AGENTS.md CLAUDE.md opencode.json` (emit-drift preview)
- **Phase gate:** Full core suite green + `stale-derived`/`emit-drift`/GEN-04 green + `/verify-work` (now including freshness) green before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tools/harness_lint/caps.py` — `EXPECTED_PERSONAS` 4→5 (add `curator`); update `test_agents.py` reasoning
- [ ] `docs/reference/` — delete 4 orphan pages, commit `greeting.md` (reconcile pre-existing drift)
- [ ] `tools/docs_sync/generate.py` — add prune-then-write + a prune test
- [ ] `tools/docs_sync/tests/` — update determinism snapshot / EXPECTED_PAGES after reconcile
- [ ] `.github/workflows/ci.yml` — `stale-derived` job + `gate.needs` + a negative-control test for the gate logic
- [ ] `tools/harness_emit/emit-manifest.json` — regenerate + commit after adding curator + refresh-memory
- [ ] New test: hook-posture (no memory regen on the on-write path) + curator write-boundary + body-invokes-only-tools
- [ ] Framework install: none — pytest/uv already present

## Security Domain

> `security_enforcement` absent in config → treated as enabled. Scoped to this phase's actual surface (CI, git, agent write-boundary, path confinement).

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V1 Architecture | yes | Two-plane invariant + machines-gate/humans-ratify; curator cannot write the constitution plane |
| V4 Access Control | yes | `path_deny_globs` (constitution/secret deny) + Phase-4 contract-guard hook enforce curator's derived-only boundary |
| V5 Input Validation | yes | Generators read `contracts/**/*.schema.json` via stdlib `json` on the same path as `contract_hash`; `_confine` guards all writes |
| V6 Cryptography | no | No new crypto; contract-drift RFC 8785 hashing is reused unchanged |
| V12 File/Path | yes | `docs_sync._confine` / `repo_map` symlink-guard prevent traversal; prune must also `_confine` deletes to `docs/reference/` |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Curator escalates to edit a contract/ADR/golden | Elevation of Privilege | `path_deny_globs` denies `contracts/**`/`docs/adr/**`/`golden/**` for ALL personas; contract-guard hook enforces (GOLDEN_APPROVE_HUMAN bypass is constitution-only, curator never uses it) |
| `docs_sync` prune deletes outside `docs/reference/` | Tampering | Reuse `_confine`: refuse any delete target not under `docs/reference/`; preserve `README.md` explicitly |
| CI job gains write scope / interpolates event input | Tampering / EoP | Keep top-level `permissions: { contents: read }`; the `stale-derived` job needs no write; NEVER interpolate `${{ github.event.* }}` into a run shell (existing ci.yml posture) |
| Real model identifier leaks into emitted curator | Information Disclosure | Emitter `check_agent`/`check_opencode_config` loud-fail on non-placeholder model tokens (D-11) |
| Stale derived plane merges (freshness bypass) | Repudiation / Tampering | `stale-derived` gate + `/verify-work` step; use `git add -A`+`--cached` so untracked new pages are caught (P1) |

## Sources

### Primary (HIGH confidence)
- Repo tree (read this session): `tools/memory_regen/{contracts_index,repo_map,inject,__init__}.py`, `tools/docs_sync/generate.py`, `tools/harness_emit/{generate,validate,project_agent,project_command}.py` + `emit-manifest.json`, `tools/harness_lint/caps.py` + `tests/test_core_no_example_dep.py`, `harness/agents/{code-reviewer,explorer}.md`, `harness/commands/{orient,docs-sync,verify-work}.md`, `harness/permission-matrix.json`, `harness/skills/two-plane-memory/SKILL.md`, `.github/workflows/ci.yml`, `.gitignore`
- Live commands run: `python -m tools.docs_sync` (confirmed 2 pages written + 4 orphans untouched + greeting.md untracked); `git ls-files docs/reference/`; `git check-ignore`; `find contracts -name '*.schema.json'`
- `.planning/{ROADMAP,REQUIREMENTS,STATE}.md` + `09-CONTEXT.md` — phase scope, D-01..D-11, MAINT-01..04

### Secondary (MEDIUM confidence)
- git gitignore semantics ("cannot re-include a file under an excluded directory") — well-established git behavior; verify with `git check-ignore` at plan time (P3)

### Tertiary (LOW confidence)
- None — no unverified web claims; this phase is entirely repo-internal.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every reuse target read from the live tree; no external packages
- Architecture: HIGH — mirrors proven Phase-7 `emit-drift` + existing generator determinism
- Pitfalls: HIGH — P1/P2 empirically confirmed by running `docs_sync` + inspecting git state; P3/P4/P5 confirmed against source

**Project Constraints (from CLAUDE.md / AGENTS.md):**
- Contract-first; two-plane memory (derived never hand-edited — machine-write + CI-verify is OK)
- Machines gate, humans ratify (constitution plane human-owned; curator has no constitution write)
- GEN-04 core→example no-dependency stays green; curator/command domain-neutral
- Every new agent/command round-trips the Phase-7 emitter to both runtimes; NO model identifier in any repo artifact
- Prefer PR/CI enforcement over heavy per-commit local hooks (MAINT-03)

**Research date:** 2026-07-13
**Valid until:** 2026-08-13 (stable — internal machinery; re-verify only if `tools/harness_emit` or the generators change)
</content>
</invoke>
