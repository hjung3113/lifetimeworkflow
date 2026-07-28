# 최종 마일스톤 설계서 — Adaptive Task Control Plane

> **HISTORICAL (역사 기록).** 이 문서는 Phase 43이 삭제한 task-control plane을 설계한 기록이며,
> 여기 서술된 control·경로·커맨드는 더 이상 존재하지 않는다. `docs/adr/0008-task-control-plane-lifecycle.md`가
> 이 문서를 "Design authority"로 인용하고 ADR은 append-only이므로 삭제하지 않고 보존한다. ADR-0012 참조.

> 사람 승인용 최종 제안서. 이 문서는 구현 자체가 아니라 다음 단일 마일스톤의
> 범위, 책임 경계, 결정론적 완료 조건을 고정한다.

## 1. 마일스톤 이름과 한 줄 목표

**마일스톤 이름:** Adaptive Task Control Plane — Risk-Routed State, Evidence, and Handoff

**한 줄 목표:** 기존 orchestrator, GSD, two-plane memory, `/review`, `/verify-work`,
`/checkpoint`, contract/golden/CI 게이트를 재사용하면서, 작업을 기계 판독 가능한 패킷,
위험 레인, 원자적 상태 전이, 증거, 재개 가능한 HANDOFF로 연결한다.

이 마일스톤은 새 범용 프레임워크를 설치하지 않는다.

이 마일스톤은 작업 수명주기 자체에 빠진 연결 계층만 출하한다.

## 2. 왜 이 슬라이스인가

### 2.1 설계 가이드 §14와 현재 레포의 격차

fable 제안의 §14 격차표와 인과 사슬을 최종안의 근거로 채택한다.

| 가이드 §14 우선순위 | 현재 레포 | 격차 | 이번 처리 |
|---|---|---|---|
| 1. TASK/STATE/EVIDENCE/HANDOFF + state machine | `/checkpoint`의 짧은 서술형 세션 상태만 존재 | 큼 | 작업 패킷 계약과 상태 전이 도입 |
| 2. FAST/STANDARD/STRICT/CONTROLLED | 위험 점수·자동 승격·레인별 산출물 정책 없음 | 큼 | 결정론적 Risk Router 도입 |
| 3. clarify→spec→implement→review→verify | GSD + 기존 review/verify 명령이 상당 부분 보유 | 작음 | 재구현하지 않고 state machine에 연결 |
| 4. context health gate + stress test | pointer injection은 있으나 ref·constraint·phase fail-closed 없음 | 큼 | phase-start gate와 재개 검증 도입 |
| 5. 결정론적 evidence layer | 검증기는 있으나 task/criterion과 연결된 bundle 없음 | 중간 | 기존 결과를 수집·해시·추적 |
| 6. 전문 agent allowlist/model routing | persona와 permission matrix가 이미 존재 | 작음 | 이번 범위에서 제외 |
| 7. registry/adapter | `harness_emit`과 manifest가 이미 존재 | 작음 | 기존 emit만 확장 |

### 2.2 하나의 수직 슬라이스인 이유

격차 1·2·4·5는 독립 기능이 아니라 하나의 인과 사슬이다.

1. 레인을 정하려면 목표·비목표·위험 입력을 담는 작업 패킷이 필요하다.
2. 레인별 필수 절차를 강제하려면 허용된 phase 전이와 gate가 필요하다.
3. phase 완료를 판정하려면 실행 사실을 담은 evidence가 필요하다.
4. 새 세션이 안전하게 재개하려면 state와 evidence를 고정한 HANDOFF가 필요하다.

넷 중 하나만 빠져도 나머지는 prose 권고로 퇴행한다.

따라서 이번 마일스톤은 “작업 패킷 → 위험 레인 → 상태 전이 → 증거 → 인계”를
end-to-end로 출하하되, 각 단계 내부 검증기는 기존 구현을 재사용한다.

