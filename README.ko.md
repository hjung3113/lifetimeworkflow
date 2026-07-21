<div align="center">

# 계약 우선 폴리글랏 에이전트 하네스 템플릿

**계약(contracts)을 단일 정본으로 두고, 폴리글랏 표현차·레거시 전환 리스크를 하네스가 자동으로 강제·검증한다.**

코딩 **에이전트**가 책임 분리된 폴리글랏 모노레포를 만들고·유지보수·리팩토링할 수 있게 해주는
재사용 가능한 **계약 우선** 하네스 — "여기서 어떻게 개발하는가"가 부족(tribal knowledge)이 아니라
실행 가능한 **스킬·커맨드·훅**으로 박혀 있다.

[English README](README.md) · [무엇인가](#무엇인가) · [왜](#왜) · [핵심 개념](#핵심-개념) · [v2.2 Task Control Plane](#v22--adaptive-task-control-plane) · [빠른 시작](#빠른-시작) · [저장소 구조](#저장소-구조) · [로드맵](#로드맵)

</div>

---

## 무엇인가

이 저장소는 **애플리케이션이 아니다** — **템플릿 하네스**다. 산출물은 하네스 그 자체:

- **opencode**(1차) + **Claude Code**(2차) 아티팩트 — `agents`·`commands`·`skills`·`plugins`·
  `opencode.json` — 를 `harness/` 아래 **단일 런타임-중립 소스**에서 생성.
- **Diátaxis + ADR + contracts** 문서 구조.
- 세션을 넘어 유지되는 두 평면 **컨텍스트 메모리** 층 — 사람 소유 *헌법(constitution)* vs
  기계 재생성 *파생(derived)*.

이 프로젝트를 씨앗으로 만든 반도체 설비 로그파서 도메인은 [`examples/log-parser/`](examples/log-parser)
아래 **참조 인스턴스**로 격리됐다. 코어는 어떤 인스턴스에도 의존하지 않는다.

## 왜

폴리글랏 모노레포는 경계에서 썩는다: 같은 계약이 언어마다 다르게 표현되고, 레거시→신규 전환이
조용히 어긋난다. 이 하네스는 **계약을 단일 정본**으로 두고 모든 가드레일을 실행 가능한 것으로 바꾼다:

> **계약이 정본이다. 코드가 계약과 다르면 코드가 틀린 것이다.**
> **기계가 게이트하고, 사람이 비준한다(ratify)** — 에이전트는 *제안*만 할 수 있고 골든 baseline이나
> 헌법 평면을 스스로 승인할 수 없다.

## 핵심 개념

| 개념 | 설명 |
|---|---|
| **계약 우선(Contract-first)** | `contracts/`가 코드보다 우선. 변경은 RFC 8785로 정규화 → SHA-256 → 커밋된 해시. CI가 재계산해 **골든 갱신 없는 드리프트면 실패**. |
| **골든 등가(Golden equivalence)** | 레거시↔신규 비교가 순진한 byte-diff가 아니라 7축(BOM·개행·소수/로케일·부동소수 허용오차·행 순서·타임존·TSV escape/null) 정규화 기반. |
| **두 평면 메모리** | *헌법*(`contracts/`·`docs/adr/`·`golden/`)은 사람 소유·CODEOWNERS 게이트. *파생*(`repo-map`·`contracts-index`·`docs/reference/`)은 기계 재생성·CI 검증(손편집 금지). `curator` 에이전트가 파생 신선도 소유. |
| **단일 소스 → 두 런타임 emit** | `harness/`에서 한 번 작성 → `.opencode/`와 `.claude/`에 **byte-identical** 방출. `emit-drift` CI 잡이 우회 불가로 강제. |
| **폴리글랏 경계** | 언어 경계 = 프로세스/파일/DB만(객체 직접 전달 금지). 경계 린터가 §4.3–4.6 정규화 불변식을 wire 파일에 강제. |
| **GEN-04 무의존** | 코어는 `examples/` 인스턴스나 `workspace.toml` 멤버를 import·경로참조하지 않음. 가드 테스트가 단방향 의존을 증명. |
| **기계 게이트, 사람 비준** | `/golden-approve`는 명시적 사람 플래그 + ADR 참조 + 확인 토큰 없이 baseline 승격을 거부. |

## v2.2 — Adaptive Task Control Plane

에이전트가 작업 한 건을 안전하게 완주하도록 하는 **적응형 작업 통제 평면**. 소작업은 ceremony를
억제하고, 고위험은 fail-closed로 막는다. 6개 phase(18–23):

### 1. Task Packet 계약 (Phase 18)
작업은 `.workflow/tasks/<task-id>/` 에 산다. `task`·`state`·`evidence`·`handoff` JSON Schema(Draft
2020-12) + validator + 전이 매트릭스(`transitions.json`). 계약이 코드보다 우선.

### 2. Deterministic Risk Router (Phase 19)
`harness/risk-policy.toml` 이 7축(모호성·변경범위·데이터보안·가역성·영향·조정·컨텍스트압력)을 점수화해
레인을 결정:

| 레인 | 점수 | 의미 |
|---|---|---|
| **FAST** | 0–4 | 상세 SPEC/PLAN/워크트리/이중 리뷰 없이 통과. 사용자 의식 단계 ≤2(intake+verify). |
| **STANDARD** | 5–9 | 기본 리뷰 + 명세. |
| **STRICT** | 10–14 | 독립 review record 요구. |
| **CONTROLLED** | 15–21 | 독립 review + rollback 증거 요구. |

**reason-code 승격**(점수와 무관하게 상향): `auth_authorization`·`secret_pii`→STRICT,
`payment`·`destructive_data_change`→CONTROLLED, `golden_or_contract_mutation`→CONTROLLED(점수 0이어도).
오버레이는 **escalate-only** — 코어 레인을 낮추거나 필수 산출물을 제거할 수 없다. 커맨드: **`/intake`**.

### 3. Atomic State Manager + Phase Gate (Phase 20)
상태 전이는 temp+rename **원자적 교체** + `state.revision` **compare-and-swap(flock)** — 같은 revision
경쟁 시 정확히 하나만 성공, 중단된 쓰기 후 정확히 하나의 valid canonical. phase 시작 전 repo/워크트리/
baseline/제약 attestation을 **fail-closed** 검사. 커맨드: **`/phase-gate`**.

### 4. Evidence Bundle Adapters (Phase 21)
기존 게이트(lint·test·contract-drift·golden·`/verify-work`)를 **재구현하지 않고 감싸서** 위조 탐지
가능한 증거로 수집: gate-argv 레지스트리(정본 명령 정확일치), **HEAD-커밋 신뢰루트**(에이전트가 커밋
못 하는 불변식이 trust root), secret/PII 거부, criterion↔evidence 추적. status PASSED/FAILED/SKIPPED/
BLOCKED 엄격 분리(skip을 pass로 승격 불가).

### 5. Handoff + Fresh-Session Resume (Phase 22)
대화 transcript 없이 **특정 revision의 immutable HANDOFF 스냅샷**을 새 세션에 전달. 원본 계약·evidence를
복제하지 않고 path/hash로 참조. `resume_gate` **PreToolUse 훅**이 revision-bound attestation으로
검증 전 EXECUTE/REVIEW/VERIFY mutation을 fail-closed 차단(재개 후 정상 작업은 데드락 없이 진행).
커맨드: **`/handoff`**·**`/checkpoint`**·**`/orient`**.

### 6. Lifecycle Evaluation (Phase 23)
사람이 비준한 도메인-중립 **레인 fixture 20개(레인별 5)** + negative/stress 12개(buried constraint·
stale handoff·wrong worktree·tampered evidence·concurrent writers·secret artifact·constitution
change·illegal downgrade). E2E runner가 각 fixture를 실제 git task로 실체화해 intake→전이→evidence→
handoff→별도 프로세스 orient→phase-gate를 **실행으로 증명**(선언 검사 아님). `docs/how-to/task-lifecycle.md`
+ 비준된 **ADR-0008**(namespace·authority·lifecycle·overlay).

## 빠른 시작

> 사전조건: [`uv`](https://docs.astral.sh/uv/)(Python 워크스페이스). .NET 10 쪽은 선택이며
> `tools/bootstrap/`로 필요 시 설치. Python 전체 스위트는 .NET 없이 돈다.

```bash
# 1. uv 워크스페이스 동기화 (루트 pyproject.toml + 모든 tools/ + libs/python 멤버)
uv sync --all-packages

# 2. 전체 하네스 테스트 스위트 (904 통과)
uv run pytest -q

# 3. harness/ 소스에서 런타임 표면 재방출 후 byte-identical 확인
uv run python -m tools.harness_emit
git diff --exit-code -- .opencode .claude/agents .claude/commands .claude/skills opencode.json AGENTS.md

# 4. 계약 + schema-hash 드리프트 게이트 검증
uv run python -m tools.contract_drift.drift

# 5. Task Control Plane: 위험 레인 라우팅 + lifecycle 증명
uv run python -m tools.risk_router            # 7축 점수 → 레인
uv run python -m tools.lifecycle_eval.runner  # 20개 비준 fixture를 실제 E2E 경로로 실행
```

## 저장소 구조

```
harness/            # ★ 에이전트 표면의 런타임-중립 소스 (여기서 작성)
  agents/ commands/ skills/ plugins/
  risk-policy.toml  #   v2.2 위험 라우팅 정책 (7축 점수·레인 cut·reason code·오버레이)
  project.toml      #   GEN-03 언어/툴체인 슬롯 (순수 DATA)
.opencode/ .claude/  # 생성된 런타임 트리 (손편집 금지) ← tools.harness_emit
contracts/           # 헌법 평면 — JSON Schema 계약 (단일 정본)
  harness/task-control/  # v2.2: task·state·evidence·handoff·transitions·gate-registry·attestation
golden/              # 헌법 평면 — 승인된 등가 baseline
docs/                # Diátaxis + adr/(0001–0008) + glossary + how-to/task-lifecycle.md
tools/               # Python 도구: risk_router·task_control·evidence·handoff·lifecycle_eval·
                     #   harness_emit·contract_drift·golden_runner·memory_regen·hooks·…
examples/log-parser/ # 참조 인스턴스 (도메인 특화; 코어는 이것에 의존하지 않음)
.planning/           # GSD 워크플로우 상태: PROJECT.md·ROADMAP.md·MILESTONES.md·phases/·milestones/
AGENTS.md CLAUDE.md  # nearest-wins 에이전트 규칙
```

## 로드맵

- ✅ **v1.0 — Foundation (Phase 1–8)**: 헌법+골든 코어 · 두 평면 메모리 · agents/commands/skills ·
  plugins/hooks · 템플릿 탈특화 · 설정형 CI · 단일소스 dual-runtime emitter · 파이프라인 토폴로지.
- ✅ **v2.0 — Long-Horizon (Phase 9–11)**: self-maintaining 파생 + curator · context-economy
  fan-out/synthesize · multi-repo workspace.
- ✅ **v2.1 — Process Memory & Provenance (Phase 12–16)**: PROCESS 메모리 층(`.memory/agreements/`) ·
  injector 리프레임 · `/agree` write 경로 · emit round-trip 게이트 · 로컬 메모리 web UI.
- ✅ **v2.2 — Adaptive Task Control Plane (Phase 18–23)**: 위 6개 phase. TCP-01..18 완료, ADR-0008 비준.

개발은 **GSD** 워크플로우(`.planning/` + `/gsd:*` 커맨드)로 진행. 새 마일스톤은 `/gsd:new-milestone`.

## 기여 규칙

- 생성 트리(`.opencode/`·`.claude/`·`opencode.json`)와 파생물(`.memory/derived/`·`docs/reference/`)을
  **손편집 금지** — `harness/`/`contracts/` 소스를 고치고 emitter/regenerator를 다시 돌려라.
- 가장 가까운 [`AGENTS.md`](AGENTS.md) 먼저 읽기. 서브트리별 `AGENTS.md`가 비협상 규칙을 재진술.
- push 전: `uv run pytest -q`, 재방출 후 `git diff` clean 확인, contract-drift/golden 게이트 green 유지.
  `/verify-work`가 세션 내 복합 게이트를 실행.

---

<div align="center">
<sub>GSD 워크플로우로 빌드 · <code>harness/</code> 단일 소스 → opencode + Claude Code 방출 · 기계가 게이트, 사람이 비준.</sub>
</div>
