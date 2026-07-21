# Phase 15: Emit Round-Trip + Gates *(v2.1 D)* — Research

**Researched:** 2026-07-16
**Domain:** Single-source dual-runtime emit round-trip; drift/model-id/GEN-04 gate settlement
**Confidence:** HIGH — every claim below was verified by running the real emitter and the real suite against this working tree.

> No `CONTEXT.md` exists for this phase (discuss-phase was not run). Constraints below are derived
> from `.planning/REQUIREMENTS.md` (MEM2-06), `ROADMAP.md` Phase 15, `CLAUDE.md`, and — critically —
> the **Phase 14 carry-in notes in `STATE.md`**, which were written specifically to brief this phase.

---

## Summary

This is a **mechanical, zero-code phase**. The Phase-7 emitter is glob-driven and needs **no change**;
Phase 14 authored `harness/commands/agree.md` source-only, and Phase 13 edited three command bodies,
one skill body, and one plugin — none of which were ever projected into the committed `.opencode/` /
`.claude/` trees. Phase 15 owes exactly one thing: **run the emitter, commit what it writes, and
regenerate the one stale test fixture.**

I did not take this on trust. I ran the real emitter into an isolated tmp tree (`root=tmp`, no repo
mutation) and diffed it against the committed trees, so the delta below is **measured, not
predicted**: 2 new files, 8 changed files, 1 line of `AGENTS.md`, 2 manifest entries, and one `.ambr`
snapshot. `opencode.json` and `.claude/settings.json` come out **byte-identical** — they do not
change, and a plan that expects them to is wrong. I also confirmed the full suite baseline is exactly
the **1 failed / 658 passed** that `STATE.md` predicted, with the single red being the sanctioned
`test_projected_tree_matches_committed_snapshot`.

Two findings materially change how this phase should be planned, and both are traps rather than work.
**First: `EXPECTED_COMMANDS` does not exist** — I grepped the entire repo. Success Criterion 1 names
it anyway, which is the *third* time this milestone's own source has named a non-existent constant;
Phase 14 already ruled on this (D-11) and refused to invent it. Phase 15 must refuse identically.
**Second, and more dangerous: no local test reads the committed trees at all.** The one red test
renders from `harness/` source and compares to `.ambr` — it never opens `.opencode/`. So
`--snapshot-update` alone would turn the suite green *without a single byte being emitted*, and the
local suite would happily report success. That is precisely the gate-theft `STATE.md` warns about,
and the only thing that actually catches it is the CI `emit-drift` job's `git diff --exit-code`.

**Primary recommendation:** Run `uv run python -m tools.harness_emit`, commit the measured delta,
*then* regenerate the `.ambr` scoped to `test_emit_determinism.py`, and verify by locally replicating
the CI gate (`re-emit && git diff --exit-code` over the documented path set) — never by trusting a
green pytest. Do not create `EXPECTED_COMMANDS`. Do not touch the emitter.

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MEM2-06 | Every new/changed agent, skill, and command (`/agree`, updated skills, updated `AGENTS.md` managed block) round-trips the Phase-7 emitter to **both** runtimes with **no model id**; emit-drift clean, `EXPECTED_COMMANDS`/counts updated, GEN-04 green. | Exact measured delta (§Measured Emit Delta); model-id gate verified clean (§Gate Inventory); GEN-04 verified clean against the *projected* snapshot (§GEN-04); `EXPECTED_COMMANDS` proven non-existent (§Mis-Worded Criteria). ADR portion already landed in Phase 12 + errata `ff832ac`. |

**Scope note (REQUIREMENTS.md:70):** MEM2-06 spans two phases. The **ADR-0006 authoring** portion is
already delivered (Phase 12, plus the Phase-14 errata `ff832ac`). Phase 15 owns **only the emit
portion**. Traceability owner is Phase 15; the requirement is counted once here.

---

## Project Constraints (from CLAUDE.md)

