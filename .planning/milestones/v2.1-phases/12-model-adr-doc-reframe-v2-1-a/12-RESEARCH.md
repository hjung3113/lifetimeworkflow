# Phase 12: Model + ADR + Doc Reframe (v2.1 A) — Research

**Researched:** 2026-07-14
**Domain:** In-repo memory-model scaffolding + documentation reframe + human-gated ADR authoring (no external tech)
**Confidence:** HIGH (entirely internal; every claim verified against a repo file at path:line)

## Summary

This phase is almost entirely internal to THIS repo. It (1) scaffolds a NEW committed, human-authored `.memory/agreements/` tier (per-guideline `<slug>.md` files) documented with an entry-shape spec + seed, explicitly a committed tier like `state/` and NOT derived; (2) rewords the "provisional / hint, not truth" distrust prose to *data-authority* framing in 5 named surfaces; and (3) authors ADR-0006 recording the memory-model change, landing via the human-ratified constitution path (an agent Write to `docs/adr/` is correctly denied by contract-guard — the deny is the design, not a bug).

Two load-bearing discoveries de-risk the plan. **First:** the AGENTS.md distrust prose (lines 87–88) sits OUTSIDE the `HARNESS-MANAGED` marker block (lines 97–106) — it is hand-editable human content preserved verbatim by the emitter, so editing it creates NO emit tension and does NOT belong to Phase 15. **Second:** the ADR-0006 legitimate authoring route already has a precedent (ADR-0002/0003/0005 all "landed via the live gate with `GOLDEN_APPROVE_HUMAN`"): the human ratifies by supplying the `GOLDEN_APPROVE_HUMAN` token (the golden-approve-style human flag) at write time, with CODEOWNERS as the merge-time backstop. The plan must express the deny as an expected, verifiable fact and route the write through the token, never around the hook.

**Primary recommendation:** Treat this as a docs+scaffold phase with zero new machinery. Scaffold `.memory/agreements/` with a documented entry shape (markdown + YAML frontmatter, house-style) + a seed file + a README plane-table update (3 planes → 4); do a scoped find/replace of distrust prose across 5 surfaces preserving the data-authority meaning; author ADR-0006 as a next-numbered MADR via `/adr`, landing it through the `GOLDEN_APPROVE_HUMAN` human-ratified path. Do NOT touch `inject.py`, the emitter, or the generated `.opencode/`/`.claude/` trees.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| New PROCESS memory channel (`.memory/agreements/`) | Committed state plane (`.memory/`, human-authored) | — | It is a committed human-authored tier like `state/`, NOT derived (never regenerated) and NOT constitution (not path-denied). Proposal §7b / MEM2-01. |
| Entry-shape documentation (schema/fixture) | `.memory/` (README + seed/template) | `harness/skills/two-plane-memory` (map) | House style documents planes in `.memory/README.md` + the two-plane skill; there is no JSON-schema convention for memory (only `contracts/` uses `.schema.json`). |
| Distrust→data-authority reword | Docs/prose (5 surfaces) | — | Pure prose edit; `.memory/*` + `harness/skills/*` (source) + `AGENTS.md` (hand-editable region). |
| ADR-0006 authoring | Constitution plane (`docs/adr/`) | CODEOWNERS (merge gate) + contract-guard (in-session gate) | Append-only MADR; write denied without `GOLDEN_APPROVE_HUMAN`; human ratifies. |
| Emit round-trip of source changes | DEFERRED to Phase 15 | — | `two-plane-memory/SKILL.md` is `harness/` source; its emit to both runtimes is Phase 15, NOT here. |

## User Constraints (from kickoff decisions + roadmap non-negotiables)

> No `CONTEXT.md` exists for this phase yet (`.planning/phases/12-.../` is empty). These constraints are copied from the ROADMAP milestone header + REQUIREMENTS kickoff decisions + PROJECT.md Key Decisions and are AUTHORITATIVE for planning.

### Locked Decisions (kickoff Q1–Q6, 2026-07-14)
- **Q1 = committed-but-writable** — `.memory/agreements/` is committed but NOT path-denied/CODEOWNERS-gated (frictionless capture; provenance-lint is the guard). [CITED: REQUIREMENTS.md:6, MEMORY-UPGRADE-PROPOSAL.md §6-Q1 / Out-of-Scope]
- **Q3 = per-guideline files** — one `<slug>.md` per guideline, not one monolith. [CITED: proposal §7b]
- **Q5 = retire via per-file `status`** — `status: retired`, not deletion. [CITED: proposal §7b / REQUIREMENTS.md:6]
- Q2 (`/agree` vs `/checkpoint`), Q4 (inject budget), Q6 (freshness) belong to Phases 13/14 — NOT this phase.

