# Requirements: v2.3 Contract Graph, Brownfield Adoption, Living Docs

**Defined:** 2026-07-19
**Core Value:** 계약(contracts)을 단일 정본으로 두고, 폴리글랏 표현차·레거시 전환 리스크를 하네스가 자동으로 강제·검증한다 — "어떻게 개발·유지보수·리팩토링하는가"가 실행 가능한 스킬·커맨드·훅으로 박혀 있다.

> Source: `.planning/research/v2.3-scoping-FINAL.md` (sol-vs-fable debate panel: independent proposals → cross-rebuttal → codex sol merged FINAL, human-approved). Requirements derive directly from the approved design — not re-scoped.
> **Machinery marker:** REUSE = composes shipped machinery unchanged · NEW = missing machinery · NEW+REUSE = narrow new mechanism around named shipped primitives.

## v2.3 Requirements

### Theme A — General Contract-Relationship Topology (Phases 24–25)

- [ ] **TOPO-01** *(NEW+REUSE, Phase 24)*: `contracts/harness/topology/` 아래 사람 승인 Draft 2020-12 스키마가 각 관계를 stable id + tracked contract reference + 정확히 하나의 authority endpoint + 1개 이상 dependent endpoint + 선택적 explanatory kind/labels로 정의하고, positive/negative fixture가 기존 contract-hash/drift ratification 경로를 통과한다.
- [ ] **TOPO-02** *(NEW+REUSE, Phase 24)*: project·workspace TOML이 추가형 `[[contract_graph.relationships]]` record를 받아들이되 기존 loader API와 레거시 설정은 불변이고, 새 accessor는 검증·traversal·discovery·도메인 정책 없이 raw data만 반환한다.
- [ ] **TOPO-03** *(NEW+REUSE, Phase 24)*: 하나의 결정론적 `effective_relationships()` 경로가 모든 레거시 `[pipeline].edges`를 authority/dependent 관계로 lowering 후 explicit record와 union하며, 중복 id·중복 semantic edge·모순 시 fail하고, 현재 선형 fixture는 byte-unchanged로 유지된다.
- [ ] **TOPO-04** *(NEW+REUSE, Phase 25)*: 도메인 중립 컴파일러와 `harness_lint` 게이트가 안정 정렬·repo-confined 그래프 데이터와 안정 진단 코드를 내고, endpoint·authority-owned contract 해소를 검증하며, fan-in/fan-out/disconnected component/canonical cycle을 허용한다.
- [ ] **TOPO-05** *(NEW+REUSE, Phase 25)*: direct·reverse·transitive 관계-impact 질의가 cycle에서 종료하고 결정론적 정렬된 id·path만 반환하며(conductor routing·문서 리포트용), 새 task-evidence 요구를 만들거나 contract body를 preload하지 않는다.
- [ ] **TOPO-06** *(NEW+REUSE, Phase 25)*: 기존 orchestrator·`/pipeline`·`pipeline-map` skill이 canonical 그래프를 소비하고, locked 선형 렌더링을 보존하며, branch/cycle을 안전 렌더하고, `harness/`에서 두 런타임으로 byte-identical 왕복하며 새 graph command·persona를 만들지 않는다.
- [ ] **TOPO-07** *(NEW+REUSE, Phase 25)*: generic project/workspace fixture가 shared-contract fan-out·request와 response를 별도 record로·event fan-out·legal cycle·cross-repo authority 해소를 증명하고, log-parser instance는 불변, GEN-04 twin green, 사람 승인 ADR이 모델을 기록한다.

### Theme B — Brownfield Adoption (Phases 26–27)