| Directive | Bearing on this phase |
|-----------|----------------------|
| **모델 아이덴티티**: no model identifier in repo artifacts (commits, PRs, code comments) | Directly SC2. Verified clean — see §Gate Inventory. Also applies to the phase's own commit messages. |
| **Contract-first**: `contracts/` is canonical; code that differs is wrong | Not engaged — this phase touches no contract. |
| **Memory: two-plane; derived artifacts are auto-generated, never hand-managed** | The `.opencode/` + `.claude/` trees are **derived**. This phase must regenerate them, never hand-edit them. The `DERIVED_MARKER` (`generate.py:48`) on every emitted file states this. |
| **Single source → both runtimes** (dev = Claude, deploy = opencode) | The whole point of the phase: both trees must carry `/agree`. |
| **GSD Workflow Enforcement**: no direct edits outside a GSD command | Execution runs under `/gsd:execute-phase`. |
| **`AGENTS.md` is the source for agent rules; nearest-wins** | The emitter splices only inside the HARNESS-MANAGED fence; everything outside is preserved verbatim (`merge.splice_managed_block`). |

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Discover harness source | `tools/harness_emit/generate.py` (`iter_commands` / `iter_skills` / `iter_agents` / `iter_plugins`) | — | Non-recursive `glob("*.md")`; a new source file is picked up with **zero code change**. |
| Project → runtime shape | `project_command` / `project_skill` / `project_agent` | — | Per-runtime frontmatter projection; already handles `/agree`. |
| Loud-fail validation | `tools/harness_emit/validate.py` + `tools/harness_lint/caps.py` | — | Validate-then-write: any cap/model/permission violation aborts **having written nothing**. |
| Write derived trees | `emit()` → `.opencode/` + `.claude/` | — | Regime A (owned + manifest-tracked). |
| Merge shared markdown | `merge.splice_managed_block` → `AGENTS.md`, `CLAUDE.md` | — | Regime B (splice-only, never full-write, not manifest-listed). |
| Ownership manifest | `manifest.prune_then_write` | — | Regime A path set only; `gsd-*` excluded. |
| Guard committed trees | **CI `emit-drift` job only** | *(no local twin)* | ⚠ See §The Gate-Theft Trap. |
| Guard projection determinism | `.ambr` snapshot (source-rendered) | — | Does **not** read the committed trees. |
| Core→example independence | `tools/harness_lint/tests/test_core_no_example_dep.py` | — | Scans `git ls-files tools harness libs` — **the `.ambr` is in scope**. |

---

## Measured Emit Delta

> **Method (HIGH confidence — reproducible):** I emitted the real `harness/` into an isolated tmp tree
> via `harness_emit.emit(opencode_dir=…, claude_dir=…, manifest_path=…, root=tmp)` with `AGENTS.md`,
> `CLAUDE.md`, and `.claude/settings.json` seeded, then `diff -rq` against the committed trees. The
> repo was **not** mutated. Emit returned **84 artifacts** and raised nothing (all validators pass).

### New files (2)
| Path | Source |
|------|--------|
| `.opencode/command/agree.md` | `harness/commands/agree.md` (Phase 14, `104cecd`) |
| `.claude/commands/agree.md` | same source, Claude projection (description-only frontmatter) |

### Changed files (8)
| Path | Cause | Diff size |
|------|-------|-----------|
| `.opencode/command/orient.md` · `.claude/commands/orient.md` | Phase 13 body edits | ~20 lines |
| `.opencode/command/checkpoint.md` · `.claude/commands/checkpoint.md` | Phase 13 (`updated:` stamp, MEM2-05) | ~15 lines |
| `.opencode/command/lint.md` · `.claude/commands/lint.md` | Phase 14 provenance lint | ~11 lines |
| `.opencode/skill/two-plane-memory/SKILL.md` · `.claude/skills/two-plane-memory/SKILL.md` | Phase 12/13 distrust→data-authority reword (MEM2-03) | ~20 lines |
| `.opencode/plugin/session-inject.ts` | Phase 13 comment reword (`banner-first`→`directive-first`; `provisional banner`→`data-provenance banner`) — byte-copied verbatim | 2 lines |

### Merged (1)
`AGENTS.md` HARNESS-MANAGED block, **line 104 only** — the Commands index gains `agree`:
```
- **Commands** (…): add-language, adr, agree, build, checkpoint, …
```
`CLAUDE.md`'s managed block is static → **no change**.

### Manifest (+2)
`tools/harness_emit/emit-manifest.json` gains exactly `.claude/commands/agree.md` and
`.opencode/command/agree.md`. Nothing pruned.

