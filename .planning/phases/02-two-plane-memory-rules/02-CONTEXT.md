# Phase 2: Two-Plane Memory + Rules - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning

<domain>
## Phase Boundary

헌법-vs-파생 메모리 분리를 **에이전트가 컨텍스트를 소비하기 전에** 확립한다. 파생 아티팩트는 재생성(손으로 관리 금지), 휘발 상태는 session-start에 주입 가능. (REQs: MEM-01/02/03, RULES-01/02, HOOK-05)

**In scope**: `.memory/` 두 평면 레이아웃 + gitignore 경계, repo-map(tree-sitter+PageRank) & contracts-index 생성기(재생성 증명), 루트+per-package AGENTS.md(nearest-wins) + CLAUDE.md 포인터, Claude SessionStart 주입기(포인터/인덱스 상한 주입 + provisional 마킹).
**Out of scope(이 페이즈)**: opencode.json/권한/에이전트 표면(Phase 3), 훅 강제(HOOK-01~04, Phase 4), CI(Phase 5). 도메인 확정값(프로젝트 Out of Scope).
</domain>

<decisions>
## Implementation Decisions

### HOOK-05 런타임 비대칭 (session-start injection)
- **D-01:** **Claude SessionStart 주입기는 지금 실제 구현·테스트**(이 dev 환경이 Claude). **opencode측(`event`=session.created + `chat.system.transform`)은 소스만 authored하고 실행 검증은 deferred** — 이 컨테이너에 opencode 런타임이 없음(.NET 딜퍼와 동일 패턴). 두 런타임이 **동일한 주입 계약**(같은 페이로드·같은 상한·같은 provisional 규칙)을 공유하도록 계약을 먼저 고정.
- **D-02:** 주입은 **무시 불가**(Claude: SessionStart hook stdout → additionalContext). 주입 내용에는 "휘발 상태는 provisional; ADR/contract가 항상 우선" 배너를 포함(성공기준 4).

### .memory/ gitignore vs 커밋 경계 (MEM-02)
- **D-03:** **`.memory/derived/`(repo-map·contracts-index) = gitignore**(SessionStart가 재생성), **`.memory/state/`(activeContext·progress) = 커밋**. ephemeral 컨테이너라 파생물은 매 세션 재생성하되 소량 상태는 세션을 넘겨 유지(Phase 1 `/checkpoint` 취지). → 로드맵 성공기준 1의 "`.memory/` gitignore"를 **"파생물만 gitignore, 소량 상태는 커밋"**으로 정련(ephemeral 제약 반영; GSD `.planning/`도 같은 이유로 상태를 커밋).
- **D-04:** 파생물은 **손으로 관리 금지** — 삭제 후 생성기 재실행이 동일 재현(성공기준 2). 생성기 출력 상단에 "DERIVED — do not hand-edit" 마커.

### 파생 아티팩트 생성기 (MEM-03)
- **D-05:** **repo-map = tree-sitter + networkx PageRank**(CLAUDE.md 권장, PyPI 설치 가능), 심볼 그래프 → PageRank 랭킹 → 토큰 예산 상한 내 top-N elided defs. **contracts-index = `contracts/**/*.schema.json` + YAML 스펙 스캔** → 계약 목록·owner·drift 해시 상태 인덱스. 둘 다 `.memory/derived/`에 출력, `libs/python` 또는 `tools/`의 재생성 스크립트로.
- **D-06:** 생성기는 계약/코드에서만 파생(GSD `.planning/`에 비의존) — **독립 two-plane** 유지(프로젝트 결정).

### session-start 주입 예산 (MEM-02/HOOK-05)
- **D-07:** 주입 = **포인터·인덱스 요약 ~1k 토큰 cap**: contracts-index 요약 + repo-map top-N + activeContext 포인터 + 현재 drift 상태. **계약 전문은 주입 금지**(에이전트가 필요 시 직접 read). 상한 초과 시 truncate가 아니라 우선순위 절단(포인터 우선).

