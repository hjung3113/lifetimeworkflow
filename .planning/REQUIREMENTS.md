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

- [x] **POLY-01**: 폴리글랏 경계 린터 — `integration_contracts §4-5` 체크리스트(인코딩·BOM·LF·TSV 이스케이프·타임존·소수점/로케일·null-vs-empty·쓰기 원자성·식별자/구간 규칙)를 on-write 훅 + CI에서 실행되는 실행 가능한 규칙으로 인코딩한다 (CONTRACT-02 코어 공유)

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

- [x] **AGENT-01**: orchestrator(primary) — 작업 분해·위임
- [x] **AGENT-02**: dotnet-engineer — .NET 10 구현, `dotnet *` 스코프
- [x] **AGENT-03**: python-engineer — Python/uv 구현, `uv *`·`pytest *` 스코프
- [x] **AGENT-04**: code-reviewer — 읽기전용(Read/Grep/Glob), 쓰기·bash 없음
- [x] **AGENT-05**: explorer — 저가 모델 코드 탐색, 경로 반환

### CMD — 슬래시 커맨드

- [x] **CMD-01**: 툴체인 래퍼 커맨드(`/build`·`/test`·`/lint`) — .NET/Python 정본 호출 캡슐화
- [x] **CMD-02**: `/golden` — 실행 + 정규화 diff
- [x] **CMD-03**: `/golden-approve` — CODEOWNERS 사람 사인오프로만 baseline 갱신 (에이전트 self-bless 금지)
- [x] **CMD-04**: `/checkpoint` — 휘발 평면(activeContext·progress) 갱신, ephemeral 컨테이너 대비 커밋
- [x] **CMD-05**: `/new-normalization-rule` — 계약 우선 순서(계약 → 데이터기반 (input,expected) 케이스 → 코드) 강제
- [x] **CMD-06**: `/strangler-step` — 한 경로만 추출, `/golden` 패리티 게이트 통과 필수, 빅뱅 금지
- [x] **CMD-07**: `/adr` — append-only MADR 스캐폴드
- [x] **CMD-08**: `/docs-sync` — 계약에서 Diátaxis `reference/` 재생성
- [x] **CMD-09**: `/component` — 신규 컴포넌트를 올바른 구조·AGENTS.md·테스트 하네스와 함께 스캐폴드

### HOOK — 플러그인 / 훅 (강제 표면)

- [x] **HOOK-01**: format-on-write — 편집 시 자동 포맷(formatter 연동), LF/인코딩 강제점
- [x] **HOOK-02**: secret protection — secret 읽기/쓰기 차단(deny-list + 패턴 스캔)
- [x] **HOOK-03**: commit gate — 게이트(contract-drift·골든 패리티·폴리글랏 린터) 실패 시 커밋 차단
- [x] **HOOK-04**: contract-guard — 헌법 평면·golden 쓰기를 승인 경로 없이 차단, on-write 인코딩/TSV 규칙 강제
- [x] **HOOK-05**: session-start 컨텍스트 주입기 — opencode `event`(session.created) + `chat.system.transform`, Claude `SessionStart` additionalContext로 휘발 상태·drift 상태를 **무시 불가** 주입 (런타임 비대칭 조정)

### DOCS — 문서 아키텍처

- [x] **DOCS-01**: Diátaxis 문서 트리(tutorials/how-to/reference/explanation) + `glossary`(ubiquitous language)
- [x] **DOCS-02**: `docs/adr/` MADR 구조(번호·불변·supersede)
- [x] **DOCS-03**: `reference/`는 계약에서 **파생**(사람은 tutorials/how-to/explanation만 작성)

### SKILL — 스킬 (progressive disclosure)

- [x] **SKILL-01**: 코어 스킬 세트(dotnet-conventions·python-conventions·golden-testing·data-contracts) — frontmatter 상시 + 본문 지연로딩, 런타임 크기 상한 준수
- [x] **SKILL-02**: skill-creator(메타) + 도메인 스킬(normalization-catalog·pipeline-patterns[carryover·시나리오])

### BOOT — 툴체인 부트스트랩

- [ ] **BOOT-01**: .NET 10 SDK 설치 스크립트(`dotnet-install.sh --channel 10.0`) — ephemeral 컨테이너에 SDK 부재
- [ ] **BOOT-02**: uv 워크스페이스 + Python 툴링(ruff·pyright·pytest) 골격
- [ ] **BOOT-03**: 부트스트랩을 SessionStart/setup에 와이어링

