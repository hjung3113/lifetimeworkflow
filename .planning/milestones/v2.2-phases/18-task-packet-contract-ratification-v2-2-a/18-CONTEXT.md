# Phase 18: Task Packet Contract Ratification - Context

**Gathered:** 2026-07-18
**Status:** Ready for planning

<domain>
## Phase Boundary

작업 상태·증거·인계의 shape와 소유권을 **코드보다 먼저** 사람 승인 계약으로 고정한다. 산출: `task`/`state`/`evidence`/`handoff` JSON Schema(Draft 2020-12) 4종 + `.workflow/tasks/<id>/` 인스턴스 슬롯 + phase/lane enum + 허용 전이표 + contract-drift 베이스라인 + paired golden. **요구사항 TCP-01, TCP-02.** 라우터·상태도구·evidence 수집기 등 소비 코드는 이 phase 범위 밖(19–21).
</domain>

<decisions>
## Implementation Decisions

> `--auto` 단일 패스. 설계가 이미 `docs/explanation/next-milestone-task-control-plane.md`(codex sol, 사람 승인)에 잠겨 있어 대부분 pre-answered. 아래는 그 문서의 Phase 1 절 + 사람 결정 A/B에서 파생.

### 저장 위치 & 평면 (사람 결정 A — locked)
- **D-01:** task 인스턴스는 `.workflow/tasks/<task-id>/`에 둔다 (fable의 `.memory/tasks/` 기각). 새 최상위 namespace — `.memory/`의 세션-memory 책임과 이름으로 분리.
- **D-02:** `.workflow/tasks/`는 **committed volatile**, derived 아님(자동 재생성 금지). `.memory/state/`에는 active task ID + HANDOFF 포인터만.
- **D-03:** `.memory/state/`↔`.workflow/tasks/` **상호 독립** — 한쪽 삭제가 다른 쪽 validation/regeneration을 바꾸지 않음(완료 기준으로 테스트).

### 계약 위치 & 게이트
- **D-04:** schema 4종은 헌법 평면 `contracts/harness/task-control/`에 둔다 → contract-drift 해시 베이스라인 등록, schema hash 이동 시 paired golden + 사람 승인 요구.
- **D-05:** 에이전트는 `contracts/`를 직접 쓰지 않는다(gate-model). 개발 세션에서 **dev 브랜치에 draft**하고 CODEOWNERS가 merge 시 ratify. dev 세션 게이트 마찰은 `HARNESS_DEV_BYPASS`(Phase 17, secure-default)로만 해소하되 byte-hygiene은 절대 미완화.

### 스키마 shape (설계 §Phase 1에서 확정)
- **D-06:** phase enum = `INTAKE, CLARIFY, SPEC, PLAN, EXECUTE, REVIEW, VERIFY, COMPLETE, BLOCKED`. (SHIP/LEARN은 현 template에 실 배포 대상 없음 → 연기.)
- **D-07:** lane enum = `FAST, STANDARD, STRICT, CONTROLLED`. 레인별 허용 전이 경로: FAST `INTAKE→EXECUTE→VERIFY→COMPLETE`; STANDARD +조건부 CLARIFY/간략 SPEC·PLAN/REVIEW; STRICT CLARIFY·승인SPEC·PLAN·REVIEW·VERIFY 필수; CONTROLLED STRICT+단계별 human gate.
- **D-08:** `task.json` 필드: goal, non-goals, risk inputs, lane, acceptance-criterion IDs, constraint IDs, decision refs(ADR 포인터만 — 자유서술 결정 필드 없음). `state.json`: phase, revision, baseline/current ref, completed items, next action, blockers. `evidence.json`: gate run index + criterion/finding trace. `handoff.json`: 재개 snapshot. artifacts는 immutable, packet엔 경로·요약·해시만.
- **D-09:** immutable task ID 포맷 = `T-<UTCyyyymmddHHMMSS>-<kebab-slug>`. baseline commit SHA는 생성 시 고정.
- **D-10:** ID 참조 규칙 — acceptance criterion / constraint / evidence / finding ID는 존재하는 대상만 참조(dangling 거부).

