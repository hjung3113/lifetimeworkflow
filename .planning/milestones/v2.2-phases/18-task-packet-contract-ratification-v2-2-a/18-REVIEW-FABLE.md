# Phase 18 적대적 리뷰 — HEAD 0beb703

리뷰 범위: `git show HEAD` 전체 diff + 18-CONTEXT D-01~D-11 + 설계 §4 Phase 1 완료기준 1~9 + TCP-01/02 + ROADMAP Phase 18. 정적 검토 — 세션 sandbox가 `uv run pytest`/`python3` 실행 거부해서 테스트 스위트 직접 실행 못함(아래 regex 결함은 손분석으로 확정, ECMA/Python `re` 공통 semantics).

전반 판정: 구조 건전. schema 4종 Draft 2020-12 형식·enum·ID 포맷 D-06~D-10 일치, 헌법 규율(모델 식별자·gitignore·CODEOWNERS·derived 분류) 위반 없음. 실결함 2건(major), 테스트 약점 다수(minor).

---

## Major

### M-1. `evidence` artifact path의 traversal 차단 regex가 선두 `..` 세그먼트를 통과시킴
**`contracts/harness/task-control/evidence.schema.json:73`**

```
"pattern": "^artifacts/(?!.*(?:^|/)\\.\\.(?:/|$)).+$"
```

- lookahead가 `artifacts/` **뒤** 위치(pos 10)에서 평가됨. `(?:^|/)`의 `^` 대안은 문자열 시작(pos 0)에서만 매치 가능 → lookahead 안에서 죽은 분기.
- 결과: `..` 앞에 `/`가 있어야만 거부됨. **`artifacts/../task.json`, `artifacts/..` 는 schema 통과** (`artifacts/a/../b`, `artifacts/../../x`는 거부 — `/..`가 존재하니까). packet 루트로 탈출해 mutable `state.json`/`task.json`을 "immutable artifact"로 가리킬 수 있음 — Phase 21 evidence 변조탐지 전제 훼손.
- 대비: `task.schema.json:103` repoPath는 같은 패턴이지만 lookahead가 pos 0에 있어 `^` 분기가 살아 있음 → `../x` 정상 거부. 비대칭이 의도(모든 `..` 세그먼트 차단)와 버그를 동시에 증명.
- **권고:** `"^artifacts/(?!(?:.*/)?\\.\\.(?:/|$)).+$"` 로 교체(선두+중간 `..` 모두 커버), negative fixture `artifacts/../x` 추가. schema 변경이니 manifest 재해시 + 사람 승인 경로로.

### M-2. 허용 전이표(D-07 산출물)가 헌법 평면 밖 코드에만 존재 — drift gate 미적용
**`tools/task_packet/transitions.py:26-63`**

- CONTEXT·ROADMAP SC1 모두 "phase/lane enum + **허용 전이표**"를 이 phase의 ratification 산출물로 명시. enum은 schema(→ hash gate, CODEOWNERS)에 박혔지만 전이표는 `tools/` 파이썬 상수 — `contracts/` 해시도 CODEOWNERS `/contracts/` 규칙도 안 걸림. 에이전트가 `_STANDARD`에 edge 하나 추가해도 어떤 게이트도 안 울림 → "shape를 코드보다 먼저 사람 승인으로 고정한다"는 phase 목적을 전이표에 한해 미달. `PHASES` frozenset도 schema enum 복제(transitions.py:5) — 이중 정본.
- **권고:** 전이표를 `contracts/harness/task-control/transitions.json`(lane→edge 목록) 데이터로 승격해 manifest 등록, `transitions.py`는 로드만. 최소한 schema enum ↔ `PHASES` 일치 + 전이표를 contract-side fixture에 핀하는 테스트 추가.

## Minor

### m-1. `invalid-task-timestamp` negative 테스트가 비격리 — timestamp 검증 삭제해도 green
**`tools/task_packet/tests/fixtures/negative/cases.json:2-6` + `test_task_packet.py` (`test_negative_fixtures_are_rejected`)**

