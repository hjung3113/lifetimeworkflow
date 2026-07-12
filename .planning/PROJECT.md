# Contract-First 폴리글랏 에이전트 하네스 템플릿 (Contract-First Polyglot Agent-Harness Template)

> **방향 전환 (2026-07-08, ADR-0002):** 이 프로젝트는 원래 반도체 설비 로그파서 파이프라인 **전용** 하네스로 출발했으나, 실제 구현 방향이 계속 바뀌면서 **재사용 가능한 범용 하네스 템플릿**으로 재정의되었다. 로그파서 도메인은 삭제하지 않고 `examples/log-parser/`의 **worked example(레퍼런스 인스턴스)**로 강등한다. Phase 1–4에서 만든 durable한 아키텍처는 그대로 유지된다.

## What This Is

**어떤 contract-first 폴리글랏 프로젝트든** 에이전트가 만들고·유지보수·개발·리팩토링할 수 있게 해주는 **재사용 가능한 에이전트 하네스 템플릿**이다. 산출물은 특정 컴포넌트 구현 코드가 아니라 하네스 그 자체 — opencode/Claude agents·commands·skills·plugins, Diátaxis+ADR+contracts 문서구조, 세션을 넘어 유지되는 두 평면(헌법/파생) 컨텍스트 메모리 층, 그리고 계약·골든·drift·권한을 강제하는 런타임 게이트다. 대상 사용자는 (1) 이 템플릿을 clone/scaffold해 자기 프로젝트에 얹는 개발자와 (2) 그들을 돕는 코딩 에이전트다. **도메인·언어는 하드코딩이 아니라 채워 넣는 슬롯**이다 — 반도체 로그파서는 그 슬롯을 채운 하나의 예시일 뿐.

## Core Value

**계약(contracts)을 단일 정본으로 두고, 폴리글랏 표현차·전환 리스크를 하네스가 자동으로 강제·검증한다 — 그리고 이 강제 구조가 특정 도메인·언어에 묶이지 않고 어느 프로젝트에나 재사용된다.** 에이전트가 레포에서 "어떻게 개발·유지보수·리팩토링하는가"가 부족(tribal knowledge)이 아니라 실행 가능한 스킬·커맨드·훅으로 박혀 있고, 그 박힌 구조를 도메인만 갈아끼워 다음 프로젝트로 가져갈 수 있어야 한다.

## Current Milestone: v2.0 Long-Horizon

**Goal:** 에이전트(그리고 사람)가 *멀티-프로젝트* 작업을 *여러 세션·긴 달력 시간*에 걸쳐 이어가되, 프로젝트 자신의 컨텍스트(코드 그래프·메모리·문서·결정)가 자동으로 신선하게 유지된다 — 기계가 유지보수하고, 사람이 재가한다.

**Target features (phases 9→10→11, 넘버링 연속):**
- **Self-Maintaining Derived Artifacts + Curator (Phase 9 / α)** — 파생물(repo-map·contracts-index·docs `reference/`·memory)이 머지 시점에 CI로 자동 신선화; Phase-7 re-emit-diff를 미러하는 "stale-derived" 게이트 + `curator` 에이전트가 유지 소유.
- **Context-Economy Fan-out/Synthesize (Phase 10 / β)** — 팬아웃 → 요약만 회수 → 합성하는 1급 워크플로로 장수 세션의 컨텍스트를 작게 유지. γ의 재사용 기반.
- **Multi-Repo Workspace (Phase 11 / γ)** — 여러 레포를 하나의 워크스페이스로 선언·조작; repo-scoped 서브에이전트 + 크로스-레포 contract drift/golden 게이트.

**Key context:** 모두 기존 기계(two-plane memory·`tools/memory_regen`·`/docs-sync`·orchestrator·Phase-6 CI·Phase-7 emitter·project.toml 슬롯)를 **재사용**하며 재구축 금지. 비협상 제약: derived는 손으로 편집 금지(기계가 쓰고 CI가 검증하는 것은 허용), 헌법 평면(contracts/adr/golden)은 사람 재가 유지(machines gate, humans ratify), GEN-04 core→example 무의존 유지, 모든 신규 agent/skill/hook은 Phase-7 emitter를 왕복. Open decisions(플랜 타임 해결): (α) committed-derived vs session-derived split, (γ) workspace model a/b/c (lean b: workspace manifest).

## Requirements

### Validated

(None yet — ship to validate)

### Active

<!-- 하네스 산출물. 모두 검증 전까지 가설. -->

<!-- v2.0 Long-Horizon (phases 9/10/11) — see REQUIREMENTS.md for MAINT-/ECON-/MREPO- detail -->

- [ ] **Self-maintaining derived artifacts + curator (v2.0 α)**: `curator` 에이전트 + CI stale-derived 게이트(repo-map·contracts-index·docs `reference/` 재생성 후 diff 실패) + write-시 저렴/PR-시 무거운 훅 포스처 + `/refresh-memory` 로컬 프리핸드오프 재생성.
- [ ] **Context-economy fan-out/synthesize (v2.0 β)**: 팬아웃→요약회수→합성 skill/command + compact citation-bearing 요약 반환 계약 + delegate-vs-inline 컨텍스트-예산 가이드(orchestrator·`/orient` 배선).
- [ ] **Multi-repo workspace (v2.0 γ)**: 워크스페이스 매니페스트/모델(project.toml 슬롯을 한 단계 올림) + repo-scoped 서브에이전트에 β 팬아웃 적용 + 크로스-레포 contract drift/golden 게이트 + Phase-8 topology의 레포 경계 일반화.

