# Requirements — v2.5 De-ceremony

Scoped to milestone v2.5 (phases 39–46). Ratified design: `.planning/research/v2.5-scoping-FINAL.md`
(three-round two-model panel; see `v2.5-scoping-BRIEF.md` §0 for the binding constraint,
`v2.5-carryforward-DOSSIER.md` for the verified facts, `v2.5-scoping-ROUND3-PREMISE.md` for the
DEV/PRODUCT boundary). Previous milestone's requirements: `.planning/milestones/v2.4-REQUIREMENTS.md`.

**Milestone goal:** stop the harness from verifying itself and start it serving its stated purpose —
delete ~16k LOC of self-verification machinery, take the gates a human must personally *author* from
five kinds to zero, and give the **product** an honest lifecycle, since GSD governs only this dev
checkout and is never shipped.

## The binding constraint (governs every requirement below)

Never expand scope beyond the purpose by adding verification gates, security layers, or ceremony. The
default answer to "should we also gate X?" is **NO**. The surface may not grow without retiring at
least as much. A requirement that adds a control proving the harness cannot bypass itself is out of
scope by definition — that is the class this milestone removes.

## The four goal functions every requirement must serve

① per-package convention consistency · ② interface-contract consistency between packages ·
③ an LLM understanding cross-project relationships better than in a generic repo · ④ long-horizon
maintainability.

## Theme A — Decision + Self-Gate Teardown (Phases 39–41)

- [x] **CER-01** *(NEW, Phase 39)*: One **human-ratified ADR-0012** records that **CI + the merge are
  the authority**, names every surface this milestone deletes, supersedes ADR-0001's
  constitution-member list (golden leaves the core) and ADR-0010 (the review ledger retires), and
  **accepts ADR-0011** by filling its empty `Date`/`Deciders` while recording that its code landed
  (`bc9a6d9`) before its ratification. It declares the bash surface a **permanent residual by design**
  so it cannot return as debt. (④)
- [x] **CER-02** *(NEW, Phase 39)*: The same ADR ratifies the **DEV/PRODUCT boundary** — DEV is this
  checkout (Claude Code + GSD, never installed); PRODUCT is what
  `tools/adoption_scan/destinations.py::_CATEGORY_GLOBS` installs into a target monorepo, run on
  opencode and Claude Code by a weaker in-house model — with the operative rule that **no product
  capability may be declined on the ground that GSD covers it**; only a named shipped artifact may
  cover it. Re-collapsing the two scopes then costs a superseding ADR. (④)
- [x] **CER-03** *(NEW, Phase 39)*: **RAT-4, RAT-5 and the per-tool deny spelling reach a recorded
  disposition as obsolete-by-deletion** — one decision, no mechanism, on the ground that every
  human-ratification gate here assumes reviewer ≠ author while this repo has one owner. v2.4's
  SEAL-05 ("portable ratification record") is explicitly **withdrawn**, not deferred. (④)
- [ ] **CER-04** *(NEW, Phase 40)*: `tools/skill_registry` (611 LOC), `harness/skills/registry.lock`
  and CI `registry-lock` are **deleted**, with the job removed from `gate.needs` in the same commit.
  This must land **before any skill deletion** — the lock's declaration source is
  `harness/disciplines.toml` (`registry.py:44`) and `_disciplines_by_skill` raises on its absence
  (`registry.py:105-110`), so a later ordering breaks structurally. (④)
- [x] **CER-05** *(NEW, Phase 41)*: The **docs-review plane is deleted entirely** — the 8 `[[binding]]`
  rows unbound first, then `tools/docs_guard` (6110 LOC), `docs/.docs-review-ledger.toml`, hook
  `ledger_guard` and its `path_deny_globs` entry, `/docs-update`, skill `docs-upkeep`,
  `contracts/harness/docs/*`, CI `docs-guard` and its `gate.needs` entry. Verified reason the
  severity-flip alternative was rejected: `guard.py:383-399` classifies `BROKEN` before every staleness
  check and `cli.py:6-13` exits 1 on `BROKEN` regardless of severity — and every deletion in this
  milestone produces `BROKEN`. **The CI fan-in gate goes green as a result.** (④)

