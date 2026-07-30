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
- 🚧 **v2.6 Minimal Monorepo Core** — Phases 47, 48, 49, 50a, 50b (**in progress**, started
  2026-07-30)

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

### 🚧 v2.6 Minimal Monorepo Core (Phases 47, 48, 49, 50a, 50b) — IN PROGRESS

Requirements: `.planning/REQUIREMENTS.md` (MONO-01..12, 12/12 mapped). **No research round** — the
design was settled by the v2.5 scoping panel and every phase cites this repo's own code rather than an
external ecosystem, so `.planning/research/` holds nothing for v2.6 by decision.

**Goal:** close gap ③ of the owner's four-part purpose — *an LLM working in this repo understands
cross-project relationships better than it would in a generic repo*. Smallest goal-complete subset =
all of v2.5 **+ 47 + 49**; the owner chose all five. ① is already covered by the lint adapters +
nearest-wins `AGENTS.md` + `/component`; ② by `contracts/` + `contract_hash`/`contract_drift` +
`contract_graph` + CI; ④ by append-only ADR + the derived plane + ADR-0011's CI-strong posture. The
genuine gap is ③.

> **Binding constraint (carried from v2.5, governs every criterion below):** never expand scope beyond
> the purpose by adding verification gates, security layers, or ceremony. Default answer to "should we
> also gate X?" is **NO**; the surface may not grow without retiring at least as much. Concretely for
> this milestone: **47 and 49 are gate-free by design** (no new CI job, no new gate), **48 adds no new
> command**, **50a is net ±0 on skills** (8 → 8, `harness-author` absorbs `skill-creator`), and
> **nothing is injected into SessionStart**.

- [x] **Phase 47: Package Facts** *(v2.6)* — extend `tools/adoption_scan/detect.py`'s manifest (completed 2026-07-29)
  detection (`:41-47,100-121`, which today records manifest *existence* and parses no dependencies)
  into a committed **derived** package + dependency graph that feeds `contract_graph`;
  `[[components]]` in `harness/project.toml` is demoted to an **override slot** layered over the
  derived facts. **Report-only: no gate, no CI job.** (MONO-01, MONO-02, MONO-03, MONO-04)
  **Success criteria:**
  1. One committed derived artifact lists every package in this checkout with its manifest path,
     language and package id; deleting it and regenerating from a clean tree yields a byte-identical
     file.
  2. Every dependency edge in that artifact is parsed from the manifests themselves (`pyproject.toml`,
     `package.json`, `go.mod`, `Cargo.toml`, `*.csproj`) — no hand-maintained dependency list exists
     anywhere in the tree, and removing a dependency from a fixture manifest removes exactly that edge
     on regeneration.
  3. A `[[components]]` entry overrides the derived record for the same package, and both live configs
     (core `harness/project.toml` + `examples/log-parser/`) still load with **zero edits**.
  4. Given a contract path, `contract_graph` reports the package that owns it, using the package facts.
  5. The phase adds no gate and no CI job: `ci.yml`'s job set and `gate.needs` are unchanged from the
     phase's base commit, and the derived artifact's freshness rides the **existing** `stale-derived`
     job rather than a new one.
- [x] **Phase 48: Convention Profiles** *(v2.6)* — nearest-wins per-package convention data whose (completed 2026-07-30)
  lint/test commands are derived from the existing `[[languages]]` slot, populated by `/component`
  step 2 inside its existing mandated order. **No new command.** (MONO-05, MONO-06, MONO-07)
  **Success criteria:**
  1. Asking "which conventions apply here?" from a path inside a package returns that package's
     profile, and from a path with no enclosing package returns the repo-wide default — demonstrated
     on a nested case where the inner answer differs from the enclosing one.
  2. A profile never restates a lint or test command literal: the commands it reports come from
     `[[languages]]` in `harness/project.toml`, so editing the language config changes the reported
     commands with no profile edited.
  3. Running `/component` produces a convention profile for the new package as part of step 2, in its
     existing structure → AGENTS.md → tests order.
  4. The command count is unchanged (`/component` extended, nothing added), and no gate or CI job is
     added.
