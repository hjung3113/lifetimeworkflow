# Phase 23: Lifecycle Evaluation + Docs + CI - Context

**Gathered:** 2026-07-19
**Status:** Ready for planning — FINAL phase of v2.2

<domain>
## Phase Boundary

소작업 ceremony 억제·고위험 fail-closed·fresh-session 재개를 **출하 전 재현 가능하게 증명**하고, 구조 결정을 **사람이 ratify**한다. 산출: 사람-ratified domain-neutral lifecycle fixture 20개(레인별 5) + negative/stress 사례, E2E lifecycle eval runner, CI jobs(schemas·router·transition/concurrency·context gate·evidence/handoff·emit parity/drift·full-suite fan-in), `docs/how-to/task-lifecycle.md`, 사람-승인 구조 ADR(namespace·authority·lifecycle·overlay), shadow 지표 정의. **요구사항 TCP-16, TCP-17, TCP-18.** Phases 18–22 전 계층 검증. 이번이 v2.2 마지막.
</domain>

<decisions>
## Implementation Decisions

> `--auto` 단일 패스. 정본: 설계 §Phase 6. Phase 18–22 전 산출물을 E2E로 굳힘. 새 계약 최소 — 주로 fixture·runner·CI·docs·ADR.

### 사람-ratified 평가 (TCP-16, TCP-17)
- **D-01:** domain-neutral lifecycle fixture **20개(레인별 5: FAST/STANDARD/STRICT/CONTROLLED)**. expected lane·결과는 **사람 ratification 데이터** — agent는 draft만, **사용자가 expected lane을 승인**(자가승인 금지). fixture는 `examples/` 아닌 core 중립.
- **D-02:** negative/stress 사례: buried constraint, stale handoff, wrong worktree/ref, missing/tampered evidence, concurrent writers, secret artifact, constitution change, illegal downgrade overlay — **모두 실행/COMPLETE 전 차단**됨을 실증. **P22 deferred 흡수**: un-resumed→transition→Write-deny 회귀 + `env VAR=1 git commit`/`git -C` prefix 우회 차단을 negative fixture로.
- **D-03:** E2E lifecycle eval runner: create→intake(risk router)→transition→evidence→handoff→(별도 프로세스)orient→phase-gate 전 경로. false downgrade **0건**. FAST는 상세 SPEC/PLAN/worktree/이중review 없이 통과 + **사용자 의식 단계 상한(intake+verify 2회)** fixture로 고정. STRICT/CONTROLLED는 독립 review + rollback evidence 요구.
- **D-04:** 아직 없는 production 통계로 false-escalation 비율을 출하 gate처럼 **꾸미지 않음**. shadow 지표(lane override·ceremony count·gate failure reason·evidence completeness·handoff reconstruction time)는 **정의만** — 후속 정책 보정 자료, 이번 deterministic gate 대체 아님.

### CI (TCP-16, TCP-18)
- **D-05:** `.github/workflows/ci.yml` 확장(재구현 금지): schemas·router·transition/concurrency·context gate·evidence/handoff·emit parity/drift·기존 full-suite fan-in job + lifecycle eval job. 기존 gate(pytest·contract-drift·golden·stale-derived·GEN-04·emit-drift·모델 식별자 lint) green 유지.

### 문서·ADR (TCP-18) — 사람-owned
- **D-06:** `docs/how-to/task-lifecycle.md` 추가(Diátaxis how-to). generator-owned 영역과 human-owned 영역 명확 구분.
- **D-07:** 구조 ADR **0008**(Task Control Plane의 namespace·authority·lifecycle·overlay 결정). **agent가 작성하되 승인 금지 — 사람 승인 없이 구조 결정 미확정.** append-only. CODEOWNERS(docs/adr/) 게이트. Claude는 draft를 제출하고 **사용자 ratification을 요청**한다.

