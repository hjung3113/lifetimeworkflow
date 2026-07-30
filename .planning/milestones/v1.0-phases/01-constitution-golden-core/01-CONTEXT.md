# Phase 1: Constitution + Golden Core - Context

**Gathered:** 2026-07-07
**Status:** Ready for planning

<domain>
## Phase Boundary

계약 우선 안전망의 **walking skeleton** — 실제 레거시↔신규 동등성 루프 하나를 처음부터 끝까지 닫는다. 전 표면을 만들지 않고, 정규화 비교 코어·골든러너·contract-drift 게이트가 실제로 한 바퀴 도는 것을 실증한다. (REQs: CONTRACT-01~04, BOOT-01~03, DOCS-01/02)

**In scope**: 계약 시드(placeholder), 언어중립 정규화 비교 코어 + 각 언어 구현, 골든 픽스처 + 골든러너(한 루프), contract-drift 해시 게이트, .NET 10 + uv 부트스트랩, Diátaxis/adr/glossary 스켈레톤.
**Out of scope (이 페이즈)**: 전체 커맨드/에이전트/스킬 표면(Phase 3), 훅/플러그인 강제(Phase 4), CI(Phase 5), emitter(Phase 6), 실제 파서/컨버터 로직·도메인 확정값(프로젝트 Out of Scope).
</domain>

<decisions>
## Implementation Decisions

### 골든 루프의 실체 (walking skeleton substance)
- **D-01:** 루프 = **Python 골든러너가 .NET 토이 변환기(신규 역할)를 CLI로 spawn → 출력 캡처 → 공유 정규화 코어로 정규화 → 승인된 baseline(레거시 역할)과 diff**. 이 한 루프가 A-model(CLI spawn + exit code)·폴리글랏 프로세스 경계·인코딩·골든 승인 흐름을 전부 exercise한다. (녹화쌍-only, 표현차-only 옵션은 기각 — end-to-end 미달)
- **D-02:** .NET 토이 변환기는 **최소 실체**다 — 시드 TSV를 읽어 정규화 출력만 내는 수준. 실제 파서·정규화 로직(50종 보정 등)은 구현하지 않는다(프로젝트 Out of Scope). "신규 컴포넌트가 존재하는 척"이 아니라 하네스 배관을 증명하는 fixture-grade 변환기.
- **D-03:** "레거시" baseline = 승인된 골든 출력 파일(`golden/`), 실행체 없음. 동등성은 baseline ↔ .NET 토이 출력의 정규화 diff.

### 정규화 비교 코어 소유 (linchpin, CONTRACT-02)
- **D-04:** **언어중립 canonicalization 계약(스펙)** 을 정본으로 두고 .NET·Python이 각각 얇게 구현, **공유 픽스처로 교차검증**한다. 한 언어가 정본이 아니라 규칙이 정본 — 폴리글랏 철학(§0) 일치, 언어별 구현 drift는 공유 픽스처가 잡는다.
- **D-05:** 코어 규칙 = §4.3~4.6 정규화 항목: UTF-8/BOM 제거, LF 강제, InvariantCulture 소수점(`.`), float 허용오차 비교, 키/행 결정적 정렬, UTC/ISO-8601 고정 문자열, TSV 이스케이프·null-vs-empty 명시. 이 코어는 Phase 4 폴리글랏 린터(POLY-01)가 **재사용**한다 — 한 번 만들고 공유.

### 계약 기계판독 정본 (contract format)
- **D-06:** **YAML 스펙(사람 가독, skeleton 유지) + 동반 JSON Schema(Draft 2020-12)** 이중 구성. YAML은 사람이 읽는 스펙 문서, `.schema.json`이 검증·해시 대상 정본. 스택 정합(JsonSchema.Net 9.2.2 / jsonschema 4.26.0 / check-jsonschema).
- **D-07:** contract-drift 게이트(CONTRACT-04) 해시 대상 = 각 `.schema.json`을 **RFC 8785(JCS) 정규화 후 SHA-256**. 해시는 **컬럼 목록뿐 아니라 §4-5 횡단 규약(인코딩·타임존·null·이스케이프 등)** 까지 포함해야 한다(PITFALLS P14: 해시가 cross-cutting 규약을 놓치면 divergence 미검출). breaking/non-breaking 분류 포함.

