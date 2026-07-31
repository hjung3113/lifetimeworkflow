# Roadmap: Contract-First 폴리글랏 에이전트 하네스 템플릿

> **Re-scope (2026-07-08, ADR-0002):** 원래 반도체 로그파서 전용 하네스로 Phase 1–4를 완주했으나, 재사용 가능한 **범용 템플릿**으로 재정의. 완료된 Phase 1–4(도메인 시드 포함)는 유지하고, **새 Phase 5 "De-specialization & Template Extraction"**을 삽입해 도메인·언어 특화 콘텐츠를 `examples/log-parser/`로 격리 + 코어 중립화한다.

## Overview

This harness is a config compiler plus runtime overlay — not an application — so it is built
bottom-up in the order the risk profile dictates. The operative principle throughout: **machines
gate, humans ratify**; agents may propose but never self-bless a golden, promote a contract, or
auto-mutate the constitution plane. Since ADR-0002 a second principle applies: the core is domain-
and language-neutral, specialization lives only under `examples/<instance>/`, and the core never
depends on an example.

**Full phase detail for shipped milestones lives in `.planning/milestones/v*-ROADMAP.md`.** This
file keeps only the milestone-level index so it stays constant-size as milestones ship.

## Milestones

- ✅ **v1.0 Harness Core** — Phases 1–8 (shipped 2026-07-12)
- ✅ **v2.0 Long-Horizon** — Phases 9–11 (shipped 2026-07-14)
- ✅ **v2.1 MEM2 — Process Memory & Provenance Reframe** — Phases 12–17 (shipped 2026-07-18)
- ✅ **v2.2 Adaptive Task Control Plane** — Phases 18–23 (shipped 2026-07-19)
- ✅ **v2.3 Contract Graph, Brownfield Adoption, Living Docs** — Phases 24–29 (shipped 2026-07-22)
- ⚠ **v2.4 Gate Right-Sizing, Carried Debt, Lane Discipline** — Phases 30–38 (**closed PARTIAL
  2026-07-26**: 34–37 shipped; 30 partial; 31/32/33 cut; 38 landed as code `bc9a6d9`, formalized by
  v2.5 phase 39)
- ✅ **v2.5 De-ceremony** — Phases 39–46 (shipped 2026-07-30)
- ✅ **v2.6 Minimal Monorepo Core** — Phases 47, 48, 49, 50a shipped 2026-07-30; **50b BLOCKED and
  carried to v2.7** (no real multi-package target repo — MONO-12)
- 🔄 **v2.7 Real-Target Adoption** — Phases 51–54; **51 shipped 2026-07-31** (OBS-03 refuted), 52–54 planned

## Phases

**Phase Numbering:** integer phases (1, 2, 3) are planned milestone work; decimal phases (26.1,
27.2) are urgent insertions, and appear between their surrounding integers in numeric order.
**Letter-suffixed phases (50a, 50b) are new in v2.6 and mean something different:** they are a
**split** of one *already scoped* phase into an independently shippable half and a half held behind a
hard external precondition. A split is decided at kickoff, not inserted mid-flight, and the halves
keep the parent's number. Spell them `50a` / `50b` — never `50.1` / `50.2`, which would read as
insertions.

<details>
<summary>✅ v1.0 Harness Core (Phases 1–8) — SHIPPED 2026-07-12</summary>

- [x] **Phase 1: Constitution + Golden Core** — walking skeleton: seed contracts, the shared normalization comparator + golden runner + contract-drift gate, one real legacy↔new equivalence loop closed end-to-end. (2026-07-08)
- [x] **Phase 2: Two-Plane Memory + Rules** — constitution-vs-derived memory split, auto-regenerated derived artifacts, nearest-wins AGENTS.md, non-ignorable session-start injection. (2026-07-08)
- [x] **Phase 3: Agents + Commands + Skills** — the full authored harness surface in canonical source, with migration commands gated behind the trusted golden net. (2026-07-08)
- [x] **Phase 4: Plugins + Hooks** — runtime enforcement of everything authored in 1–3: contract-guard, polyglot linter, format-on-write, secret protection, commit gate. (2026-07-08)
- [x] **Phase 5: De-specialization & Template Extraction** *(INSERTED — ADR-0002)* — demote the log-parser seed to `examples/log-parser/`, turn hardwired .NET+Python into a project-config slot, prove the core is example-free. (2026-07-09)
- [x] **Phase 5.5: Authored-Surface Genericization** *(INSERTED — GEN-05)* — demote domain skills, derive per-language personas from the config slot, extend the GEN-04 guard to prose. (2026-07-09)
- [x] **Phase 5.7: Lifecycle Completeness** *(INSERTED — LIFE-01..11)* — close the load-bearing gaps an adversarial audit found, so the contract→implement→test→debug loop is actually executable end to end. (2026-07-09)
- [x] **Phase 6: CI + Gates (generic)** — non-bypassable CI mirror of the in-session gates plus the human ratification path, driven by a config-derived language matrix. (2026-07-09)
- [x] **Phase 7: Single-Source Dual-Runtime Emitter** — one authored source compiles into both opencode and Claude Code artifacts, with per-runtime limit validators that fail loud. (2026-07-12)
- [x] **Phase 8: Pipeline-Topology Conductor + Per-Component Agents** — evolve the agent model from per-language to pipeline-aware; a topology slot in the neutral core and a 4-component demonstration in the example. (2026-07-11)

