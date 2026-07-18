# Phase 21: Evidence Bundle Adapters - Context

**Gathered:** 2026-07-19
**Status:** Ready for planning

<domain>
## Phase Boundary

"실행했다"는 서술을 기존 게이트의 **실제 결과에 연결된 위조 탐지 가능 증거**로 바꾼다. 검증 로직(lint·test·contract-drift·golden·freshness·`/verify-work` 5-gate)은 **재구현하지 않고 감싸서 수집만** 한다. 산출: `tools/evidence/` capture adapter — command ID·normalized argv·exit code·status·artifact path·SHA-256·gate version 기록, `PASSED/FAILED/SKIPPED/BLOCKED` 엄격 분리, acceptance-criterion ↔ evidence 양방향 trace, review finding severity/disposition/evidence ref, secret/PII refusal + redaction report, 기존 `/review`·`/verify-work`에 adapter 배선. **요구사항 TCP-11, TCP-12, TCP-13.** handoff snapshot은 Phase 22, lifecycle eval/ADR은 Phase 23 — 범위 밖.
</domain>

<decisions>
## Implementation Decisions

> `--auto` 단일 패스. 정본: 설계 §Phase 4. Phase 18 evidence.schema.json + Phase 20 상태도구(transition/gate가 evidence coverage를 소비)를 소비·확장.

### 수집 무재구현 (TCP-11)
- **D-01:** adapter는 lint·test·contract-drift·golden·freshness 로직을 **재구현 금지** — 기존 명령을 child process로 실행하고 command ID·normalized argv·exit code·start/end marker·gate version·artifact path·SHA-256만 기록. exit code는 **실제 child 결과에서만** 채운다(합성 금지).
- **D-02:** status ∈ `{PASSED, FAILED, SKIPPED, BLOCKED}`. skip reason과 pass를 엄격 분리 — **SKIPPED를 PASSED로 승격 불가**. presence-safe no-op/skip은 기존 명령의 결과를 그대로 기록. 실행 안 한 gate는 PASSED 등록 불가.
- **D-03:** raw stdout/stderr는 **artifact 파일로 저장**, packet(evidence.json)에는 경로·요약·SHA-256만. artifact는 Phase 20 immutable run-ID 규칙(orphan 진단 대상) 따름.

### criterion·finding trace (TCP-12)
- **D-04:** acceptance-criterion ↔ evidence **양방향 trace**. 필수 criterion에 passing evidence 없으면 VERIFY 완료 거부(Phase 20 `_evidence_covers_*` 소비 지점 연동). artifact 1 byte 변조 시 hash 검증 실패.
- **D-05:** review finding에 severity·disposition·evidence reference 기록. unresolved blocker/major finding 있으면 COMPLETE 전이 거부. **evidence.schema.json 확장 필요**(finding에 severity/disposition/evidence_ref, gate_run에 argv/exit_code/gate_version/started_at/ended_at 등) → dev draft + `python -m tools.contract_hash` 재해시 + contract-drift 재기준.

### 보안·경계 (TCP-13)
- **D-06:** secret/credential/PII 패턴을 evidence·artifact·HANDOFF **평문 기록 전 탐지→명시적 거부(fail-closed) + redaction report**. 탐지 못 한 값이 평문으로 새는 경로 없어야 함. 로컬 evidence와 CI reference를 명시적으로 구분(source 필드).

### 헌법·게이트 보존
- **D-07:** 기존 `/verify-work` 5-gate 의미·실행 순서 유지, FAST 비용 절감 이유로 내부 gate 제거 금지. 기존 5-gate regression test 그대로 통과. constitution-plane diff는 도구 pass와 별개 human approval evidence 요구(없으면 완료 거부) — 기계 판정 가능 범위만(approval reference 존재·shape), "승인했다" 주장 금지.
- **D-08:** tools는 domain-neutral Python core. evidence는 `.workflow/tasks/` 인스턴스에 write, `.memory/derived` 아님. adapter가 명령 배선하는 커맨드 소스(`/review`·`/verify-work`)는 harness/ 에서 emit(직접편집 금지). 모델 식별자 없음. byte hygiene(LF·no-BOM, 입력경계 BOM strip).
- **D-10 (Phase 21 reverify):** evidence anchor writes use the state CAS revision/lock and COMPLETE additionally requires `evidence.json` byte-identical to its tracked `HEAD` blob. This closes in-session task-directory forgery under the no-agent-commit trust root. A signed external attestation/token remains deferred to Phase 23 lifecycle evaluation; Phase 21 does not claim to provide it.

