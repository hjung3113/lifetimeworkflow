---
phase: 14-write-path-anti-churn-guard-v2-1-c
verified: 2026-07-18T00:00:00Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
---

# Phase 14: Write-path anti-churn guard (v2.1-C) Verification Report

**Phase Goal:** A dedicated /agree command is the sanctioned — and only — way a working-agreement is
added or retired, and it fires only on explicit user feedback; a tools/harness_lint
provenance/anti-invent guard enforces that every entry is origin-stamped and that agents cannot
self-invent unsolicited entries.
**Verified:** 2026-07-18
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `/agree` is the sanctioned write surface; `tools/agree/write.py` refuses (exit 3) rather than inventing a stamp when `--because` is missing/empty/whitespace-only | ✓ VERIFIED | `tools/agree/write.py:52-58` raises `AgreementRefused` on `not (because or "").strip()`; `main()` catches and returns 3 (`write.py:141-142`); mirrors `approve.py`'s `GoldenApprovalRefused` convention per SUMMARY and code inspection |
| 2 | `--because` value becomes the provenance tail, YAML-serialized (not f-string), preventing frontmatter-key forgery via injected `\n` | ✓ VERIFIED | `write.py:69-77` builds `frontmatter` dict with `provenance: f"added because {because}"` as a dict value, then `_dump_frontmatter` (`write.py:22-30`) uses `ruamel.yaml` `YAML(typ="safe")` dump — value is YAML-quoted, not string-concatenated into raw text |
| 3 | Retire flips `status:` to `retired` in place; never deletes | ✓ VERIFIED | `write.py:89-104` `retire()` loads via `load_agreement`, sets `frontmatter["status"] = "retired"`, writes back with body preserved; no `unlink`/removal path exists |
| 4 | A `tools/harness_lint` provenance guard enforces every agreement carries a well-formed origin stamp (status ∈ {active,retired}, quoted ISO `added`, `provenance` matching `^added because \S`), including retired entries, and fails loud (exit 1) on omission/malformation | ✓ VERIFIED | `tools/harness_lint/provenance.py:34-64` `check_agreement()` implements all three structural checks; `lint_dir` (`:74-80`) iterates `iter_agreement_files` (L1-L4 predicate, no L5 active-only filter) so `status: retired` and any `status: pending` typo are both checked; `main()` exits 1 on violations (`:96`) |
| 5 | The guard enforces shape, not truth (honest scope, D-03) — a well-formed but fabricated provenance passes; no PreToolUse hook claims to prevent invention | ✓ VERIFIED (documented design, not a gap) | `provenance.py` docstring explicitly states "validates shape, not truth... accident prevention, not a sandbox"; no PreToolUse/invention-prevention hook exists in `tools/harness_lint/` or `.claude/settings*`; `agree.md` explicitly disclaims this ("impossible to forget, not impossible to forge") |
| 6 | `/agree` is discoverable as a command | ✓ VERIFIED | `harness/commands/agree.md` exists with valid frontmatter (`description`, `agent: orchestrator`); `tools/harness_lint/tests/test_commands.py` is glob-driven (`_command_files()` = `sorted(_COMMANDS_DIR.glob("*.md"))`) so `agree.md` is auto-covered by `test_frontmatter_parses` and related parametrized tests with zero test edits (confirmed by test run below) |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tools/agree/write.py` | `AgreementRefused`, `add`, `retire`, `main`, YAML-serialized provenance | ✓ VERIFIED | All exports present; 145 lines; imports `iter_agreement_files`/`load_agreement` from `tools.harness_lint.agreements` (D-05 shared predicate) |
| `tools/agree/pyproject.toml` | zero-dep virtual member, `package = false` | ✓ VERIFIED (via test run) | Present in `files_modified`; `uv.lock` regenerated; workspace member resolves (pytest ran successfully under `uv run`) |
| `harness/commands/agree.md` | source-only `/agree` command surface, `$ARGUMENTS` macro | ✓ VERIFIED | Contains `!`uv run python -m tools.agree.write $ARGUMENTS`` — positional macro, no shell-string construction |
| `tools/harness_lint/provenance.py` | `Violation`, `check_agreement`, `lint_file`, `lint_dir`, `main` | ✓ VERIFIED | All exports present; 106 lines |
| `tools/harness_lint/agreements.py` | shared L1-L4 predicate: `iter_agreement_files`, `load_agreement` | ✓ VERIFIED | 41 lines; non-recursive `glob("*.md")`, symlink exclusion, confinement via `resolve().relative_to()`, fail-closed parse (catches `OSError`/`ValueError`/`YAMLError`) |
| `harness/commands/lint.md` | wires provenance lint into `/lint`, presence-safe | ✓ VERIFIED | `lint.md:44` — `if [ ! -d .memory/agreements ]; then echo SKIP...; else uv run python -m tools.harness_lint.provenance; fi` |
| `docs/adr/0006-*.md` errata | dated `## Errata` correcting phantom-seed claim, empty set declared correct | ✓ VERIFIED | Errata section present, dated 2026-07-16, appended after `## Links`, cites `git ls-files` + commit `96b8db2`; confirmed by direct `git ls-files .memory/agreements/` returning exactly `README.md` + `_TEMPLATE.md` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `tools/agree/write.py` | `tools/harness_lint/agreements.py` | `from tools.harness_lint.agreements import iter_agreement_files, load_agreement` | ✓ WIRED | Import present at `write.py:11`; used in `retire()` for confined lookup |
| `tools/harness_lint/provenance.py` | `tools/harness_lint/agreements.py` | shared L1-L4 predicate | ✓ WIRED | Import present at `provenance.py:19` |
| `harness/commands/agree.md` | `tools/agree/write.py` | `!` macro | ✓ WIRED | `uv run python -m tools.agree.write $ARGUMENTS` |
| `harness/commands/lint.md` | `tools/harness_lint/provenance.py` | presence-safe bash macro | ✓ WIRED | Confirmed at `lint.md:44` |
| `tools/agree/tests/test_agree_refusal.py` | `tools/harness_lint/provenance.py` | round-trip: writer output passes lint | ✓ WIRED (confirmed by test pass) | Test suite green |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full phase-scoped test suite | `uv run pytest tools/agree tools/harness_lint -q` | `282 passed` | ✓ PASS |
| Extended suite incl. memory_regen (D-17/D-18 cross-cutting) | `uv run pytest tools/agree tools/harness_lint tools/memory_regen -q` | `364 passed`, 4 snapshots passed | ✓ PASS |
| `/lint` provenance macro is presence-safe | inspected `harness/commands/lint.md:44` | conditional skip when `.memory/agreements` absent; else runs `provenance.main()` | ✓ PASS |
| `agree.md` auto-discovered by glob-driven command test | inspected `test_commands.py` `_command_files()` | glob over `harness/commands/*.md`; `EXPECTED_GOLDEN_ADJACENT` frozenset does NOT include `"agree"` (correctly, per D-11) | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| MEM2-04 | 14-01, 14-02, 14-03, 14-04 | `/agree` appends/retires only on explicit feedback; `tools/harness_lint` provenance guard; command "added to EXPECTED_COMMANDS" | ✓ SATISFIED (with documented wording defect) | Substance fully satisfied per truths 1-6 above. The literal phrase "added to `EXPECTED_COMMANDS`" in REQUIREMENTS.md:24 refers to a symbol that does not exist in source (D-11) — `test_commands.py` is glob-driven, not enum-driven, and covers `agree.md` automatically. This is a requirement-wording defect carried forward from drafting, not an unmet requirement; the CONTEXT.md D-11 decision and Nyquist audit both treat this as accepted. REQUIREMENTS.md:65 still shows `| MEM2-04 | Phase 14 | Pending |` — this status line is stale and should be updated to Verified as part of phase closure, but does not itself indicate unmet work. |

