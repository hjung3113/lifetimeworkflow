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
- 🚧 **v2.5 De-ceremony** — Phases 39–46 (in progress)
- 📋 **v2.6 Minimal Monorepo Core** — Phases 47–50 (scoped, not started)

## Phases

**Phase Numbering:** integer phases (1, 2, 3) are planned milestone work; decimal phases (26.1,
27.2) are urgent insertions, and appear between their surrounding integers in numeric order.

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
human-approved). Requirements: `.planning/REQUIREMENTS.md`.

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

### 🚧 v2.5 De-ceremony (Phases 39–46) — IN PROGRESS

Design: `.planning/research/v2.5-scoping-FINAL.md` — a three-round two-model panel (`gpt-5.6-sol` high
× `claude-opus-5` high; factual dossier by `gpt-5.6-terra` medium) over a Claude-authored brief,
owner-approved. Requirements: `.planning/REQUIREMENTS.md` (CER-01..11, PROD-01..05).

**Goal:** stop the harness from verifying itself and start it serving its stated purpose — a monorepo
where ① per-package conventions stay consistent, ② interface contracts between packages stay
consistent, ③ an LLM understands cross-project relationships better than in a generic repo, and
④ the thing stays maintainable. Delete ~16k LOC of self-verification machinery, take the gates a human
must personally **author** from five kinds to **zero**, and give the **product** an honest lifecycle.

> **Binding constraint (owner):** never expand scope beyond the purpose by adding verification gates,
> security layers, or ceremony. Default answer to "should we also gate X?" is **NO**; the surface may
> not grow without retiring at least as much.
>
> **The DEV/PRODUCT boundary (the round-3 correction):** rounds 1–2 deleted the product's whole
> lifecycle on the ground that "GSD already owns it" — true of this checkout, false of the product.
> GSD is never installed. Operative rule, ratified in ADR-0012: *no product capability may be declined
> because GSD covers it; only a named shipped artifact may cover it.* What ships is
> `tools/adoption_scan/destinations.py::_CATEGORY_GLOBS`, not the emitter (`generate.py:41-43`
> projects this checkout into itself).

- [x] **Phase 39: Decision Boundary** *(v2.5 A)* — one human-ratified **ADR-0012**: CI + the merge are (completed 2026-07-26)
  the authority; the DEV/PRODUCT boundary is ratified with its operative rule; ADR-0001's
  constitution-member list is superseded (golden leaves the core) and ADR-0010 retires; ADR-0011 is
  accepted with `Date`/`Deciders` filled and its code-before-ratification recorded; RAT-4 / RAT-5 /
  the per-tool deny spelling close as **obsolete-by-deletion**; the bash surface is declared a
  **permanent residual by design**. (CER-01, CER-02, CER-03)
  **Success:** ADR-0012 exists and is `accepted`; ADR-0011 has non-empty `Date`/`Deciders`; the three
  carried items show a recorded disposition in `STATE.md`; SEAL-05 is marked withdrawn, not deferred.
- [x] **Phase 40: Self-Gate Teardown** *(v2.5 A)* — delete `tools/skill_registry` (611 LOC),
  `harness/skills/registry.lock`, CI `registry-lock` and its `gate.needs` entry. **Must precede every
  skill deletion** (`registry.py:44,105-110`). (CER-04) (completed 2026-07-27, `45364d7`)
  **Success:** no `registry.lock` in the tree; `gate.needs` has no dangling job; the suite is green.
  **Verified:** suite 1664 passed/0 failed; `gate.needs` 12 entries, no dangling (YAML-resolved);
  emit-drift + stale-derived + contract-drift + ruff-ratchet clean; UAT 4/4 passed.
  **Carry-forward for 41/43/44 —** deletion-phase ordering is **delete → stage → commit → verify →
  amend-if-red**, NOT verify-before-commit. `tools/adoption_scan` reads git, not the filesystem
  (`destinations.py:217` `git ls-files`), so a tracked-file deletion reds 3 tests until staged (2 of
  them) and committed (`test_catalog_invariant_to_untracked_local_state`, which diffs against HEAD
  and is red by construction while uncommitted). Measured 3→1→0. See `40-01-SUMMARY.md`.
