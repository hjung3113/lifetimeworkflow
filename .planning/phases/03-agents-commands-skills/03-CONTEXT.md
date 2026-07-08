# Phase 3: Agents + Commands + Skills - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning

<domain>
## Phase Boundary

전체 하네스 표면을 **중립 단일소스**에 저작한다 — golden-adjacent 커맨드가 마이그레이션 커맨드보다 먼저, 마이그레이션은 *신뢰된* 골든망 뒤에 게이트. (REQs: CONFIG-01/02, AGENT-01..05, CMD-01..09, SKILL-01/02, DOCS-03)

**In scope**: `harness/` 단일소스(opencode.json+권한매트릭스, 5 agent 페르소나, 9 command, 스킬셋), 권한 last-wins 리졸버(순수함수), `/docs-sync`(계약→docs/reference 생성기, DOCS-03, 실행가능), 구조 검증.
**Out of scope(이 페이즈)**: 단일소스→런타임 emit(Phase 6), on-write 훅 강제(HOOK-01~04, Phase 4), CI(Phase 5). opencode 런타임 실동작(런타임 부재 → deferred).
</domain>

<decisions>
## Implementation Decisions

### 단일소스 위치 & 산출 모델
- **D-01:** 하네스 표면을 **중립 `harness/` 단일소스**에 저작: `harness/agents/*.md`, `harness/commands/*.md`, `harness/skills/*/SKILL.md`, `harness/plugins/*.ts`, `harness/opencode.json`(+권한매트릭스). **Phase 6 emitter가 여기서 `.opencode/`와 `.claude/`를 산출**(사용자 결정 "opencode 우선 + 단일소스로 Claude 생성"; Phase 2가 이미 `harness/plugins/session-inject.ts`를 씀 — 일관). Phase 3는 소스만 만들고 런타임 설치/emit은 Phase 6.
- **D-02:** opencode/Claude 런타임 실동작은 이 컨테이너에서 검증 불가(opencode 미설치) → **구조 검증으로 대체**: opencode.json JSON-Schema 유효, frontmatter 유효, 스킬 크기상한 검사, 권한매트릭스 well-formed. 라이브 런타임 로딩은 deferred(.NET/opencode 딜퍼 패턴). **단, 순수-로직/생성기는 실제 실행·테스트한다**(아래 D-04·D-06).

