# Phase 1: Constitution + Golden Core - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-07
**Phase:** 1-Constitution + Golden Core
**Areas discussed:** 골든 루프의 실체, 정규화 비교 코어 소유, 계약 기계판독 정본, .NET 10 부트스트랩

---

## 골든 루프의 실체 (Golden Loop substance)

| Option | Description | Selected |
|--------|-------------|----------|
| .NET 토이변환기 + Python 골든러너 | Python 골든러너가 .NET 토이 변환기를 CLI spawn→출력 캡처→공유 정규화→승인 baseline과 diff. A-model·폴리글랏 경계·인코딩 전부 exercise | ✓ |
| 녹화 골든쌍 + 비교기만 | 실행체 없이 (input,승인 output) 쌍 + 비교기만; spawn 생략 | |
| 표현차 픽스처만 | BOM/CRLF/locale/TZ만 다른 픽스처로 비교기 자체만 실증 | |

**User's choice:** .NET 토이변환기 + Python 골든러너 (권장)
**Notes:** 컴포넌트 로직은 Out of Scope이므로 토이 변환기는 fixture-grade(시드 TSV→정규화 출력 최소형). "레거시"는 승인된 골든 출력 파일이 대신함.

---

## 정규화 비교 코어 소유 (Comparator ownership, CONTRACT-02)

| Option | Description | Selected |
|--------|-------------|----------|
| 언어중립 계약 + 각 언어 구현 | canonicalization 규칙을 계약(스펙)으로, .NET·Python 각각 얇게 구현, 공유 픽스처 교차검증 | ✓ |
| Python 단일 참조구현 | Python이 정본 비교기, .NET은 산출물만 비교대상 | |
| 각 언어 독립 + 상호 골든검증 | 양쪽 독립 구현 후 golden으로 상호 동등성 강제 | |

**User's choice:** 언어중립 계약 + 각 언어 구현 (권장)
**Notes:** 규칙이 정본, 언어별 drift는 공유 픽스처가 검출. Phase 4 폴리글랏 린터(POLY-01)가 같은 코어 재사용.

---

## 계약 기계판독 정본 (Contract format)

| Option | Description | Selected |
|--------|-------------|----------|
| YAML 스펙 + 동반 JSON Schema | YAML=사람가독 스펙(skeleton 유지), .schema.json(Draft 2020-12)=검증·해시 대상 | ✓ |
| YAML만 | skeleton YAML 그대로 RFC8785 정규화 후 해시 | |
| JSON Schema만 | YAML 폐기, JSON Schema가 유일 정본 | |

**User's choice:** YAML 스펙 + 동반 JSON Schema (권장)
**Notes:** 스택 정합(JsonSchema.Net/jsonschema/check-jsonschema). drift 해시는 §4-5 cross-cutting 규약까지 포함해야 함(P14).

---

## .NET 10 부트스트랩 (Bootstrap)

| Option | Description | Selected |
|--------|-------------|----------|
| SessionStart 훅 idempotent 자동설치 | dotnet-install --channel 10.0을 SessionStart에서 캐시 확인 후 스킵/설치 | ✓ |
| 명시적 /bootstrap 커맨드 | 수동 트리거, 사람이 기억해야 함 | |
| devcontainer/Docker 사전설치 | 이미지에 SDK 박음, 이미지 관리 부담 | |

**User's choice:** SessionStart 훅 idempotent 자동설치 (권장)
**Notes:** ephemeral 컨테이너 무개입 자기부트스트랩. Python(uv)도 동일 경로에 idempotent 와이어링.

---

## Claude's Discretion

- 토이 변환기의 구체 변환 규칙, 골든 픽스처 구체 값, 디렉터리 세부 네이밍, RFC 8785 구현체 선택(라이브러리 vs 직접), Diátaxis 스켈레톤 초기 페이지 목록 — §4-5 규칙·A-model 경계 고정 하에 planner/researcher 재량.

## Deferred Ideas

- 전용 golden-runner/polyglot-auditor 에이전트 페르소나 → v2(EXT-02)/Phase 3~4 재검토.
- 폴리글랏 린터 on-write 훅 강제 → Phase 4.
- CI 게이트 실행 → Phase 5.