- [ ] **Phase 49: Contract Impact** *(v2.6)* — one `/impact <contract>` command over
  `contract_graph.query`'s existing `direct`/`reverse`/`transitive` (`query.py:29,39,55`) plus the
  Phase-47 package facts; fills phase 46's evidence slot in the `contract-change` route. **On demand
  only — no SessionStart injection, no gate, no CI job.** (MONO-08, MONO-09)
  **Success criteria:**
  1. `/impact <contract>` reports the affected **contracts** and the affected **packages**, covering
     direct, reverse and transitive relations.
  2. No second traversal engine exists: the affected sets come from `contract_graph.query`'s existing
     three functions and the Phase-47 package facts.
  3. Nothing is injected: the SessionStart injector's assembled output is byte-identical with and
     without this phase, and no CI job or hook references `/impact`.
  4. The `contract-change` route in `harness/agents/orchestrator.md` names `/impact` as the evidence
     step it previously left unfilled, and the emit round-trip to both runtimes is byte-clean.
- [ ] **Phase 50a: Harness Authoring** *(v2.6 — SPLIT half (a), ships independently)* — one
  `harness-author` skill: Q&A with defaults cited as `path:line` from this checkout, output
  runtime-neutral under `harness/` only (the emitter projects it), **absorbing `skill-creator`** for
  net skills ±0. Presupposes PROD-01 (shipped in v2.5 phase 42). (MONO-10, MONO-11)
  **Success criteria:**
  1. `harness-author` exists as a skill and its offered defaults are cited as `path:line` locations
     that resolve in this checkout.
  2. Its output lands under `harness/` only; `.opencode/` and `.claude/` change solely through
     re-emit, and the emit round-trip is byte-clean.
  3. `skill-creator` no longer exists and everything it did is reachable through `harness-author`; the
     skill count is **8 before and 8 after**.
  4. Zero new packages under `tools/`, zero new commands, zero new contracts.
- [ ] **Phase 50b: Managed Adopt / Upgrade** *(v2.6 — SPLIT half (b), blocked on an external
  precondition)* — simplified `/adopt` as a managed install/update over one manifest that **reports
  conflicts** rather than silently overwriting a target repo's files. (MONO-12)
  **Hard precondition:** a **real multi-package target repo**. None exists in this checkout. If none
  exists when the phase is reached, 50b is recorded **BLOCKED and carried** — it does not stall the
  milestone, which closes on 47 · 48 · 49 · 50a.
  **Success criteria:**
  1. One manifest records what the harness installed into the target, so a later run can tell managed
     files from target-owned files.
  2. Re-running `/adopt` against an already-adopted target **updates** managed files from that
     manifest instead of re-installing, and is a no-op when nothing changed.
  3. A managed file the target has since diverged from its recorded baseline is **reported as a
     conflict and left untouched** — never silently overwritten.
  4. The phase's precondition is discharged on the record: either a named real multi-package target
     repo is cited, or the phase is marked BLOCKED and carried with that reason.

**DAG:** `47 → {48, 49}`. `50a` needs `48`. `50b` needs `48` **and** a real multi-package target repo
— a hard *external* precondition, not a code dependency, which is why it cannot be scheduled away.

**Recorded deviation from the v2.5 panel's sketch:** the panel scoped four phases (47–50). At v2.6
kickoff the owner **split phase 50 into `50a` and `50b`**, because 50b explicitly does not start
without a real multi-package target and no such target exists in this checkout. Splitting lets 50a
ship and 50b block cleanly, rather than one phase stalling the milestone. This is the repo's first
letter-suffixed split (see *Phase Numbering* above); decimal numbering was **not** used because
`50.1`/`50.2` are reserved for urgent insertions and would misdescribe this.

#### Phase 47: Package Facts

**Goal:** An agent asking *"what packages exist here, what do they depend on, and which package owns
this contract?"* gets one **derived, committed, machine-built** answer instead of reading 24 manifests
or trusting a hand-written `[[components]]` table. This is the base of gap ③ — 48 and 49 both read it.

**Requirements:** MONO-01, MONO-02, MONO-03, MONO-04

**Scope** (measured 2026-07-30 against this checkout):

- **Extend `tools/adoption_scan/detect.py`, do not fork it.** `_MANIFEST_KIND_BY_NAME`
  (`detect.py:41-47`) recognizes `pyproject.toml` · `package.json` · `go.mod` · `Cargo.toml`, plus the
  `*.csproj` suffix special-case at `detect.py:107-108`. `detect_manifests` (`detect.py:100-121`)
  records `path`/`kind`/`classification`/`evidence` — **manifest existence only, zero dependency
  parsing**. MONO-02's edges come from adding dependency extraction per manifest kind here, on the
  same D-02 `observed` evidence ladder the module already enforces.