## 3. 미해결 이견 2건의 최종 결정

### 사람 확인 포인트 A — 작업 패킷 저장 위치

**최종 결정: `.workflow/tasks/<task-id>/`를 채택한다.**

**fable 반대 논거:** `.memory/tasks/`는 기존 volatile-committed memory 슬롯을 재사용하므로
새 최상위 디렉터리, map, ignore, lint 표면을 만들지 않는다.

**판정 근거:** TASK/STATE/EVIDENCE/HANDOFF는 세션 기억이나 재생성 memory가 아니라
독립 작업 수명주기 기록이다. 별도 namespace가 `.memory/state/`의 bounded-session 책임과
two-plane data-authority 의미를 보존하며, `.memory/state/`에는 active task pointer만 둔다.

**사람이 뒤집을 때의 조건:** task packet을 “committed volatile memory의 하위 유형”으로
공식 정의하고 `.memory/`의 크기·주입·보존 정책을 함께 확장할 의사가 있다면
`.memory/tasks/`도 가능하다. 그 경우 경로만 바꾸지 말고 memory ADR·lint·문서를 같이 바꾼다.

### 사람 확인 포인트 B — Phase 수

**최종 결정: 6개 Phase를 채택한다.**

**fable 반대 논거:** evidence와 handoff는 자연스럽게 결합되므로 5개 Phase가 더 작고,
평가·CI도 한 Phase면 충분하다.

**판정 근거:** evidence는 검증 결과의 진실성과 tamper detection을 소유하고,
handoff는 `/checkpoint`·`/orient`·SessionStart·commit/ref 재개를 소유한다.
실패 양상과 rollback 경계가 달라 별도 Phase가 더 검토 가능하며 범위 자체는 늘지 않는다.

**사람이 뒤집을 때의 조건:** 같은 구현 owner와 같은 PR에서 evidence와 resume integration을
반드시 함께 배포해야 한다면 Phase 4와 5를 병합할 수 있다. 완료 기준은 삭제하지 않는다.

## 4. Phase별 상세

### Phase 1 — Task Packet Contract Ratification

#### 목적

작업 상태·증거·인계의 shape와 소유권을 코드보다 먼저 고정한다.

#### 산출물

- 사람 승인으로 진입하는 JSON Schema Draft 2020-12 계약 4종:
  `task.schema.json`, `state.schema.json`, `evidence.schema.json`, `handoff.schema.json`.
- 헌법 평면 내 권장 위치: `contracts/harness/task-control/`.
- 작업 인스턴스 위치: `.workflow/tasks/<task-id>/`.
- 최소 디렉터리 shape:
  - `task.json`: goal, non-goals, risk inputs, lane, criteria, constraints, decisions.
  - `state.json`: phase, revision, baseline/current ref, completed items, next action, blockers.
  - `evidence.json`: gate run index와 criterion/finding trace.
  - `handoff.json`: 재개 snapshot; 세션 경계가 있을 때 생성.
  - `artifacts/`: immutable logs/reports; bundle에는 경로·요약·해시만 저장.
- phase enum:
  `INTAKE`, `CLARIFY`, `SPEC`, `PLAN`, `EXECUTE`, `REVIEW`, `VERIFY`,
  `COMPLETE`, `BLOCKED`.
- 레인별 허용 경로:
  - FAST: `INTAKE → EXECUTE → VERIFY → COMPLETE`.
  - STANDARD: 필요 시 CLARIFY, 간략 SPEC/PLAN, REVIEW 포함.
  - STRICT: CLARIFY, 승인된 SPEC, PLAN, REVIEW, VERIFY 필수.
  - CONTROLLED: STRICT + 단계별 human gate, dry-run, rollback evidence.
- task-local decision과 durable ADR decision의 구분:
  장기 구조 결정만 ADR pointer를 요구한다.
- `.memory/state/`와 `.workflow/tasks/`의 책임 맵.