### Anti-Patterns Found

None found in phase-modified files. No `TODO`/`FIXME`/`XXX`/`HACK`/`PLACEHOLDER` markers in
`tools/agree/`, `tools/harness_lint/agreements.py`, `tools/harness_lint/provenance.py`,
`harness/commands/agree.md`, or the ADR errata. No empty-return stubs; no hardcoded-empty props in
non-test code.

### Human Verification Required

None. All truths are verifiable via source inspection and automated test execution; no visual,
real-time, or external-service behavior is in scope for this phase.

### Gaps Summary

No gaps found. All must-haves across the four plans (predicate extraction, provenance lint, /agree
writer, ADR errata) are present, substantive, and wired, and the full relevant test suite (364 tests
across `tools/agree`, `tools/harness_lint`, `tools/memory_regen`) passes. The one wording
discrepancy — REQUIREMENTS.md's literal reference to a nonexistent `EXPECTED_COMMANDS` symbol — is a
documented, accepted drafting defect (D-11) satisfied in substance by glob-driven command discovery,
not a functional gap. The honesty caveat (D-03, shape-not-truth) is a deliberate, documented design
property of the guard, not an unmet requirement — its Manual-Only status for "truth" enforcement was
never a phase promise. REQUIREMENTS.md:65's `Pending` status marker is stale relative to actual
completion and should be updated during closure, but this is a bookkeeping note, not a phase gap.

---

_Verified: 2026-07-18_
_Verifier: Claude (gsd-verifier)_
