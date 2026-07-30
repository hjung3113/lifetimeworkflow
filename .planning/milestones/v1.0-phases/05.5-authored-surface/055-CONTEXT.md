# Phase 5.5: Authored-Surface Genericization — Context

**Gathered:** 2026-07-09
**Status:** Ready for planning
**Origin:** GEN-05 (ADR-0002 re-scope; SCOPE-A follow-up to Phase 5's data-plane move)

<domain>
## Phase Boundary

Phase 5는 **데이터 평면**(contracts/libs/golden)을 `examples/log-parser/`로 옮겼다. Phase 5.5는 **저작 표면**(skills·commands·agents)의 도메인·언어 특화를 걷어내 템플릿을 완성한다 — 어느 자산이 범용(코어) vs 도메인(예시) vs 언어(인스턴스)인지 확정하고, 도메인 스킬을 예시로 강등, 언어 페르소나를 인스턴스로, 범용 자산 본문의 반도체 특화 제거, GEN-04 가드를 prose까지 확장. (REQ: GEN-05)

**In scope**:
- 도메인 스킬(`normalization-catalog`, `pipeline-patterns`) → `examples/log-parser/skills/` (또는 예시별 스킬 위치)
- 인스턴스 언어 자산(`dotnet-conventions` 스킬, `dotnet-engineer` 페르소나) → `examples/log-parser/`
- 범용 자산 본문 제네릭화: `data-contracts` 스킬·`new-normalization-rule` 커맨드에서 반도체(equipment/log-spec/§도메인) 특화 예시 제거 → 도메인 중립 예시/generic 인스턴스 참조
- GEN-04 가드를 **prose까지 확장**: 코어(`tools/`·`harness/`·`libs/`)가 도메인 토큰(예: `equipment`, `standard-log`, `correction-rules`, `libs/dotnet`, 반도체 어휘) prose 참조 0 — 단, 신중히(범용 단어 오탐 방지, allowlist)
- 문서 갱신: 이동한 자산의 새 위치 반영(examples/log-parser/AGENTS.md·README, docs)

**Out of scope (이 페이즈)**:
- Phase 6 CI / Phase 7 emitter
- 스킬/페르소나의 **런타임 emit**(Phase 7이 project.toml→per-language 산출; 5.5는 소스 정리만)
- 정규화/게이트 로직 변경(저작 표면=마크다운, 로직 불변)
- 새 도메인 예시 추가
</domain>

<decisions>
## Implementation Decisions

### D-01 — 저작 자산 3분류 (범용/도메인/언어)
- **코어 잔류 (범용):**
  - 스킬: `golden-testing`(골든/승인 방법론), `skill-creator`(메타), `data-contracts`(계약우선 방법론 — 본문 도메인 예시만 제네릭화)
  - 페르소나: `orchestrator`, `code-reviewer`, `explorer`
  - 페르소나: **`python-engineer` + 스킬 `python-conventions` 도 코어** — 하네스 자체가 Python(`tools/`)으로 저작되므로 Python은 "코어를 개발하는 언어". 로그파서 인스턴스가 Python 컴포넌트에 이를 재사용하는 것은 예시→코어(허용).
  - 커맨드: `build`·`test`·`lint`·`golden`·`golden-approve`·`adr`·`checkpoint`·`component`·`strangler-step`·`docs-sync`(범용), `new-normalization-rule`(본문 제네릭화 후 잔류 — 아래 D-02)
- **examples/log-parser/로 이동 (도메인):**
  - 스킬 `normalization-catalog`(반도체 보정 카탈로그), `pipeline-patterns`(carryover/live/rework 시나리오)
- **examples/log-parser/로 이동 (인스턴스 언어측):**
  - 스킬 `dotnet-conventions`(.NET 규약), 페르소나 `dotnet-engineer`(.NET 구현)
  - 근거: 코어는 언어중립(ADR-0002). .NET은 로그파서 인스턴스가 project.toml `[languages]`에 선언한 언어. Python은 코어의 저작언어라 예외적으로 잔류.

### D-02 — new-normalization-rule 커맨드
- "normalization"은 경계에서 데이터를 정규화하는 **일반 개념**(반도체 전용 아님). 커맨드의 본질은 계약우선 순서 강제(계약 → (input,expected) 데이터케이스 → 코드).
- **결정:** 커맨드는 코어 잔류하되 본문에서 반도체 특화(equipment/보정규칙 예시)를 걷어내고 도메인 중립 예시(generic `greeting` 인스턴스 또는 추상 예)로 대체. 이름 유지(범용어). 계약우선 순서 로직 불변.

### D-03 — 언어 페르소나/스킬의 "이동 vs 설정 파생"
- Phase 5의 GEN-03은 **설정 SSOT + 일관성 테스트**(풀 코드젠 아님)로 확정됨. 5.5도 동일 기조: **소스를 정리(이동)하고, project.toml이 정본**임을 강화. 실제 per-language emit는 Phase 7.
- `dotnet-engineer`·`dotnet-conventions`를 `examples/log-parser/{agents,skills}/`로 이동 → 인스턴스가 자기 언어 자산을 소유. 코어에는 언어중립 페르소나만.
- 권한매트릭스의 `dotnet *` allow-scope는 project.toml 인스턴스 선언과 일관(GEN-03 테스트가 이미 커버) — 매트릭스 자체는 인스턴스 슬롯 데이터라 잔류/참조 OK. (코어 페르소나 파일이 `dotnet`을 prose로 명명하지 않으면 됨.)

### D-04 — GEN-04 가드 prose 확장
- Phase 5 가드(SCOPE A)는 `examples/`·`components/toy-converter`·`import examples`만. 5.5에서 **prose 도메인 참조**까지 확장하되 **신중**:
  - 코어에서 이동된-자산/도메인 토큰(`libs/dotnet`, `normalization-catalog`, `pipeline-patterns`, `dotnet-engineer`, `dotnet-conventions`, 반도체 어휘 `equipment`·`standard-log`·`wafer`·`설비` 등)을 flag.
  - **allowlist/신중:** 범용 단어(`normalize`, `.NET`을 일반 언급하는 문맥)는 오탐 위험 — 토큰을 구체적으로(경로/고유명) 한정하고, negative-control로 검증. 가드가 과잉이면 SCOPE-A로 후퇴하지 말고 토큰 목록을 정밀화.
  - 이동 후 코어 grep이 이 토큰들 0이어야 통과.

### D-05 — 문서/참조 갱신
- 이동한 스킬/페르소나의 새 위치를 `examples/log-parser/AGENTS.md`·`README.md`·관련 docs에 반영. 코어 문서(루트 AGENTS.md·CLAUDE.md)의 저작표면 목록에서 이동분 제거.
- `harness/skills`·`harness/agents` 구조 검증 테스트(`tools/harness_lint`)가 이동 후에도 그린 — 기대 스킬/페르소나 목록을 코어 잔류분으로 갱신(Phase 3의 anti-sprawl 테스트가 정확한 세트를 핀하므로 반드시 갱신).

### Claude's Discretion
- examples 하위 스킬/에이전트 정확 위치(`examples/log-parser/skills/` vs `.../harness-overlay/`), 제네릭화 예시 문안, 가드 토큰 목록·allowlist, harness_lint 기대목록 갱신 방식은 planner/researcher 재량.
- **고정:** 위 3분류(D-01), python은-코어·dotnet은-인스턴스, new-normalization-rule 잔류+제네릭화, 가드 prose 확장(신중), 로직 불변, 이동후 비-예시 스위트 그린.
</decisions>

<canonical_refs>
## Canonical References
- `.planning/ROADMAP.md §Phase 5.5`, `.planning/REQUIREMENTS.md GEN-05`, `docs/adr/0002-general-template-de-specialization.md`(범용화 정본)
- Phase 5 산출: `.planning/phases/05-despecialization/{05-CONTEXT,05-RESEARCH,05-05-*}.md`(가드·이동 선례), `examples/log-parser/`(이동 목적지 구조)
- 대상 인벤토리: `harness/skills/{normalization-catalog,pipeline-patterns,dotnet-conventions,data-contracts}/SKILL.md`, `harness/agents/{dotnet-engineer,python-engineer}.md`, `harness/commands/new-normalization-rule.md`
- 검증 대상: `tools/harness_lint/tests/{test_skills,test_agents,test_commands,test_core_no_example_dep}.py`(기대목록·가드 — 갱신·확장), `harness/project.toml`(언어 SSOT), `harness/permission-matrix.json`
</canonical_refs>

<code_context>
## Existing Code Insights
### Reusable Assets / Patterns (locked)
- Phase 5 가드(`test_core_no_example_dep.py`) = prose 확장의 직접 베이스.
- Phase 5 이동(`git mv` verbatim, 히스토리 보존, 비-예시 스위트 그린) = 스킬/페르소나 이동의 패턴.
- `tools/harness_lint` anti-sprawl 테스트가 정확한 스킬/페르소나 세트를 핀 → 이동 시 반드시 기대목록 갱신(안 하면 RED).
### Integration Points
- 이동 → harness_lint 기대목록 + 루트 문서 + 가드 토큰목록.
- 코어 페르소나가 `dotnet` prose 명명 제거 → 권한매트릭스는 project.toml 슬롯 데이터라 무관.
- 저작표면은 마크다운 — 런타임 로직 불변; emit(Phase 7)이 나중에 project.toml→per-language 산출.
</code_context>

<specifics>
## Specific Ideas
- 성공기준 데모: (1) `normalization-catalog`·`pipeline-patterns`·`dotnet-conventions`·`dotnet-engineer`가 `examples/log-parser/` 아래로 이동, 코어 harness/에서 사라짐; (2) `data-contracts`·`new-normalization-rule` 본문에 반도체 어휘 0; (3) 확장된 GEN-04 가드가 코어 prose 도메인 토큰 0 강제(negative-control 포함); (4) 비-예시 pytest 스위트 그린(harness_lint 기대목록 갱신 반영).
- 이동은 `git mv`로 히스토리 보존.
</specifics>

<deferred>
## Deferred Ideas
- per-language 저작표면 **emit**(project.toml→dotnet 페르소나 생성) → Phase 7 emitter.
- 추가 도메인 예시 → 후속.
- 스코프 이탈 없음.
</deferred>

---
*Phase: 5.5 — Authored-Surface Genericization (INSERTED, GEN-05)*
*Context gathered: 2026-07-09 (gray areas resolved with recommended defaults — AskUserQuestion unavailable; user gave explicit go-ahead "계속해")*