### 권한 & 설정 (CONFIG-01/02)
- **D-03:** `harness/opencode.json`: 모델 티어링(explorer 저가 / implementer 고가), instructions glob(AGENTS.md + contracts/**), formatter(ruff/dotnet format), MCP 와이어링(config-only). 15키 권한 매트릭스는 별도 데이터로 두고 **last-wins glob 리졸버를 Python 순수함수로 구현·유닛테스트**(`*:ask` → `dotnet *:allow`·`uv *:allow`·`git push*:ask`; reviewer 읽기전용; secret/constitution 쓰기 deny; `*.env` deny). 리졸버는 Phase 4 훅이 재사용.

### 에이전트 페르소나 (AGENT-01..05)
- **D-04:** 5 페르소나 = markdown + frontmatter(description=라우팅 신호 3인칭·구체, model tier, permission scope, tools allowlist): orchestrator(primary), dotnet-engineer(`dotnet *`), python-engineer(`uv *`·`pytest *`), code-reviewer(읽기전용 Read/Grep/Glob·bash/edit 없음), explorer(저가 모델). frontmatter 스키마를 **구조 검증**(description 비어있지 않음, permission 유효, reviewer에 write/bash 없음).

### 커맨드 (CMD-01..09)
- **D-05:** 9 커맨드 = markdown 프롬프트 매크로, Phase-1 tools 캡슐화. 시퀀스: golden-adjacent(`/build`·`/test`·`/lint`·`/golden`·`/golden-approve`·`/adr`·`/checkpoint`·`/component`) 먼저, 마이그레이션(`/new-normalization-rule`·`/strangler-step`·`/docs-sync`) 나중. `/strangler-step`은 **캡처된 legacy 골든 baseline 없이는 거부** + 한 경로만 추출 + `/golden` 패리티 필수(성공기준 4). `/build`의 dotnet 부분은 .NET 게이트(스크립트가 dotnet 부재 시 명확히 스킵/안내).
- **D-06:** **`/docs-sync`(DOCS-03)는 실행 가능한 Python 생성기**(memory_regen 패턴): `contracts/` → `docs/reference/*.md` 파생, 손작성 금지. 삭제+재생성 동일(결정론) — 실제 실행·테스트. `/new-normalization-rule`은 순서 강제 로직(계약→(input,expected) 데이터케이스→코드)을 스캐폴드로.

### 스킬 (SKILL-01/02)
- **D-07:** 코어 스킬(dotnet-conventions·python-conventions·golden-testing·data-contracts) + skill-creator(메타) + 도메인(normalization-catalog·pipeline-patterns[carryover·시나리오]). progressive disclosure(frontmatter 상시 + 본문 지연). **런타임 크기상한 구조 검증**: Claude SKILL.md name ≤64·desc ≤1024·body <~500줄; opencode/기타 상한. emit-time 검증기 본체는 Phase 6, 여기선 소스가 상한 준수하는지 체크.

### Claude's Discretion
- 커맨드/스킬/에이전트 문안, harness/ 세부 트리, 권한 매트릭스 정확한 glob 목록, docs/reference 생성 포맷, MCP 서버 선택은 planner/researcher 재량. 단 단일소스=harness/·golden-adjacent-먼저·reviewer-읽기전용·docs-sync-파생·런타임-실동작-deferred는 고정.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 리서치 & 결정
- `.planning/research/SUMMARY.md`(Phase 3 스파인: 전 표면 저작, golden-adjacent 먼저), `FEATURES.md`(P1/P2 커맨드·에이전트·스킬 목록·복잡도·의존그래프), `STACK.md`(opencode.json 스키마·권한 15키·스킬 크기상한), `ARCHITECTURE.md`(단일소스→dual emit), `PITFALLS.md`(P6 런타임 상한, P7 description-as-label, P8 skill sprawl, P5 emit drift)
- `.planning/PROJECT.md`(런타임 제약·단일소스·모델 아이덴티티), `.planning/ROADMAP.md §Phase 3`(4 성공기준)
- `CLAUDE.md`(opencode 15키 권한·스킬 크기상한·wshobson 단일소스 패턴·기술스택)

### Phase 1·2 기존 자산(커맨드/에이전트가 감쌈)
- `tools/` (contract_drift·contract_hash·golden_runner·memory_regen) — `/build /test /lint /golden /docs-sync` 등이 호출
- `harness/plugins/session-inject.ts`(Phase 2) — harness/ 단일소스 선례
- `AGENTS.md` + per-package(Phase 2) — 에이전트가 참조할 규칙
- `.memory/`, `contracts/`, `docs/` — 커맨드·스킬의 대상
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Phase-1 tools**(pytest·ruff·contract_drift·golden_runner) = 커맨드가 감쌀 정본 호출.
- **memory_regen 생성기 패턴**(Phase 2) = `/docs-sync` 생성기의 직접 템플릿(결정론·DERIVED 마커).
- **`harness/plugins/`**(Phase 2) = 단일소스 트리 선례.
- **권한/에이전트 개념**: `.claude/agents/`(GSD)가 frontmatter 에이전트의 참고 형태.

### Established Patterns (locked)
- 단일소스 → dual emit(Phase 6). 런타임 실동작 deferred.
- golden-adjacent 먼저, 마이그레이션은 신뢰된 골든 뒤.
- reviewer 읽기전용·description=라우팅신호·least-privilege tools.
- 파생(docs/reference)=생성기, 손작성 금지.

### Integration Points
- opencode.json instructions glob ↔ AGENTS.md + contracts/**.
- 권한 리졸버(순수함수) ↔ Phase 4 훅 재사용.
- 커맨드 ↔ Phase-1 tools CLI.
- /docs-sync ↔ contracts/ → docs/reference/.
- harness/ 소스 ↔ Phase 6 emitter 입력.
</code_context>

<specifics>
## Specific Ideas
- 성공기준 검증(런타임 없이): opencode.json이 JSON-Schema 유효 + 권한 리졸버 유닛테스트(last-wins·default-deny·reviewer-읽기전용) + frontmatter/스킬-크기 구조 테스트 + `/docs-sync` 삭제+재생성 결정론(실행).
- `/strangler-step` 거부 데모: 골든 baseline 없으면 non-zero 종료.
- 스킬 크기상한: 저작 시 Claude 한도(name≤64·desc≤1024·body<500) 준수 체크(구조).
</specifics>

<deferred>
## Deferred Ideas
- 단일소스 → `.opencode/`+`.claude/` 실제 emit + per-runtime 검증기 본체 → Phase 6.
- opencode 런타임에서 에이전트/커맨드/권한 실로딩 검증 → opencode 설치 후.
- 커맨드의 dotnet 경로 실행 → .NET 정책 열림 후.
- 스코프 이탈 없음.
</deferred>

---

*Phase: 3-Agents + Commands + Skills*
*Context gathered: 2026-07-08 (gray areas resolved with recommended defaults — AskUserQuestion unavailable; adjustable on request)*
