---
phase: 14
slug: write-path-anti-churn-guard-v2-1-c
status: draft
nyquist_compliant: false
wave_0_complete: true
created: 2026-07-16
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

| # | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists |
|---|-------------|------------|-----------------|-----------|-------------------|-------------|
| 1 | MEM2-04 | — | Well-formed stamp passes | unit | `uv run pytest tools/harness_lint/tests/test_provenance.py -x` | ❌ W1 |
| 2 | MEM2-04 | T-13-01 | **NEG:** `provenance:` absent → Violation | unit | ↑ | ❌ W1 |
| 3 | MEM2-04 | T-13-01 | **NEG:** no `added because ` prefix → Violation | unit | ↑ | ❌ W1 |
| 4 | MEM2-04 | T-13-01 | **NEG:** empty tail (`"added because"`) → Violation | unit | ↑ | ❌ W1 |
| 5 | MEM2-04 | T-13-01 | **NEG:** whitespace-only tail → Violation | unit | ↑ | ❌ W1 |
| 6 | MEM2-04 | — | **NEG:** `added: 2026-07-16` unquoted → `date` → **Violation, NOT TypeError** (D-02) | unit | ↑ | ❌ W1 |
| 7 | MEM2-04 | — | **NEG:** `added: "16-07-2026"` → Violation | unit | ↑ | ❌ W1 |
| 8 | MEM2-04 | — | **NEG:** `status: pending` → Violation (**only reachable because of D-14**) | unit | ↑ | ❌ W1 |
| 9 | MEM2-04 | — | **NEG:** `status: retired` entry **IS linted**, not skipped (D-14) | unit | ↑ | ❌ W1 |
| 10 | MEM2-04 | T-13-01 | **EXCL:** `_TEMPLATE.md` + `README.md` excluded, **not flagged** | unit | ↑ | ❌ W1 |
| 11 | MEM2-04 | T-13-04 | **EXCL:** symlink not followed (mirror `test_inject_assembler.py:72-76`) | unit | `test_agreements_predicate.py` | ❌ W1 |
| 12 | MEM2-04 | T-13-05 | Empty dir → `[]`, exit 0 (presence-safe) | unit | ↑ | ❌ W1 |
| 13 | MEM2-04 | — | `main()`: exit 0 clean / 1 dirty; FAIL→stderr, OK→stdout | unit | `test_provenance.py` (capsys) | ❌ W1 |
| 14 | MEM2-04 | T-13-06 | Predicate is **sorted**, not filesystem order | unit | `test_agreements_predicate.py` | ❌ W1 |
| 15 | MEM2-04 | — | **D-05/D-18 parity:** lint & injector select the same files | integration | ↑ | ❌ W1 |
| 16 | MEM2-04 | T-13-01 | `/agree --because ""` / `"   "` / omitted → **exit 3** | unit | `tools/agree/tests/test_agree_refusal.py` | ❌ W1 |
| 17 | MEM2-04 | **D-15** | **NEG:** `--because` containing `"` or `\n` cannot forge a sibling frontmatter key | unit | ↑ | ❌ W1 |
| 18 | MEM2-04 | — | `/agree --because "<x>"` → file whose stamp **passes the provenance lint** (round-trip) | integration | ↑ | ❌ W1 |
| 19 | MEM2-04 | — | `--retire <slug>` flips status in place; **file still exists**; diff limited to the status line | unit | ↑ | ❌ W1 |
| 20 | MEM2-04 | — | `--retire` unknown slug → refuse, no file created | unit | ↑ | ❌ W1 |
| 21 | MEM2-04 | — | `agree.md` passes the glob command lint (**D-11**, zero test edits) | unit | `uv run pytest tools/harness_lint/tests/test_commands.py -q` | ✅ exists |
| 22 | MEM2-04 | — | `agree.md` description carries a `_ROUTING_TRIGGERS` token | unit | ↑ | ✅ exists |
| R1 | REGRESSION | T-13-06 | byte-identity determinism survives the extraction | unit | `uv run pytest tools/memory_regen/tests/test_inject_determinism.py -q` | ✅ exists |
| R2 | REGRESSION | — | **wall-clock gate WIDENED to `agreements.py`** + negative control (**D-17**) | unit | ↑ (**EDIT REQUIRED**) | ⚠ EDIT |
| R3 | REGRESSION | T-13-02 | ~4000-char budget holds | unit | `test_inject_assembler.py:32, 152-158` | ✅ exists |
| R4 | REGRESSION | — | `harness_emit` no worse than **1 failed / 46 passed** | smoke | `uv run pytest tools/harness_emit -q` | ✅ exists |
| R5 | REGRESSION | — | `.opencode/` + `.claude/` untouched (**D-10**) | smoke | `git status --porcelain .opencode .claude` → empty | manual |

*Status legend: ⬜ pending · ✅ green · ❌ red · ⚠️ needs edit*

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

- [ ] All tasks have automated verify (or an explicit manual-only entry above)
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references *(N/A — no gaps)*
- [ ] No watch-mode flags
- [ ] Feedback latency < 2s
- [ ] **R2's widened wall-clock gate has a negative control** (planted token FAILS)
- [ ] **Full-suite reading is `1 failed`, not `0 failed`** — snapshot untouched
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
