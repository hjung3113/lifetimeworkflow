---
phase: 39
reviewers: [codex, opencode]
reviewed_at: 2026-07-26
plans_reviewed: [39-01-PLAN.md, 39-02-PLAN.md]
not_invoked:
  claude: self — running inside Claude Code, skipped for independence
  gemini: CLI available but auth ineligible (setup user error, exit 1)
  coderabbit: not installed
  qwen: not installed
  cursor: not installed
  ollama/lm_studio/llama_cpp: no local server running
---

# Cross-AI Plan Review — Phase 39 (Decision Boundary)

`/gsd:review --phase 39 --all` reached 2 of the 4 detected CLIs. `claude` was skipped by the
independence rule (this session is Claude Code). `gemini` is installed but its account is not
eligible for the configured project, so it exited 1 with no output.

Note on `opencode`: it refused to run from the repo root — `Configuration is invalid at
/Users/hyojung/orca/lifetimeworkflow/opencode.json ↳ Unrecognized key: _note`. The review was
obtained by running it from a scratch directory with a self-contained prompt. **The emitted
`opencode.json` carrying an unrecognized `_note` key is a real defect in the deployed runtime
surface, unrelated to Phase 39 — worth a separate look.**

---

## Codex Review

*(model: CLI default; review returned in Korean)*

### Plan 01 — ADR-0012 및 ADR 상태 정리

**Summary.** 목표와 범위는 대체로 잘 맞습니다. 인간 승인 전에는 ADR 경로를 쓰지 않고, 승인·토큰 확인 뒤에만
제한된 문서 변경을 수행하도록 설계되어 constitution-plane 경계를 존중합니다. 다만 기존 작업트리 변경과 현재
ADR 메타데이터의 불일치에 대한 검증 기준이 부족하고, "모든 삭제 표면"의 열거가 모호해 누락 위험이 있습니다.

**Strengths**
- `checkpoint:human-verify`를 ADR 쓰기보다 먼저 둬서 `GOLDEN_APPROVE_HUMAN` 우회를 명시적으로 금지합니다.
- 0001/0010은 `Status`와 `Superseded by`만 바꾸도록 해 supersede-don't-edit 원칙을 잘 지킵니다.
- ADR-0011의 코드 선행 배포(`bc9a6d9`)를 기록해 의사결정 기록의 시간적 정합성을 보완합니다.
- Phase 44까지 `golden/**` 관련 ADR-vs-code 불일치가 의도적·일시적임을 ADR-0012에 명시하게 해, Phase 39에서
  hook/test를 건드리는 scope creep을 막습니다.
- DEV/PRODUCT 경계와 "GSD가 있다고 제품 기능을 삭제하지 않는다"는 운영 규칙을 ADR에 넣어 이후 삭제 단계의 잘못된
  근거 사용을 방지합니다.

**Concerns**
- **HIGH — human gate의 실제 확인 방법이 불명확합니다.** "토큰을 session env 또는
  `.claude/settings.local.json`에 설정"은 서로 다른 전달 경로입니다. Task 2가 실제 실행 환경에서 non-empty
  값을 어떻게 확인할지, 그 값이 인간이 설정한 값이라는 사실을 어떻게 처리할지 명확하지 않습니다.
- **MEDIUM — '모든 삭제 표면' 기준이 완전히 폐쇄적이지 않습니다.** Task 1의 열거는 `docs-review plane`처럼 묶음
  표현을 쓰므로 `ledger_guard`, ledger, registry 관련 구성요소, adoption/task-control 분리에서 삭제되는 정확한
  표면이 ADR 본문에서 빠질 수 있습니다.
- **MEDIUM — "CI + merge authority"의 사실적 전제가 과하게 구체적입니다.** `CODEOWNERS review at the PR to
  main`이 실제 branch protection에 의해 강제되는지 확인 없이 ADR의 운영 사실로 단정하면, 선언과 실제 운영 사이에
  새 불일치가 생길 수 있습니다.
- **MEDIUM — `git diff` 검증이 dirty worktree를 구분하지 못합니다.** 이미 존재하던 ADR 변경이 있으면 "두 줄만
  변경"을 증명하지 못하며, 반대로 사용자의 기존 변경을 이번 작업 탓으로 볼 수 있습니다.
- **LOW — 플랜의 `files_modified`와 SUMMARY 산출물 요구가 충돌합니다.** `39-01-SUMMARY.md`를 만들라고 하지만
  수정 파일 목록에는 없습니다.