### 헌법 정합
- **D-08:** fixture·runner는 domain-neutral core. 새 계약 생기면 dev draft + 재해시(단 breaking은 ADR 동반). 모델 식별자 없음. byte hygiene. emit-drift 0. constitution-plane(adr) 변경은 사람 승인 확인.

### 실행 위임
- **D-09:** 구현 **codex terra medium (fast off, headless)**. 리뷰 **교대 → sol**(P22=sol 초기+fable 확인; 이번 순번 sol). 단 negative fixture가 secret/forgery/exploit-shaped라 codex content-filter 위험 → 해당 부분은 fable. Claude 검증/머지. ADR·expected-lane ratification은 **사용자 게이트**. 참조 [[design-and-gsd-via-codex-sol]].
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 설계 정본
- `docs/explanation/next-milestone-task-control-plane.md` §Phase 6 — 산출물·책임경계·완료기준 1~13 정본.
- `.planning/REQUIREMENTS.md` TCP-16,17,18 + Out of Scope(production 통계 위장 금지, shadow는 보정자료).
- `.planning/ROADMAP.md` "Phase 23" success criteria 5개.

### 검증 대상 (Phase 18–22 전 계층)
- `tools/task_packet`(P18 packet), `tools/risk_router`+`harness/risk-policy.toml`(P19 lane), `tools/task_control`(P20 state/transition/phase-gate), `tools/evidence`(P21 evidence/registry), `tools/handoff`+`tools/hooks/resume_gate.py`(P22 handoff/resume-gate).
- `contracts/harness/task-control/*` 전부.

### 헌법·관례
- `docs/adr/`(0001–0007 존재, 신규 0008), `docs/adr/README.md`, `docs/how-to/README.md`, `.github/workflows/ci.yml`, CODEOWNERS(adr/·contracts/·golden/). `tools/harness_emit`(emit-drift), stale-derived·GEN-04 가드.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 18–22 도구 전부 — 이번엔 조합해 E2E fixture로 굳힘, 재구현 없음.
- 기존 CI `ci.yml`: dotnet/python/contract-check/golden job 구조 — lifecycle eval job 추가만.
- 기존 negative 검증들(P20 concurrent writer, P21 tamper, P22 stale handoff/wrong worktree)이 이미 단위 테스트로 존재 — fixture로 승격·통합.

### Established Patterns
- 순수·결정론 + 정렬·해시. fixture는 재현가능·ratified. shadow 지표는 정의만.
- 헌법 평면(adr)은 gate-model: agent draft, 사람(CODEOWNERS) ratify — 이번 ADR이 그 경로를 실제로 밟는 대표 사례.

### Integration Points
- lifecycle eval runner ↔ 전 도구. CI fan-in ↔ 기존 job. ADR ratification ↔ 사용자.
</code_context>

<specifics>
## Specific Ideas

- 완료기준: 설계 §Phase 6 완료기준 1~13 승격 — 20 fixture ratified lane 정확일치, false downgrade 0, FAST 상한(intake+verify), STRICT/CONTROLLED 독립review+rollback, buried-constraint prohibited action 차단+required evidence, tampered/missing evidence·stale handoff COMPLETE 전 차단, wrong worktree/ref·concurrent stale writer 실행 전 차단, 전체 pytest 회귀 0, contract-drift/golden/stale-derived/GEN-04 green, emit-drift 0, 모델 식별자 lint green, 사람 승인 ADR+constitution 변경 확인.
- 20 fixture는 사용자에게 expected lane 표로 제시해 ratify 받는다(자가승인 금지).
</specifics>

<deferred>
## Deferred Ideas (v2.2 이후)

- Signed external evidence attestation(P21 D-10) — Future Requirement.
- TCP-F01..F05(skill layer, adversarial panel, agent allowlist, registry.lock, instance overlay) — 후속 마일스톤.
- Production shadow 지표 실측·정책 보정 — 이번엔 정의만.
</deferred>