</details>

<details>
<summary>✅ v2.0 Long-Horizon (Phases 9–11) — SHIPPED 2026-07-14</summary>

- [x] **Phase 9: Self-Maintaining Derived Artifacts + Curator** *(v2.0 α)* — a read-mostly `curator` agent plus a CI stale-derived gate keep derived artifacts fresh; humans never hand-edit them. (2026-07-13)
- [x] **Phase 10: Context-Economy Fan-out/Synthesize Orchestration** *(v2.0 β)* — fan-out → schema-bounded citation-bearing summary → synthesize, as a reusable substrate. (2026-07-13)
- [x] **Phase 11: Multi-Repo Workspace** *(v2.0 γ)* — several repos as one workspace: manifest, repo-scoped subagents, cross-repo drift/golden gates, repo-crossing pipeline edges. (2026-07-14)

</details>

<details>
<summary>✅ v2.1 MEM2 — Process Memory & Provenance Reframe (Phases 12–17) — SHIPPED 2026-07-18</summary>

- [x] **Phase 12: Model + ADR + Doc Reframe** *(v2.1 A)* — the committed, human-authored PROCESS memory tier (`.memory/agreements/`), and the data-authority reframe ratified as ADR-0006. (2026-07-14)
- [x] **Phase 13: Injector Reframe + Channel Wiring** *(v2.1 B)* — split the SessionStart banner into a priority-0 working-agreements directive and a data-scoped provenance banner, preserving determinism and the ~4,000-char budget. (2026-07-16)
- [x] **Phase 14: Write Path + Anti-Churn Guard** *(v2.1 C)* — `/agree` adds or retires a working agreement only on explicit user feedback, backed by a provenance/anti-invent guard. (2026-07-16)
- [x] **Phase 15: Emit Round-Trip + Gates** *(v2.1 D)* — round-trip every new surface through the emitter to both runtimes with no model id; emit-drift clean, GEN-04 green. (2026-07-15)
- [x] **Phase 16: Local Memory Web UI** *(v2.1 E)* — local, no-network, no-auth view/edit/retire over a machine-built derived pointer index. (2026-07-18)
- [x] **Phase 17: Constitution-Gate Dev/Enforce Decoupling** *(infra)* — the secure-default `HARNESS_DEV_BYPASS` opt-out, distinct from `GOLDEN_APPROVE_HUMAN`, recorded as ADR-0007. Byte hygiene is never waived; CODEOWNERS stays the real gate. (2026-07-15)

</details>

<details>
<summary>✅ v2.2 Adaptive Task Control Plane (Phases 18–23) — SHIPPED 2026-07-19</summary>

- [x] **Phase 18: Task Packet Contract Ratification** *(v2.2 A)* — fix the shape and ownership of task state before any code: ratified schemas for TASK/STATE/EVIDENCE/HANDOFF, the `.workflow/tasks/<id>/` slot, phase/lane enums and the allowed-transition table. (TCP-01, TCP-02)
- [x] **Phase 19: Deterministic Risk Router** *(v2.2 B)* — a pure-function 7-axis scorer → FAST/STANDARD/STRICT/CONTROLLED lane with byte-identical output, and the `/intake` entry point that keeps FAST ceremony-free. (TCP-03..06)
- [x] **Phase 20: Atomic State Manager + Context/Transition Gate** *(v2.2 C)* — concurrency-safe transitions (temp-write+rename, revision CAS, interrupted-write recovery) and a fail-closed phase-start gate surfaced as `/phase-gate`. (TCP-07..10)
- [x] **Phase 21: Evidence Bundle Adapters** *(v2.2 D)* — collect, never reimplement, existing gate results into tamper-evident evidence with command·exit·SHA-256; strict skip≠pass. (TCP-11..13)
- [x] **Phase 22: Handoff + Fresh-Session Resume** *(v2.2 E)* — an immutable HANDOFF a fresh session reconstructs 100% from, with pointer-only SessionStart injection. (TCP-14, TCP-15)
- [x] **Phase 23: Lifecycle Evaluation + Docs + CI** *(v2.2 F)* — 20 ratified domain-neutral lifecycle fixtures plus stress/negative cases, a ceremony cap on FAST, and CI fan-in keeping every existing gate green. (TCP-16..18)