- **LOW — 날짜가 고정되어 있습니다.** 실제 인간 ratification이 다음 날 이뤄지면 `2026-07-26` 고정 문구가 사실과
  달라질 수 있습니다.

**Suggestions**
- Task 2 시작 전에 토큰 값 자체를 출력하지 않고, `GOLDEN_APPROVE_HUMAN`이 non-empty인지 안전하게 확인하는 명령과
  실패 시 즉시 중단 규칙을 명시하세요. `.claude/settings.local.json` 방식은 실제 session env에 주입되는 방식이
  검증된 경우에만 허용해야 합니다.
- ADR-0012에 포함할 "Phase 40–44 삭제 표면"을 ROADMAP의 항목별 체크리스트로 고정하세요. 묶음 명칭 대신 구성요소
  이름을 정확히 나열하면 CER-01 판정이 명확해집니다.
- CODEOWNERS/PR 보호가 실제로 보장되지 않았다면, "CODEOWNERS review가 강제한다"보다 "CI와 merge가 최종 수용
  지점이며, 적용 가능한 저장소 검토 정책을 따른다"처럼 검증 가능한 표현을 사용하세요.
- 쓰기 전 각 기존 ADR의 기준 blob/hash 또는 `git diff -- <files>`를 기록하고, 쓰기 후 변경분을 그 기준과
  비교하세요.
- SUMMARY 파일은 `files_modified`에 명시적으로 포함하거나 scope 검사 예외임을 적으세요.
- `Date`와 `Deciders`는 인간 승인 시점에 확정하게 하세요.

**Risk Assessment: MEDIUM.** 보안 경계에 대한 의도는 좋고 우회 금지도 분명합니다. 다만 토큰 전달·확인 방식, 정확한
삭제 표면 목록, dirty worktree에서의 변경 증명이 보완되지 않으면 human-ratification 기록의 신뢰성과 CER-01
완결성에 문제가 생길 수 있습니다.

### Plan 02 — STATE.md 처분 기록 및 무회귀 확인

**Summary.** CER-03의 네 처분을 append-only로 남기고 코드·게이트 변경 없이 기존 검증을 재실행하려는 형태는
적절합니다. 다만 "현재와 동일한 red/green" 판단을 과거 연구 문서에만 의존하고 있고, emitter 실행이 실제로 파일을
변경할 수 있는데도 무변경 검증으로 취급하는 점은 보완이 필요합니다.

**Strengths**
- 기존 RAT-4/RAT-5/security 행을 수정하지 않고 새 행을 추가하도록 해 이력 보존을 지킵니다.
- 세 항목을 `obsolete-by-deletion`, SEAL-05를 명확히 `withdrawn`으로 분리해 CER-03의 의미를 정확히 반영합니다.
- 각 새 행이 ADR-0012를 참조하도록 해 Phase 39의 단일 의사결정 근거와 연결됩니다.
- `docs_guard`의 기존 실패를 고치지 말고 실패 사유가 같음을 기록하라고 한 점은 범위 확장을 막습니다.
- 코드·계약·hook·CI를 새로 만들거나 고치지 않는다는 방향은 v2.5의 binding constraint와 부합합니다.

**Concerns**
- **HIGH — `tools.harness_emit`은 읽기 전용 검증이 아닐 수 있습니다.** emitter가 생성 트리를 수정할 수 있는데,
  plan은 이를 "zero drift 확인"으로만 다룹니다. 이미 dirty인 `.claude/` 또는 `.opencode/`에서는
  `git diff --exit-code`가 이번 phase와 무관하게 실패하거나, 반대로 기존 차이를 덮을 위험이 있습니다.
- **MEDIUM — docs-guard의 '동일한 실패' 판정 기준이 약합니다.** `task-control-cli-howto` 문자열만 확인하면 다른
  추가 실패를 놓칠 수 있습니다. 사전·사후 출력 또는 실패 binding 집합을 비교해야 합니다.
- **MEDIUM — "정확히 3개" obsolete 행이라는 완료 문구와 검증 명령이 불일치합니다.** 검증은 `>= 3`입니다. 새로 추가한
  네 행을 식별하는 검증이어야 합니다.
- **LOW — 기존 `.planning/STATE.md` 사용자 변경을 보존한다는 절차가 없습니다.**
- **LOW — 역시 SUMMARY 산출물이 `files_modified`에 빠져 있습니다.**

