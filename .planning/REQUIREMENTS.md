# Requirements: 설비 로그파서 파이프라인 opencode 하네스

**Defined:** 2026-07-07
**Core Value:** 계약(contracts)을 단일 정본으로 두고, 폴리글랏 표현차·레거시 전환 리스크를 하네스가 자동으로 강제·검증한다 — "어떻게 개발·유지보수·리팩토링하는가"가 실행 가능한 스킬·커맨드·훅으로 박혀 있다.

> 산출물은 **하네스**이지 파이프라인 컴포넌트 구현이 아니다. 요구사항은 하네스 능력(agents/commands/skills/plugins + 문서구조 + 두 평면 메모리 + 안전망 게이트)을 정의한다. 리서치 정본: `.planning/research/SUMMARY.md`(6-페이즈 스파인·빌드오더), `FEATURES.md`(우선순위 매트릭스).

## v1 Requirements

하네스 v1 = 리서치가 수렴한 빌드오더대로 전 표면을 안전망 우선으로 구축. 각 REQ는 로드맵 페이즈에 매핑된다.

### CONTRACT — 헌법 평면 & 계약 게이트

- [x] **CONTRACT-01**: parserimprove `monorepo_skeleton`의 계약(TSV 로그 스펙·정규화 규칙·기준정보·state)을 `contracts/`에 **example/seed(placeholder)로 명시**하여 시드한다 (도메인 확정값은 Out of Scope)
- [x] **CONTRACT-02**: 정규화 비교 코어(canonicalizing comparator) — UTF-8/BOM 제거·LF·InvariantCulture 소수점·float 허용오차·키 정렬·UTC/ISO-8601 — 를 골든러너와 폴리글랏 린터가 **공유**하는 단일 구현으로 만든다
- [x] **CONTRACT-03**: 골든 픽스처 세트 + 골든러너 — 정규화 비교로 레거시↔신규 **동등성**을 언어 무관하게 검증한다 (byte-diff 금지)
- [x] **CONTRACT-04**: contract-drift 게이트 — 계약(스키마)을 RFC 8785 정규화 후 SHA-256 해시로 고정하고, 미승인 변경 시 실패시키며 breaking 여부를 분류한다

### POLY — 폴리글랏 경계 안전망

- [ ] **POLY-01**: 폴리글랏 경계 린터 — `integration_contracts §4-5` 체크리스트(인코딩·BOM·LF·TSV 이스케이프·타임존·소수점/로케일·null-vs-empty·쓰기 원자성·식별자/구간 규칙)를 on-write 훅 + CI에서 실행되는 실행 가능한 규칙으로 인코딩한다 (CONTRACT-02 코어 공유)

### MEM — 두 평면 컨텍스트 메모리

- [x] **MEM-01**: 헌법 평면 레이아웃 — `contracts/`·`docs/adr/`·`glossary`·`golden/`를 사람 소유·CODEOWNERS 게이트·불변으로 배치한다 (에이전트 자동 변경 금지)
- [x] **MEM-02**: 파생/휘발 평면 — `.memory/`(activeContext·progress) + 파생물(repo-map·contracts-index)을 두고, 파생물은 손으로 관리하지 않는다(자동 재생성, gitignore)
- [x] **MEM-03**: 파생 아티팩트 생성기 — repo-map(tree-sitter + PageRank)과 contracts-index를 계약/코드에서 재생성한다

### RULES — 규칙 (AGENTS.md)

- [x] **RULES-01**: 루트 `AGENTS.md`(모노레포 맵·golden-path·contract-first·지연로딩 규칙) + `CLAUDE.md` 포인터
- [x] **RULES-02**: per-package `AGENTS.md`(.NET / Python)로 언어별 규칙을 nearest-wins 스코핑한다 (런타임별 병합 의미 차이는 훅으로 보강)

### CONFIG — opencode.json & 권한

- [x] **CONFIG-01**: `opencode.json` — 모델 티어링(explorer 저가 / implementer 고가)·instructions glob·formatter·MCP 와이어링
- [x] **CONFIG-02**: 15키 권한 매트릭스 — bash glob last-wins, reviewer 읽기전용 스코핑, secret/constitution 쓰기 deny

### AGENT — 에이전트 페르소나

- [ ] **AGENT-01**: orchestrator(primary) — 작업 분해·위임
- [ ] **AGENT-02**: dotnet-engineer — .NET 10 구현, `dotnet *` 스코프
- [ ] **AGENT-03**: python-engineer — Python/uv 구현, `uv *`·`pytest *` 스코프
- [ ] **AGENT-04**: code-reviewer — 읽기전용(Read/Grep/Glob), 쓰기·bash 없음
- [ ] **AGENT-05**: explorer — 저가 모델 코드 탐색, 경로 반환

