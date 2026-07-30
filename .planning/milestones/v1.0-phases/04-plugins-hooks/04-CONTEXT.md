# Phase 4: Plugins + Hooks - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1-3에서 저작한 규칙을 **무시 불가 훅으로 런타임 강제**한다 — prose는 조언, 훅은 강제. (REQs: HOOK-01/02/03/04, POLY-01)

**In scope**: 강제 로직(Python, 재사용) + Claude 훅 와이어링(이 dev env에서 실동작·테스트) + opencode 플러그인 stub(authored/deferred). contract-guard·format-on-write·secret·commit-gate·폴리글랏 린터.
**Out of scope(이 페이즈)**: 실제 emit(Phase 6), CI(Phase 5). opencode 플러그인 런타임 실동작(런타임 부재→deferred). 커밋게이트의 골든-패리티 실행(.NET 게이트).
</domain>

<decisions>
## Implementation Decisions

### 강제 로직 위치 & 이중 런타임 (전 REQ)
- **D-01:** 강제 로직을 **재사용 가능한 Python**으로 구현하고, **Claude 훅**(`.claude/settings.json` PreToolUse/PostToolUse/Stop)으로 와이어링해 **이 dev 환경에서 실동작·유닛테스트**한다. **opencode 플러그인**(`harness/plugins/*.ts`: `tool.execute.before/after`)은 **같은 Python 로직을 감싸는 stub으로 authored, 실행 검증 deferred**(opencode 런타임 부재; .NET/opencode 딜퍼 패턴). 두 런타임이 동일 강제 계약 공유.
- **D-02:** 훅은 03-01의 **권한 리졸버**(`tools/harness_perms`)와 Phase-1 **정규화 코어**(`libs/python/normalize`)를 **재사용**(재구현 금지, 성공기준 2 "built once").

### POLY-01 폴리글랏 경계 린터
- **D-03:** `tools/polyglot_lint/` — `integration_contracts §4.3~4.6` 체크리스트(인코딩·BOM·LF·TSV 이스케이프·타임존·소수점/로케일·null-vs-empty·쓰기 원자성·식별자/구간)를 **실행 가능한 규칙**으로. 정규화 코어 재사용, on-write(훅) + in-session(커맨드/CI) 실행, **fail loud**. 유닛테스트로 위반 검출 증명.

### HOOK-04 contract-guard
- **D-04:** PreToolUse 훅 — `contracts/`·`docs/adr/`·`golden/`(헌법 평면) 쓰기를 **승인 경로 없이 차단/ask**(03-01 리졸버 path-deny 재사용), + on-write 인코딩/TSV 규칙 강제. 성공기준 1.

### HOOK-01 format-on-write · HOOK-02 secret
- **D-05:** format-on-write = PostToolUse — LF/no-BOM/InvariantCulture 강제(언어중립 Python; py는 ruff format 연동; **dotnet-format 부분은 .NET 게이트 → dotnet 부재 시 skip-gracefully**). secret protection = PreToolUse deny-list + 패턴 스캔(read/write 차단). 성공기준 3.

### HOOK-03 commit-gate
- **D-06:** Stop/pre-commit 훅 — **contract-drift(01-05) + 골든-패리티(01-06, .NET 게이트 skip) + 폴리글랏 린터(POLY-01)** 실패 시 커밋 차단. + 성공기준 4의 **권한매트릭스 order-resolution 스위트**(03-01 리졸버 테스트 확장: last-wins·default-deny·헌법 평면 edit deny 증명).

### Claude's Discretion
- 훅 스크립트 세부·디렉터리 네이밍·secret 패턴 목록·플러그인 stub 형태·린터 규칙 정확 구현은 planner/researcher 재량. 단 로직-재사용(리졸버·정규화코어)·이중런타임(Claude 실동작/opencode deferred)·fail-loud·헌법-평면-차단은 고정.
</decisions>

<canonical_refs>
## Canonical References
**Downstream agents MUST read these before planning or implementing.**
- `.planning/research/SUMMARY.md`(Phase 4 스파인: 런타임 강제, 비타협은 훅에), `PITFALLS.md`(P11 런타임별 병합→불변식은 훅), `ARCHITECTURE.md`(safety 게이트 데이터흐름)
- `.planning/PROJECT.md` ; `.planning/ROADMAP.md §Phase 4`(4 성공기준) ; `CLAUDE.md`(§4.3~4.6 canonicalization 표, 골든 comparator 빌딩블록)
- `/workspace/presentationformat/archive/parserimprove/uploads/integration_contracts_design.md` §4.3~4.6·§5 체크리스트 — POLY-01 규칙 정본
- **재사용 자산**: `tools/harness_perms/resolver.py`(03-01 권한 path-deny) · `libs/python/normalize/`(Phase-1 정규화 코어) · `tools/contract_drift/`(01-05) · `tools/golden_runner/`(01-06) · `.claude/settings.json`(기존 훅 4슬롯 — 공존 추가) · `harness/plugins/session-inject.ts`(플러그인 stub 선례)
</canonical_refs>

<code_context>
## Existing Code Insights
### Reusable Assets
- `tools/harness_perms/resolver.py` — contract-guard의 path-deny 판정.
- `libs/python/normalize/` — 폴리글랏 린터의 §4-5 정규화(built once).
- `tools/contract_drift/`·`tools/golden_runner/` — commit-gate가 조합.
- `.claude/settings.json` SessionStart 4슬롯 — 훅 공존 추가 선례; PreToolUse/PostToolUse/Stop는 신규.
- `harness/plugins/session-inject.ts` — opencode 플러그인 stub 형태.
### Established Patterns (locked)
- 비타협 불변식은 상속 prose가 아니라 훅(P11). Claude 실동작 / opencode deferred. fail loud. 로직 재사용(재구현 금지).
### Integration Points
- contract-guard/secret ↔ PreToolUse(Edit/Write/Read). format-on-write ↔ PostToolUse. commit-gate ↔ Stop/pre-commit. 전부 `.claude/settings.json`에 공존 추가 + `harness/plugins/*.ts` stub.
</code_context>

<specifics>
## Specific Ideas
- 성공기준 데모(런타임): contracts/ 편집 시 contract-guard가 차단(테스트); BOM/CRLF 넣은 TSV가 폴리글랏 린터 fail; secret 패턴이 차단; 커밋게이트가 drift/린터 실패 시 non-zero.
- 골든-패리티 조합은 .NET 부재 시 skip-gracefully(딜퍼), 나머지 게이트는 실동작.
</specifics>

<deferred>
## Deferred Ideas
- opencode 플러그인 런타임 실동작 → opencode 설치 후.
- 커밋게이트 골든-패리티 실행 → .NET 정책 열림 후.
- 스코프 이탈 없음.
</deferred>

---
*Phase: 4-Plugins + Hooks*
*Context gathered: 2026-07-08 (gray areas resolved with recommended defaults — AskUserQuestion unavailable; adjustable on request)*