### GEN — 범용화 & 템플릿 추출 (Phase 5, INSERTED · ADR-0002)

- [x] **GEN-01**: 로그파서 도메인 시드(`contracts/{log-specs,reference-data,normalization,state}`, `libs/{python/normalize,dotnet/Normalize,normalize-fixtures}`, `components/toy-converter`, 관련 `golden/`)를 `examples/log-parser/`로 이동 — 신규 ADR + contract-hash manifest 재베이스라인 동반, 이동 후 라이브 contract-drift 게이트가 clean
- [x] **GEN-02**: 도메인 중립 최소 기본 인스턴스(제네릭 샘플 계약 + 골든 픽스처)를 루트에 제공 — 반도체 콘텐츠 없이 contract→hash→drift→golden 전체 루프가 돎을 증명
- [x] **GEN-03**: 참여 언어·툴체인을 단일 프로젝트 설정 슬롯(예: `harness/project.toml`)에서 읽기 — 권한 매트릭스 `dotnet */uv */pytest *` 스코프·엔지니어 페르소나·`/build`·`/test`·`/lint` 본문이 설정에서 파생(하드코딩 아님). 로그파서 예시가 .NET 10 + Python(uv) 값 공급
- [x] **GEN-04**: 코어→예시 단방향 의존 가드 테스트 — `tools/`·`harness/`·`libs/`(코어)가 `examples/**`를 import·경로참조 안 함(SCOPE A: 코드 의존만 강제), 추출 후 비-예시 테스트 스위트 그린 유지 + 루트 문서(`CLAUDE.md`·루트 `AGENTS.md`·`docs/`)는 템플릿+인스턴스 추가법 기술, 로그파서 특화는 예시 자체 `AGENTS.md`/README로 이동
- [x] **GEN-05** (Phase 5.5, INSERTED — 저작 표면 범용화, 데이터-평면 de-spec 후속): 도메인 특화 **저작 표면**을 범용화 — 도메인 스킬(`normalization-catalog`·`new-normalization-rule`·`pipeline-patterns`)을 `examples/log-parser/`(또는 예시별 스킬)로 강등, 언어 특화 페르소나(`dotnet-engineer`·`python-engineer`·`dotnet-conventions`)를 `harness/project.toml` 언어 슬롯에서 파생, prose의 `libs/dotnet` 등 잔여 도메인 참조 정리. 어느 스킬이 범용(golden-testing·data-contracts·skill-creator) vs 도메인인지 결정 포함. GEN-04 가드를 prose까지 확장.

### LIFE — 라이프사이클 완성 (Phase 5.7, INSERTED · 적대적 리뷰 보강, 전부 도메인 중립)

> 적대적 감사(2026-07-09)가 확인한 갭: 에이전트가 온보딩→계획→구현→계약검증→테스트→디버그→리뷰→문서→리팩터→통합을 실제로 끌고 갈 저작 자산이 얇음. 상세: `.planning/phases/05.7-lifecycle-completeness/057-CONTEXT.md`.

**MUST-HAVE (내부 루프가 깨짐):**
- [x] **LIFE-01** `/contract-check` 커맨드(신규): `check-jsonschema` + 드리프트-해시 비교 래핑(`tools/contract_drift`·`tools/contract_hash` 재사용). 현재 `new-normalization-rule.md`·`CLAUDE.md`가 참조하나 **부재**(dead link) — 계약검증 단계를 실행 가능하게
- [x] **LIFE-02** `golden-debug` 스킬(+선택 `/diagnose-golden`): 골든 red → 7 canonicalization 축(BOM/CRLF/InvariantCulture 소수점/float 허용오차/행키 정렬/UTC/TSV-이스케이프-vs-null) 결정트리 — 축별 판별법+수정측. 하네스 존재 이유인데 진단 절차 제로(최대 갭)
- [x] **LIFE-03** `polyglot-boundary` 스킬(신규): §4.3-4.6 불변식 단일 정본화(현재 3파일+prose 산재), body는 CLAUDE.md canonicalization 표를 `references/`로. Core Value를 tribal→스킬
- [x] **LIFE-04** 중립 language-engineer 템플릿/`/add-language` 스캐폴드: `project.toml [[languages]].persona`가 가리킬 페르소나를 코어가 파생 생성(스코프·contract-first·§4.3-4.6·golden-gate 보일러플레이트). 2번째 인스턴스 언어에서 "채워쓰는 템플릿" 성립
- [x] **LIFE-05** `/new-normalization-rule` 탈도메인화: 중립 `/new-contract-rule`로 일반화(코어 잔류) 또는 examples/로 이동 — GEN-05 잔여 + GEN-04 가드 정합