## Theme B — Plane Removal + Install-Set Repair (Phases 42–44)

- [ ] **CER-06** *(NEW, Phase 42)*: `adoption_apply` is **decoupled from task-control** — no
  `tools.task_control.manager.show`, no task-revision binding, no `GOLDEN_APPROVE_HUMAN` — by inlining
  the ~60-LOC atomic create/replace sequence, and the 7 redaction regexes it needs are inlined from
  `gate-registry.json` into `adoption_scan` (which already owns its own `SECRET_PATH_GLOBS` for the
  same reason, `scan.py:52-54`; the live consumer is `scan.py:110-112`). Adoption becomes
  draft → apply → PR review. (④)
- [ ] **PROD-01** *(NEW, Phase 42)*: **The product receives the code its own artifacts invoke.**
  `_CATEGORY_GLOBS` (`destinations.py:142-181`) contains no `tools/**` glob today, so a target monorepo
  gets every command that shells `uv run python -m tools.X` (`orient.md:6-7`), gets
  `.github/workflows/**` (`:176`) running the same modules, gets `pyproject.toml` stubs (`:177-178`) —
  and gets **none of the Python**. The surviving `tools/**` is added to the install catalogue, and the
  fix is a data row, not a mechanism. (①②③④ — without it the product is inert)
- [ ] **CER-07** *(NEW, Phase 43)*: The **task-control lifecycle plane is deleted whole** — 8 `tools/`
  packages (7021 LOC: `task_control`, `task_packet`, `risk_router`, `evidence`, `handoff`,
  `discipline`, `capability`, `lifecycle_eval`), the 7 task-control contracts, commands
  `intake · phase-gate · handoff · discipline`, hook `resume_gate`, the 5 discipline skills,
  `harness/{capabilities,disciplines,risk-policy}.toml`, `.workflow/tasks/`, and CI `lifecycle-eval`
  with its `gate.needs` entry. `memory_regen`'s active-task block (`inject.py:165-195`) is stripped
  while the activeContext pointer (`:148-162`) stays. **No residue package**: a Python state manager is
  unreachable in the product by construction. (④)
- [ ] **CER-08** *(NEW, Phase 44)*: The **non-goal surface is deleted** — `secret_scan` **with no
  replacement CI job** (a security layer not motivated by a threat this repo faces),
  `deny-domains.{json,schema.json}`, `gate-registry.json` and their `DATA_CONTRACT_PATHS` entries,
  `tools/memory_ui` (1756 LOC), `tools/strangler_guard` + `/strangler-step`, `/pipeline` + skill
  `pipeline-map` + `[pipeline].edges`, skill `gate-model`, and `/component`'s topology-registration
  half (steps 1–3 survive as an ① mechanism). (④)
- [ ] **CER-09** *(NEW, Phase 44)*: The **golden stack relocates to `examples/log-parser/`** —
  `tools/golden_runner`, root `golden/`, `/golden`, `/golden-approve`, skills `golden-testing` and
  `golden-debug`, CI `golden`. Ground: `resolve_dotnet()` (`runner.py:78-85`) puts .NET code in the
  core, which ADR-0002(b) forbids in its own words, and `compare()` calls `normalize_tsv`
  unconditionally (`:137-139`) with `baseline.{verified,received}.tsv` hardcoded (`:64-75`). Making it
  format-pluggable would be additive machinery the constraint forbids. The core no longer promises
  golden parity; each instance owns that evidence. (④)

## Theme C — Projection Repair + the Product's Lifecycle (Phases 45–46)

- [ ] **CER-10** *(NEW, Phase 45)*: Both runtime trees **re-emit clean** after the deletions:
  `caps.py` frozensets, `emit-manifest.json` and `HARNESS_SIGNATURES` (`merge.py:86-95`) updated;
  `contracts/.hashes/manifest.json` rebaselined; `docs/reference/**`,
  `.memory/derived/contracts-index.md` and the syrupy snapshots regenerated; `gate.needs` repaired.
  `emit-drift` and `stale-derived` are green with an empty diff. (④)