</details>

<details>
<summary>✅ v2.3 Contract Graph, Brownfield Adoption, Living Docs (Phases 24–29) — SHIPPED 2026-07-22</summary>

DAG: `24→25→28→29` and `24→26→27→29`. Design: `.planning/research/v2.3-scoping-FINAL.md`.
Full detail: `.planning/milestones/v2.3-ROADMAP.md`. Audit: `.planning/milestones/v2.3-MILESTONE-AUDIT.md`.

- [x] **Phase 24: Contract-Relationship Vocabulary + Compatibility** *(v2.3 A)* — the ratified graph record, the additive `[[contract_graph.relationships]]` slot with thin-loader passthrough, and deterministic legacy `[pipeline]`→graph lowering that unions additively and leaves the linear fixtures byte-unchanged. (TOPO-01..03) (2026-07-19)
- [x] **Phase 25: Graph Compiler, Queries, Conductor, Proof** *(v2.3 A)* — one domain-neutral compiler plus a `harness_lint` consistency gate, cycle-safe affected-set queries, and `/pipeline`·`pipeline-map`·orchestrator generalized with no new command or persona. Ratified as ADR-0009. (TOPO-04..07) (2026-07-19)
- [x] **Phase 26: Deterministic Brownfield Inventory + Mapping** *(v2.3 B)* — a read-only deterministic repo inventory, an evidence-classified mapping plan in the TOPO vocabulary, and a complete destination/disposition manifest — agent-free and fully CI-testable. (ADOPT-01..03) (2026-07-20)
- [x] **Phase 26.1: Secret-Pattern Precision** *(INSERTED)* — tighten the generic `secret_patterns[1]` value regex so it stops excluding this repo's own `ci.yml`, while proving all seven named secret shapes still match. (2026-07-20)
- [x] **Phase 26.2: Secret-Pattern Semantics** *(INSERTED)* — 26.1's charset-diversity requirement was inert under `re.IGNORECASE`, and its digit requirement opened a false-negative seam feeding the evidence-redaction path. Reconcile documented semantics with runtime behaviour and close the test blind spot that let both ship green. (2026-07-20)
- [x] **Phase 27: Task-Local Adoption Workflow + Safe Application** *(v2.3 B)* — adoption as a `.workflow/tasks/` task reusing the v2.2 CAS/evidence/HANDOFF, structural constitution-write refusal, idempotent collision-safe apply, hash-bound human ratification, and `/adopt` with three fixtures (one §4.3–4.6-dirty). (ADOPT-04..07) (2026-07-21)
- [x] **Phase 27.1: Adoption Safety** *(INSERTED)* — close the path-normalization bypass, apply-mode confinement bypass, and unconsulted approval gate found by adversarial review. (2026-07-21)
- [x] **Phase 27.2: Adoption Apply Robustness** *(INSERTED)* — clean refusal for directory-shaped destinations, `check_valid` never raising on a corrupted `approval.json`, and a concurrency test that actually fails when `fcntl.flock()` is removed. (2026-07-21)
- [x] **Phase 28: Human-Docs Registry, Guard, Derived Queue** *(v2.3 C)* — `docs/doc-dependencies.toml` plus the review ledger, deterministic fingerprints, the FRESH/BROKEN/STALE_REQUIRED/STALE_ADVISORY/UNCOVERED gate, ADR-safe dispositions, and a derived staleness queue with a conditional SessionStart pointer. (DOCSUP-01..05) (2026-07-21)
- [x] **Phase 29: Docs Drive Loop + Adoption Integration + Closeout** *(v2.3 C)* — the `/docs-update` drive loop (accepted ADRs, reference and derived structurally excluded), reviewed seeding of the high-risk corpus and adoption-runbook bindings, and the milestone closeout against the full gate fan-in. Ratified as ADR-0010. (DOCSUP-06, DOCSUP-07) (2026-07-22)

