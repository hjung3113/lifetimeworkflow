# Contract-First 폴리글랏 에이전트 하네스 템플릿 (Contract-First Polyglot Agent-Harness Template)

> **방향 전환 (2026-07-08, ADR-0002):** 이 프로젝트는 원래 반도체 설비 로그파서 파이프라인 **전용** 하네스로 출발했으나, 실제 구현 방향이 계속 바뀌면서 **재사용 가능한 범용 하네스 템플릿**으로 재정의되었다. 로그파서 도메인은 삭제하지 않고 `examples/log-parser/`의 **worked example(레퍼런스 인스턴스)**로 강등한다. Phase 1–4에서 만든 durable한 아키텍처는 그대로 유지된다.

## What This Is

**어떤 contract-first 폴리글랏 프로젝트든** 에이전트가 만들고·유지보수·개발·리팩토링할 수 있게 해주는 **재사용 가능한 에이전트 하네스 템플릿**이다. 산출물은 특정 컴포넌트 구현 코드가 아니라 하네스 그 자체 — opencode/Claude agents·commands·skills·plugins, Diátaxis+ADR+contracts 문서구조, 세션을 넘어 유지되는 두 평면(헌법/파생) 컨텍스트 메모리 층, 그리고 계약·골든·drift·권한을 강제하는 런타임 게이트다. 대상 사용자는 (1) 이 템플릿을 clone/scaffold해 자기 프로젝트에 얹는 개발자와 (2) 그들을 돕는 코딩 에이전트다. **도메인·언어는 하드코딩이 아니라 채워 넣는 슬롯**이다 — 반도체 로그파서는 그 슬롯을 채운 하나의 예시일 뿐.

## Core Value

**계약(contracts)을 단일 정본으로 두고, 폴리글랏 표현차·전환 리스크를 하네스가 자동으로 강제·검증한다 — 그리고 이 강제 구조가 특정 도메인·언어에 묶이지 않고 어느 프로젝트에나 재사용된다.** 에이전트가 레포에서 "어떻게 개발·유지보수·리팩토링하는가"가 부족(tribal knowledge)이 아니라 실행 가능한 스킬·커맨드·훅으로 박혀 있고, 그 박힌 구조를 도메인만 갈아끼워 다음 프로젝트로 가져갈 수 있어야 한다.

> **v2.0 Long-Horizon — ✅ SHIPPED 2026-07-14:** All 3 phases (9 α, 10 β, 11 γ) shipped and verified; 11/11 requirements validated; milestone audit passed (integration 12/12, 568 tests green). Archived to `.planning/milestones/v2.0-*`. See `## Requirements → Validated`.

> **v2.1 MEM2 — Process Memory & Provenance Reframe — ✅ SHIPPED 2026-07-18:** All 5 phases (12–16) shipped and verified; 7/7 requirements (MEM2-01..07) validated; milestone audit passed (integration 6/6, browser round-trip 5/5, 690 tests green). Archived to `.planning/milestones/v2.1-*`. See `## Requirements → Validated`.

## Current State

**v2.3 shipped 2026-07-22** — the harness's topology is no longer assumed linear (an authority-centred
contract-relationship *graph*, with the legacy `[pipeline]` slot lowered into it additively rather
than migrated), it can be *adopted into* an existing brownfield repo through a deterministic
inventory → plan → manifest → refuse-by-default apply path carried as an ordinary `.workflow/tasks/`
task, and human review of human-written prose is now an enforceable dated obligation rather than a
hope — a registry + committed ledger + a guard that fails on BROKEN/STALE_REQUIRED. Ratified as
ADR-0009 and ADR-0010.

v1.0 (1–8) + v2.0 (9–11) + v2.1 (12–17) + v2.3 (24–29) are archived under `.planning/milestones/`;
v2.2 (18–23) is recorded in `MILESTONES.md` with its phase dirs left in place. **v2.4 closed PARTIAL
on 2026-07-26** (34–37 shipped; 30 partial; 31/32/33 cut; 38 landed as code) and **v2.5 De-ceremony is
now in progress** — see the Current Milestone section.

Two provenance obligations stay open across the boundary (RAT-4, RAT-5) plus one recorded
harness-wide finding: constitution-plane write-denies are spelled per *tool*, so a write through
`bash."uv *"` is not denied the way the same write through `Write`/`Edit` is. All three are carried
in `STATE.md` under *Deferred Items*. **v2.5 phase 39 closes all three as obsolete-by-deletion, not by
mechanism** — they are one finding with one cause (every human-ratification gate here assumes
reviewer ≠ author, and this repo has one owner), and the planes they guard are deleted in phases 41
and 44.