**Suggestions**
- emitter 실행 전 `.claude/`와 `.opencode/` 상태를 기록하고, 가능하면 check/dry-run 모드를 사용하세요.
- docs-guard는 사전·사후 모두 실행해 실패 binding 목록·원인을 비교하세요.
- STATE 행 검증을 `v2.5 P39, ADR-0012` 표식 기준으로 네 행 각각 확인하도록 바꾸세요.
- STATE 변경 후 새 `+` 행이 정확히 네 개의 테이블 행인지 검토하세요.
- `harness_emit`이 쓰기를 수반한다면 검증 단계에서 작업트리 보존 조건을 명시하세요.

**Risk Assessment: MEDIUM.** 실제 기능 변경은 없고 scope는 잘 제한돼 있습니다. 그러나 emitter의 잠재적 쓰기와 기존
작업트리 상태를 분리하지 않으면 "이 phase가 아무것도 악화하지 않았다"는 핵심 성공 기준을 신뢰성 있게 증명하기
어렵습니다.

### Overall

두 계획은 Phase 39의 본질 — 하나의 인간 ratified ADR와 네 개의 처분 기록, 코드·gate·CI 변경 없음 — 에 대체로
충실합니다. 이 단계는 이후 대규모 삭제가 임의적이지 않도록 기준 결정을 남기는 최소한의 전제라서, 목적 없는
ceremony라고 보기는 어렵습니다. 다만 v2.5의 de-ceremony 목표에 맞추려면 이 human checkpoint가 **Phase 39의
일회성 전환 절차**이며 이후 새 상시 gate를 만들지 않는다는 점을 ADR와 요약에 분명히 남기는 것이 좋습니다.

---

## OpenCode Review

*(model: glm-5.2 via the user's OpenCode config)*

**Overall.** Both plans are well-engineered, security-aware, and scope-disciplined. They correctly
treat the constitution-plane write gate as load-bearing (never bypassed), enforce
append-only/supersede-don't-edit discipline with `git diff` proofs, and explicitly refuse to "fix"
the pre-existing unrelated `docs-guard` RED. The dependency ordering (02 depends on 01), wave
structure, and autonomous flags are all correct. The dominant risk is **strategic, not tactical**.

### Plan 39-01

**Strengths**
- Constitution-plane gate respected, not bypassed — Task 1 performs *zero* writes to `docs/adr/**`;
  Task 2 is gated on the token and stops-and-reports on deny (T-39-01 mitigated).
- Supersede-don't-edit enforced with proof — `git diff --stat` must show only frontmatter lines
  changed on 0001/0010 (T-39-02 mitigated).
- Scope boundary explicit and testable — `files_modified` plus an acceptance criterion that
  `contract_guard.py` shows zero diff.
- Honest about ADR-0010's pre-existing internal inconsistency (frontmatter `accepted` vs body
  `## Approval` saying "proposed") — flags it, refuses to fix it.
- Catches the missing README row for ADR-0011.
- Names the temporary ADR-vs-code inconsistency as an expected Consequence, not a defect.

**Concerns**
- **[HIGH] Strategic: is this phase itself ceremony?** A milestone named "De-ceremony," whose binding
  constraint forbids growing the surface, opens with a phase that *adds* a 5-clause ADR, supersession
  pointers, a README index expansion, and four STATE.md rows. The defense (later phases need a
  citable authority) is real, but the irony is sharp. This is a **milestone-design question the plans
  inherit, not a plan defect** — if the answer is "the ADR is overkill," both plans dissolve. Consider
  whether a shorter rationale attached to the Phase 40 deletion PR serves the same function at lower
  surface cost.
- **[MEDIUM] ADR-0012 bundles five distinct decisions into one record.** Bundling makes future
  partial-reversal awkward — re-introducing a ratification gate later means superseding all five
  clauses or writing an awkward partial-supersede. ADR-0010's precedent is fair, but its clauses were
  more tightly coupled than these.
- **[MEDIUM] "Names every v2.5-deleted surface" creates brittle coupling to Phases 40–44.** Clause (b)
  welds an append-only, ratified record to future, mutable phase scope. If Phase 42 keeps `memory_ui`
  or Phase 44 relocates golden elsewhere, ADR-0012's enumeration becomes false. Mitigation: enumerate
  at milestone-intent level with a ROADMAP pointer rather than freezing a verbatim list. (Requirement-
  level issue from CER-01, but the plan could soften the phrasing.)
- **[LOW] "Permanent residual by design" is a strong, hard-to-reverse claim** — worth a sanity check
  that "permanent" is truly intended vs. "accepted for v2.5."