- [x] **Phase 41: Docs-Review Plane Removal** *(v2.5 A)* — unbind the 8 `[[binding]]` rows, then delete (completed 2026-07-26)
  `tools/docs_guard` (6110 LOC), the ledger, hook `ledger_guard` + its `path_deny_globs` entry,
  `/docs-update`, skill `docs-upkeep`, `contracts/harness/docs/*`, CI `docs-guard` + its `gate.needs`
  entry. The severity-flip alternative is provably dead: `guard.py:383-399` classifies `BROKEN` before
  staleness and `cli.py:6-13` exits 1 on `BROKEN` regardless of severity. (CER-05)
  **Success:** the CI fan-in gate is **green**; no human-authored ledger row is required by anything.
- [x] **Phase 42: Adoption Decoupling + Install-Set Repair** *(v2.5 B)* — drop task-control coupling (completed 2026-07-27)
  from `adoption_apply` (inline the ~60-LOC atomic create/replace; inline `gate-registry.json`'s 7
  redaction regexes into `adoption_scan`, live consumer `scan.py:110-112`); **add the surviving
  `tools/**` to `_CATEGORY_GLOBS`**, which today ships commands and CI that invoke Python the target
  never receives (`destinations.py:142-181`). (CER-06, PROD-01)
  **Success:** adoption runs draft → apply with no `task_control` import and no
  `GOLDEN_APPROVE_HUMAN`; a fixture install produces a tree where an emitted command's module exists.
- [ ] **Phase 43: Lifecycle Plane Removal** *(v2.5 B)* — delete 8 `tools/` packages (7021 LOC), the 7
  task-control contracts, commands `intake·phase-gate·handoff·discipline`, hook `resume_gate`, the 5
  discipline skills, `harness/{capabilities,disciplines,risk-policy}.toml`, `.workflow/tasks/`, CI
  `lifecycle-eval` + its `gate.needs` entry; strip `memory_regen`'s active-task block
  (`inject.py:165-195`) keeping the pointer (`:148-162`). No residue package. (CER-07)
  **Success:** no module imports a deleted package; `test_capability_wiring.py` is gone with
  `capabilities.toml`; the suite is green.
- [ ] **Phase 44: Non-Goal Surface Removal** *(v2.5 B)* — delete `secret_scan` (**no replacement
  job**), `deny-domains.*`, `gate-registry.json` and their `DATA_CONTRACT_PATHS` entries,
  `tools/memory_ui` (1756 LOC), `tools/strangler_guard` + `/strangler-step`, `/pipeline` +
  `pipeline-map` + `[pipeline].edges`, skill `gate-model`, `/component`'s topology half; **relocate the
  golden stack to `examples/log-parser/`** (ADR-0002(b): `runner.py:78-85` puts .NET in the core).
  (CER-08, CER-09)
  **Success:** `contracts/` holds 6–8 entries with a rebaselined hash manifest; the core suite passes
  with no golden module; the instance leg still runs golden.
- [ ] **Phase 45: Projection Repair** *(v2.5 C)* — re-emit both trees; update `caps.py` frozensets,
  `emit-manifest.json`, `HARNESS_SIGNATURES` (`merge.py:86-95`); rebaseline
  `contracts/.hashes/manifest.json`; regenerate `docs/reference/**`, contracts-index and the syrupy
  snapshots; repair `gate.needs`; **scrub prose naming deleted surfaces**, including root
  `AGENTS.md:8-9` and `AGENTS.md:52-62`, both outside the managed block. (CER-10, CER-11)
  **Success:** `emit-drift` and `stale-derived` produce an empty diff; no surviving artifact names a
  deleted one.