- [ ] **CER-11** *(NEW, Phase 45)*: **Prose that names a deleted surface is scrubbed**, including the
  two claims **outside** the emitter's managed block that a re-emit will therefore not repair: root
  `AGENTS.md:8-9` (names the guard hooks as "the true backstop" — false after phase 44) and
  `AGENTS.md:52-62` (golden-path table naming `tools.golden_runner`, relocated by CER-09). Every
  surviving command, skill and persona is free of dangling references. (④)
- [ ] **PROD-02** *(NEW, Phase 46)*: **The product has a lifecycle, authored where it already lives.**
  `harness/agents/orchestrator.md` — which already declares itself *"the only planner in the deployed
  harness (GSD is dev-side and is not emitted)"* (`:48`) — is rewritten: its 8 dangling citations
  stripped, its 25-row routing table (`:90-129`) retired, and **4 route sections** added —
  `small-change · bugfix · feature · contract-change` — each with an explicit stop condition, plus the
  delegation-packet fields and the **six-field completion contract** (`Outcome · Artifacts/changes ·
  Verification · Decisions/assumptions · Risks/unresolved · Next command`,
  `WORKFLOW_CONTRACTS.md:39-46`). `contract-change` exists because it is the one route where this
  harness is not repo-agnostic; `research` is deliberately absent (it terminates in a document and
  `explorer` + `fan-out-synthesize` + `context-budget` already cover it). (②③)
- [ ] **PROD-03** *(NEW, Phase 46)*: Each deleted discipline skill leaves **one operative sentence** in
  the route that needed it — bugfix→reproduce before fixing; feature→settle vocabulary first;
  contract-change→contract entry, then failing case, then code; all→red before green. Five skills
  become ~20 lines of prose in a file already being rewritten. (①)
- [ ] **PROD-04** *(NEW, Phase 46)*: **One** new command `harness/commands/flow.md` is the product's
  named entry point (the driver is the weakest model in the picture and has no GSD habit to fall back
  on), and **route · step · next command** are recorded in the already-shipped
  `.memory/state/activeContext.md` (`destinations.py:151`), written by the existing `/checkpoint`
  (`checkpoint.md:24-38`) and read by the existing `/orient` (`orient.md:2-5`). **No `.flow/state.md`,
  no router agent, no new skill, no new contract, no new CI job, no new hook** — net **+1 command,
  +0 everything else**, against 9 commands retired. (③④)
- [ ] **PROD-05** *(NEW, Phase 46)*: Each route's *Repository evidence* section is filled from
  **monorepo facts** the harness alone can compute — in v2.5 the existing `harness_config` +
  `contract_graph` facts, worded so v2.6's `/impact` slots in without a rewrite. This is the
  differentiator: the vendored matt flows are repo-agnostic; these are not. **Zero flow artifacts are
  imported** — the vendored tree stays a pinned DEV-only reference, and the mattpocock upstream skills
  are **not** a product dependency even optionally (the vendored contract says *stop* when one is
  missing, `UPSTREAM_SKILLS.md:34-42`, so "degrades gracefully" was false). (②③)

## Future Requirements — v2.6 Minimal Monorepo Core (phases 47–50)

Deferred by design, not lost. Smallest goal-complete subset = all of v2.5 + **MONO-01 + MONO-03**.