### Cross-cutting Non-Negotiables (all v2.1 phases)
- Contract-first / constitution gated: **ADR-0006 lands via the human-ratified path — an agent Write to `docs/adr/` is correctly denied by contract-guard.** [CITED: ROADMAP.md:382]
- Machines gate / humans ratify: agreements written ONLY on explicit user feedback (Phase 14 enforces; Phase 12 only scaffolds/documents the shape).
- The agreements channel is a **committed human-authored tier like `state/`, NOT derived** — never regenerated, never collides with `.memory/derived/`.
- Project decisions are **linked** (ADR / PROJECT.md Key Decisions), never restated in the PROCESS channel (§7c).
- Every surface change round-trips the emitter to both runtimes with **no model id** — **but the emit round-trip itself is Phase 15's job**, not this phase.
- GEN-04 core→example independence stays green (`.memory/` is outside the GEN-04 scan set — no risk).

### Deferred Ideas (OUT OF SCOPE for Phase 12)
- `inject.py` banner split / `WORKING_AGREEMENTS` block / activeContext-pointer reword → **Phase 13** (MEM2-02). Do NOT edit `tools/memory_regen/inject.py` here.
- `/agree` command + provenance/anti-invent lint → **Phase 14** (MEM2-04).
- Emit round-trip of any source (`harness/`) change to `.opencode/`+`.claude/` → **Phase 15** (MEM2-06 emit portion).
- Local memory web UI → **Phase 16**.
- Promoting `.memory/agreements/` into the constitution plane (path-deny+CODEOWNERS) → OUT (Q1 decided committed-but-writable). [CITED: REQUIREMENTS.md:50]

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MEM2-01 | Record a working-agreement as per-guideline `.memory/agreements/<slug>.md` (title, one-line rule, status active/retired, provenance "added because <user feedback>", added-date). Committed, user-authored, curated tier like `state/`, NOT derived. Entries link to ADRs/Key-Decisions, never restate project decisions. | SC1/SC3 below — exact scaffold location, entry-shape recommendation, .gitignore analysis, README plane-table update, §7c linking anchor. |
| MEM2-03 | Reword distrust framing to data authority in 5 surfaces; no session-start surface says "confirm before trusting" grounded context. | SC2 below — verbatim current quotes + exact reword targets per surface; AGENTS.md managed-block analysis. |
| MEM2-06 (ADR-0006 authoring portion ONLY) | Author ADR-0006 recording the memory-model change via the human-ratified constitution path. Emit portion is Phase 15. | SC4 below + dedicated "ADR-0006 Authoring Path" section — the deny is expected; the `GOLDEN_APPROVE_HUMAN` route. |
</phase_requirements>

## Project Constraints (from CLAUDE.md / AGENTS.md)

- **No model identifier** in any repo artifact (commits, PRs, code comments, emitted trees). [CITED: CLAUDE.md 모델 아이덴티티]
- **Two-plane memory:** derived is machine-managed (never hand-edit); decisions go in append-only ADR. The new agreements tier is a THIRD committed-but-human-authored posture (like `state/`) — reconcile the README's "three planes" table to four. [CITED: AGENTS.md:82-88, .memory/README.md:9-15]
- **Constitution-plane-is-gated** is a restated non-negotiable; `docs/adr/**` is CODEOWNERS-gated + contract-guard-denied to agents. [CITED: AGENTS.md:88-96, CODEOWNERS]
- **GSD workflow enforcement:** file edits go through a GSD command. [CITED: CLAUDE.md GSD Workflow Enforcement]
- **Contract-first:** `contracts/` wins over code; but agreements are NOT contract data (behavior/methodology only) — no golden/drift machinery applies. [CITED: proposal §2 location-&-gating]

---

## SC1 — Scaffold `.memory/agreements/` as a committed, human-authored tier (MEM2-01)

### Current state (verified)
`.memory/` today holds exactly (verified by `find`):
```
.memory/README.md                        # committed plane declaration
.memory/.inject-disabled                 # marker (injection disabled until MEM2)
.memory/derived/contracts-index.md       # committed-derived (the ONE tracked exception)
.memory/state/activeContext.md           # committed volatile state
.memory/state/progress.md                # committed volatile state
```
There is **no** `agreements/` tier and **no** schema/fixture convention for memory (a `find` for memory schemas/fixtures returned nothing — only `contracts/` uses `.schema.json`, and that is the constitution plane). [VERIFIED: find over repo]