#### 책임 경계

- agent는 `contracts/`, `docs/adr/`, `golden/`을 직접 쓰지 않는다.
- 계약 4종과 paired golden/hash 변경은 사람 주도 ratification이 선행한다.
- `task.json`은 계약·ADR을 덮지 않으며 source path와 hash로 참조한다.
- `.memory/state/`는 active task ID와 다음 pointer만 소유한다.
- `.workflow/tasks/`는 derived plane이 아니며 자동 재생성하지 않는다.
- SHIP/LEARN은 실제 배포 의미가 없는 현재 template 범위에서 연기한다.

#### 결정론적 완료 기준

1. positive fixture 최소 5개가 네 schema를 모두 통과한다.
2. 필수 필드별 negative fixture가 각각 exit non-zero다.
3. 알 수 없는 phase·lane·transition은 거부된다.
4. criterion, constraint, evidence, finding의 dangling ID가 거부된다.
5. baseline commit 또는 repo root가 없는 패킷은 실행 phase에 진입하지 못한다.
6. schema hash 이동에는 paired golden과 사람 승인 기록이 요구된다.
7. `.memory/state/` 삭제 여부가 task packet validation 결과를 바꾸지 않는다.
8. task packet 부재가 기존 SessionStart derived regeneration을 깨지 않는다.
9. core contract와 fixture에 instance 경로·도메인 용어가 없다.

### Phase 2 — Deterministic Risk Router

#### 목적

소작업은 짧게, 고위험 작업은 강하게 처리하도록 레인과 필수 산출물을 재현 가능하게 정한다.

#### 산출물

- `harness/risk-policy.toml`: runtime-neutral core policy.
- `tools/risk_router/`: 구조화 입력 → decision JSON 순수 계산기.
- `/intake`의 단일 source: `harness/commands/intake.md`.
- 일곱 점수 축, 각 `0..3`:
  ambiguity, change scope, data/security, reversibility,
  user/operations impact, coordination, context pressure.
- 기본 cut:
  `0..4 FAST`, `5..9 STANDARD`, `10..14 STRICT`, `15..21 CONTROLLED`.
- 자동 승격 reason code:
  auth/authorization, payment, secret/PII, destructive data change,
  unclear rollback, external contract break, constitution-plane touch,
  repeated constraint violation.
- lane별 required artifact/gate matrix.
- active instance가 제공할 수 있는 risk overlay 슬롯.
- effective policy hash와 router version 기록; 실제 모델 식별자는 기록하지 않음.

#### 책임 경계

- router는 repo를 읽거나 LLM 판단을 수행하지 않는다.
- 같은 packet + core policy + overlay hash는 같은 decision JSON을 낸다.
- repo fact probe와 사용자 결정이 risk input을 채우고 router는 계산만 한다.
- instance overlay는 선언적 데이터이며 **escalate-only**다.
- overlay는 최소 lane 상향, 새 promotion predicate, 추가 required gate만 허용한다.
- overlay는 cut 하향, core gate 제거, required artifact 삭제를 할 수 없다.
- core는 instance를 참조하지 않고 instance가 core policy를 소비한다.
- 이번 마일스톤은 overlay 메커니즘을 출하하되 특정 example overlay 작성은 비목표다.

#### 결정론적 완료 기준

1. cut 경계 fixture가 네 레인을 정확히 반환한다.
2. 동일 입력·policy hash의 출력은 byte-identical하다.
3. 모든 자동 승격 fixture가 점수 레인보다 낮지 않은 결과를 낸다.
4. 누락·범위 밖 score·unknown reason은 exit non-zero다.
5. decision JSON은 scores, total, lane, reasons, required artifacts, policy hashes를 포함한다.
6. overlay가 lane 또는 gate를 낮추려 하면 validation이 실패한다.
7. core-only 결과보다 effective overlay 결과가 항상 같거나 강하다.
8. FAST fixture는 상세 SPEC, PLAN, worktree, 이중 review를 자동 요구하지 않는다.
9. CONTROLLED fixture는 human gate, dry-run, rollback, audit evidence를 요구한다.
10. 실제 모델 ID/provider 문자열이 policy, output, fixture에 없다.

