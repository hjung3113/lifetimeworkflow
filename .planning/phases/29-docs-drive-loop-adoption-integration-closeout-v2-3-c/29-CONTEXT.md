# Phase 29: Docs Drive Loop + Adoption Integration + Closeout - Context

**Gathered:** 2026-07-21
**Status:** Ready for planning (after Phase 28 lands — see Dependency note)
**Mode:** Autonomous smart-discuss — grey areas decided at Claude's discretion per explicit user instruction ("질문 하지말고 니 권장대로 처리해"). Every decision below adopts `29-RESEARCH.md`'s stated recommendation.

<domain>
## Phase Boundary

Add a bounded human-facing docs workflow, wire adoption seeding into it, and close all three v2.3 themes with the full gate fan-in. **This is the final phase of milestone v2.3.**

Requirements: DOCSUP-06, DOCSUP-07 (`.planning/REQUIREMENTS.md:38-39`).
Success criteria: `.planning/ROADMAP.md` `### Phase 29`, four observable criteria.

**IN scope:** the thin `/docs-update` command + `docs-upkeep` skill emitted byte-identically to both runtimes; the structural (tested, not prose) exclusion of accepted ADRs / `docs/reference/**` / `.memory/derived/**` / contracts / golden; `/adopt` proposing registry entries while being structurally unable to make a binding green; seeding the high-risk corpus and the adoption-runbook bindings; the milestone closeout with the full gate fan-in.

**OUT of scope:** anything Phase 28 owns (registry, ledger, guard, digest, five states, ratchet, derived queue, SessionStart pointer); instance-local registry overlays.

## Dependency note

Phase 28 must land first. At research time Phase 28 had RESEARCH + CONTEXT committed but no plans and no code — `tools/docs_guard/` did not exist. `29-RESEARCH.md` tags every Phase-28 interface it binds to as ASSUMED (registry/ledger paths, exit codes 0/1/3, the five states, ADR dispositions, the docs-guard CI job). **The planner must re-verify those interfaces against the shipped Phase 28 code before writing tasks**, and treat any divergence as a plan input, not a surprise at execution time.

</domain>

<decisions>
## Implementation Decisions

All of `29-RESEARCH.md`'s recommendations are ADOPTED, including its four open questions.

