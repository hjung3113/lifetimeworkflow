# Requirements: v2.2 Adaptive Task Control Plane

**Defined:** 2026-07-18
**Core Value:** 계약(contracts)을 단일 정본으로 두고, 폴리글랏 표현차·레거시 전환 리스크를 하네스가 자동으로 강제·검증한다 — "어떻게 개발·유지보수·리팩토링하는가"가 실행 가능한 스킬·커맨드·훅으로 박혀 있다.

> Source: `docs/explanation/next-milestone-task-control-plane.md` (codex sol, sol-vs-fable debate, human-approved). Locked decisions: A=`.workflow/tasks/`, B=6 phases. Requirements derive directly from the approved design — not re-scoped.

## v2.2 Requirements

### Task Packet Contract (Phase 18)

- [ ] **TCP-01**: 작업 상태 shape가 사람 승인 JSON Schema Draft 2020-12 4종(`task`/`state`/`evidence`/`handoff`)으로 코드보다 먼저 고정되고 contract-drift 해시 게이트에 등록된다 (schema 변경 시 paired golden + 사람 승인 요구).
- [ ] **TCP-02**: 한 작업 인스턴스가 `.workflow/tasks/<task-id>/`에 phase·lane·baseline-ref 상태로 존재하며, `.memory/state/`와 상호 독립이다(한쪽 삭제가 다른 쪽 검증 결과를 바꾸지 않음).

### Deterministic Risk Router (Phase 19)

- [ ] **TCP-03**: 7축(ambiguity·change-scope·data/security·reversibility·impact·coordination·context-pressure) 점수를 FAST/STANDARD/STRICT/CONTROLLED 레인으로 매핑하는 순수 함수 라우터가 동일 입력에 byte-identical decision을 낸다(레포 미접근·LLM 판단 없음).
- [ ] **TCP-04**: 자동 승격 규칙(auth·payment·secret/PII·destructive data·unclear rollback·external contract break·헌법 평면 접촉)이 점수와 무관하게 최소 레인을 강제하고, 승격은 레인을 낮출 수 없다.
- [ ] **TCP-05**: 각 레인이 필수 산출물/게이트 matrix를 선언하고, instance risk overlay는 선언적 데이터로 **escalate-only**(레인 하향·게이트 제거 불가)이며 core는 instance를 참조하지 않는다.
- [ ] **TCP-06**: `/intake`가 작업을 점수화해 task packet을 생성하고, FAST 레인은 packet 외 추가 ceremony(상세 SPEC·PLAN·worktree·이중 review)를 자동 요구하지 않는다.

### Atomic State Manager + Context/Transition Gate (Phase 20)

- [ ] **TCP-07**: 상태 전이가 원자적·동시성 안전하다 — 중단된 쓰기 후 정확히 하나의 valid state가 canonical하고, 같은 revision을 경쟁하는 두 writer 중 정확히 하나만 성공한다(revision CAS).
- [ ] **TCP-08**: 허용된 phase 전이만 성공하고 불법 전이는 어떤 canonical 파일도 바꾸지 않고 실패한다(필수 산출물 부재 advance 포함).
- [ ] **TCP-09**: phase-start 게이트가 stale git ref·baseline mismatch·wrong worktree·constraint attestation 누락에 대해 EXECUTE 진입 전 fail-closed한다.
- [ ] **TCP-10**: `/phase-gate`가 각 phase 시작 시 게이트 + constraint 재진술(coverage/staleness 결정론적 검사, 이해 증명 주장 없음)을 실행한다.

### Evidence Bundle Adapters (Phase 21)

- [ ] **TCP-11**: evidence adapter가 기존 게이트(lint·test·contract-drift·golden·freshness·`/verify-work`)를 재구현하지 않고 command·exit code·artifact path·SHA-256·status로 수집하며, `SKIPPED`를 `PASSED`로 바꾸지 않는다.
- [ ] **TCP-12**: acceptance-criterion ↔ evidence 양방향 trace가 존재하고, 필수 criterion에 passing evidence가 없으면 VERIFY 완료가 거부되며, artifact 1 byte 변조 시 hash 검증이 실패한다.
- [ ] **TCP-13**: secret/credential/PII 패턴이 evidence·HANDOFF에 평문 기록되지 않고 명시적으로 거부(redaction report)된다.

### Handoff + Fresh-Session Resume (Phase 22)