### Phase 3 — Atomic State Manager and Context/Transition Gate

#### 목적

작업 전이를 원자적·동시성 안전하게 만들고, phase 시작 전에 ref와 제약을 fail-closed 검증한다.

#### 산출물

- `tools/task_control/` CLI:
  init, show, attest, transition, block, resume, validate.
- temp write + fsync 가능한 범위 + same-filesystem atomic replace.
- `state.revision` 기반 compare-and-swap optimistic concurrency.
- state 외 artifact는 immutable run ID로 먼저 완성한 뒤 state/index가 참조하는 commit 규칙.
- interrupted-write recovery와 orphan artifact 진단.
- `/phase-gate`의 단일 source: `harness/commands/phase-gate.md`.
- phase-start 검사:
  repo root, worktree/ref, baseline commit, expected revision,
  required sources, blocking decisions, required artifacts, constraint attestation.
- `context-attestation.json` shape:
  constraint ID, source path/hash, applies-to phase,
  prohibited action IDs, required evidence IDs, planned action mapping.
- 기존 orchestrator의 topology/context-budget routing과 task phase 연결.

#### 책임 경계

- gate는 LLM의 “이해”를 증명한다고 주장하지 않는다.
- ID/source-hash coverage는 누락·staleness만 결정론적으로 검사한다.
- prohibited action은 현재 hook/permission으로 기계 판정 가능한 범위만 차단한다.
- required evidence와 human gate는 phase 완료에서 실제 충족 여부를 검사한다.
- 단순 constraint 문장 복붙은 evidence requirement를 충족하지 못한다.
- repeated violation은 새 세션, lane 상향, 또는 BLOCKED로만 처리한다.
- lock daemon, distributed transaction, cross-worktree shared database는 만들지 않는다.

#### 결정론적 완료 기준

1. transition matrix의 모든 edge는 성공하고 모든 non-edge는 실패한다.
2. 필수 artifact가 없는 advance는 어떤 canonical file도 바꾸지 않는다.
3. 같은 revision을 갱신하는 두 writer 중 정확히 하나만 성공한다.
4. 강제 종료 후 이전 valid state 또는 새 valid state 중 정확히 하나가 canonical하다.
5. stale ref, wrong worktree, baseline mismatch는 EXECUTE 전에 차단된다.
6. unresolved blocker가 있으면 BLOCKED/해제 외 전이가 거부된다.
7. constraint ID 또는 source hash 누락은 phase start를 거부한다.
8. prohibited action fixture는 실행 전에 차단된다.
9. required evidence가 없는 constraint는 VERIFY/COMPLETE로 전이하지 못한다.
10. orphan artifact는 canonical evidence로 오인되지 않고 진단 가능하다.
11. emit 후 `/phase-gate`가 두 runtime에 존재하고 generated-tree drift가 0이다.

### Phase 4 — Evidence Bundle Adapters

#### 목적

기존 gate 실행을 재구현하지 않고 task, criterion, review finding에 연결된 위조 탐지 증거로 남긴다.

#### 산출물

- `tools/evidence/` capture adapter.
- 각 run의 command ID, normalized argv, exit code, status,
  artifact path, SHA-256, start/end marker, gate version 기록.
- status: `PASSED`, `FAILED`, `SKIPPED`, `BLOCKED`.
- skip reason과 pass의 엄격한 분리.
- acceptance criterion ↔ evidence 양방향 trace.
- review finding의 severity, disposition, evidence reference.
- secret/credential/PII pattern refusal와 redaction report.
- 기존 `/review`와 `/verify-work`에 capture adapter 연결.
- 로컬 evidence와 CI reference의 명시적 구분.

