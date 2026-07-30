# Phase 22: Handoff + Fresh-Session Resume - Context

**Gathered:** 2026-07-19
**Status:** Ready for planning

<domain>
## Phase Boundary

대화 transcript 없이 **특정 state revision의 immutable snapshot**을 새 세션에 전달하고 **검증 전 재개 금지**를 강제한다. 산출: `tools/handoff/` generator/validator, `handoff.schema.json` 확장(decisions·changed_paths·evidence refs·unresolved·exact next action·stop condition·required read paths), `/handoff` 커맨드(harness 소스), 기존 `/checkpoint`·`/orient`·SessionStart injector 개정(pointer-only). **요구사항 TCP-14, TCP-15.** lifecycle fixture·ADR·CI는 Phase 23 — 범위 밖.
</domain>

<decisions>
## Implementation Decisions

> `--auto` 단일 패스. 정본: 설계 §Phase 5. Phase 18 handoff.schema.json + Phase 20 state/revision + Phase 21 evidence refs 소비·확장. 기존 checkpoint/orient/injector 재구현 금지 — 개정만.

### HANDOFF snapshot (TCP-14)
- **D-01:** HANDOFF는 **대화 요약이 아니라 특정 state revision의 immutable snapshot**. 필드: task ID, goal, non-goals, lane, current phase/revision, critical constraint refs, decisions, baseline/current commit, changed paths, evidence refs, unresolved items, **exact next action, stop condition, required read paths**. handoff.schema.json 확장 → dev draft + contract_hash 재해시 + drift 재기준.
- **D-02:** HANDOFF는 원본 계약·ADR·evidence·artifact를 **복제하지 않고 path/hash로 참조**. 참조하는 state/evidence/artifact hash를 검증. stale revision/ref/artifact를 가리키면 **실패(자동 보정 금지 — 재생성 요구)**.
- **D-03:** fresh-session checker가 **HANDOFF만으로 필수 필드 100% 복원**(task-id·goal·non-goals·critical constraints·phase·ref·next-action). Phase 21 처럼 committed(HEAD) 기준 무결성 활용 가능.

### 기존 명령 개정 (TCP-15) — 재구현 금지
- **D-04:** `/checkpoint` 개정: active task 있을 때 **valid HANDOFF를 먼저 생성**하고 session state엔 **task pointer만** 기록. 기존 bounded `.memory/state/` 정책 + 선택적 commit 의미 보존.
- **D-05:** `/orient` 개정: active HANDOFF를 **최우선 pointer**로 표시, resume 전에 **`/phase-gate`(Phase 20) 요구**. 새 세션은 HANDOFF 검증 전 EXECUTE/REVIEW/VERIFY 시작 금지.
- **D-06:** SessionStart injector(`tools/memory_regen/inject.py` → `session-inject.ts` emit) 개정: active task를 **pointer-only 주입**(task ID·phase·lane·revision·next action·HANDOFF 경로만). task 본문·로그·contract body 주입 금지. **기존 ~1k token cap + lazy-load 보존**(task 유무 양쪽 snapshot).

### 헌법 정합
- **D-07:** tools는 domain-neutral. HANDOFF는 `.workflow/tasks/` 인스턴스에 write, `.memory/state/`엔 active task ID + pointer만(task packet 복제 금지). `/checkpoint`·`/orient`·`/handoff` **두 runtime emit parity** + emit-drift 0. secret/PII는 HANDOFF에도 평문 미기록(Phase 21 D-06 재사용). 모델 식별자 없음. byte hygiene.

### 실행 위임
- **D-08:** 구현 **codex terra medium (fast off, headless)**. 리뷰 **교대 → sol**(P21=fable). 단 HANDOFF가 secret refusal 경로를 크게 건드리면 codex content-filter 위험 → fable로. Claude 검증/머지. 러너 `scratchpad/run_agent.sh`. 참조 [[design-and-gsd-via-codex-sol]].
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 설계 정본
- `docs/explanation/next-milestone-task-control-plane.md` §Phase 5(Handoff and Fresh-Session Resume) — 산출물·책임경계·완료기준 1~8 정본.
- `.planning/REQUIREMENTS.md` TCP-14,15 + Out of Scope(기존 checkpoint/injector 재구현 금지, token cap 보존).
- `.planning/ROADMAP.md` "Phase 22" success criteria 4개.

### 소비·확장 대상 (Phase 18/20/21)
- `contracts/harness/task-control/handoff.schema.json` — 현 필드(task_id/state_revision/goal/non_goals/critical_constraint_ids/phase/lane/baseline/current_ref/next_action/evidence_ids/finding_ids). **확장 지점**(decisions·changed_paths·unresolved·stop_condition·required_read_paths).
- `contracts/harness/task-control/{state,evidence}.schema.json` — revision·evidence ref 참조.
- `tools/task_control/`(P20 state/gate), `tools/evidence/`(P21 evidence refs·HEAD 무결성).

### 헌법·관례 (개정 대상)
- `harness/commands/{checkpoint.md,orient.md}` — 개정(재구현 금지). `harness/commands/handoff.md` — 신규 생성.
- `tools/memory_regen/inject.py` + emitted `session-inject.ts` — injector 개정(token cap·lazy-load 보존). `tools/harness_emit/`(emit parity + drift). `AGENTS.md`, `tools/polyglot_lint`.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 18 handoff.schema.json: 기본 shape 존재 — 확장만.
- Phase 20 `tools/task_control` state/revision + `/phase-gate`: orient가 resume 전 호출.
- Phase 21 `tools/evidence` + HEAD-committed 무결성 패턴: HANDOFF hash 참조·검증에 재사용.
- 기존 `inject.py` 결정론 + ~1k token budget + lazy-load: 개정 시 불변식 유지.

### Established Patterns
- 순수·결정론 + 정렬·해시. HANDOFF generator는 state/evidence에서 파생, 재현가능.
- 헌법 평면 write는 gate-model. handoff.schema 확장은 dev draft + 재해시.
- 커맨드는 harness/ 소스 → 두 runtime emit + emit-drift 게이트.

### Integration Points
- `/checkpoint` → HANDOFF 생성 + pointer. `/orient` → HANDOFF surface + `/phase-gate`. injector → pointer-only.
- Phase 23 lifecycle fixture가 create→transition→evidence→handoff→orient→phase-gate E2E를 CI로 굳힘 — 이번엔 도구·E2E 그린까지.
</code_context>

<specifics>
## Specific Ideas

- 완료기준: 설계 §Phase 5 완료기준 1~8 승격 — HANDOFF schema+참조 hash 검증, stale revision/ref/artifact HANDOFF 실패, fresh-session checker 필수필드 100% 복원, create→transition→evidence→handoff→**새 프로세스** orient→phase-gate green E2E, injector snapshot이 task 유무 양쪽에서 token cap 준수, injector 출력 pointer-only(본문 없음), `.memory/state/`에 pointer 외 packet 복제 없음, checkpoint/orient/handoff 두 runtime emit parity.
- E2E 테스트: **별도 프로세스**로 orient 실행해 HANDOFF만으로 복원 실증(대화 컨텍스트 없음).
</specifics>

<deferred>
## Deferred Ideas

- Lifecycle fixture 20개·stress/negative 사례·ADR·CI 굳히기(Phase 23).
- Signed external attestation(Phase 21 D-10 defer)도 23.
</deferred>