### CMD — 슬래시 커맨드

- [ ] **CMD-01**: 툴체인 래퍼 커맨드(`/build`·`/test`·`/lint`) — .NET/Python 정본 호출 캡슐화
- [ ] **CMD-02**: `/golden` — 실행 + 정규화 diff
- [ ] **CMD-03**: `/golden-approve` — CODEOWNERS 사람 사인오프로만 baseline 갱신 (에이전트 self-bless 금지)
- [ ] **CMD-04**: `/checkpoint` — 휘발 평면(activeContext·progress) 갱신, ephemeral 컨테이너 대비 커밋
- [ ] **CMD-05**: `/new-normalization-rule` — 계약 우선 순서(계약 → 데이터기반 (input,expected) 케이스 → 코드) 강제
- [ ] **CMD-06**: `/strangler-step` — 한 경로만 추출, `/golden` 패리티 게이트 통과 필수, 빅뱅 금지
- [ ] **CMD-07**: `/adr` — append-only MADR 스캐폴드
- [ ] **CMD-08**: `/docs-sync` — 계약에서 Diátaxis `reference/` 재생성
- [ ] **CMD-09**: `/component` — 신규 컴포넌트를 올바른 구조·AGENTS.md·테스트 하네스와 함께 스캐폴드

### HOOK — 플러그인 / 훅 (강제 표면)

- [ ] **HOOK-01**: format-on-write — 편집 시 자동 포맷(formatter 연동), LF/인코딩 강제점
- [ ] **HOOK-02**: secret protection — secret 읽기/쓰기 차단(deny-list + 패턴 스캔)
- [ ] **HOOK-03**: commit gate — 게이트(contract-drift·골든 패리티·폴리글랏 린터) 실패 시 커밋 차단
- [ ] **HOOK-04**: contract-guard — 헌법 평면·golden 쓰기를 승인 경로 없이 차단, on-write 인코딩/TSV 규칙 강제
- [x] **HOOK-05**: session-start 컨텍스트 주입기 — opencode `event`(session.created) + `chat.system.transform`, Claude `SessionStart` additionalContext로 휘발 상태·drift 상태를 **무시 불가** 주입 (런타임 비대칭 조정)

### DOCS — 문서 아키텍처

- [x] **DOCS-01**: Diátaxis 문서 트리(tutorials/how-to/reference/explanation) + `glossary`(ubiquitous language)
- [x] **DOCS-02**: `docs/adr/` MADR 구조(번호·불변·supersede)
- [ ] **DOCS-03**: `reference/`는 계약에서 **파생**(사람은 tutorials/how-to/explanation만 작성)

### SKILL — 스킬 (progressive disclosure)

- [ ] **SKILL-01**: 코어 스킬 세트(dotnet-conventions·python-conventions·golden-testing·data-contracts) — frontmatter 상시 + 본문 지연로딩, 런타임 크기 상한 준수
- [ ] **SKILL-02**: skill-creator(메타) + 도메인 스킬(normalization-catalog·pipeline-patterns[carryover·시나리오])

### BOOT — 툴체인 부트스트랩

- [ ] **BOOT-01**: .NET 10 SDK 설치 스크립트(`dotnet-install.sh --channel 10.0`) — ephemeral 컨테이너에 SDK 부재
- [ ] **BOOT-02**: uv 워크스페이스 + Python 툴링(ruff·pyright·pytest) 골격
- [ ] **BOOT-03**: 부트스트랩을 SessionStart/setup에 와이어링

### CI — 지속적 통합 & 게이트

- [ ] **CI-01**: 폴리글랏 매트릭스 CI(GitHub Actions) — `dotnet test` + `pytest` + contract-check를 비우회 실행
- [ ] **CI-02**: CODEOWNERS(`contracts/`·`adr/`·`golden/` 게이트) + PR 템플릿(경량 breaking 체크)

### EMIT — 단일소스 듀얼런타임 산출 (마지막 페이즈)

- [ ] **EMIT-01**: 정본 하네스 소스 포맷(`harness/`) — agents/commands/skills/plugins의 단일 소스
- [ ] **EMIT-02**: emitter — 소스에서 opencode(1차) + Claude Code(`.claude/`) 아티팩트를 생성, per-runtime 제약 검증기(스킬 크기 상한 등)가 truncate 대신 loud-fail

## v2 Requirements

검증 후 또는 도메인 프로젝트 진행에 따라 추가. 현재 로드맵 밖.

### 운영·확장