#### 책임 경계

- adapter는 lint, test, contract-drift, golden, freshness 로직을 재구현하지 않는다.
- 기존 `/verify-work`의 다섯 gate 의미와 실행 순서를 유지한다.
- FAST 비용 절감 때문에 `/verify-work` 내부 gate를 제거하지 않는다.
- presence-safe no-op/skip은 기존 명령의 결과를 그대로 기록한다.
- exit code는 실제 child process 결과에서만 채운다.
- raw stdout/stderr는 artifact로 저장하고 packet에는 경로·요약·해시만 둔다.
- constitution-plane 변경은 도구 pass와 별개로 human approval evidence를 요구한다.

#### 결정론적 완료 기준

1. pass/fail/skip/blocked fixture가 서로 다른 status로 round-trip한다.
2. artifact 한 byte 변경 시 hash verification이 실패한다.
3. 실행하지 않은 gate를 PASSED로 등록할 수 없다.
4. required criterion에 passing evidence가 없으면 VERIFY 완료가 거부된다.
5. unresolved blocker/major finding이 있으면 COMPLETE 전이가 거부된다.
6. constitution-plane diff에 human approval reference가 없으면 완료가 거부된다.
7. secret fixture는 packet/artifact에 평문 기록되지 않고 명시적으로 거부된다.
8. missing artifact와 stale evidence index가 validation에서 실패한다.
9. 기존 `/verify-work`의 다섯 gate regression test가 그대로 통과한다.

### Phase 5 — Handoff and Fresh-Session Resume

#### 목적

대화 transcript 없이 정확한 task snapshot을 새 세션에 전달하고 안전한 재개를 강제한다.

#### 산출물

- `tools/handoff/` generator/validator.
- HANDOFF 필드:
  task ID, goal, non-goals, lane, current phase/revision,
  critical constraint refs, decisions, baseline/current commit,
  changed paths, evidence refs, unresolved items,
  exact next action, stop condition, required read paths.
- HANDOFF가 참조하는 state/evidence/artifact hash 검증.
- `/handoff`의 단일 source: `harness/commands/handoff.md`.
- `/checkpoint` 개정:
  active task가 있을 때 valid HANDOFF를 먼저 생성하고 task pointer만 session state에 기록.
- `/orient` 개정:
  active HANDOFF를 최우선 pointer로 보이고 resume 전에 `/phase-gate` 요구.
- SessionStart injector 개정:
  task ID, phase, lane, revision, next action, HANDOFF 경로만 주입.
- 기존 ~1k token cap과 lazy-load 보존.

#### 책임 경계

- HANDOFF는 대화 요약이 아니라 특정 state revision의 immutable snapshot이다.
- HANDOFF는 원본 계약·ADR·evidence를 복제하지 않고 path/hash로 참조한다.
- SessionStart는 task 본문·로그·contract body를 주입하지 않는다.
- `/checkpoint`의 기존 bounded `.memory/state/` 정책과 선택적 commit 의미를 보존한다.
- stale HANDOFF는 자동 보정하지 않고 재생성을 요구한다.
- 새 세션은 HANDOFF 검증 전 EXECUTE/REVIEW/VERIFY를 시작하지 않는다.

#### 결정론적 완료 기준

1. HANDOFF schema와 모든 참조 hash가 검증된다.
2. stale revision/ref/artifact를 가리키는 HANDOFF는 실패한다.
3. fresh-session checker가 HANDOFF만으로 필수 필드 100%를 복원한다.
4. create → transition → evidence → handoff → 새 프로세스 orient → phase-gate가 green이다.
5. injector snapshot은 task 유무 양쪽에서 기존 token cap을 지킨다.
6. injector 출력은 pointer만 포함하고 task/contract/artifact 본문을 포함하지 않는다.
7. `.memory/state/`에는 active task ID와 pointer 외 task packet 복제가 없다.
8. `/checkpoint`, `/orient`, `/handoff`의 두 runtime emit parity가 통과한다.