### How `state/` establishes itself as a committed (non-derived) tier — the model to copy
The mechanism is **purely `.gitignore` + README declaration**, not a schema. `.gitignore` ignores only the derived plane contents-form: [VERIFIED: .gitignore:17-24]
```
.memory/derived/*
!.memory/derived/contracts-index.md
```
`.memory/state/**` and `.memory/README.md` are tracked by default (nothing ignores them). `.memory/README.md:43-53` declares STATE as "committed volatile state (D-03)". [VERIFIED: .memory/README.md:43-53]

**Implication for `.memory/agreements/`:** because only `.memory/derived/*` is ignored, `.memory/agreements/**` is **tracked by default — NO `.gitignore` change is needed** to make it committed. BUT git does not track empty directories, so the scaffold MUST include at least one committed file (a seed entry, a `_TEMPLATE.md`, or a tier-README) or the directory will not exist in git. This satisfies SC1's "scaffolded (empty or seed)".

### Recommended entry shape (house style)
Proposal §7b defines the per-file content: **title + one-line rule + `status` (active/retired) + provenance stamp ("added because <user feedback>") + added-date.** [CITED: proposal §7b, MEM2-01]

House-style options for encoding it:
- **RECOMMENDED — markdown + YAML frontmatter.** Mirrors the repo's established authored-surface convention (`harness/skills/*/SKILL.md`, `harness/commands/*.md`, and each MADR uses a structured header). Frontmatter carries `status`, `added` (ISO date), `provenance`; the body carries title + one-line rule + link(s) to ADR/Key-Decisions. This makes the Phase-14 provenance lint trivial (parse frontmatter with the existing `tools/harness_lint/frontmatter.py` parser — it already exists). [VERIFIED: tools/harness_lint/frontmatter.py exists]
- Alternative — flat markdown with labelled lines (no frontmatter). Simpler but the lint would regex the body. Not recommended given a frontmatter parser is already in-tree.

Suggested seed file `.memory/agreements/<slug>.md` skeleton (planner finalizes exact keys):
```markdown
---
status: active            # active | retired
added: 2026-07-14         # ISO date
provenance: "added because <verbatim user feedback>"
---
# <Title — the working-agreement in a few words>

<one-line rule — the essence, methodology/working-style only>

Related: [ADR-0006](../../docs/adr/0006-...md) / PROJECT.md §Key Decisions  # LINK, never restate (§7c)
```

### Where to document the shape
- **Primary:** add a 4th row/section to `.memory/README.md`'s "planes at a glance" table (currently titled "Three planes" — must become **four**). Document PROCESS/agreements as: committed ✅ / regenerated ❌ / human-authored via feedback / curated (add-on-feedback, explicit-retire). [VERIFIED: .memory/README.md:9-15 table]
- **Secondary (recommended, aligns with SC1 "documented"):** add the committed agreements tier to `harness/skills/two-plane-memory/SKILL.md`'s tier map (it already enumerates state / committed-derived / gitignored-derived sub-tiers at lines 30-46). NOTE: this is `harness/` source — the edit is in scope but its EMIT is Phase 15.
- The entry shape itself: document inline in `.memory/README.md` (or a short `.memory/agreements/README.md`) + ship a `_TEMPLATE.md` or a real seed as the fixture. There is no JSON-schema precedent for memory, so a documented markdown template IS the house-style "schema/fixture".

### Verify SC1
- `git ls-files .memory/agreements/` returns ≥1 tracked file (proves committed + non-empty).
- `.memory/agreements/` is NOT matched by `.gitignore` (`git check-ignore .memory/agreements/<seed>.md` exits non-zero / empty).
- `.memory/README.md` table lists 4 planes and marks agreements committed + never-regenerated.
- No file under `.memory/agreements/` is written by any generator (grep `tools/memory_regen` for `agreements` → must be absent; it must never collide with `derived/`).

---

## SC2 — Reword distrust framing to data authority in 5 surfaces (MEM2-03)

The goal: **preserve the data-authority meaning** ("contracts/ + docs/adr/ win a *data* conflict") while removing epistemic phrasing ("a hint, not truth", "confirm before trusting", bare "provisional") that reads as "distrust your own grounded work". None of the 5 surfaces literally contains "confirm before trusting" (that exact phrase lives in `inject.py:96-99`, which is **Phase 13**) — they carry the sibling phrasings "hint, not truth" / "provisional". Reword each to a data-scoped statement.

### Surface 1 — `.memory/README.md` (lines 5-8 header + 43-53 STATE section)
Current (verbatim): [VERIFIED: .memory/README.md]
- L5-8: "It is not itself a derived artifact — edit it by hand only to refine the plane declaration."
- L50-53: *"State is **committed** (so it survives), but it is **provisional**: the SessionStart injector injects only a *pointer* to `activeContext`, never its body, under a banner declaring that `contracts/` and `docs/adr/` always override `.memory/state/` on conflict."*
**Reword:** keep "committed / pointer-only / contracts+ADR win on a **data** conflict"; drop the standalone "provisional" epistemic load — frame as "on a DATA conflict, `contracts/`+`docs/adr/` are authoritative; this is about which artifact wins a contradiction, not a reason to distrust grounded work." Also add the 4th plane row here (overlaps SC1).

