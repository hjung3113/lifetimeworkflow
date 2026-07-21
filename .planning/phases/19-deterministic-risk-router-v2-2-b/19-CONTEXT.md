# Phase 19: Deterministic Risk Router - Context

**Gathered:** 2026-07-18
**Status:** Ready for planning

<domain>
## Phase Boundary

작업 규모가 아니라 위험·맥락 압력에 비례해 절차를 강화하되, **레인 판정과 필수 산출물을 전부 재현 가능한 순수 함수**로 계산한다. 산출: `harness/risk-policy.toml`(runtime-neutral 정책 데이터), `tools/risk_router/`(7축 점수→레인 순수 함수 + CLI), 자동 승격 reason code, 레인별 필수 산출물 matrix, escalate-only instance overlay 슬롯, `/intake` 커맨드(harness/ 소스). **요구사항 TCP-03, TCP-04, TCP-05, TCP-06.** 상태 도구·전이 게이트는 Phase 20, evidence는 21 — 범위 밖.
</domain>

<decisions>
## Implementation Decisions

> `--auto` 단일 패스. 정본: `docs/explanation/next-milestone-task-control-plane.md` §Phase 2. Phase 18 계약(task packet의 lane·risk-input 필드)을 소비.

### 라우터 성질
- **D-01:** 점수 계산은 LLM 판단문이 아니라 구조화 입력에 대한 **결정론적 순수 함수**. 레포 미접근. 동일 입력+policy hash → byte-identical decision JSON.
- **D-02:** 7축 각 0..3: ambiguity, change scope, data/security, reversibility, user/operations impact, coordination, context pressure. 기본 cut: 0-4 FAST / 5-9 STANDARD / 10-14 STRICT / 15-21 CONTROLLED.
- **D-03:** 사실 입력(repo probe로 채울 수 있는 것)과 사용자 결정 입력을 구분 — 라우터 자체는 계산만. probe는 `/intake` 커맨드 프롬프트 책임(에이전트가 채워 넣음), 라우터는 순수.

### 자동 승격 (TCP-04)
- **D-04:** reason code = auth/authorization, payment, secret/PII, destructive data change, unclear rollback, external contract break, **constitution-plane touch**(contracts·docs/adr·golden), repeated constraint violation. 각각 최소 레인 강제(예: 헌법 접촉 → 최소 STRICT, golden/계약 변경·prod destructive → CONTROLLED).
- **D-05:** 자동 승격은 점수 레인을 **항상 이긴다**. human override는 레인을 **낮출 수 없고** 올리거나 예외를 audit reason으로 기록만.

### Overlay (TCP-05)
- **D-06:** instance risk overlay는 선언적 데이터(`harness/project.toml` 슬롯 방식) + schema 검증 + provenance. **escalate-only**: 최소 lane 상향·새 promotion predicate·추가 required gate만. cut 하향·core gate 제거·required artifact 삭제 불가(property test로 강제). core는 instance/example 경로 미참조(GEN-04 유지).
- **D-07:** 이번 phase는 overlay **메커니즘만** 출하. 특정 example(log-parser) overlay 작성은 비목표(TCP-F05).

### 필수 산출물 matrix + /intake (TCP-06)
- **D-08:** 레인별 required artifact/gate matrix를 policy 데이터로 선언(설계 §6 표). FAST = packet 1개 + lint/test만; 추가 ceremony 자동 요구 금지(FAST 역류 방지 — Phase 23 fixture가 상한 고정).
- **D-09:** `/intake`는 harness/commands 소스 → 두 런타임 emit. 에이전트가 7축 점수화 → 라우터 호출 → Phase 18 task packet 생성. 기존 orchestrator topology/context-budget intake와 연결(대체 아님).

### 헌법 정합
- **D-10:** `risk-policy.toml`(선언적 정책)과 overlay 슬롯은 사람 편집 대상. 라우터 결과·policy hash에 **실제 모델 ID 없음** — 승격은 capability-neutral(`human review required`, `fresh session required`)로 표현. `/intake` emit은 emit-drift 0.

### 실행 위임 (교대 루프)
- **D-11:** 구현 **codex sol 주도**. 리뷰어 **교대** — Phase 18은 fable가 리뷰했으니 Phase 19 리뷰는 **sol 독립 인스턴스(fresh context)** 우선, blocker 잔여 시 fable 교차확인. Claude 오케스트레이트/검증/머지. 참조 [[design-and-gsd-via-codex-sol]].
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 설계 정본
- `docs/explanation/next-milestone-task-control-plane.md` §Phase 2(Deterministic Risk Router) + §6(위험도 기반 강제 정책 표: 7축·cut·자동승격·레인별 필수 산출물) — 산출물·정책 원칙·완료기준 정본.
- `.planning/REQUIREMENTS.md` TCP-03..06 + Out of Scope(LLM lane 결정 금지, 모델 ID 금지, overlay 완화 금지).
- `.planning/ROADMAP.md` "Phase 19" success criteria 5개.

### Phase 18 (소비 대상)
- `contracts/harness/task-control/task.schema.json` — lane·risk-input 필드(라우터 출력이 packet에 기록됨).
- `contracts/harness/task-control/transitions.json` — 레인별 허용 전이(matrix와 정합 유지).
- `tools/task_packet/` — packet 생성/검증 API(라우터 결과 소비).

### 헌법·관례
- `AGENTS.md`(root), `harness/project.toml`(instance 슬롯 방식 — overlay 슬롯 참고), `docs/adr/ADR-0002`(core→example 무의존/GEN-04).
- `tools/harness_emit/` — `/intake` 두 런타임 emit 경로. `tools/harness_config` — topology/config 로드 패턴.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `harness/project.toml` + `tools/harness_config`: instance 데이터 슬롯 + 로드 패턴 — overlay 슬롯을 같은 방식으로.
- `tools/harness_emit/`: `/intake` 커맨드를 harness/ 소스에서 두 런타임으로 emit. emit-drift 게이트 재사용.
- `tools/task_packet/`(Phase 18): 라우터 decision을 packet에 기록.

### Established Patterns
- runtime-neutral 계산·저장 엔진은 `tools/`, runtime 커맨드는 harness/ 소스에서 엔진 호출(설계 §7 정합).
- 순수 함수 + 결정론(byte-identical) — Phase 18 검증기와 동일 규율(정렬·해시).
- GEN-04: core가 example 미참조. overlay는 core 소비 방향(단방향).

### Integration Points
- orchestrator intake/context-budget(기존 topology 라우팅)와 `/intake` 연결 — 대체 아님, 보강.
- Phase 20 상태도구가 레인별 필수 산출물 matrix를 소비(전이 게이트) — 이번엔 matrix 데이터만 확정.
</code_context>

<specifics>
## Specific Ideas

- 완료기준은 설계 §Phase 2 완료기준 1~10을 acceptance criteria로 승격 — 특히: cut 경계 fixture(0-4/5-9/10-14/15-21), 자동 승격이 점수 이김, overlay가 lane/gate 낮추려 하면 validation 실패, effective≥core, FAST fixture ceremony 없음, CONTROLLED fixture 전부 요구, 모델 ID 없음.
</specifics>

<deferred>
## Deferred Ideas

- Atomic state manager·phase-gate(20), evidence(21), handoff·injector(22), lifecycle fixture·ADR(23).
- log-parser overlay 작성(TCP-F05) — 후속 마일스톤.
- capability-neutral 모델 라우팅 실연동(TCP-F03) — 후속.
</deferred>
