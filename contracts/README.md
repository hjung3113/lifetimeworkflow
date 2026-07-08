# contracts/ — 계약 헌법 평면 (Constitution Plane)

*owner: TBD · status: seeded placeholders*

이 디렉터리는 **사람이 소유하는 헌법 평면**이다 (CODEOWNERS 게이트 대상, Phase 4/5에서 하드 강제).
파생 평면(`.memory/` repo-map·contracts-index 등, Phase 2)과 달리 **손으로 관리**하며 자동 재생성 대상이
아니다.

## ⚠️ 시드는 예시 placeholder — 도메인 진실 아님

이 아래 YAML들은 parserimprove monorepo_skeleton에서 복사한 **시드 골격**이다. 모든 `TBD`·`owner: TBD`·
예시 컬럼/규칙 값은 **example placeholder일 뿐 도메인 확정값(domain truth)이 아니다.** 실제 도메인 확정값
(컬럼 확정, 50종 보정 규칙, 마스터 데이터 실값)은 이 프로젝트의 **Out of Scope**다 (CONTRACT-01).
계약을 채우는 것이 아니라, 하네스가 계약을 **강제·검증**하는 배관을 시드하는 것이 목적이다.

## 계약 정본 규약 (D-06)

- **YAML 스펙** = 사람이 읽는 스켈레톤 스펙 문서.
- **동반 `.schema.json`** = JSON Schema Draft 2020-12. **검증·해시 대상 정본.** 코드가 스키마와 다르면
  코드가 틀린 것이다. 계약 변경은 골든/contract-drift 게이트를 동반한다.
- `format-conventions.schema.json` = §4.3–4.6 횡단 규약(인코딩·BOM·LF·소수점·타임존·null-token·TSV-escape·
  interval)을 명시 필드로 **materialize**한 파일. contract-drift 해시(Plan 05)가 이 파일을 포함해야
  컬럼 변경뿐 아니라 규약 변경까지 divergence로 잡는다 (PITFALLS P14).

## 구성

```txt
contracts/
├── log-specs/        standard-log.spec.yaml + .schema.json
├── normalization/    correction-rules.catalog.yaml + .schema.json
│                     format-conventions.schema.json   (§4-5 materialized, P14 해시 타깃)
├── reference-data/   equipment-master.yaml + .schema.json
└── state/            equipment-progress.yaml + .schema.json
```

`check-jsonschema --schemafile <schema> <instance>` 로 각 시드 YAML을 동반 스키마에 검증한다.

## golden/ 은 별도 top-level 형제 (contracts/ 하위 아님)

골든 동등성 세트는 **`contracts/`의 하위가 아니라** 최상위 `golden/`에 있다 — `contracts/`와 형제인
독립 헌법-평면 디렉터리다(D-06/D-07 locked layout: `contracts/` · `golden/` · `adr/` · `glossary` = 헌법).
따라서 `contracts/golden/` 서브디렉터리는 **존재하지 않는다.** 루트 `../golden/README.md` 참조.