### Claude's Discretion (→ sol 위임)
- tools 측 검증기 구조·CLI 이름(`tools/task_packet/` 등), fixture 파일 배치, golden 케이스 형식은 **codex sol**이 계획·구현 시 레포 관례(`tools/` 기존 패턴, `contracts/` 기존 schema)에 맞춰 결정.

### 실행 위임 (사람 지시 — 이 phase부터 자율)
- **D-11:** 이 phase의 계획·구현은 **codex sol 주도**(Orca 워크트리), 리뷰는 **claude fable ↔ sol 교대**, 자율 진행. Claude(본 세션)는 오케스트레이트/검증(게이트 실행)/머지. 참조: 메모리 [[design-and-gsd-via-codex-sol]], [[execute-via-codex-orca]].
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 이 마일스톤 설계 정본
- `docs/explanation/next-milestone-task-control-plane.md` §1–§4, §7 — Phase 1(Task Packet Contract) 산출물·책임경계·결정론적 완료기준의 정본. 사람 결정 A(`.workflow/tasks/`)·B(6 phase) 반영본.
- `.planning/REQUIREMENTS.md` — TCP-01, TCP-02 정의 + Out of Scope(`.memory/tasks/` 기각, secret 미기록 등).
- `.planning/ROADMAP.md` §"Phase 18" — success criteria 4개(schema 등록·fixture pass/fail·deletion-independence·dangling reject).

### 헌법·플레인 규율
- `AGENTS.md`(root) + `docs/adr/` — 계약우선·two-plane·헌법 평면 게이트 규율.
- `docs/adr/ADR-0006*`(메모리 모델), `docs/adr/ADR-0007*`(HARNESS_DEV_BYPASS) — 저장 평면 + dev-bypass 근거.
- 기존 `contracts/` schema(예: `contracts/normalization/format-conventions.schema.json`) — Draft 2020-12 관례·contract-drift 등록 방식 참조.
- `tools/contract_drift/`, `tools/contract_hash/` — 신규 schema 4종 베이스라인 등록 경로.

### 참고(차용 아님)
- `docs/references/opencode-matt-workflows/` — PROGRESS는 스크립트로만·구조화 라우팅 패턴만 참조(flow-* 포팅 금지).
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/contract_hash/` + `tools/contract_drift/`: 신규 schema 4종을 그대로 해시·베이스라인 등록 — 재구현 불필요.
- `tools/memory_regen/contracts_index.py`: contracts-index 파생 재생성 — 신규 schema 자동 반영.
- 기존 `contracts/**/*.schema.json`: Draft 2020-12 shape·명명·검증(check-jsonschema) 관례의 살아있는 예시.

### Established Patterns
- 계약우선 순서(new-contract-rule 스킬): 계약 → data-based (input, expected) 케이스 → 실패 코드 스텁. Phase 18은 schema → fixture(pos/neg) → (다음 phase의) 소비 도구 스텁.
- 헌법 평면 write는 gate-model: 에이전트 draft, CODEOWNERS ratify.

### Integration Points
- `.workflow/tasks/` 신규 최상위 — `.gitignore`(committed이므로 ignore 아님), `tools/harness_lint`/GEN-04 스코프, SessionStart injector 스코프(19–22에서 배선)와 접점. Phase 18은 **디렉터리 규약·schema만** 확정, 배선은 후속.
</code_context>

<specifics>
## Specific Ideas

- 결정론적 완료 기준은 sol의 설계 §Phase 1 완료기준 1–9를 그대로 acceptance criteria로 승격.
- fixture: 유효 ≥5 / 필수 필드별 negative 각 1 / 미정의 phase·lane·transition 거부 / dangling ID 거부 / baseline 부재 거부 / deletion-independence.
</specifics>

<deferred>
## Deferred Ideas

- Risk router·overlay(Phase 19), atomic state manager·phase-gate(Phase 20), evidence 수집기(21), handoff·injector 배선(22), lifecycle fixture·ADR(23) — 각 후속 phase.
- log-parser instance용 risk overlay 작성(TCP-F05) — 후속 마일스톤.
</deferred>