### Fixture (1)
`tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` — regenerate.

### ⚠ Explicitly UNCHANGED (do not plan edits here)
| Path | Verified |
|------|----------|
| `opencode.json` | `diff` → **empty**. No permission/model/config change this milestone. |
| `.claude/settings.json` | `diff` → **empty**. Regime B-json merge reproduces it byte-for-byte. |
| `.claude/agents/**` · `.opencode/agent/**` | **No** agent changed this milestone. (`.claude/agents` shows only GSD-owned `gsd-*.md`, correctly untouched + unlisted.) |
| All other skills (10 of 11) | Only `two-plane-memory` changed. |
| `tools/harness_emit/**.py` | **Zero emitter code change** — glob discovery already covers `/agree`. |

---

## Standard Stack

No new packages. `tools/harness_emit/pyproject.toml` declares `dependencies = []` and is a virtual uv
workspace member. **No `## Package Legitimacy Audit` section is required — this phase installs
nothing** and `uv.lock` must not change.

### Commands (all verified by execution)
| Command | Purpose |
|---------|---------|
| `uv run python -m tools.harness_emit` | The re-emit. **No flags** (`main()` reserves `argv` but parses nothing — `generate.py:463`). Writes both trees + `opencode.json` + manifest; splices `AGENTS.md`/`CLAUDE.md`; merges `settings.json`. |
| `uv run pytest` | Full non-example suite (root `testpaths = ["libs/python", "tools"]`). Baseline: **1 failed / 658 passed**. |
| `uv run pytest --snapshot-update tools/harness_emit/tests/test_emit_determinism.py` | Regenerate the `.ambr`. **Scope to this file** — verified safe: this `.ambr` holds exactly **one** snapshot (`test_projected_tree_matches_committed_snapshot`), and the other four `.ambr` files (`docs_sync`, `memory_regen` ×3) are untouched by a scoped run. |
| `git diff --exit-code -- .opencode opencode.json .claude/agents .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json` | **The documented path set** — verbatim from `.github/workflows/ci.yml:197`. This is the local replica of the CI `emit-drift` gate. |
| `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py` | GEN-04. |

---

## Gate Inventory

| Gate | Lives at | Scope | Status |
|------|----------|-------|--------|
| **emit-drift** (CI) | `.github/workflows/ci.yml:187-197`, in `gate.needs` | Re-emit + `git diff --exit-code` over the 8-path set | **RED** — will go green on re-emit |
| **core-suite** (CI) | `ci.yml:170-178` → `uv run pytest` | Full non-example suite | **RED** — the one `.ambr` failure |
| **stale-derived** (CI) | `ci.yml:211-239` | `docs/reference` + `contracts-index.md` | Green; **not** engaged (distinct concern, D-07) |
| **GEN-04** | `tools/harness_lint/tests/test_core_no_example_dep.py` | `git ls-files tools harness libs` | Green; `.ambr` **is** in scope — see below |
| **no model id (agents)** | `validate.check_agent` (`validate.py:84-88`) + `test_agents.py:129` | `model` frontmatter must `== "provider/explorer-tier"` | Green |
| **no model id (config)** | `validate.check_opencode_config` (`validate.py:216-220`) | `model`/`*_model` must match `^provider/[a-z0-9-]+-tier$` | Green |
| **no model id (committed config)** | `test_opencode_json.py:51` | committed root `opencode.json` | Green |
| **command count** | `test_coexist.py:39` `test_all_20_commands_emit_to_both_trees` | Counts the **source** via tmp emit | **Already 20, already passing** |
| **skill set** | `validate.check_skill_set` + `test_emit_determinism.py:99` vs `EXPECTED_SKILLS` (11) | Source | Green; no skill added |

### SC2 "no model id anywhere in the emitted trees" — verified
I scanned the full emitted tmp tree (`.opencode/`, `.claude/commands`, `.claude/skills`,
`opencode.json`) for real provider identifiers (`claude-*opus|sonnet|haiku`, `gpt-N`, `gemini-N`,
`o1/o3-mini`): **zero hits**. The only model values present are the placeholder tiers
`provider/explorer-tier` and `provider/implementer-tier`. I separately rendered the *projected*
snapshot and found **no model-id-like tokens at all**. SC2 is satisfiable with no new work.