### Claude's Discretion
- repo-map 토큰 예산 정확값(~1k 기본), tree-sitter 그래머 설치 방식, contracts-index 스키마 세부, AGENTS.md 문안, 디렉터리 세부 네이밍은 planner/researcher 재량. 단 nearest-wins·독립 two-plane·provisional-우선·파생물-재생성 원칙은 고정.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 리서치 & 결정
- `.planning/research/SUMMARY.md` — Phase 2 스파인(파생 평면 + .memory/ + nearest-wins + session-start injection, bloat 방지)
- `.planning/research/ARCHITECTURE.md` — two-plane 아키텍처(헌법/파생), 주입 전략(SessionStart·instructions glob·on-demand·queryable index)
- `.planning/research/PITFALLS.md` — P11(nested AGENTS.md 런타임별 병합 차이 → 불변식은 훅에), P12(파생 문서 rot), P13(auto-captured 메모리 오도)
- `.planning/PROJECT.md` — Memory 제약(two-plane, 파생물 손관리 금지, 결정=append-only ADR), 독립 메모리 결정
- `.planning/ROADMAP.md` §Phase 2 — Goal·성공기준 4개
- `CLAUDE.md` — Context-memory tooling 표(tree-sitter grammars, py-tree-sitter, networkx 3.x PageRank, memory-bank 규약, SessionStart injection)

### Phase 1 기존 자산(재사용/연동)
- `contracts/` + `contracts/.hashes/manifest.json` — contracts-index가 인덱싱할 대상 + drift 상태 소스
- `docs/adr/`, `docs/glossary.md` — 헌법 평면 구성원(주입기가 포인터로 참조)
- `.claude/settings.json` — 기존 SessionStart 훅(GSD 2개 + Phase 1 부트스트랩) — 주입기 훅은 여기에 **공존** 추가(덮어쓰기 금지)
- `tools/bootstrap/` — SessionStart 와이어링 선례
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Phase 1 SessionStart 훅 패턴**(`.claude/settings.json` + `tools/bootstrap`): 주입기 훅을 같은 배열에 공존 추가하는 선례.
- **`contracts/.hashes/manifest.json`**(01-05): contracts-index가 drift 상태를 읽어올 소스.
- **`libs/python`**(01-04): Python 생성기 코드의 워크스페이스 멤버 자리.
- **uv 워크스페이스**(01-01): tree-sitter·networkx를 `uv add`로 추가(PyPI 허용).

### Established Patterns (locked)
- **독립 two-plane**: 헌법(사람 소유·게이트) vs 파생/휘발(자동). GSD `.planning/` 비의존.
- **파생물 재생성**: 삭제→재실행→동일 재현. 손편집 금지.
- **provisional 우선순위**: 휘발 상태는 잠정, ADR/contract가 우선.
- **런타임 비대칭은 훅으로**: nested AGENTS.md 병합이 런타임마다 달라(P11), 비타협 불변식은 상속 prose가 아니라 훅/주입기에.

### Integration Points
- **주입기 훅 ↔ .claude/settings.json** SessionStart 배열(공존).
- **contracts-index ↔ contracts/ + .hashes** (drift 상태 표면).
- **repo-map ↔ libs/·tools/·components/** 심볼 그래프.
- **opencode측 주입 stub ↔ Phase 3 CONFIG**(opencode.json instructions/plugin이 실제 배선될 자리).
</code_context>

<specifics>
## Specific Ideas
- 성공기준 2 데모: `.memory/derived/repo-map.md`·`contracts-index.md` 삭제 → 생성기 재실행 → git diff 없음(동일 재현) = "손편집 아님" 증명.
- 성공기준 4 데모: 주입 페이로드가 계약 전문이 아니라 포인터/인덱스이고 상한 이내이며 provisional 배너 포함.
- opencode측 주입은 authored-stub(실행 deferred) — DOTNET-RESUME.md처럼 "opencode 런타임 붙으면 검증" 노트.
</specifics>

<deferred>
## Deferred Ideas
- opencode 런타임에서의 주입 실검증 → opencode 표면(Phase 3 CONFIG) 또는 opencode 설치 후.
- 파생물 증분 캐시(diskcache) 최적화 → 필요 시 후속.
- 스코프 이탈 없음.
</deferred>

---

*Phase: 2-Two-Plane Memory + Rules*
*Context gathered: 2026-07-08 (gray areas resolved with recommended defaults — AskUserQuestion tool was unavailable; adjustable on request)*