### Surface 2 — `.memory/state/activeContext.md` (lines 3-5, the blockquote)
Current (verbatim): [VERIFIED]
> `PROVISIONAL — this file is a hint, not truth. contracts/ and docs/adr/ always override .memory/state/ on conflict. No secrets, tokens, credentials, or PII here. The SessionStart injector injects only a *pointer* to this file, never its body.`
**Reword:** replace "this file is a hint, not truth" with a data-authority line, e.g. *"DATA AUTHORITY — on a data conflict, `contracts/` and `docs/adr/` win over `.memory/state/`. This is a session progress log, not a reason to re-verify grounded work."* Keep the secrets/PII + pointer clauses.

### Surface 3 — `.memory/state/progress.md` (lines 3-4, the blockquote)
Current (verbatim): [VERIFIED]
> `PROVISIONAL — a hint, not truth. contracts/ and docs/adr/ always win on conflict. No secrets/PII. Durable decisions go in append-only docs/adr/, not here.`
**Reword:** same treatment — "a hint, not truth" → data-authority phrasing; keep "durable decisions → ADR".

### Surface 4 — `harness/skills/two-plane-memory/SKILL.md` (lines 31-33)
Current (verbatim): [VERIFIED]
> `It is **provisional**: contracts/ and docs/adr/ always override it on conflict. Decisions do NOT live here — they belong in append-only ADRs.`
**Reword:** "It is **provisional**" → "On a **data** conflict, contracts/ and docs/adr/ are authoritative over it". **EMIT NOTE:** this is `harness/` source; re-emit to `.opencode/skill/` + `.claude/skills/` is **Phase 15** — do NOT edit the generated copies in this phase.

### Surface 5 — `AGENTS.md` (lines 87-88)
Current (verbatim): [VERIFIED: AGENTS.md:87-88]
> `pointer-only, provisional-banner-first). Volatile .memory/state/ is **provisional** — contracts/ and docs/adr/ always override it on conflict.`
**Reword:** "is **provisional**" → data-authority phrasing.
**CRITICAL — no emit tension here:** these lines are at **87-88, OUTSIDE the `HARNESS-MANAGED` block which starts at line 97** (`<!-- BEGIN HARNESS-MANAGED -->` L97 … `<!-- END HARNESS-MANAGED -->` L106). The managed block is a pointer-only generated index (`tools/harness_emit` writes only that fenced region; "Everything OUTSIDE the HARNESS-MANAGED markers is preserved verbatim"). Therefore editing AGENTS.md:87-88 is a **hand edit of preserved human content** — it needs NO re-emit and is NOT Phase 15 work. [VERIFIED: AGENTS.md:97-106, tools/harness_emit/generate.py:230-303]

### Source-vs-generated tension summary (flagged per additional_context)
| Surface | Kind | Emit round-trip needed? | Owner |
|---------|------|------------------------|-------|
| `.memory/README.md`, `.memory/state/*` | committed, non-emitted | No | Phase 12 |
| `AGENTS.md:87-88` | outside HARNESS-MANAGED block (preserved verbatim) | **No** | Phase 12 |
| `harness/skills/two-plane-memory/SKILL.md` | `harness/` SOURCE (emitted to both runtimes) | **Yes — but deferred** | edit source in Phase 12; **re-emit in Phase 15** |

### Verify SC2
- grep the 5 surfaces for `hint, not truth` / `\bprovisional\b` (standalone epistemic use) → 0 hits after edit (or only in a data-scoped sentence).
- grep the 5 surfaces confirm each STILL states the data-authority rule (contracts/+adr win a conflict) — the meaning is preserved, only the framing changes.
- Confirm `tools/memory_regen/inject.py` is UNCHANGED (its reword is Phase 13 — `git diff` shows no `inject.py` edit).

---

## SC3 — Entry shape links to ADRs/Key-Decisions, never restates a project decision (MEM2-01/§7c)

### The linking anchors (verified)
- **ADRs:** `docs/adr/NNNN-*.md`, indexed in `docs/adr/README.md`. Next is **0006** (0005 is latest). [VERIFIED: ls docs/adr]
- **Key Decisions:** `.planning/PROJECT.md` `## Key Decisions` (line 90) — a markdown table cross-referencing ADRs (e.g. `[ADR-0002] ...`). [VERIFIED: PROJECT.md:90-102]
- House-style "link, not restate" precedent: ADRs themselves cross-link via `Complements:`/`Supersedes:` lines and a `## Links` section (see ADR-0005 `## Links`, ADR-0004 `## Links`). The agreements `Related:` line mirrors this. [VERIFIED: ADR-0005:114-123]

