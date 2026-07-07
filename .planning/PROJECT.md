# 설비 로그파서 파이프라인 opencode 하네스 (LogParser Pipeline Harness)

## What This Is

반도체 설비 이벤트 로그파서를 책임 분리된 폴리글랏 모노레포(.NET 10 파서·컨버터 / Python 스케줄러·수집기)로 재설계하는 프로젝트를, **에이전트가 만들고·유지보수·개발·리팩토링**할 수 있게 해주는 **opencode 에이전트 하네스**다. 산출물은 컴포넌트 구현 코드가 아니라 하네스 그 자체 — opencode agents·commands·skills·plugins, Diátaxis+ADR+contracts 문서구조, 그리고 세션을 넘어 유지되는 두 평면(헌법/파생) 컨텍스트 메모리 층이다. 대상 사용자는 이 모노레포에서 일하는 개발자와 그들을 돕는 코딩 에이전트다.

## Core Value

**계약(contracts)을 단일 정본으로 두고, 폴리글랏 표현차·레거시 전환 리스크를 하네스가 자동으로 강제·검증한다** — 에이전트가 이 레포에서 "어떻게 개발·유지보수·리팩토링하는가"가 부족(tribal knowledge)이 아니라 실행 가능한 스킬·커맨드·훅으로 박혀 있어야 한다.

## Requirements

### Validated

(None yet — ship to validate)

### Active

<!-- 하네스 산출물. 모두 검증 전까지 가설. -->

- [ ] **opencode 하네스 표면**: agents(orchestrator·dotnet·python·reviewer·golden-runner·polyglot-auditor·explorer), commands(/golden·/golden-approve·/contract-check·/new-normalization-rule·/adr·/strangler-step·/docs-sync·/component·/checkpoint), skills(dotnet·python·pipeline-patterns·data-contracts·golden-testing·normalization-catalog·skill-creator), plugins(contract-guard·session-start 주입기·format-on-write·polyglot-boundary 린터)
- [ ] **opencode.json**: 모델·15키 권한 매트릭스(bash glob last-wins)·instructions glob·MCP·formatter
- [ ] **단일소스 다중 런타임 산출**: 하네스 소스에서 opencode(1차)와 Claude Code(.claude/) 아티팩트를 생성 (각 런타임 제약 존중)
- [ ] **문서 아키텍처**: Diátaxis(tutorials/how-to/reference/explanation) + adr/(불변 MADR) + glossary + 루트/컴포넌트별 AGENTS.md, reference/는 계약에서 생성(에이전트 유지)
- [ ] **two-plane 컨텍스트 메모리**: 헌법 평면(contracts·adr·glossary·golden — 사람 소유·게이트) + 파생/휘발 평면(.memory/ activeContext·progress + repo-map·contracts-index 파생) + SessionStart 훅 무시불가 주입
- [ ] **폴리글랏 안전망**: 골든 동등성 비교기(정규화 비교)·contract-drift CI 게이트(스키마 해시)·CODEOWNERS+/golden-approve 사람 승인
- [ ] **도메인 계약·문서 시드**: parserimprove monorepo_skeleton의 contracts(TSV 스펙·정규화·기준정보·state)·docs를 example/seed로 명시하여 포함
- [ ] **툴체인 부트스트랩**: .NET 10 SDK 설치 스크립트 + uv 워크스페이스 + polyglot 매트릭스 CI 골격을 SessionStart/setup에 연결

### Out of Scope

- **컴포넌트 구현 코드(파서·컨버터·스케줄러·수집기 로직)** — 이 프로젝트는 하네스이지 파이프라인 구현이 아니다. 실제 값·알고리즘은 사내에서 채운다.
- **표준 로그 TSV 스펙의 컬럼 확정값·DB 스키마 확정값** — 도메인 정본 미정(parserimprove 10장), 계약은 골격·placeholder로 시드.
- **B 모델(gRPC/메시지 큐) 운영 구현** — 하네스는 A 모델(CLI spawn) 계약을 우선 인코딩, B는 커맨드/스킬 확장 지점으로만.
- **Configuration 파서 관련 하네스** — parserimprove상 차후 컴포넌트.
- **발표 시스템(presentationformat)** — 참조 도메인 소스일 뿐 산출물 아님.

## Context