- [ ] **Phase 46: Product Flow** *(v2.5 C)* — rewrite `harness/agents/orchestrator.md` (already *"the
  only planner in the deployed harness"*, `:48`): strip its 8 dangling citations, retire the 25-row
  table (`:90-129`), add **4 routes** `small-change · bugfix · feature · contract-change` with stop
  conditions, the delegation-packet fields, the **six-field completion contract**
  (`WORKFLOW_CONTRACTS.md:39-46`), one operative sentence per deleted discipline skill, and
  *Repository evidence* from existing `harness_config` + `contract_graph` facts. Add **one** command
  `/flow`; record route · step · next command in the already-shipped `.memory/state/activeContext.md`.
  **Zero flow artifacts imported**; upstream mattpocock skills are not a product dependency.
  (PROD-02, PROD-03, PROD-04, PROD-05)
  **Success:** net **+1 command, +0 agents/skills/tools/contracts/CI/hooks/state files**; a weak model
  can pick a route and close with the six fields from the emitted tree alone; re-emit is byte-clean.

**DAG:** strictly serial `39 → 40 → 41 → 42 → 43 → 44 → 45 → 46`. Deletion-first is literal: 40 before
any skill deletion; 41 before deletions that would classify `BROKEN`; 42 before 43 (adoption and
`memory_regen` must be decoupled first); 45 after all deletions; 46 last, because it is the only
additive phase.

**Ordering rules that must hold inside every phase** (each verified against a file): (1) registry lock
dies before the first skill deletion; (2) unbind a docs binding before deleting a source it names;
(3) every contract deletion edits `contract_hash/hash.py:32` **and** rebaselines the hash manifest in
the same commit; (4) decouple `adoption_apply` + `memory_regen` before deleting `task_control` /
`handoff`; (5) every CI job deletion removes its `gate.needs` entry in the same commit
(`ci.yml:410`); (6) every `harness/` change re-emits in the same commit and every skill/agent
add-or-delete edits `caps.py` (`validate.py:182-183`); (7) never hand-edit `.claude/` or `.opencode/`;
(8) **new** — a deleted `harness/` artifact's dedicated gate test dies in the same commit
(`test_conductor_graph_render.py:31-32,42-57`, `test_capability_wiring.py:30,51`,
`test_language_config.py:48-51`).

**Recorded deviation from the panel:** three split deltas decided by the coordinator and approved by
the owner — `/flow` ships (sol) rather than being cut (opus); the fourth route is `contract-change`
(opus) rather than `research` (sol); the lifecycle is its own phase 46 (sol) rather than a widening of
45 (opus).

#### Phase 39: Decision Boundary

**Goal:** Land one human-ratified ADR-0012 that makes CI + the merge the authority, ratifies the DEV/PRODUCT boundary with its operative rule, retires the superseded decision records, and closes the three carried human-ratification items as obsolete-by-deletion.

Every later v2.5 deletion phase then has a written decision to cite instead of re-litigating scope.

**Requirements:** CER-01, CER-02, CER-03

**Scope:**
- Author `docs/adr/0012-*.md` as `accepted`: CI + the merge are the authority; it names every surface
  this milestone deletes; it supersedes ADR-0001's constitution-member list (golden leaves the core)
  and ADR-0010 (the review ledger retires); it declares the bash surface a **permanent residual by
  design**.
- Ratify the DEV/PRODUCT boundary in the same ADR — DEV is this checkout (Claude Code + GSD, never
  installed); PRODUCT is what `tools/adoption_scan/destinations.py::_CATEGORY_GLOBS` installs into a
  target monorepo — with the operative rule that **no product capability may be declined on the ground
  that GSD covers it**; only a named shipped artifact may cover it.
- **Accept ADR-0011**: fill its empty `Date`/`Deciders` and record that its code landed (`bc9a6d9`)
  before its ratification.
- Record dispositions in `STATE.md` for **RAT-4**, **RAT-5**, and the per-tool deny spelling as
  *obsolete-by-deletion*; mark v2.4's **SEAL-05** *withdrawn*, not deferred.

**Non-goals:** no code deletion, no gate/CI change, no new mechanism, no new tool or contract. This
phase is decision-record-only. Per the milestone's binding constraint, the surface may not grow.

**Success Criteria**:
1. `docs/adr/0012-*.md` exists with `Status: accepted`, non-empty `Date`/`Deciders`, and names the deleted surfaces, the ADR-0001/ADR-0010 supersession, and the bash-residual declaration.
2. ADR-0012 states the DEV/PRODUCT boundary and its operative rule so a later phase can cite it to justify keeping a product capability GSD also covers.
3. `docs/adr/0011-*.md` has non-empty `Date` and `Deciders` and records the code-before-ratification fact with the `bc9a6d9` reference.
4. `.planning/STATE.md` records a disposition for RAT-4, RAT-5 and the per-tool deny spelling as obsolete-by-deletion, and marks SEAL-05 withdrawn (not deferred).
5. ADR-0001 and ADR-0010 carry a superseded-by pointer to ADR-0012 with their decision bodies unedited (append-only / supersede-don't-edit).
6. The existing suite and the contract-drift gate stay green — no contract, gate, or emitted artifact changes from this phase.

#### Phase 40: Self-Gate Teardown

**Goal:** Delete the skill-registry self-gate — the lock file, its tool, its two gate tests and its CI
job — so that no later v2.5 phase can delete a skill and be blocked by a declaration *about* the skill
tree. This is the first pure-deletion phase and it **must precede every skill deletion** in phases
41, 43 and 44: `registry.py:44,105-110` recomputes the surface from `harness/skills/**` and fails on
any diff against the committed lock, so deleting a skill first would red the gate.

Authority to delete is already recorded — ADR-0012 (`docs/adr/0012-ci-and-merge-as-decision-authority.md:96-97`)
names this exact surface.

**Requirements:** CER-04

**Scope** (verified against the tree, 2026-07-26):
- Delete `tools/skill_registry/` — `registry.py`, `__main__.py`, `__init__.py`, `pyproject.toml`,
  `tests/{conftest.py,test_skill_registry.py}` (611 LOC total).
- Delete `harness/skills/registry.lock` (8462 bytes, 24 declared skills).
- Delete the LANE-04 mirror gate `tools/harness_lint/tests/test_skill_registry_lock.py` (50 LOC) —
  ordering rule (8): a deleted `harness/` artifact's dedicated gate test dies in the same commit.
- Delete CI job `registry-lock` (`ci.yml:275-303`, including its comment block) **and** its entry in
  `gate.needs` (`ci.yml:410`) — ordering rule (5), same commit.
- Refresh `uv.lock` (`uv.lock:198` — `source = { virtual = "tools/skill_registry" }`). The workspace
  glob `members = ["tools/*"]` (`pyproject.toml:34`) needs no edit; removing the directory removes the
  member.

**Non-goals:** no skill is deleted in this phase (that starts in 41); no other CI job, hook, contract,
or emitted artifact changes; no replacement gate — per the milestone's binding constraint the surface
may not grow, and the accepted consequence is recorded below. `docs/explanation/agent-workflow-skillset-design-guide.md`
mentions a `registry.lock` as *vendored-skill provenance* — a different, unimplemented concept, not
this gate; it is out of scope here (prose scrub belongs to Phase 45).

**Accepted consequence** (scoping FINAL §156, risk 4): once the lock is gone, a skill `description`
rewrite silently changes agent routing with no gate catching it. Accepted — CI + the merge are the
authority (ADR-0012).

**Success Criteria**:
1. No `registry.lock` anywhere in the tree and no `tools/skill_registry/` directory; `grep -rn "skill_registry\|registry-lock"` over `tools/`, `harness/`, `.github/`, `pyproject.toml` and `uv.lock` returns nothing.
2. `.github/workflows/ci.yml` has no `registry-lock` job and `gate.needs` (`ci.yml:410`) has no dangling `registry-lock` entry — no other `needs` entry is added or removed.
3. `uv run pytest` is green with no collection error from a removed package, and `uv sync --all-packages` resolves against the refreshed `uv.lock`.
4. The emitted trees are unchanged: `emit-drift` and `stale-derived` produce an empty diff (`registry.lock` is a declaration about `harness/skills/`, not an emitted artifact — deleting it must not move `.opencode/` or `.claude/`).
5. The contract-drift gate stays clean — this phase touches no `contracts/` entry and no `contract_hash/hash.py` path list.
6. Net surface change is deletion-only: **−1 CI job, −1 tool package, −1 lock file, −2 gate tests, +0** commands/agents/skills/contracts/hooks.

#### Phase 41: Docs-Review Plane Removal

**Goal:** Delete the human-doc review-obligation plane in its entirety — the bindings, the ledger,
the guard, the hook, the command, the skill, the contracts and the CI job — so that **no gate
requires a human-authored artifact to go green**. This is the last of the five such gates v2.5
retires, and it is what turns the CI fan-in gate green: `docs-guard` has been red since the plane
shipped, because a human ledger row is the only thing that can green it.

Authority to delete is already recorded — ADR-0012 (`docs/adr/0012-ci-and-merge-as-decision-authority.md`)
is `accepted` and supersedes ADR-0010, the record that declared this obligation model.

**Requirements:** CER-05

**Scope** (verified against the tree, 2026-07-27):
- Unbind first: remove the 8 `[[binding]]` rows from `docs/doc-dependencies.toml` and delete
  `docs/.docs-review-ledger.toml` (90 lines) before any tool deletion.
- Delete `tools/docs_guard/` — `guard.py`, `cli.py`, `ledger.py`, `registry.py`, `impact.py`,
  `digest.py`, `exclusions.py`, `__main__.py`, `__init__.py`, `pyproject.toml` and its 8 test modules
  (6110 LOC total).
- Delete the registry and its derived page: `docs/doc-dependencies.toml`,
  `docs/reference/doc-dependencies.md`; delete `contracts/harness/docs/doc-dependencies.schema.json`
  and **rebaseline `contracts/.hashes/manifest.json`** in the same commit.
- Delete the hook and its permission data: `tools/hooks/ledger_guard.py`,
  `harness/plugins/ledger-guard.ts`, the `docs/.docs-review-ledger.toml` entry in
  `harness/permission-matrix.json:34` (and its `_note` prose at `:2`), and the emitted hook group
  (`.claude/settings.json:165`) via re-emit.
- Delete the runtime surface at source: `harness/commands/docs-update.md`,
  `harness/skills/docs-upkeep/`, and their rows in `tools/harness_emit/emit-manifest.json`
  (`:18,41,71,89,101`), then run `python -m tools.harness_emit`.
- Delete the derived staleness queue: `tools/memory_regen/docs_staleness.py` (233 LOC, imports
  `tools.docs_guard` at `:158`), its test, the `("docs", _docs_staleness_pointer(...))` injector row
  (`inject.py:82,217`) and `test_inject_docs_pointer.py`.
- Delete the adoption docs-binding proposal path (DOCSUP-07) incl.
  `tools/adoption_apply/tests/test_docs_binding_proposal.py`.
- Delete CI job `docs-guard` (`ci.yml:317-351`, including its comment block) **and** its entry in the
  fan-in `needs` (`ci.yml:381`) — same commit.
- Sweep the surviving references: `AGENTS.md:106-107`, `.memory/README.md`,
  `harness/skills/gate-model/SKILL.md` (docs-plane claims only), `tools/harness_lint/caps.py:128-129,151`
  and the wiring tests (`test_docs_update_wiring.py`, `tools/hooks/tests/test_settings_coexist.py`,
  `tools/harness_emit/tests/test_coexist.py`, `test_tests_are_isolatable.py`,
  `test_workspace_member_completeness.py`, `tools/docs_sync/tests/test_docs_sync_determinism.py`).
  Refresh `uv.lock` for the removed workspace member.

**Non-goals:** **no replacement of any kind** — no advisory/warn-only docs job, no severity flip, no
successor link-checker. Per the milestone's binding constraint the surface may not grow. The
severity-flip alternative is provably dead: `guard.py:383-399` classifies `BROKEN` before every
staleness check and `cli.py:6-13` exits 1 on `BROKEN` regardless of severity, and every v2.5 deletion
produces `BROKEN`. No new ADR (ADR-0012 already covers it) and **no edit to ADR-0010**
(supersede-don't-edit). Out of scope: `tools/docs_sync` + `/docs-sync` (a different machine), the
full `gate-model` skill (Phase 44), adoption ↔ task-control decoupling (Phase 42), `memory_regen`'s
active-task block (Phase 43).

**Accepted consequence:** a human-authored document can go stale against its sources with nothing
reporting it. Accepted — CI + the merge are the authority (ADR-0012).

**Success Criteria**:
1. The CI fan-in gate is **green**, and `.github/workflows/ci.yml` has no `docs-guard` job and no dangling `docs-guard` entry in the fan-in `needs` (resolved as YAML, not by grep); no other `needs` entry is added or removed.
2. No human-authored artifact is required by any gate: `docs/.docs-review-ledger.toml`, `docs/doc-dependencies.toml` and `tools/docs_guard/` do not exist, and no module imports `tools.docs_guard`.
3. `grep -rnE "docs_guard|docs-guard|docs-review-ledger|ledger_guard|docs-upkeep|docs-update|doc-dependencies"` over `tools/`, `harness/`, `contracts/`, `docs/`, `.github/`, `.claude/`, `.opencode/`, `AGENTS.md`, `.memory/README.md` and `uv.lock` returns nothing (`.planning/` history is exempt and is not rewritten).
4. `uv run pytest` is green with no collection error from a removed package, and `uv sync --all-packages` resolves against the refreshed `uv.lock`.
5. `emit-drift` and `stale-derived` produce an empty diff after `python -m tools.harness_emit` — the removals reached the emitted trees through the emitter, not by hand-editing `.opencode/` or `.claude/`.
6. `contract-drift` is clean against a rebaselined `contracts/.hashes/manifest.json` that no longer carries a `contracts/harness/docs/` entry, and the ruff ratchet is clean.
7. Net surface change is deletion-only: **−1 CI job, −1 tool package, −1 hook, −1 command, −1 skill, −1 contract, −2 data files, +0** commands/agents/skills/contracts/hooks. Removed LOC is reported from `git diff --stat`, not estimated.

#### Phase 42: Adoption Decoupling + Install-Set Repair

**Goal:** Make adoption a standalone product capability — `draft → apply → PR review`, with no
task-control import and no `GOLDEN_APPROVE_HUMAN` — and make the installed product **non-inert** by
shipping the Python its own emitted artifacts invoke. Today a target monorepo receives commands that
shell `uv run python -m tools.X`, receives `.github/workflows/**` running the same modules, receives
`pyproject.toml` stubs, and receives **none of the Python**.

Authority: ADR-0012's DEV/PRODUCT boundary and its operative rule — *no product capability may be
declined because GSD covers it; only a named shipped artifact may cover it.* PROD-01 is the first
place that rule bites.

**Requirements:** CER-06, PROD-01

**Scope** (verified against the tree, 2026-07-28 — the requirement prose predates three changes):
- **The task-control coupling is `approval.py:37`**, not `apply.py`: `from tools.task_control.manager
  import show`, plus `HUMAN_TOKEN_ENV = "GOLDEN_APPROVE_HUMAN"` (`approval.py:45`). Drop the import
  and the task-revision binding it serves.
- **The ~60-LOC atomic create/replace is ALREADY inlined** in `tools/adoption_apply/apply.py`
  (`:207`, `:241`) — only the docstrings still say "Mirrors `tools.task_control.manager._atomic_create`".
  This phase therefore only has to update that prose, not re-inline the sequence. Confirm before planning.
- **Inline the secret patterns** `tools/adoption_scan/scan.py` reads from
  `contracts/harness/task-control/gate-registry.json` (`scan.py:48`, live consumer `:110-112`).
  There are **8** patterns, not 7. `scan.py:52-54` already owns `SECRET_PATH_GLOBS` for exactly this
  reason — follow that precedent. The contract file itself is Phase 44's deletion (CER-08); this phase
  removes adoption's dependency on it.
- **Add the surviving `tools/**` to `_CATEGORY_GLOBS`** (`tools/adoption_scan/destinations.py:142-181`).
  A data row, not a mechanism. Scope it to what survives v2.5 — do not ship packages phases 43/44 delete.
- Adoption's own tests move with it: anything asserting the task-revision binding or the human-token
  gate on the adoption path.

**Non-goals:** no new gate, tool, contract, or dependency — the milestone's binding constraint holds.
Do NOT delete `gate-registry.json`, `tools/task_control`, or `secret_scan` here (Phases 43/44 own
those); this phase only severs adoption's dependence on them. No change to the adoption contracts'
shapes, and no widening of what `/adopt` may write without a human.

**Accepted consequence:** the adoption apply path loses its human-token gate. That is the point —
CI + the merge are the authority (ADR-0012), and adoption's real review is the PR.

**Success Criteria**:
1. `grep -rn "task_control" tools/adoption_apply/ tools/adoption_scan/` returns nothing — no import, no docstring reference, no test.
2. `grep -rn "GOLDEN_APPROVE_HUMAN" tools/adoption_apply/ tools/adoption_scan/` returns nothing; a full draft → apply run completes with the variable unset.
3. `tools/adoption_scan/scan.py` reads no file under `contracts/harness/task-control/`; its 8 secret patterns are owned locally alongside `SECRET_PATH_GLOBS`, and the secret-redaction tests still pass unchanged.
4. `_CATEGORY_GLOBS` contains a `tools/**` entry, and a **fixture install** produces a target tree in which every module an emitted command invokes (`uv run python -m tools.X`) actually exists — asserted by a test, not by inspection.
5. `uv run pytest -q` is green; `emit-drift`, `stale-derived`, `contract-drift` and the ruff ratchet are clean.
6. Net surface change adds no command, agent, skill, contract, hook, or dependency — the only additions are data rows and locally-owned constants.

#### Phase 43: Lifecycle Plane Removal

**Goal:** Delete the task-control lifecycle plane whole — 8 `tools/` packages, its contracts, its four
commands, its hook, its five discipline skills, its three `harness/*.toml` declarations, its
`.workflow/tasks/` state directory, and its CI job. **No residue package**: a Python state manager must
be unreachable in the product by construction, not merely unused.

This is the milestone's largest single deletion (**7021 LOC** of packages alone, verified 2026-07-28).
Phase 42 already severed adoption — the last non-lifecycle consumer — so the plane now stands alone.

Authority: ADR-0012 names this surface; the lifecycle's in-session gates are exactly the ceremony v2.5
retires, and CI + the merge are the authority that replaces them.

**Requirements:** CER-07

**Scope** (every path verified present, 2026-07-28):
- **8 packages, 7021 LOC total** — `tools/task_control` (1677), `tools/handoff` (1238),
  `tools/discipline` (990), `tools/risk_router` (877), `tools/evidence` (783), `tools/task_packet`
  (605), `tools/lifecycle_eval` (472), `tools/capability` (379).
- **6 of the 7 task-control contracts**: `attestation`, `evidence`, `handoff`, `state`, `task`,
  `transitions`. ⚠ **`gate-registry.json` is NOT deleted here** — CER-08 names it explicitly together
  with its `DATA_CONTRACT_PATHS` entry (`tools/contract_hash/hash.py:32`), so Phase 44 owns it. CER-07's
  prose says "the 7 task-control contracts"; the live directory holds 7 files and one of them is
  claimed by the next phase. Recorded here so the two phases do not both try to delete it.
  Rebaseline `contracts/.hashes/manifest.json` with the deletions.
- **4 commands**: `harness/commands/{intake,phase-gate,handoff,discipline}.md` + their emitted copies
  (via the emitter, never by hand) + their `tools/harness_emit/emit-manifest.json` rows.
- **The hook**: `tools/hooks/resume_gate.py` and `harness/plugins/resume-gate.ts`, plus the emitted
  `.claude/settings.json` hook group — which is a hand-maintained literal in
  `tools/harness_emit/merge.py` (`HARNESS_SIGNATURES` + a hook-group dict), NOT a projected file.
  Phase 41 built the `RETIRED_SIGNATURES` drop mechanism there for exactly this case and left it in
  place with an empty tuple — use it, then empty it again once the re-emit has landed.
- **5 discipline skills**: `harness/skills/{clarify,diagnose,domain-modeling,test-driven-change,adversarial-review-panel}/`
  and their `tools/harness_lint/caps.py` declarations (`EXPECTED_SKILLS` hard-fails the emitter before
  it writes a byte — Phase 41 hit this).
- **3 declarations**: `harness/{capabilities,disciplines,risk-policy}.toml`, and
  `tools/harness_lint/tests/test_capability_wiring.py` which dies with `capabilities.toml`.
- **State + CI**: `.workflow/tasks/`, CI job `lifecycle-eval` (`ci.yml:221-231`) and its entry in the
  fan-in `needs` (`ci.yml:345`) — resolved as YAML, not grep.
- **`tools/memory_regen/inject.py`**: strip the active-task block, KEEP the activeContext pointer.
  These are adjacent in the same function — read both before cutting.

**Non-goals:** **no residue package** — do not leave a shim, a stub, a "minimal state manager", or a
deprecation path. No replacement gate or CI job. Do not delete `gate-registry.json`, `secret_scan`,
`deny-domains.*`, `tools/memory_ui`, or the golden stack (Phase 44). Per the binding constraint the
surface may not grow.

**Accepted consequence:** in-session task lifecycle, risk routing, evidence bundles and handoffs stop
existing as harness machinery. Recorded and intended — the equivalent function is the PR.

**Success Criteria**:
1. None of the 8 package directories exists, and `grep -rnE "task_control|task_packet|risk_router|tools\.evidence|tools\.handoff|tools\.discipline|tools\.capability|lifecycle_eval" tools/ harness/ contracts/ .github/ .claude/ .opencode/` returns nothing outside `.planning/`.
2. No module imports a deleted package: `uv run pytest --collect-only -q` exits 0 with zero collection errors.
3. `contracts/harness/task-control/` contains only `gate-registry.json`; the hash manifest is rebaselined and `uv run python -m tools.contract_drift.drift` exits 0.
4. `test_capability_wiring.py` is gone with `capabilities.toml`; `caps.py` declares no deleted skill or command.
5. CI has no `lifecycle-eval` job and the YAML-resolved fan-in `needs` has no dangling entry (10 entries after removal; no other entry added or removed).
6. `tools/memory_regen/inject.py` no longer emits an active-task block but STILL emits the activeContext pointer — asserted by a test, not by reading.
7. `uv run pytest -q` green; `emit-drift`, `stale-derived`, `contract-drift`, ruff ratchet clean; `uv.lock` refreshed for the removed workspace members.
8. Net surface change is deletion-only: **−8 packages, −6 contracts, −4 commands, −1 hook, −5 skills, −3 declarations, −1 CI job, +0** of anything.

### 📋 v2.6 Minimal Monorepo Core (Phases 47–50) — SCOPED, NOT STARTED

Smallest goal-complete subset = all of v2.5 **+ 47 + 49**. ① is already covered by the lint adapters +
nearest-wins `AGENTS.md` + `/component`; ② by `contracts/` + `contract_hash`/`contract_drift` +
`contract_graph` + CI; ④ by append-only ADR + the derived plane + ADR-0011's CI-strong posture. The
genuine gap is ③.

- [ ] **Phase 47: Package Facts** — extend `adoption_scan/detect.py`'s manifest detection
  (`:41-47,100-121`) into a committed **derived** package + dependency graph feeding `contract_graph`;
  `[[components]]` demoted to an override slot. **Report-only, no gate.** (MONO-01)
- [ ] **Phase 48: Convention Profiles** — nearest-wins per-package convention data + language→lint/test
  mapping, populated by `/component` step 2. (MONO-02)
- [ ] **Phase 49: Contract Impact** — one `/impact` command over `contract_graph.query`'s existing
  `direct`/`reverse`/`transitive` (`query.py:29,39,55`) + package facts; fills phase 46's evidence
  slot. On demand only, **no SessionStart injection**. (MONO-03)
- [ ] **Phase 50: `harness-author` + Managed Adopt/Upgrade** — (a) `harness-author`: one skill, Q&A
  with grounded `path:line` defaults, **absorbs `skill-creator`** (net skills ±0), zero new
  packages/commands/contracts, output runtime-neutral under `harness/` only; **presupposes PROD-01**.
  (b) simplified `/adopt` as a managed install/update with one manifest + conflict report — **does not
  start without a real multi-package target**. (MONO-04)

**DAG:** `47 → {48, 49}`; `50` needs `48` and, for its (b) half, a real target.

### 📋 Carried to a later milestone

- **EVOL-02** contract versioning / compatibility engine — the only survivor; still a standalone
  engine needing its own ADR.
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
| 40. Self-Gate Teardown | v2.5 | 0/TBD | Not started | - |
| 41. Docs-Review Plane Removal | v2.5 | 5/5 | Complete   | 2026-07-26 |
| 42. Adoption Decoupling + Install-Set Repair | v2.5 | 5/5 | Complete   | 2026-07-27 |
| 43. Lifecycle Plane Removal | v2.5 | 0/5 | Planned | - |
| 44. Non-Goal Surface Removal | v2.5 | 0/TBD | Not started | - |
| 45. Projection Repair | v2.5 | 0/TBD | Not started | - |
| 46. Product Flow | v2.5 | 0/TBD | Not started | - |
| 47. Package Facts | v2.6 | — | Scoped | - |
| 48. Convention Profiles | v2.6 | — | Scoped | - |
| 49. Contract Impact | v2.6 | — | Scoped | - |
| 50. harness-author + Managed Adopt | v2.6 | — | Scoped | - |

Per-phase plan counts for v1.0–v2.2 are preserved in the milestone archives under
`.planning/milestones/`; they are not restated here so this table stays a fixed size.