### The rule to encode
The agreements entry-shape spec MUST state: an entry is **working-style / methodology only**; a project/architecture decision belongs in `docs/adr/` + PROJECT.md Key Decisions and is **linked**, never restated (single-source-of-truth). [CITED: proposal §7c, REQUIREMENTS.md:51 Out-of-Scope]

### Verify SC3
- The entry-shape doc/template contains an explicit "link to ADR/Key-Decisions, never restate a project decision (§7c)" instruction.
- The seed entry (if any) demonstrates a `Related:` link, not a duplicated decision body.

---

## SC4 — ADR-0006 via the human-ratified constitution path (MEM2-06 authoring portion)

### The deny is expected and correct — mechanics (verified)
`tools/hooks/contract_guard.py` gates `PreToolUse(Write|Edit)` on `CONSTITUTION_GLOBS = ["contracts/**", "docs/adr/**", "golden/**"]`. `decide()`: if the (repo-relative) path is on the plane AND `approved` is false → **deny** with a message naming the `/golden-approve` + CODEOWNERS ratification path. `approved` is truthy ONLY when env `GOLDEN_APPROVE_HUMAN` is a non-empty, non-blank string (empty does NOT bypass). [VERIFIED: tools/hooks/contract_guard.py:42-98]

So an agent's naive `Write docs/adr/0006-*.md` is **correctly denied** — this is the design (ADR-0004 ratified this fail-open/human-gated posture). [VERIFIED: ADR-0004]

### The legitimate authoring route (precedent-backed)
There is an established, repeatedly-used path (NOT a bypass): the **human supplies the `GOLDEN_APPROVE_HUMAN` token**, which IS the human ratification act; the write then proceeds; CODEOWNERS on `/docs/adr/` is the merge-time backstop. Precedents in STATE.md:
- ADR-0002/0003: "landed via the human `GOLDEN_APPROVE_HUMAN` gate". [VERIFIED: STATE.md:157,162]
- ADR-0005 posture + STATE.md:218 explicitly for THIS phase: *"an agent Write to `docs/adr/` is correctly denied by contract-guard — the ADR lands via the human-ratified path (mirrors ADR-0004/0005)."* [VERIFIED: STATE.md:218]

**Concrete plan-expressible route:**
1. Agent uses `/adr` to **draft** the ADR-0006 content (next number = highest `docs/adr/NNNN-*` + 1 = **0006**; MADR sections; add a row to `docs/adr/README.md` index — never remove rows). [VERIFIED: harness/commands/adr.md:24-38]
2. The actual **Write to `docs/adr/0006-*.md` is a checkpoint:human-verify step** — it either (a) requires the human to have exported `GOLDEN_APPROVE_HUMAN` (the golden-approve-style flag = ratification), or (b) is performed by the human directly. The plan must NOT have the agent fabricate the token (agents are instructed never to). [VERIFIED: contract_guard.py:44-46 comment]
3. CODEOWNERS (`/docs/adr/ @hjung3113`) routes the PR to the human owner at merge — the merge-time ratification mirror. [VERIFIED: CODEOWNERS]

### ADR-0006 content (what it records)
The memory-model change: adding the 4th PROCESS/working-agreements channel (`.memory/agreements/`, committed human-authored, curated, injected as a directive) + scoping the provenance/"provisional" framing to data-authority. Use the MADR shape of ADR-0004/0005 verbatim: header block (`*MADR 4.x · plane: constitution ...*`, Status: accepted, Date, Deciders, Supersedes: —, Complements: [ADR-0002] domain-neutrality / the two-plane memory ADR lineage), then Context / Decision Drivers / Considered Options / Decision Outcome / Consequences / Links. Append-only: number 0006 is permanent, never edit an accepted ADR. [VERIFIED: docs/adr/README.md:9-21, ADR-0005 header]