- **One committed derived artifact** listing every package with manifest path, language and package
  id. `git ls-files` finds **24** recognized manifests today (1 `package.json`, 3 `.csproj`, 20
  `pyproject.toml`). Derived-plane rules apply unchanged: generator under `tools/`, never hand-edited,
  byte-identical on regeneration from a clean tree.
- **`[[components]]` becomes an override slot, not the source.** Two live configs must keep loading
  with **zero edits**: the core generic default (`harness/project.toml` — `source`/`sink`, both
  `python`) and the instance overlay (`examples/log-parser/project.toml:34-63` — `parser`/`converter`
  (dotnet) + `scheduler`/`collector` (python)). A declared component overrides the derived record for
  the same package; it does not delete or contradict it silently.
- **Contract → owning package attribution** lands in `tools/contract_graph`, reusing the existing
  compiler/query surface (`compile.py`, `query.py`) — no second graph engine.
- **No gate, no CI job.** `ci.yml`'s job set (`setup · lang-tests · contract-check · drift · golden ·
  core-suite · lint · emit-drift · stale-derived · workspace`) and `gate.needs` (`ci.yml:329`) are
  unchanged from this phase's base commit. Freshness rides the **existing** `stale-derived` job
  (`ci.yml:271`), which today regenerates `docs/reference` + `.memory/derived/contracts-index.md` —
  the new artifact joins that regen command and that diff check, adding no job.

**Non-goals:** a dependency *policy* (allowed/forbidden edges), any hand-maintained package list, any
SessionStart injection of the package graph, version/compatibility resolution (that is carried
EVOL-02).

**Success Criteria** (what must be TRUE):

1. One committed derived artifact lists every package in this checkout with its manifest path,
   language and package id; deleting it and regenerating from a clean tree yields a byte-identical
   file.
2. Every dependency edge in that artifact is parsed from the manifests themselves (`pyproject.toml`,
   `package.json`, `go.mod`, `Cargo.toml`, `*.csproj`) — no hand-maintained dependency list exists
   anywhere in the tree, and removing a dependency from a fixture manifest removes exactly that edge
   on regeneration.
3. A `[[components]]` entry overrides the derived record for the same package, and both live configs
   (core `harness/project.toml` + `examples/log-parser/project.toml`) still load with **zero edits**.
4. Given a contract path, `contract_graph` reports the package that owns it, using the package facts.
5. The phase adds no gate and no CI job: `ci.yml`'s job set and `gate.needs` are unchanged from the
   phase's base commit, and the derived artifact's freshness rides the **existing** `stale-derived`
   job rather than a new one.

#### Phase 48: Convention Profiles

**Goal:** An agent working anywhere in the tree can ask *"which conventions apply here?"* and get the
**nearest-wins** answer — the enclosing package's profile, not the repo-wide default — without any
profile restating a lint or test command the language config already owns. Phase 47 answered *what
packages exist*; this answers *what rules apply where*.

**Requirements:** MONO-05, MONO-06, MONO-07

**Scope** (measured 2026-07-30 against this checkout):

- **Nearest-wins resolution over the Phase-47 package facts.** `.memory/derived/package-facts.md` +
  `tools/memory_regen/package_facts.py` (`build_facts`, `discover_manifests`) already give every
  package's directory; `tools/contract_graph/ownership.py`'s `owning_package()` already implements
  segment-based nearest-enclosing-package lookup. This phase reuses that resolution rather than
  writing a second path-matcher.
- **Commands are DERIVED, never restated.** `harness/project.toml`'s `[[languages]]` rows own
  `test` and `format` (plus `bash_scope`, `test_paths`); `tools/harness_config/loader.py` already
  exposes them via `languages()`. A profile names its language and inherits the commands — editing
  `[[languages]]` must change what every profile reports, with no profile edited. That is the
  falsifiable form of MONO-06.
- **Prose rules stay where they already live.** 7 `AGENTS.md` files are tracked (3 of them adoption
  test fixtures); the nearest-wins AGENTS.md convention shipped in Phase 2 and is unchanged. The
  profile is the *machine-readable* answer that sits alongside it, not a replacement — and it must
  not fork the two into disagreeing sources.
- **`/component` is EXTENDED, not joined.** `harness/commands/component.md` (35 lines) declares a
  mandated order — structure → self-sufficient `AGENTS.md` → tests. The profile is populated inside
  **step 2**, keeping that order intact. Live command count is **18** and must be 18 after.
- **No gate, no CI job.** As with Phase 47, `ci.yml`'s job set and `gate.needs` stay byte-unchanged,
  and any derived output rides the existing `stale-derived` job.

**Non-goals:** a convention *enforcement* gate (this milestone forbids adding gates); per-package
prose generation that would compete with `AGENTS.md`; any new command; SessionStart injection of
profiles.

**Success Criteria** (what must be TRUE):

1. Asking "which conventions apply here?" from a path inside a package returns that package's
   profile, and from a path with no enclosing package returns the repo-wide default — demonstrated
   on a nested case where the inner answer differs from the enclosing one.
2. A profile never restates a lint or test command literal: the commands it reports come from
   `[[languages]]` in `harness/project.toml`, so editing the language config changes the reported
   commands with no profile edited.
3. Running `/component` produces a convention profile for the new package as part of step 2, in its
   existing structure → AGENTS.md → tests order.
4. The command count is unchanged (`/component` extended, nothing added), and no gate or CI job is
   added.

#### Phase 49: Contract Impact

**Goal:** Turn the `contract-change` route's *Repository evidence* step from a raw inline one-liner
into one named command. `/impact <contract>` answers "what does changing this contract reach?" over
**both** planes now available: the compiled contract graph (v2.3) and the Phase-47 package facts —
so the answer names affected **packages**, not only affected contract nodes. This is the payoff of
47 and 49 being the milestone's smallest goal-complete subset.

**Requirements:** MONO-08, MONO-09

**Scope** (measured 2026-07-30 against this checkout):

- **No second traversal engine.** The affected sets come from `tools/contract_graph/query.py`'s
  existing `direct` (`:29`), `reverse` (`:39`) and `transitive` (`:55`) over
  `compile_graph()`'s adjacency, plus `tools/harness_config.effective_relationships()` /
  `components()`. Package attribution reuses Phase 47's `owning_package()` and the package facts.
  Writing a fresh walk would create the second authority plane REQUIREMENTS.md explicitly forbids.
- **Replaces prose with a command, not with a new engine.** `harness/agents/orchestrator.md`'s
  `contract-change` route currently inlines a `uv run python -c "..."` one-liner in its *Repository
  evidence* block and explains `direct`/`reverse`/`transitive` in prose. That block becomes
  `/impact`, and the route names it as the evidence step it previously left unfilled (criterion 4).
- **On demand only.** No SessionStart injection, no gate, no CI job, no hook may reference `/impact`.
  The injector's assembled output must be byte-identical with and without this phase.
- **The one sanctioned surface addition in v2.6.** The milestone's no-growth rule is "no growth
  without retiring at least as much"; the roadmap scopes `/impact` as exactly one new command, and
  50a pays for itself separately (skills 8 → 8). Phase 48 pinned the command surface with
  `test_command_count_is_stable` (`== 18`) and `test_command_names_are_stable` (the 18-name set) —
  **both must be updated to 19 and to include `impact` in the same change**, which is precisely the
  guard working as intended rather than an obstacle.
- **Emit round-trip.** A new `harness/commands/impact.md` plus the edited `orchestrator.md` must
  project cleanly into both runtime trees via `tools.harness_emit`; `.opencode/` and `.claude/` are
  never hand-edited.

**Non-goals:** a gate on impact output; caching or persisting impact results; injecting impact into
any session banner; contract *versioning* / compatibility analysis (that is carried EVOL-02).

**Success Criteria** (what must be TRUE):

1. `/impact <contract>` reports the affected **contracts** and the affected **packages**, covering
   direct, reverse and transitive relations.
2. No second traversal engine exists: the affected sets come from `contract_graph.query`'s existing
   three functions and the Phase-47 package facts.
3. Nothing is injected: the SessionStart injector's assembled output is byte-identical with and
   without this phase, and no CI job or hook references `/impact`.
4. The `contract-change` route in `harness/agents/orchestrator.md` names `/impact` as the evidence
   step it previously left unfilled, and the emit round-trip to both runtimes is byte-clean.

### 📋 Carried to a later milestone

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
| 47. Package Facts | v2.6 | 5/5 | Complete   | 2026-07-29 |
| 48. Convention Profiles | v2.6 | 3/3 | Complete   | 2026-07-30 |
| 49. Contract Impact | v2.6 | — | Not started | - |
| 50a. Harness Authoring | v2.6 | — | Not started | - |
| 50b. Managed Adopt / Upgrade | v2.6 | — | Not started | - |

Per-phase plan counts for v1.0–v2.2 are preserved in the milestone archives under
`.planning/milestones/`; they are not restated here so this table stays a fixed size.