<!-- v1.0 하네스 표면 (shipped in phases 1–8; complete-milestone 시 Validated로 이동) -->

- [ ] **opencode 하네스 표면**: agents(orchestrator·dotnet·python·reviewer·golden-runner·polyglot-auditor·explorer), commands(/golden·/golden-approve·/contract-check·/new-normalization-rule·/adr·/strangler-step·/docs-sync·/component·/checkpoint), skills(dotnet·python·pipeline-patterns·data-contracts·golden-testing·normalization-catalog·skill-creator), plugins(contract-guard·session-start 주입기·format-on-write·polyglot-boundary 린터)
- [ ] **opencode.json**: 모델·15키 권한 매트릭스(bash glob last-wins)·instructions glob·MCP·formatter
- [ ] **단일소스 다중 런타임 산출**: 하네스 소스에서 opencode(1차)와 Claude Code(.claude/) 아티팩트를 생성 (각 런타임 제약 존중)
- [ ] **문서 아키텍처**: Diátaxis(tutorials/how-to/reference/explanation) + adr/(불변 MADR) + glossary + 루트/컴포넌트별 AGENTS.md, reference/는 계약에서 생성(에이전트 유지)
- [ ] **two-plane 컨텍스트 메모리**: 헌법 평면(contracts·adr·glossary·golden — 사람 소유·게이트) + 파생/휘발 평면(.memory/ activeContext·progress + repo-map·contracts-index 파생) + SessionStart 훅 무시불가 주입
- [ ] **폴리글랏 안전망**: 골든 동등성 비교기(정규화 비교)·contract-drift CI 게이트(스키마 해시)·CODEOWNERS+/golden-approve 사람 승인
- [ ] **범용화(신규, ADR-0002)**: 도메인·언어 특화 콘텐츠를 `examples/log-parser/`로 격리하고, 코어를 도메인·언어 중립으로. 언어는 프로젝트 설정 슬롯에서 파생. 코어→예시 무의존(단방향). 새 프로젝트가 scaffold할 수 있는 최소 generic 기본 인스턴스 제공.
- [ ] **레퍼런스 예시 인스턴스**: parserimprove monorepo_skeleton의 contracts(TSV 스펙·정규화·기준정보·state)·정규화 코어·toy-converter를 `examples/log-parser/`의 worked example로 보존(삭제 아님) — "이렇게 슬롯을 채운다"의 살아있는 예시.
- [ ] **툴체인 부트스트랩(설정형)**: 언어별 SDK 설치·워크스페이스·CI 매트릭스를 프로젝트 설정에서 파생. 예시 인스턴스는 .NET 10 SDK + uv 워크스페이스로 채움.

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
- **Polyglot (설정형)**: 하네스는 폴리글랏을 지원하되 **특정 언어를 하드코딩하지 않는다**. 참여 언어·툴체인은 프로젝트 설정(예: `harness/project.toml` 또는 동등물)의 슬롯이며, 에이전트 페르소나·권한 매트릭스·CI 매트릭스가 그 설정에서 파생된다. 언어 경계는 프로세스/파일/DB로만 — 객체 직접 전달 금지 (이 불변식은 언어 무관하게 유지). 레퍼런스 예시(`examples/log-parser/`)는 .NET 10 + Python(uv)로 그 슬롯을 채운다.
- **Contract-first**: contracts/가 코드보다 우선. 코드가 계약과 다르면 코드가 틀린 것. 계약 변경은 골든/contract-drift 게이트를 동반. **계약의 도메인 내용은 슬롯** — 하네스는 계약을 강제하는 기계이지 특정 계약 자체가 아니다.
- **Memory**: two-plane. 파생물(repo-map·contracts-index·docs/reference)은 손으로 관리 금지(자동 생성). 결정은 append-only ADR.
- **Genericity(신규)**: durable 코어(`tools/`, `harness/`, 게이트, 메모리, 문서구조)는 도메인·언어 중립. 도메인·언어 특화 콘텐츠는 `examples/<instance>/` 아래로 격리. 코어가 특정 예시를 import/의존하면 안 됨(예시→코어 단방향 의존).
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
| **[ADR-0002] 범용 템플릿으로 재정의, 로그파서는 examples/로 강등** | 실제 구현 방향이 크게 바뀜 — 도메인 고정 하네스는 부채. durable 아키텍처(Phase 1–4)는 재사용 가치가 있으므로 도메인·언어 슬롯화 | ✅ Accepted 2026-07-08 |
| **[ADR-0002] 언어를 하드코딩 대신 설정 슬롯화(.NET+Python은 예시 인스턴스)** | 폴리글랏 기계는 가치, 특정 두 언어 고정은 아님 | ✅ Accepted 2026-07-08 |
| **[ADR-0002] 도메인 이동은 새 Phase 5로, ADR+해시 재베이스라인 동반** | contracts/는 헌법 평면 — 라이브 drift/contract-guard 게이트가 방어, 의도된 헌법 변경으로 처리 | ✅ Accepted 2026-07-08 |

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
*Last updated: 2026-07-12 — opened milestone v2.0 Long-Horizon (self-maintaining memory + context-economy orchestration + multi-repo workspace); phases 9/10/11 continue numbering after v1.0 (phases 1–8) complete.*
