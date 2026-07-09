# Phase 5: De-specialization & Template Extraction — Context

**Gathered:** 2026-07-08
**Status:** Ready for planning
**Origin:** ADR-0002 re-scope (log-parser-specific harness → general reusable template)

<domain>
## Phase Boundary

Phase 1–4에서 구축한 **durable 코어를 그 도메인 인스턴스(반도체 로그파서)로부터 분리**한다 — 레포를 재사용 가능한 템플릿으로. 도메인 계약·정규화·toy-converter를 `examples/log-parser/`로 강등, .NET+Python 가정을 프로젝트 설정 슬롯으로, generic 기본 인스턴스 추가, 코어→예시 무의존 증명. (REQs: GEN-01, GEN-02, GEN-03, GEN-04)

**In scope**:
- 로그파서 도메인 시드 이동(`contracts/{log-specs,reference-data,normalization,state}`, `libs/{python/normalize,dotnet/Normalize,normalize-fixtures}`, `components/toy-converter`, 관련 `golden/`) → `examples/log-parser/` + 신규 ADR + contract-hash manifest 재베이스라인 (이동 후 라이브 drift 게이트 clean)
- generic 최소 기본 인스턴스(루트): 도메인 중립 샘플 계약 + 골든 픽스처 — contract→hash→drift→golden 루프가 반도체 콘텐츠 없이 돎
- 언어·툴체인 설정 슬롯(`harness/project.toml` 또는 동등물): 권한 매트릭스 언어 스코프·엔지니어 페르소나·`/build`·`/test`·`/lint` 본문이 설정에서 파생
- 코어→예시 단방향 의존 가드 테스트 + 비-예시 스위트 그린
- 루트 문서(CLAUDE.md·루트 AGENTS.md·docs/) 템플릿화, 로그파서 특화는 예시 자체로 이동
- **게이트 정본 경로**: commit-gate에 `GOLDEN_APPROVE_HUMAN` 승인 우회 추가(contract-guard와 일관) — 의도된 사람-승인 헌법 변경의 착지 경로

**Out of scope (이 페이즈)**:
- Phase 6 CI(설정형 매트릭스) / Phase 7 emitter
- 새 도메인 예시 추가(로그파서 하나면 충분; 템플릿 검증은 generic 기본 인스턴스로)
- 정규화 코어의 알고리즘 변경 — 이동만, 로직 불변
- opencode 런타임 실동작(계속 deferred)
</domain>

<decisions>
## Implementation Decisions

### D-01 — 도메인 이동 대상 & 목적지 (GEN-01)  *(AMENDED 2026-07-08 per 05-RESEARCH Q1 — normalize 엔진은 범용, 코어 유지)*
- **이동(도메인)**: `contracts/log-specs/`, `contracts/reference-data/`, `contracts/state/`, `contracts/normalization/correction-rules*`(반도체 보정 카탈로그), `libs/dotnet/Normalize/`, `libs/dotnet/Normalize.Tests/`, `components/toy-converter/`, 그리고 이들을 참조하는 도메인 `golden/` 케이스 + `golden_runner`의 도메인 테스트 → `examples/log-parser/` 아래로 (원 트리 구조 보존).
- **코어 유지(범용 — 옮기지 않음)**: `libs/python/normalize/`(§4.3-4.6 canonicalizer 엔진 — 반도체 어휘 0, 코어 `polyglot_lint`·`golden_runner`가 import → 옮기면 GEN-04 자기위반 + uv 워크스페이스 파손), `libs/normalize-fixtures/`(코어 corpus-parity 테스트가 참조). 이들은 어떤 polyglot 프로젝트든 필요한 경계 유틸이라 **코어의 일부**다. `contracts/normalization/format-conventions.schema.json`(P14 §4.3-4.6 범용 규약)은 general-leaning — 이동 여부는 planner가 RESEARCH 근거로 결정(기본: generic 기본 인스턴스의 계약으로 코어 잔류 후보).
- **재사용 툴(`tools/`)은 이동 안 함** — 코어. 단, 도메인 루트를 하드코딩한 부분은 **설정/인자화**해서 코어가 예시를 모르게. (RESEARCH: 대부분 이미 parametrized — 정확 지점은 05-RESEARCH Q1 인벤토리.)
- 예시→코어 의존은 허용(단방향): 예시의 .NET 테스트가 코어 `libs/normalize-fixtures/`를 참조하는 것은 OK. 코어→예시만 금지(D-04).
- `contracts/.hashes/manifest.json`은 재생성(재베이스라인). 이동 후 `contracts/`에는 generic 기본 인스턴스(D-02)만 남음 → manifest 반영, 라이브 drift 게이트 clean.