### Verify SC4
- `docs/adr/0006-*.md` exists with MADR sections + Status: accepted; `docs/adr/README.md` index has a 0006 row (no rows removed).
- Behavioral proof the deny works: an agent Write to `docs/adr/` WITHOUT the token is denied (contract_guard emits the deny JSON) — this can be shown by the existing contract-guard test suite pattern; the ADR only lands with the human token / human write.
- No `GOLDEN_APPROVE_HUMAN` value is hardcoded anywhere in the plan or repo.
- ADR-0006 body **links** to (does not restate) the reworded surfaces + the agreements shape.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Next ADR number + MADR scaffold | Manual file with guessed number/format | `/adr` command (`harness/commands/adr.md`) | Already computes next number, enforces append-only, updates the index. |
| Making agreements "committed" | New gitignore rules / tracking config | Nothing — default-tracked (only `.memory/derived/*` is ignored) + one seed file | Empty dirs aren't tracked; a seed file is the whole mechanism (mirrors `state/`). |
| Parsing agreement frontmatter (Phase 14 lint) | New YAML parser | `tools/harness_lint/frontmatter.py` (in-tree) | Existing shared frontmatter parser — reuse in Phase 14; choose frontmatter shape now to match it. |
| Getting the ADR past the gate | `--no-verify` / fabricating the token / editing the hook | The `GOLDEN_APPROVE_HUMAN` human-supplied token + CODEOWNERS | The deny is the ratified design (ADR-0004). Bypassing it violates the core non-negotiable. |

**Key insight:** every mechanism this phase needs already exists (`.gitignore` posture, `/adr`, contract-guard, CODEOWNERS, frontmatter parser). Phase 12 invents NO machinery — it scaffolds data + edits prose + authors one ADR.

## Common Pitfalls

### Pitfall 1: Editing `inject.py` / the emitter in Phase 12
**What goes wrong:** the tempting "reword the banner too" pulls `tools/memory_regen/inject.py` (BANNER, activeContext pointer) and the emit round-trip into scope.
**Why:** those strings carry the same distrust tone. But they are **Phase 13 (MEM2-02)** and **Phase 15 (MEM2-06 emit)** respectively.
**Avoid:** scope Phase 12 to the 5 named human-facing surfaces + the scaffold + ADR-0006. Verify `git diff` touches no `inject.py`, no `tools/harness_emit`, no `.opencode/`/`.claude/` generated tree.
**Warning sign:** a plan task references `inject.py:41-44` or `EXPECTED_COMMANDS` or `harness_emit`.

### Pitfall 2: Editing the generated skill copy instead of the source
**What goes wrong:** rewording `.opencode/skill/two-plane-memory/...` or `.claude/skills/...` directly.
**Why:** those are emitter output; a re-emit overwrites them, and hand-editing generated trees violates the derived-never-hand-edit rule.
**Avoid:** edit ONLY `harness/skills/two-plane-memory/SKILL.md` (source). Leave the re-emit to Phase 15.
**Warning sign:** a find/replace target path under `.opencode/` or `.claude/`.

### Pitfall 3: Treating `.memory/agreements/` as derived or constitution
**What goes wrong:** adding a generator for it (derived), or path-denying it (constitution).
**Why:** Q1 = committed-but-writable; §7d = NOT derived. It is a THIRD posture: committed + human-authored + curated.
**Avoid:** no generator, no gitignore entry, no CODEOWNERS entry for `.memory/agreements/`. Just committed files + a documented shape.
**Warning sign:** `.memory/agreements/` appearing in `tools/memory_regen`, `.gitignore`, or `CODEOWNERS`.

### Pitfall 4: Restating a project decision in an agreement (violates §7c)
**What goes wrong:** a seed agreement duplicates an ADR/Key-Decision instead of linking it.
**Avoid:** the entry-shape spec + any seed must LINK (`Related: [ADR-xxxx]`), never restate. Methodology/working-style only.

### Pitfall 5: Agent fabricates `GOLDEN_APPROVE_HUMAN` to land ADR-0006
**What goes wrong:** the agent sets the env token itself to satisfy the gate.
**Why:** that defeats "humans ratify"; agents are explicitly instructed never to fabricate it.
**Avoid:** model the ADR write as a `checkpoint:human-verify` step — the human supplies the token or writes the file. CODEOWNERS backstops at merge.

## Runtime State Inventory

> This is a scaffold + doc-reframe phase, not a rename/migration. No stored-data keys, live-service config, OS-registered state, secrets, or build artifacts embed a string being changed. The "reword" is prose-only across 5 tracked docs — no runtime system caches the old wording.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no datastore keys the reword touches. | None. |
| Live service config | None — no external service holds this prose. | None. |
| OS-registered state | None. | None. |
| Secrets/env vars | `GOLDEN_APPROVE_HUMAN` is READ by contract-guard as the ratification flag — human-supplied, not renamed. | None (do not fabricate it). |
| Build artifacts | Emitted `.opencode/`/`.claude/` copies of `two-plane-memory/SKILL.md` become stale after the source reword — **but re-emit is Phase 15**, not this phase. | Flag for Phase 15; do NOT re-emit here. |

**Nothing found in a category:** stated explicitly above ("None — verified by …").

## Validation Architecture