- **[LOW] Task 1 has no explicit re-draft loop** if the human requests changes.
- **[LOW] Deciders hardcoded as `kimhyojung (CODEOWNERS)`** — safe because the checkpoint lets the
  human correct it, but "confirm or correct at Task 1" would be more robust.

**Suggestions**
- Name the test path (`tools/hooks/tests/test_contract_guard.py:352-375`) inside ADR-0012's
  Consequences when assigning the `CONSTITUTION_GLOBS` update to Phase 44.
- Soften clause (b) to "the surfaces the v2.5 milestone targets for deletion, as listed in ROADMAP.md
  §v2.5".
- Consider splitting ADR-0012 in two: CI+merge authority + bash-residual (authority for Phase 40) and
  the DEV/PRODUCT boundary (authority for Phase 42). *Counter: contradicts the "one ratified unit"
  style — judge against the owner's ADR taste.*
- Task 2's chained `grep -c ... && grep -c ...` succeeds on *any* nonzero count. Add a lower bound
  where it matters, e.g. `test "$(grep -c 'Superseded by:.*0012' docs/adr/0001-*.md)" -eq 1`.

### Plan 39-02

**Strengths**
- Append-only discipline is provable — `git diff` must show no `-` lines (T-39-04 mitigated).
- Refuses to mask regressions as "pre-existing" — records exact pass/fail counts and the exact
  `docs-guard` failure reason, not a "green" summary (T-39-05 mitigated).
- Emission-drift check present and correct — `git diff --exit-code .claude .opencode` after re-emit
  catches a non-obvious failure mode cheaply.
- Scope note precise: `.planning/**` is GSD-owned, not constitution-plane, so autonomous writes are
  legitimate here. The asymmetry with 39-01 is correctly modeled.
- Correctly refuses to edit the archived v2.4 milestone file for SEAL-05.

**Concerns**
- **[MEDIUM] Reliance on grep counts is fragile** — `grep -c "obsolete-by-deletion"` succeeding at ≥3
  means a typo'd or duplicated row could pass. The automated verify is a presence-check, not a
  correctness-check; content correctness rests on the manual read the Validation doc already names.
- **[LOW] The four new rows duplicate information already in ADR-0012 + the existing RAT-4/RAT-5
  rows** — mild surface growth. Defense: STATE.md is the live doc future phases read.
- **[LOW] No explicit handling if Task 2's gate goes RED for a *new* reason** — no branch for
  "`pytest` didn't exit 0, what now?"

**Suggestions**
- Add to Task 2: "If `pytest` or `contract_drift` fail for any reason *not* documented as pre-existing
  in 39-RESEARCH.md, STOP and report — do not attempt diagnosis or repair." Mirrors 39-01's
  stop-and-report discipline.
- Consider consolidating the four STATE.md rows into fewer. *Counter: separate rows aid grep-by-item.*
- Add `git diff --numstat .planning/STATE.md` asserting no nonzero `-` count, making the append-only
  proof machine-checkable.

### Cross-cutting

- **[HIGH — strategic]** "Is this ceremony?" is unavoidable and unaddressed by the plans. Neither the
  plans nor the research answer "could Phase 39 be collapsed into a paragraph in Phase 40's deletion
  PR?" A 5-minute owner decision gates ~2 phases of work.
- **[MEDIUM]** Coupling between the ratified, immutable ADR-0012 and mutable Phases 40–44 — the
  highest-leverage design risk in the phase, inherited from CER-01.
- **[LOW]** Phase-level success rests substantially on the owner's manual read of ADR-0012 at Task 1's
  checkpoint. Ensure that read actually happens.

**Risk Assessment: LOW–MEDIUM.** Tactical/execution risk LOW — carefully sequenced, security-gated,
scope-bounded, provable acceptance criteria; the highest-severity failure mode (agent self-blessing a
write) is handled correctly. Strategic/design risk MEDIUM — the ceremony question and the
immutable/mutable coupling. **Net recommendation:** approve as written if the owner confirms (a) a
dedicated ADR-0012 is genuinely preferred over a lighter deletion-PR rationale, and (b) the
verbatim-surface enumeration is acceptable or softened. If either answer is "no," revise CER-01 rather
than the plans — the plans are faithful to what's asked.

---

## Consensus Summary