**Phase 39 complete 2026-07-26** — ADR-0012 (*CI and the Merge as Decision Authority*) is ratified
and accepted: CI fan-in + the merge to `main` are the decision authority, the v2.5 deletion
enumeration is recorded as intent-at-ratification, the DEV/PRODUCT boundary carries an operative
rule (no product capability may be declined because GSD covers it — only a named shipped artifact
may cover it), ADR-0001's constitution-member list is superseded and ADR-0010 retires, the bash
surface is declared a permanent residual by design, and the phase's own human checkpoint is a
one-time transition creating no standing gate. ADR-0011 is formally accepted alongside it. RAT-4,
RAT-5, and the per-tool deny-spelling gap are recorded `obsolete-by-deletion`; v2.4's SEAL-05 is
`withdrawn`. Requirements CER-01/02/03 validated in Phase 39.

## Current Milestone: v2.5 De-ceremony

**Goal:** stop the harness from verifying itself and start it serving its stated purpose. Four
milestones of gate machinery grew a surface where the *harness's own integrity* is the subject and the
monorepo is the pretext. v2.5 deletes ~16k LOC of that machinery, reduces the gates a **human must
personally author** from 5 kinds to **0** (the human's only act becomes reviewing and merging a PR),
and — the round-3 correction — gives the **product** an honest lifecycle, because GSD governs only
this dev checkout and is never shipped.

**The purpose all scope is now measured against (owner's restatement):** a monorepo of several
related, closely-coupled projects, where ① each package's conventions stay consistent, ② the
interface contracts between packages stay consistent, ③ an LLM working in the repo understands
cross-project relationships better than it would in a generic repo, and ④ the thing stays
maintainable long-horizon. **Nothing more.**

**Binding constraint (owner, verbatim in intent):** 절대 만들고자 하는 목적 이상으로 불필요한 검증
게이트나 보안 등으로 프로젝트 규모를 **확장하지 말 것** — never expand scope beyond the purpose by
adding verification gates, security layers, or ceremony. Default answer to "should we also gate X?" is
**NO**; the surface may not grow without retiring at least as much. This constraint governs every
future phase of this project, not just v2.5.

**The DEV / PRODUCT boundary (ratified in this milestone's ADR-0012):** the **DEV** scope is this
checkout — Claude Code + GSD (`.planning/**`, `.claude/get-shit-done/**`, `/gsd:*`) — which is never
installed. The **PRODUCT** scope is what `tools/adoption_scan/destinations.py::_CATEGORY_GLOBS`
installs into a target monorepo, run on opencode (and Claude Code) by a **weaker in-house model**.
Operative rule: *no product capability may be deleted or declined on the ground that GSD covers it* —
GSD is not there; only a **named shipped artifact** may cover it.

**Target features (8 phases, 계속 번호 39–46):**
- **A. Decision + teardown** *(phases 39–41)* — one human-ratified **ADR-0012** making CI + the merge
  the authority and ratifying the DEV/PRODUCT boundary; then the self-gates come down in
  dependency order: `skill_registry` + `registry.lock`, then the whole docs-review plane
  (`tools/docs_guard` 6110 LOC + the ledger + `ledger_guard`), which is what turns the CI fan-in green.
- **B. Plane removal** *(phases 42–44)* — adoption decoupled from task-control **and the install set
  repaired** (`_CATEGORY_GLOBS` ships no `tools/**` today, so every emitted command and the shipped CI
  are broken in a target repo); the 8-package task-control lifecycle plane deleted whole; the
  non-goal surface deleted (`secret_scan`, `deny-domains`, `memory_ui`, strangler, the pipeline
  metaphor, `gate-model`) with the golden stack **relocated** to `examples/log-parser/`.
- **C. Repair + the product's lifecycle** *(phases 45–46)* — re-emit both runtime trees, rebaseline
  hashes/snapshots/`caps.py`, scrub prose that names deleted surfaces; then author the product
  lifecycle where it already lives: `harness/agents/orchestrator.md` (which already declares itself
  the only planner in the deployed harness) gains **4 routes** — `small-change · bugfix · feature ·
  contract-change` — the delegation-packet fields, the six-field completion contract, and resume via
  `.memory/state/activeContext.md`, plus **one** new command `/flow`. **+1 command, +0 everything
  else**; no router agent, no state machine, no gate.

**Key context (ratified design):** `.planning/research/v2.5-scoping-FINAL.md`, produced by a
three-round two-model panel (`gpt-5.6-sol` high × `claude-opus-5` high — independent review →
cross-rebuttal → dev/product re-derivation) over a Claude-authored brief, with `gpt-5.6-terra` medium
supplying the factual carry-forward dossier. The panel **overruled the brief** on six counts, each
line-cited: the docs-guard severity flip provably cannot work (`guard.py:383-399` classifies `BROKEN`
before staleness and `cli.py:6-13` exits 1 on `BROKEN` regardless of severity, and every deletion in
this milestone produces `BROKEN`); import **zero** matt-flow artifacts (§0 budget + the vendored routes
hard-require `.opencode/workflows/scripts/*.sh` that the emitter owns); mattpocock upstream skills are
**not** a product dependency, even optionally (the vendored contract says *stop*, not degrade);
`.flow/state.md` is a second control plane over `.memory/state/activeContext.md`; the golden stack
violates ADR-0002(b) by holding .NET code in the core; and `harness-author` is admissible only under
hard constraints (one skill, absorbs `skill-creator`, zero new packages/commands/contracts).

**OUT of scope — carried to v2.6 (phases 47–50):** manifest-derived package facts (③); per-package
convention profiles (①); the `/impact` command over the existing `contract_graph` queries (②③);
`harness-author` + managed adopt/upgrade (④, and its (b) half does not start without a real
multi-package target). Smallest goal-complete subset = all of v2.5 + phases 47 + 49. Also out,
permanently: any gate whose purpose is to prove the harness cannot bypass itself; any security control
not motivated by a threat this repo faces; any human-must-**author** step.

## Partially Shipped Milestone: v2.4 Gate Right-Sizing, Carried Debt, Lane Discipline

> ⚠ **CLOSED PARTIAL 2026-07-26.** Phases **34–37 complete and verified** (1683 passed / 8 snapshots):
> ruff as a required CI gate, the carried-debt dispositions, discipline skills + adversarial panel,
> capability routing + `registry.lock`. Phase **30** landed its contract pair only (`27ee704`, human);
> plans 30-02/03/04 were never written or executed — and v2.5 **cuts** them, because
> `deny-domains.json`'s own `_note` says no hook reads it and a drift test over it would prove a file
> equals itself. Phases **31/32 were cut by ADR-0011**; phase **33 never started** and is cut
> (`secret_scan` is deleted outright in v2.5-44, so SEAL-04 is moot, and SEAL-05's portable
> ratification record is exactly the mechanism v2.5 replaces with a recorded decision). Phase **38**
> (gate right-sizing, DEREG-01) **landed as code** in `bc9a6d9` but was never formalized as a phase —
> and its ADR-0011 is still `proposed` with empty `Date`/`Deciders`. **v2.5 phase 39 discharges that
> bookkeeping**: it accepts ADR-0011, records that its code preceded its ratification, and closes
> RAT-4 / RAT-5 / the per-tool deny spelling as *obsolete by deletion* rather than by mechanism —
> all three being one finding with one cause: every human-ratification gate here assumes reviewer ≠
> author, and this repo has one owner. Two drafted docs-review ledger rows remain unlanded; phase 41
> deletes the plane that wants them.

**Goal (re-pivoted 2026-07-26, ADR-0011):** originally "make every declared gate actually fire". The
human found that reading of "enforce" had over-regulated the dev inner loop — the in-session guard
wall slowed development and deadlocked the session twice. Re-scoped to **right-size the gates:
dev-light, CI-strong.** Enforcement's authoritative home is CI + CODEOWNERS (which serve the real
goal — consistency + long-horizon maintainability); the in-session guards degrade instead of
deadlocking and a dev session opts out via `HARNESS_DEV_LIGHT`. Carried debt and lane discipline
stay in scope; SEAL-02/03 (adding MORE in-session denies) are cut.

**Target features (8 phases, 계속 번호 30–37):**
- **A. Gate Integrity** *(SEAL-01..05, phases 30–33)* — a deny-domain REGISTRY (constitution /
  secret / review-ledger declared separately with owner, bypass semantics, covered tool surfaces and
  runtime adapters, plus per-domain drift tests) → a ratified threat model and **chosen enforcement
  posture** for the uncovered bash surface → implementation of that posture in both runtimes with
  live negative controls → `secret_scan` reading its patterns from the contract, RAT-4's disposition
  and a portable ratification record.
- **B. Carried Debt** *(DEBT-01..04, phases 34–35)* — `ruff check` becomes a required CI gate with a
  ratcheting baseline; phase-27 verification disposition; compile-the-graph-once (28 IN-03);
  `DEF-05-02-1` verified and closed.
- **C. Lane Discipline** *(LANE-01..04, phases 36–37)* — the v2.2 TCP-F carry: discipline skills
  wired into the task lifecycle, a STRICT+ adversarial review panel as a declared lane requirement,
  specialist allowlist + capability-neutral routing, and skill `registry.lock` + adapter CI.

**Key context (ratified design):** `.planning/research/v2.4-scoping-FINAL.md`. Scoped by one codex
sol review pass (low effort, read-only, line-cited) over a Claude-authored draft — NOT the full
sol-vs-fable debate panel used for v2.2/v2.3, by explicit instruction. The review corrected three
claims this repo had made about itself, most importantly withdrawing the v2.3 close's accusation
that ADR-0010 clause 3b "overclaims" (it does not; it scopes layer 1 explicitly to
`PreToolUse(Write|Edit)`, so the defect is a MISSING FOURTH LAYER — corrected by `455b366`).
**Recorded deviation:** the reviewer advised cutting Themes C *and* D and shipping five phases; the
human kept C and cut D, accepting the stated sizing risk.

**OUT of scope (Theme D, carried explicitly to the next milestone):** impact-driven task-evidence
policy (EVOL-01, needs its own ADR); contract versioning/compatibility engine (EVOL-02); `examples/**`
instance-local docs-registry overlay (EVOL-03); TCP-F05 signed external attestation + STRICT
rollback. Also out: repairing GitHub's trust model (branch protection, reviewer eligibility) — the
harness may define a portable ratification record, not fix CODEOWNERS for a solo owner.

## Shipped Milestone: v2.3 Contract Graph, Brownfield Adoption, Living Docs

> ✅ **SHIPPED 2026-07-22.** 10 phases (24, 25, 26, 26.1, 26.2, 27, 27.1, 27.2, 28, 29), 43 plans,
> 58 tasks, 310 commits over 3 days. All 21 requirements (TOPO-01..07, ADOPT-01..07, DOCSUP-01..07)
> validated; 16/16 fan-in gates exit 0. Archived to `.planning/milestones/v2.3-*`.

**Goal:** 선형 파이프라인 슬롯을 임의의 프로젝트 간 계약 관계를 담는 결정론적 **권위-중심 contract-relationship graph**로 일반화하고, 그 그래프를 (B) 기존 레포에 하네스를 **도입(brownfield adoption)**하고 (C) 사람이 작성한 문서의 **drift를 탐지·갱신**하는 두 워크플로의 어휘로 사용한다 — 데이터 형상·결정론적 분석기·얇은 워크플로만 추가하고 두 번째 프레임워크/엔진/권위 평면은 만들지 않는다.

**Target features (6 phases, 계속 번호 24–29):**
- **A. Contract-Relationship Graph** *(TOPO-01..07, phases 24–25)* — `contracts/harness/topology/` 아래 사람 승인 관계 record 스키마 + 추가형 `[[contract_graph.relationships]]` TOML 슬롯 + 레거시 `[pipeline]` **lowering**(추가형 union, 마이그레이션 아님) + 도메인 중립 컴파일러·consistency 게이트 + affected-set 질의 + `/pipeline`·`pipeline-map`·orchestrator 일반화.
- **B. Brownfield Adoption** *(ADOPT-01..07, phases 26–27)* — 결정론적 read-only inventory → evidence 분류(observed/inferred/unknown) 매핑 → destination/disposition manifest → adoption을 `.workflow/tasks/` 작업으로(v2.2 CAS/evidence/HANDOFF 재사용, 새 `.workflow/adoption/` 평면 없음) + 구조적 헌법-쓰기 거부 + 해시 결합 사람 ratification + `/adopt` skill·command + 3개 fixture.
- **C. Living Docs** *(DOCSUP-01..07, phases 28–29)* — 중앙 `docs/doc-dependencies.toml` + review ledger + FRESH/BROKEN/STALE_REQUIRED/STALE_ADVISORY/UNCOVERED 게이트 + 파생 staleness 큐·SessionStart pointer + `/docs-update` drive loop(ADR/reference/derived 제외).

**Key context (ratified design):** 설계는 sol-vs-fable 토론 패널로 scoping — 독립 제안 → 교차 반박 → codex sol이 병합 FINAL authored, 사람 승인. 원본: `.planning/research/v2.3-scoping-FINAL.md`. 확정 결정: `TOPO-*`(GEN-04 가드와의 충돌 회피, `GEN-*` 아님) · 추가형 lowering(identical-or-fail 마이그레이션 아님) · task-plane adoption(sibling 평면 아님) · 중앙 registry(per-doc frontmatter 아님) · required/advisory staleness 심각도. DAG `24→25→28→29` + `24→26→27→29`. 3개 open-Q 기본값 채택: 슬롯명 `[[contract_graph.relationships]]`; required-staleness 바인딩 = 루트 README·AGENTS·task-lifecycle how-to·template-and-instances explanation·adoption runbook(나머지 advisory); ADR 번호는 구현 시 할당(topology 모델에 ADR-0009 예약). 헌법 제약 전면 준수: contract-first / machines-gate-humans-ratify / GEN-04 / 모델 식별자 미포함 / harness-emit 왕복 / two-plane / 단일 orchestrator / reuse-not-reimplement.

**OUT of scope:** version/semver 호환 엔진, impact-driven task-evidence 정책(별도 ADR로 연기), topology runtime/broker, 두 번째 orchestrator, autonomous contract 추출, accepted-ADR 편집, TCP-F01..F05·signed external attestation·STRICT rollback.

## Requirements

### Validated

- ✓ **Self-maintaining derived artifacts + curator (v2.0 α)** — `curator` 에이전트 + CI stale-derived 게이트 + write-시 저렴/PR-시 무거운 훅 포스처 + `/refresh-memory`. *(v2.0, Phase 9)*
- ✓ **Context-economy fan-out/synthesize (v2.0 β)** — 팬아웃→요약회수→합성 skill/command + citation-bearing 반환 계약 + delegate-vs-inline 컨텍스트-예산 배선. *(v2.0, Phase 10)*
- ✓ **Multi-repo workspace (v2.0 γ)** — `workspace.toml` 매니페스트(project.toml 슬롯 한 단계 상향) + repo-scoped β 팬아웃 + 크로스-레포 contract drift/golden 게이트 + repo:stage 파이프라인 edge + core→workspace-member GEN-04 가드. *(v2.0, Phase 11)*

- ✓ **ADR-0006 + emit 왕복 (v2.1 MEM2-06)** — 사람-게이트 append-only ADR-0006 + `/agree`·갱신 skill·`AGENTS.md` managed block을 Phase-7 emitter로 두 런타임(`.opencode/` + `.claude/`)에 왕복. emit-drift clean, 모델 id 없음(placeholder tier만), GEN-04 green. *(v2.1, ADR=Phase 12 / emit=Phase 15)*

- ✓ **PROCESS 메모리 채널 (v2.1 MEM2-01)** — committed·human-authored `.memory/agreements/<slug>.md` per-guideline 티어(§7b), provenance 스탬프가 찍힌 엔트리; ADR/Key-Decisions를 링크하되 재진술 금지(§7c). *(v2.1, Phase 12)*
- ✓ **Injector provenance 재구성 (v2.1 MEM2-02)** — priority-0 full-body working-agreements 지시문 + data-scoped 배너; determinism(바이트 동일) + ~4000-char budget 보존. *(v2.1, Phase 13)*
- ✓ **Distrust 문구 재구성 (v2.1 MEM2-03)** — echo되는 5개 표면 전부 data-authority로; 'confirm before trusting' 잔여 없음. *(v2.1, Phase 12)*
- ✓ **`/agree` write path + anti-churn 가드 (v2.1 MEM2-04)** — 명시적 사용자 피드백 전용 append/retire + `tools/harness_lint` provenance/anti-invent 가드. *(v2.1, Phase 14)*
- ✓ **Progress staleness 가드 (v2.1 MEM2-05)** — `/checkpoint` `updated:` stamp + agent-side freshness(verbatim, `assemble()` 내 wall-clock 없음). *(v2.1, Phase 13)*
- ✓ **로컬 메모리 웹 UI (v2.1 MEM2-07)** — 127.0.0.1-only 무-네트워크 툴 + DERIVED pointer-index + surface-and-confirm 참조 무결성, 브라우저 왕복 검증 5/5. *(v2.1, Phase 16)*

- ✓ **Adaptive Task Control Plane (v2.2, TCP-01..18)** — 기계 판독 task packet(`.workflow/tasks/`) + 결정론적 7축 위험 라우터(FAST/STANDARD/STRICT/CONTROLLED) + 원자적 상태 관리자(flock+revision CAS) + fail-closed `/phase-gate` + forgery-detecting evidence adapters + immutable HANDOFF·gated fresh-session resume + 사람 승인 lifecycle fixtures + ADR-0008. 904 tests green, origin 푸시. *(v2.2, phases 18–23)*

- ✓ **Contract-Relationship Graph (v2.3 A, TOPO-01..07)** — 사람 승인 relationship record 스키마 + 추가형 `[[contract_graph.relationships]]` 슬롯 + 레거시 `[pipeline]` 추가형 lowering(마이그레이션 아님, 기존 선형 config 바이트 불변) + 도메인 중립 `compile_graph()` + 안정 진단 슬러그 3종 + cycle-safe `direct`/`reverse`/`transitive`(ids + 연결 경로) + `/pipeline`·`pipeline-map`·orchestrator 일반화(새 command·persona 0개, 선형 렌더 바이트 동일) + ADR-0009. *(v2.3, phases 24–25)*
- ✓ **Brownfield Adoption (v2.3 B, ADOPT-01..07)** — read-only 결정론적 inventory → evidence 분류(observed/inferred/unknown) plan → destination/disposition manifest → refuse-by-default apply를 `.workflow/tasks/` 작업으로(v2.2 CAS/evidence/HANDOFF 재사용, 새 권위 평면 없음) + `(draft_hash, task_revision, git_ref)` 결합 promotion(입력 변경 시 승인 무효) + 구조적 헌법-쓰기 거부 + `/adopt`·`brownfield-adoption` + 3개 도메인 중립 fixture 트리(하나는 CRLF/BOM dirty). *(v2.3, phases 26–27.2)*
- ✓ **Living Docs (v2.3 C, DOCSUP-01..07)** — `docs/doc-dependencies.toml` registry + committed review ledger(binding id·정확한 digest·disposition만 — 시간·사람·prose·모델 id 없음) + FRESH/BROKEN/STALE_REQUIRED/STALE_ADVISORY/UNCOVERED 게이트 + uncovered 비-회귀 + 파생 staleness 큐·조건부 SessionStart pointer + `/docs-update` drive loop(accepted ADR·`docs/reference/**`·`.memory/derived/**`·contracts·golden 구조적 제외) + ADR-0010. 사람이 세션 밖에서 최초 ledger를 authored(`c32c08d`)하고 ADR-0010을 ratify(`ad4e339`)한 뒤 `docs_guard` exit 1 → 0, 8/8 FRESH. *(v2.3, phases 28–29)*

### Active

<!-- v1.0 하네스 표면 (shipped in phases 1–8) -->

- [ ] **opencode 하네스 표면**: agents(orchestrator·dotnet·python·reviewer·golden-runner·polyglot-auditor·explorer), commands(/golden·/golden-approve·/contract-check·/new-normalization-rule·/adr·/strangler-step·/docs-sync·/component·/checkpoint), skills(dotnet·python·pipeline-patterns·data-contracts·golden-testing·normalization-catalog·skill-creator), plugins(contract-guard·session-start 주입기·format-on-write·polyglot-boundary 린터)
- [ ] **opencode.json**: 모델·15키 권한 매트릭스(bash glob last-wins)·instructions glob·MCP·formatter
- [ ] **단일소스 다중 런타임 산출**: 하네스 소스에서 opencode(1차)와 Claude Code(.claude/) 아티팩트를 생성 (각 런타임 제약 존중)
- [ ] **문서 아키텍처**: Diátaxis(tutorials/how-to/reference/explanation) + adr/(불변 MADR) + glossary + 루트/컴포넌트별 AGENTS.md, reference/는 계약에서 생성(에이전트 유지)
- [ ] **two-plane 컨텍스트 메모리**: 헌법 평면(contracts·adr·glossary·golden — 사람 소유·게이트) + 파생/휘발 평면(.memory/ activeContext·progress + repo-map·contracts-index 파생) + SessionStart 훅 무시불가 주입
- [ ] **폴리글랏 안전망**: 골든 동등성 비교기(정규화 비교)·contract-drift CI 게이트(스키마 해시)·CODEOWNERS+/golden-approve 사람 승인
- [ ] **범용화(신규, ADR-0002)**: 도메인·언어 특화 콘텐츠를 `examples/log-parser/`로 격리하고, 코어를 도메인·언어 중립으로. 언어는 프로젝트 설정 슬롯에서 파생. 코어→예시 무의존(단방향). 새 프로젝트가 scaffold할 수 있는 최소 generic 기본 인스턴스 제공.
- [ ] **레퍼런스 예시 인스턴스**: parserimprove monorepo_skeleton의 contracts(TSV 스펙·정규화·기준정보·state)·정규화 코어·toy-converter를 `examples/log-parser/`의 worked example로 보존(삭제 아님) — "이렇게 슬롯을 채운다"의 살아있는 예시.
- [ ] **툴체인 부트스트랩(설정형)**: 언어별 SDK 설치·워크스페이스·CI 매트릭스를 프로젝트 설정에서 파생. 예시 인스턴스는 .NET 10 SDK + uv 워크스페이스로 채움.

### Out of Scope

- **컴포넌트 구현 코드(파서·컨버터·스케줄러·수집기 로직)** — 이 프로젝트는 하네스이지 파이프라인 구현이 아니다. 실제 값·알고리즘은 사내에서 채운다.
- **표준 로그 TSV 스펙의 컬럼 확정값·DB 스키마 확정값** — 도메인 정본 미정(parserimprove 10장), 계약은 골격·placeholder로 시드.
- **B 모델(gRPC/메시지 큐) 운영 구현** — 하네스는 A 모델(CLI spawn) 계약을 우선 인코딩, B는 커맨드/스킬 확장 지점으로만.
- **Configuration 파서 관련 하네스** — parserimprove상 차후 컴포넌트.
- **발표 시스템(presentationformat)** — 참조 도메인 소스일 뿐 산출물 아님.

## Context

- **도메인 정본**: `/workspace/presentationformat/archive/parserimprove/uploads/` — `parser_project_revised.md`(전체), `integration_contracts_design.md`(통합 계약·폴리글랏 §4~5 체크리스트), `scheduler_design.md`, `file_collector_design.md`, `converter_design.md`, `standard_parser_design.md`, `monorepo_skeleton/`(문서 00~04+GLOSSARY, 계약 골격).
- **도메인 요지**: 설비 실시간 TSV 로그 → 수집 → (비표준은)컨버터 표준화 → 표준 파서(값 정규화·보정·start/end 병합·carryover) → 공정 DB. 폴리글랏 버그는 기능이 아니라 표현차(인코딩·LF·TSV 이스케이프·타임존·소수점·null)에서 난다. 골든 동등성이 언어 무관 안전망. live/rework/따라잡기 시나리오는 '가공'의 축이며 '수집'과 분리. 상태는 DB SSOT.
- **개발 환경**: Claude Code + GSD(get-shit-done-cc v1.42.3, 로컬+글로벌 설치됨). GSD가 개발 워크플로(spec→plan→execute→verify)를 구동. 산출 하네스의 컨텍스트 메모리는 GSD `.planning/`과 **독립**된 two-plane 설계.
- **툴체인 현황(이 환경)**: Python 3.11 + uv 0.8.17 ✅, Docker 29.3 ✅, **.NET 10 SDK 미설치**(설치 스크립트 필요), 원격 ephemeral 컨테이너(커밋·푸시로만 영속).
- **리서치 종합(3 에이전트)**: ① 하네스 4계층 분리(rules/agents/commands/skills) + per-package AGENTS.md 지연로딩 + 모델 티어링 + bash glob 권한 매트릭스 + 훅 가드레일. ② 컨텍스트 메모리는 "직접 만드는 것(intent/결정)"과 "파생되는 것(state)" 분리 — 파생물 자동 재생성, 휘발 state는 훅으로 무시불가 주입, 결정은 불변(ADR). ③ contracts=헌법, golden=안전망, Diátaxis reference만 에이전트 생성, `/golden`·`/contract-check`·`/strangler-step` 커맨드로 리팩토링을 계약우선·패리티게이트로 인코딩.

## Constraints

- **Runtime**: opencode 1차 타깃, 단일 소스에서 Claude Code 아티팩트도 생성(개발=Claude, 배포=opencode). 각 런타임 제약(예: 스킬 크기 상한) 존중.
- **Polyglot (설정형)**: 하네스는 폴리글랏을 지원하되 **특정 언어를 하드코딩하지 않는다**. 참여 언어·툴체인은 프로젝트 설정(예: `harness/project.toml` 또는 동등물)의 슬롯이며, 에이전트 페르소나·권한 매트릭스·CI 매트릭스가 그 설정에서 파생된다. 언어 경계는 프로세스/파일/DB로만 — 객체 직접 전달 금지 (이 불변식은 언어 무관하게 유지). 레퍼런스 예시(`examples/log-parser/`)는 .NET 10 + Python(uv)로 그 슬롯을 채운다.
- **Contract-first**: contracts/가 코드보다 우선. 코드가 계약과 다르면 코드가 틀린 것. 계약 변경은 골든/contract-drift 게이트를 동반. **계약의 도메인 내용은 슬롯** — 하네스는 계약을 강제하는 기계이지 특정 계약 자체가 아니다.
- **Memory**: two-plane. 파생물(repo-map·contracts-index·docs/reference)은 손으로 관리 금지(자동 생성). 결정은 append-only ADR.
- **Genericity(신규)**: durable 코어(`tools/`, `harness/`, 게이트, 메모리, 문서구조)는 도메인·언어 중립. 도메인·언어 특화 콘텐츠는 `examples/<instance>/` 아래로 격리. 코어가 특정 예시를 import/의존하면 안 됨(예시→코어 단방향 의존).
- **Env**: 원격 ephemeral — 하네스는 SessionStart 훅으로 툴체인/상태를 자기부트스트랩. 브랜치 `claude/data-pipeline-harness-8aypct`.
- **모델 아이덴티티**: 커밋·PR·코드 코멘트 등 레포 산출물에 모델 식별자 미포함.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 산출물 = 하네스, 컴포넌트 코드 아님 | 사용자 명시: 스킬·커맨드·에이전트·문서·메모리 층을 만드는 것 | — Pending |
| opencode 우선 + 단일소스 Claude 생성 | 개발은 Claude Code(GSD), 배포는 opencode; wshobson 단일소스 다중산출 패턴 | — Pending |
| 독립 two-plane 컨텍스트 메모리 | 파생/휘발 분리로 rot 방지, GSD 비의존해 opencode 네이티브 유지 | — Pending |
| parserimprove 계약·문서 실제 시드(예시 명시) | 구체 예시가 하네스 검증에 유용, generic보다 실효 | — Pending |
| 맞춤 직접 구성(gsd-opencode 포트 미채택) | 도메인 맞춤·최소·정확; 750파일 범용 대비 | — Pending |
| A 모델(CLI spawn) 우선 인코딩, B는 확장점 | integration_contracts §④; MVP 견고성, A→B 페이로드 동형 유지 | — Pending |
| **[ADR-0002] 범용 템플릿으로 재정의, 로그파서는 examples/로 강등** | 실제 구현 방향이 크게 바뀜 — 도메인 고정 하네스는 부채. durable 아키텍처(Phase 1–4)는 재사용 가치가 있으므로 도메인·언어 슬롯화 | ✅ Accepted 2026-07-08 |
| **[ADR-0002] 언어를 하드코딩 대신 설정 슬롯화(.NET+Python은 예시 인스턴스)** | 폴리글랏 기계는 가치, 특정 두 언어 고정은 아님 | ✅ Accepted 2026-07-08 |
| **[ADR-0002] 도메인 이동은 새 Phase 5로, ADR+해시 재베이스라인 동반** | contracts/는 헌법 평면 — 라이브 drift/contract-guard 게이트가 방어, 의도된 헌법 변경으로 처리 | ✅ Accepted 2026-07-08 |
| **[ADR-0009] 관계 그래프는 record 모델 + 추가형 lowering (마이그레이션 아님)** | 기존 선형 `[pipeline]` config를 바이트 불변으로 두면서 일반 그래프를 얻는 유일한 방법. identical-or-fail 마이그레이션은 세 개의 살아있는 config를 전부 흔든다 | ✅ Accepted 2026-07-19 |
| **[ADR-0009] conductor는 새 command·persona 없이 기존 3개 표면을 일반화** | 두 번째 orchestrator/router는 하네스가 명시적으로 금지하는 것. 선형 렌더를 하드코딩 리터럴 회귀 테스트로 바이트 고정해 일반화 비용을 0으로 증명 | ✅ Accepted 2026-07-19 |
| **[v2.3 B] adoption은 `.workflow/tasks/` 위의 평범한 작업, sibling 권위 평면 아님** | v2.2 CAS·evidence·HANDOFF를 재사용하면 새 상태 기계가 필요 없다. `.workflow/adoption/` 평면은 두 번째 진실 원천이 되었을 것 | ✅ Accepted 2026-07-20 |
| **[ADR-0010] 사람-docs review 의무 모델 — 해시는 review 부채를 증명하지 prose 정확성을 증명하지 않는다** | semantic 문서 oracle이나 LLM-only freshness 게이트는 CI에서 모델을 돌려야 하고 검증 불가능한 green을 만든다. digest는 "사람이 이 (sources,target) 쌍을 봤다"만 기록 | ✅ Accepted 2026-07-22 |
| **[v2.3 C] ledger는 사람만 쓴다 — agent 우회 경로를 약화하지 않고 layer 1을 실제로 구현** | self-blessed row와 정직한 seed row는 바이트 동일하다. 오직 사람의 커밋만 둘을 가른다. `ledger_guard`는 `GOLDEN_APPROVE_HUMAN`도 `HARNESS_DEV_BYPASS`도 인정하지 않는다 | ✅ Accepted 2026-07-22 |
| **[v2.3 closeout] 헌법 평면 drift는 enforcement를 고치지 ADR을 고치지 않는다** | ADR-0001은 4-member 평면을 선언했고 Phase-4 스택은 3개만 강제했다. 내부 감사 두 건이 `proposed` ADR-0010을 `accepted` ADR-0001보다 우선해 인용하며 정반대 수리를 권고했고, 외부 감사가 그 역전을 잡았다 | ✅ Accepted 2026-07-22 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-26 — milestone **v2.5 De-ceremony** (phases 39-46) started via `/gsd:new-milestone`. Design ratified by a three-round two-model panel (`gpt-5.6-sol` high x `claude-opus-5` high, factual dossier by `gpt-5.6-terra` medium) over a Claude-authored brief: `.planning/research/v2.5-scoping-FINAL.md`; research skipped (design complete). v2.4 closed PARTIAL — 34-37 shipped, 30 partial, 31/32/33 cut, 38 landed as code (`bc9a6d9`) and formalized by v2.5 phase 39. Phase directories for 30/34-37 deliberately NOT cleared (they hold the drafts and verification records phase 39 discharges).*

<details>
<summary>Previous footer — v2.3 close (2026-07-22)</summary>

*Last updated: 2026-07-22 after the v2.3 milestone. Shipped 10 phases / 43 plans / 58 tasks over 3 days and 310 commits; 21/21 requirements validated; 16/16 fan-in gates exit 0. Closed with 8 acknowledged deferred items (see `STATE.md`), of which the load-bearing three are RAT-4, RAT-5, and the per-tool spelling of the constitution-plane write-denies. No milestone is in progress — next step is `/gsd:new-milestone`.*

</details>

<details>
<summary>Previous footer — v2.3 start (2026-07-19)</summary>

*2026-07-19 — milestone v2.3 (Contract Graph, Brownfield Adoption, Living Docs) started via `/gsd:new-milestone`. Design scoped by a sol-vs-fable debate panel (independent proposals → cross-rebuttal → codex sol merged FINAL), human-approved (`.planning/research/v2.3-scoping-FINAL.md`); all 3 themes in one milestone, 21 requirements (TOPO/ADOPT/DOCSUP), phases 24–29. Requirements + roadmap derived directly from the approved design; research skipped (design complete). Prior milestone v2.2 (Adaptive Task Control Plane, phases 18–23) shipped + pushed (recorded in MILESTONES.md this session; formal `/gsd:complete-milestone` archive of phase dirs deferred — new numbering 24+ avoids collision).*

</details>