</details>

### ⚠ v2.4 Gate Right-Sizing, Carried Debt, Lane Discipline (Phases 30–38) — CLOSED PARTIAL 2026-07-26

> **CLOSED PARTIAL 2026-07-26.** Shipped: **34** (ruff as a required CI gate), **35** (carried-debt
> dispositions), **36** (discipline skills + adversarial panel), **37** (capability routing +
> `registry.lock`) — 1683 passed / 8 snapshots. **30** landed only its contract pair (`27ee704`,
> human-written); plans 30-02/03/04 were never authored, and **v2.5 cuts them** —
> `deny-domains.json`'s own `_note` says no hook reads it and a drift test over it would prove a file
> equals itself. **31/32** were cut by ADR-0011. **33** never started and is cut: `secret_scan` is
> deleted outright in v2.5-44 (so SEAL-04 is moot) and SEAL-05's portable ratification record is the
> mechanism v2.5 replaces with a recorded decision. **38** landed as code (`bc9a6d9`) but was never
> formalized, and its ADR-0011 is still `proposed` with empty `Date`/`Deciders` — **v2.5 phase 39
> discharges that bookkeeping** and closes RAT-4 / RAT-5 / the per-tool deny spelling as
> obsolete-by-deletion. Two drafted docs-review ledger rows stay unlanded; v2.5 phase 41 deletes the
> plane that wants them. Phase directories are deliberately **not** cleared — they hold those drafts
> and records.

> **RE-PIVOT (2026-07-26, ADR-0011):** the human found the in-session gate wall over-regulated for a
> repo whose goal is consistency + long-horizon maintainability, and it deadlocked the session twice.
> Theme A flips from *harden the in-session denies* to **right-size them: dev-light, CI-strong**.
> Enforcement's home is CI + CODEOWNERS; the guards degrade instead of deadlocking and a dev session
> opts out via `HARNESS_DEV_LIGHT`. SEAL-02/03 (spelling-independent bash denies = MORE blocking) are
> CUT. Phase 38 delivers the right-sizing.

Design: `.planning/research/v2.4-scoping-FINAL.md` (Claude draft + one codex-sol review pass,
human-approved). Requirements: `.planning/milestones/v2.4-REQUIREMENTS.md`.

**Goal:** close the gap between what this harness *declares* and what it *enforces*, discharge the
debt carried across three milestones, and finish the task-lifecycle discipline left unbuilt by v2.2.
Thesis, quoting ADR-0010 back at the harness: *a layer that is only a data row is a claimed control
that does not exist — worse than a missing layer, because it reads as covered.*

- [ ] **Phase 30: Deny-Domain Registry** *(v2.4 A)* — declare every path-deny domain
  (`contract_guard` constitution, `secret_scan` secret paths, `ledger_guard` review ledger) with its
  owner, bypass semantics, covered tool surfaces and runtime adapters; a `harness_lint` drift test
  fails when a hook's live constant disagrees with its declaration. The domains stay **distinct** —
  this is an inventory, not a merge. (SEAL-01)
