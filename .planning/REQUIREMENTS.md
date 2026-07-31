# Requirements — v2.7 Real-Target Adoption

> Scope: 하네스를 **실제 외부 모노레포**에 도입해서, 새 기계를 짓는 대신 **현실이 무엇을 깨뜨리는지
> 관측하고 그것만 수리**한다. 타깃은 `~/Desktop/2026/FeedbackOps`의 격리된 git 워크트리
> (pnpm workspace + turbo, root + `packages/{ui,shared}` + `apps/{frontend,backend}`, 전부 JS/TS).
>
> 이월 후보 7개 중 4개는 자기-하드닝, 1개는 투기적 인프라로 판정되어 스코프에서 제외됐다 —
> 근거는 `.planning/PROJECT.md`의 *Why this and not more machinery*.

## v2.7 Requirements

### A. 격리 도입 (RTA)

- [ ] **RTA-01**: 개발자가 FeedbackOps의 격리된 git 워크트리를 타깃으로 `/adopt`를 실행할 수 있고,
  원본 `develop` 체크아웃은 한 바이트도 바뀌지 않는다.
- [x] **RTA-02**: `/adopt` discover 단계가 실제 pnpm 워크스페이스 멤버 5개(root · `packages/ui` ·
  `packages/shared` · `apps/frontend` · `apps/backend`)를 인벤토리에 빠짐없이 올린다.
- [ ] **RTA-03**: 도입 후 타깃에서 package facts가 패키지 간 **실제 의존 엣지**를 산출한다
  (`packages/shared` → `apps/frontend`, `apps/backend`).
- [x] **RTA-04**: 도입 후 타깃의 각 패키지가 lint/test 커맨드를 포함한 nearest-wins 컨벤션 프로파일을
  갖는다.

### B. 관리형 설치/갱신 (이월)

- [ ] **MONO-12**: `/adopt` 재실행이 install이 아니라 update로 동작한다 — 매니페스트가 관리 파일을
  기록하고 / 변경 없으면 **no-op**이며 / 분기된 관리 파일은 **충돌 보고 후 미변경**.
  *(v2.6 phase 50b에서 BLOCKED로 이월된 요구사항. 성공 기준 3개 불변; 막혔던 것은 코드가 아니라
  실제 멀티패키지 타깃의 부재였고 이 마일스톤이 그것을 지명한다.)*

### C. 관측 → 수리 (OBS)

- [ ] **OBS-01**: 도입 중 관측된 결함이 재현 가능한 기록으로 남는다 — 증상 · 재현 경로 · 코드 위치.
- [x] **OBS-02**: 관측 결함 중 목적 ①②③④(패키지별 컨벤션 / 패키지 간 계약 / LLM의 크로스-프로젝트
  이해 / 장기 유지보수)에 해당하는 것이 수리되고 **회귀 테스트**를 갖는다.
- [ ] **OBS-03**: pnpm `workspace:*` 프로토콜 의존성이 버전 문자열이 아니라 워크스페이스 엣지로
  기록된다.
  *(**가설**로 기재 — 관측이 확정하거나 **기각**한다. 기각은 실패가 아니라 이 마일스톤의 산출물이다.
  현재 근거: `tools/adoption_scan/detect.py:46-50`의 매니페스트 인식 5종에 `pnpm-workspace.yaml`이
  없고, `_dependencies_from_package_json`이 `workspace:^`를 버전 문자열로 받을 소지가 있다.)*

### D. 부채 (DEBT)

- [ ] **DEBT-01**: `"dir"`-키 필터 어댑터가 단일 공유 헬퍼가 되고, 두 호출부
  (`tools/harness_config/loader.py:conventions_for()` · `tools/contract_graph/impact.py:report()`)가
  그것을 쓴다. 표면 **감소**.

### E. 제약을 요구사항으로 (NG)

- [ ] **NG-01**: 마일스톤 종료 시 커맨드(19) · 스킬(8) · 컨트랙트(6) · CI 잡 · 게이트 수가 시작 대비
  **증가하지 않는다**. 무증식 제약을 처음으로 측정 가능한 요구사항으로 만든 것 — 위반은 마일스톤
  실패다.

## Future Requirements

- **EVOL-02** — 계약 버저닝 / 호환성 엔진. 별도 ADR이 필요한 단독 엔진. 계약 6개에 버전 스큐 사례가
  아직 0건이라 겪지 않은 문제다. 실사용에서 스큐가 **관측되면** 그때 스코프에 든다.
- **두 번째 타깃 레포 (vocpage)** — FeedbackOps 도입에서 나온 수리의 **재현성** 확인. 첫 도입이
  끝나기 전에는 의미가 없다.

## Out of Scope

- **인용 게이트 / AST 게이트 사각지대 보강** — 게이트로 게이트를 보강하는 일. v2.5가 27k LOC를 지워
  되돌린 실패 모드와 같은 범주.
- **D-24 CODEOWNERS 어드바이저리** — 게이트 추가인데 은퇴시킬 대상이 없다. 무증식 제약 위반.
- **세션 내 ruff 강제장치** — ADR-0012가 CI + 머지를 결정 권한으로 못박았다. 세션 안에 CI를 복제하는
  것은 그 결정을 되돌리는 것이고, 실제 비용은 수정 커밋 1개였다.
- **`/impact`의 모호 거부 수리** — 관계 레코드가 생기면 자동 해소된다. 지금 고치는 것은 없는 문제를
  고치는 것.
- **타깃 레포의 제품 코드 변경** — 도입은 하네스 아티팩트만 쓴다. FeedbackOps의 애플리케이션 코드를
  고치는 것은 이 마일스톤이 아니다.

## Traceability

<!-- filled by the roadmap -->

| REQ-ID | Phase |
|---|---|
| RTA-01 | Phase 52 |
| RTA-02 | Phase 52 |
| RTA-03 | Phase 52 |
| RTA-04 | Phase 52 |
| MONO-12 | Phase 53 |
| OBS-01 | Phase 51 |
| OBS-02 | Phase 52 |
| OBS-03 | Phase 51 |
| DEBT-01 | Phase 54 |
| NG-01 | Phase 54 |