fixture가 `task.task_id`만 `T-20261340000000-…`로 바꾸고 state/evidence/handoff는 옛 ID 유지 → `_validate_task_id`를 지워도 cross-doc `task_id does not match`가 어차피 `PacketValidationError`를 던져 테스트 통과. D-09 timestamp 검증이 테스트로 증명 안 됨. **권고:** 4개 문서 모두 같은 invalid ID로 세팅하거나, 예외 메시지 매칭(`match="invalid UTC timestamp"`) 추가.

### m-2. deletion-independence 테스트 2종이 구조적으로 실패 불가능(tautology 성향)
**`test_task_packet.py:1328-1350`**

- memory 쪽: `tmp_path/.memory/state`를 만들고 지우지만 `validate_packet`은 packet dir + `REPO_ROOT` schema만 읽음 — 삭제가 영향 줄 경로 자체가 없음.
- derived 쪽: contracts 사본에서 `contracts_index`만 재생성 — SessionStart 재생성의 나머지(repo-map, pointer-index) 미커버. 완료기준 8의 "기존 SessionStart derived regeneration"을 contracts_index 하나로 대변.
- 미래 결합 도입 시 회귀 감지용으로는 유효하니 유지하되, **권고:** repo-map/pointer-index 재생성도 같은 방식으로 커버 + VERIFICATION에 "proxy 테스트"임을 명시.

### m-3. 완료기준 2의 "exit non-zero" 미검증
**`tools/task_packet/validate.py:1610-1620`** — 테스트 전부 `PacketValidationError` 예외 단정, `main()` CLI 경로(반환 1/0, stderr FAIL) 무테스트. 기준 문언은 exit code다. **권고:** `main([str(packet)])` 반환값 테스트 1~2개.

## Nit

- **n-1.** `state.completed_items` dangling criterion 경로와 `_ids` 중복-ID 거부(validate.py:1519-1523)에 fixture/테스트 없음 — validator는 구현돼 있음.
- **n-2.** `test_core_contracts_and_fixtures_are_domain_neutral`는 도메인 용어만 검사. 설계 §"모델 식별자 금지"는 fixture/code도 대상인데 모델·provider 문자열 검사는 없음(현재 위반물은 없음 — 전 diff 육안 확인).
- **n-3.** `docs/reference/task.md`·`state.md` 등 generic stem이 공유 namespace 최상위 점유 — 동명 contract 등장 시 충돌. docs_sync 쪽 이슈라 이번 phase 범위 밖.

## 헌법·완료기준 체크 결과 (결함 아님, 확인 사항)

- **모델 식별자:** 커밋된 파일·메시지에 없음. `REVIEW_FABLE.md`는 untracked, 이 커밋 산출물 아님.
- **byte hygiene:** LF/no-BOM 자가 테스트(`test_task_control_files_are_lf_utf8_without_bom`) 존재. 단 `docs/reference/*.md`·PLAN 문서는 검사 목록 밖(format hook이 커버).
- **contracts draft-only:** D-05 준수 — dev 브랜치 draft, 커밋 메시지에 명시, CODEOWNERS `/contracts/` 재귀 매치 확인. validator는 schema를 contracts/에서 live-load, 어떤 완화·내장 사본도 없음.
- **`.workflow/tasks` 평면 분류:** `.gitignore` 미등록 + 전 파일 tracked → committed volatile 맞음(D-02). README가 책임 경계(D-03) 정확히 기술.
- **manifest/index 정합:** 4개 hash가 `contracts/.hashes/manifest.json`·contracts-index·syrupy snapshot 3곳 일치, 세션 라이브 drift `clean`.
- **완료기준 1~9:** 1·3·4·6·9 충족, 2·7·8은 위 m-1~m-3의 약점 딸린 채 형식상 충족, 5는 "실행 phase 진입 거부"를 schema-required 거부로 대리(진입 게이트 자체는 Phase 20 소관 — 범위상 타당).

**결론:** merge 전 M-1은 schema 수정 필수(사람 승인 동반), M-2는 이 phase에서 고치거나 Phase 20 전이 게이트 전에 계약화한다는 명시적 결정(ADR 한 줄이라도) 필요. minor는 후속 커밋 가능.