- [ ] **ADOPT-01** *(NEW+REUSE, Phase 26)*: read-only local-root inventory가 언어·package/component 경계·기존 schema/spec/doc/ADR/AGENTS/CODEOWNERS/CI 표면·candidate process 경계를 confined·ignore-준수·size-cap된 evidence pointer·hash로 결정론적으로 보고하고, secret·binary·vendor·generated·source dump은 제외한다.
- [ ] **ADOPT-02** *(NEW+REUSE, Phase 26)*: 제안된 모든 member·component·relationship·contract candidate·test command·문서 destination·AGENTS 경계가 source evidence와 함께 observed/inferred/unknown으로 분류되고, 미해결 ownership은 invented authority가 아니라 question으로 남는다.
- [ ] **ADOPT-03** *(NEW+REUSE, Phase 26)*: adoption plan이 contracts·golden·ADR·Diátaxis 4분면·두 memory 평면·task/config/workspace topology·root/nested AGENTS·CODEOWNERS 가이드·runtime-neutral source·emitted runtime에 정확히 하나의 `create`/`marker-merge`/`preserve`/`conflict`/`derived-regenerate`/`human-ratification-required` disposition을 부여한다.
- [ ] **ADOPT-04** *(NEW+REUSE, Phase 27)*: 각 adoption batch가 `.workflow/tasks/<task-id>/artifacts/adoption/<batch-id>/`에 존재하며 inventory·plan·draft tree·question·conflict·source ref·task revision·artifact hash·approval을 기존 CAS·evidence·HANDOFF·resume lifecycle에 결합한다.
- [ ] **ADOPT-05** *(NEW+REUSE, Phase 27)*: discovery/draft 모드는 task artifact root 안에서만 쓰고, apply 모드는 review된 비-헌법 파일을 atomically create·marker-merge하되 silent overwrite·동시 target drift를 거부하고 `contracts/`·`docs/adr/`·`golden/` destination을 mutation 전에 거부한다.
- [ ] **ADOPT-06** *(NEW+REUSE, Phase 27)*: promotion이 제안된 contract·golden·ADR·relationship authority·conflict·unknown을 다루는 사람 결정을 요구하며, 정확한 draft hash·task revision·git ref에 결합되어 입력 변경 시 승인이 무효화된다.
- [ ] **ADOPT-07** *(NEW+REUSE, Phase 27)*: 하나의 얇은 `/adopt` command와 `brownfield-adoption` skill이 결정론적 툴·기존 explorer/fan-out/orchestrator/task 게이트·promotion 워크플로·runbook을 조합하고, 3개 generic fixture(polyglot 단일 레포·2-레포 client/server·partial-adoption/collision)가 idempotence·임의 command 미실행·헌법 거부·emitter closure·GEN-04를 증명하며 최소 하나의 fixture는 CRLF·BOM 입력을 포함한다.

### Theme C — Human-Authored Documentation Upkeep (Phases 28–29)

- [ ] **DOCSUP-01** *(NEW+REUSE, Phase 28)*: review된 `docs/doc-dependencies.toml`이 stable source selector를 사람 작성 target 문서·disposition 정책·`required`/`advisory` 심각도에 결합하고, path escape·중복 id·빈 required selector·derived/reference target·accepted-ADR 편집 정책을 거부한다.
- [ ] **DOCSUP-02** *(NEW+REUSE, Phase 28)*: 결정론적 guard가 정렬된 source·target path/byte 세트를 해시하고, committed ledger가 binding id·정확한 review된 digest·`updated`/`reviewed-no-change` disposition만 저장한다(시간·사람·prose copy·모델 식별자 없음).
- [ ] **DOCSUP-03** *(NEW+REUSE, Phase 28)*: guard가 binding을 `FRESH`/`BROKEN`/`STALE_REQUIRED`/`STALE_ADVISORY`/`UNCOVERED`로 분류하고, `BROKEN`·`STALE_REQUIRED`를 fail·`STALE_ADVISORY`를 warn·uncovered-count 비-회귀를 강제하며, 매칭 disposition 없는 ledger-only digest bump을 거부한다.
- [ ] **DOCSUP-04** *(NEW+REUSE, Phase 28)*: 기존 memory-regeneration 기계가 pointer-only `.memory/derived/docs-staleness.md` 큐를 결정론적으로 렌더하고 최대 한 줄의 조건부 SessionStart pointer를 추가하되, derived-never-hand-edited·byte-identical `assemble()`·기존 ~4,000자 예산을 보존한다.
- [ ] **DOCSUP-05** *(NEW+REUSE, Phase 28)*: 안정 리포트가 변경된 path/hash·그래프 impact id·target doc·심각도·요구 disposition을 그룹핑하고, accepted ADR은 `REVIEWED_STILL_CURRENT`/`SUPERSEDING_ADR_REQUIRED`만 내며, contract/golden 실패는 선행·authoritative로 유지되고, old-to-new diff는 git에서 회수 가능할 때만 표시한다.
- [ ] **DOCSUP-06** *(NEW+REUSE, Phase 29)*: 하나의 얇은 `/docs-update` command와 `docs-upkeep` skill이 결정론적 큐를 읽어 bounded 사람-doc 편집 또는 정확한 review disposition을 draft하고 기존 review/verify 흐름으로 라우팅하며, accepted ADR·`docs/reference/**`·`.memory/derived/**`·contracts·golden을 구조적으로 제외하고 두 런타임에 왕복한다.
- [ ] **DOCSUP-07** *(NEW+REUSE, Phase 29)*: 정상 사람-review 변경이 최고 위험 기존 문서와 adoption runbook의 binding을 seed하며, `/adopt`은 registry/ledger 항목을 제안할 수 있으나 inferred ownership은 미해결로 남기고 명시적 review 없이는 green이 될 수 없다.

