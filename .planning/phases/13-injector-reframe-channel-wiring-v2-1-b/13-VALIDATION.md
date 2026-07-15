---
phase: 13
slug: injector-reframe-channel-wiring-v2-1-b
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-15
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `13-RESEARCH.md` § Validation Architecture (:673). The planner fills
> the per-task IDs; the behavior/command columns below are authoritative.
>
> **Defining characteristic of this phase:** the determinism safety net SC2 says is
> "preserved" **does not exist yet** — `inject.py:20-22` claims delete+regen byte-identity
> but no test asserts it. It must be **built in Wave 0, before the reframe**, or SC2 is
> unfalsifiable.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.x (uv workspace) + syrupy 5.2.0 |
| **Config file** | root `pyproject.toml` (uv workspace); `tools/memory_regen/tests/conftest.py` (sys.path wiring, `repo_root` fixture) |
| **Quick run command** | `uv run pytest tools/memory_regen -q` |
| **Full suite command** | `uv run pytest tools/memory_regen tools/harness_lint -q` |
| **Estimated runtime** | ~5s scoped / ~20s full |

> **Suite baseline (pre-existing, NOT a Phase 13 regression):** `uv run pytest tools/harness_emit`
> is **1 failed, 46 passed** on a clean tree before any Phase 13 work
> (`test_projected_tree_matches_committed_snapshot`, inherited from Phase 12's deferred re-emit).
> Phase 13's gate is `tools/memory_regen` + `tools/harness_lint` green, with `harness_emit`
> **no worse than 1 failed**. Do NOT regenerate the `.ambr` to make it green — that blesses
> Phase 12's un-emitted tree and steals Phase 15's gate.

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tools/memory_regen -q` (~5s)
- **After every plan wave:** Run `uv run pytest tools/memory_regen tools/harness_lint -q` (~20s)
- **Before `/gsd:verify-work`:** Both green + `harness_emit` no worse than its 1 inherited failure
- **Max feedback latency:** 20 seconds — no watch-mode flags

---

## Per-Task Verification Map

| Plan | Wave | Req | SC | Behavior | Threat Ref | Test Type | Automated Command | File Exists | Status |
|------|------|-----|----|----------|------------|-----------|-------------------|-------------|--------|
| 13-02 | 1 | MEM2-02 | SC2 | **delete+regen byte-identical** — `assemble()` twice ⇒ identical sha256, incl. populated agreements dir | T-13-06 | unit | `uv run pytest tools/memory_regen/tests/test_inject_determinism.py::test_assemble_is_byte_identical -x` | ❌ W0 | ⬜ pending |
| 13-02 | 1 | MEM2-02 | SC2 | **Committed syrupy snapshot** pins payload over a fixed fixture tree | T-13-06 | snapshot | `…::test_payload_matches_snapshot -x` | ❌ W0 | ⬜ pending |
| 13-02 | 1 | MEM2-05 | SC3 | **No wall-clock (static)** — `inject.py` source has no `datetime`/`date.today`/`time.`/`now()` | — | static | `…::test_inject_module_has_no_wallclock -x` | ❌ W0 | ⬜ pending |
| 13-02 | 1 | MEM2-05 | SC3 | **No hook wall-clock (static)** — `memory-inject.sh` no `date`/`$(date)`; `session-inject.ts` no `Date.now`/`new Date` | — | static | `…::test_hook_wrappers_have_no_wallclock -x` | ❌ W0 | ⬜ pending |
| 13-01 | 1 | MEM2-05 | SC3 | **`/checkpoint` mandates the stamp** | — | structural | `grep -q "updated:" harness/commands/checkpoint.md` | ⚠️ after edit | ⬜ pending |
| 13-01 | 1 | MEM2-05 | SC3 | **State files carry a stamp** | — | structural | `grep -q "^updated:" .memory/state/activeContext.md .memory/state/progress.md` | ⚠️ after edit | ⬜ pending |
| 13-01 | 1 | MEM2-05 | SC4 | **Tight progress** — `checkpoint.md` mandates in-flight + remaining + last-N-done, forbids accumulation | — | structural | `grep -qi "last .*done\|no.*done-log\|git holds" harness/commands/checkpoint.md` | ⚠️ after edit | ⬜ pending |
| 13-03 | 2 | MEM2-02 | SC2 | **Sorted iteration** — shuffled creation order ⇒ identical payload; entries slug-ascending | T-13-06 | unit | `…::test_agreements_order_is_sorted_not_filesystem -x` | ❌ W0 | ⬜ pending |
| 13-03 | 2 | MEM2-02 | SC2 | **Budget with agreements present** — full-cap block ⇒ `len(payload) <= 4000` | T-13-02 | unit | `…::test_budget_holds_with_full_agreements_block -x` | ❌ W0 | ⬜ pending |
| 13-03 | 2 | MEM2-02 | SC1/SC2 | **Repo-map survives** a full-cap (M) agreements block — the budget knee | T-13-02 | unit | `…::test_repo_map_survives_full_cap_agreements -x` | ❌ W0 | ⬜ pending |
| 13-03 | 2 | MEM2-02 | SC1 | **Overflow → pointer** — N+1 entries ⇒ pointer, no entry bodies; >M chars ⇒ pointer | T-13-02 | unit | `…::test_overflow_degrades_to_pointer -x` | ❌ W0 | ⬜ pending |
| 13-03 | 2 | MEM2-02 | SC1 | **Never-dropped** — at `budget_chars=1`, agreements + banner + drift all present | T-13-02 | unit | `…::test_agreements_banner_drift_never_dropped -x` | ❌ W0 | ⬜ pending |
| 13-03 | 2 | MEM2-02 | SC1 | **Active-set filter** — `status: retired` excluded; `_TEMPLATE.md` + `README.md` excluded; missing status excluded (fail-closed) | T-13-01 | unit | `…::test_only_active_non_template_agreements_compose -x` | ❌ W0 | ⬜ pending |
| 13-03 | 2 | MEM2-02 | SC1 | **Data-scoped banner** — no `provisional`/`hint, not truth`/`confirm before trusting`; contains `DATA` + `contract` + `adr` | — | unit | `…::test_banner_is_data_scoped` (**rewrite** of `test_inject_assembler.py:19-34`) | ⚠️ rewrite | ⬜ pending |
| 13-03 | 2 | MEM2-02 | SC1 | **Two distinct blocks** — agreements header ≠ banner; both present when agreements exist | — | unit | `…::test_two_distinct_blocks_emitted -x` | ❌ W0 | ⬜ pending |
| 13-03 | 2 | MEM2-02 | SC1 | **Pointer reworded** — no `confirm against contracts/ADR before trusting`; `ACTIVE_HEADER` says progress log | — | unit | `…::test_pointer_is_progress_log_not_imperative -x` | ❌ W0 | ⬜ pending |
| 13-03 | 2 | MEM2-02 | SC1 | **Scope-limiting header** — block header states agreements never override `contracts/`, `docs/adr/`, gates | T-13-01 | unit | `…::test_agreements_header_states_scope_limit -x` | ❌ W0 | ⬜ pending |
| 13-03 | 2 | MEM2-02 | SC1 | **Render shape** — only title + one-line rule; `provenance` field never rendered | T-13-01, T-13-03 | unit | `…::test_render_excludes_provenance -x` | ❌ W0 | ⬜ pending |
| 13-03 | 2 | MEM2-02 | SC1 | **Confined reads** — non-recursive `glob("*.md")`, no symlink follow, no traversal outside `agreements_dir` | T-13-04 | unit | `…::test_agreements_reads_are_confined -x` | ❌ W0 | ⬜ pending |
| 13-03 | 2 | MEM2-05 | SC3 | **Verbatim stamp** — fixture `updated: 2026-01-02` ⇒ `[updated: 2026-01-02]` in payload | — | unit | `…::test_updated_stamp_surfaced_verbatim -x` | ❌ W0 | ⬜ pending |
| 13-03 | 2 | MEM2-05 | SC3 | **Absent-stamp degradation** — no frontmatter / missing key / missing file ⇒ graceful text, **no raise** | T-13-05 | unit | `…::test_absent_stamp_degrades_gracefully -x` | ❌ W0 | ⬜ pending |
| 13-03 | 2 | MEM2-02 | SC1 | **Pointer-only preserved** — no `$schema`; activeContext body (`## In flight`) absent | — | unit | existing `test_inject_assembler.py:88-103` — must stay green | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tools/memory_regen/tests/test_inject_determinism.py` — **NEW**. Byte-identity + syrupy snapshot + no-wall-clock net. Covers SC2/SC3. **Must land before the reframe.** Model: `tools/docs_sync/tests/test_docs_sync_determinism.py:43`.
- [ ] `tools/memory_regen/tests/conftest.py` — **NEW fixture** `tmp_agreements_tree`: synthetic agreements (≥1 active, ≥1 retired, a `_TEMPLATE.md` decoy, a no-frontmatter file), created in **non-alphabetical order** so the sorted-iteration test is meaningful.
- [ ] `assemble(agreements_dir=…)` parameter — **testability prerequisite**, peer of `derived_dir`/`state_dir` (`inject.py:105-109`). Without it, cap/ordering/overflow tests cannot be hermetic (the real active set is empty).
- [ ] `tools/memory_regen/tests/__snapshots__/` — syrupy snapshot dir (does not exist for this package).
- [ ] Rewrite `test_inject_assembler.py:19-34,71,116-122` in lockstep with the reframe — **expected red**, a *planned* update, not a regression.
- No framework install needed (pytest + syrupy already in the workspace).

---

## Manual-Only Verifications

| Behavior | Req | Why Manual | Test Instructions |
|----------|-----|------------|-------------------|
| opencode `session-inject.ts` parity | MEM2-02 | No opencode runtime in this container — authored-only, execution deferred (`session-inject.ts:4-8`) | Static assert only: stub still references `tools.memory_regen.inject` (`test_hook_wiring.py:66-69`) |
| Injected payload *reads* as a directive, not distrust | MEM2-02 (SC1) | Wording quality is human judgement; tests assert only absence of banned phrases | Operator reads `uv run python -m tools.memory_regen.inject` output |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
