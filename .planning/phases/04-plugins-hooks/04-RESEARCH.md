# Phase 4: Plugins + Hooks - Research

**Researched:** 2026-07-08
**Domain:** Runtime enforcement layer — Claude Code hooks (`.claude/settings.json` PreToolUse/PostToolUse/Stop) wiring reusable pure-Python enforcement logic + authored-only opencode plugin stubs
**Confidence:** HIGH for Claude Code hook mechanics, reuse-asset APIs, and the enforcement-logic design (all verified in-repo + against current Claude Code hooks docs). MEDIUM for opencode plugin hook names (opencode.ai 403s; deferred/authored-only anyway).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Implement enforcement logic as **reusable Python**, wired via **Claude hooks** (`.claude/settings.json` PreToolUse/PostToolUse/Stop) so it **runs and is unit-tested in this dev env**. **opencode plugins** (`harness/plugins/*.ts`: `tool.execute.before/after`) are **authored as stubs wrapping the same Python logic, execution-validation deferred** (no opencode runtime; mirrors the .NET/opencode deferral pattern). Both runtimes share one enforcement contract.
- **D-02:** Hooks **reuse** the 03-01 permission resolver (`tools/harness_perms`) and the Phase-1 normalization core (`libs/python/normalize`) — **no re-implementation** (success criterion "built once").
- **D-03 (POLY-01):** `tools/polyglot_lint/` — encode the `integration_contracts §4.3–4.6` checklist (encoding·BOM·LF·TSV-escape·timezone·decimal/locale·null-vs-empty·write-atomicity·identifier/interval) as **executable rules**. Reuse the normalization core, run **on-write (hook) + in-session (command/CI)**, **fail loud**, prove violation detection with unit tests.
- **D-04 (HOOK-04) contract-guard:** PreToolUse hook — **block/ask** writes to `contracts/`·`docs/adr/`·`golden/` (constitution plane) **without an approval path** (reuse the 03-01 resolver path-deny), plus on-write encoding/TSV enforcement. Success criterion 1.
- **D-05 (HOOK-01 · HOOK-02):** format-on-write = PostToolUse — LF / no-BOM / InvariantCulture (language-neutral Python; Python via `ruff format`; **`dotnet-format` is .NET-gated → skip gracefully when dotnet absent**). secret protection = PreToolUse deny-list + pattern scan (blocks read/write). Success criterion 3.
- **D-06 (HOOK-03) commit-gate:** Stop/pre-commit hook composing **contract-drift (01-05) + golden-parity (01-06, .NET-gated skip) + polyglot-lint (POLY-01)** — block commit on failure. Plus the success-criterion-4 **permission-matrix order-resolution suite** (extend 03-01 resolver tests: last-wins · default-deny · constitution-plane edit deny).

### Claude's Discretion

- Hook script details · directory naming · secret pattern list · plugin stub shape · exact linter rule implementation are **planner/researcher discretion**. **Fixed:** logic-reuse (resolver · normalize core) · dual-runtime (Claude live / opencode deferred) · fail-loud · constitution-plane blocking.

### Deferred Ideas (OUT OF SCOPE)

- opencode plugin runtime execution → after opencode install.
- commit-gate golden-parity **execution** → after .NET policy opens (author the composition + skip-gracefully now).
- No scope creep identified.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **HOOK-01** | format-on-write — auto-format on edit; LF/encoding enforcement point | §format-on-write: PostToolUse hook reads `tool_input.file_path`, applies `normalize_tsv`-style byte fixes (strip BOM, CRLF→LF), then `ruff format` for `.py` (gated), `dotnet format` gated-skip for `.cs`. Idempotent; ordered after linter so it fixes rather than fights. |
| **HOOK-02** | secret protection — block secret read/write (deny-list + pattern scan) | §secret: PreToolUse(Read\|Write\|Edit) — path deny-list via resolver `path_deny_globs` (`*.env`) + a regex pattern set (AWS keys, private-key PEM headers, generic high-entropy tokens) scanning `tool_input.content`/target path. Deny via `permissionDecision:"deny"`. |
| **HOOK-03** | commit gate — block commit when contract-drift / golden-parity / polyglot-lint fail | §commit-gate: recommend **both** a PreToolUse(Bash)`git commit` gate (live in this env, testable) AND an authored `.git/hooks/pre-commit` shim; composes `tools.contract_drift.drift` + `tools.golden_runner` (dotnet-skip) + `tools.polyglot_lint`. Non-zero → block. Plus resolver order-resolution suite. |
| **HOOK-04** | contract-guard — block constitution/golden writes without approval; on-write encoding/TSV | §contract-guard: PreToolUse(Write\|Edit) — `resolve_path(matrix["path_deny_globs"], file_path)=="deny"` → `permissionDecision:"deny"` unless approval token present; then run polyglot on-write rules on the payload. |
| **POLY-01** | polyglot boundary linter — §4.3–4.6 checklist as executable on-write + CI rules, sharing the Phase-1 normalization core | §polyglot-linter: `tools/polyglot_lint/lint.py` with `lint_bytes(raw)` / `lint_tsv(text)` / `lint_file(path)` → `list[Violation]`. Detects BOM/CRLF/decimal-locale/non-UTC-datetime/null-vs-empty/TSV-column-shift by comparing raw vs `normalize.core` output. CLI exit 1 on any violation. |
</phase_requirements>

## Summary