- **EXT-01**: B-model 확장점(gRPC/메시지 큐 스캐폴딩) — A-model 견고화 후, job 페이로드 동형 유지 (`integration_contracts §4④`)
- **EXT-02**: golden-runner·polyglot-auditor 전용 에이전트 — 골든/린터 워크플로가 전용 페르소나를 요할 만큼 무거워질 때
- **EXT-03**: shadow-run(병행 운영) 툴링 (`parser_project_revised §5.5`)
- **EXT-04**: Configuration 파서 하네스 표면 (차후 컴포넌트)

## Out of Scope

| Feature | Reason |
|---------|--------|
| 컴포넌트 구현 로직(파서·컨버터·스케줄러·수집기 알고리즘) | 산출물은 하네스; 실제 값·알고리즘은 사내에서 채움 (PROJECT.md) |
| 표준 로그 TSV 컬럼 확정값·DB 스키마 확정값 | 도메인 정본 미정(parserimprove §7·§10); 계약은 placeholder 시드 |
| 빅뱅 재작성 커맨드(`/rewrite-legacy`) | 레거시 스펙 미문서화·동등성 최상위 리스크 → `/strangler-step`으로 대체 (anti-feature) |
| 에이전트의 골든 self-approve / 헌법 평면 자동 변경 | 안전망·단일정본 무결성 파괴 → 사람 CODEOWNERS 게이트 (anti-feature) |
| 손으로 쓰는 reference 문서 | 계약 정본과 즉시 drift → `/docs-sync` 파생 (anti-feature) |
| 객체 레벨 .NET↔Python interop(FFI·공유객체) | 경계는 프로세스/파일/DB만(§0) → A-model CLI spawn (anti-feature) |
| "실시간 전부"를 SSOT로 스트리밍 | DB가 SSOT(§4.1); 스트림은 휘발 신호 (anti-feature) |
| 발표 시스템(presentationformat) | 참조 도메인 소스일 뿐 산출물 아님 |

## Traceability

로드맵 매핑 완료 (2026-07-07). 모든 v1 REQ가 정확히 하나의 페이즈에 매핑됨.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CONTRACT-01 | Phase 1 | Complete |
| CONTRACT-02 | Phase 1 | Complete |
| CONTRACT-03 | Phase 1 | Complete |
| CONTRACT-04 | Phase 1 | Complete |
| BOOT-01 | Phase 1 | Pending |
| BOOT-02 | Phase 1 | Pending |
| BOOT-03 | Phase 1 | Pending |
| DOCS-01 | Phase 1 | Complete |
| DOCS-02 | Phase 1 | Complete |
| MEM-01 | Phase 2 | Complete |
| MEM-02 | Phase 2 | Complete |
| MEM-03 | Phase 2 | Complete |
| RULES-01 | Phase 2 | Complete |
| RULES-02 | Phase 2 | Complete |
| HOOK-05 | Phase 2 | Complete |
| CONFIG-01 | Phase 3 | Complete |
| CONFIG-02 | Phase 3 | Complete |
| AGENT-01 | Phase 3 | Pending |
| AGENT-02 | Phase 3 | Pending |
| AGENT-03 | Phase 3 | Pending |
| AGENT-04 | Phase 3 | Pending |
| AGENT-05 | Phase 3 | Pending |
| CMD-01 | Phase 3 | Pending |
| CMD-02 | Phase 3 | Pending |
| CMD-03 | Phase 3 | Pending |
| CMD-04 | Phase 3 | Pending |
| CMD-05 | Phase 3 | Pending |
| CMD-06 | Phase 3 | Pending |
| CMD-07 | Phase 3 | Pending |
| CMD-08 | Phase 3 | Pending |
| CMD-09 | Phase 3 | Pending |
| SKILL-01 | Phase 3 | Pending |
| SKILL-02 | Phase 3 | Pending |
| DOCS-03 | Phase 3 | Pending |
| HOOK-01 | Phase 4 | Pending |
| HOOK-02 | Phase 4 | Pending |
| HOOK-03 | Phase 4 | Pending |
| HOOK-04 | Phase 4 | Pending |
| POLY-01 | Phase 4 | Pending |
| CI-01 | Phase 5 | Pending |
| CI-02 | Phase 5 | Pending |
| EMIT-01 | Phase 6 | Pending |
| EMIT-02 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 43 total (이전 "36" 헤더는 stale — 실제 REQ-ID 수는 43)
- Mapped to phases: 43 ✓
- Unmapped: 0 ✓

**Phase distribution:** P1=9, P2=6, P3=19, P4=5, P5=2, P6=2

**Note on POLY-01 / CONTRACT-02:** POLY-01(전체 린터)은 Phase 4에 단일 매핑. 그 정규화 코어는 CONTRACT-02(Phase 1)로 별도 REQ이며 Phase 1에서 한 번 만들어 골든러너·린터가 공유 — 중복 매핑 아님.

---
*Requirements defined: 2026-07-07*
*Last updated: 2026-07-07 after roadmap traceability mapping*