`nyquist_validation: true` [VERIFIED: .planning/config.json:19] — section included.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.x (uv workspace) |
| Config file | root `pyproject.toml` (uv workspace) + `tools/harness_lint/pyproject.toml` |
| Quick run command | `uv run pytest tools/harness_lint/tests -q` |
| Full suite command | `uv run pytest -q` (non-example legs; .NET legs skip on egress-deny) |

### Phase Requirements → Test Map
| Req | Behavior | Test Type | Automated Command | File Exists? |
|-----|----------|-----------|-------------------|-------------|
| MEM2-01 | `.memory/agreements/` is committed (≥1 tracked file), not gitignored, not generated | structural | `git ls-files .memory/agreements/ \| grep .` + `git check-ignore -v .memory/agreements/*` (expect none) | ❌ Wave 0 (new tier — add a structural test if the phase wants a guard; otherwise assert via git in verify-work) |
| MEM2-01 | README declares 4 planes incl. agreements | structural/manual | grep `.memory/README.md` for the agreements row | manual |
| MEM2-03 | 5 surfaces reworded; no "hint, not truth"/standalone "provisional"; data-authority preserved | grep assertion | `grep -RnE "hint, not truth" <5 files>` → 0; `grep` each still states contracts/adr win a conflict | manual/grep |
| MEM2-03 | `inject.py` untouched | regression | `git diff --exit-code tools/memory_regen/inject.py` | existing |
| MEM2-06(ADR) | ADR-0006 exists, indexed, MADR-shaped; agent write denied without token | behavioral | existing contract-guard tests (`tools/hooks` suite) prove the deny; manual check ADR file + index row | existing (contract-guard) |
| GEN-04 | core→example independence stays green | guard | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -q` | ✅ existing |

### Sampling Rate
- **Per task commit:** `uv run pytest tools/harness_lint/tests -q` (fast; catches structural regressions).
- **Per wave merge / phase gate:** `uv run pytest -q` full non-example suite green before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] (Optional) `tools/harness_lint/tests/test_agreements_tier.py` — assert `.memory/agreements/` is tracked (≥1 file), not matched by `.gitignore`, and absent from `tools/memory_regen` outputs (guards Pitfall 3). Low effort; recommended so the committed-not-derived invariant is machine-checked, but SC1 can also be met by a git-based verify step.
- [ ] No framework install needed (pytest/uv already present).

*(If the phase opts out of the new test, SC verification falls back to the grep/git commands above in `/verify-work`.)*

## Security Domain

> `security_enforcement` not present in config (treat as enabled). This phase adds NO auth, session, crypto, or external-input surface — it edits docs + scaffolds committed markdown + authors one ADR. The only security-relevant control is the **constitution-plane access gate** (contract-guard + CODEOWNERS + `GOLDEN_APPROVE_HUMAN`), which this phase EXERCISES (does not modify).

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V4 Access Control | yes | contract-guard deny on `docs/adr/**` + CODEOWNERS merge gate + human `GOLDEN_APPROVE_HUMAN` token (ADR ratification). Do not weaken or bypass. |
| V5 Input Validation | minor | Phase 14 (not here) adds the provenance/anti-invent lint on agreement files. |
| V2/V3/V6 | no | No authN, session, or crypto surface. |

| Threat Pattern | STRIDE | Mitigation |
|----------------|--------|------------|
| Agent self-ratifies constitution change (fabricates token / edits hook / `--no-verify`) | Elevation of Privilege / Repudiation | Human-only `GOLDEN_APPROVE_HUMAN`; CODEOWNERS; append-only ADR (tamper-evident). Plan models the ADR write as human-verify. |
| Agent invents an unsolicited agreement | Tampering | Provenance stamp required by shape now; ENFORCED by Phase-14 lint (out of scope here, but the shape must carry the stamp so Phase 14 can check it). |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Markdown + YAML frontmatter is the right encoding for agreement entries (vs flat markdown). | SC1 | Low — either works; frontmatter just eases the Phase-14 lint. Planner/user may prefer flat. |
| A2 | The `GOLDEN_APPROVE_HUMAN`-token route is the operative human-ratification path for ADR-0006 (vs human writes the file directly). | SC4 | Low — both are legitimate; STATE.md:218 + ADR precedents confirm the token route. Either satisfies "human ratifies". |
| A3 | Adding the 4th tier to `two-plane-memory/SKILL.md` is desirable for SC1 "documented" (not strictly required by the SC wording, which lists the skill only under SC2 reword). | SC1/SC3 | Low — additive documentation; if skipped, README alone still satisfies "documented". |
| A4 | A dedicated `test_agreements_tier.py` is optional, not mandated. | Validation | Low — git-based verify covers it; a test just hardens it. |

**All other claims are `[VERIFIED]` against a repo file at path:line or `[CITED]` to the proposal/roadmap.**

## Open Questions (RESOLVED)

All three resolved by the Phase-12 plans (12-01 / 12-02 / 12-03), matching the recommendations below.

1. **Entry encoding: frontmatter vs flat markdown?**
   - Known: shape = title + one-line rule + status + provenance + added-date (§7b).
   - Unclear: exact key names / frontmatter vs body placement.
   - Recommendation: YAML frontmatter (`status`, `added`, `provenance`) + markdown body (title, rule, `Related:` link), to match `harness_lint/frontmatter.py`. Confirm at plan/discuss time; Phase 14's lint depends on this choice.
   - **RESOLVED:** 12-01 Task 1 ships the YAML-frontmatter entry shape (`status`/`added`/`provenance` keys + markdown title/rule/`Related:` link), matching `harness_lint/frontmatter.py` so Phase-14 lint reuses the parser.
2. **Seed content: empty tier (README + `_TEMPLATE.md`) vs one real seed agreement?**
   - SC1 allows "empty or seed". Recommendation: ship a `_TEMPLATE.md` (documents the shape, is a committed file that makes the dir exist) and OPTIONALLY one real seed only if a genuine user working-agreement already exists — do NOT invent one (machines-gate/humans-ratify; agreements come from user feedback).
   - **RESOLVED:** 12-01 ships `_TEMPLATE.md` + tier README only — no invented seed agreement (agreements come from user feedback).
3. **Does the phase want a machine guard (`test_agreements_tier.py`) now, or defer all agreement-lint to Phase 14?**
   - Recommendation: a tiny committed-not-derived structural test now (cheap, guards Pitfall 3); provenance-content lint stays Phase 14.
   - **RESOLVED:** deferred — no new pytest guard this phase; structural correctness is covered by the per-task grep/`test -f` asserts, and provenance-content lint stays Phase 14 (keeps the Phase-12 scope to model+docs+ADR).

## Sources

### Primary (HIGH — repo files, verified at path:line)
- `.planning/ROADMAP.md:384-397` — Phase 12 goal, SC1-4, requirements, milestone non-negotiables.
- `.planning/REQUIREMENTS.md:14-30,50-51,70` — MEM2-01/03/06 text, Out-of-Scope, MEM2-06 two-phase split.
- `.planning/MEMORY-UPGRADE-PROPOSAL.md` §2/§3/§5/§6/§7 — model, reframe, phase split, kickoff Qs, operator refinements (§7 authoritative).
- `.memory/README.md:5-15,43-53`; `.memory/state/activeContext.md:3-5`; `.memory/state/progress.md:3-4`; `harness/skills/two-plane-memory/SKILL.md:30-46`; `AGENTS.md:87-88,97-106` — the 5 reword surfaces + managed-block boundary.
- `.gitignore:17-24` — derived-only ignore (agreements tracked by default).
- `tools/hooks/contract_guard.py:42-98` — the deny mechanics + `GOLDEN_APPROVE_HUMAN`.
- `docs/adr/README.md:9-21`; `docs/adr/0004-*.md`; `docs/adr/0005-*.md`; `harness/commands/adr.md` — MADR format, append-only, `/adr` scaffold, next=0006.
- `.github/CODEOWNERS` — `/docs/adr/ @hjung3113` merge gate + enforcement caveats.
- `.planning/PROJECT.md:90-102` — Key Decisions anchor (§7c link target).
- `.planning/STATE.md:112,157,162,218` — ADR-via-token precedent + Phase-12 ratification note.
- `tools/harness_emit/generate.py:230-303` — AGENTS.md managed block is pointer-only, preserves outside-marker content.
- `tools/harness_lint/frontmatter.py` (exists) — reusable frontmatter parser for the agreement shape.

### Secondary / Tertiary
- None — no external sources needed; phase is fully internal.

## Metadata

**Confidence breakdown:**
- SC1 scaffold mechanics: HIGH — verified `.gitignore` + `state/` precedent + no schema convention.
- SC2 reword targets: HIGH — all 5 quotes verified verbatim; managed-block boundary verified.
- SC3 linking anchors: HIGH — ADR index + PROJECT.md Key Decisions verified.
- SC4 ADR path: HIGH — contract-guard code + CODEOWNERS + token precedent all verified.
- Entry-shape encoding recommendation: MEDIUM — house-style inference (A1), user may adjust.

**Research date:** 2026-07-14
**Valid until:** ~2026-08-14 (stable internal structure; re-verify only if `.memory/`, `contract_guard.py`, or the emitter change before planning).

## RESEARCH COMPLETE
