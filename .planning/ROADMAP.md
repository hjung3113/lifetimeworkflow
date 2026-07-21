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
- 📋 **Next milestone** — not yet scoped (`/gsd:new-milestone`)

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

### 📋 Next Milestone — not yet scoped

Run `/gsd:new-milestone` to scope it. Items already known to be waiting, carried in
`.planning/STATE.md` under *Deferred Items*:

- **RAT-4 / RAT-5** — two open provenance obligations (the Phase-28 `HARNESS_DEV_BYPASS`
  constitution write; four ADRs unmerged to `main`). Neither blocks mechanically.
- **Constitution-plane write-denies are spelled per-tool** — the deny fires on `Write|Edit` while
  `bash."uv *"` is an unprompted `allow`, and `contract_guard` shares the shape. Decided at the v2.3
  close: record now, repair here, together with the ADR-0010 clause 3b wording correction.
- **`ruff check` is not a CI gate**, and carries 617 pre-existing errors.
- **`examples/**` instance-local docs-registry overlay** — the seam left deliberately open by
  28-CONTEXT D-14.
- **Deferred requirement sets** — TCP-F01..F05 (v2.2 carry), impact-driven task-evidence policy,
  a contract versioning/compatibility engine, signed external evidence attestation, STRICT rollback.

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

Per-phase plan counts for v1.0–v2.2 are preserved in the milestone archives under
`.planning/milestones/`; they are not restated here so this table stays a fixed size.