| # | Grey area | Decision | Rationale |
|---|-----------|----------|-----------|
| D-01 | Authoring location + template for the new surface | `harness/commands/docs-update.md` + `harness/skills/docs-upkeep/SKILL.md`. Template = the `/adopt` + `brownfield-adoption` pair (Phase 27-06), not `/docs-sync` and not `/refresh-memory`. | `/adopt` is the closest analog: a thin command over a human-gated, exit-code-routed tool. DOCSUP-06 says "one THIN command" — the skill carries the procedure. |
| D-02 | Emit round-trip obligations | Follow the seven-step round-trip in `29-RESEARCH.md` §1.4. **`caps.py:129-144` `EXPECTED_SKILLS` 12→13 and `test_coexist.py:39,64,65` command count 24→25 must move in the SAME change.** Frontmatter constraints are enforced, not advisory: the command description must literally contain "use" or "when" (`test_commands.py:34`), and skill descriptions must be mutually distinct (`test_skills.py:108`). | These are real gate tests; missing one reds the suite at emit time. |
| D-03 | The `emit-drift` untracked-file blind spot | Explicitly verify the emit round-trip with a check that sees UNTRACKED files (e.g. `git status --porcelain`), not bare `git diff`. | `emit-drift` (`ci.yml:213`) uses bare `git diff`, which is blind to untracked files — four newly emitted files can pass it green while the tree is wrong. This is carried finding 15-REVIEW CR-01; do not re-inherit it. |
| D-04 | `/docs-update`'s input: derived queue or re-run the guard? | **Re-run the guard** — `python -m tools.docs_guard` with fixed argv. Never read the derived queue as the source of truth. | Settled by the fresh-clone case: `.gitignore:23` is the contents-form `.memory/derived/*` with only `contracts-index.md` re-included, so the queue is never present in a clone. Reading it yields a FALSE GREEN ("no work") on fresh checkout. |
| D-05 | Exit-code routing for `/docs-update` | `0` → stop, nothing to do. `1` → the only working state: draft a bounded human-doc edit OR an exact review disposition, then route to the existing `/review` + `/verify-work` flow. `3` → refuse to draft anything; the registry is invalid, so fix the registry and do not touch docs. | Binds to Phase 28 D-05. Exit 3 is a different operator action; conflating it with 1 would have an agent editing docs to "fix" a malformed registry. |
| D-06 | How the five exclusions become STRUCTURAL, not prose | One pure `exclusion_reason(target) -> str | None` helper in `tools/docs_guard/`, which **imports** `CONSTITUTION_GLOBS` and `DERIVED_GLOBS` from their existing homes rather than retyping them, and uses resolved-path + lowered-candidate matching copied from `refuse_unsafe_destination`. Failing test: `tools/docs_guard/tests/test_exclusions.py`, ≥6 rows including a negative control, with the RED run recorded. | Importing means deleting a glob from its home fails repo-wide. Copying the resolve+lower matching is mandatory — otherwise 27.1's CR-01 (`./contracts/x`, `CONTRACTS/x` bypass) replays verbatim on a new surface. A skill body that merely *says* "don't edit ADRs" does NOT satisfy SC-1; a grep-the-SKILL-body wiring lint is worth having but is not the control. |
| D-07 | DOCSUP-07 — how `/adopt` proposes without self-approving | `/adopt` may draft registry rows. It must be structurally unable to write the **ledger**, because the ledger (not the registry) decides greenness. Enforce with a narrow `REVIEW_LEDGER_GLOBS` refusal at the existing single choke point `refuse_unsafe_destination` (`tools/adoption_apply/apply.py:109`), with its own constant and its own exception type. **Planned in Phase 28** (relayed to planner-28) — Phase 29 consumes and tests it end-to-end. | Do NOT close this by widening `CONSTITUTION_GLOBS`: that would force every ordinary human review commit to carry the ratification token and would break the disjoint-domain invariant at `contract_guard.py:16-20`. |
| D-08 | The seeding commit | Must carry a `checkpoint:human-verify` — the agent drafts, the **human** lands the ledger half. | Otherwise the plan contradicts its own control: an agent that can land a ledger row has self-approved a binding. |
| D-09 | Seed corpus (research Q1) | Two highest-risk required seeds: `docs/how-to/task-lifecycle.md` (embeds literal CLI invocations at :10, :20-21, :28) and `harness/skills/brownfield-adoption/SKILL.md` (already went out of sync once — that is *why* 27.1 SC-3 exists). Target ~6 required + 2 advisory bindings. Targeting `harness/**` source is legal; the emitted `.opencode/` / `.claude/` twins are structurally rejected by `DERIVED_GLOBS` — make that a test row. **Do NOT seed `AGENTS.md` or `CLAUDE.md`.** | Those two carry the emitter-owned HARNESS-MANAGED fence (`AGENTS.md:98-107`); a drafted edit inside the fence is reverted on re-emit and reds `emit-drift`. |
| D-10 | Binding deletion | Add a **binding-count ratchet** beside `uncovered_max` in the ledger. **Planned in Phase 28**; Phase 29 verifies it end-to-end. | Silently deleting an inconvenient binding is otherwise unguarded for targets outside the corpus definition. |
| D-11 | SC-4 CI fan-in delta | **Net new CI jobs from Phase 29: ZERO.** SC-4 is an inventory to *confirm green*, not a to-do list. All 11 jobs already exist (`ci.yml`, `gate.needs` at `:285`); the docs-guard job is Phase 28's. Model-identifier lint = `test_agents.py:129-135` + `test_opencode_config.py:81,89` + `validate.py:192,215-222`; injector budget = `test_inject_assembler.py:32-33,152-157` — both already inside `core-suite`. | Verified job-by-job in `29-RESEARCH.md` §6. |
| D-12 | `git diff --check` (research Q2) | Keep it a **verification command**, not a CI job. | It has never been a CI job (repo-wide grep: zero hits; it appears only in VERIFICATION/PLAN prose). A job would double-report `polyglot_lint`. |
| D-13 | Does Phase 29 need its own ADR? (research Q6) | **No** — provided Phase 28's ADR is scoped to cover the docs-plane agent-authority boundary ("agents may propose registry rows; only a human may author a ledger disposition; the ledger is the greenness authority"). That widening was relayed to planner-28 while Phase 28 was still being planned. If the shipped Phase 28 ADR does NOT carry that scope, Phase 29 must author a superseding ADR — verify before planning. | ADRs are append-only / supersede-don't-edit; once accepted, 29 cannot amend 28's, and a second full ratification is expensive. |
| D-14 | Milestone closeout shape | Use `.planning/v2.1-MILESTONE-AUDIT.md`'s frontmatter as the template (scores / gaps / nyquist / tech_debt). `nyquist_validation: true` is set in config, so **each v2.3 phase needs a finalized VALIDATION.md**. The per-requirement evidence table is the audit's evidence — **not** STATE.md, which is already stale (says 27.1, `completed_phases: 7`). | Concrete precedent beats inventing a closeout format. |
| D-15 | Standing residuals must survive the closeout | Carry `tools/hooks/secret_scan.py:44-47` (pattern list hardcoded instead of read from the contract) into the v2.3 audit's `tech_debt`, together with 27.2's residuals (AD-01 barrier-timeout legibility, AD-02 `fcntl` singleton monkeypatching, the pre-existing `I001` on `adoption_apply/cli.py`) and 27.1's (IN-02 flock/NFS, WR-08 parent-dir symlink TOCTOU). | Otherwise a fence that has been deliberately carried since 26.2 silently disappears at milestone close. |