### .NET 10 부트스트랩 (BOOT)
- **D-08:** **SessionStart 훅 idempotent 자동 설치** — `dotnet-install.sh --channel 10.0`을 SessionStart에서 캐시(설치본) 확인 후 있으면 스킵, 없으면 설치. ephemeral 컨테이너 무개입 자기부트스트랩. (수동 /bootstrap·Docker 이미지는 기각 — 각각 "기억해야 함"·"이미지 관리 부담")
- **D-09:** Python 쪽 부트스트랩 = uv 워크스페이스 resolve + ruff·pyright·pytest(BOOT-02). uv는 이미 존재(0.8.17). 동일 SessionStart 경로에 idempotent 와이어링(BOOT-03).

### Claude's Discretion
- 토이 변환기의 구체 변환 규칙(어떤 컬럼을 어떻게 정규화하는 시늉을 할지), 골든 픽스처의 구체 값, 디렉터리 세부 네이밍, RFC 8785 구현체 선택(라이브러리 vs 직접), Diátaxis 스켈레톤의 초기 페이지 목록은 planner/researcher 재량. 단 §4-5 규칙과 A-model 경계는 고정.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

> 참고: parserimprove 문서는 `hjung3113/presentationformat` 레포(경로 `archive/parserimprove/uploads/`)에 있고, 이 세션에서는 `/workspace/presentationformat/`에 클론되어 있다. Phase 1(CONTRACT-01)이 필요한 계약을 이 레포 `contracts/`로 **복사 시드**하므로, 이후 정본은 레포 내부가 된다.

### 도메인 계약 시드 소스 (CONTRACT-01)
- `/workspace/presentationformat/archive/parserimprove/uploads/monorepo_skeleton/contracts/log-specs/standard-log.spec.yaml` — 표준 로그 TSV 스펙 골격(시드 대상)
- `/workspace/presentationformat/archive/parserimprove/uploads/monorepo_skeleton/contracts/normalization/correction-rules.catalog.yaml` — 정규화·보정 규칙 카탈로그 골격
- `/workspace/presentationformat/archive/parserimprove/uploads/monorepo_skeleton/contracts/reference-data/equipment-master.yaml` — 기준정보 마스터 골격
- `/workspace/presentationformat/archive/parserimprove/uploads/monorepo_skeleton/contracts/state/equipment-progress.yaml` — 진행상태/carryover 골격
- `/workspace/presentationformat/archive/parserimprove/uploads/monorepo_skeleton/docs/` — 도메인 문서군(00~04+GLOSSARY), Diátaxis/glossary 참고

### 폴리글랏 경계 & 정규화 코어 (CONTRACT-02/03, D-04~07)
- `/workspace/presentationformat/archive/parserimprove/uploads/integration_contracts_design.md` §4.1(스키마 단일소스)·§4.3~4.6(인코딩·타임존·소수점 규약)·§5(Py↔.NET 체크리스트)·§6(계약 변경=골든 갱신) — 정규화 코어·drift 게이트의 정본 규칙
- `/workspace/presentationformat/archive/parserimprove/uploads/parser_project_revised.md` §5.1(골든 동등성)·§5.4(데이터기반 정규화 테스트) — 골든 안전망 근거