- **도메인 정본**: `/workspace/presentationformat/archive/parserimprove/uploads/` — `parser_project_revised.md`(전체), `integration_contracts_design.md`(통합 계약·폴리글랏 §4~5 체크리스트), `scheduler_design.md`, `file_collector_design.md`, `converter_design.md`, `standard_parser_design.md`, `monorepo_skeleton/`(문서 00~04+GLOSSARY, 계약 골격).
- **도메인 요지**: 설비 실시간 TSV 로그 → 수집 → (비표준은)컨버터 표준화 → 표준 파서(값 정규화·보정·start/end 병합·carryover) → 공정 DB. 폴리글랏 버그는 기능이 아니라 표현차(인코딩·LF·TSV 이스케이프·타임존·소수점·null)에서 난다. 골든 동등성이 언어 무관 안전망. live/rework/따라잡기 시나리오는 '가공'의 축이며 '수집'과 분리. 상태는 DB SSOT.
- **개발 환경**: Claude Code + GSD(get-shit-done-cc v1.42.3, 로컬+글로벌 설치됨). GSD가 개발 워크플로(spec→plan→execute→verify)를 구동. 산출 하네스의 컨텍스트 메모리는 GSD `.planning/`과 **독립**된 two-plane 설계.
- **툴체인 현황(이 환경)**: Python 3.11 + uv 0.8.17 ✅, Docker 29.3 ✅, **.NET 10 SDK 미설치**(설치 스크립트 필요), 원격 ephemeral 컨테이너(커밋·푸시로만 영속).
- **리서치 종합(3 에이전트)**: ① 하네스 4계층 분리(rules/agents/commands/skills) + per-package AGENTS.md 지연로딩 + 모델 티어링 + bash glob 권한 매트릭스 + 훅 가드레일. ② 컨텍스트 메모리는 "직접 만드는 것(intent/결정)"과 "파생되는 것(state)" 분리 — 파생물 자동 재생성, 휘발 state는 훅으로 무시불가 주입, 결정은 불변(ADR). ③ contracts=헌법, golden=안전망, Diátaxis reference만 에이전트 생성, `/golden`·`/contract-check`·`/strangler-step` 커맨드로 리팩토링을 계약우선·패리티게이트로 인코딩.

## Constraints

- **Runtime**: opencode 1차 타깃, 단일 소스에서 Claude Code 아티팩트도 생성(개발=Claude, 배포=opencode). 각 런타임 제약(예: 스킬 크기 상한) 존중.
- **Polyglot**: 파서·컨버터=.NET 10(CPU 바운드), 스케줄러·수집기=Python(uv). 언어 경계는 프로세스/파일/DB로만 — 객체 직접 전달 금지.
- **Contract-first**: contracts/가 코드보다 우선. 코드가 계약과 다르면 코드가 틀린 것. 계약 변경은 골든/contract-drift 게이트를 동반.
- **Memory**: two-plane. 파생물(repo-map·contracts-index·docs/reference)은 손으로 관리 금지(자동 생성). 결정은 append-only ADR.
- **Env**: 원격 ephemeral — 하네스는 SessionStart 훅으로 툴체인/상태를 자기부트스트랩. 브랜치 `claude/data-pipeline-harness-8aypct`.
- **모델 아이덴티티**: 커밋·PR·코드 코멘트 등 레포 산출물에 모델 식별자 미포함.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 산출물 = 하네스, 컴포넌트 코드 아님 | 사용자 명시: 스킬·커맨드·에이전트·문서·메모리 층을 만드는 것 | — Pending |
| opencode 우선 + 단일소스 Claude 생성 | 개발은 Claude Code(GSD), 배포는 opencode; wshobson 단일소스 다중산출 패턴 | — Pending |
| 독립 two-plane 컨텍스트 메모리 | 파생/휘발 분리로 rot 방지, GSD 비의존해 opencode 네이티브 유지 | — Pending |
| parserimprove 계약·문서 실제 시드(예시 명시) | 구체 예시가 하네스 검증에 유용, generic보다 실효 | — Pending |
| 맞춤 직접 구성(gsd-opencode 포트 미채택) | 도메인 맞춤·최소·정확; 750파일 범용 대비 | — Pending |
| A 모델(CLI spawn) 우선 인코딩, B는 확장점 | integration_contracts §④; MVP 견고성, A→B 페이로드 동형 유지 | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-07 after initialization*