**SHOULD-HAVE (라이프사이클 완성):**
- [x] **LIFE-06** `/orient` 커맨드/온보딩 스킬: 결정론적 진입점(읽기 순서 + golden-path), `tools.memory_regen` 산출 래핑, injector deferred 의존 탈피
- [x] **LIFE-07** `/review` 워크플로 커맨드: diff → code-reviewer(읽기전용) → 심각도 분류 findings → 스코프 엔지니어 반환 + secret-scan 포스처
- [x] **LIFE-08** `gate-model` 스킬: 무엇이·어떻게 gated인지 맵(헌법 평면·machines-gate/humans-ratify·exit-3 거부·훅 표면·path_deny_globs)
- [x] **LIFE-09** `two-plane-memory` 스킬: 헌법-vs-파생 / 커밋된-state-vs-gitignored-derived / 파생-손편집-금지(현재 AGENTS.md prose만)
- [x] **LIFE-10** `/verify-work` (pre-handoff) 커맨드: 세션 내 복합 게이트(`/lint`+`/test`+`/contract-check`+`/golden` 터치 케이스). CI(Phase6)·checkpoint와 구별
- [x] **LIFE-11** orchestrator 라우팅 플레이북 보강(또는 `routing` 스킬): 결정표(작업형태→페르소나/커맨드) + 최소 intake→decompose 절차

### CI — 지속적 통합 & 게이트 (Phase 6, generic)

- [x] **CI-01**: **설정 파생** 폴리글랏 매트릭스 CI(GitHub Actions) — 언어별 테스트 잡 + generic contract-check/drift/golden을 비우회 실행. 잡은 `harness/project.toml` 설정에서 파생(하드코딩 `dotnet test`/`pytest` 아님); 로그파서 예시가 .NET 10 + pytest 레그 공급(.NET egress 유예가 GitHub 러너에서 실제 실행되는 지점)
- [x] **CI-02**: CODEOWNERS(`contracts/`·`adr/`·`golden/` + 예시 인스턴스 등가물 게이트) + PR 템플릿(경량 breaking 체크)

### EMIT — 단일소스 듀얼런타임 산출 (마지막 페이즈)

- [x] **EMIT-01**: 정본 하네스 소스 포맷(`harness/`) — agents/commands/skills/plugins의 단일 소스
- [x] **EMIT-02**: emitter — 소스에서 opencode(1차) + Claude Code(`.claude/`) 아티팩트를 생성, per-runtime 제약 검증기(스킬 크기 상한 등)가 truncate 대신 loud-fail

### PIPE — 파이프라인 토폴로지 지휘자 & 컴포넌트 에이전트 (Phase 8, ADDED · post-Phase-6 요청, 전부 도메인 중립)

> 에이전트 모델을 per-**언어**에서 파이프라인-**인식**으로 진화시킨다. 코어(`harness/`)에는 재사용 가능한 **메커니즘**(토폴로지 슬롯 + 지휘자 + 컴포넌트 엔지니어 템플릿)만, 구체적 4-컴포넌트 시연은 `examples/log-parser/`에 둔다(ADR-0002 / GEN-04: 코어는 예제에 의존 금지).