### Phase 6 — Lifecycle Evaluation, Documentation, and CI

#### 목적

소작업 ceremony 억제, 고위험 fail-closed, fresh-session 재개를 출하 전에 재현 가능하게 증명한다.

#### 산출물

- 사람 ratification을 받은 domain-neutral lifecycle fixture 20개:
  레인별 5개.
- negative/stress cases:
  buried constraint, stale handoff, wrong worktree/ref,
  missing/tampered evidence, concurrent writers,
  secret artifact, constitution change, illegal downgrade overlay.
- end-to-end lifecycle eval runner.
- CI jobs:
  schemas, router, transition/concurrency, context gate,
  evidence/handoff, emit parity/drift, existing full suite fan-in.
- 라이프사이클 how-to 문서 (당시 계획된 산출물. Phase 43의 plane 삭제와 함께 제거되었다 —
  이 문서 상단의 HISTORICAL 헤더 참조).
- 사람 작성·승인 대상 ADR:
  Task Control Plane의 namespace, authority, lifecycle, overlay 결정.
- shadow 운영 시 수집할 지표 정의:
  lane override, ceremony count, gate failure reason,
  evidence completeness, handoff reconstruction time.

#### 책임 경계

- fixture expected lane은 사람 ratification을 거친 데이터다.
- 아직 없는 production 통계로 false-escalation 비율을 출하 gate처럼 꾸미지 않는다.
- shadow 지표는 후속 정책 보정 자료이며 이번 deterministic gate를 대체하지 않는다.
- ADR은 agent가 작성·승인하지 않는다; 사람 승인 없이는 구조 결정을 확정하지 않는다.
- 문서는 generator-owned 영역과 human-owned 영역을 명확히 구분한다.

#### 결정론적 완료 기준

1. 20개 fixture가 ratified expected lane과 정확히 일치한다.
2. false downgrade는 fixture 기준 0건이다.
3. FAST fixture는 상세 SPEC/PLAN/worktree/이중 review 없이 통과한다.
4. FAST의 사용자 의식 단계는 intake와 verify 두 번을 넘지 않는다.
5. STRICT/CONTROLLED fixture는 독립 review와 rollback evidence를 요구한다.
6. buried-constraint fixture는 ID 복원뿐 아니라 prohibited action 차단 또는
   required evidence 충족까지 검증한다.
7. tampered/missing evidence와 stale HANDOFF는 모두 COMPLETE 전에 차단된다.
8. wrong worktree/ref와 concurrent stale writer는 모두 실행 전에 차단된다.
9. `uv run pytest` 전체가 회귀 없이 통과한다.
10. contract-drift, golden, stale-derived, GEN-04가 모두 green이다.
11. harness emit 후 `.opencode/`와 `.claude/` drift가 0이다.
12. 실제 모델 식별자가 repo artifact에 없다는 기존 lint가 green이다.
13. 사람 승인 ADR과 constitution-plane 변경 승인이 확인된다.

## 5. 명시적 비목표

- GSD 대체 또는 두 번째 사용자 대면 orchestrator 도입.
- OpenSpec, Superpowers, gstack, BMAD, Spec Kit 전체 설치.
- `opencode-matt-workflows` bundle, installer, flow-* 19종 vendor.
- 기존 `/review`, `/verify-work`, `/checkpoint`, CI 검증 로직 재구현.
- contract hash, golden comparator, §4.3–4.6 normalization 재구현.
- LLM router persona 또는 LLM 기반 lane 결정.
- 실제 모델 ID/provider/cost tier를 코드·packet·evidence·commit·PR에 기록.
- SHIP/LEARN phase와 deployment provider 의미론.
- 전문 agent marketplace, skill registry, 자동 upstream update.
- 특정 example instance용 risk overlay 작성.
- overlay를 이용한 core lane/gate 완화.
- FAST에 상세 SPEC, PLAN, worktree, TDD, 이중 review 상시 강제.
- adversarial review panel의 기본 강제.
- lock daemon, distributed transaction, bespoke dispatch engine.
- `.memory/derived/` 또는 generated runtime tree 손편집.
- transcript·대형 로그·secret을 packet이나 SessionStart에 적재.
- 자동 push, merge, golden approval, ADR approval.