**Coverage nuance `[VERIFIED: codebase]`:** the model-id gates check the `model` *frontmatter key*
and `opencode.json` values — **no gate greps emitted bodies/prose for a model id**. It is covered
transitively (bodies are copied verbatim from `harness/` source, and source *agents* are scanned),
but a model id in a *command/skill body* would not be caught by any automated gate. Not a problem
today (verified zero); worth one grep in verification rather than a new gate.

### GEN-04 — a real hazard that does not bite
`_CORE_ROOTS = ("tools", "harness", "libs")` and the scan enumerates `git ls-files`. The `.ambr` is
tracked at `tools/harness_emit/tests/__snapshots__/…` → **it is scanned**, and it embeds the **full
body** of every agent, command, and skill. So regenerating it *could* import a forbidden token
(`examples/`, `equipment`, `설비`, `wafer`, `dotnet-engineer`, …) into a core-plane file. This has
bitten twice before (`STATE.md`: the 08-01 and 10-01 prose leaks).

I pre-verified it: I rendered the projected snapshot in-memory and scanned it against all 12 GEN-04
tokens → **0 hits**. Each new/changed source file (`agree.md`, `orient.md`, `checkpoint.md`,
`lint.md`, `two-plane-memory/SKILL.md`) is individually clean, and the current committed `.ambr` has
0 hits. **GEN-04 will stay green.** Keep it as an explicit post-regen verification step, not a task.

---

## The Gate-Theft Trap *(the single most important finding)*

`test_projected_tree_matches_committed_snapshot` (`test_emit_determinism.py:55-81`) renders from
`_AGENTS_DIR` / `_COMMANDS_DIR` / `_SKILLS_DIR` — i.e. **`harness/` source** — and compares to the
`.ambr`. **It never reads `.opencode/` or `.claude/`.**

I grepped for any test that reads the committed runtime trees. There is **none**:
```
tools/harness_emit/tests/test_settings_merge.py:29   → .claude/settings.json  (only)
tools/harness_lint/tests/test_derived_freshness.py:29 → .claude/settings.json  (only)
tools/hooks/tests/test_settings_coexist.py:23        → .claude/settings.json  (only)
```
Nothing reads `.opencode/command/*.md` or `.claude/commands/*.md`.

**Consequence:** `pytest --snapshot-update` alone → **0 failed / 659 passed**, with the committed
trees still missing `/agree`. The local suite would report total success on an unemitted repo. Only
the CI `emit-drift` job would catch it — after push.

This is exactly what `STATE.md` means by *"`0 failed` = someone updated the `.ambr` and stole this
gate."* The nuance the planner must internalize: **the `.ambr` update is legitimate and required in
Phase 15** (it is the "emit fixtures updated" half of SC1 — the snapshot is genuinely stale vs
source). The theft is not *updating* the snapshot; it is updating it *instead of* emitting.

**Therefore, mandate ordering + local gate replication:**
1. `uv run python -m tools.harness_emit` — emit **first**.
2. `git status --porcelain` → **must** show the 2 new + 8 changed + `AGENTS.md` + manifest. If this
   is empty, stop: the emit did nothing and the phase is a no-op.
3. *Then* `--snapshot-update` scoped to `test_emit_determinism.py`.
4. `uv run pytest` → 0 failed / 659 passed.
5. **Re-emit + `git diff --exit-code -- <8-path set>`** → clean. *This* is the proof, not step 4.

---

## Mis-Worded Criteria in This Phase's Own Source

> This milestone has a documented pattern of success criteria naming things that do not exist.
> Phase 14 hit it three times (`STATE.md`, `14-CONTEXT.md:170`). Phase 15's SC1 inherits one.

### `EXPECTED_COMMANDS` does not exist — do NOT create it
SC1 says *"emit fixtures/counts + `EXPECTED_COMMANDS` are updated to match."* I grepped the entire
repo (`--exclude-dir=.git`). **Every** hit is in `.planning/` prose — requirements, roadmap, and
Phase-13/14 research/plans *documenting that it does not exist*. There is **no such symbol in any
source file**. `caps.py` defines `EXPECTED_PERSONAS`, `EXPECTED_SKILLS`, `EXPECTED_TEMPLATES` — no
commands equivalent. `test_commands.py` is **glob-driven**, which is why `agree.md` was auto-covered
in Phase 14 with zero test edits.