### D-01b — Open Questions 확정 (05-RESEARCH)
- **Q1 정규화 코어**: **코어 유지**(위). 도메인 계약·.NET impl·toy-converter·도메인 golden만 이동.
- **Q2 토큰 범위**: commit-gate 승인 우회는 **drift 컴포넌트 한정**. polyglot·secret·golden 컴포넌트는 토큰과 무관하게 hard 유지(안전 위반은 승인으로도 통과 불가). (D-05 참조.)
- **Q3 generic 컨버터**: generic 기본 인스턴스(D-02)의 골든 케이스는 **언어무관(Python) identity/echo 컨버터**를 써서 **.NET 없이도 green** — 템플릿 clone 직후 즉시 도는 루프. (도메인 예시의 .NET toy-converter는 egress-deferred SKIP 유지.) RESEARCH가 지적한 3개 스냅샷/테스트(docs_sync·memory_regen·golden_runner)는 이동/재생성으로 그린 복구.

### D-02 — generic 기본 인스턴스 (GEN-02)
- 루트 `contracts/`에 도메인 중립 최소 샘플: 예) `contracts/sample/greeting.schema.json`(단순 필드 스키마) + 동반 골든 케이스(`golden/sample/...`). 반도체 어휘 0.
- 목적: 코어 기계(hash·drift·golden·docs-sync·polyglot-lint)가 **빈 도메인에서도 돎**을 증명 — 템플릿 clone 직후 상태.
- 이게 `/docs-sync`·contracts-index·repo-map 파생물의 새 입력 → 파생물도 재생성.

### D-03 — 언어 설정 슬롯 (GEN-03)
- 단일 SSOT: `harness/project.toml`(또는 `.json`) — `[languages]` 목록(id, 툴 커맨드 glob, SDK 부트스트랩 참조, 테스트/포맷 커맨드). 
- 파생: 권한 매트릭스의 `dotnet */uv */pytest *` allow 스코프, 엔지니어 페르소나(dotnet-engineer/python-engineer), `/build`·`/test`·`/lint` 커맨드 본문이 이 설정에서 나오도록. **최소 구현**: 설정 파일 + 그것을 읽는 얇은 로더 + 예시가 .NET+Python 값 공급. (풀 코드젠은 과함 — 설정을 정본으로 두고, 현재 하드코딩을 "예시 인스턴스가 채운 값"으로 재해석하는 수준이면 GEN-03 충족.)
- Claude 재량: 설정 포맷·로더 위치·페르소나/커맨드가 설정을 소비하는 정확한 메커니즘.

### D-04 — 코어→예시 단방향 의존 가드 (GEN-04)
- 가드 테스트: `tools/`·`harness/`·`libs/`(코어에 남는 것) 어디도 `examples/**`를 import/경로참조 안 함. (grep 기반 or import-scan 테스트.)
- 이동 후 **비-예시 pytest 스위트 그린** 유지. 예시 자체 테스트(정규화·toy-converter)는 `examples/log-parser/`로 함께 이동하고 거기서 green(단, .NET는 계속 egress-deferred skip).

### D-05 — 게이트 정본 경로 (핵심, 이 페이즈 필수)
- **문제**: 라이브 commit-gate의 drift 체크가 도메인 이동 커밋 자체를 차단. contract-guard엔 `GOLDEN_APPROVE_HUMAN` 우회가 있으나 commit-gate엔 없음 → 의도된 사람-승인 헌법 변경의 정본 착지 경로 부재(템플릿 갭).
- **결정**: commit-gate에 **동일한 `GOLDEN_APPROVE_HUMAN` 승인 우회** 추가 — 토큰이 non-empty면 drift 실패를 **차단이 아니라 경고+통과**(단 polyglot/secret 등 안전 위반은 여전히 차단할지 여부는 planner 재량; 최소한 drift 컴포넌트는 approve로 우회). contract-guard와 일관된 "machines gate, humans ratify".
- **운영 흐름**(문서화): 사람이 `GOLDEN_APPROVE_HUMAN` export → 에이전트가 의도된 계약 변경 착지 → ADR가 기록. 게이트를 *끄는* 게 아니라 *승인 경로*를 만드는 것.
- **이 레포의 실제 이동 실행 시**: 사람(사용자)이 이미 승인함(ADR-0002). 이동 커밋을 이 승인 경로로 착지. planner는 실행 executor가 토큰을 어떻게 세팅하는지(세션 env / settings.json env 임시 / 실행 스크립트)까지 명시할 것. **게이트 bash-우회 금지**.
- 이 변경은 commit-gate 테스트(04-05) 확장 동반: approve 토큰 present → drift 우회 통과, absent → 여전히 차단.