## 6. 최대 리스크 3개와 완화

### 리스크 1 — 작업 평면이 또 하나의 정본이 됨

`.workflow/tasks/`가 contracts/ADR 또는 `.memory/state/`와 같은 사실을 복제하면
authority 충돌과 stale state가 발생한다.

**완화**

- contracts/ADR은 정책·데이터·장기 결정의 정본이다.
- `.workflow/tasks/`는 task-local 목표·진행·증거만 소유한다.
- `.memory/state/`는 active task pointer만 소유한다.
- 외부 사실은 path + content hash로 참조하고 복제하지 않는다.
- deletion-independence, dangling-reference, stale-hash tests를 유지한다.

### 리스크 2 — FAST에도 ceremony가 역류함

기계 판독 파일과 gate를 추가하면서 작은 수정의 실제 비용이 커질 수 있다.

**완화**

- FAST 경로를 `INTAKE → EXECUTE → VERIFY → COMPLETE`로 고정한다.
- 상세 SPEC/PLAN/HANDOFF는 조건이 없으면 생성하지 않는다.
- packet 파일은 도구가 원자적으로 생성하고 사용자는 문서 ceremony를 수행하지 않는다.
- FAST 사용자 의식 단계 상한과 required artifact matrix를 fixture로 고정한다.
- 기존 `/verify-work`는 한 번 호출하되 내부 안전 의미는 약화하지 않는다.

### 리스크 3 — 재진술과 evidence가 거짓 확신을 줌

constraint ID 복붙, forged summary, stale artifact가 형식 검사를 통과하면
“이해했다” 또는 “검증했다”는 과도한 신뢰를 만들 수 있다.

**완화**

- 재진술 gate는 comprehension proof가 아니라 coverage/staleness gate로 한정한다.
- constraint를 prohibited action과 required evidence/human gate에 연결한다.
- exit code는 child process에서만 받고 artifact hash를 검증한다.
- buried-constraint eval은 ID 존재가 아니라 행동 차단과 evidence 충족을 검사한다.
- 반복 위반은 lane 상향, fresh session, BLOCKED 중 하나로 fail-closed한다.

## 7. 기존 헌법 제약과의 정합

### 계약 우선

- task/state/evidence/handoff shape는 사람 승인 계약이 코드보다 먼저다.
- 도구가 schema와 다르면 도구를 수정한다.
- schema hash 변경은 paired golden과 contract-drift gate를 통과한다.
- criterion→evidence trace가 구현 편의에 따른 요구 축소를 막는다.

### 헌법 평면은 기계가 게이트하고 사람이 승인

- agent는 `contracts/`, `docs/adr/`, `golden/`을 쓰지 않는다.
- Phase 1 계약과 Phase 6 ADR은 사람 주도 산출물이다.
- human approval reference 없이는 관련 task가 COMPLETE로 전이하지 못한다.
- evidence pass는 golden/ADR/contract ratification을 대신하지 않는다.

### 파생물 손편집 금지

- `.memory/derived/`는 기존 generator만 쓴다.
- task packet과 evidence는 derived plane에 두지 않는다.
- generated `.opencode/`·`.claude/` 파일을 직접 편집하지 않는다.
- emit drift와 stale-derived gate를 exit checklist에 유지한다.

### 모든 런타임 산출물은 `harness/`에서 emit

- `/intake`, `/phase-gate`, `/handoff`, `/checkpoint`, `/orient`, `/verify-work`의
  runtime 정의 정본은 `harness/` 아래에 둔다.
