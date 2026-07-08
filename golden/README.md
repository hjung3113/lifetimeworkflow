# 골든 파일(동등성) 세트 — 헌법 평면 (TOP-LEVEL)

*owner: TBD · status: draft (seed placeholder)*

> **위치 규약 (locked, D-06/D-07):** `golden/`은 `contracts/`의 **형제인 최상위(top-level) 헌법-평면
> 디렉터리**다 — `contracts/golden/`이 아니다. 헌법 평면 = `contracts/` · `golden/` · `adr/` · `glossary`
> (사람 소유, CODEOWNERS 게이트). 이 README 내용은 parserimprove monorepo_skeleton의 golden README에서
> 시드로 복사했으나, 그 `contracts/` 하위 중첩은 복사하지 않았다(레포 헌법 레이아웃이 top-level `golden/`로 고정).

전환 검증의 핵심. 실제 로그 파일을 입력으로, **기존 파서 출력 vs 신규(컨버터+표준파서) 출력**을 diff해
*의도한 차이만 존재하고 의도치 않은 차이는 없는지* 검증한다. byte-diff가 아니라 §4.3–4.6 정규화 코어를
통과시킨 뒤 비교한다(P4: BOM/CRLF/소수점-로케일/TZ 차이는 중화, 실차이는 살린다).

## 구성 (스켈레톤)

```txt
golden/
  <case_id>/
    input/          실제 로그 원본 (비민감·소량)
    expected/       기존 파서 기준 출력 (.received = 기계 제안 · .verified = 사람 승인)
    meta.yaml       설비/모델/메이커, 의도된 차이 허용 목록
```

## 규칙

- 가공 로직(컨버터·표준파서·정규화·보정) 변경 PR은 골든테스트 통과가 1급 검증.
- 의도된 차이는 `meta.yaml`에 명시(허용), 그 외 diff는 실패.
- **민감정보·크리덴셜·실데이터 커밋 금지.** 샘플은 소량·비민감 (T-02-01 / ASVS V12).
- **machines gate, humans ratify (P9):** `.received`→`.verified` 승격은 사람 승인만. 에이전트 self-bless
  금지. 승격은 ADR/rationale 링크를 동반한다. (하드 강제 CODEOWNERS/플러그인 = Phase 4/5.)

> 상세 전략: parserimprove `parser_project_revised.md` §5.1.