### D-06 — ADR
- 신규 ADR(0002-general-template-de-specialization 또는 다음 번호) 작성: MADR, Status accepted, ADR-0001 supersede 아님(보완). 결정 = 범용 재정의 + 도메인 강등 + 언어 슬롯화 + 게이트 승인경로. 이 ADR 작성 자체가 헌법-평면 쓰기 → D-05 승인 경로로 착지.

### Claude's Discretion
- `examples/` 하위 정확한 트리, generic 샘플 계약 내용, `harness/project.toml` 스키마, 로더/소비 메커니즘, 가드 테스트 구현(grep vs import-scan), commit-gate 우회의 정확한 세맨틱(어느 컴포넌트까지 우회)은 planner/researcher 재량. **고정**: 코어→예시 무의존·이동후-drift-clean·generic-기본-인스턴스-작동·게이트-승인경로(끄기 아님)·정규화 로직 불변·ADR 동반.
</decisions>

<canonical_refs>
## Canonical References
**Downstream agents MUST read these before planning or implementing.**
- `.planning/PROJECT.md`(재정의된 정체성·Genericity 제약·ADR-0002 결정), `.planning/ROADMAP.md §Phase 5`(5 성공기준), `.planning/REQUIREMENTS.md §GEN`(GEN-01..04)
- `CLAUDE.md`(스택 핀·§4.3-4.6 표 — 이동 대상이지 삭제 아님)
- 이동 대상 인벤토리: `contracts/**`, `libs/**`, `components/toy-converter/**`, `golden/**`
- **코어 자산(이동 안 함, 도메인 경로 인자화 대상)**: `tools/contract_hash/hash.py`(contracts/ 스캔 루트), `tools/contract_drift/drift.py`(run_gate 베이스라인), `tools/golden_runner/runner.py`(case_dir 루트), `tools/polyglot_lint/lint.py`(corpus 참조), `tools/docs_sync/generate.py`(contracts→reference 루트), `tools/memory_regen/*`(스캔 루트), `tools/hooks/commit_gate.py`(D-05 승인 우회 추가 대상), `tools/hooks/contract_guard.py`(GOLDEN_APPROVE_HUMAN 선례), `harness/permission-matrix.json`(언어 스코프), `harness/agents/{dotnet,python}-engineer.md`, `harness/commands/{build,test,lint}.md`(언어 파생 대상)
- `docs/adr/README.md`(MADR 규약·append-only), `docs/adr/0001-*.md`(선례)
</canonical_refs>

<code_context>
## Existing Code Insights
### Reusable Assets (코어 — 유지, 도메인 경로 인자화)
- `tools/*` 전부 코어. 도메인 루트를 상수로 박은 곳만 설정/인자로.
- `tools/hooks/contract_guard.py`의 `GOLDEN_APPROVE_HUMAN` 처리 = commit-gate 우회의 복제 선례(D-05).
### Established Patterns (locked)
- 코어→예시 단방향. 이동후 drift clean. 정규화 로직 불변(이동만). 게이트는 승인경로(끄기 아님). ADR 동반. 파생물 재생성.
### Integration Points
- 이동 → contract_hash/drift/golden_runner/docs_sync/memory_regen의 스캔 루트가 generic 기본 인스턴스로 재지향 + 예시 루트도 처리 가능해야(예시 자체 골든/계약도 검증되게 — 단 코어가 예시를 "아는" 게 아니라 인자로 받는 형태).
- `harness/project.toml` → 권한매트릭스/페르소나/커맨드.
- commit-gate 우회 → 04-05 테스트 확장.
</code_context>

<specifics>
## Specific Ideas
- 성공기준 데모: (1) 이동 후 `uv run python -m tools.contract_drift.drift`가 clean; (2) 루트 generic 샘플로 `/golden` 루프가 돎(반도체 0); (3) `harness/project.toml`에서 언어 스코프 파생; (4) 코어 grep가 `examples/` 참조 0 + 비-예시 스위트 그린; (5) `GOLDEN_APPROVE_HUMAN` present 시 의도된 계약 변경 커밋 착지.
- 이동은 `git mv`로 히스토리 보존.
</specifics>

<deferred>
## Deferred Ideas
- 설정형 CI 매트릭스 → Phase 6.
- 추가 도메인 예시 → 후속.
- opencode 런타임 실동작 → opencode 설치 후.
- 스코프 이탈 없음.
</deferred>

---
*Phase: 5 — De-specialization & Template Extraction (INSERTED, ADR-0002)*
*Context gathered: 2026-07-08 (gray areas resolved with recommended defaults — AskUserQuestion unavailable; user gave explicit go-ahead "ㄱㄱㄱㄱ")*
