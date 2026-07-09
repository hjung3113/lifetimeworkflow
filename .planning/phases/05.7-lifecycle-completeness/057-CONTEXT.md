# Phase 5.7: Lifecycle Completeness — Context

**Gathered:** 2026-07-09
**Status:** COMPLETE (2026-07-09 next session) — research→plan→execute done; see 057-RESEARCH/VALIDATION/01-PLAN/02-PLAN + 057-0{1,2}-SUMMARY. Non-example suite green (402); LIFE-01..11 all delivered.
**Origin:** User-requested adversarial review — "skills/commands/agents too thin for an agent to carry work through the full dev lifecycle." A full authored-surface audit (subagent, 2026-07-09) confirmed concrete, load-bearing gaps.

<domain>
## Phase Boundary

게이트·계약·메모리·안전망은 탄탄하나, **에이전트가 한 작업 단위를 온보딩→계획→구현→계약검증→테스트→디버그→리뷰→문서→리팩터→통합까지 끌고 갈 저작 자산**이 얇다. 이 페이즈는 적대적 감사에서 드러난 갭을 **도메인 중립**으로 보강한다. (신규 REQ: LIFE-01..11)

**In scope**: 라이프사이클 각 단계의 부족한 스킬·커맨드·에이전트 자산을 신규 저작 또는 보강. 전부 코어(도메인 중립), GEN-04 가드 준수(examples/도메인 참조 0), 스킬 상한(name≤64/desc≤1024/body<500, progressive disclosure), reviewer 읽기전용, 최소권한, 모델 식별자 없음.

**Out of scope (이 페이즈)**:
- Phase 6 CI(비-세션 게이트) / Phase 7 emitter(런타임 산출)
- 런타임 실동작 검증(opencode 미설치 — 구조/실행가능 검증만; .NET 게이트는 계속 deferred)
- 로그파서 도메인 콘텐츠(examples/에 속함)
- 기존 ADEQUATE 자산 재작성(golden-testing·docs-sync·adr·strangler-step·component은 충분 — 손대지 말 것)
</domain>

<audit_findings>
## Adversarial Audit — Sufficiency Table (2026-07-09)

| 단계 | 현재 자산 | 판정 | 근거 |
|---|---|---|---|
| Orient/onboard | AGENTS.md golden-path 표; session-inject.ts(런타임 deferred) | THIN | 저작된 `/orient`·온보딩 스킬 없음 |
| Plan/decompose | orchestrator.md 라우팅 prose | MISSING | 배포 하네스에 task-intake→plan 흐름 없음(GSD는 dev-side 전용, emit 안 됨) |
| Implement | component, new-normalization-rule(도메인), python-engineer | THIN | 코어에 python 엔지니어뿐; 중립 엔지니어 템플릿 없음; 하네스 확장(tool/plugin 저작) 스킬 없음 |
| Contract work | data-contracts 스킬 | THIN→MISSING | `/contract-check` 참조되나 **부재**; 스키마 저작 가이드 stub |
| Test/golden | golden-testing 스킬, /golden, /golden-approve, /test | ADEQUATE | 유지 |
| Debug/diagnose | (없음) | MISSING | 골든 미스매치/§4.3-4.6 repr 버그 진단 커맨드·스킬 제로 — 프로젝트 최고난도·최고가치 작업 |
| Review | code-reviewer 에이전트, /lint, secret-scan | THIN | 리뷰 워크플로 커맨드 없음(diff→reviewer→findings) |
| Document | docs-sync, adr, Diátaxis | ADEQUATE | 유지 |
| Refactor/migrate | strangler-step, component | ADEQUATE | 유지 |
| Integrate/release | checkpoint | MISSING | 상태 영속만; pre-handoff self-verify/통합 흐름 없음(CI=Phase6는 별개) |
| X-cut: 폴리글랏 §4.3-4.6 모델 | golden-testing+data-contracts+AGENTS.md 산재 | THIN | Core Value에 전용 progressive-disclosure 스킬 없음 |
| X-cut: 게이트/강제 모델 | AGENTS.md prose + permission-matrix _note | MISSING | 무엇이 왜 gated인지 스킬 없음 |
| X-cut: 두 평면 메모리 모델 | AGENTS.md prose | MISSING | 헌법-vs-파생/커밋-vs-gitignore 규칙 스킬 없음 |
| X-cut: orchestrator 라우팅 | orchestrator.md 본문(간략) | THIN | 라우팅 휴리스틱이 짧은 prose |