Two independent reviewers, both landing on **MEDIUM overall risk with no execution blocker**. Neither
found a security defect, a dependency-ordering error, or a requirement the plans fail to cover. Both
say the plans are faithful to CER-01/02/03; the disagreements are about the *requirement*, not the
*plan*.

### Agreed Strengths

- **The constitution-plane gate is respected, not bypassed.** Both reviewers single this out as the
  highest-severity failure mode and both confirm it is handled correctly — Task 1 writes nothing under
  `docs/adr/**`, and the plan forbids editing `contract_guard.py` or self-setting the token.
- **Supersede-don't-edit is provable, not promised** — `git diff` on 0001/0010 must show only
  frontmatter lines.
- **Scope containment holds** — no tool/contract/skill/command/CI/hook is added, and the plans make
  scope creep detectable rather than merely forbidden.
- **The pre-existing `docs-guard` RED is correctly quarantined** — recorded, not fixed, and kept out
  of the `&&` verify chain.
- **The Phase-44 deferred ADR-vs-code inconsistency is named up front** instead of left to be
  rediscovered as a bug.
- **The `bc9a6d9` code-before-ratification record** and the missing ADR-0011 README row are both
  caught.

### Agreed Concerns (highest priority — raised by both)

1. **The no-regression proof cannot distinguish this phase's changes from a dirty worktree.** Codex
   calls it HIGH on both plans (`git diff` can't prove "only two lines changed" if the tree was
   already dirty; `harness_emit` may *write*, so `git diff --exit-code .claude .opencode` can fail or
   mask for unrelated reasons). OpenCode reaches the same place from the other side — the emission
   check is right, but there's no branch for "the gate went red for a new reason." **Fix:** capture a
   pre-write baseline (blob hashes or a recorded `git diff`) before Task 2, and add an explicit
   "STOP and report, do not repair" rule for any non-pre-existing failure.
2. **The automated verification is a presence-check, not a correctness-check.** Both flag that
   `grep -c` succeeding at "≥ N" lets a typo'd or duplicated row pass while the plan's prose claims
   "exactly 3". **Fix:** assert exact counts (`-eq 1`, `-eq 4`) and key the STATE.md check on the
   unique `v2.5 P39, ADR-0012` marker rather than the generic phrase.
3. **"Names every v2.5-deleted surface" is the weakest clause in ADR-0012** — though for opposite
   reasons; see Divergent Views.
4. **`Date` / `Deciders` should be fixed at the moment of human ratification**, not hardcoded to
   `2026-07-26` / `kimhyojung (CODEOWNERS)` in advance.

### Divergent Views (worth the owner's judgment)

- **Enumeration: more precise, or less frozen?** Codex wants clause (b) *tightened* — replace bundle
  names like "docs-review plane" with an item-by-item component list, so CER-01 is unambiguously
  judgeable. OpenCode wants it *loosened* — a verbatim freeze welds an append-only ratified record to
  Phases 40–44, which are still mutable, so it should point at ROADMAP §v2.5 rather than copy it.
  These pull in opposite directions. A middle path exists: enumerate precisely but scope the claim as
  *intent at ratification time* rather than as a fact about future phases.
- **Is Phase 39 ceremony?** OpenCode raises this as its top HIGH strategic concern and asks whether
  the ADR could collapse into a paragraph on Phase 40's deletion PR. Codex explicitly disagrees —
  it calls the phase the minimum premise that keeps later deletions from being arbitrary — but adds a
  condition: ADR-0012 must state that this human checkpoint is a **one-off transition step for Phase
  39 and creates no standing gate**. That condition is a cheap way to satisfy both readings.
- **Is the human-gate mechanism clear enough?** Codex rates the token path HIGH-unclear ("session env
  or `.claude/settings.local.json`" are different delivery paths, and Task 2 never says how it checks
  non-emptiness safely). OpenCode reads the same tasks and lists the gate as the plan's leading
  strength. Cheap to settle: name one delivery path and one non-echoing check command.

### Codex-only findings

- The ADR's "CODEOWNERS review at the PR to main" claim is asserted as operational fact without
  confirming branch protection actually enforces it — a declaration/reality gap of exactly the kind
  this ADR exists to close.
- `39-01-SUMMARY.md` is required as an output but absent from `files_modified`.

### OpenCode-only findings

- Bundling five separable decisions into one ADR raises the cost of a future partial reversal.
- "Permanent residual by design" is strong and hard to walk back — confirm "permanent" is meant, not
  "accepted for v2.5".
- Task 1 has no explicit human-requests-changes → re-draft loop.
