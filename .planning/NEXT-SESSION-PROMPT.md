# 다음 세션 핸드오프 — v2.7 마일스톤 시작

> 이 파일은 다음 세션 시작 시 붙여넣을 프롬프트다. 아래 `## 붙여넣을 프롬프트` 블록만 복사하면 된다.
> 작성: 2026-07-30, v2.6 종료 직후.

---

## 붙여넣을 프롬프트

```
/gsd:new-milestone
```

위 커맨드 실행 후, 아래 컨텍스트를 참고해서 v2.7을 스코핑해줘.

### 지금 상태 (v2.6 종료 시점)

- **v2.6 Minimal Monorepo Core 완료 및 아카이브** (2026-07-30). 페이즈 47·48·49·50a 완료,
  **50b는 BLOCKED 이월**. 요구사항 11/12 (MONO-01..11), 테스트 **981개 통과**.
- `.planning/REQUIREMENTS.md`는 **의도적으로 없음** — 마일스톤과 함께 아카이브됨.
  `/gsd:new-milestone`이 새로 만든다.
- `.planning/phases/`는 **비어 있음**. 이전 마일스톤 페이즈 디렉터리 전부
  `.planning/milestones/v*-phases/`로 정리됨.
- 브랜치 `claude/data-pipeline-harness-8aypct`는 푸시됨. **PR #7 열려 있음**
  (`https://github.com/hjung3113/lifetimeworkflow/pull/7`) — 머지 여부는 아래 참조.
- 태그 `v2.6`은 **로컬만** 존재, 원격 미푸시 (의도적).

### 먼저 확인할 것 (세션 시작 시)

1. **PR #7 상태.** `gh pr view 7 --json state,mergeable` — 머지됐는지, CI가 그린인지 확인.
   v2.6 종료 시점에 `lint` 잡(ruff ratchet)이 붉었고 수정 커밋이 들어갔다. 아직 열려 있으면
   `gh pr checks 7`로 전체 잡 확인부터.
2. **로컬-원격 동기화.** `git status -sb`. 머지됐다면 main 기준으로 새 브랜치를 딸지 결정.
3. **`/orient`** 실행 — 파생 평면 재생성 + 읽기 순서 확인.

### v2.7 후보 인풋 (이미 기록된 것들)

우선순위 판단은 오너 몫. 아래는 v2.6이 남긴 실제 잔여물이다.

**A. MONO-12 / 페이즈 50b — 관리형 `/adopt` (BLOCKED, 이월)**
- 하드 **외부** 전제조건: **실제 멀티패키지 타깃 레포**. 코드는 빠진 게 없다.
- 이 체크아웃엔 합성 픽스처뿐 (`tools/adoption_apply/tests/fixtures/{polyglot-single,
  client-server,partial-collision-crlf}` + `workspace.toml`의 2-멤버 데모).
- `/adopt`는 타깃 레포에 **파일을 쓴다**. 그래서 v2.6에서는 머신에 있던 무관한 레포를
  타깃으로 징발하지 않았다. **타깃 레포를 지명하면 바로 풀린다.**
- 성공 기준 3개 그대로 유효: 매니페스트가 관리 파일을 기록 / 재실행은 업데이트이고 변경 없으면
  no-op / 분기된 관리 파일은 **충돌 보고 후 미변경**.

**B. v2.6이 수락한 기술부채** (`.planning/v2.6-MILESTONE-AUDIT.md`)
- `"dir"`-키 필터 어댑터가 `tools/harness_config/loader.py:conventions_for()`와
  `tools/contract_graph/impact.py:report()`에 **복사 중복**. 현재 갈라지지 않았음이 라인 단위로
  검증됐지만, 도크스트링 상호참조와 행위 테스트 외에 구조적 방지책이 없다. **공유 헬퍼로 추출**이
  가장 값싼 개선.
- `/impact`가 그래프가 빈 동안 **오타 경로와 추적되지만 미배선된 컨트랙트를 구분 못 함**.
  관계 레코드가 생기면 `searched` 후보 목록으로 갈라진다.
- 인용 게이트는 **펜스 코드블록 면제**, 숫자 범위 인용은 앵커가 범위 안에 있는지만 확인(내용
  정확 매칭 아님). 문서화된 사각지대.

**C. 장기 이월**
- **EVOL-02** 컨트랙트 버저닝/호환성 엔진 — 독립 ADR이 필요한 단독 엔진. 계속 이월 중.
- **D-24** 이 레포의 CODEOWNERS 어드바이저리 — 골든 베이스라인 diff에 대한 머신측 체크로
  재개 가능하지만, 무증식 제약상 뭔가 은퇴 없이 게이트 추가는 모순. 문서화된 잔여물.

**D. 프로세스에서 드러난 것 (v2.7 스코핑 시 고려)**
- v2.6에서 **적대적 리뷰 4회가 페이즈 검증이 통과시킨 치명 결함 8건을 잡았다.** 검증과 리뷰는
  다른 일을 한다는 실증. 리뷰 단계를 줄이는 방향은 데이터가 반대한다.
- **세션 게이트에 ruff ratchet이 빠져 있었다.** v2.6 내내 `uv run pytest`는 돌렸지만
  `uv run python -m tools.ruff_baseline`은 안 돌려서, CI에서야 위반 23건이 드러났다.
  `/verify-work`가 이미 lint를 포함하는데 페이즈 실행자들이 그걸 안 거쳤다 — **핸드오프 전
  게이트를 실제로 실행하게 만드는 것**이 후보 개선 항목.

### 지켜야 할 제약 (v2.5부터 이어짐, v2.6에서도 유지됨)

- **무증식**: 검증 게이트·보안 레이어·세리모니를 추가해 목적 범위를 넘기지 말 것.
  "X도 게이트할까?"의 기본 답은 **NO**. 최소 같은 양을 은퇴시키지 않으면 표면은 커지지 않는다.
- 현재 표면: **커맨드 19개, 스킬 8개**, 컨트랙트 6개. 파생 평면은 손으로 편집 금지.
- 컨트랙트 우선. GEN-04: `tools/`·`harness/`·`libs/` 어디에도 `examples/` 리터럴 금지
  (테스트·도크스트링 포함).
- 레포 산출물(커밋·PR·코드 코멘트)에 **모델 식별자 미포함**.
- `harness/`만 손으로 authoring, `.opencode/`·`.claude/`는 재-emit으로만 변경.

### 참고 파일

- `.planning/PROJECT.md` — Current State + Next Milestone Goals
- `.planning/milestones/v2.6-ROADMAP.md` — v2.6 전체 상세
- `.planning/v2.6-MILESTONE-AUDIT.md` — 감사(상태 `tech_debt`, 갭 0)
- `.planning/STATE.md` — 블로커/기술부채 목록
- `AGENTS.md` — 이 레포의 정본 규칙