**검증된 구조 사실(load-bearing):**
- `/contract-check` 부재이나 `harness/commands/new-normalization-rule.md:24` + `CLAUDE.md:57,70,115`가 참조 → **dangling command**.
- 코어에 중립 language-engineer 패턴 없음(python-engineer만; dotnet-engineer는 examples/로 이동). `project.toml [[languages]].persona`가 가리킬 파일을 코어가 생성할 방법 없음 → 2번째 인스턴스 언어에서 "채워쓰는 템플릿" 주장 실패.
- `/new-normalization-rule` 커맨드가 도메인 명명("normalization/correction rules")으로 코어에 잔류 + 부재 커맨드 참조 → GEN-05 잔여 + GEN-04 prose-가드 위반 위험.
</audit_findings>

<decisions>
## Implementation Decisions (proposed additions — planner refines)

### MUST-HAVE (없으면 내부 루프가 깨짐 — 우선 웨이브)
- **D-01 LIFE-01 `/contract-check` 커맨드(신규):** `check-jsonschema` + 드리프트-해시 비교 래핑(기존 `tools/contract_drift`·`tools/contract_hash` 재사용). `contracts/**` 제네릭 소비. `new-normalization-rule`·CLAUDE.md의 dead link 해소.
- **D-02 LIFE-02 `golden-debug` 스킬(+선택 `/diagnose-golden` 커맨드)(신규):** 골든 red → 7 canonicalization 축(BOM/CRLF/InvariantCulture 소수점/float 허용오차/행키 정렬/UTC 타임존/TSV-이스케이프-vs-null) 결정트리 — 축별 "이게 원인인지 판별법" + "어느 쪽을 고칠지". 도메인 중립(§4.3-4.6 코어 대상). **최대 갭.**
- **D-03 LIFE-03 `polyglot-boundary` 스킬(신규):** §4.3-4.6 불변식을 1개 always-frontmatter 스킬로 통합(현재 3파일+prose 산재). body는 CLAUDE.md canonicalization 표를 `references/`로 참조(상한 준수). Core Value를 tribal→스킬.
- **D-04 LIFE-04 중립 language-engineer 템플릿/`/add-language` 스캐폴드(신규):** 중립 `engineer` 페르소나 템플릿(스코프·contract-first·§4.3-4.6·golden-gate 보일러플레이트) → 새 인스턴스 언어 엔지니어를 손저작 아닌 파생. `project.toml` 흐름과 연결. python-engineer는 코어 잔류(하네스 저작언어)이되, 템플릿에서 파생 가능함을 보여줄 것.
- **D-05 LIFE-05 `/new-normalization-rule` 탈도메인화:** 중립 `/new-contract-rule`로 일반화(계약엔트리 → `(input,expected)` 데이터케이스 → 실패 스텁; "normalization" 명명 제거) 코어 잔류, **또는** examples/로 이동(형제 스킬처럼). planner가 택1. GEN-05 잔여 + GEN-04 가드 정합 확보.

### SHOULD-HAVE (라이프사이클 완성 — 후속 웨이브)
- **D-06 LIFE-06 `/orient` 커맨드/온보딩 스킬:** 결정론적 "이 순서로 읽어라 + golden-path" 진입점. `tools.memory_regen` 산출 + AGENTS.md golden-path 래핑. injector D-02-deferred 의존 탈피.
- **D-07 LIFE-07 `/review` 워크플로 커맨드:** diff → code-reviewer(읽기전용) → 심각도 분류 findings → 스코프 엔지니어 반환. secret-scan 포스처 노출. reviewer를 실행 가능 단계로.
- **D-08 LIFE-08 `gate-model` 스킬:** 무엇이·어떻게 gated인지 맵(헌법 평면, machines-gate/humans-ratify, exit-3 거부(golden-approve·strangler_guard), 훅 표면(contract-guard·polyglot-lint·secret-scan·commit-gate), path_deny_globs). 차단 이유를 추론 가능하게.
- **D-09 LIFE-09 `two-plane-memory` 스킬:** 헌법-vs-파생 / 커밋된-state-vs-gitignored-derived / 파생-손편집-금지 규칙(현재 AGENTS.md §4 prose만).
- **D-10 LIFE-10 `/verify-work` (pre-handoff) 커맨드:** 세션 내 복합 게이트(`/lint`+`/test`+`/contract-check`+`/golden` 터치된 케이스). Phase-6 CI(비세션)·`/checkpoint`(상태영속)와 구별.
- **D-11 LIFE-11 orchestrator 라우팅 플레이북 보강(또는 `routing` 스킬):** 결정표(작업형태→페르소나/커맨드) + 최소 intake→decompose 절차. 배포 하네스의 유일한 계획자.

