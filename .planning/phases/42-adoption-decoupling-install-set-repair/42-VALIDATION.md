---
phase: 42
slug: adoption-decoupling-install-set-repair
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-28
---

# Phase 42 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `42-RESEARCH.md` §"Validation Architecture".
> **Shape:** mostly removal (a gate, an import, a data read) plus **one new test file** — the
> fixture-install test that proves PROD-01. Per CONTEXT.md **D-16** no mutation-proof /
> adversarial-input table is owed: this phase removes a gate and adds no control. The new test is
> *coverage of a product property*, not a contributor-facing gate.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest via `uv run pytest` (uv workspace, `members = ["libs/python", "tools/*"]`) |
| **Config file** | root `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `uv run pytest tools/adoption_apply tools/adoption_scan -q` |
| **Full suite command** | `uv run pytest -q` (1340 passing at Phase 41 close) |
| **Estimated runtime** | quick ~10-20s · full ~50s |

---

## Sampling Rate

- **After every task commit:** `uv run pytest tools/adoption_apply tools/adoption_scan -q`, plus
  `uv run pytest --collect-only -q` whenever a module or test file is deleted — a stranded import
  surfaces as a collection error, not a failure.
- **After every plan wave:** full `uv run pytest -q`.
- **Before `/gsd:verify-work`:** full suite green and all four structural gates clean
  (`emit-drift`, `stale-derived`, `contract-drift`, ruff ratchet).
- **Ordering caveat (D-12):** run gates *after* `git add` + `git commit -- <pathspec>`, never before —
  `tools/adoption_scan/destinations.py:217` reads `git ls-files`, so a tracked deletion reds until
  staged and committed. A red before the commit is expected; amend if still red after.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| (approval gate delete) | TBD | 1 | CER-06 | — | N/A | absence + collection | `test ! -f tools/adoption_apply/approval.py` ; `uv run pytest --collect-only -q` exits 0 | ✅ | ⬜ pending |
| (contract delete + rebaseline) | TBD | 1 | CER-06 | — | N/A | gate | `uv run python -m tools.contract_drift.drift` exits 0 | ✅ | ⬜ pending |
| (secret-pattern inline) | TBD | 2 | CER-06 | — | redaction unchanged | unit | `uv run pytest tools/adoption_scan/tests/test_scan_exclusions.py -x` | ✅ (needs the `:211` repoint) | ⬜ pending |
| (`tools/**` catalog row) | TBD | 2 | PROD-01 | — | N/A | unit | `uv run pytest tools/adoption_scan -q` | ✅ | ⬜ pending |
| (fixture-install test) | TBD | 2 | PROD-01 | — | N/A | integration **(NEW)** | `uv run pytest tools/adoption_scan/tests/test_install_completeness.py -x` | ❌ **Wave 0** | ⬜ pending |
| (test/prose sweep) | TBD | 3 | CER-06 | — | N/A | grep + suite | greps below ; `uv run pytest -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Structural assertions (SC-1/SC-2):**

```
grep -rn "task_control" tools/adoption_apply/ tools/adoption_scan/
grep -rn "GOLDEN_APPROVE_HUMAN" tools/adoption_apply/ tools/adoption_scan/
```

Both must return **exit 1, no output**.

**The unset-env run (SC-2's behavioral half):** a `draft → apply` cycle completes with
`GOLDEN_APPROVE_HUMAN` unset — `env -u GOLDEN_APPROVE_HUMAN` in front of both invocations against a
scratch target. `test_cli.py`'s rewritten end-to-end case covers this once its `_promote()`
precondition is dropped.

**What a botched decoupling looks like** (observables, not feelings):
- a stranded `from tools.task_control...` or `from tools.adoption_apply.approval import ...` →
  pytest **collection** error;
- `test_scan_exclusions.py:211` reads `scan._GATE_REGISTRY_PATH` directly → `AttributeError` after the
  inline. **This string matches neither structural grep** — it is the easiest miss in the phase;
- the 8 inlined patterns not byte-identical → a redaction test fails. Fix the copy, never the test;
- a removed contract without a manifest rebaseline → `contract-drift` red;
- a `harness/**` prose edit not followed by `python -m tools.harness_emit` → `emit-drift` non-empty.

---

## Wave 0 Requirements

- [ ] `tools/adoption_scan/tests/test_install_completeness.py` — **the one new file in this phase**.
  Walks every `uv run python -m tools.X` reference in the emitted commands and `.github/workflows/**`
  (research enumerated **21** distinct modules) and asserts each `tools.X` exists in an applied target
  tree. Reuses existing helpers (`destination_catalog`, `harness_proposed_hashes`, `build_manifest`,
  `apply_manifest`) against `tmp_path` — **no new fixture directory**.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Adoption still usable end-to-end by a human after the gate is gone | CER-06 | The point of the phase is that review moves to the PR; only a human can judge the resulting flow reads sensibly | Run `draft` then `apply` against a scratch target with `GOLDEN_APPROVE_HUMAN` unset; confirm no step asks for a promotion and the rewritten `/adopt` docs match what actually happens |

---

## Validation Sign-Off

- [ ] All tasks have an automated verify command (table above)
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 delivered: `test_install_completeness.py` exists and passes
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s (quick) / < 60s (full)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