**Phase 14 already ruled (D-11, `14-CONTEXT.md:107`):** do not invent the constant to satisfy the
wording — doing so *adds* an anti-sprawl maintenance burden the glob design deliberately avoids.
**Phase 15 must hold the same line.** Do not fail the phase on SC1's literal wording; SC1's substance
is satisfied by the emit + the `.ambr` regen.

### "counts updated" — already done, nothing to update
`test_all_20_commands_emit_to_both_trees` was **already bumped 19→20 by Phase 14** (`fa1aea8`) and
**already passes**, because `_emit(tmp_path)` counts the runtime-neutral **source**, not the committed
trees. (`STATE.md` flags this as the Phase-14 D-10 error that survived planner *and* plan-checker.)
There is **no count edit** in this phase.

**One genuine cosmetic gap:** `test_coexist.py:3` (module docstring) still says *"The emitter writes
its **19** harness commands"* — Phase 14 bumped the function and its docstring but not the module
docstring. Worth a one-line fix; not a gate.

---

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---------|-------------|-------------|-----|
| Adding `/agree` to the trees | Hand-write `.opencode/command/agree.md` | `python -m tools.harness_emit` | The trees are DERIVED; a hand-edit is exactly what `emit-drift` exists to catch, and the `DERIVED_MARKER` forbids it. |
| Picking up a new command | Register it in a list/const | The existing non-recursive glob | `iter_commands` already found it — proven by the tmp emit. |
| A commands anti-sprawl constant | `EXPECTED_COMMANDS` frozenset | The glob-driven `test_commands.py` | D-11. It does not exist by design. |
| Proving the trees are current | A green `pytest` | `re-emit && git diff --exit-code` | No local test reads the trees. See §The Gate-Theft Trap. |
| Updating `AGENTS.md`'s command index | Edit line 104 | The emitter's `splice_managed_block` | Regime B; hand-editing inside the fence re-reds `emit-drift`. |
| Regenerating the `.ambr` | Hand-edit the snapshot | Scoped `--snapshot-update` | 178+ lines of rendered output. |

**Key insight:** every artifact this phase changes is machine-owned. The entire phase is *"invoke the
generator and commit its output."* Any task that hand-writes a byte into `.opencode/`, `.claude/`, or
the `.ambr` is a bug.

---

## Common Pitfalls

### Pitfall 1: Greening the suite without emitting *(the phase-defining risk)*
**What goes wrong:** `--snapshot-update` first → suite green → phase declared done → trees still 19.
**Why:** the `.ambr` test reads source, not trees; nothing local guards the trees.
**Avoid:** emit first; assert `git status` is non-empty; verify with the re-emit + `git diff` replica.
**Warning sign:** `0 failed` before `python -m tools.harness_emit` has ever run.

### Pitfall 2: Inventing `EXPECTED_COMMANDS` to satisfy SC1
**What goes wrong:** a frozenset is added, duplicating what the glob does, adding drift surface.
**Avoid:** D-11. Verify with `grep -rn "EXPECTED_COMMANDS" tools/` → **0**.

### Pitfall 3: Planning edits to `opencode.json` / `settings.json`
**What goes wrong:** tasks are written to "update the config"; they are no-ops or, worse, hand-edits
that red the drift gate.
**Avoid:** measured `diff` → **both empty**. The emitter rewrites them to identical bytes.

### Pitfall 4: A bare `git diff` in verification
**What goes wrong:** `/agree` lands as **new untracked files**. Bare `git diff` sees only tracked
changes and would **miss** them — a false pass.
**Why it's subtle:** CI's `emit-drift` uses bare `git diff` and is *correct there* only because CI
checks out a tree where the files are already committed. Locally, before `git add`, they are
untracked. `ci.yml:206-210` documents this exact trap for the `stale-derived` job (Pitfall P1),
which uses `git add -A` + `git diff --cached --exit-code` for precisely this reason.
**Avoid:** `git add` the new files **before** the local drift replica, or use `--cached`.

