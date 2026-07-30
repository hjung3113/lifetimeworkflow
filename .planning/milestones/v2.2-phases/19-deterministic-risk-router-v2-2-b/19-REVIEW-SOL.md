# 적대적 리뷰 결과 — HEAD `7a78937`

## Blocker

없음.

## Major

### 1. CONTROLLED 승격이 STRICT의 필수 산출물을 삭제한다

- 위치: [harness/risk-policy.toml](/Users/hyojung/orca/workspaces/lifetimeworkflow/phase19-riskrouter/harness/risk-policy.toml:29), [test_router.py](/Users/hyojung/orca/workspaces/lifetimeworkflow/phase19-riskrouter/tools/risk_router/tests/test_router.py:141)
- 근거:
  - STRICT에는 `review_record`가 필수지만 CONTROLLED에는 없다.
  - 따라서 STRICT 점수에서 `payment` 승격을 걸거나, overlay로 STRICT→CONTROLLED 승격하면 lane은 올라가면서 `review_record`가 사라진다.
  - 직접 재현 결과:
    - STRICT: `plan, review_record, spec, task_packet`
    - CONTROLLED: `audit_evidence, plan, rollback_plan, spec, task_packet`
  - 테스트는 lane이 그대로인 경우에만 artifact/gate superset을 검사해 이 결함을 정확히 우회한다.
- 영향: “승격은 절차를 약화하지 않는다”, “effective ≥ core”, plan의 monotonic matrix를 위반한다.
- 권고: 상위 lane matrix를 누적 superset으로 만들거나, 라우팅 시 도달 lane까지 하위 lane 요구사항을 합집합한다. 모든 lane 상승 및 overlay 승격에 대해 artifact/gate superset을 검증해야 한다.

### 2. overlay가 있으면 `decide()`가 repository 파일을 읽으므로 순수 함수가 아니다

- 위치: [router.py](/Users/hyojung/orca/workspaces/lifetimeworkflow/phase19-riskrouter/tools/risk_router/router.py:95), [router.py](/Users/hyojung/orca/workspaces/lifetimeworkflow/phase19-riskrouter/tools/risk_router/router.py:199)
- 근거: `decide(core, payload, overlay)`가 `validate_overlay()`를 호출하고, 그 내부에서 전역 경로 `overlay.schema.json`을 매번 읽는다.
- 영향: 동일한 함수 입력과 policy/overlay hash라도 schema 파일의 존재·내용·접근권한에 따라 성공/실패가 달라진다. D-01의 repo 미접근 및 순수 함수 조건을 직접 위반한다.
- 권고: 파일/schema 검증은 load 경계에서 끝내고, 순수 evaluator에는 검증된 policy data만 전달한다. schema 자체가 계산 입력이라면 명시적으로 주입하고 hash 범위에도 포함해야 한다.

### 3. golden/계약 변경을 CONTROLLED로 보낼 표현력이 없다

- 위치: [risk-policy.toml](/Users/hyojung/orca/workspaces/lifetimeworkflow/phase19-riskrouter/harness/risk-policy.toml:17), [intake.md](/Users/hyojung/orca/workspaces/lifetimeworkflow/phase19-riskrouter/harness/commands/intake.md:17)
- 근거:
  - `external_contract_break = STRICT`
  - `constitution_plane_touch = STRICT`
  - intake가 받을 수 있는 flag도 이 두 broad reason뿐이다.
  - D-04는 일반 헌법 접촉은 최소 STRICT이되, golden/계약 변경은 CONTROLLED라고 명시한다.
- 영향: contracts 또는 golden 변경을 `constitution_plane_touch`로 입력하면 STRICT에서 멈출 수 있다.
- 권고: golden/contract mutation을 구별하는 결정론적 reason code를 추가해 CONTROLLED로 매핑하거나, 기존 입력 shape 안에서 그 subtype을 명시적으로 표현한다.

### 4. `/intake`의 packet 생성 성공 기준이 구현·검증되지 않았다

- 위치: [intake.md](/Users/hyojung/orca/workspaces/lifetimeworkflow/phase19-riskrouter/harness/commands/intake.md:27), [intake.md](/Users/hyojung/orca/workspaces/lifetimeworkflow/phase19-riskrouter/harness/commands/intake.md:31)
- 근거:
  - 실행 블록은 stdin payload 없이 `uv run python -m tools.risk_router`만 호출한다.
  - 이후 packet 생성은 “Create…”라는 에이전트 prose 지시로 위임된다.
  - “policy hashes와 promotion reasons를 intake record에 보존”하라고 하지만 Phase 18 task schema에는 해당 필드나 `intake record` artifact가 정의돼 있지 않다.
  - 테스트도 router와 emit 개수만 검사하며 `/intake` 입력→유효 packet 생성 E2E fixture가 없다.
