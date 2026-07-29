# Phase 26: Deterministic Brownfield Inventory + Mapping *(v2.3 B)* - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-19
**Phase:** 26-Deterministic Brownfield Inventory + Mapping (v2.3 B)
**Areas discussed:** Output = contract, Classification bias, Disposition table, Exclusion policy, Question record shape, Phase-26 proof fixture

---

## Area selection

All four initially-offered gray areas were selected (Output = contract, Classify bias, Disposition table, Exclusion policy). After those closed, the user chose "더 논의" and two of three follow-up areas were selected (Question 출력 구조, Phase 26 증명 fixture); "Inventory 탐지 범위" was declined and left to researcher/planner.

---

## Output = contract

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, contract-first | Author inventory + plan + manifest schemas under `contracts/harness/adoption/`. Task-control precedent, drift-gate protection. Cost: constitution authoring + human ratification. | ✓ (via delegation) |
| Contract only the manifest | Only the cross-boundary manifest is schema-governed; inventory + plan stay test-validated. | |
| No, test-validated | All three plain deterministic files, shape locked by golden snapshots only. | |

**User's choice:** "추천대로" — delegated to Claude's recommendation.
**Notes:** Recommendation given and locked as D-01 = contract-first, all three. Rationale stated to the user: mirrors `contracts/harness/task-control/` (adoption is "an ordinary task", v2.3 FINAL §146); all three outputs cross into Phase 27 via ADOPT-04's CAS hash binding, so all three earn drift-gate protection; ratification rides the established constitution path rather than being a deviation.

---

## Classification bias (observed / inferred / unknown)

| Option | Description | Selected |
|--------|-------------|----------|
| 소유권만 항상 unknown | Bias ambiguous evidence to `inferred` with source; only ownership/authority claims forced to `unknown`. | |
| 보수적 unknown | All ambiguous evidence → `unknown` → question. `observed` on direct evidence only, `inferred` on strong structural signals only. Safest, most questions. | ✓ |
| 구조 적극 추론 | Infer liberally from directory/naming structure; `unknown` only when signals genuinely absent. | |

**User's choice:** 보수적 unknown
**Notes:** Accepted cost is a noisy question list on large repos. Ownership/authority is `unknown` by construction under this rule, so ADOPT-02's "no invented authority" clause is satisfied a fortiori. This choice raised the importance of the question-record shape, which became a follow-up area.

---

## Disposition table

| Option | Description | Selected |
|--------|-------------|----------|
| 내용 같으면 preserve, 다르면 conflict | Existing target + hash match → `preserve` (idempotent); hash differs → `conflict`. `marker-merge` reserved for marker-capable files. No auto-overwrite. | ✓ |
| 마커 가능하면 marker-merge 우선 | Marker-capable files marker-merge even on hash mismatch; only non-marker files conflict. | |
| 충돌은 무조건 conflict | Any existing target → `conflict` regardless of hash. Simplest, most questions. | |

**User's choice:** 내용 같으면 preserve, 다르면 conflict
**Notes:** Remaining table rows were not put to the user — they are requirement-locked and were stated back for confirmation: constitution paths (`contracts/`, `docs/adr/`, `golden/`) → always `human-ratification-required` regardless of existence (ADOPT-05/06); derived plane → `derived-regenerate`; absent non-constitution target → `create`. With the chosen collision row the table is total, satisfying roadmap success criterion 3.

---

## Exclusion policy

| Option | Description | Selected |
|--------|-------------|----------|
| tools/evidence 재사용 + 제외 레이어 | Reuse v2.2 confinement/size-cap/hash; add only an adoption-specific exclusion layer. | |
| 제외 전용 신규 모듈 | Independent adoption scanner with its own confinement/cap/exclusion. | |
| 보류 — 리서쳐가 결정 | Researcher decides after inspecting the `tools/evidence` API; CONTEXT records "reuse-first, justify if not". | ✓ |

**User's choice:** 보류 — 리서쳐가 결정
**Notes:** Recorded as D-07. Secret-detection posture noted to follow D-02's safest bias (exclude on suspicion) unless research finds a concretely better rule.

---

## Question record shape

| Option | Description | Selected |
|--------|-------------|----------|
| 증거+후보, 안정 그룹핑 | `{stable id, target, evidence pointer(path+hash), proposed candidate}`, grouped by destination-kind, stably sorted. | |
| 최소 평면 목록 | `{id, question text, target path}` only; no grouping or candidates. | |
| 보류 — 리서쳐 | Researcher designs the shape after inspecting how Phase 27's ratification step consumes it. | ✓ |

**User's choice:** 보류 — 리서쳐
**Notes:** Recorded as D-05 with a floor: stable id + target + evidence pointer (path+hash) are mandatory whatever shape is chosen, and ordering must be deterministic.

---

## Phase-26 proof fixture

| Option | Description | Selected |
|--------|-------------|----------|
| 합성 mini-repo fixture 하나 | One small synthetic target tree embedding every case; determinism by double-run diff. | ✓ (via delegation) |
| 탐지별 초소 fixture 분리 | A dedicated tiny fixture per detection; clearer failures, more fixtures. | |
| 보류 — 플래너 | Leave fixture layout entirely to the planner. | |

**User's choice:** "추천대로" — delegated to Claude's recommendation.
**Notes:** Recommendation given and locked as D-06. Rationale stated: v2.3 FINAL §152 forbids a broad fixture stack and Phase 27 owns the three application fixtures, so Phase 26 must not proliferate fixtures; the single-fixture downside (unclear failure cause) is neutralized by a separate assert per detection; determinism proven by a double run plus a shuffled-enumeration-order run; the tree also seeds Phase 27's fixtures.

---

## Claude's Discretion

- Module location/naming, internal data structures, canonical sort keys, schema property spellings, entry point, test file layout.
- Inventory detection breadth (languages, package managers, "candidate process boundary" heuristics, whether to reuse repo-map tree-sitter) — the user explicitly declined to constrain this and declined the offered discussion area.
- Exclusion/size-cap mechanism (D-07) and question-record shape (D-05) — delegated to the researcher with recorded floors.

## Deferred Ideas

- Phase 27 surface: `/adopt` command, `brownfield-adoption` skill, task-local batches, apply/marker-merge execution, ratification checkpoint, three application fixtures.
- Phase 29: docs registry/ledger seeding from adoption (DOCSUP-07).
- Graph-impact reporting over the adoption plan (needs Phase 25 queries; not a Phase 26 dependency).
- Permanently out of scope per v2.3 FINAL §147: autonomous contract extraction, golden inference from behavior, source refactoring, repo moves, CI/package-manager rewriting, executing discovered scripts, remote workspace members.

## Process note

The user asked mid-session that questions addressed to them be written in Korean. Applied from that point onward and saved as a durable preference.