### Pitfall 5: An unscoped `--snapshot-update`
**What goes wrong:** a repo-wide run touches the other four `.ambr` files (`docs_sync`,
`memory_regen` ×3).
**Avoid:** scope to `tools/harness_emit/tests/test_emit_determinism.py`. Verified safe: that `.ambr`
holds exactly one snapshot. Confirm with `git status -- tools/**/__snapshots__` → only the emit one.

### Pitfall 6: A GEN-04 prose leak via the regenerated `.ambr`
**What goes wrong:** the `.ambr` is a core-plane tracked file embedding every body; a domain token in
any body REDs GEN-04. Precedent: two prior leaks (`STATE.md`, 08-01 and 10-01).
**Avoid:** pre-verified 0 hits — but re-run GEN-04 **after** the regen, not before.

### Pitfall 7: A model identifier in the phase's own commit messages
**What goes wrong:** `CLAUDE.md`'s 모델 아이덴티티 constraint covers commits/PRs, and **no gate scans
commit messages** — the model-id gates only scan frontmatter and `opencode.json`.
**Avoid:** author commit messages without model identifiers; this is a human/agent discipline, not an
enforced gate.

---

## Downstream Consequence (worth stating in the plan)

Per `STATE.md`, **PR #3 is red on exactly two jobs — `core-suite` and `emit-drift` — and both are
this one inherited re-emit debt** (reproduced locally: 1 failed / 620 passed at that commit; 658 now).
`gate.needs` lists both, so **ADR-0004 / 0005 / 0006 / 0007 cannot merge to `main` until Phase 15
lands.** Settling this phase unblocks that ratification. That is the phase's real payoff and belongs
in the summary. It also raises the stakes on Pitfall 1: a stolen gate here would green PR #3 while
leaving the trees wrong.

---

## Runtime State Inventory

> Phase 15 is a regeneration/projection phase — the rename/refactor inventory applies in spirit
> (what still holds a stale copy after source changed?). Answered explicitly per category.

| Category | Items found | Action required |
|----------|-------------|------------------|
| **Stored data** | **None** — no datastore keys this milestone. Verified: no ChromaDB/Mem0/Redis surface in the emit path. | none |
| **Live service config** | **None** — no external service holds the command surface. `opencode.json` is repo-committed and **unchanged** (measured). | none |
| **OS-registered state** | **None** — no Task Scheduler/pm2/launchd/systemd registration names a harness command. `.claude/settings.json` hook groups are the nearest analogue and are **byte-identical** (measured). | none |
| **Secrets/env vars** | **None** in the emit path. Two adjacent, out-of-scope items: gitignored `.claude/settings.local.json` carries `HARNESS_DEV_BYPASS=1`; and `~/.codex/config.toml` holds a plaintext `gho_…` token (`STATE.md` security note, outside this repo — **do not** address here). | none |
| **Build artifacts / stale copies** | **THIS IS THE PHASE.** The committed `.opencode/` + `.claude/` trees and the `.ambr` are stale derived copies of `harness/`. Also stale: `test_coexist.py:3` module docstring ("19"). `__pycache__` is gitignored/irrelevant. | the re-emit + `.ambr` regen (§Measured Emit Delta) |

---

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `uv` | every command | ✓ | present; `uv run pytest` executed successfully | — |
| Python 3.11 | emitter + suite | ✓ | 3.11 (`__pycache__` = `cpython-311`) | — |
| `pytest` + `syrupy` | suite + `.ambr` | ✓ | pytest 8.4.2 | — |
| `git` | drift replica | ✓ | — | — |
| **.NET 10 SDK** | — | ✗ (egress-blocked, `STATE.md`) | — | **Not needed.** Root `testpaths` = `libs/python` + `tools`; the .NET leg is example-only and off the non-example suite. |
| Network | — | n/a | — | **Not needed** — no installs; `uv.lock` must not change. |

**No blocking missing dependencies.** The known .NET blocker does not touch this phase.

---

## Validation Architecture

*(`workflow.nyquist_validation: true` in `.planning/config.json`.)*

### Test framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 + syrupy (`.ambr`) |
| Config | root `pyproject.toml` — `testpaths = ["libs/python", "tools"]`, `addopts = "-ra"` |
| Quick run | `uv run pytest tools/harness_emit -q` (~1s) |
| Full suite | `uv run pytest` — **1.53s**, currently 1 failed / 658 passed |

