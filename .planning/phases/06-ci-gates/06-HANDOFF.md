# Phase 6 — Session Handoff

**Written:** 2026-07-09 (long session at context budget). Phase 6 is **researched**; **plan → check → execute** are for the NEXT session.

## Where things stand
- Phases 1–5, 5.5, 5.7 COMPLETE and pushed (`origin/claude/data-pipeline-harness-8aypct`, tip `355910b`). Non-example `uv run pytest` green (402 passed); GEN-04 guard clean (code+prose).
- Phase 6 (CI + Gates, generic) is set up: `06-CONTEXT.md` (decisions + two open user decisions) and `06-RESEARCH.md` (HIGH confidence, verified action versions, sequencing).

## USER DECISIONS — RESOLVED (2026-07-09)
- **D-A CODEOWNERS owner = `@hjung3113`** (user: "add just me; I'll change it later if needed"). Author `.github/CODEOWNERS` mapping the constitution-plane globs → `@hjung3113`, and DOCUMENT that hard enforcement requires enabling "require review from code owners" in branch protection (advisory-only otherwise); note the solo-repo self-approval nuance. Do NOT enable branch protection (repo setting, user-controlled).
- **D-B real PR = deferred to explicit approval.** Author the `pull_request`-triggered workflow + validate its YAML/logic locally this phase, but do NOT open the real PR (`claude/…` → default branch) without the user's explicit go-ahead.
- **CI secret-scan = deferred** (not in the 4 success criteria; no batch surface). Do not add a CI secret job.

## Next session — exact steps
1. **Read** `06-CONTEXT.md` + `06-RESEARCH.md` (no re-research needed).
2. **Plan** (gsd-planner). CRITICAL sequencing from RESEARCH — two small tool-ENABLER plans in Wave 1 (with Wave-0 tests), BEFORE the workflow-authoring plan (Wave 2) that consumes them:
   - **Enabler-1:** add a per-language `test_paths` field to `harness/project.toml [[languages]]` + trivial `tools/harness_config` loader passthrough + extend `tools/harness_config` tests. (Reason: the example has 3 `.csproj` and NO `.sln` so bare `dotnet test` fails; example pytest lives at `examples/log-parser/tests`, not on root `testpaths`.)
   - **Enabler-2:** add `--contracts-dir` / `--baseline` argparse to `tools/contract_drift/drift.py` `main()` (already parameterized at the function level, drift.py:133; `main()` ignores argv at drift.py:166) so CI can run drift against BOTH the root and the example manifest. Also note `tools/golden_runner` CLI defaults `converter=dotnet` — the root generic identity golden runs via `pytest tools/golden_runner` (not the CLI).
   - **Workflow plan (Wave 2):** `.github/workflows/ci.yml` — a `setup` job emitting the language matrix from `harness/project.toml` via a Python step (reuse `tools/harness_config`), `fromJSON` fan-out per-language jobs (example supplies .NET 10 + pytest legs), fixed generic jobs (contract-check via `check-jsonschema` over `contracts/**` AND `examples/**/contracts/**`; drift over root+example manifests; golden = `pytest tools/golden_runner` + `pytest examples/log-parser/tests` where .NET runs for real), and a fan-in `gate` job (`needs: [...]`, `if: always()`, fail on any failure). Pinned actions: `actions/checkout@v7.0.0`, `actions/setup-dotnet@v5.4.0` (`dotnet-version: 10.0.100` EXACT, not `10.0.x`), `astral-sh/setup-uv@v8.3.2`. Plus `.github/CODEOWNERS` (contracts/·docs/adr/·golden/·examples/*/contracts/·examples/*/golden/ → D-A owner) and `.github/pull_request_template.md` (breaking-change/golden/drift checklist).
3. **Check** (gsd-plan-checker) → revise to 0 blockers.
4. **Execute** wave-by-wave. Enabler plans touch `tools/`/`harness/project.toml` (NOT constitution plane) → no token. The workflow/CODEOWNERS/PR-template are `.github/` (not constitution plane) → no token. **Do NOT open the real PR without D-B confirmation.**

## Locked constraints
- Config-DERIVED matrix (no hardcoded dotnet/pytest jobs); reuse existing `tools/*` CLIs (no re-implementation); CODEOWNERS gates the constitution plane; domain-neutral core (example supplies its own legs); no model identifiers; keep non-example suite green.
- Branch-protection required-checks enforcement is a repo SETTING (out of scope — document that the human enables it).

## After 6
Phase 7 (Single-Source Dual-Runtime Emitter): `harness/` → `.opencode/` + `.claude/` with per-runtime limit validators + a re-emit-diff CI check.