## Future Requirements

Deferred to a later milestone:

- **TCP-F01..F05** (v2.2 carry): clarify/TDD/diagnose/domain-modeling discipline 스킬을 task lifecycle에 연결 · STRICT+ adversarial 다중 전문가 review 패널 · 전문 agent allowlist + capability-neutral 라우팅 · skill registry.lock + adapter CI · log-parser instance risk overlay.
- **Impact-driven task-evidence policy** — topology affected-set이 v2.2 레인의 필수 evidence를 바꾸도록 하는 것. 별도 ratified control-plane 결정(ADR) 필요.
- **Contract versioning/compatibility engine** — semver range·migration graph·compat matrix. 구별된 tracked version path는 v2.3에서 표현 가능하나 호환 엔진은 연기.
- **Signed external evidence attestation** (P21 D-10) · **STRICT-rollback policy** (별도 breaking ADR 필요).

## Out of Scope

| Feature | Reason |
|---------|--------|
| Contract 호환/버전 엔진 (semver range·migration graph·Pact·Buf·broker·schema registry) | 구별된 version은 별도 tracked contract path로 표현; 호환 엔진은 기존 hash/drift/golden 안전망을 중복·초과. |
| Impact-driven task-evidence 정책 | v2.3은 결정론적 affected-set hint만 제공·기존 per-member 게이트 재사용; 레인 필수 evidence 변경은 별도 ratified 결정. |
| Topology runtime (service discovery·message bus·network crawler·remote clone·daemon·distributed transaction) | 그래프는 순수 데이터 + 정적 분석; 런타임 아님. |
| 두 번째 orchestrator·router·graph command·전문 persona | `/pipeline`·`pipeline-map`·기존 orchestrator·explorer·fan-out 재사용; GSD dev-side 유지·라우터는 순수 함수. |
| 새 adoption authority·staging 평면 (`.workflow/adoption/`) | adoption은 `.workflow/tasks/<task-id>/` 아래 산출물의 일반 작업. |
| Autonomous contract 추출·brownfield 마이그레이션 | `/adopt`은 candidate·scaffold를 draft; authority 선언·behavior→golden 추론·source refactor·repo 이동·CI 재작성·discovered script 실행·remote member 미지원. |
| 헌법 self-ratification | 에이전트는 contract·accepted ADR·golden을 promote 불가; CODEOWNERS·게이트·명시적 사람 checkpoint authoritative. |
| Derived-plane 재구현 | `/docs-sync`·curator·`/refresh-memory`·stale-derived가 reference/derived 재생성 독점 유지; 새 큐는 기존 memory 기계로 생성·hand-edit 금지. |
| Semantic 문서 oracle·auto-commit | 해시는 review 부채를 증명(prose 정확성 아님); CI에서 모델 미실행·LLM-only freshness 게이트 없음. |
| Accepted-ADR 편집 | drift는 `REVIEWED_STILL_CURRENT` 또는 superseding ADR draft만; accepted 결정은 append-only. |
| 광범위 fixture·프레임워크 stack | adoption fixture 3종 + focused topology/docs fixture로 충분; 통합 exit는 게이트 조합. |
| TCP-F01..F05·signed external evidence·STRICT rollback | Themes A/B/C를 전달하지 않고 settled task-control 표면을 재개방. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TOPO-01 | Phase 24 | Pending |
| TOPO-02 | Phase 24 | Pending |
| TOPO-03 | Phase 24 | Pending |
| TOPO-04 | Phase 25 | Pending |
| TOPO-05 | Phase 25 | Pending |
| TOPO-06 | Phase 25 | Pending |
| TOPO-07 | Phase 25 | Pending |
| ADOPT-01 | Phase 26 | Pending |
| ADOPT-02 | Phase 26 | Pending |
| ADOPT-03 | Phase 26 | Pending |
| ADOPT-04 | Phase 27 | Pending |
| ADOPT-05 | Phase 27 | Pending |
| ADOPT-06 | Phase 27 | Pending |
| ADOPT-07 | Phase 27 | Pending |
| DOCSUP-01 | Phase 28 | Pending |
| DOCSUP-02 | Phase 28 | Pending |
| DOCSUP-03 | Phase 28 | Pending |
| DOCSUP-04 | Phase 28 | Pending |
| DOCSUP-05 | Phase 28 | Pending |
| DOCSUP-06 | Phase 29 | Pending |
| DOCSUP-07 | Phase 29 | Pending |