### 실행 위임
- **D-09:** 구현 **codex terra medium (fast off, headless)**. 리뷰 **교대 → sol**(P20=fable). Claude 검증/머지. 표준 러너 `scratchpad/run_agent.sh`. 참조 [[design-and-gsd-via-codex-sol]].
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 설계 정본
- `docs/explanation/next-milestone-task-control-plane.md` §Phase 4(Evidence Bundle Adapters) — 산출물·책임경계·완료기준 1~9 정본.
- `.planning/REQUIREMENTS.md` TCP-11..13 + Out of Scope(gate 재구현 금지·5-gate 보존).
- `.planning/ROADMAP.md` "Phase 21" success criteria 4개.

### 소비·확장 대상 (Phase 18/20)
- `contracts/harness/task-control/evidence.schema.json` — gate_runs(id/gate/status/criterion_ids/finding_ids/artifact) + findings(id/summary/constraint_ids). **확장 지점.**
- `contracts/harness/task-control/{task,state}.schema.json`, `transitions.json` — VERIFY/COMPLETE 전이 요건.
- `tools/task_control/manager.py` `_evidence_covers_*` — evidence coverage 소비(이 phase가 채운다).
- `harness/commands/{verify-work.md,review.md}` — adapter 배선 대상.

### 헌법·관례
- `AGENTS.md`(root), `tools/task_packet`·`tools/risk_router`·`tools/task_control`(결정론·순수·해시 규율), `tools/harness_emit/`(커맨드 emit + emit-drift), `tools/polyglot_lint`(byte hygiene).
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 20 `tools/task_control`: evidence schema 검증·coverage 판정 경로 이미 존재 — 이 phase가 실제 capture로 채운다.
- Phase 18 evidence.schema.json: 기본 shape. severity/disposition/argv/exit_code/redaction 확장.
- 기존 SHA-256/canonical serialize 관례(P18/19/20 검증기): artifact hash·argv 정규화에 재사용.

### Established Patterns
- 순수·결정론 + 정렬·해시. capture adapter는 부수효과(child spawn) 있으나 재현가능·위조탐지.
- 헌법 평면 write는 gate-model(agent draft, CODEOWNERS ratify). evidence.schema 확장은 dev draft.

### Integration Points
- adapter ↔ 기존 `/verify-work`(5-gate)·`/review`: 감싸기만, 순서·의미 보존.
- Phase 20 transition/gate가 evidence coverage 소비, Phase 22 handoff가 evidence ref 소비.
</code_context>

<specifics>
## Specific Ideas

- 완료기준: 설계 §Phase 4 완료기준 1~9 승격 — status round-trip, 1-byte 변조 hash fail, 미실행 gate PASSED 등록 불가, required criterion passing evidence 없으면 VERIFY 거부, unresolved blocker/major finding COMPLETE 거부, constitution diff human-approval ref 없으면 완료 거부, secret fixture 평문 미기록+거부, missing artifact/stale index validation 실패, 기존 5-gate regression 그대로 통과.
- 위조 테스트: 실제 pass/fail/skip/blocked fixture 4종 + artifact 변조 fixture + secret/PII fixture.
</specifics>

<deferred>
## Deferred Ideas

- Handoff snapshot·fresh-session resume(22), lifecycle fixture·ADR·CI(23).
- CI reference evidence 실제 업로드/대조 파이프라인은 shape·구분만(실배선은 23 CI).
</deferred>