- [ ] **TCP-14**: HANDOFF가 특정 state revision의 immutable snapshot이고, HANDOFF만 읽은 새 세션이 task-id·goal·non-goals·critical constraints·현재 phase·ref·next-action을 100% 복원한다(stale ref/artifact 참조 시 실패).
- [ ] **TCP-15**: `/checkpoint`·`/orient`가 HANDOFF를 생성·surface하도록 개정되고, SessionStart injector가 active task를 pointer-only(task-id·phase·lane·next-action·HANDOFF 경로)로 주입하며 기존 ~1k token cap과 lazy-load를 보존한다.

### Lifecycle Evaluation + Docs + CI (Phase 23)

- [ ] **TCP-16**: 사람 ratified domain-neutral lifecycle fixture 20개(레인별 5개) + stress/negative 사례(buried constraint·stale handoff·wrong worktree·tampered/missing evidence·concurrent writers·constitution change·illegal downgrade overlay)가 CI에서 통과한다.
- [ ] **TCP-17**: FAST fixture가 상세 SPEC/PLAN/worktree/이중 review 없이 통과하고 FAST 사용자 의식 단계 상한(intake+verify 2회)이 fixture로 고정된다(ceremony 역류 방지).
- [ ] **TCP-18**: 구조 결정 ADR(namespace·authority·lifecycle·overlay)이 사람에 의해 append-only 승인되고, `docs/how-to/task-lifecycle.md`가 추가되며, 기존 전체 게이트(pytest·contract-drift·golden·stale-derived·GEN-04·harness emit-drift·모델 식별자 lint)가 green을 유지한다.

## Future Requirements

Deferred to a later milestone (설계가이드 §14 우선순위 3·6·7 + 후속 후보).

### Skill Layer
- **TCP-F01**: clarify / TDD / diagnose / domain-modeling 규율 스킬을 task lifecycle에 연결.
- **TCP-F02**: adversarial review 다중 전문가 패널을 STRICT+ 레인에 조건부 도입.

### Routing & Supply Chain
- **TCP-F03**: 전문 agent allowlist + capability-neutral 모델 라우팅을 레인과 연동.
- **TCP-F04**: skill registry.lock + adapter 생성 CI(버전·해시·라이선스).

### Instance Overlay Authoring
- **TCP-F05**: log-parser instance용 risk overlay(인증·데이터·운영 위험) 작성.

## Out of Scope

| Feature | Reason |
|---------|--------|
| GSD 대체 / 두 번째 사용자 대면 orchestrator | 오케스트레이터는 하나(설계가이드 §3). 라우터는 순수 함수이지 orchestrator 아님. GSD는 dev-side로 유지. |
| `opencode-matt-workflows` bundle·installer·flow-* 19종 vendor | 프레임워크 스태킹 안티패턴(§13). 패턴만 차용. |
| 기존 `/review`·`/verify-work`·`/checkpoint`·CI 검증 로직 재구현 | evidence adapter는 수집만; 기존 gate 의미 보존. |
| contract hash·golden comparator·§4.3–4.6 normalization 재구현 | 기존 안전망 재사용, 복제 금지. |
| LLM router persona / LLM 기반 lane 결정 | 레인 판정은 전부 결정론적. |
| 실제 모델 ID·provider·cost tier를 코드·packet·evidence·commit·PR에 기록 | 비협상 제약(모델 식별자 미포함). |
| SHIP/LEARN phase + deployment provider 의미론 | 현 template에 실 배포 대상 없음 — 연기. |
| lock daemon·distributed transaction·bespoke dispatch engine | 원자성 범위는 temp-write+rename+revision CAS까지만. |
| `.memory/tasks/` 저장 위치 | 사람 결정 A로 기각 — `.workflow/tasks/` 채택(memory 3번째 책임 평면 회피). |
| 5-phase 구조 | 사람 결정 B로 기각 — evidence·handoff·eval 실패양상 분리 위해 6-phase. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TCP-01 | Phase 18 | Pending |
| TCP-02 | Phase 18 | Pending |
| TCP-03 | Phase 19 | Pending |
| TCP-04 | Phase 19 | Pending |
| TCP-05 | Phase 19 | Pending |
| TCP-06 | Phase 19 | Pending |
| TCP-07 | Phase 20 | Pending |
| TCP-08 | Phase 20 | Pending |
| TCP-09 | Phase 20 | Pending |
| TCP-10 | Phase 20 | Pending |
| TCP-11 | Phase 21 | Pending |
| TCP-12 | Phase 21 | Pending |
| TCP-13 | Phase 21 | Pending |
| TCP-14 | Phase 22 | Pending |
| TCP-15 | Phase 22 | Pending |
| TCP-16 | Phase 23 | Pending |
| TCP-17 | Phase 23 | Pending |
| TCP-18 | Phase 23 | Pending |