### Claude's Discretion
- 신규 vs 보강, 커맨드 vs 스킬 형태, `/diagnose-golden`을 별도 커맨드로 둘지 골든-debug 스킬에 흡수할지, `/new-contract-rule` 일반화 vs 이동, `/add-language` 스캐폴드 정확 형태, 웨이브 분할은 planner/researcher 재량.
- **고정:** 위 갭이 실재(감사 검증)·전부 도메인 중립·GEN-04 가드 준수·스킬 상한·reviewer 읽기전용·최소권한·모델식별자 없음·ADEQUATE 자산 미개변·기존 tools 재사용(재구현 금지).
</decisions>

<canonical_refs>
## Canonical References
- 이 CONTEXT의 `<audit_findings>`(감사 정본), `.planning/ROADMAP.md §Phase 5.7`, `.planning/REQUIREMENTS.md §LIFE`
- 재사용 tools: `tools/contract_drift`·`tools/contract_hash`(→ /contract-check), `tools/golden_runner`(→ golden-debug), `tools/memory_regen`(→ /orient), `libs/python/normalize`+`libs/normalize-spec.md`+CLAUDE.md canonicalization 표(→ polyglot-boundary·golden-debug)
- 기존 저작표면 선례: `harness/commands/*.md`(커맨드 매크로 형태), `harness/skills/*/SKILL.md`(progressive disclosure), `harness/agents/*.md`(페르소나), `harness/project.toml`(언어 슬롯 — /add-language 연결)
- 구조 검증: `tools/harness_lint/tests/{test_commands,test_skills,test_agents,test_agent_referential_integrity,test_core_no_example_dep}.py` — 신규 자산 추가 시 anti-sprawl 기대셋·referential-integrity·prose 가드 반드시 갱신(Phase 5.5 교훈: 이동/추가가 이 테스트들을 깬다)
</canonical_refs>

<code_context>
## Existing Code Insights
### Established Patterns (locked)
- 커맨드=얇은 매크로가 기존 tools 캡슐화(재구현 금지). 스킬=progressive disclosure(frontmatter 상시+본문 지연, references/로 상한 회피).
- **anti-sprawl 테스트가 정확한 세트를 핀** → 신규 커맨드/스킬/페르소나 추가 시 `EXPECTED_*` 갱신 필수(Phase 5.5에서 이 미갱신이 반복 RED 유발).
- referential-integrity 테스트: 커맨드 frontmatter `agent:`가 실재 페르소나여야 함 → 신규 커맨드의 agent 지정 주의.
- GEN-04 가드(코드+prose): 신규 코어 자산에 examples/·도메인 토큰 0.
### Integration Points
- 신규 커맨드 ↔ 기존 tools CLI(contract_drift/hash/golden_runner/memory_regen).
- /add-language ↔ project.toml [[languages]] 슬롯.
- 신규 자산 ↔ harness_lint 기대셋·가드.
</code_context>

<specifics>
## Specific Ideas
- 성공기준 데모(런타임 없이 구조/실행가능): (1) `/contract-check`가 실재하고 dead link 해소, 스키마 검증 실행; (2) golden-debug 스킬이 7축 결정트리 담고 골든 red 진단 절차 제공; (3) polyglot-boundary 스킬이 §4.3-4.6 단일 정본; (4) language-engineer 템플릿에서 새 언어 페르소나 파생 가능; (5) /new-normalization-rule 탈도메인(가드 통과); (6) 라이프사이클 각 MISSING 단계에 실행 가능 자산 존재; (7) 비-예시 스위트 그린(harness_lint 기대셋 갱신 반영).
- 헌법 평면 미접촉 예상(harness/·docs 비-adr) → 토큰 불필요. 단 ADR로 라이프사이클-완성 결정을 남길지는 planner 판단(남긴다면 승인경로 필요).
</specifics>

<deferred>
## Deferred Ideas
- 스킬/커맨드의 per-runtime **emit** → Phase 7.
- CI 통합(비세션 게이트) → Phase 6.
- opencode 런타임 실동작 → opencode 설치 후.
- 스코프 이탈 없음.
</deferred>

---
*Phase: 5.7 — Lifecycle Completeness (INSERTED, LIFE-01..11)*
*Context gathered: 2026-07-09 by adversarial audit (subagent aacebcd). DESIGNED this session; research→plan→execute HANDED OFF to next session (context budget).*
