# Phase 7: Single-Source Dual-Runtime Emitter — Context

**Gathered:** 2026-07-11 (discuss-phase, --text mode)
**Status:** Ready for research → planning. All gray areas locked to recommended defaults (user: "기본값").
**Mode:** mvp

<domain>
## Phase Boundary

정본 하네스 소스 `harness/`를 **두 런타임-네이티브 아티팩트 세트**로 컴파일한다: opencode(1차) + Claude Code(2차). Phase 2–5·8이 채운 `harness/` 소스의 순수 함수 — 마지막에 짓는 이유. 산출물이 하네스 자체(로그파서 예제 아님)를 두 런타임으로 emit하는 것.

**In scope:**
- `tools/harness_emit/` — `harness/{agents,commands,skills,plugins}` + 설정을 소비하는 emitter
- opencode 산출: `.opencode/{agent,command,skill,plugin,tool}` + `opencode.json`(15키 권한 매트릭스) + `AGENTS.md`
- Claude 산출: `.claude/{agents,commands,skills}` + `settings.json` + `CLAUDE.md` — **GSD 자산 미접촉**
- per-runtime 한계 검증기(loud-fail): Claude 스킬 name≤64/desc≤1024/body<~500, opencode 권한 매트릭스 형태
- CI 재-emit-diff 드리프트 게이트(Phase 6 contract-drift 패턴 재사용)

**Out of scope:**
- 멀티레포 emit → v2-γ
- curator 자동 최신화(파생물 훅) → v2-α
- opencode 런타임 실동작(미설치 — 구조/실행가능 검증만; 실런은 opencode 설치 후)
- 예제 도메인 콘텐츠 emit(하네스만 emit; examples/는 별개)
</domain>

<decisions>
## Implementation Decisions (locked — planner refines mechanics)

- **D-01 Emitter 언어 = Python.** `tools/harness_emit/`(기존 모든 `tools/*`가 Python — harness_config/contract_drift/golden_runner와 일관, CI에 자연 편입). `.ts` 플러그인은 **생성이 아니라 verbatim 복사**(opencode `.opencode/plugin/`로) — Node 툴체인 불필요. (CLAUDE.md 스택표의 Node/adapters 제안은 이 이유로 미채택; 소스가 이미 Markdown+TS라 transpile 대상이 아님.)
- **D-02 emit 산출물은 커밋 + 재-emit-diff 드리프트 게이트(가장 중요).** `.opencode/`와 emit된 `.claude/{agents,commands,skills}`(+ opencode.json/AGENTS.md/settings.json/CLAUDE.md 관리 블록)는 **커밋**된다 — 그래야 성공기준 4(CI가 재emit해서 diff나면 fail)가 성립. Phase 6 `tools/contract_drift`/CI 게이트 패턴을 그대로 확장. 산출물은 "손편집 금지 파생물"이지만 **기계가 쓰고 CI가 검증** = 두 평면 원칙 위배 아님. (v2-α가 이 패턴을 파생물 전체로 재사용.)
- **D-03 `.claude/` 안 GSD 공존 = 매니페스트 소유 + 병합.** emitter는 **자기가 쓴 파일의 명시적 매니페스트만** 소유하고, `gsd-*` 파일·`.claude/get-shit-done/`·`.claude/hooks/`(GSD 소유)는 **절대 안 건드림**. 하네스 아티팩트는 `gsd-`와 충돌 안 하도록 네임스페이스. `settings.json`·`CLAUDE.md`·`AGENTS.md`는 **덮어쓰기 아니라 관리-마커 블록 병합**(GSD/사람 콘텐츠 보존).
- **D-04 소스는 런타임-중립, emitter가 유일한 특화 지점.** `harness/` frontmatter는 런타임-중립 유지; emitter가 매핑 표 하나로 특화 — opencode(`mode: subagent`, `permission-matrix.json`→`opencode.json` 15키), Claude(`.claude/*` + `settings.json`). 소스에 런타임 형태를 박지 않는다(단일소스 정본 유지).
- **D-05 MVP 슬라이스 = 에이전트 먼저.** 걷는 골격: 에이전트(4개)를 소스→양 런타임→검증기→CI diff까지 end-to-end 관통(frontmatter 매핑+검증기+드리프트 게이트 전부 훑음). 이후 커맨드→스킬→플러그인→설정 순 확장.

### 이미 확정 (✔)
- 타깃 경로/파일 세트(위 In scope), 검증기 loud-fail, `.claude/get-shit-done/` 미접촉, wshobson 단일소스→어댑터 패턴.

### Claude's Discretion
- emitter 내부 모듈 분할, 매핑 표 세부, 매니페스트 형식, 병합 마커 문법, 검증기 배치(emit-time + CI 둘 다), CI 잡 이름은 researcher/planner 재량.
- **고정:** Python emitter·커밋되는 산출물+드리프트 게이트·GSD 미접촉/병합·소스 런타임-중립·에이전트-우선 MVP·모델 식별자 없음.
</decisions>

<canonical_refs>
## Canonical References (downstream MUST read)

- `.planning/ROADMAP.md §Phase 7`(4 성공기준), `.planning/REQUIREMENTS.md §EMIT`(EMIT-01/02)
- `CLAUDE.md` — "Single-Source → Multi-Runtime Emit(generation layer)" 표(wshobson 패턴, `.opencode/agent/<name>.md` `mode: subagent`, Claude `.claude/agents/`), "Emit-time validators"(Claude 스킬 name≤64/desc≤1024/body<500; opencode 15키), 런타임 제약
- 소스: `harness/{agents,commands,skills,plugins}`, `harness/permission-matrix.json`, `harness/opencode.json`, `harness/opencode.config.schema.json`, `harness/project.toml`
- 재사용 패턴 선례: `tools/contract_drift`+`tools/contract_hash`(재-emit-diff 드리프트 게이트의 원형), `.github/workflows/ci.yml`(Phase 6 게이트에 emit-drift 잡 추가), `tools/harness_config/loader.py`(설정 로더 관용구)
- 공존 대상(미접촉): `.claude/get-shit-done/`, `.claude/agents/gsd-*`, `.claude/commands/`(gsd-*), `.claude/hooks/`
- `.planning/MILESTONE-CONTEXT.md`(v2-α가 D-02 드리프트 패턴을 파생물 전체로 확장)
</canonical_refs>

<specifics>
## Specific Ideas
- 성공기준 데모(opencode 미설치 → 구조/실행가능 검증): (1) `tools/harness_emit`가 `.opencode/*`+`opencode.json`+`AGENTS.md`를 `harness/`에서 생성; (2) 같은 소스가 `.claude/*`+`settings.json`+`CLAUDE.md` 생성하되 `get-shit-done/` 미접촉; (3) 한계 위반 시 검증기가 truncate 아니라 build FAIL; (4) CI가 재emit→diff로 손편집 드리프트 포착.
- emit-drift 게이트는 Phase 6 CI에 잡 1개 추가(재emit → `git diff --exit-code` on 산출 경로).
</specifics>

<deferred>
## Deferred Ideas
- 멀티레포/워크스페이스 emit → v2-γ
- curator 자동 파생물 최신화(훅) → v2-α
- opencode 런타임 실행 검증 → opencode 설치 후
- 스코프 이탈 없음
</deferred>

---
*Phase: 07 — Single-Source Dual-Runtime Emitter (EMIT-01/02, mvp)*
*Context gathered 2026-07-11 via discuss-phase --text; all gray areas locked to defaults.*