### Requirement → test map
| Req | Behavior | Type | Automated command | Exists? |
|-----|----------|------|-------------------|---------|
| MEM2-06 | `/agree` projects to both trees | unit | `uv run pytest tools/harness_emit/tests/test_coexist.py::test_all_20_commands_emit_to_both_trees` | ✅ (already green) |
| MEM2-06 | Projection matches committed fixture | snapshot | `uv run pytest tools/harness_emit/tests/test_emit_determinism.py::test_projected_tree_matches_committed_snapshot` | ✅ (red → green on regen) |
| MEM2-06 | Re-emit byte-identical | unit | `…::test_emit_twice_byte_identical` | ✅ green |
| MEM2-06 | **Committed trees are current** | integration | `uv run python -m tools.harness_emit && git diff --exit-code -- .opencode opencode.json .claude/agents .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json` | ⚠ **CI-only — no local test.** Must be run manually. |
| MEM2-06 | No model id | unit | `uv run pytest tools/harness_lint/tests/test_opencode_json.py tools/harness_lint/tests/test_agents.py -k model` | ✅ green |
| MEM2-06 | GEN-04 green | unit | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py` | ✅ green (re-run after regen) |
| MEM2-06 | Full suite | suite | `uv run pytest` | ✅ → expect **0 failed / 659 passed** |

### Sampling rate
- **Per task:** `uv run pytest tools/harness_emit -q`
- **Per wave / phase gate:** `uv run pytest` (0 failed / 659) **plus** the manual re-emit + `git diff` replica.

### Wave 0 gaps
**None** — the test infrastructure fully covers this phase. The single structural gap (no local test
reads the committed trees) is **deliberately not** filled here: adding one would be new emitter-adjacent
test surface beyond MEM2-06's scope. Flagged in §Open Questions as a candidate follow-up.

---

## Security Domain

*(`security_enforcement` not set in `.planning/config.json` → treated as enabled.)*

### Applicable ASVS categories
| Category | Applies | Control |
|----------|---------|---------|
| V2 Authentication | no | no auth surface |
| V3 Session Management | no | — |
| V4 Access Control | **yes (repo-plane)** | `contract-guard` hook + `path_deny_globs` deny agent writes to `docs/adr/`; CODEOWNERS on the constitution plane. Not engaged: this phase writes only derived paths. |
| V5 Input Validation | **yes** | `validate.py` validate-then-write — caps/permission-keys/model/skill-set loud-fail before any byte is written. |
| V6 Cryptography | no | — |

### Threat patterns for this stack
| Pattern | STRIDE | Mitigation | Status |
|---------|--------|------------|--------|
| **T-07-04 Elevation** — emitter executes plugin source | Elevation | `iter_plugins` → `read_bytes`/`write_bytes`; **never** parsed/imported/executed (`generate.py:422-434`) | Intact — `session-inject.ts` is byte-copied |
| **T-07-01 traversal** — emitted path escapes its lane | Tampering | `_confine()` before **every** write incl. recursive `references/` | Intact |
| **T-07-02 Tampering** — emitter clobbers GSD-owned files | Tampering | Regime B splice; `gsd-*` manifest exclusion; proven by `test_coexist` seeded-GSD tests | Intact — measured diff shows `.claude/commands/gsd/` and `gsd-*.md` untouched |
| **T-07-03 Info disclosure** — real model id leaks into an artifact | Info disclosure | `check_agent` + `_PLACEHOLDER_MODEL_RE` | Verified 0 leaks (§Gate Inventory) |
| **Derived-plane tamper** — hand-edit masquerades as generated | Tampering | `DERIVED_MARKER` + CI `emit-drift` | The gate this phase settles |
| **Gate theft** — fixture updated instead of source regenerated | Tampering | *(no automated control)* | ⚠ **Process-only.** See §The Gate-Theft Trap. |

---

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|---------------|
| A1 | Suite goes **659 passed / 0 failed** after emit + regen (658+1) | Validation | Low — arithmetic on a measured baseline; the regen fixes exactly the one red. |
| A2 | No Phase-15-concurrent source edit lands before the emit | Delta | Medium — the measured delta is a snapshot of this working tree. **Re-measure at execution** (`git status`), don't trust these file counts blindly. |
| A3 | CI `emit-drift` passes once the delta is committed | Gates | Low — the job is literally re-emit + diff, and re-emit is proven byte-identical (`test_emit_twice_byte_identical`). |
| A4 | The stale `test_coexist.py:3` "19" docstring is safe to fix in this phase | Mis-Worded | Low — a comment; no gate reads it. Could also be deferred. |

*Everything else in this document was verified by executing the real emitter and the real suite
against this working tree.*

---

## Open Questions

1. **Should a local test guard the committed trees?**
   - *Known:* none does; only CI `emit-drift` does; the gate-theft hole is real and structural.
   - *Unclear:* whether a test asserting `.opencode/command/*.md` == projected source belongs in the
     unit suite, or whether that duplicates CI by design (the `.ambr` deliberately gives
     "determinism WITHOUT git diff", `test_emit_determinism.py:56`).
   - *Recommendation:* **out of scope for MEM2-06.** Note it as a candidate follow-up; do not grow
     test surface in a phase whose whole point is "change no code."

2. **Should `ruff check` become a CI gate?**
   - *Known:* `STATE.md` records ~57 pre-existing E-codes in `tools/` + 2 format failures; `ruff` is
     **not** a CI gate today.
   - *Recommendation:* **explicitly out of scope.** Pre-existing debt, unrelated to MEM2-06. Do not
     let it contaminate this phase. Ensure the two `.ambr`/emit paths don't add new lint debt.

3. **Does `/agree` need `subtask: true` in its opencode projection?**
   - *Known:* emitted `.opencode/command/agree.md` carries `agent: orchestrator` but no `subtask`;
     `/fan-out-synthesize` carries `subtask: true`.
   - *Recommendation:* **not this phase's call.** It is an authored Phase-14 source decision; the
     emitter faithfully projects what is authored. Changing it means editing `harness/commands/agree.md`
     — a source change, out of scope. Flag only if a reviewer raises it.

---

## Sources

### Primary (HIGH — executed/read in this session)
- `tools/harness_emit/generate.py` (479 ln) — `emit()`, glob discovery, `_confine`, Regime A/B, `DERIVED_MARKER`
- `tools/harness_emit/validate.py`, `tools/harness_lint/caps.py` — validators, `PLACEHOLDER_MODEL`, `EXPECTED_SKILLS`
- `tools/harness_emit/tests/{test_coexist.py,test_emit_determinism.py}` — count + snapshot semantics
- `tools/harness_lint/tests/test_core_no_example_dep.py` — GEN-04 scan scope
- `.github/workflows/ci.yml:165-281` — `core-suite`, `emit-drift` (path set, ln 197), `stale-derived`, `gate.needs`
- **Executed:** real `emit()` into tmp + `diff -rq` vs committed → the measured delta
- **Executed:** `uv run pytest` → 1 failed / 658 passed (baseline confirmed)
- **Executed:** projected-snapshot render + GEN-04 token scan (0 hits) + model-id scan (0 hits)
- **Executed:** repo-wide `grep EXPECTED_COMMANDS` → source hits: **0**
- `.planning/STATE.md` — Phase 14 carry-in notes (written for this phase; PR #3 status, gate-theft warning)
- `.planning/REQUIREMENTS.md` (MEM2-06, ln 30/70), `.planning/ROADMAP.md` (ln 476-484), `CLAUDE.md`

### Secondary (MEDIUM)
- `.planning/phases/14-*/14-{CONTEXT,RESEARCH}.md` — D-10/D-11 precedent on `EXPECTED_COMMANDS` + the source-vs-tree count error

### Tertiary
- None. No external/web source was needed — this phase is entirely repo-internal.

---

## Metadata

**Confidence breakdown:**
- **Emit delta:** HIGH — measured by executing the real emitter, not inferred.
- **Gates:** HIGH — read the CI YAML and the guard sources; ran them.
- **Pitfalls:** HIGH — Pitfalls 1/2 are documented Phase-14 failures; 4/6 have in-repo precedent; 3/5 measured.
- **Stack:** HIGH — zero new deps; commands executed successfully.

**Research date:** 2026-07-16
**Valid until:** **Until the next commit touching `harness/`.** The measured delta is tree-specific —
re-measure with `git status` at execution (A2). Otherwise stable (no external deps).