- [~] **Phase 31: Threat Model + Posture ADR** *(v2.4 A — CUT by ADR-0011: don't add more in-session denies)* — a ratified ADR choosing the enforcement
  posture for the uncovered bash surface (filesystem-level / constrained allowlist / protected
  wrappers / documented residual) and stating what stays uncovered. Ratified BEFORE enforcement is
  written. (SEAL-02)
- [~] **Phase 32: Implement the Posture** *(v2.4 A — CUT by ADR-0011)* — the chosen posture in both runtimes with
  per-class deletion proofs and live negative controls, plus a superseding ADR recording the newly
  covered surface. Acceptance is written against the declared posture, never "all spellings". (SEAL-03)
- [ ] **Phase 33: Contract-Driven Secret Scan + Ratification Record** *(v2.4 A)* — `secret_scan`
  reads its patterns from the gate registry instead of hardcoding them; RAT-4 reaches a recorded
  disposition; the harness defines a portable ratification record that does not depend on a git host
  assigning a reviewer. (SEAL-04, SEAL-05)
- [x] **Phase 34: Ruff as a Required CI Gate** *(v2.4 B)* — vendored tree into `extend-exclude`, a
  ratcheting baseline for the genuine remainder, and the job made blocking. Owns its own phase
  because turning 617 findings into a gate is the risky one. (DEBT-01)
- [x] **Phase 35: Carried-Debt Dispositions** *(v2.4 B)* — phase-27 verification disposition (honest
  stamp or written off, never manufactured); compile-the-graph-once (28 IN-03) with a recorded
  decision on `impact.py`'s signature; `DEF-05-02-1` verified and closed. (DEBT-02, DEBT-03, DEBT-04)
- [x] **Phase 36: Discipline Skills + Adversarial Review Panel** *(v2.4 C)* — clarify/TDD/diagnose/
  domain-modeling skills wired into the task lifecycle so a lane's discipline is executable, and a
  STRICT+ adversarial multi-expert panel as a declared lane requirement, reusing the Phase-10 fan-out
  substrate. (LANE-01, LANE-02)
- [x] **Phase 37: Capability Routing + Registry Lock + Closeout** *(v2.4 C)* — specialist allowlist
  and capability-neutral routing, skill `registry.lock` + adapter CI, and the milestone closeout
  against the full gate fan-in. (LANE-03, LANE-04)

**DAG:** `30 → 31 → 32` is a hard chain — the registry must exist before the posture can be reasoned
about, and the posture must be ratified before enforcement is written. `33` depends on 30 only.
`34`, `35` and `36 → 37` are otherwise parallel.

**Recorded deviation:** the review advised five phases (cut Themes C and D); the human kept C and cut
D. The named failure mode — phase 32 expanding without bound — is mitigated by phase 31's posture ADR
being a hard precondition. If 31 cannot pick a posture, stop rather than proceed.

<details>
<summary>✅ v2.5 De-ceremony (Phases 39–46) — SHIPPED 2026-07-30</summary>

DAG: strictly serial `39 → 40 → 41 → 42 → 43 → 44 → 45 → 46`; deletion-first is literal.
Design: `.planning/research/v2.5-scoping-FINAL.md`. Full detail: `.planning/milestones/v2.5-ROADMAP.md`.
Requirements: `.planning/milestones/v2.5-REQUIREMENTS.md` (CER-01..11, PROD-01..05, 16/16).
Authority: ADR-0012 (CI + the merge), closed out by ADR-0013 (task-control-plane retirement).
Net: 33/33 plans, 171 commits, **−27,398 LOC** outside `.planning/`; human-authored gates 5 kinds → 0.

- [x] **Phase 39: Decision Boundary** *(v2.5 A)* — one human-ratified ADR-0012: CI + the merge are the authority; the DEV/PRODUCT boundary ratified with its operative rule; ADR-0001's constitution-member list superseded and ADR-0010 retired; ADR-0011 accepted; RAT-4/RAT-5/per-tool deny spelling closed as obsolete-by-deletion; the bash surface declared a permanent residual by design. (CER-01..03) (2026-07-26)
- [x] **Phase 40: Self-Gate Teardown** *(v2.5 A)* — delete `tools/skill_registry` (611 LOC), `harness/skills/registry.lock`, its two gate tests and its CI job. Found unrecorded during the close and closed retroactively on direct evidence. (CER-04) (2026-07-29)
- [x] **Phase 41: Docs-Review Plane Removal** *(v2.5 A)* — unbind the 8 `[[binding]]` rows, then delete the ledger, `ledger_guard`, `/docs-update` and the whole docs-review plane, with **no replacement of any kind**. (CER-05) (2026-07-26)
- [x] **Phase 42: Adoption Decoupling + Install-Set Repair** *(v2.5 B)* — adoption becomes a standalone `draft → apply → PR review` capability with no task-control coupling; the product receives the code its own artifacts invoke. (CER-06, PROD-01) (2026-07-27)
- [x] **Phase 43: Lifecycle Plane Removal** *(v2.5 B)* — delete 8 `tools/` packages, the 7 task-control contracts, 4 commands, `resume_gate`, the 5 discipline skills, `.workflow/tasks/` and the `lifecycle-eval` CI job. **−12,383 LOC**; review then caught the `RETIRED_SIGNATURES` defect that would have bricked every stale checkout. (CER-07) (2026-07-28)
- [x] **Phase 44: Non-Goal Surface Removal** *(v2.5 B)* — delete `secret_scan` (no replacement job), `tools/memory_ui`, `strangler_guard`, `/pipeline`, skill `gate-model` and more; **relocate the golden stack to `examples/log-parser/`**. **−6,067 LOC**; two replays, the first finding 6 of 10 commits ending red. (CER-08, CER-09) (2026-07-29)
- [x] **Phase 45: Projection Repair** *(v2.5 C)* — re-emit both trees, rebaseline the hash manifest, regenerate the derived plane, repair `gate.needs`, and scrub prose naming deleted surfaces. Constitution plane 4 → 3 members; the declaration had fourteen copies. (CER-10, CER-11) (2026-07-29)
- [x] **Phase 46: Product Flow** *(v2.5 C)* — rewrite `orchestrator.md` with 4 routes (`small-change · bugfix · feature · contract-change`), the six-field completion contract, and one operative sentence per deleted discipline skill; add `/flow`; record route/step/next in the shipped state plane. **+1,341 LOC**, the milestone's only net addition. (PROD-02..05) (2026-07-29)

</details>

<details>
<summary>✅ v2.6 Minimal Monorepo Core (Phases 47–50a) — SHIPPED 2026-07-30 · 50b BLOCKED</summary>

Full detail: `.planning/milestones/v2.6-ROADMAP.md`. Requirements:
`.planning/milestones/v2.6-REQUIREMENTS.md`. Audit: `.planning/v2.6-MILESTONE-AUDIT.md`.

- [x] **Phase 47: Package Facts** — a committed derived package + dependency graph parsed from the
  manifests themselves; `[[components]]` demoted to an override slot; contract→owning-package
  attribution. Report-only. (MONO-01..04) (2026-07-30)
- [x] **Phase 48: Convention Profiles** — nearest-wins per-package conventions whose commands derive
  from `[[languages]]`, populated by `/component` step 2. No new command. (MONO-05..07) (2026-07-30)
- [x] **Phase 49: Contract Impact** — `/impact <contract>` over the existing
  `direct`/`reverse`/`transitive` plus the package facts; fills the `contract-change` route's evidence
  slot. The milestone's one sanctioned +1 command. (MONO-08, MONO-09) (2026-07-30)
- [x] **Phase 50a: Harness Authoring** — the `harness-author` skill with `path:line`-cited defaults,
  absorbing `skill-creator` at skills 8 → 8. (MONO-10, MONO-11) (2026-07-30)
- [⛔] **Phase 50b: Managed Adopt / Upgrade** — **BLOCKED and carried**: no real multi-package target
  repo exists, and `/adopt` writes into its target. MONO-12 carried; unblock by naming a real target.

Net surface: **+1 command, ±0 skills, +0 gates / CI jobs / contracts / packages / dependencies**,
nothing injected into SessionStart. 981 tests passing at close.

</details>

### 📋 v2.7 Real-Target Adoption (Phases 51–54) — PLANNED

**Milestone Goal:** Adopt the harness into an isolated worktree of the real FeedbackOps monorepo,
observe the unrepaired result before designing changes, and repair only failures that the run proves
matter to the harness's four purposes. The original `develop` checkout stays byte-unchanged.

Binding boundary: Phase 51 must finish its evidence record before any repair phase begins. A
confirmed or refuted OBS-03 hypothesis is equally successful. Commands remain 19, skills 8,
contracts 6, and CI jobs and gates do not increase. Runtime artifacts are authored only in
`harness/` and changed through re-emission; new repository artifacts contain no model identifiers.

- [x] **Phase 51: Real-Target Observation Baseline** - Run the current harness against the isolated
  target and capture reproducible evidence before designing repairs.
- [ ] **Phase 52: Evidence-Bounded Real-Target Adoption** - Make the required adoption capabilities
  work using only failures established by Phase 51.
- [ ] **Phase 53: Managed Adopt Updates** - Prove install-to-update behavior, unchanged no-op, and
  divergence-safe conflict handling on the real target.
- [ ] **Phase 54: Surface Budget Closeout** - Remove the named duplicate adapter and close the
  milestone without growing commands, skills, contracts, CI jobs, or gates.

### 📋 Deferred beyond v2.7

- **EVOL-02** contract versioning / compatibility engine — the only survivor; still a standalone
  engine needing its own ADR.
- **D-24** CODEOWNERS advisory on this repo — re-openable as a machine-side check on golden baseline
  diffs, unblocked by ADR-0012 but out of v2.6: adding a gate contradicts the no-growth constraint
  unless something retires with it. Stays a documented residual.
- **Obsoleted by v2.5, recorded so they are not re-adopted:** **EVOL-01** (impact-driven task-evidence
  policy) and **TCP-F05** (signed external attestation + STRICT rollback) die with the task-control
  plane deleted in phase 43; **EVOL-03** (`examples/**` instance-local docs-registry overlay) dies with
  the docs-review plane deleted in phase 41; **SEAL-04** is moot once `secret_scan` is deleted
  (phase 44) and **SEAL-05** (portable ratification record) is withdrawn by phase 39's recorded
  decision.

## Phase Details

### Phase 51: Real-Target Observation Baseline
**Goal**: The current harness's behavior on the isolated FeedbackOps worktree is known from reproducible evidence before any repair is designed
**Depends on**: Phase 50a and an isolated FeedbackOps worktree
**Requirements**: OBS-01, OBS-03
**Success Criteria** (what must be TRUE):
  1. A baseline `/adopt` discover → draft → apply attempt runs against the isolated worktree only, and before/after evidence shows the original `develop` checkout is byte-unchanged. The attempt is permitted to fail or produce wrong output — its purpose is evidence, not success — and whatever state it leaves behind is discarded, so Phase 52 starts from a freshly created worktree.
  2. Every adoption defect observed in the baseline has a record containing its symptom, reproducible path, and implicated code location.
  3. The pnpm `workspace:*` hypothesis has a reproducible verdict: confirmed by incorrect dependency output or refuted by evidence that the current output already records the workspace edge.
  4. No repair design or implementation precedes the completed baseline evidence record.
**Plans**: TBD

### Phase 52: Evidence-Bounded Real-Target Adoption
**Goal**: FeedbackOps receives the required adoption capabilities, with changes limited to purpose-relevant failures proven by Phase 51
**Depends on**: Phase 51
**Requirements**: RTA-01, RTA-02, RTA-03, RTA-04, OBS-02
**Success Criteria** (what must be TRUE):
  1. A developer can complete `/adopt` discover → draft → apply against the isolated FeedbackOps worktree while the original `develop` checkout remains byte-unchanged.
  2. The adoption inventory contains all five real workspace members: root, `packages/ui`, `packages/shared`, `apps/frontend`, and `apps/backend`.
  3. Generated package facts contain the real `packages/shared` dependency edges to both `apps/frontend` and `apps/backend`.
  4. Each adopted package resolves a nearest-wins convention profile containing its lint and test commands.
  5. Every change made in this phase traces to a Phase 51 observation within purpose ①②③④ and has a regression test; observations requiring no change remain evidence-backed confirmations.
**Plans**: 6 plans
Plans:
- [ ] 52-01-PLAN.md — Contract-first: add the `non-workspace-member` reason to `inventory.schema.json`, rebaseline the schema hash, regenerate the derived plane (D-20)
- [ ] 52-02-PLAN.md — OBS-D-01: pnpm workspace member scoping in `detect.py`/`scan.py` + synthetic fixture + regression tests
- [ ] 52-03-PLAN.md — OBS-D-03: permanent `lint` key on `conventions_for()` + target-derived JS `[[languages]]` row through draft/apply
- [ ] 52-04-PLAN.md — OBS-D-04: declare the marker-merge lock sidecars, report a stale one on stderr; OBS-D-02 `workspace:*` lock-in test
- [ ] 52-05-PLAN.md — Fresh detached FeedbackOps worktree: before-proof, discover → draft → apply captures, apply-write comparison
- [ ] 52-06-PLAN.md — Downstream observations, after-proof with drift attribution, auto-disposal, and the SC-5 trace ledger

### Phase 53: Managed Adopt Updates
**Goal**: Re-running `/adopt` safely manages installed harness files instead of reinstalling them
**Depends on**: Phase 52
**Requirements**: MONO-12
**Success Criteria** (what must be TRUE):
  1. The adoption manifest records every file managed by `/adopt`.
  2. A re-run updates changed managed content, while a re-run with no source or target changes is an observable no-op.
  3. A target-side divergence in a managed file produces a conflict report and leaves that file byte-unchanged.
**Plans**: TBD

### Phase 54: Surface Budget Closeout
**Goal**: The milestone closes with the named duplication removed and no growth in governed harness surfaces
**Depends on**: Phase 53
**Requirements**: DEBT-01, NG-01
**Success Criteria** (what must be TRUE):
  1. `conventions_for()` and `report()` use one shared `"dir"`-filter helper, with no duplicated adapter implementation and unchanged caller-visible results.
  2. Closeout counts are no greater than the milestone baseline: 19 commands, 8 skills, 6 contracts, and unchanged-or-lower CI job and gate counts.
  3. Any runtime-surface change originates under `harness/`, and a re-emit leaves `.opencode/` and `.claude/` synchronized with that source.
  4. Repository artifacts added by v2.7 contain no model identifiers.
**Plans**: TBD

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1–8 | v1.0 | 41/41 | Complete | 2026-07-12 |
| 9–11 | v2.0 | 11/11 | Complete | 2026-07-14 |
| 12–17 | v2.1 | see archive | Complete | 2026-07-18 |
| 18–23 | v2.2 | see archive | Complete | 2026-07-19 |
| 24. Contract-Relationship Vocabulary | v2.3 | 2/2 | Complete | 2026-07-19 |
| 25. Graph Compiler, Queries, Conductor | v2.3 | 5/5 | Complete | 2026-07-19 |
| 26. Brownfield Inventory + Mapping | v2.3 | 9/9 | Complete | 2026-07-20 |
| 26.1 Secret-Pattern Precision (INSERTED) | v2.3 | 1/1 | Complete | 2026-07-20 |
| 26.2 Secret-Pattern Semantics (INSERTED) | v2.3 | 1/1 | Complete | 2026-07-20 |
| 27. Adoption Workflow + Safe Application | v2.3 | 6/6 | Complete | 2026-07-21 |
| 27.1 Adoption Safety (INSERTED) | v2.3 | 3/3 | Complete | 2026-07-21 |
| 27.2 Adoption Apply Robustness (INSERTED) | v2.3 | 2/2 | Complete | 2026-07-21 |
| 28. Human-Docs Registry, Guard, Queue | v2.3 | 9/9 | Complete | 2026-07-21 |
| 29. Docs Drive Loop + Closeout | v2.3 | 5/5 | Complete | 2026-07-22 |
| 30. Deny-Domain Registry | v2.4 | 1/4 | Contract landed (27ee704); loader CUT — kept as inventory | 2026-07-26 |
| 31. Threat Model + Posture ADR | v2.4 | — | CUT (ADR-0011) | - |
| 32. Implement the Posture | v2.4 | — | CUT (ADR-0011) | - |
| 33. Secret Scan + Ratification Record | v2.4 | — | CUT (v2.5 deletes `secret_scan`; SEAL-05 withdrawn) | - |
| 34. Ruff as a Required CI Gate | v2.4 | 3/3 | Complete | 2026-07-22 |
| 35. Carried-Debt Dispositions | v2.4 | 3/3 | Complete | 2026-07-22 |
| 36. Discipline Skills + Review Panel | v2.4 | 4/4 | Complete | 2026-07-22 |
| 37. Capability Routing + Closeout | v2.4 | 2/2 | Complete | 2026-07-22 |
| 38. Gate Right-Sizing (dev-light/CI-strong) | v2.4 | 1/1 | Complete | 2026-07-26 |
| 39. Decision Boundary | v2.5 | 2/2 | Complete    | 2026-07-26 |
| 40. Self-Gate Teardown | v2.5 | 1/1 | Complete   | 2026-07-29 |
| 41. Docs-Review Plane Removal | v2.5 | 5/5 | Complete   | 2026-07-26 |
| 42. Adoption Decoupling + Install-Set Repair | v2.5 | 5/5 | Complete   | 2026-07-27 |
| 43. Lifecycle Plane Removal | v2.5 | 5/5 | Complete   | 2026-07-28 |
| 44. Non-Goal Surface Removal | v2.5 | 6/6 | Complete   | 2026-07-29 |
| 45. Projection Repair | v2.5 | 6/6 | Complete   | 2026-07-29 |
| 46. Product Flow | v2.5 | 3/3 | Complete   | 2026-07-29 |
| 47–50a | v2.6 | 11/11 | Complete (see archive) | 2026-07-30 |
| 50b | v2.6 | — | **BLOCKED** — no real multi-package target repo; MONO-12 carried | - |
| 51. Real-Target Observation Baseline | v2.7 | 3/3 | Complete (verified 4/4; OBS-03 **refuted**) | 2026-07-31 |
| 52. Evidence-Bounded Real-Target Adoption | v2.7 | 0/TBD | Not started | - |
| 53. Managed Adopt Updates | v2.7 | 0/TBD | Not started | - |
| 54. Surface Budget Closeout | v2.7 | 0/TBD | Not started | - |

Per-phase plan counts for v1.0–v2.2 are preserved in the milestone archives under
`.planning/milestones/`; they are not restated here so this table stays a fixed size.