- 영향: ROADMAP success criterion 4와 D-09를 관찰 가능하게 입증하지 못한다. 런타임마다 에이전트가 서로 다른 저장 방식을 선택할 수 있다.
- 권고: decision 저장 위치/shape를 명시하고, `/intake`가 실제 Phase 18 packet을 생성한 뒤 validator를 통과하는 E2E fixture를 추가한다.

## Minor

### 5. overlay provenance가 구현되지 않았다

- 위치: [overlay.schema.json](/Users/hyojung/orca/workspaces/lifetimeworkflow/phase19-riskrouter/tools/risk_router/overlay.schema.json:3), [router.py](/Users/hyojung/orca/workspaces/lifetimeworkflow/phase19-riskrouter/tools/risk_router/router.py:230)
- 근거: schema에는 provenance 필드가 없고 decision에는 content hash만 있다. overlay source나 project slot provenance는 보존되지 않는다.
- 권고: host-independent repo-relative source identifier와 content hash 등 최소 provenance를 정의하고 decision/audit record에 남긴다.

### 6. 동등 lane human override의 audit reason이 조용히 사라진다

- 위치: [router.py](/Users/hyojung/orca/workspaces/lifetimeworkflow/phase19-riskrouter/tools/risk_router/router.py:213)
- 근거: override가 현재 lane보다 높을 때만 `promotion_reasons`에 추가된다. 같은 lane에 audit reason을 제출하면 출력에 남지 않는다.
- 권고: 하향은 계속 거부하되, 동등/상향 override reason은 별도 audit record로 항상 보존한다.

### 7. 결정론·모델 식별자 테스트가 완료기준보다 얕다

- 위치: [test_router.py](/Users/hyojung/orca/workspaces/lifetimeworkflow/phase19-riskrouter/tools/risk_router/tests/test_router.py:53), [test_router.py](/Users/hyojung/orca/workspaces/lifetimeworkflow/phase19-riskrouter/tools/risk_router/tests/test_router.py:58)
- 근거:
  - byte-identical 테스트는 같은 객체로 같은 함수를 연속 두 번 호출하는 사실상 반복 assert다.
  - dict 삽입 순서 변화, 별도 프로세스, overlay, 환경 변화는 다루지 않는다.
  - 모델 검사는 한 decision 문자열의 `model`/`provider` substring만 검사하며 policy·overlay·fixture 전체를 검사하지 않는다.
- 권고: key-order permutations, subprocess 반복, core/overlay 양쪽 hash fixture를 추가하고, 대상 policy/output/fixtures 전체에 capability-neutral lint를 적용한다.

### 8. BOM 입력 hygiene가 root invariant와 맞지 않는다

- 위치: [__main__.py](/Users/hyojung/orca/workspaces/lifetimeworkflow/phase19-riskrouter/tools/risk_router/__main__.py:27)
- 근거: `encoding="utf-8"`로 읽은 뒤 `json.loads(str)`를 호출하므로 UTF-8 BOM이 제거되지 않고 JSON decode가 실패한다.
- 권고: 입력 경계에서 BOM을 명시적으로 strip하고 CRLF/LF fixture도 추가한다. 출력 자체는 정렬 JSON, ASCII escape, 단일 LF로 안정적이다.

## Nit

### 9. 새 snapshot 때문에 `git diff --check`가 실패한다

- 위치: [test_emit_determinism.ambr](/Users/hyojung/orca/workspaces/lifetimeworkflow/phase19-riskrouter/tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr:1393)
- 근거: 새 snapshot 구간에 trailing whitespace가 24곳 추가됐다.
- 권고: snapshot 포맷상 불가피한지 확인하고, 가능하면 공백만 있는 줄을 정리한다.

## 정상 확인 사항

- cut 경계 `0–4 / 5–9 / 10–14 / 15–21`는 정확하다.
- 점수 lane보다 높은 자동 승격과 human override 하향 거부는 동작한다.
- scores, flags, artifact/gate 출력 순서는 명시적으로 정렬돼 있다.
- 현재 커밋 대상 policy/output fixture에서 실제 모델 ID는 발견되지 않았다.
- `tools/risk_router`와 core policy에서 `examples/` 직접 참조는 발견되지 않았다.
- FAST는 현재 `task_packet + lint/test`만 요구한다.
- `/intake`는 harness source와 양 runtime projection에 포함돼 있다.

테스트 실행은 read-only 환경에서 임시 디렉터리와 uv cache를 만들 수 없어 시작 전에 실패했다. 코드 수정은 하지 않았다.
