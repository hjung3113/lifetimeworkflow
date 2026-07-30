---
phase: 06-ci-gates
plan: 03
subsystem: infra
tags: [ci, github-actions, codeowners, pr-template, config-matrix, fan-in-gate, least-privilege]

# Dependency graph
requires:
  - phase: 06-01
    provides: per-language test_paths slot in harness/project.toml + languages() passthrough
  - phase: 06-02
    provides: drift CLI --contracts-dir/--baseline flags for example-manifest gating
provides:
  - config-derived pull_request CI workflow (setup emits matrix from languages(), lang-tests fans out via fromJSON)
  - three generic jobs shelling existing CLIs verbatim (contract-check both trees, drift root+example, golden identity+.NET parity)
  - core-suite job running the harness's own non-example pytest suite (non-bypassable tooling-regression catch, W-2)
  - fan-in gate job (needs all six, if always(), fails on failure/cancelled) — the required-check candidate
  - CODEOWNERS routing constitution plane + example equivalents to @hjung3113
  - pull_request_template.md breaking/golden/drift checklist
affects: [branch-protection enablement (human, out of scope), future PR to default branch (D-B, deferred)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Config-derived CI matrix: setup job emits {include:[...]} JSON from languages() to $GITHUB_OUTPUT; lang-tests consumes via fromJSON (no hardcoded language legs)"
    - "matrix.id-keyed conditional toolchain install (.NET on dotnet leg, uv on python leg)"
    - "Generic jobs shell existing tools/* CLIs verbatim (D-01 — CI re-implements nothing)"
    - "Fan-in gate: needs=[all], if: always(), case-match join(needs.*.result) for failure/cancelled"
    - "Least-privilege: top-level permissions: contents: read; official pinned actions; no github.event.* in run shells"

key-files:
  created:
    - .github/workflows/ci.yml
    - .github/CODEOWNERS
    - .github/pull_request_template.md
  modified: []

key-decisions:
  - "uv sync --all-packages and setup-uv are gated to the python leg in lang-tests (the dotnet leg runs `dotnet test` and needs no uv workspace); setup-dotnet gated to the dotnet leg — keeps both installs conditional per matrix.id per plan while avoiding a guaranteed uv-not-found failure on the dotnet leg"
  - "gate fan-in uses case-match on ,join(needs.*.result), with comma sentinels so a substring never false-matches"
  - "workflow self-validation documented as a header-comment command (not a CI job) — check-jsonschema builtin schema is a local/authoring gate, not a runner dependency"

requirements-completed: [CI-01, CI-02]

# Metrics
duration: ~7min
completed: 2026-07-09
---

# Phase 6 Plan 03: Config-Derived CI Workflow + CODEOWNERS + PR Template Summary

**Authored the non-bypassable CI mirror (`.github/workflows/ci.yml`) — a `pull_request`-triggered workflow whose per-language test matrix is derived from `harness/project.toml` via `languages()` (never hardcoded), whose three generic jobs shell the existing contract-check/drift/golden CLIs verbatim over both the core and example trees, whose `core-suite` job re-runs the harness's own pytest suite, and whose fan-in `gate` job (needs all six, `if: always()`) is the required-check candidate — plus the human-ratification plane: `.github/CODEOWNERS` (constitution plane + example equivalents → @hjung3113) and a breaking/golden/drift `pull_request_template.md`. Structurally valid against the builtin GitHub-workflow schema; least-privilege + pinned actions; no real PR opened (D-B deferred).**

## Performance
- **Duration:** ~7 min
- **Started:** 2026-07-09T13:24:11Z
- **Tasks:** 4 (Task 1a, Task 1b, Task 2, Task 3)
- **Files created:** 3

## Accomplishments
- **Task 1a — setup + lang-tests scaffold:** `setup` job reuses `tools.harness_config.loader.languages()` to emit `{"include":[{id,test,test_paths}]}` to `$GITHUB_OUTPUT`; `lang-tests` fans out via `fromJSON(needs.setup.outputs.matrix)` with `matrix.id`-keyed .NET 10 / uv install. No hardcoded `dotnet test`/`pytest` job leg (D-01). Validated after this pass.
- **Task 1b — generic jobs + gate:** added `contract-check` (check-jsonschema loop over `contracts/**` AND `examples/**/contracts/**` with a visible `any==0 → SKIP`), `drift` (root bare invocation + example `--contracts-dir examples/log-parser/contracts --baseline …/manifest.json`), `golden` (setup-dotnet 10.0.100 → `pytest tools/golden_runner` + `pytest examples/log-parser/tests`, .NET runs for real), `core-suite` (`uv run pytest` — the harness's own non-example suite, W-2), and `gate` (`needs: [setup, lang-tests, contract-check, drift, golden, core-suite]`, `if: always()`, fails on `failure`/`cancelled`).
- **Task 2 — CODEOWNERS:** `/contracts/`, `/docs/adr/`, `/golden/`, `/examples/*/contracts/`, `/examples/*/golden/` → `@hjung3113`; header documents the "require review from Code Owners" branch-protection caveat and the solo-repo self-approval nuance.
- **Task 3 — PR template:** markdown task-list covering breaking contract change (+ADR link), golden update (CODEOWNERS-gated), and root+example contract-drift self-verification.
- **Security posture (T-06-05/06/07/09):** top-level `permissions: { contents: read }`; actions pinned to `actions/checkout@v7.0.0`, `actions/setup-dotnet@v5.4.0` (`dotnet-version: '10.0.100'` exact), `astral-sh/setup-uv@v8.3.2`; no `${{ github.event.* }}` interpolated into any `run:` shell; every tool-running job runs `uv sync --all-packages`.

## Task Commits
1. **Task 1a: setup + lang-tests matrix scaffold** — `ade97a4` (feat)
2. **Task 1b: generic jobs + fan-in gate** — `406c507` (feat)
3. **Task 2: CODEOWNERS** — `32b6bd5` (feat)
4. **Task 3: PR template** — `9e68fe2` (feat)

## Files Created
- `.github/workflows/ci.yml` — config-derived polyglot matrix + 3 generic jobs + core-suite + fan-in gate on `pull_request`; header documents the branch-protection required-check requirement (human, out of scope) and the self-validation command.
- `.github/CODEOWNERS` — constitution-plane + example-equivalent merge-ratification routing to `@hjung3113`, with enforcement + self-approval caveats.
- `.github/pull_request_template.md` — breaking / golden / contract-drift checklist (33 lines).

## Decisions Made
- **uv sync + setup-uv gated to the python leg** in `lang-tests` (see Deviations): keeps the plan's "conditional install keyed on `matrix.id`" while preventing a guaranteed `uv: not found` failure on the dotnet leg (which runs `dotnet test`, not a uv command).
- **gate fan-in** uses `case ",$results," in *,failure,*|*,cancelled,*)` with comma sentinels so a status substring can never false-match.
- **Workflow self-validation** is documented as a header-comment command rather than an added CI job — the builtin-schema check is an authoring/local gate, not a runner dependency, and adding it as a job would need it wired into `gate.needs` for meaning.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `uv sync --all-packages` on the dotnet leg would fail (uv not installed there)**
- **Found during:** Task 1a
- **Issue:** A literal reading places `uv sync --all-packages` unconditionally in `lang-tests`, but `setup-uv` is `matrix.id == 'python'`-conditional per the plan — so the dotnet leg (which only installs .NET) would hit `uv: not found` on the sync step, failing the whole leg before `dotnet test` runs.
- **Fix:** Gated both the `setup-uv` install AND the `uv sync --all-packages` step to `if: matrix.id == 'python'`. The dotnet leg installs only .NET and runs `${{ matrix.test }} ${{ join(matrix.test_paths, ' ') }}` = `dotnet test <csproj>`; the python leg installs uv, syncs, then runs `uv run pytest <tests>`. Both installs remain conditional on `matrix.id` exactly as the plan requires; the `run` test step stays unconditional and config-driven.
- **Files modified:** `.github/workflows/ci.yml`
- **Verification:** `uv run check-jsonschema --builtin-schema vendor.github-workflows .github/workflows/ci.yml` exits 0; the dotnet leg no longer references uv.
- **Committed in:** `ade97a4`

---

**Total deviations:** 1 auto-fixed (1 blocking — coherence between conditional toolchain install and the sync step).
**Impact on plan:** No scope change. All locked constraints (config-derived matrix, verbatim CLI reuse over both trees, core-suite, six-way fan-in gate, pinned actions, least-privilege, no event interpolation) met. SCOPE STOPPED at authored + locally-validated YAML — no PR opened.

## Verification Results
- `uv run check-jsonschema --builtin-schema vendor.github-workflows .github/workflows/ci.yml` → **exit 0** ("ok -- validation done"), after both Task 1a and Task 1b.
- `.github/CODEOWNERS` grep gate → OK (`@hjung3113` + all five globs present).
- `.github/pull_request_template.md` grep gate → OK (breaking/golden/drift present; 33 lines).
- No hardcoded language leg — `fromJSON` present; matrix sourced from `harness_config` loader.
- Actions pinned to `@v7.0.0` / `@v5.4.0` (`10.0.100`) / `@v8.3.2`; `permissions: { contents: read }`; no `github.event.*` in any `run:` shell (sole occurrence is a header comment).
- `core-suite` job present; `gate` has `needs: [setup, lang-tests, contract-check, drift, golden, core-suite]` + `if: always()`.
- Model-identifier scan across `.github/` → **none**.
- Full non-example suite `uv run pytest` → **413 passed** (3 snapshots) — green.
- **No real PR opened:** `gh` is not installed in this environment and no PR-creation step was run (D-B respected).

## Threat Surface Scan
No new security-relevant surface beyond the plan's `<threat_model>`. The workflow itself is the surface the threat register already covers (script injection, action pinning, token scope, false-pass no-op) — all mitigated as documented. No new endpoints, auth paths, or schema changes.

## User Setup Required
- **Branch protection (human, out of scope):** to make the mirror TRULY non-bypassable, enable the `gate` job as a required status check (Settings → Branches) and optionally "Require review from Code Owners". Documented in both `ci.yml` and `CODEOWNERS` headers; deliberately not automated (D-02).
- **PR to default branch (D-B, deferred):** opening the `claude/…` → default-branch PR is a separate, explicit user go-ahead — not performed here.

## Self-Check: PASSED
- Created files present: `.github/workflows/ci.yml`, `.github/CODEOWNERS`, `.github/pull_request_template.md`.
- Task commits present: `ade97a4`, `406c507`, `32b6bd5`, `9e68fe2`.

---
*Phase: 06-ci-gates*
*Completed: 2026-07-09*
