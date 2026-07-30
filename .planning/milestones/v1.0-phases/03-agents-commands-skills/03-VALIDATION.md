---
phase: 3
slug: agents-commands-skills
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-08
---

# Phase 3 — Validation Strategy

> Source: `03-RESEARCH.md` §Validation Architecture. Structural-validation phase (opencode runtime absent, D-02) + two RUNNABLE Python deliverables (permission resolver, /docs-sync).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.4,<9 + syrupy 5.2.0 (determinism snapshots) |
| **Config file** | root `pyproject.toml` (`testpaths` covers `tools`) |
| **Quick run command** | `uv run pytest tools/harness_perms tools/docs_sync tools/harness_lint -x -q` |
| **Full suite command** | `uv run pytest` (keep Phase-1/2 suites green) |
| **Estimated runtime** | ~15–40 s |

---

## Sampling Rate

- **After every task commit:** `uv run pytest tools/harness_perms tools/docs_sync tools/harness_lint -x -q`
- **After every plan wave:** `uv run pytest`
- **Before `/gsd:verify-work`:** full suite green; /docs-sync determinism snapshot stable

---

## Per-Task Verification Map

| Req | Behavior | Test Type | Automated Command | File |
|-----|----------|-----------|-------------------|------|
| CONFIG-01 | `harness/opencode.json` JSON-Schema valid; has model/small_model/instructions/formatter/mcp | structural | `uv run pytest tools/harness_lint/tests/test_opencode_json.py -x` | ❌ W0 |
| CONFIG-02 | 15-key matrix well-formed; last-wins resolves (`git push --force`→ask/deny, `dotnet test`→allow, edit `golden/*`+`*.env`→deny) | unit | `uv run pytest tools/harness_perms/tests/test_resolver.py -x` | ❌ W0 |
| AGENT-01..05 | each agent frontmatter valid (description non-empty routing signal, mode/permission valid) | structural | `uv run pytest tools/harness_lint/tests/test_agents.py -x` | ❌ W0 |
| AGENT-04 | code-reviewer read-only in BOTH representations (`tools:` allowlist + `permission:` — no edit/bash/write) | structural | same file | ❌ W0 |
| CMD-01..09 | each command frontmatter valid; description carries a routing trigger | structural | `uv run pytest tools/harness_lint/tests/test_commands.py -x` | ❌ W0 |
| CMD-03 | `/golden-approve` refuses w/o human token/adr | unit | `uv run pytest tools/golden_runner/tests/test_approve_gate.py -x` | ✅ exists (Phase 1) |
| CMD-06 | `/strangler-step` scaffold refuses w/o captured legacy golden baseline (non-zero exit) | unit | `uv run pytest tools/harness_lint/tests/test_strangler_refusal.py -x` | ❌ W0 |
| CMD-08 / DOCS-03 | `/docs-sync` delete+regenerate byte-identical; writes ONLY `docs/reference/` | integration+snapshot | `uv run pytest tools/docs_sync/tests/test_docs_sync_determinism.py -x` | ❌ W0 |
| SKILL-01/02 | each SKILL.md: name≤64 + regex + dir-match; desc≤1024 non-empty; body <~500 lines (warn) | structural | `uv run pytest tools/harness_lint/tests/test_skills.py -x` | ❌ W0 |

*Status: ⬜ pending · ✅ green · ❌ red*

---

## Wave 0 Requirements

- [ ] `tools/harness_perms/resolver.py` + tests — CONFIG-02 last-wins glob (stdlib `fnmatch`), default-deny, path denies (`contracts/**`,`golden/**`,`*.env`); reused by Phase-4 hooks
- [ ] `tools/docs_sync/generate.py` + determinism test — CMD-08/DOCS-03 (schema-JSON-only MVP, reference-only, syrupy snapshot cloning `contracts_index.py`)
- [ ] `tools/harness_lint/frontmatter.py` (shared YAML frontmatter parser) + tests for opencode.json / agents / commands / skills
- [ ] `tools/harness_lint/tests/test_strangler_refusal.py` — CMD-06 refusal
- [ ] `harness/opencode.config.schema.json` — vendored subset schema for the hermetic structural test
- [ ] `pyproject.toml` for each new `tools/*` uv member (workspace requirement; run `uv sync --all-packages`)
- [ ] Framework install: none (pytest/syrupy already locked)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| opencode actually loads agents/commands/skills; permission matrix enforces at runtime | CONFIG/AGENT/CMD/SKILL | opencode runtime absent (D-02) — surface authored-only | Deferred — verify when opencode is installed (Phase 6 emitter / opencode setup). Structural + resolver logic ARE automated. |
| `/build`/`/test` dotnet path executes | CMD-01 | .NET egress-blocked | Deferred — script must skip/announce gracefully when dotnet absent; Python path tested |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 40s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