### 하네스 결정 & 스택 (전 REQ)
- `.planning/PROJECT.md` — Core Value, Constraints, Key Decisions(A-model·two-plane·contract-first)
- `.planning/REQUIREMENTS.md` — Phase 1 REQ: CONTRACT-01~04, BOOT-01~03, DOCS-01/02
- `.planning/ROADMAP.md` §Phase 1 — Goal·Success Criteria
- `.planning/research/STACK.md` — 도구·버전(dotnet-install, JsonSchema.Net, jsonschema, check-jsonschema, RFC 8785, xunit.v3/Verify, pytest/syrupy, uv/ruff/pyright)
- `.planning/research/ARCHITECTURE.md` — 빌드오더·헌법/파생 평면·safety 게이트 데이터흐름
- `.planning/research/PITFALLS.md` — P4(byte-diff false red)·P9(에이전트 골든 self-bless)·P14(해시가 cross-cutting 규약 누락) 특히 이 페이즈 관련
- `CLAUDE.md` — 프로젝트 기술 스택 표(버전 고정)·Golden-Equivalence Comparator Building Blocks 표
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **parserimprove monorepo_skeleton contracts/** (`/workspace/...`): YAML 계약 골격 — CONTRACT-01 시드의 직접 원천. 그대로 복사 후 placeholder 표시.
- **GSD 훅 패턴** (`.claude/settings.json`의 SessionStart/PostToolUse 훅): SessionStart 부트스트랩(BOOT-03)·이후 페이즈 훅의 참고 구현 형태(command 훅 wiring).
- **CLAUDE.md 기술 스택 표**: 버전·라이브러리가 이미 조사·고정됨 — 재조사 불필요.

### Established Patterns (locked, 재질문 금지)
- **A-model 경계**: Python → .NET은 CLI spawn + exit code + 파일/DB. 객체 직접 전달 금지(§0).
- **§4.3~4.6 canonicalization**: UTF-8 no-BOM·LF·InvariantCulture·UTC/ISO-8601 — 코어·린터 공유 규칙.
- **machines gate, humans ratify**: 골든 baseline 갱신은 사람 승인만(에이전트 self-bless 금지, P9). Phase 1 골든러너/골든 baseline은 이 원칙 위에 설계.
- **파생 vs 헌법 평면**: contracts/·golden/·adr/·glossary = 헌법(사람 소유). Phase 2에서 파생 평면 추가.

### Integration Points
- **SessionStart 훅**: BOOT-03가 여기에 .NET/uv 부트스트랩을 idempotent하게 건다. 기존 GSD SessionStart 훅과 공존(별도 훅 항목 or 래퍼).
- **contracts/ ↔ drift 게이트**: `.schema.json` 파일이 게이트의 입력. 시드(CONTRACT-01)와 게이트(CONTRACT-04)가 이 경로 규약으로 연결.
- **정규화 코어 ↔ Phase 4 린터(POLY-01)**: 같은 코어를 재사용하도록 인터페이스를 언어중립 계약으로 노출.
</code_context>

<specifics>
## Specific Ideas

- walking skeleton의 성공 판정 시나리오(로드맵 성공기준 3 반영): "BOM/CRLF/decimal-locale/TZ만 다른 fixture는 골든 PASS, 진짜 값 회귀는 FAIL" — 정규화 코어가 표현차를 중화하되 실차이는 살린다는 것을 한 쌍의 fixture로 증명.
- drift 게이트 데모(성공기준 2): 실제 스키마 한 줄 변경 → 해시 변동 → 게이트 트립 → breaking/non-breaking 분류. 컬럼 외 §4-5 규약 변경도 잡히는지 확인.
- `/golden`·`/golden-approve`의 Phase 1 범위: 커맨드의 **최소 실행 형태**(골든러너 호출 + 승인 거부 게이트)만. 풀 커맨드 표면 정비는 Phase 3.
</specifics>

<deferred>
## Deferred Ideas

- 전용 golden-runner/polyglot-auditor **에이전트** 페르소나 → v2(EXT-02) / 필요 시 Phase 3~4에서 재검토. Phase 1은 스크립트/커맨드 최소형.
- 폴리글랏 린터 **on-write 훅 강제** → Phase 4(POLY-01/HOOK). Phase 1은 코어(라이브러리)만.
- CI에서의 게이트 실행 → Phase 5(CI-01). Phase 1은 로컬 실행 가능한 형태.
- 이외 스코프 이탈 없음 — 논의는 페이즈 경계 내에 머묾.
</deferred>

---

*Phase: 1-Constitution + Golden Core*
*Context gathered: 2026-07-07*