- runtime-neutral 계산과 저장 엔진은 `tools/`에 둔다.
- 두 runtime projection은 `tools.harness_emit`만 생성한다.
- parity와 generated-tree clean diff를 CI에서 강제한다.

### 모델 식별자 금지

- risk는 작업 특성과 context pressure로만 계산한다.
- packet, evidence, HANDOFF, fixture, code, commit, PR에 실제 모델 ID를 두지 않는다.
- 승격은 fresh session, stronger review, human gate 같은 capability-neutral 결과로 표현한다.

### 폴리글랏 경계와 §4.3–4.6 정규화

- workflow tool은 instance 언어와 in-process 객체를 교환하지 않는다.
- 언어별 검증은 기존 process/CLI 경계를 통해 실행한다.
- golden evidence는 기존 canonicalized comparator 결과를 참조한다.
- 새 layer가 normalization 규칙을 복사하거나 raw byte diff를 도입하지 않는다.

### template과 instance의 단방향 의존

- core policy/schema/tool은 domain-neutral하다.
- instance overlay는 core를 소비하며 core는 overlay나 example 경로를 참조하지 않는다.
- overlay는 additive escalation만 가능하다.
- 기존 GEN-04 guard를 최종 fan-in gate로 유지한다.

## 8. 출하 판정 체크리스트

- [ ] 사람 확인 포인트 A의 `.workflow/tasks/` 위치가 승인되었다.
- [ ] 사람 확인 포인트 B의 6개 Phase가 승인되었다.
- [ ] 계약 4종과 paired golden/hash가 사람 승인 및 contract-drift를 통과했다.
- [ ] FAST/STANDARD/STRICT/CONTROLLED cut과 자동 승격이 fixture와 일치한다.
- [ ] instance overlay가 core 정책을 낮출 수 없다는 property test가 green이다.
- [ ] 허용 transition은 성공하고 불법 transition은 상태 변경 없이 실패한다.
- [ ] atomic interruption test에서 canonical state가 정확히 하나 남는다.
- [ ] concurrent stale writer 두 개 중 정확히 하나만 성공한다.
- [ ] wrong root/worktree/ref/baseline이 EXECUTE 전에 차단된다.
- [ ] constraint coverage와 source hash가 phase start에서 검증된다.
- [ ] prohibited action 또는 required evidence mapping이 phase 완료에서 검증된다.
- [ ] 기존 `/verify-work`의 다섯 gate 의미와 regression suite가 보존된다.
- [ ] criterion↔evidence 양방향 trace에 dangling ID가 없다.
- [ ] tampered/missing artifact가 hash validation에서 실패한다.
- [ ] secret fixture가 packet/HANDOFF/artifact에 평문 기록되지 않는다.
- [ ] unresolved blocker/major finding은 COMPLETE를 막는다.
- [ ] HANDOFF-only fresh-session checker가 필수 필드를 100% 복원한다.
- [ ] SessionStart payload가 pointer-only이며 기존 ~1k cap을 지킨다.
- [ ] FAST fixture가 상세 SPEC/PLAN/worktree/이중 review 없이 통과한다.
- [ ] 20개 ratified lifecycle fixture가 모두 expected lane과 결과를 만족한다.
- [ ] 전체 `uv run pytest`가 green이다.
- [ ] contract-drift, golden, stale-derived, GEN-04가 green이다.
- [ ] `harness_emit` 후 두 runtime tree의 drift가 0이다.
- [ ] repo artifact에 실제 모델 식별자가 없다.
- [ ] 구조 결정 ADR이 사람에 의해 append-only로 승인되었다.

위 체크리스트가 모두 충족되고 사람 확인 포인트 A·B가 승인된 경우에만
Adaptive Task Control Plane 마일스톤을 출하 완료로 판정한다.

=== DONE ===
