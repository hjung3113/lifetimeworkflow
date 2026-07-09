# Phase 6: CI + Gates (generic) — Context

**Gathered:** 2026-07-09
**Status:** Ready for planning (two execution-time decisions pending user confirmation — see `<open_decisions>`)

<domain>
## Phase Boundary

세션 내 훅 게이트(Phase 4)의 **비우회 CI 미러** + 사람 비준 경로를 완성한다 — 단, 하드코딩 `dotnet test`/`pytest`가 아니라 `harness/project.toml` **설정 파생 매트릭스**로(범용 템플릿 유지). 여기서 .NET egress 유예가 GitHub 러너에서 **실제 실행**된다. (REQ: CI-01, CI-02)

**In scope**:
- `.github/workflows/*.yml` — 설정 파생 폴리글랏 매트릭스: 언어별 테스트 잡(project.toml에서 파생) + generic 잡(contract-check·drift-hash·golden), PR마다 비우회
- `.github/CODEOWNERS` — 헌법 평면(contracts/·docs/adr/·golden/ + 예시 인스턴스 등가물) 사람 비준 게이트
- `.github/pull_request_template.md` — 경량 breaking/golden 체크리스트
- .NET 10을 GitHub 러너에 설치(egress OK) → CONTRACT-02 .NET 패리티·golden 실제 실행(로컬 deferred였던 것)

**Out of scope (이 페이즈)**:
- Phase 7 emitter(런타임 산출)
- 브랜치 보호 규칙 자체 설정(레포 설정 — 사람 조작; 워크플로는 required-check 후보를 제공하되 enable은 사람)
- opencode 런타임 실동작
</domain>

<decisions>
## Implementation Decisions (proposed — planner refines)

- **D-01 설정 파생 매트릭스(CI-01):** 워크플로에 `matrix` 생성 잡 — `harness/project.toml [[languages]]`를 읽어 per-language 잡 매트릭스를 `fromJSON`으로 팬아웃(하드코딩 금지). 로그파서 예시가 .NET 10 + Python(pytest) 레그 공급. + 고정 generic 잡: `contract-check`(check-jsonschema over contracts/** + examples/**/contracts), `drift`(contract-hash manifest 비교), `golden`(루트 generic identity 케이스 + 예시 .NET 케이스 — .NET 러너에서 실제 실행). 재사용: 기존 `tools/*` CLI를 CI가 그대로 호출(재구현 금지).
- **D-02 비우회(CI-01):** 모든 게이트 잡이 PR에서 required가 되도록 fan-in 게이트(전부 green 요구). 실제 required-check enforcement는 브랜치 보호(레포 설정) — 워크플로는 잡을 제공, enable 안내는 문서.
- **D-03 CODEOWNERS(CI-02):** `contracts/`·`docs/adr/`·`golden/` + `examples/*/contracts`·`examples/*/golden`을 사람 오너에 매핑. 오너 아이덴티티 = `<open_decisions D-A>`.
- **D-04 PR 템플릿(CI-02):** breaking-change / golden 업데이트 / contract-drift 확인 체크리스트. 레포 PR 템플릿 규약 존중.
- **D-05 .NET on GH:** `actions/setup-dotnet` 또는 `dotnet-install.sh --channel 10.0`(egress OK on GH). BOOT-01/CONTRACT-02의 로컬-deferred .NET이 CI에서 실제 도는 지점 — 골든 .NET 패리티가 진짜로 검증됨.

### Claude's Discretion
- 워크플로 파일 분할·잡 이름·매트릭스 생성 방식(python으로 project.toml→JSON emit 스텝)·CODEOWNERS glob 세부·PR 템플릿 문안은 planner/researcher 재량.
- **고정:** 설정 파생(하드코딩 아님)·기존 tools 재사용·헌법 평면 CODEOWNERS 게이트·모델식별자 없음·범용(예시 레그는 예시가 공급).
</decisions>

<open_decisions>
## Open Decisions — NEED USER CONFIRMATION before execution

- **D-A CODEOWNERS 오너 아이덴티티:** 헌법 평면(contracts/adr/golden)을 누가 비준하나? CODEOWNERS는 GitHub 사용자/팀 핸들 필요. **권장 기본값: `@hjung3113`**(레포 오너). 팀/조직이면 알려줄 것.
- **D-B CI를 실제로 돌릴 PR 개설 여부:** CI-01은 `pull_request` 트리거 → 실제 검증하려면 PR이 존재해야 함(그리고 .NET이 GH 러너에서 처음 실제 실행됨). **권장: 워크플로 저작 + YAML/로직 로컬 검증**, 그리고 **실제 PR 개설은 사용자 승인 후**(outward-facing). PR을 열면 `claude/data-pipeline-harness-8aypct` → 기본 브랜치 전체 diff가 노출됨.
</open_decisions>

<canonical_refs>
## Canonical References
- `.planning/ROADMAP.md §Phase 6`(4 성공기준), `.planning/REQUIREMENTS.md CI-01/CI-02`, `CLAUDE.md`(CI 매트릭스·CODEOWNERS·JCS drift 게이트 가이드)
- 재사용: `tools/contract_drift`·`tools/contract_hash`(drift/contract-check), `tools/golden_runner`(golden, .NET), `tools/polyglot_lint`, `harness/project.toml`(언어 매트릭스 소스), `tools/bootstrap`(.NET/uv 설치 선례), `check-jsonschema`(계약 인스턴스 검증)
- Phase 4 훅(CI가 미러): `tools/hooks/*`(contract-guard·polyglot·secret·commit-gate)
</canonical_refs>

<deferred>
## Deferred Ideas
- 브랜치 보호 required-check enable(레포 설정) → 사람.
- emit 재생성 CI 체크(EMIT drift) → Phase 7.
- 스코프 이탈 없음.
</deferred>

---
*Phase: 6 — CI + Gates (generic)*
*Context gathered: 2026-07-09. Two open decisions (D-A owner identity, D-B real-PR) pending user confirmation before execution.*
