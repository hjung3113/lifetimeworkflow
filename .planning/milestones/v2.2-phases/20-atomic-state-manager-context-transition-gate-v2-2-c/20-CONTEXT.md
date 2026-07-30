# Phase 20: Atomic State Manager + Context/Transition Gate - Context

**Gathered:** 2026-07-18
**Status:** Ready for planning

<domain>
## Phase Boundary

오케스트레이터의 prose 진행을 **원자적·동시성 안전한 상태 전이**로 바꾸고, phase 시작 전에 ref·제약을 **fail-closed** 검증한다. 산출: `tools/task_control/` 상태 도구(create/show/transition/block/resume/validate), atomic write + revision CAS + 중단쓰기 복구, `/phase-gate` 커맨드(harness 소스), context-attestation shape. **요구사항 TCP-07, TCP-08, TCP-09, TCP-10.** evidence 수집은 Phase 21, handoff는 22 — 범위 밖.
</domain>

<decisions>
## Implementation Decisions

> `--auto` 단일 패스. 정본: 설계 §Phase 3. Phase 18 계약(state schema·transitions.json) + Phase 19(레인별 필수 산출물 matrix) 소비.

### 원자성·동시성 (TCP-07)
- **D-01:** state 쓰기는 temp-file + 같은 파일시스템 atomic replace(rename). 중단된 쓰기 후 이전 valid state 또는 새 valid state 중 **정확히 하나**가 canonical.
- **D-02:** `state.revision` 기반 compare-and-swap(optimistic concurrency). 모든 mutation은 expected revision 요구 — 같은 revision 경쟁 시 정확히 하나만 성공, 나머지 거부(stale writer).
- **D-03:** state 외 artifact는 immutable run ID로 먼저 완성 후 state/index가 참조하는 commit 규칙. orphan artifact 진단 가능(canonical evidence로 오인 금지). **비목표:** lock daemon·분산 트랜잭션·cross-worktree 공유 DB.

### 전이 (TCP-08)
- **D-04:** transitions.json(Phase 18)의 허용 전이 matrix만 성공. 불법 전이·필수 산출물 부재 advance는 **어떤 canonical 파일도 바꾸지 않고** exit≠0. 레인별 필수 산출물은 Phase 19 risk-policy matrix에서 읽음.

### phase-start 게이트 (TCP-09, TCP-10)
- **D-05:** phase-start 검사: repo root, worktree/ref, baseline commit, expected revision, required sources readable, unresolved blocker, constraint attestation, 레인별 required artifact 존재·schema. stale ref·baseline mismatch·wrong worktree·attestation 누락 → EXECUTE 진입 전 fail-closed(exit≠0 + refresh 목록).
- **D-06:** `context-attestation.json` shape: constraint ID, source path/hash, applies-to phase, prohibited action IDs, required evidence IDs, planned action mapping. 게이트는 "이해 증명" 주장 안 함 — ID/source-hash **coverage·staleness만 결정론적** 검사(복붙 통과 방지는 Phase 23 buried-constraint eval이 실측). prohibited action은 현재 hook/permission으로 기계 판정 가능 범위만.
- **D-07:** `/phase-gate`는 harness/commands 소스 → 두 런타임 emit. 각 phase 시작 시 게이트 + constraint 재진술 실행.

### 기존 기능 조합 (재구현 금지)
- **D-08:** 기존 orchestrator가 유일한 상태 전이 요청자. 기존 `/checkpoint`는 세션 요약만(active task ID + pointer 추가만 — Phase 22). 기존 topology routing은 EXECUTE owner 선택에 계속 사용. context-budget은 context pressure 입력·fan-out 결정에 계속.

### 헌법 정합 + 실행 위임
- **D-09:** tools는 domain-neutral Python core. `.workflow/tasks/`(Phase 18) 인스턴스에 write, `.memory/derived/` 아님. `/phase-gate` emit-drift 0. 모델 식별자 없음. byte hygiene.
- **D-10:** 구현 **codex terra medium (fast off, headless)**. 리뷰 **교대 → fable**(P19=sol). Claude 검증/머지. 표준 러너 `scratchpad/run_agent.sh`. 참조 [[design-and-gsd-via-codex-sol]].
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 설계 정본
- `docs/explanation/next-milestone-task-control-plane.md` §Phase 3(Atomic State Manager and Context/Transition Gate) + §7.9(context health gate schema) — 산출물·조합·완료기준 정본.
- `.planning/REQUIREMENTS.md` TCP-07..10 + Out of Scope(lock daemon·분산트랜잭션 금지, 기존 gate 재구현 금지).
- `.planning/ROADMAP.md` "Phase 20" success criteria 4개.

### 소비 대상 (Phase 18/19)
- `contracts/harness/task-control/state.schema.json` — state shape(revision 포함).
- `contracts/harness/task-control/transitions.json` — 허용 전이 matrix.
- `harness/risk-policy.toml` + `tools/risk_router/` — 레인별 required artifact/gate matrix.
- `tools/task_packet/` — packet 검증 API.

### 헌법·관례
- `AGENTS.md`(root), `harness/agents/orchestrator.md`(유일 조정자·topology routing), `harness/commands/checkpoint.md`(세션 상태 경계), `tools/harness_emit/`(/phase-gate emit).
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/task_packet/`(P18): state schema 검증·전이 legality 로직 일부 재사용(라우팅 전이표는 transitions.json).
- `tools/risk_router/`(P19): 레인별 필수 산출물 matrix 소비.
- `tools/harness_emit/`: `/phase-gate` 두 런타임 emit + emit-drift 게이트.
- 기존 atomic-write 패턴: `tools/` 내 파일 쓰기(temp+rename) 관례 확인 후 재사용.

### Established Patterns
- 순수·결정론 + 정렬·해시(P18/19 검증기 규율). 상태도구는 부수효과 있으나 atomic·재현가능.
- 헌법 평면 write는 gate-model(agent draft, CODEOWNERS ratify) — 이번엔 tools/ + harness/ 위주라 contracts 신규 변경 최소.

### Integration Points
- orchestrator ↔ 상태도구(유일 전이 요청자). `/checkpoint`·`/orient`는 Phase 22에서 배선(여기선 pointer 계약만 인지).
- Phase 21 evidence가 gate 결과를 소비, Phase 22 handoff가 state revision 소비 — 이번엔 shape·게이트만.
</code_context>

<specifics>
## Specific Ideas

- 완료기준: 설계 §Phase 3 완료기준 1~11 승격 — transition matrix edge/non-edge, 필수산출물 부재 advance 무변경, 두 writer 중 하나만 성공, 강제종료 후 정확히 하나 canonical, stale ref/wrong worktree/baseline fail-closed, unresolved blocker→BLOCKED 외 거부, constraint/source-hash 누락 거부, prohibited action 차단, required evidence 없는 constraint VERIFY/COMPLETE 거부, orphan artifact 진단, /phase-gate emit drift 0.
- 동시성 테스트: 실제 두 writer 경쟁(멀티프로세스 또는 revision CAS 시뮬)로 정확히 하나 성공 증명.
</specifics>

<deferred>
## Deferred Ideas

- Evidence 수집기(21), handoff·injector 배선(22), lifecycle fixture·ADR(23).
- Artifact run의 완성 marker 및 evidence hash 검증은 Phase 21에서 evidence 수집/검증과 함께
  도입한다. Phase 20은 phase-oriented presence만 소비하며, orphan은 phase-gate refresh에 노출한다.
- `/checkpoint`·`/orient` 실제 개정은 Phase 22.
</deferred>