- **MONO-01** *(Phase 47)* — **Package facts**: extend `adoption_scan/detect.py`'s existing manifest
  detection (`:41-47,100-121` — `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, `*.csproj`)
  into a committed **derived** package + dependency graph feeding `contract_graph`; hand-declared
  `[[components]]` demoted to an override slot. **Report-only, no gate.** (③)
- **MONO-02** *(Phase 48)* — **Convention profiles**: nearest-wins per-package convention data +
  language→lint/test command mapping, populated by `/component` step 2. (①)
- **MONO-03** *(Phase 49)* — **`/impact`**: one command over `contract_graph.query`'s existing
  `direct`/`reverse`/`transitive` (`query.py:29,39,55`) plus package facts; fills PROD-05's evidence
  slot. On demand only — **no SessionStart injection**. (②③)
- **MONO-04** *(Phase 50)* — **`harness-author`** (one skill, Q&A with grounded `path:line` defaults,
  **absorbing `skill-creator`** so net skills ±0, zero new packages/commands/contracts, output
  runtime-neutral under `harness/` only, codebase scan before any question; **presupposes PROD-01**)
  **+ managed adopt/upgrade** (simplified `/adopt` as a managed install/update with one manifest and a
  conflict report; **does not start without a real multi-package target** — carries forward if none
  exists). (①③④)
- **EVOL-01/02/03**, **TCP-F05** — carried from v2.4 and now largely obsolete: EVOL-01
  (impact-driven task-evidence policy) and TCP-F05 (signed attestation + STRICT rollback) die with the
  lifecycle plane; EVOL-03 (`examples/**` docs-registry overlay) dies with the docs plane. Only
  **EVOL-02** (contract versioning / compatibility engine) survives as a genuine future item.

## Out of Scope

| Item | Reason |
|------|--------|
| Any gate whose purpose is to prove the harness cannot bypass itself | The class this milestone deletes. `deny-domains.json`'s own `_note` says no hook reads it and a drift test over it would prove a file equals itself. |
| A replacement secret-scanning CI job | A security layer not motivated by a threat this repo faces. The constraint's default answer is NO. |
| Any human-must-**author** step (ledger row, approval token, ratification record) | Reviewer ≠ author is false here. A solo owner satisfying such a gate is self-signing: cost without protection. The human reviews and merges. |
| Importing matt-flow agents/commands (19 commands, 27 agents) | Budget: the proposal was +5 agents/+1 command/+2 contracts/+1 state file retiring nothing. Also mechanically blocked — the vendored routes hard-require `.opencode/workflows/scripts/*.sh` (`flow-small-change.md:110,135,139`) and `.opencode/` is emitter-owned. |
| A runtime dependency on `npx skills@latest add mattpocock/skills` | The vendored contract says *stop* when an upstream skill is missing, so the "graceful degrade" premise was false. Ship self-contained prose. |
| `.flow/state.md` or any second state plane | `.memory/state/activeContext.md` already exists, is committed, ships, and is read/written by existing commands. |
| A `flow-router` persona | Widens `caps.py:57` `EXPECTED_PERSONAS`, the one anti-sprawl invariant kept on purpose, and duplicates what the sole primary exists to do. |
| Generalizing GEN-04 into a dependency-matrix **gate** | `test_core_no_example_dep.py` is a path guard plus a prose-token tier, not a matrix. Promote only when a real monorepo produces a forbidden edge. v2.6's package facts are report-only. |
| Repairing GitHub's trust model (branch protection, reviewer eligibility, CODEOWNERS for a solo owner) | Repository administration, not harness behaviour. |
| Restoring the 5 discipline skills, or a `PROGRESS.md`-style second control plane | One operative sentence each, in the route that needs it. |
| Editing accepted ADRs | Append-only; clarify by superseding. |
| Pact / broker contract testing, a second orchestrator, autonomous contract extraction | Standing exclusions carried from prior milestones. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CER-01 | Phase 39 | Not started |
| CER-02 | Phase 39 | Not started |
| CER-03 | Phase 39 | Not started |
| CER-04 | Phase 40 | Not started |
| CER-05 | Phase 41 | Complete |
| CER-06 | Phase 42 | Not started |
| PROD-01 | Phase 42 | Not started |
| CER-07 | Phase 43 | Not started |
| CER-08 | Phase 44 | Not started |
| CER-09 | Phase 44 | Not started |
| CER-10 | Phase 45 | Not started |
| CER-11 | Phase 45 | Not started |
| PROD-02 | Phase 46 | Not started |
| PROD-03 | Phase 46 | Not started |
| PROD-04 | Phase 46 | Not started |
| PROD-05 | Phase 46 | Not started |

**Coverage:** 16 requirements → 8 phases, every requirement in exactly one phase.

> **Recorded deviation from the panel.** Three deltas the two reviewers split on were decided by the
> coordinator and approved by the owner: `/flow` ships as a command (sol) rather than being cut (opus)
> — discoverability for a weak model with no GSD fallback; the fourth route is `contract-change`
> (opus) rather than `research` (sol) — it is the one route where this harness is not repo-agnostic;
> and the lifecycle is its own **phase 46** (sol) rather than a widening of phase 45 (opus) — so that
> one commit is not both repair and authoring, and deletion-first stays literal.
