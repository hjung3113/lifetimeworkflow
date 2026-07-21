---
phase: 14
slug: write-path-anti-churn-guard-v2-1-c
status: final
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-16
audited: 2026-07-18
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `14-RESEARCH.md` § Validation Architecture. Baselines verified live, not assumed.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 (`>=8.4,<9`, `pyproject.toml:17`) + syrupy 5.2.0 |
| **Config file** | `pyproject.toml:37-41` — `testpaths = ["libs/python", "tools"]`, `addopts = "-ra"` |
| **Quick run command** | `uv run pytest tools/harness_lint tools/memory_regen -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~0.5s quick · ~1.6s full |

### ⚠ Baseline is NOT zero-failures — read before interpreting any run

`uv run pytest -q` = **exactly 1 failed / 620 passed**. The single failure is
`tools/harness_emit/tests/test_projected_tree_matches_committed_snapshot` — Phase 12/13's deferred
re-emit debt, owned by **Phase 15**. Verified live this session (both by the researcher and directly).

- **A run reporting `1 failed` is GREEN for this phase.** `0 failed` on the full suite means someone
  updated the snapshot — that is a **failure condition**, not success.
- **NEVER** run `--snapshot-update` on `tools/harness_emit/tests/__snapshots__/`. It blesses the
  un-emitted tree and steals Phase 15's gate.
- CI `core-suite` and `emit-drift` are red on PR #3 for this same single reason. Do not "fix" them.

---

## Sampling Rate

- **After every task commit:** `uv run pytest tools/harness_lint tools/memory_regen -q` → **0 failed**
- **After every plan wave:** `uv run pytest -q` → **exactly 1 failed**, plus
  `git status --porcelain .opencode .claude tools/harness_emit/tests/__snapshots__` → **empty**
- **Before `/gsd:verify-work`:** full suite at the 1-failed baseline · `ruff check . && ruff format --check .` ·
  `/lint` green against an empty agreements dir
- **Max feedback latency:** ~2 seconds

---

## Per-Task Verification Map

**Audited 2026-07-18** — every row below was re-run live against the shipped code (not assumed from
plan intent). `Verified` reflects the actual state observed during the retroactive audit.

| # | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | Verified |
|---|-------------|------------|-----------------|-----------|-------------------|----------|
| 1 | MEM2-04 | — | Well-formed stamp passes | unit | `test_provenance.py::test_well_formed_stamp_is_clean` | ✅ green |
| 2 | MEM2-04 | T-13-01 | **NEG:** `provenance:` absent → Violation | unit | `test_provenance.py::test_absent_provenance_is_a_violation` | ✅ green |
| 3 | MEM2-04 | T-13-01 | **NEG:** no `added because ` prefix → Violation | unit | `test_provenance.py::test_provenance_requires_added_because_prefix` | ✅ green |
| 4 | MEM2-04 | T-13-01 | **NEG:** empty tail (`"added because"`) → Violation | unit | `test_provenance.py::test_provenance_rejects_empty_tail` | ✅ green |
| 5 | MEM2-04 | T-13-01 | **NEG:** whitespace-only tail → Violation | unit | `test_provenance.py::test_provenance_rejects_whitespace_only_tail` | ✅ green |
| 6 | MEM2-04 | — | **NEG:** `added: 2026-07-16` unquoted → `date` → **Violation, NOT TypeError** (D-02) | unit | `test_provenance.py::test_unquoted_date_yields_violation_not_typeerror` | ✅ green |
| 7 | MEM2-04 | — | **NEG:** `added: "16-07-2026"` → Violation | unit | `test_provenance.py::test_non_iso_added_stamp_is_a_violation` | ✅ green |
| 8 | MEM2-04 | — | **NEG:** `status: pending` → Violation (**only reachable because of D-14**) | unit | `test_provenance.py::test_pending_status_is_a_violation` | ✅ green |
| 9 | MEM2-04 | — | **NEG:** `status: retired` entry **IS linted**, not skipped (D-14) | unit | `test_provenance.py::test_retired_entries_are_linted_without_being_rejected` | ✅ green |
| 10 | MEM2-04 | T-13-01 | **EXCL:** `_TEMPLATE.md` + `README.md` excluded, **not flagged** | unit | `test_provenance.py::test_template_and_readme_are_excluded` | ✅ green |
| 11 | MEM2-04 | T-13-04 | **EXCL:** symlink not followed (mirror `test_inject_assembler.py:72-76`) | unit | `test_agreements_predicate.py::test_symlink_escape_is_excluded` | ✅ green |
| 12 | MEM2-04 | T-13-05 | Empty dir → `[]`, exit 0 (presence-safe) | unit | `test_agreements_predicate.py::test_empty_and_missing_dirs_are_presence_safe` | ✅ green |
| 13 | MEM2-04 | — | `main()`: exit 0 clean / 1 dirty; FAIL→stderr, OK→stdout | unit | `test_provenance.py::test_main_uses_stdout_for_ok_and_stderr_for_all_failures` (capsys) | ✅ green |
| 14 | MEM2-04 | T-13-06 | Predicate is **sorted**, not filesystem order | unit | `test_agreements_predicate.py::test_files_are_sorted_not_creation_order` | ✅ green |
| 15 | MEM2-04 | — | **D-05/D-18 parity:** lint & injector select the same files | integration | `test_agreements_predicate.py::test_predicate_parity_with_injector_render_policy` | ✅ green |
| 16 | MEM2-04 | T-13-01 | `/agree --because ""` / `"   "` / omitted → **exit 3** | unit | `tools/agree/tests/test_agree_refusal.py::test_cli_refusal_exits_three_for_missing_or_blank_because` | ✅ green |
| 17 | MEM2-04 | **D-15** | **NEG:** `--because` containing `"` or `\n` cannot forge a sibling frontmatter key | unit | `test_agree_refusal.py::test_yaml_serialization_prevents_frontmatter_key_forgery` | ✅ green |
| 18 | MEM2-04 | — | `/agree --because "<x>"` → file whose stamp **passes the provenance lint** (round-trip) | integration | `test_agree_refusal.py::test_written_agreement_round_trips_through_provenance_lint` | ✅ green |
| 19 | MEM2-04 | — | `--retire <slug>` flips status in place; **file still exists**; diff limited to the status line | unit | `test_agree_refusal.py::test_retire_flips_status_in_place_and_preserves_body` | ✅ green |
| 20 | MEM2-04 | — | `--retire` unknown slug → refuse, no file created | unit | `test_agree_refusal.py::test_retire_unknown_slug_refuses_and_creates_nothing` | ✅ green |
| 21 | MEM2-04 | — | `agree.md` passes the glob command lint (**D-11**, zero test edits) | unit | `uv run pytest tools/harness_lint/tests/test_commands.py -q -k agree` | ✅ green (4 tests, parametrized by glob discovery incl. `agree.md`) |
| 22 | MEM2-04 | — | `agree.md` description carries a `_ROUTING_TRIGGERS` token | unit | `test_commands.py::test_description_is_routing_signal[agree]` | ✅ green |
| R1 | REGRESSION | T-13-06 | byte-identity determinism survives the extraction | unit | `uv run pytest tools/memory_regen/tests/test_inject_determinism.py -q` | ✅ green |
| R2 | REGRESSION | — | **wall-clock gate WIDENED to `agreements.py`** + negative control (**D-17**) | unit | `test_inject_determinism.py::test_inject_module_has_no_wallclock` + `::test_negative_control_wallclock_scan_flags_planted_token` | ✅ green — gate scans `tools/harness_lint/agreements.py`, not only `inject.py`; negative control (`x = datetime`) provably fails the same predicate |
| R3 | REGRESSION | T-13-02 | ~4000-char budget holds | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py -q` | ✅ green (20 tests) |
| R4 | REGRESSION | — | `harness_emit` no worse than **1 failed / 46 passed** baseline | smoke | `uv run pytest tools/harness_emit -q` | ✅ green — **47 passed, 0 failed** at audit time (better than the Phase-14-era baseline; the emit-drift debt cited in this doc's ⚠ banner was closed by Phase 15) |
| R5 | REGRESSION | — | `.opencode/` + `.claude/` untouched (**D-10**) | smoke | `git status --porcelain .opencode .claude` → empty | ✅ verified empty at audit time |

*Status legend: ✅ green (executed live, passing) · ❌ red · ⚠️ needs edit*

### Anti-invent posture (D-03) stays manual-only by design

MEM2-04 also requires agents cannot auto-invent entries. The provenance lint validates **shape**,
not **truth** — a fabricated-but-well-formed `provenance: "added because <lie>"` stamp passes any
automated check by construction (see `tools/harness_lint/provenance.py`'s own module docstring: "A
well-formed but fabricated provenance can pass; this is accident prevention, not a sandbox"). This
audit confirms that framing is correct and leaves it as the pre-existing **Manual-Only
Verification** below rather than manufacturing a test that would assert a false property.

### R2 is the one that can silently rot

`tools/memory_regen/tests/test_inject_determinism.py:70-75` reads **`inject.py` as TEXT** and scans
for 5 wall-clock tokens. Moving the predicate into `tools/harness_lint/agreements.py` takes that code
**out from under a live gate** without any test going red. The widening MUST land in the same task as
the extraction (D-17) — a passing suite is not evidence here, so add a **negative control** (a planted
clock token in the new module must FAIL the gate) to prove the widened gate actually bites.

---

## Wave 0 Requirements

**None — existing infrastructure covers all phase requirements.**

- pytest 8.4.2 installed; `tools/harness_lint/tests/conftest.py` + `tools/memory_regen/tests/conftest.py` exist.
- `tmp_agreements_tree` (`tools/memory_regen/tests/conftest.py:91-145`) is a ready-made 5-file corpus
  (active ×2, retired ×1, `_TEMPLATE.md`, `README.md`) **created in non-alphabetical order** — so the
  sort assertion (#14) is falsifiable rather than vacuous.

**Wave-1 infra note (not a Wave-0 gap):** a new `tools/agree/` member needs
`tools/agree/tests/conftest.py` with the sys.path shim — clone `memory_regen/tests/conftest.py:26-33`
verbatim.

**Fixture-reuse caveat:** `tmp_agreements_tree` lives in `tools/memory_regen/tests/conftest.py` and is
therefore **not visible** to `tools/harness_lint/tests/` or `tools/agree/tests/`. Plans must either
relocate it to a shared location or duplicate it deliberately — do not assume cross-member conftest
visibility.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `.opencode/` + `.claude/` untouched (D-10) | MEM2-04 | Absence-of-change is a git property, not a pytest assertion | `git status --porcelain .opencode .claude` → must be empty |
| ADR-0006 errata lands via the dev-bypass path (D-12) | MEM2-06 adj. | Constitution write; `contract_guard` denies the agent Write tool by design | Set `HARNESS_DEV_BYPASS` in gitignored `.claude/settings.local.json` (currently ABSENT) **or** use raw shell. **Never forge `GOLDEN_APPROVE_HUMAN`.** Byte-hygiene (`lint_bytes`) still applies on this path (`contract_guard.py:83-90`) — the errata must be LF / no-BOM. |
| Anti-invent property (D-03) | MEM2-04 | **Unenforceable by any test.** The lint checks shape, not truth — a fabricated-but-well-formed stamp passes. | Human review of the git diff. Do not add tests that pretend otherwise. |

---

## Validation Sign-Off

- [x] All tasks have automated verify (or an explicit manual-only entry above)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references *(N/A — no gaps)*
- [x] No watch-mode flags
- [x] Feedback latency < 2s
- [x] **R2's widened wall-clock gate has a negative control** (planted token FAILS)
- [x] **Full-suite reading confirmed live at audit time: `690 passed`, `0 failed`.** The
      `1 failed / 620 passed` baseline this doc originally warned about (the deferred
      `test_projected_tree_matches_committed_snapshot` re-emit debt) was Phase 15's to close, and
      Phase 15 has since landed (see repo git log: `docs(phase-15): complete phase execution`).
      `0 failed` is therefore the correct green reading now, not a stolen-gate failure condition —
      this note supersedes the stale banner at the top of this file for future readers.
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** confirmed by retroactive Nyquist audit 2026-07-18 (see trail below).

---

## Validation Audit 2026-07-18

Retroactive adversarial coverage audit (Nyquist auditor pass) against a phase whose code was
already live. Starting hypothesis per protocol: assume every MEM2-04 observable behavior is
uncovered until a passing test proves otherwise. Implementation files were read-only for this pass
(`tools/agree/write.py`, `tools/harness_lint/provenance.py`, `tools/harness_lint/agreements.py`) —
no implementation edits were made or needed.

**Method:** every row of the Per-Task Verification Map (22 requirement rows + 5 regression rows)
was re-run individually, live, against the current tree — not accepted on the strength of the plan
narrative. Each row's `Automated Command` above is the exact command executed for this audit.

**Findings:**

- **0 genuinely MISSING behaviors found.** Every MEM2-04-observable behavior named in the gap list
  (refusal-first `--because` exit-3, provenance shape checks incl. the D-02 TypeError-vs-Violation
  distinction, YAML-safe serialization / no frontmatter-key-forgery, retire-flips-in-place with
  file-preservation, glob-driven `/agree` command discovery, D-05/D-18 lint↔injector selection
  parity, and the R2 wall-clock-gate widening with its negative control) already had a real,
  independently-runnable, passing pytest test — not a stub, not a structural-only check standing in
  for behavior.
- No new test files were created — generating a duplicate test against an already-covered behavior
  would have been noise, not coverage, per the "do not duplicate" instruction.
- One stale-but-harmless doc artifact was found and corrected: the file's own "⚠ Baseline is NOT
  zero-failures" banner (top of file) was accurate when written (Phase 12/13 debt, owned by Phase
  15) but Phase 15 has since landed per `git log` (`421fbf5 docs(phase-17): complete phase
  execution` postdates `a78fd2b docs(phase-15): complete phase execution`), and the full suite now
  reads **690 passed, 0 failed** live. The sign-off checklist above now carries the corrected
  reading and points future readers past the stale banner; the banner text itself was left in place
  (implementation/history record, not something this audit should silently rewrite) rather than
  edited to avoid overstating this pass's scope.
- The D-03 anti-invent property was re-confirmed as correctly manual-only, not a coverage gap: the
  provenance lint's own module docstring states it checks shape, not truth, by design. No test can
  distinguish a genuine user quote from a plausible fabrication without external ground truth;
  writing one would assert a false property, which the auditor stance explicitly forbids.

**Verification command and result (run at audit time):**

```
$ uv run pytest tools/agree tools/harness_lint -q
282 passed in 0.43s

$ uv run pytest -q
690 passed in 5.52s
```

**Disposition:** all 22 MEM2-04 rows + 5 regression rows are backed by live-verified automated
tests; the sole remaining behavior (D-03 anti-invent) is a correctly-justified manual-only entry,
not an unfilled gap. `status: final`, `nyquist_compliant: true` set above.

**Approval:** pending
