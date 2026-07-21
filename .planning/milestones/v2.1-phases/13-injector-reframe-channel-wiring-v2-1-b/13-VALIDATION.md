---
phase: 13
slug: injector-reframe-channel-wiring-v2-1-b
status: final
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-15
audited: 2026-07-18
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
| 13-02 | 1 | MEM2-02 | SC2 | **delete+regen byte-identical** — `assemble()` twice ⇒ identical sha256, incl. populated agreements dir | T-13-06 | unit | `uv run pytest tools/memory_regen/tests/test_inject_determinism.py::test_assemble_is_byte_identical -x` | ✅ | ✅ green |
| 13-02 | 1 | MEM2-02 | SC2 | **Committed syrupy snapshot** pins payload over a fixed fixture tree | T-13-06 | snapshot | `uv run pytest tools/memory_regen/tests/test_inject_determinism.py::test_payload_matches_snapshot -x` | ✅ | ✅ green |
| 13-02 | 1 | MEM2-05 | SC3 | **No wall-clock (static)** — `inject.py` source has no `datetime`/`date.today`/`time.`/`now()` | — | static | `uv run pytest tools/memory_regen/tests/test_inject_determinism.py::test_inject_module_has_no_wallclock -x` | ✅ | ✅ green |
| 13-02 | 1 | MEM2-05 | SC3 | **No hook wall-clock (static)** — `memory-inject.sh` no `date`/`$(date)`; `session-inject.ts` no `Date.now`/`new Date` | — | static | `uv run pytest tools/memory_regen/tests/test_inject_determinism.py::test_hook_wrappers_have_no_wallclock -x` | ✅ | ✅ green |
| 13-01 | 1 | MEM2-05 | SC3 | **`/checkpoint` mandates the stamp** | — | unit | `uv run pytest tools/memory_regen/tests/test_checkpoint_command.py::test_checkpoint_mandates_the_updated_stamp -x` | ✅ | ✅ green |
| 13-01 | 1 | MEM2-05 | SC3 | **State files carry a stamp** | — | unit | `uv run pytest tools/memory_regen/tests/test_checkpoint_command.py::test_state_files_carry_the_updated_stamp -x` | ✅ | ✅ green |
| 13-01 | 1 | MEM2-05 | SC4 | **Tight progress** — `checkpoint.md` mandates in-flight + remaining + last-N-done, forbids accumulation | — | unit | `uv run pytest tools/memory_regen/tests/test_checkpoint_command.py::test_checkpoint_mandates_tight_bounded_progress -x` | ✅ | ✅ green |
| 13-01 | 1 | MEM2-05 | SC3 | **`/checkpoint` adds no wall-clock** (D-11/Q6) — no `$(date` in `checkpoint.md` | — | unit | `uv run pytest tools/memory_regen/tests/test_checkpoint_command.py::test_checkpoint_adds_no_wallclock -x` | ✅ | ✅ green |
| 13-03 | 2 | MEM2-02 | SC2 | **Sorted iteration** — shuffled creation order ⇒ identical payload; entries slug-ascending | T-13-06 | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py::test_agreements_order_is_sorted_not_filesystem -x` | ✅ | ✅ green |
| 13-03 | 2 | MEM2-02 | SC2 | **Budget with agreements present** — full-cap block ⇒ `len(payload) <= 4000` | T-13-02 | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py::test_budget_holds_with_full_agreements_block -x` | ✅ | ✅ green |
| 13-03 | 2 | MEM2-02 | SC1/SC2 | **Repo-map survives** a full-cap (M) agreements block — the budget knee | T-13-02 | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py::test_repo_map_survives_full_cap_agreements -x` | ✅ | ✅ green |
| 13-03 | 2 | MEM2-02 | SC1 | **Overflow → pointer** — N+1 entries ⇒ pointer, no entry bodies; >M chars ⇒ pointer | T-13-02 | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py::test_overflow_degrades_to_pointer -x` | ✅ | ✅ green |
| 13-03 | 2 | MEM2-02 | SC1 | **Never-dropped** — at `budget_chars=1`, agreements + banner + drift all present | T-13-02 | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py::test_agreements_banner_drift_never_dropped -x` | ✅ | ✅ green |
| 13-03 | 2 | MEM2-02 | SC1 | **Active-set filter** — `status: retired` excluded; `_TEMPLATE.md` + `README.md` excluded; missing status excluded (fail-closed) | T-13-01 | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py::test_only_active_non_template_agreements_compose -x` | ✅ | ✅ green |
| 13-03 | 2 | MEM2-02 | SC1 | **Data-scoped banner** — no `provisional`/`hint, not truth`/`confirm before trusting`; contains `DATA` + `contract` + `adr` | — | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py::test_banner_is_data_scoped -x` | ✅ | ✅ green |
| 13-03 | 2 | MEM2-02 | SC1 | **Two distinct blocks** — agreements header ≠ banner; both present when agreements exist | — | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py::test_two_distinct_blocks_emitted -x` | ✅ | ✅ green |
| 13-03 | 2 | MEM2-02 | SC1 | **Pointer reworded** — no `confirm against contracts/ADR before trusting`; `ACTIVE_HEADER` says progress log | — | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py::test_pointer_is_progress_log_not_imperative -x` | ✅ | ✅ green |
| 13-03 | 2 | MEM2-02 | SC1 | **Scope-limiting header** — block header states agreements never override `contracts/`, `docs/adr/`, gates | T-13-01 | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py::test_agreements_header_states_scope_limit -x` | ✅ | ✅ green |
| 13-03 | 2 | MEM2-02 | SC1 | **Render shape** — only title + one-line rule; `provenance` field never rendered | T-13-01, T-13-03 | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py::test_render_excludes_provenance -x` | ✅ | ✅ green |
| 13-03 | 2 | MEM2-02 | SC1 | **Confined reads** — non-recursive `glob("*.md")`, no symlink follow, no traversal outside `agreements_dir` | T-13-04 | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py::test_agreements_reads_are_confined -x` | ✅ | ✅ green |
| 13-03 | 2 | MEM2-05 | SC3 | **Verbatim stamp** — fixture `updated: 2026-01-02` ⇒ `[updated: 2026-01-02]` in payload | — | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py::test_updated_stamp_surfaced_verbatim -x` | ✅ | ✅ green |
| 13-03 | 2 | MEM2-05 | SC3 | **Absent-stamp degradation** — no frontmatter / missing key / missing file ⇒ graceful text, **no raise** | T-13-05 | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py::test_absent_stamp_degrades_gracefully -x` | ✅ | ✅ green |
| 13-03 | 2 | MEM2-02 | SC1 | **Pointer-only preserved** — no `$schema`; activeContext body (`## In flight`) absent | — | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py::test_active_context_is_pointer_not_body -x` | ✅ | ✅ green |
| 13-04 | 3 | MEM2-02 | SC1 | **Kill switch absent** — `.memory/.inject-disabled` does not exist (D-20) | T-13-01 | unit | `uv run pytest tools/memory_regen/tests/test_hook_end_to_end.py::test_kill_switch_file_is_absent -x` | ✅ NEW | ✅ green |
| 13-04 | 3 | MEM2-02 | SC1 | **Live end-to-end payload** — `bash .claude/hooks/memory-inject.sh` emits non-empty, data-scoped `additionalContext` (not the `\|\| echo ''` swallow, T-13-05) | T-13-05 | integration | `uv run pytest tools/memory_regen/tests/test_hook_end_to_end.py::test_hook_emits_non_empty_data_scoped_payload -x` | ✅ NEW | ✅ green |
| 13-04 | 3 | MEM2-02 | SC1 | **No retired provisional wording in the live payload** (D-06) | — | integration | `uv run pytest tools/memory_regen/tests/test_hook_end_to_end.py::test_hook_payload_carries_no_retired_provisional_wording -x` | ✅ NEW | ✅ green |

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

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 20s (full `tools/memory_regen -q` run: ~2.1s for 358 tests)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** granted (retroactive audit, 2026-07-18) — see Validation Audit trail below.

---

## Validation Audit 2026-07-18

Retroactive Nyquist coverage audit (phase code was already live; `status: draft` /
`nyquist_compliant: false` were stale). Every row in the Per-Task Verification Map above was
cross-referenced against the actual test suite (not assumed from the map's prior "❌ W0 / ⬜
pending" placeholders, which predated Wave 0 execution and were never updated after 13-02/13-03
landed).

**Method:** for each MEM2-02 / MEM2-05 observable behavior, located the named test in
`tools/memory_regen/tests/{test_inject_assembler,test_inject_determinism,test_hook_wiring}.py`,
ran it individually, and classified COVERED only on a passing execution — not on the test file
existing.

### Gaps found

1. **`/checkpoint` structural mandates (3 map rows) were "automated" only as bare shell `grep`
   commands, never wrapped into the `uv run pytest tools/memory_regen -q` sampling loop.** A
   regression here (e.g. an edit to `checkpoint.md` dropping the `updated:` mandate) would not be
   caught by the documented sampling cadence in this file (`After every task commit: run
   uv run pytest tools/memory_regen -q`), since the sampling command never touches a bare grep.
2. **No test executed the live SessionStart hook end-to-end.** 13-04's acceptance criteria ran
   `bash .claude/hooks/memory-inject.sh | node -e '...'` manually during plan execution and
   asserted the emitted `additionalContext` was non-empty, data-scoped, and free of retired
   `provisional` wording — proving the kill switch removal (D-20) and the `\|\| echo ''` swallow
   (T-13-05) were not silently masking a broken assembler. That command was never captured as a
   standing regression test; nothing in the suite would catch a reintroduced
   `.memory/.inject-disabled` kill switch or a hook silently degrading to an empty payload.

All other map rows (assembler ordering/cap/overflow/fail-closed filtering, determinism/byte-
identity, no-wall-clock static gates, verbatim stamp surfacing, absent-stamp degradation, pointer
rewording, banner data-scoping) were confirmed COVERED — the named tests exist, ran, and passed.

### Gaps resolved (new tests, all passing)

| New file | Behavior | Result |
|----------|----------|--------|
| `tools/memory_regen/tests/test_checkpoint_command.py::test_checkpoint_mandates_the_updated_stamp` | `/checkpoint` mandates the `updated:` stamp, quoted | PASS |
| `tools/memory_regen/tests/test_checkpoint_command.py::test_checkpoint_mandates_tight_bounded_progress` | `/checkpoint` mandates last-N-done + remaining, forbids accumulation | PASS |
| `tools/memory_regen/tests/test_checkpoint_command.py::test_checkpoint_adds_no_wallclock` | `/checkpoint` adds no `$(date` (D-11/Q6) | PASS |
| `tools/memory_regen/tests/test_checkpoint_command.py::test_state_files_carry_the_updated_stamp` | Both state files carry `^updated:` frontmatter | PASS |
| `tools/memory_regen/tests/test_hook_end_to_end.py::test_kill_switch_file_is_absent` | `.memory/.inject-disabled` does not exist | PASS |
| `tools/memory_regen/tests/test_hook_end_to_end.py::test_hook_emits_non_empty_data_scoped_payload` | Live hook subprocess emits `additionalContext` > 1000 chars containing `DATA` | PASS |
| `tools/memory_regen/tests/test_hook_end_to_end.py::test_hook_payload_carries_no_retired_provisional_wording` | Live payload contains no `provisional` / `hint, not truth` / `confirm before trusting` | PASS |

No debug iterations needed — all 7 new tests passed on first run. No implementation files were
read as fixable-on-failure; `inject.py`, `memory-inject.sh`, and `checkpoint.md` were treated
strictly read-only throughout.

### Escalated

None. No BLOCKER findings — every MEM2-02 / MEM2-05 observable behavior in the map now resolves
to an automated, passing test.

### Full suite after the audit

`uv run pytest tools/memory_regen tools/harness_lint -q` → **351 passed** (was 344 before this
audit's 7 new tests were added; +7 = 351, consistent).