</decisions>

<code_context>
## Existing Code Insights

Full citations in `29-RESEARCH.md` (HIGH confidence on repo machinery — every citation read from source). Load-bearing pointers:

- `.gitignore:23-24` — VERIFIED: the derived queue is already ignored; zero change needed, and this is what forces D-04.
- `tools/hooks/contract_guard.py:16-20,43` — the disjoint-domain invariant and `CONSTITUTION_GLOBS`; why D-07 does not widen it.
- `harness/permission-matrix.json:27-33`, `.github/CODEOWNERS:26-32` — verified: the ledger is in neither, hence the hole D-07 closes.
- `tools/adoption_apply/apply.py:109` — `refuse_unsafe_destination`, the single choke point D-07 extends.
- `.github/workflows/ci.yml` — 11 jobs; `gate.needs` at `:285`; `emit-drift` at `:213` (the bare-`git diff` blind spot behind D-03).
- `tools/harness_emit/caps.py:129-144`, `test_coexist.py:39,64,65`, `test_commands.py:34`, `test_skills.py:108` — the emit-time counters and frontmatter gates D-02 must move together.
- `docs/how-to/task-lifecycle.md:10,20-21,28`, `harness/skills/brownfield-adoption/SKILL.md` — the two highest-risk seed targets (D-09).
- `AGENTS.md:98-107` — the HARNESS-MANAGED fence that excludes `AGENTS.md`/`CLAUDE.md` from seeding.
- `.planning/v2.1-MILESTONE-AUDIT.md` — the closeout template (D-14).

</code_context>

<specifics>
## Specific Ideas

- **Anti-pattern fence, still active.** Every control-shaped change gets its adversarial-input table authored FIRST and a RED run recorded against pre-fix code. For this phase that means at minimum: the exclusion helper (`./contracts/x`, `CONTRACTS/x`, an emitted `.opencode/` twin, and a negative control that must stay ALLOWED), and the `/adopt`-cannot-write-the-ledger refusal.
- **Re-verify Phase 28's shipped interfaces before planning tasks** — the research bound to them as ASSUMED.
- Milestone closeout runs the SC-4 fan-in and reports actual numbers, not claims.

</specifics>

<deferred>
## Deferred Ideas

- Instance-local (`examples/**`) docs registry overlay — seam left open by Phase 28 D-14, not built.
- `tools/hooks/secret_scan.py:44-47` reading the contract — carried since 26.2; goes to the milestone audit's tech_debt (D-15), not fixed here.
- A grep-the-SKILL-body wiring lint — worth having, explicitly NOT a substitute for the structural exclusion control (D-06).

</deferred>