Phase 4 turns the advisory prose of Phases 1–3 into **non-bypassable runtime enforcement**. The mechanism in this dev environment is Claude Code hooks: `.claude/settings.json` already carries live `SessionStart`/`PreToolUse`/`PostToolUse` slots (GSD's own), and this phase **appends new slots that coexist** with them. Each new hook is a thin adapter (bash or node reading stdin JSON) that shells into a **pure, unit-tested Python module** under `tools/`. The Python modules are the real product; the hook wiring is a runtime envelope. The identical modules are wrapped a second time by authored-only opencode TS plugin stubs (`harness/plugins/*.ts`) that are **not executed here** (no opencode runtime) — the single enforcement contract both runtimes honor is "shell into `python -m tools.<gate>`".

Every gate **reuses existing built-once assets** (D-02): the permission resolver `tools.harness_perms` (`resolve_path`, `resolve_bash`, `load_matrix`) and the normalization core `normalize.core` (`normalize_tsv`, `normalize_cell`, `DEFAULT_NULL_TOKEN`, `NULL_SENTINEL`). The polyglot linter detects violations by **normalizing a copy and diffing against the raw** — if `normalize_tsv(raw)` differs from a straight UTF-8/LF decode of `raw`, the raw violated a §4.3–4.6 convention. No new external packages are introduced; everything is stdlib + already-pinned `ruff`. The five gates follow the established repo idiom exactly (pure core function + `main(argv)` CLI + `if __name__=="__main__": raise SystemExit(main())`, `REPO_ROOT=parents[2]`, `subprocess.run([list], shell=False)`, refusal→exit 3 / failure→exit 1, `pyproject.toml package=false` uv workspace member with a `tests/` dir).

**Primary recommendation:** Build five pure Python modules (`tools/polyglot_lint`, `tools/hooks/contract_guard`, `tools/hooks/secret_scan`, `tools/hooks/format_on_write`, `tools/hooks/commit_gate`) + one shared thin stdin adapter, unit-test each against crafted inputs, wire them as **additional** `.claude/settings.json` slots, extend the 03-01 resolver test suite for order-resolution, and author (do not run) the matching `harness/plugins/*.ts` stubs. Use the current Claude Code hook contract: PreToolUse denies via exit-0 JSON `hookSpecificOutput.permissionDecision:"deny"` (with exit-2/stderr as the loud fallback); PostToolUse/Stop block via top-level `{"decision":"block","reason":…}` + exit 2.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Block writes to constitution plane (HOOK-04) | Enforcement logic (`tools/hooks/contract_guard`, pure Python) | Runtime hook (Claude PreToolUse; opencode `tool.execute.before`) | Decision must be identical across runtimes → lives in shared Python; the hook is only the envelope that maps the decision to each runtime's block protocol. |
| §4.3–4.6 boundary rules (POLY-01) | Enforcement logic (`tools/polyglot_lint`, reuses `normalize.core`) | Runtime hook (PostToolUse/PreToolUse) + CI (Phase 5) | Rules are language-neutral data-format invariants; must run identically on-write, in-session, and in CI — one implementation, three call sites. |
| Encoding/format fixing (HOOK-01) | Enforcement logic (byte fixer) + external formatter (`ruff`, `dotnet format`) | Runtime hook (PostToolUse `tool.execute.after`) | Formatting is a post-write mutation; the byte-level LF/BOM/culture fix is language-neutral Python, the language formatter is an optional gated add-on. |
| Secret detection (HOOK-02) | Enforcement logic (`tools/hooks/secret_scan`, reuses resolver path-deny) | Runtime hook (PreToolUse) | Must intercept **before** the tool executes (read or write) → PreToolUse deny is the only correct tier; detection logic is shared Python. |
| Commit gate composition (HOOK-03) | Enforcement logic (`tools/hooks/commit_gate` composing drift+golden+lint) | Runtime hook (Claude PreToolUse-Bash / Stop) **and** git `pre-commit` (VCS tier) | Two enforcement surfaces (in-session vs VCS) share one composed implementation; git pre-commit is the non-bypassable-by-model surface, the Claude hook is the fast in-session surface. |
| Permission order-resolution proof (crit. 4) | Test tier (extend `tools/harness_perms/tests`) | — | It is a proof-of-behavior over existing data + resolver; no new runtime component, just a test suite. |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (`fnmatch`, `pathlib`, `codecs`, `decimal`, `datetime`, `re`, `subprocess`, `json`, `argparse`) | 3.11+ | All enforcement logic | Every existing gate in this repo is stdlib-only (resolver, drift, golden, strangler_guard). `[VERIFIED: in-repo grep — resolver.py/drift.py/normalize/core.py]` |
| `tools.harness_perms` (in-repo) | 0.0.0 | `resolve_path`, `resolve_bash`, `load_matrix` — path-deny + last-wins bash | D-02 mandated reuse; signatures explicitly frozen for Phase-4 hooks (docstring says so). `[VERIFIED: tools/harness_perms/resolver.py]` |
| `normalize.core` (in-repo, `libs/python/normalize`) | — | `normalize_tsv(raw:bytes)->str`, `normalize_cell(value,kind,null_token)->str`, `DEFAULT_NULL_TOKEN="\\N"`, `NULL_SENTINEL="<NULL>"` | D-02/D-03 mandated reuse; the §4.3–4.6 canonicalizer the linter must share. `[VERIFIED: libs/python/normalize/core.py]` |
| `ruff` | `~=0.15` (pinned in root `pyproject.toml` dev group) | `ruff format` for Python files in HOOK-01 | Already the project formatter (CLAUDE.md, root pyproject). No new dep. `[VERIFIED: pyproject.toml dev group]` |
| Node.js | 22 (`/opt/node22/bin/node`) | Optional stdin-JSON adapter for hooks (parity with existing GSD hooks) | Existing GSD hooks use `/opt/node22/bin/node` for JSON parsing; bash+node is the in-repo hook idiom. `[VERIFIED: .claude/settings.json]` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `tools.contract_drift.drift` (in-repo) | — | `run_gate()` → `{"ok":bool,"drifted":[...]}`; `main()` exits 0/1 | commit-gate composition (HOOK-03). `[VERIFIED: tools/contract_drift/drift.py]` |
| `tools.golden_runner.runner` (in-repo) | — | golden parity via normalized compare; spawns .NET toy converter | commit-gate composition — **wrap in dotnet-presence check, skip gracefully** (D-05/D-06). `[VERIFIED: tools/golden_runner/runner.py]` |
| `dotnet format` | .NET 10 SDK | HOOK-01 .NET formatting | **Gated** — only when `$DOTNET_ROOT/dotnet` resolves; skip-gracefully otherwise (env has no .NET egress). `[CITED: CLAUDE.md installation notes]` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| bash+node stdin adapter | pure-bash `jq` parsing | Repo has **no `jq`** (gsd-validate-commit.sh explicitly notes "no jq dependency", uses node). Node is present and already the idiom. Prefer node or a tiny Python adapter. |
| PreToolUse exit-0 JSON `permissionDecision:"deny"` | exit-2 + stderr | Both block. Exit-0-JSON gives a structured `permissionDecisionReason` and is the current documented form; exit-2 is the loud fallback. Use JSON primary, keep exit-2 for hard errors. `[CITED: code.claude.com/docs/en/hooks]` |
| Claude Stop-hook commit gate | git `pre-commit` hook | Stop hooks fire at turn-end, not at commit-time, and can loop; a `git commit` PreToolUse-Bash matcher is the precise in-session interception (precedent: gsd-validate-commit.sh). Recommend PreToolUse-Bash + authored git pre-commit; Stop hook optional. |
| detect-secrets / gitleaks (external) | — | Adds an external dependency + registry-legitimacy surface for marginal benefit at this scope. A curated stdlib `re` pattern set covers the required cases and stays stdlib-only. Revisit in Phase 5 CI if needed. |

**Installation:**
```bash
# No new external packages. All gates are stdlib + already-pinned ruff.
# New tool modules are uv workspace members (package=false), picked up by existing `uv sync`.
```

**Version verification:** No new packages to verify against a registry — Phase 4 introduces zero third-party dependencies. `ruff ~=0.15` is already resolved in `uv.lock` (root pyproject dev group). `[VERIFIED: pyproject.toml]`

## Package Legitimacy Audit

> No external packages are installed by this phase. All enforcement modules are Python-stdlib-only and reuse in-repo assets; the only formatter (`ruff`) is already pinned and locked from Phase 1.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| _(none — no new external packages)_ | — | — | — | — | n/a | — |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*No install step → slopcheck not applicable. If a future revision adds `detect-secrets`/`gitleaks`, run the Package Legitimacy Gate before adopting.*

## Architecture Patterns

### System Architecture Diagram

```
                       Claude Code runtime (LIVE here)              opencode runtime (DEFERRED)
                       .claude/settings.json hooks                 harness/plugins/*.ts (authored only)
                              │                                            │
   tool call ────────────────┤                                            │  tool.execute.before/after
   (Write/Edit/Read/Bash)    │                                            │  (same shell contract, NOT run)
                             ▼                                            ▼
        ┌──────────────────────────────────────────────────────────────────────────────┐
        │  THIN STDIN ADAPTER  (bash+node OR python -m)                                  │
        │  reads {tool_name, tool_input.{file_path,content,command}, session_id, cwd}    │
        └──────────────────────────────────────────────────────────────────────────────┘
             │ PreToolUse            │ PreToolUse           │ PostToolUse        │ PreToolUse-Bash(git commit) / Stop
             ▼                       ▼                      ▼                    ▼
   ┌─────────────────┐   ┌──────────────────┐   ┌──────────────────┐   ┌───────────────────────────┐
   │ contract_guard  │   │ secret_scan      │   │ format_on_write  │   │ commit_gate               │
   │ (HOOK-04)       │   │ (HOOK-02)        │   │ (HOOK-01)        │   │ (HOOK-03)                 │
   └────────┬────────┘   └────────┬─────────┘   └────────┬─────────┘   └────────────┬──────────────┘
            │ resolve_path         │ resolve_path +        │ byte-fix +              │ composes ↓
            │ + polyglot on-write  │ regex pattern scan    │ ruff/dotnet(gated)      │
            ▼                      ▼                       ▼                         ▼
   ┌──────────────────────────────────────────┐   ┌───────────────┐   ┌──────────────────────────────┐
   │ REUSED BUILT-ONCE ASSETS (D-02)          │   │ ruff format   │   │ contract_drift.run_gate()    │
   │ tools.harness_perms: resolve_path/bash   │   │ dotnet format │   │ golden_runner (dotnet-SKIP)  │
   │ normalize.core: normalize_tsv/_cell      │   │  (GATED)      │   │ polyglot_lint.lint_file()    │
   └──────────────────────────────────────────┘   └───────────────┘   │ + resolver order-res. suite  │
                     ▲                                                 └──────────────────────────────┘
                     │ shared §4.3–4.6 rule
            ┌────────┴─────────┐
            │ tools/polyglot_lint (POLY-01): lint_bytes/lint_tsv/lint_file → [Violation]  │
            └───────────────────────────────────────────────────────────────────────────┘

  DECISION → RUNTIME MAP:  block = Claude PreToolUse exit-0 JSON permissionDecision:"deny"
                                   (fallback exit 2 + stderr) ;  PostToolUse/Stop = {"decision":"block"} + exit 2
                                   opencode = tool.execute.before throw/deny (authored, not run)
```

### Recommended Project Structure

```
tools/
├── polyglot_lint/              # POLY-01 (D-03) — the shared §4.3–4.6 rule engine
│   ├── __init__.py             #   lazy re-export (mirror harness_perms __init__ PEP 562)
│   ├── lint.py                 #   lint_bytes/lint_tsv/lint_file → [Violation]; main(argv) exit 0/1
│   ├── pyproject.toml          #   package=false, deps=[] (reuses normalize via sys.path like golden_runner)
│   └── tests/test_lint.py      #   each rule: catches its violation + passes clean input
├── hooks/                      # NEW: Phase-4 enforcement modules (one dir, sibling gates)
│   ├── __init__.py
│   ├── _stdin.py               #   shared: parse Claude hook stdin JSON → dataclass; emit decision JSON
│   ├── contract_guard.py       #   HOOK-04: resolve_path deny + approval-token bypass + polyglot on-write
│   ├── secret_scan.py          #   HOOK-02: resolve_path(*.env) + PATTERNS regex scan
│   ├── format_on_write.py      #   HOOK-01: byte-fix (BOM/LF/culture) + ruff/dotnet gated
│   ├── commit_gate.py          #   HOOK-03: compose drift + golden(dotnet-skip) + polyglot_lint
│   ├── pyproject.toml
│   └── tests/                  #   crafted-stdin tests per gate (exit code + decision assertions)
├── harness_perms/tests/
│   └── test_order_resolution.py  # crit.4 suite (extend): last-wins · default-deny · constitution deny
harness/plugins/                # authored-only, DEFERRED (mirror session-inject.ts resume-note banner)
├── contract-guard.ts           #   tool.execute.before → shell `python -m tools.hooks.contract_guard`
├── secret-scan.ts              #   tool.execute.before
├── format-on-write.ts          #   tool.execute.after
└── polyglot-lint.ts            #   tool.execute.after (or before, on write payload)
.claude/settings.json           # APPEND new PreToolUse/PostToolUse/Stop slots (coexist w/ GSD slots)
.git/hooks/pre-commit           # authored shim → `uv run python -m tools.hooks.commit_gate`
```

### Pattern 1: Pure core + thin CLI + thin hook adapter (three-layer, in-repo idiom)

**What:** Each gate is a pure importable function (testable with crafted inputs, no I/O beyond reading the target), a `main(argv)->int` CLI wrapper, and — separately — a stdin adapter that maps Claude's hook JSON to a call + maps the return to Claude's decision JSON.
**When to use:** Every gate. It is exactly how `drift.py`, `runner.py`, `approve.py`, `guard.py` are already built.
**Example (structure to mirror — verified against `tools/strangler_guard/guard.py`):**
```python
# Source: in-repo idiom — tools/contract_drift/drift.py, tools/strangler_guard/guard.py
from __future__ import annotations
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[2]  # tools/<pkg>/x.py -> repo root

def check(...) -> Result:            # pure, unit-tested
    ...

def main(argv: list[str] | None = None) -> int:   # CLI: exit 0 ok / 1 fail (3 = refusal, established)
    ...

if __name__ == "__main__":
    raise SystemExit(main())
```

### Pattern 2: PreToolUse deny via structured JSON (with exit-2 loud fallback)

**What:** A blocking PreToolUse hook prints exit-0 JSON to stdout and exits 0; the runtime reads `permissionDecision`.
**When to use:** contract-guard, secret (both must stop the tool *before* execution).
**Example:**
```jsonc
// Source: code.claude.com/docs/en/hooks (verified 2026-07-08)
// stdout on exit 0:
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",              // "deny" | "ask" | "allow" | "defer"
    "permissionDecisionReason": "contract-guard: contracts/** is the constitution plane; gated by /golden-approve + CODEOWNERS."
  }
}
// Loud fallback for a hard error: write reason to stderr and `exit 2`.
```
**stdin the hook receives (verified fields):**
```jsonc
{ "session_id":"…", "hook_event_name":"PreToolUse", "cwd":"…",
  "tool_name":"Write",
  "tool_input": { "file_path":"contracts/x.schema.json", "content":"…" } }   // Bash → tool_input.command; Edit → file_path + old/new_string
```

### Pattern 3: PostToolUse / Stop block via top-level decision

**What:** PostToolUse (format-on-write does *not* block — it mutates & informs; commit-gate variant on Stop *does* block) and Stop hooks use the top-level `{"decision":"block","reason":…}` shape.
**Example:**
```jsonc
// Source: code.claude.com/docs/en/hooks
{ "decision": "block", "reason": "commit-gate: contract-drift detected (2 breaking). Fix or /golden-approve before committing." }
// exit 2 also blocks; `{"continue": false, "stopReason": …}` hard-stops the whole turn.
```

### Pattern 4: Coexist with existing hooks (append, never replace)

**What:** `.claude/settings.json` `PreToolUse`/`PostToolUse` are **arrays**; add new `{matcher, hooks:[…]}` objects. `SessionStart` already has 4 slots; `Stop` is a new top-level array. All matching hooks run; the runtime aggregates decisions (any deny wins).
**When to use:** All wiring. Do **not** rewrite the file wholesale — merge.
**Anti-pattern:** replacing the array (drops GSD's guards). Verified: existing `PreToolUse` has 4 objects (Write|Edit ×3, Bash ×1), `PostToolUse` has 3.

### Pattern 5: Detection-by-normalization (POLY-01 core trick)

**What:** The normalize core *transforms*; a *linter* must *detect*. Detect a violation by normalizing a copy and observing whether it changed relative to a naive decode. BOM present ⇔ `raw[:3]==b"\xef\xbb\xbf"`; CRLF present ⇔ `b"\r" in raw`; decimal/datetime/null violations ⇔ `normalize_cell(cell,kind) != cell` for a cell that should already be canonical; TSV column-shift ⇔ inconsistent tab counts across rows.
**When to use:** POLY-01 linter. Reuses `normalize.core` for the canonical target (no re-implementation, D-03).

### Anti-Patterns to Avoid

- **Re-implementing normalization inside the linter:** violates D-02/D-03 "built once." Import `normalize.core`; the linter only *diffs* raw vs canonical.
- **Ending the permission matrix with a broad `allow`:** Pitfall P3. The order-resolution suite must prove no trailing catch-all allow shadows a deny.
- **Trusting prose:** Pitfall P8/P11 — non-negotiables (constitution deny, §4.3–4.6) must be a *hook*, not an AGENTS.md sentence. That is the entire premise of this phase.
- **`subprocess` with `shell=True` / string commands:** repo rule (T-02-04/T-03-04). Always `subprocess.run([list], shell=False)`; the golden_runner uses an explicit absolute dotnet path, not a PATH lookup.
- **Blocking session start / turns on a missing gated toolchain:** golden-parity and dotnet-format must **skip gracefully** when .NET is absent — never fail the gate for an env limitation (D-05/D-06).
- **Hand-editing `.claude/settings.json` as a generated artifact:** here it is *authored+tested* (Phase 6 emitter will later own generation). Keep the Phase-4 additions minimal and mirror them into `harness/` source so Phase 6 can emit them.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| §4.3–4.6 canonicalization | A second BOM/decimal/timezone normalizer in the linter | `normalize.core.normalize_tsv` / `normalize_cell` | D-02 "built once"; a divergent copy re-introduces the exact polyglot drift the harness exists to prevent (P4/P14). |
| Path deny / last-wins bash resolution | New glob matcher in each hook | `tools.harness_perms.resolve_path` / `resolve_bash` / `load_matrix` | Signatures are frozen for Phase-4 reuse; the matrix data (`path_deny_globs`, `bash`) is the single source. |
| Contract drift detection | Re-hashing schemas in commit-gate | `tools.contract_drift.drift.run_gate()` | Already computes JCS SHA-256 manifest + breaking classification incl. §4-5 conventions. |
| Golden equivalence | Byte-diff in commit-gate | `tools.golden_runner.runner` (normalized compare) | Byte-diff is Pitfall P4 (false reds on BOM/CRLF/locale). Runner already normalizes. |
| Human-approval token gate | New env-var scheme | Reuse the `GOLDEN_APPROVE_HUMAN` precedent for contract-guard's "approval path" | One consistent "agent-can't-fabricate" token mechanism (see Open Question Q1). |
| Decimal formatting / BOM detection / TZ math | `float()` round-trips, manual byte slicing | stdlib `decimal.Decimal`, `codecs`/`utf-8-sig`, `datetime` (already used in `normalize.core`) | Deceptively complex; last-digit float diffs and BOM off-by-one are the classic bugs. |
| JSON stdin parsing in bash | `jq` | node (`/opt/node22/bin/node`) or `python -c` | Repo has no `jq`; existing hooks use node explicitly for this reason. |

**Key insight:** Phase 4 is almost entirely *composition* of Phase-1/3 assets behind runtime triggers. The net-new code is (a) the POLY-01 rule engine (thin, over `normalize.core`), (b) the secret regex set, (c) the stdin adapters, (d) the composition/skip logic in commit-gate. Everything else is a function call into a built-once module.

## Runtime State Inventory

> Not a rename/refactor/migration phase (net-new enforcement modules + hook wiring). Section included for the one relevant category: existing runtime hook registrations that Phase-4 additions must **coexist** with, since a naive rewrite would silently drop them.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no datastore keys/collections involved. Verified: gates operate on files + git, no DB. | none |
| Live service config (hook registrations) | `.claude/settings.json` currently registers: SessionStart ×4 (gsd-check-update, gsd-session-state, bootstrap install, memory-inject), PostToolUse ×3 (context-monitor `Bash\|Edit\|Write\|MultiEdit\|Agent\|Task`, read-injection-scanner `Read`, phase-boundary `Write\|Edit`), PreToolUse ×4 (prompt-guard, read-guard, workflow-guard all `Write\|Edit`, validate-commit `Bash`). No `Stop` array yet. | **APPEND** new slots to PreToolUse/PostToolUse arrays; **ADD** a new `Stop` array. Never replace existing objects. |
| OS-registered state | None — no Task Scheduler / systemd / pm2. `.git/hooks/` currently holds only `.sample` files (no active pre-commit). | commit-gate may **add** `.git/hooks/pre-commit` (net-new, no collision). |
| Secrets/env vars | `GOLDEN_APPROVE_HUMAN` (existing, golden_runner approval token). Phase-4 contract-guard should reuse/parallel it rather than invent a new name. `path_deny_globs` includes `*.env`/`**/*.env`. | Decide approval-token name (Open Q1); no key rotation needed. |
| Build artifacts | New uv workspace members (`tools/polyglot_lint`, `tools/hooks`) — picked up by `members=["tools/*"]` glob in root pyproject. Each needs a `pyproject.toml` (`package=false`) or `uv sync` fails (root pyproject note). | Add `pyproject.toml` per new tool dir; run `uv sync` after. |

## Common Pitfalls

### Pitfall 1: Rewriting `.claude/settings.json` and dropping GSD's guards
**What goes wrong:** Replacing the PreToolUse/PostToolUse arrays wipes gsd-prompt-guard / read-guard / workflow-guard / validate-commit / context-monitor / phase-boundary.
**Why it happens:** JSON merge is manual; the arrays look replaceable.
**How to avoid:** Read the current file, append objects to existing arrays, add a new `Stop` array. Assert (test) that the pre-existing GSD hook commands are still present after edit.
**Warning signs:** GSD workflow enforcement or commit validation stops firing after Phase 4.

### Pitfall 2: The linter re-implements normalization and drifts from the core
**What goes wrong:** A second decimal/BOM/TZ implementation in `polyglot_lint` diverges from `normalize.core`; golden runner and linter disagree on what "canonical" means (P14).
**How to avoid:** Import `normalize.core`; detect by diffing raw vs its output. Add a test that the linter's notion of canonical == `normalize_tsv`/`normalize_cell` output on the shared fixture corpus (`libs/normalize-fixtures/*.json`).
**Warning signs:** A file passes the linter but the golden runner flags a representation diff (or vice-versa).

### Pitfall 3: Gate fails because .NET/opencode is absent (env limitation ≠ policy violation)
**What goes wrong:** commit-gate exits non-zero because `dotnet` isn't installed, blocking every commit; or a test tries to run the opencode plugin.
**How to avoid:** Probe `$DOTNET_ROOT/dotnet` / `$HOME/.dotnet/dotnet` (the golden_runner's explicit-path pattern) and **skip golden-parity + dotnet-format with a logged SKIP** when absent (D-05/D-06). opencode `.ts` stubs carry the session-inject resume-note banner and are never executed here.
**Warning signs:** "dotnet: command not found" turns a green tree red; CI-only failures that don't reproduce.

### Pitfall 4: PreToolUse decision shape mismatch (block silently ignored)
**What goes wrong:** Emitting the legacy `{"decision":"block"}` for a *PreToolUse* event (that top-level shape is PostToolUse/Stop) — the tool proceeds.
**How to avoid:** PreToolUse → `hookSpecificOutput.permissionDecision:"deny"` (exit 0) **or** exit 2 + stderr. PostToolUse/Stop → top-level `{"decision":"block"}`. Test each hook by feeding crafted stdin and asserting the exact emitted JSON + exit code.
**Warning signs:** A contract-guard "deny" prints but the write still happens.

### Pitfall 5: Secret scanner false-positives on the repo's own fixtures / high-entropy test data
**What goes wrong:** Regex for "high-entropy token" flags golden fixtures, base64 in `normalize-fixtures`, or the `GOLDEN_APPROVE_HUMAN` value in tests, blocking legitimate edits.
**How to avoid:** Anchor patterns to known secret *shapes* (AWS `AKIA[0-9A-Z]{16}`, PEM `-----BEGIN … PRIVATE KEY-----`, `*.env` path deny) rather than generic entropy; allow-list `tests/`, `libs/normalize-fixtures/`, `golden/**` sample data. Unit-test both a true secret (blocked) and a benign high-entropy fixture (allowed).
**Warning signs:** Editing a test file triggers a secret block.

### Pitfall 6: Commit-gate as a Stop hook loops or fires at the wrong time
**What goes wrong:** A Stop hook that blocks "until gates pass" can loop the model; it also fires at turn-end, not commit-time, so it gates *turns* not *commits*.
**How to avoid:** Primary surface = PreToolUse matcher `Bash` intercepting `git commit` (precedent: gsd-validate-commit.sh classifies git subcommands via token-walk, not naive regex) + authored `.git/hooks/pre-commit`. Reserve Stop for advisory `additionalContext` only.
**Warning signs:** Model stuck re-attempting; gate blocks unrelated turns.

## Code Examples

### POLY-01: detection by normalization (reusing the core)
```python
# Source: derived from libs/python/normalize/core.py (normalize_tsv / normalize_cell) — in-repo
from __future__ import annotations
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_LIBS = REPO_ROOT / "libs" / "python"
if str(_LIBS) not in sys.path:            # same sys.path shim golden_runner uses
    sys.path.insert(0, str(_LIBS))
from normalize.core import normalize_cell, normalize_tsv, DEFAULT_NULL_TOKEN  # noqa: E402

@dataclass(frozen=True)
class Violation:
    rule: str        # "R1-BOM" | "R2-CRLF" | "R3-decimal" | "R5-datetime" | "R6-null" | "R7-tsv" ...
    detail: str

def lint_bytes(raw: bytes) -> list[Violation]:
    v: list[Violation] = []
    if raw.startswith(b"\xef\xbb\xbf"):
        v.append(Violation("R1-BOM", "UTF-8 BOM present; §4.3 forbids BOM."))
    if b"\r" in raw:
        v.append(Violation("R2-CRLF", "CR byte present; §4.3 requires LF."))
    return v

def lint_tsv(text: str, kinds: list[str] | None = None) -> list[Violation]:
    v: list[Violation] = []
    rows = [r for r in text.split("\n") if r != ""]
    widths = {r.count("\t") for r in rows}
    if len(widths) > 1:
        v.append(Violation("R7-tsv", f"inconsistent column count across rows: {sorted(widths)}"))
    if kinds:
        for r in rows:
            for cell, kind in zip(r.split("\t"), kinds):
                if kind in ("decimal", "datetime") and normalize_cell(cell, kind, DEFAULT_NULL_TOKEN) != cell:
                    v.append(Violation(f"R-{kind}", f"non-canonical {kind}: {cell!r}"))
    return v

def lint_file(path: str | Path, kinds: list[str] | None = None) -> list[Violation]:
    raw = Path(path).read_bytes()
    out = lint_bytes(raw)
    out += lint_tsv(normalize_tsv(raw), kinds)   # normalize_tsv strips BOM/CRLF so tsv checks see clean text
    return out

def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="POLY-01 polyglot §4.3-4.6 boundary linter")
    ap.add_argument("path"); ap.add_argument("--kinds", nargs="*")
    a = ap.parse_args(argv)
    vio = lint_file(a.path, a.kinds)
    if not vio:
        print(f"polyglot-lint: OK — {a.path}")
        return 0
    for x in vio:
        print(f"polyglot-lint: FAIL [{x.rule}] {x.detail}", file=sys.stderr)
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
```

### HOOK-04 contract-guard: reuse resolver, deny with the current PreToolUse shape
```python
# Source: reuses tools.harness_perms (in-repo) + code.claude.com/docs/en/hooks decision shape
import json, os, sys
from tools.harness_perms import load_matrix, resolve_path

APPROVAL_ENV = "GOLDEN_APPROVE_HUMAN"   # reuse existing token (Open Q1)

def decide(file_path: str, approved: bool) -> dict | None:
    matrix = load_matrix()
    if resolve_path(matrix["path_deny_globs"], file_path) == "deny" and not approved:
        return {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"contract-guard: {file_path} is the constitution plane "
                "(contracts/ · docs/adr/ · golden/). Gated by /golden-approve + CODEOWNERS."
            )}}
    return None   # no decision → normal permission flow

def main() -> int:
    data = json.load(sys.stdin)
    fp = (data.get("tool_input") or {}).get("file_path", "")
    approved = bool(os.environ.get(APPROVAL_ENV))   # presence = human-authorized session
    out = decide(fp, approved) if fp else None
    if out:
        print(json.dumps(out)); return 0            # exit 0 + JSON deny
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

### `.claude/settings.json` append (coexist — merge, do not replace)
```jsonc
// Add to the EXISTING "PreToolUse" array (alongside the 4 GSD objects):
{ "matcher": "Write|Edit",
  "hooks": [{ "type": "command",
    "command": "uv run python -m tools.hooks.contract_guard", "timeout": 10 }] },
{ "matcher": "Read|Write|Edit",
  "hooks": [{ "type": "command",
    "command": "uv run python -m tools.hooks.secret_scan", "timeout": 10 }] },
{ "matcher": "Bash",
  "hooks": [{ "type": "command",
    "command": "uv run python -m tools.hooks.commit_gate --from-hook", "timeout": 120 }] }
// Add to the EXISTING "PostToolUse" array:
// { "matcher": "Write|Edit", "hooks": [{ "type":"command",
//    "command":"uv run python -m tools.hooks.format_on_write", "timeout": 30 }] }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PreToolUse block via `{"decision":"block"}` | `hookSpecificOutput.permissionDecision:"deny"|"ask"|"allow"` (+ `permissionDecisionReason`); legacy `decision:"deny"` still accepted | Claude Code hooks schema (current, 2026) | Use the `permissionDecision` shape for PreToolUse; keep exit-2/stderr as the loud fallback. `[CITED: code.claude.com/docs/en/hooks]` |
| Hook stdin varied | Stable common fields `session_id`, `hook_event_name`, `cwd`, `tool_name`, `tool_input`, `transcript_path`, `permission_mode` | current | Adapters can rely on `tool_input.file_path` (Write/Edit) and `tool_input.command` (Bash). `[CITED: code.claude.com/docs/en/hooks]` |
| Docs at `docs.claude.com/en/docs/claude-code/hooks` | Redirects → `code.claude.com/docs/en/hooks` | 301 as of 2026-07-08 | Cite the new host. |

**Deprecated/outdated:**
- Relying solely on exit-2/stderr for PreToolUse denial: still works, but the structured `permissionDecision` carries a machine-readable reason and is the documented primary path.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | opencode plugin hook names `tool.execute.before` (deny) / `tool.execute.after` (format) are the correct guardrail seam | opencode plugin shape | LOW now — stubs are authored-only/deferred; re-verify before opencode wiring (already flagged MEDIUM in CLAUDE.md + session-inject.ts). opencode.ai 403s block direct verification. |
| A2 | The "approval path" for contract-guard should reuse the existing `GOLDEN_APPROVE_HUMAN` env token (presence = human-authorized) | contract-guard | MEDIUM — if the planner wants a distinct token or a marker-file/CODEOWNERS-note scheme, the env-presence check changes. Surfaced as Open Q1. |
| A3 | Secret pattern set = AWS access-key `AKIA[0-9A-Z]{16}`, PEM private-key headers, generic `(secret|token|api[_-]?key)\s*[:=]` + `*.env` path-deny | secret protection | MEDIUM — exact pattern list is Claude's discretion (D-05); these are conventional shapes, not verified against a project deny-list spec. Tune to avoid fixture false-positives (Pitfall 5). |
| A4 | commit-gate primary surface = PreToolUse-Bash(`git commit`) + authored `.git/hooks/pre-commit`; Stop = advisory only | commit-gate | LOW-MEDIUM — recommendation, not locked; D-06 says "Stop/pre-commit". Both are viable; the git subcommand classifier precedent (gsd-validate-commit.sh) supports the Bash-matcher choice. |
| A5 | New tool dirs auto-join the uv workspace via `members=["tools/*"]` and need a `package=false` pyproject | project structure | LOW — verified from root pyproject note ("uv requires every matched dir contain a pyproject.toml"). |

**If this table is empty:** it is not — five assumptions need planner/user confirmation, chiefly A2 (approval mechanism) and A3 (secret patterns).

## Open Questions

1. **What exactly is contract-guard's "approval path"?** (D-04 requires "without an approval path" → so an approval path must exist.)
   - What we know: `GOLDEN_APPROVE_HUMAN` env token already gates golden promotion; agents are instructed never to fabricate it. `path_deny_globs` already covers `contracts/**`, `docs/adr/**`, `golden/**`.
   - What's unclear: reuse that env token (presence-based), require a distinct per-write token, or key off a CODEOWNERS/marker signal? Env presence is simplest and consistent (A2).
   - Recommendation: reuse `GOLDEN_APPROVE_HUMAN` presence as the bypass in this env; document that CI (Phase 5) enforces the *hard* gate via CODEOWNERS. Confirm with user in discuss/plan.

2. **Exact secret pattern set + allow-list scope.**
   - What we know: `*.env` path-deny exists; test/fixture dirs contain high-entropy sample data (base64 in `normalize-fixtures`, the approval token in tests).
   - What's unclear: which patterns, and whether to allow-list `tests/`, `golden/`, `libs/normalize-fixtures/`.
   - Recommendation: shape-anchored patterns (A3) + allow-list the three fixture/test dirs; unit-test a real-secret block and a benign-fixture pass.

3. **Does format-on-write PostToolUse re-trigger PostToolUse (mutation loop)?**
   - What we know: PostToolUse fires after Write/Edit; format-on-write itself writes the file.
   - What's unclear: whether the formatter's own write re-enters the hook (Claude Code hooks fire on *tool* Write, not arbitrary FS writes by a subprocess — so a subprocess `ruff format` should not re-trigger).
   - Recommendation: format via subprocess inside the hook (not via a Claude Write tool) → no re-entry; add an idempotency test (format twice == once).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | all gates | ✓ | 3.11+ (uv workspace) | — |
| `uv` | running `uv run python -m …` in hooks | ✓ | 0.11.x (CLAUDE.md) | direct `python -m` if uv env active |
| Node.js | optional stdin adapter (parity w/ GSD hooks) | ✓ | 22 (`/opt/node22/bin/node`) | Python `_stdin.py` adapter |
| `ruff` | HOOK-01 Python format | ✓ | ~=0.15 (locked) | byte-fix only (BOM/LF) if ruff absent |
| `.NET 10 SDK` / `dotnet format` | HOOK-01 .cs format, HOOK-03 golden-parity | ✗ | — | **skip gracefully** (D-05/D-06); probe `$DOTNET_ROOT/dotnet` |
| opencode runtime | executing `harness/plugins/*.ts` | ✗ | — | authored-only/deferred (D-01) |
| `git` | commit-gate pre-commit + drift `git show` | ✓ | — (repo is a git repo) | — |
| `jq` | (not used) | ✗ | — | node / python for JSON — repo idiom |

**Missing dependencies with no fallback:** none block this phase — every .NET/opencode gap has an explicit skip-gracefully / authored-deferred path (by design, D-01/D-05/D-06).
**Missing dependencies with fallback:** .NET (golden-parity + dotnet-format skip), opencode (plugins authored not run), jq (node/python), ruff (byte-fix subset).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest `>=8.4,<9` (root pyproject dev group) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths=["libs/python","tools"]`, `minversion=8.4`) |
| Quick run command | `uv run pytest tools/polyglot_lint tools/hooks tools/harness_perms -x -q` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| POLY-01 | BOM/CRLF raw bytes → violation; clean bytes → none | unit | `uv run pytest tools/polyglot_lint/tests/test_lint.py -x` | ❌ Wave 0 |
| POLY-01 | non-canonical decimal/datetime/null cell → violation; canonical → none (shares `normalize.core`) | unit | same file | ❌ Wave 0 |
| POLY-01 | TSV column-shift (uneven tab count) → violation | unit | same file | ❌ Wave 0 |
| POLY-01 | linter's canonical == `normalize_tsv`/`normalize_cell` on `libs/normalize-fixtures/*.json` (no drift) | unit | `tools/polyglot_lint/tests/test_corpus_parity.py` | ❌ Wave 0 |
| HOOK-04 | write to `contracts/**` w/o approval → `permissionDecision:"deny"`; with token → no decision | unit | `uv run pytest tools/hooks/tests/test_contract_guard.py -x` | ❌ Wave 0 |
| HOOK-04 | source-path write (`libs/python/foo.py`) → allowed | unit | same file | ❌ Wave 0 |
| HOOK-02 | real secret (AWS key/PEM) in content or `*.env` path → deny; benign fixture → allow | unit | `uv run pytest tools/hooks/tests/test_secret_scan.py -x` | ❌ Wave 0 |
| HOOK-01 | BOM+CRLF file → LF/no-BOM after; format twice == once (idempotent) | unit | `uv run pytest tools/hooks/tests/test_format_on_write.py -x` | ❌ Wave 0 |
| HOOK-01 | dotnet absent → `.cs` path skips gracefully (no error) | unit | same file | ❌ Wave 0 |
| HOOK-03 | drift present → non-zero/block; clean → 0 | unit | `uv run pytest tools/hooks/tests/test_commit_gate.py -x` | ❌ Wave 0 |
| HOOK-03 | polyglot violation in staged file → block | unit | same file | ❌ Wave 0 |
| HOOK-03 | dotnet absent → golden-parity SKIP (not fail) | unit | same file | ❌ Wave 0 |
| Crit. 4 | last-wins: specific overrides catch-all; default-deny (`ask`) on unmatched; `rm -rf`→deny | unit | `uv run pytest tools/harness_perms/tests/test_order_resolution.py -x` | ⚠️ extend `test_resolver.py` |
| Crit. 4 | constitution-plane edit (`contracts/`/`adr/`/`golden/`) resolves to deny | unit | same | ⚠️ extend |
| Hook wiring | after settings.json edit, all pre-existing GSD hook commands still present | unit | `tools/hooks/tests/test_settings_coexist.py` (parse JSON, assert GSD commands ∈ arrays) | ❌ Wave 0 |
| Hook I/O | each hook: crafted stdin JSON → asserted exit code + emitted decision JSON | unit | per-gate test invoking `main()`/subprocess with a stdin fixture | ❌ Wave 0 |
| DEFERRED | opencode plugin execution | manual-only | n/a (authored-only, D-01) | — |
| DEFERRED | golden-parity real .NET run in commit-gate | manual-only | n/a (.NET-gated, D-06) | — |

### Sampling Rate
- **Per task commit:** `uv run pytest tools/<changed_pkg> -x -q`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** full suite green + a manual demo of each success criterion (contracts edit blocked; BOM/CRLF TSV fails linter; secret blocked; commit-gate non-zero on drift) before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tools/polyglot_lint/{__init__.py,lint.py,pyproject.toml,tests/test_lint.py,tests/test_corpus_parity.py}` — POLY-01
- [ ] `tools/hooks/{__init__.py,_stdin.py,pyproject.toml}` + `tests/` — shared adapter + gate tests
- [ ] `tools/hooks/tests/test_settings_coexist.py` — asserts GSD hooks preserved
- [ ] Extend `tools/harness_perms/tests/test_resolver.py` (or new `test_order_resolution.py`) — crit. 4 suite
- [ ] Framework already present (pytest locked) — no install needed; run `uv sync` after adding new members

## Security Domain

> `security_enforcement` not present in `.planning/config.json` → treat as enabled. This phase *is* a security-enforcement phase (secret protection, constitution-plane access control).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No user auth in the harness. |
| V3 Session Management | no | — |
| V4 Access Control | **yes** | contract-guard = path-scoped default-deny to the constitution plane via `resolve_path`; permission matrix last-wins with default-`ask` (no trailing broad allow, P3). |
| V5 Input Validation | **yes** | Hook adapters parse untrusted stdin JSON defensively (try/except, exit 0 on parse failure — GSD hook idiom); `subprocess.run([list], shell=False)` everywhere (no command injection). |
| V6 Cryptography | no (detection only) | Secret *scanner* detects key material; it does not perform crypto. Never hand-roll crypto (none needed). |
| V7 Error Handling & Logging | **yes** | Gates fail loud with a machine-readable reason; env-limitation skips are logged as SKIP, not swallowed silently in a way that hides a real failure. |
| V14 Configuration | **yes** | `*.env` path-deny; secret patterns; no secrets committed; `.claude/settings.json` additions are minimal and mirrored to `harness/` source. |

### Known Threat Patterns for {Claude Code hooks + Python subprocess gates}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Command injection via `tool_input.command` interpolation | Tampering / Elevation | Never shell-interpolate; classify git subcommands via token-walk (gsd-validate-commit.sh `lib/git-cmd.js` precedent); `subprocess.run([list], shell=False)`. |
| Agent self-approves constitution/golden edit | Elevation of Privilege | contract-guard deny + human-only token (`GOLDEN_APPROVE_HUMAN`, agent-must-not-fabricate) + CODEOWNERS in Phase 5. |
| Secret exfiltration via Read of `*.env`/key file | Information Disclosure | secret PreToolUse deny on `path_deny_globs` + content pattern scan on Write/Edit. |
| Hook bypass by rewriting `.claude/settings.json` | Tampering | `.claude/settings.json` itself is under repo review; Phase 5 CODEOWNERS + the coexist-test guard against silent removal of gates. |
| Malformed stdin crashes hook → tool proceeds unguarded (fail-open) | Denial / Tampering | Deliberate for *advisory* hooks (exit 0 on parse error); for **blocking** gates (contract-guard/secret) fail *closed* on ambiguity where safe, and unit-test the malformed-input path. |
| .NET-absent skip abused to bypass golden-parity | Tampering | Skip is logged + Phase 5 CI runs the real .NET job non-bypassably (the skip is dev-env-only, mirrored by a hard CI gate). |

## Sources

### Primary (HIGH confidence)
- In-repo verified: `tools/harness_perms/resolver.py` + `__init__.py` + `tests/test_resolver.py` (resolver API, order-resolution precedent), `libs/python/normalize/core.py` + `__init__.py` + `libs/normalize-spec.md` (R1–R8 rules, fixture corpus), `tools/contract_drift/drift.py` + `check.sh` (`run_gate`), `tools/golden_runner/runner.py` + `approve.py` (normalized compare, `GOLDEN_APPROVE_HUMAN`, explicit-dotnet-path skip pattern), `tools/strangler_guard/guard.py` (guard/refusal idiom), `.claude/settings.json` (existing hook slots to coexist with), `.claude/hooks/gsd-read-guard.js` + `gsd-validate-commit.sh` (stdin parse, block-via-exit-2 + `{"decision":"block"}`, git subcommand classifier), root `pyproject.toml` (uv workspace `members=["tools/*"]`, pytest config, ruff pin).
- `.planning/research/ARCHITECTURE.md` (Flow B enforcement path, plugin/CI shared-tooling), `.planning/research/PITFALLS.md` (P3 last-wins, P4 byte-diff, P8/P11 hooks-not-prose, P9 golden gate, P14 §4-5 hash).
- `/workspace/presentationformat/archive/parserimprove/uploads/integration_contracts_design.md` §4.3–4.6 + §5 checklist (POLY-01 rule source-of-truth).
- `code.claude.com/docs/en/hooks` (verified 2026-07-08, redirected from docs.claude.com): exit codes 0/2/other, PreToolUse `permissionDecision` deny/ask/allow/defer + `permissionDecisionReason`, PostToolUse/Stop `{"decision":"block","reason"}`, `continue`/`stopReason`, stdin fields (`session_id`,`hook_event_name`,`cwd`,`tool_name`,`tool_input`), matcher syntax (exact/`|`/regex).

### Secondary (MEDIUM confidence)
- `harness/plugins/session-inject.ts` (in-repo) — opencode plugin stub shape + resume-note banner precedent for authored-deferred `tool.execute.before/after` stubs. opencode hook names carried at MEDIUM confidence (opencode.ai 403s; re-verify at opencode wiring — A1).

### Tertiary (LOW confidence)
- Secret pattern shapes (AWS/PEM/env) — conventional industry patterns, not verified against a project-specific deny-list spec (A3; Claude's discretion per D-05).

## Metadata

**Confidence breakdown:**
- Standard stack (reuse assets + stdlib): HIGH — every API read directly from source in this session.
- Claude Code hook mechanics: HIGH — verified against current docs + existing in-repo hook precedents.
- Architecture / composition design: HIGH — mirrors the established three-layer tool idiom already shipped 4× in this repo.
- opencode plugin specifics: MEDIUM — authored-only/deferred; hook names unverified (opencode.ai 403).
- Secret pattern set: MEDIUM-LOW — discretionary; needs a project deny-list decision.

**Research date:** 2026-07-08
**Valid until:** ~2026-08-07 for in-repo/design (stable); ~2026-07-15 for Claude Code hook JSON shape (fast-moving runtime — re-verify `permissionDecision` field if wiring slips).