- [x] **PIPE-01**: `harness/project.toml`에 범용 **파이프라인-토폴로지 슬롯** — 각 컴포넌트의 id·stage·language 참조·edge 계약(consumes/produces)을 선언하는 순수 DATA 테이블(`[[components]]`/`[pipeline]`). `tools/harness_config/loader.py` passthrough + GEN-03-스타일 consistency 게이트. 예제 의존 0 (GEN-04 green).
- [x] **PIPE-02**: 기존 primary `orchestrator` 페르소나를 **토폴로지-인식 지휘자**로 진화 — 선언된 토폴로지를 읽어 parser→converter→scheduler→collector 데이터흐름 + edge 계약을 모델링하고, 언어가 아니라 파이프라인 stage/컴포넌트로 라우팅. 라우팅 테이블 + intake 절차 갱신 (primary는 하나로 유지).
- [x] **PIPE-03**: `harness/agents/templates/`에 중립 **`component-engineer` 템플릿**(engineer.md처럼 persona anti-sprawl 게이트 예외) + 선언된 토폴로지 컴포넌트에 바인딩된 per-컴포넌트 에이전트를 인스턴스화하는 scaffold/register 커맨드(`/component` 확장 또는 보완).
- [x] **PIPE-04**: `examples/log-parser/`에서 메커니즘 **엔드투엔드 시연** — 4개 구체 컴포넌트 에이전트(parser·converter·scheduler·collector) + 인스턴스 `project.toml` 슬롯에 선언된 로그파서 파이프라인 토폴로지; 지휘자가 전체 흐름을 추적.
- [x] **PIPE-05**: 파이프라인 모델을 실행 가능하게 하는 스킬/커맨드 — 토폴로지-trace `pipeline-map` 스킬 + 데이터흐름을 시각화·추적하고 올바른 컴포넌트 에이전트를 찾아주는 `/pipeline` 커맨드.
- [x] **PIPE-06**: 가드/테스트 — GEN-04 코어→예제 no-dependency 가드 + persona anti-sprawl 게이트를 지휘자·`component-engineer` 템플릿까지 확장; 토폴로지 슬롯 consistency 게이트.

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
| AGENT-01 | Phase 3 | Complete |
| AGENT-02 | Phase 3 | Complete |
| AGENT-03 | Phase 3 | Complete |
| AGENT-04 | Phase 3 | Complete |
| AGENT-05 | Phase 3 | Complete |
| CMD-01 | Phase 3 | Complete |
| CMD-02 | Phase 3 | Complete |
| CMD-03 | Phase 3 | Complete |
| CMD-04 | Phase 3 | Complete |
| CMD-05 | Phase 3 | Complete |
| CMD-06 | Phase 3 | Complete |
| CMD-07 | Phase 3 | Complete |
| CMD-08 | Phase 3 | Complete |
| CMD-09 | Phase 3 | Complete |
| SKILL-01 | Phase 3 | Complete |
| SKILL-02 | Phase 3 | Complete |
| DOCS-03 | Phase 3 | Complete |
| HOOK-01 | Phase 4 | Complete |
| HOOK-02 | Phase 4 | Complete |
| HOOK-03 | Phase 4 | Complete |
| HOOK-04 | Phase 4 | Complete |
| POLY-01 | Phase 4 | Complete |
| GEN-01 | Phase 5 | Complete |
| GEN-02 | Phase 5 | Complete |
| GEN-03 | Phase 5 | Complete |
| GEN-04 | Phase 5 | Complete |
| GEN-05 | Phase 5.5 | Complete |
| CI-01 | Phase 6 | Complete |
| CI-02 | Phase 6 | Complete |
| EMIT-01 | Phase 7 | Complete |
| EMIT-02 | Phase 7 | Complete |
| PIPE-01 | Phase 8 | Complete |
| PIPE-02 | Phase 8 | Complete |
| PIPE-03 | Phase 8 | Complete |
| PIPE-04 | Phase 8 | Complete |
| PIPE-05 | Phase 8 | Complete |
| PIPE-06 | Phase 8 | Complete |

**Coverage:**
- v1 requirements: 54 total (43 원본 + GEN-01..05 + PIPE-01..06 신규; GEN-05 = 저작 표면 후속, PIPE = Phase 8 파이프라인 지휘자)
- Mapped to phases: 54 ✓
- Unmapped: 0 ✓

**Phase distribution:** P1=9, P2=6, P3=19, P4=5, P5=4(GEN-01..04), P5.5=1(GEN-05), P6=2(CI), P7=2(EMIT)

**Note on POLY-01 / CONTRACT-02:** POLY-01(전체 린터)은 Phase 4에 단일 매핑. 그 정규화 코어는 CONTRACT-02(Phase 1)로 별도 REQ이며 Phase 1에서 한 번 만들어 골든러너·린터가 공유 — 중복 매핑 아님.

---
*Requirements defined: 2026-07-07*
*Last updated: 2026-07-07 after roadmap traceability mapping*
