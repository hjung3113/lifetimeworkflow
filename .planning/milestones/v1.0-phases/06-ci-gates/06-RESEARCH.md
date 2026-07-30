# Phase 6: CI + Gates (generic) - Research

**Researched:** 2026-07-09
**Domain:** GitHub Actions polyglot CI — config-derived matrix, non-bypassable gate fan-in, CODEOWNERS + PR-template human-ratification
**Confidence:** HIGH (action versions VERIFIED via `git ls-remote`; reused tool entrypoints read from source with file/line evidence; two schema-insufficiency gaps flagged for planner sequencing)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01 설정 파생 매트릭스(CI-01):** 워크플로에 `matrix` 생성 잡 — `harness/project.toml [[languages]]`를 읽어 per-language 잡 매트릭스를 `fromJSON`으로 팬아웃(하드코딩 금지). 로그파서 예시가 .NET 10 + Python(pytest) 레그 공급. + 고정 generic 잡: `contract-check`(check-jsonschema over contracts/** + examples/**/contracts), `drift`(contract-hash manifest 비교), `golden`(루트 generic identity 케이스 + 예시 .NET 케이스 — .NET 러너에서 실제 실행). 재사용: 기존 `tools/*` CLI를 CI가 그대로 호출(재구현 금지).
- **D-02 비우회(CI-01):** 모든 게이트 잡이 PR에서 required가 되도록 fan-in 게이트(전부 green 요구). 실제 required-check enforcement는 브랜치 보호(레포 설정) — 워크플로는 잡을 제공, enable 안내는 문서.
- **D-03 CODEOWNERS(CI-02):** `contracts/`·`docs/adr/`·`golden/` + `examples/*/contracts`·`examples/*/golden`을 사람 오너에 매핑. 오너 아이덴티티 = `<open_decisions D-A>`.
- **D-04 PR 템플릿(CI-02):** breaking-change / golden 업데이트 / contract-drift 확인 체크리스트. 레포 PR 템플릿 규약 존중.
- **D-05 .NET on GH:** `actions/setup-dotnet` 또는 `dotnet-install.sh --channel 10.0`(egress OK on GH). BOOT-01/CONTRACT-02의 로컬-deferred .NET이 CI에서 실제 도는 지점 — 골든 .NET 패리티가 진짜로 검증됨.

### Claude's Discretion
- 워크플로 파일 분할·잡 이름·매트릭스 생성 방식(python으로 project.toml→JSON emit 스텝)·CODEOWNERS glob 세부·PR 템플릿 문안은 planner/researcher 재량.
- **고정:** 설정 파생(하드코딩 아님)·기존 tools 재사용·헌법 평면 CODEOWNERS 게이트·모델식별자 없음·범용(예시 레그는 예시가 공급).

### Deferred Ideas (OUT OF SCOPE)
- 브랜치 보호 required-check enable(레포 설정) → 사람.
- emit 재생성 CI 체크(EMIT drift) → Phase 7.

### Open Decisions (execution-time — do NOT block research/planning)
- **D-A CODEOWNERS 오너 아이덴티티:** 권장 기본값 `@hjung3113` (레포 오너). Team/org handle이면 사용자 확인.
- **D-B 실제 PR 개설 여부:** 권장 — 워크플로 저작 + 로컬 YAML/로직 검증; 실제 PR은 사용자 승인 후.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CI-01 | 설정 파생 폴리글랏 매트릭스 CI — 언어별 테스트 잡 + generic contract-check/drift/golden 비우회 실행; `harness/project.toml`에서 파생(하드코딩 아님); 예시가 .NET 10 + pytest 레그 공급 | §Q1 config-derived matrix mechanism (setup job → `$GITHUB_OUTPUT` JSON → `fromJSON`), §Q2 generic jobs (exact CLI entrypoints), §Q3 .NET-on-runner (verified action versions), §Q4 fan-in. **Two schema-insufficiency gaps flagged** (per-language `test_paths`; drift CLI needs `--contracts-dir`/`--baseline`). |
| CI-02 | CODEOWNERS (헌법 평면 + 예시 등가물) + PR 템플릿(경량 breaking 체크) | §Q5 CODEOWNERS glob syntax + PR template location/checklist; §Q6 hook→CI mapping (constitution writes ratified by CODEOWNERS, not a CI job) |
</phase_requirements>

## Summary

Phase 6 turns the four Phase-4 in-session hook gates (contract-guard, polyglot-lint, secret-scan, commit-gate) into a **non-bypassable-at-merge GitHub Actions mirror**, plus the human-ratification path (CODEOWNERS + PR template). The hard constraint is that jobs are **config-derived from `harness/project.toml [[languages]]`**, not hardcoded `dotnet test`/`pytest`. The mechanism is the GitHub-native pattern: a `setup` job runs one Python step that reuses `tools/harness_config.loader` to emit a JSON matrix to `$GITHUB_OUTPUT`, and per-language jobs fan out with `strategy.matrix: ${{ fromJSON(needs.setup.outputs.matrix) }}`. The generic (language-agnostic) jobs — contract-check, drift, golden — call the **existing** `tools/*` CLIs verbatim (no re-implementation, D-01). A final `gate` job `needs:` all of them with `if: always()` and fails if any upstream failed; true branch-protection required-checks is a repo setting documented as out-of-scope.

This is also where the **.NET egress deferral finally runs for real**: on GitHub runners `actions/setup-dotnet@v5.4.0` (or the already-proven `tools/bootstrap/install.sh --channel 10.0`) installs .NET 10, so `examples/log-parser`'s `require_dotnet`-gated golden tests (currently SKIPping locally) and the xunit.v3 corpus tests **execute** instead of skip.

**Primary recommendation:** Author `.github/workflows/ci.yml` with a `setup` matrix-emitter job (Python, reuses `harness_config`), config-derived per-language jobs, three generic jobs calling existing CLIs, and a fan-in `gate`. Pin `actions/checkout@v7.0.0`, `actions/setup-dotnet@v5.4.0` (`dotnet-version: 10.0.100` — exact, not `10.0.x`), `astral-sh/setup-uv@v8.3.2`. **Sequence two prerequisite `project.toml`/CLI changes FIRST** (see §State of the Art / §Open Questions): add per-language `test_paths`, and add `--contracts-dir`/`--baseline` flags to the drift CLI — without them the "config-derived, run-the-example-legs" and "example-manifest drift" requirements cannot be satisfied by verbatim tool reuse.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Fan-out per-language test jobs | CI orchestration (GitHub Actions) | `tools/harness_config` (data source) | Matrix is a CI concern; the *data* is the SSOT config slot — CI must not re-encode the language list |
| Toolchain install on runner | CI runner | `tools/bootstrap/install.sh` (reusable) | .NET 10 / uv install is runner-provisioning; the harness already declares `sdk_bootstrap` per language |
| contract-check / drift / golden | Existing `tools/*` CLIs | CI job wrapper | D-01: CI *calls* the built-once gates, never re-implements canonicalization/hash/diff |
| Constitution-plane write authorization | CODEOWNERS (merge-time human gate) | Phase-4 `contract-guard` hook (write-time) | CI cannot block a write, only a merge; the write-block is the in-session hook, the merge-ratify is CODEOWNERS |
| Non-bypassable enforcement | Branch protection (repo setting) | fan-in `gate` job (check surface) | Workflow *provides* the required-check candidate; enabling required-checks is a human repo-settings action (out of scope) |

## Standard Stack

### Core (GitHub Actions — all official publishers, VERIFIED via `git ls-remote --tags`)
| Action | Version | Purpose | Why Standard |
|--------|---------|---------|--------------|
| `actions/checkout` | **v7.0.0** | Clone the repo into the runner | Official; v7 is current major (ESM migration, credential-in-`$RUNNER_TEMP`). [VERIFIED: git ls-remote github.com/actions/checkout] |
| `actions/setup-dotnet` | **v5.4.0** | Install .NET 10 SDK on the runner | Official; v5.x installs .NET 10. Pin `dotnet-version: 10.0.100` (GA SDK) — NOT `10.0.x` (see Pitfall 1, issue #711). [VERIFIED: git ls-remote github.com/actions/setup-dotnet] |
| `astral-sh/setup-uv` | **v8.3.2** | Install `uv`, restore the workspace, cache | Official Astral action; matches the repo's uv-workspace model. No minor tags published — must use a full-version tag. [VERIFIED: git ls-remote github.com/astral-sh/setup-uv] |

### Supporting (already in-repo — reused verbatim, D-01)
| Asset | Entrypoint | Purpose | Evidence |
|-------|-----------|---------|----------|
| Config loader | `tools/harness_config/loader.py` — `load_project()`, `languages()`, `language_bash_scopes()` | Read `[[languages]]` → emit CI matrix JSON | loader.py:32-53; docstring line 6 explicitly reserves it for "the Phase-6 config-derived CI matrix" |
| Contract-drift gate | `python -m tools.contract_drift.drift` (via `tools/contract_drift/check.sh`) | Recompute JCS SHA-256 manifest, diff vs committed baseline | check.sh:12 `exec uv run python -m tools.contract_drift.drift "$@"`; drift.py:165 `main`, drift.py:133 `run_gate(contracts_dir, baseline_path)` |
| Contract-hash | `python -m tools.contract_hash.hash [--write]` | (Re)build manifest; `--write` rebaselines | hash.py:71 `main`; MANIFEST_PATH = `contracts/.hashes/manifest.json` (hash.py:25) |
| Golden runner | `python -m tools.golden_runner.runner <case>`; `run_golden_case(case, out, converter=, project=, golden_dir=)` | Run one equivalence case; identity (no-.NET) or .NET spawn | runner.py:229 `main`; runner.py:205 `run_golden_case`; GOLDEN_DIR = `golden/` (runner.py:36) |
| Polyglot §4.3-4.6 linter | `python -m tools.polyglot_lint.lint <tsv>` | Boundary hygiene over `*.tsv` wire files | lint.py:118 `main`, lint.py:126 arg `path` |
| check-jsonschema | `uv run check-jsonschema --schemafile <schema> <instance>` | Instance-vs-schema validation | Pinned `check-jsonschema==0.37.4` (pyproject.toml:21); exact loop already authored in `harness/commands/contract-check.md:28` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `actions/setup-dotnet@v5.4.0` | `tools/bootstrap/install.sh` (`dotnet-install.sh --channel 10.0`) | The bootstrap is **already config-declared** (`sdk_bootstrap = "tools/bootstrap/install.sh"`, project.toml:26) and proven in-session — using it makes the matrix maximally config-consistent and dodges the `10.0.x` resolution bug entirely. `setup-dotnet` gives caching + cleaner logs. Recommend: prefer whichever the language's `sdk_bootstrap` field names, fall back to `setup-dotnet`. |
| Reused stdin secret hook | `gitleaks/gitleaks-action` OR a new batch mode on `tools/hooks/secret_scan.py` | The Phase-4 `secret_scan.py` `main()` is **stdin-per-write only** (secret_scan.py:78-88) — it cannot scan a tree/diff. A CI secret job needs a batch surface. See Open Question 3. |
| Single monolithic `ci.yml` | Split (`ci.yml` + `gates.yml`) | Discretion (D-01 notes). One file with clear job names is simpler for the fan-in `needs:` graph; recommend one file. |

**Installation:** No new Python/Node packages. `check-jsonschema==0.37.4` already pinned (pyproject.toml:21). All three GitHub Actions are pinned by tag in YAML.

## Package Legitimacy Audit

> No new registry packages (npm/PyPI/crates) are introduced. The "packages" are three GitHub Actions, verified against their canonical official repos via `git ls-remote --tags` (authoritative — tags are immutable once cut per Astral's policy). slopcheck (a PyPI/npm tool) does not apply to GitHub Actions refs.

| Action | Source (official) | Latest tag | Verification | Disposition |
|--------|-------------------|-----------|--------------|-------------|
| `actions/checkout` | github.com/actions/checkout | v7.0.0 | git ls-remote (5 newest: v6.0.0…v7.0.0) | Approved [VERIFIED: git ls-remote] |
| `actions/setup-dotnet` | github.com/actions/setup-dotnet | v5.4.0 | git ls-remote (v5.0.1…v5.4.0) | Approved [VERIFIED: git ls-remote] |
| `astral-sh/setup-uv` | github.com/astral-sh/setup-uv | v8.3.2 | git ls-remote (v8.1.0…v8.3.2) | Approved [VERIFIED: git ls-remote] |
| `check-jsonschema` | PyPI (already pinned) | 0.37.4 | pyproject.toml:21 pin (installed in `.venv`) | Approved — pre-existing |

**Packages removed due to slopcheck [SLOP]:** none
**Packages flagged [SUS]:** none

**Supply-chain note (optional hardening, discretion):** GitHub's own security guidance recommends pinning third-party actions to a full commit SHA (`@<sha> # v8.3.2`) rather than a moving tag. The three actions here are first-party (`actions/*`) or the toolchain vendor (`astral-sh/*`); tag-pinning is acceptable and readable. SHA-pinning is a defensible upgrade — planner's discretion.

## Architecture Patterns

### System Architecture Diagram

```
                         pull_request event
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  setup (job)     │   reuse tools/harness_config.loader
                        │  python step:    │   → build {"include":[{lang,test_paths,setup},…]}
                        │  emit matrix JSON│───────────────► $GITHUB_OUTPUT (matrix=…)
                        └──────────────────┘
                                 │ needs
              ┌──────────────────┼──────────────────────────────┐
              ▼                                                   ▼
   ┌───────────────────────────────┐              ┌────────────────────────────────┐
   │ lang-tests (matrix job)       │              │ generic gate jobs (fixed)      │
   │ strategy.matrix:              │              │  • contract-check              │
   │   fromJSON(needs.setup.matrix)│              │    check-jsonschema over       │
   │ per leg:                      │              │    contracts/** + examples/**  │
   │  dotnet → setup-dotnet 10.0.100│             │  • drift                       │
   │          dotnet test <paths>  │              │    drift CLI: ROOT manifest    │
   │  python → setup-uv; uv sync   │              │      + EXAMPLE manifest        │
   │          uv run pytest <paths>│              │  • golden                      │
   │ (example supplies both legs)  │              │    root identity (no-.NET) +   │
   └───────────────────────────────┘             │    example .NET (require_dotnet │
              │                                    │    RUNS, not skips)            │
              │                                    └────────────────────────────────┘
              └───────────────────┬────────────────────────────┘
                                  ▼
                         ┌──────────────────┐
                         │ gate (fan-in)    │  needs: [setup, lang-tests,
                         │ if: always()     │         contract-check, drift, golden]
                         │ fail if any      │  → the required-check CANDIDATE
                         │ needs.*.result   │     (branch protection = repo setting,
                         │ == 'failure'     │      human-enabled, OUT OF SCOPE)
                         └──────────────────┘

   Human-ratification plane (not a CI job):
     .github/CODEOWNERS      → contracts/ adr/ golden/ + examples/*/{contracts,golden}
     .github/pull_request_template.md → breaking/golden/drift checklist
```

### Recommended Project Structure
```
.github/
├── workflows/
│   └── ci.yml                    # setup + matrix + 3 generic + fan-in gate
├── CODEOWNERS                    # constitution-plane + example equivalents → @owner
└── pull_request_template.md      # lightweight breaking/golden/drift checklist
```

### Pattern 1: Config-derived matrix via `$GITHUB_OUTPUT` + `fromJSON`
**What:** A `setup` job emits a JSON matrix built from `project.toml`; downstream jobs consume it. This is the canonical GitHub-native "dynamic matrix" pattern — no third-party action.
**When to use:** Any time the fan-out set must come from repo data, not a hardcoded YAML list (exactly D-01).
**Example:**
```yaml
# Source: GitHub Actions docs — "Defining outputs for jobs" + "jobs.<id>.strategy.matrix"
#         combined with the repo's tools/harness_config.loader (loader.py:42 languages()).
jobs:
  setup:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.mk.outputs.matrix }}
    steps:
      - uses: actions/checkout@v7.0.0
      - uses: astral-sh/setup-uv@v8.3.2
      - id: mk
        run: |
          uv run python - <<'PY' >> "$GITHUB_OUTPUT"
          import json
          from tools.harness_config.loader import languages
          # Emits one matrix leg per configured language. test_paths is the FLAGGED
          # schema addition (see Open Question 1) — until it lands, this falls back to
          # a hardcoded path map, which VIOLATES D-01, so land the schema change first.
          include = [
              {"id": l["id"], "test": l["test"],
               "test_paths": l.get("test_paths", []),
               "setup": l.get("setup", "")}
              for l in languages()
          ]
          print("matrix=" + json.dumps({"include": include}))
          PY

  lang-tests:
    needs: setup
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix: ${{ fromJSON(needs.setup.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v7.0.0
      # per-leg toolchain install keyed off matrix.id (dotnet vs python)
```

### Pattern 2: Generic jobs call existing CLIs verbatim (D-01, no re-implementation)
```yaml
  contract-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7.0.0
      - uses: astral-sh/setup-uv@v8.3.2
      - run: uv sync --all-packages
      # Reuse the EXACT loop authored in harness/commands/contract-check.md:28,
      # extended to also glob examples/**/contracts (the only instance PAIRS live there).
      - name: check-jsonschema (contracts/** + examples/**/contracts)
        run: |
          shopt -s nullglob globstar
          fail=0; any=0
          for schema in contracts/**/*.schema.json examples/**/contracts/**/*.schema.json; do
            base="${schema%.schema.json}"
            for inst in "$base".yaml "$base".yml "$base".json; do
              [ -f "$inst" ] || continue
              any=1
              uv run check-jsonschema --schemafile "$schema" "$inst" || fail=1
            done
          done
          [ "$fail" -eq 0 ] || exit 1

  drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7.0.0
      - uses: astral-sh/setup-uv@v8.3.2
      - run: uv sync --all-packages
      - name: root manifest
        run: uv run python -m tools.contract_drift.drift
      - name: example manifest
        # REQUIRES the drift CLI flag addition (Open Question 2). run_gate() ALREADY
        # takes contracts_dir + baseline_path (drift.py:133) — only main() lacks argparse.
        run: >
          uv run python -m tools.contract_drift.drift
          --contracts-dir examples/log-parser/contracts
          --baseline examples/log-parser/contracts/.hashes/manifest.json

  golden:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7.0.0
      - uses: actions/setup-dotnet@v5.4.0
        with: { dotnet-version: '10.0.100' }
      - uses: astral-sh/setup-uv@v8.3.2
      - run: uv sync --all-packages
      - name: root generic identity case (no .NET path)
        run: uv run pytest tools/golden_runner   # identity converter, .NET-free (test_sample_loop.py)
      - name: example .NET golden parity (require_dotnet now RUNS)
        run: uv run pytest examples/log-parser/tests
```

### Pattern 3: Non-bypassable fan-in gate
```yaml
  gate:
    needs: [setup, lang-tests, contract-check, drift, golden]
    if: always()                       # run even if a dependency failed
    runs-on: ubuntu-latest
    steps:
      - name: require all upstream green
        run: |
          results='${{ join(needs.*.result, ",") }}'
          echo "upstream results: $results"
          case "$results" in
            *failure*|*cancelled*) echo "::error::a required gate failed"; exit 1 ;;
          esac
```

### Anti-Patterns to Avoid
- **Hardcoding `dotnet test` / `pytest` job legs** — violates D-01/CI-01. The legs MUST derive from `project.toml [[languages]]`.
- **Re-implementing hashing/diff/canonicalization in YAML** — violates D-01. Call `python -m tools.*` verbatim.
- **`dotnet-version: 10.0.x`** — resolves to non-existent patch (issue #711). Pin exact `10.0.100`.
- **`dotnet test` with no project/solution path** — the example has 3 `.csproj` and **no `.sln`** (verified: `find examples -name '*.sln'` → none), so a bare `dotnet test` at instance root fails ("multiple projects"). Must pass explicit test-project path(s) — the reason `test_paths` is needed.
- **Assuming a merge is blocked by the workflow alone** — required-checks is a **repo branch-protection setting** (human), documented as out-of-scope (D-02, Deferred).
- **`bash << 'EOF'` heredocs to *write* the YAML files** — author via the file tools, not shell heredocs (repo rule).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Enumerate participating languages in CI | A hardcoded matrix list in YAML | `tools/harness_config.loader.languages()` | It is the GEN-03 SSOT; a hardcoded list is exactly the drift the config slot exists to prevent (loader.py:6) |
| Schema-hash / canonicalization | `sha256sum` + `jq` in a step | `python -m tools.contract_hash.hash` / `...contract_drift.drift` | RFC 8785 JCS + §4-5 convention coverage is non-trivial; already built + tested |
| Golden diff | `diff` in a step | `python -m tools.golden_runner.runner` / `run_golden_case` | Naive `diff` fails on BOM/CRLF/locale/float-repr — the exact polyglot bugs (CLAUDE.md "What NOT to Use") |
| Instance validation | Custom JSON validator | `check-jsonschema` (0.37.4, pinned) | Draft 2020-12 reference CLI; loop already authored in `contract-check.md` |
| Toolchain install | Ad-hoc `apt`/curl | `actions/setup-dotnet`, `astral-sh/setup-uv`, or the config-declared `sdk_bootstrap` | Cached, versioned, and (for bootstrap) already the in-session install path |

**Key insight:** Phase 6 writes **almost no new logic** — it is an orchestration layer that (a) reads the SSOT config and (b) shells the existing gates. The only new *code* the phase should introduce is two small, well-scoped enablers on the reused tools (a `test_paths` config field + loader passthrough, and a drift-CLI argparse) — both flagged below so the planner sequences them BEFORE the workflow that consumes them.

## Runtime State Inventory

> Phase 6 is additive (new `.github/` files + two small config/CLI enablers). It renames nothing. Included for completeness.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no datastore keys involved. | none |
| Live service config | **GitHub branch-protection required-checks** — lives in repo Settings (UI/API), NOT git. The workflow *provides* the `gate` check; enabling it as required is a human repo-settings action. | document in workflow header + a how-to; do NOT attempt to set via CI (D-02, Deferred) |
| OS-registered state | None. | none |
| Secrets/env vars | `GOLDEN_APPROVE_HUMAN` (commit_gate.py:53) is an in-session human token — **not** a CI secret; CI gates on drift/golden directly, it does not honor the bypass token. No new CI secrets required for the gate jobs. | none (CODEOWNERS handles ratification at merge) |
| Build artifacts | Example .NET `bin/`/`obj/` are `.gitignore`d (ruff `extend-exclude` lists them, pyproject.toml:47); CI builds fresh. | none — CI is clean-checkout |

## Common Pitfalls

### Pitfall 1: `dotnet-version: 10.0.x` downloads a non-existent patch
**What goes wrong:** setup-dotnet resolves `10.0.x` to a patch version that 404s (e.g. `10.0.5`), failing the job.
**Why it happens:** The `.x` wildcard resolution against the release index lags/overshoots for a young GA line. (actions/setup-dotnet issue #711.)
**How to avoid:** Pin the exact GA SDK `dotnet-version: '10.0.100'` (CLAUDE.md pins .NET SDK 10.0.100, GA 2025-11-11). Or use the config-declared `tools/bootstrap/install.sh --channel 10.0` which pins the channel, not a patch.
**Warning signs:** 404 on the SDK download step. [CITED: github.com/actions/setup-dotnet/issues/711]

### Pitfall 2: bare `dotnet test` fails — no solution + multiple projects
**What goes wrong:** `dotnet test` at the example root errors because there are 3 `.csproj` and no `.sln`.
**Why it happens:** `dotnet test` needs a single project or a solution in scope; the Phase-5 move left `Normalize/`, `Normalize.Tests/`, `toy-converter/` as loose projects.
**How to avoid:** Pass an explicit test-project path (`examples/log-parser/libs/dotnet/Normalize.Tests/Normalize.Tests.csproj`). This is precisely why the matrix needs a per-language `test_paths` field (Open Question 1). Note the `.NET` golden parity is *also* exercised via `uv run pytest examples/log-parser/tests` (the `require_dotnet` cases), so the .NET leg has two distinct surfaces: xunit corpus (`dotnet test <csproj>`) + golden spawn (`pytest`).
**Warning signs:** "Specify which project or solution file to use" / "multiple projects" error.

### Pitfall 3: example-manifest drift is silently unchecked
**What goes wrong:** CI runs `python -m tools.contract_drift.drift` (root only) and the **example** manifest (`examples/log-parser/contracts/.hashes/manifest.json`) drifts undetected.
**Why it happens:** `run_gate()` accepts `contracts_dir`/`baseline_path` (drift.py:133) but `main()` ignores argv (drift.py:166 `# noqa: F841 (reserved for future flags)`) — there is **no CLI flag** to target the example tree today.
**How to avoid:** Add argparse `--contracts-dir` / `--baseline` to drift `main()` (and matching `--contracts-dir`/`--manifest` to `hash.main()`), then run the CLI twice. The `# noqa` comment shows this was anticipated. Flagged as Open Question 2.
**Warning signs:** An edited example schema passes CI; the in-session commit-gate (which also only checks root via `run_gate()` defaults) would likewise miss it.

### Pitfall 4: `uv sync` prunes tool-member deps
**What goes wrong:** A bare `uv sync` uninstalls workspace-member deps not in the root (e.g. `tree-sitter`, `networkx`).
**Why it happens:** Documented in bootstrap (install.sh:36-39).
**How to avoid:** Use `uv sync --all-packages` in every job that runs tools (mirrors bootstrap).
**Warning signs:** ImportError on a tool that a job shells.

### Pitfall 5: contract-check finds nothing and silently passes
**What goes wrong:** The root `contracts/**` glob matches schemas with **no sibling instance** (`greeting.schema.json`, `format-conventions.schema.json` have no `.yaml`/`.json` pair), so `any=0` and the job no-ops. The only real instance PAIRS are in the example (`equipment-master.yaml`, `equipment-progress.yaml`).
**Why it happens:** check-jsonschema validates instance-vs-schema; root instances don't exist by design (schemas are convention/const contracts).
**How to avoid:** Glob **both** `contracts/**` and `examples/**/contracts/**` (as in Pattern 2) so the example instances are actually validated; keep the `any==0 → SKIP` message so the no-op is visible in logs, not mistaken for a pass.
**Warning signs:** contract-check job logs "SKIP: no pairs" while example instances exist.

## Code Examples

See Patterns 1-3 above for the full, verified YAML. Additional per-leg toolchain snippet:

### Per-language leg toolchain install (matrix job body)
```yaml
# Source: actions/setup-dotnet README (v5), astral-sh/setup-uv README (v8)
      - if: matrix.id == 'dotnet'
        uses: actions/setup-dotnet@v5.4.0
        with: { dotnet-version: '10.0.100' }   # exact GA SDK, not 10.0.x
      - if: matrix.id == 'python'
        uses: astral-sh/setup-uv@v8.3.2
      - run: uv sync --all-packages
      - name: run configured test command over configured paths
        run: |
          # matrix.test = "dotnet test" | "uv run pytest" (verbatim from project.toml)
          # matrix.test_paths = the FLAGGED new field (space-join)
          ${{ matrix.test }} ${{ join(matrix.test_paths, ' ') }}
```

## State of the Art / Required Enablers

| Old Approach | Current Approach | When Changed | Impact on Phase 6 |
|--------------|------------------|--------------|-------------------|
| Hardcoded `dotnet`/`python` YAML jobs (CLAUDE.md CI table, line 70) | **Config-derived** matrix from `project.toml` | This phase (ADR-0002 re-scope) | The CLAUDE.md "Jobs: dotnet…python…" table is the *old* hardcoded sketch; D-01 supersedes it with `fromJSON` |
| `project.toml [[languages]]` = `{id,bash_scope,test,format,sdk_bootstrap,persona}` | **Needs `test_paths`** (per-language test dirs, spanning core + example) | Must land in Phase 6 **before** the matrix job | Without it the matrix cannot locate the example's `.NET`/pytest legs → forces a hardcoded path map = D-01 violation |
| drift/hash `main()` = fixed root manifest | **Needs `--contracts-dir`/`--baseline` argparse** | Must land before the drift job | `run_gate()` already parameterized (drift.py:133); only the CLI wrapper is missing |

**Deprecated/outdated:**
- CLAUDE.md line 70's hardcoded job list — treat as historical guidance; D-01 config-derivation is authoritative.
- The `10.0.x` version wildcard for setup-dotnet — use exact `10.0.100`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `dotnet-version: '10.0.100'` is the correct GA SDK to pin on runners | Standard Stack / Pitfall 1 | Sourced from CLAUDE.md (.NET SDK 10.0.100, GA 2025-11-11). If a newer 10.0.1xx is required by a csproj `global.json`, pin that instead. Low risk — no `global.json` found in repo. |
| A2 | The generic golden root case runs via `pytest tools/golden_runner` (identity), not the runner CLI | Pattern 2 | The runner `main()` defaults `converter="dotnet"` (runner.py:240 calls `run_golden_case(case, out)`), so `python -m tools.golden_runner.runner sample` would try .NET and fail on the identity case. Verified via test_sample_loop.py:26 which passes `converter="identity"`. HIGH confidence. |
| A3 | Example `.NET` golden parity is exercised through `pytest examples/log-parser/tests` (require_dotnet RUNS when .NET present) | Pattern 2 | Verified: conftest.py:66-77 `require_dotnet` skips only when `dotnet_exe` missing; with setup-dotnet it exists → tests run. HIGH confidence. |
| A4 | Adding `test_paths` to `project.toml` won't break the GEN-03 consistency gate | Open Question 1 | `test_language_config.py` asserts scopes/personas agree; a *new* additive field should be ignored, but the planner must run that suite after the schema bump. MEDIUM — verify. |
| A5 | Default CODEOWNERS owner is `@hjung3113` | §Q5 | This is D-A's *recommended default* (repo owner, user email hjung3113@gmail.com). If a team handle is intended, user confirms at execution. Flagged execution-time. |

## Open Questions (RESOLVED)

1. **`project.toml` needs a per-language `test_paths` field for a truly config-derived matrix.**
   - What we know: `[[languages]]` today = `{id, bash_scope, test, format, sdk_bootstrap?, persona}` (project.toml:21-34). The `test` command is bare (`dotnet test`, `uv run pytest`); the example .NET tests live at `examples/log-parser/libs/dotnet/Normalize.Tests/` (no `.sln`), and example pytest at `examples/log-parser/tests` — neither is on the root `testpaths` (pyproject.toml:39 `testpaths = ["libs/python","tools"]`).
   - What's unclear: whether to model paths per-language (`test_paths = [...]`) or via an instance-root + convention. Per-language explicit list is the minimal, unambiguous fit.
   - Recommendation: **Planner sequences a small Wave-1 plan** — add `test_paths: list[str]` to each `[[languages]]` table + a `loader.py` passthrough (already trivially forward-compatible: `l.get("test_paths", [])`) + extend `test_language_config.py` to tolerate/verify the field. THEN the matrix workflow (Wave 2) consumes it. Without this, the matrix must hardcode paths = D-01 violation.

2. **Drift/hash CLIs need `--contracts-dir`/`--baseline` flags to cover the example manifest.**
   - What we know: `run_gate(contracts_dir, baseline_path)` and `build_manifest(contracts_dir)` are already parameterized (drift.py:133, hash.py:42); only `main()` ignores argv (drift.py:166 `# noqa … reserved for future flags`).
   - Recommendation: Add argparse to both `main()`s (a ~10-line change), sequenced with (or just before) the drift job. Alternative stop-gap: a `python -c` inline call — but adding the flag is cleaner and matches the reserved-for-flags intent.

3. **CI secret-scan has no batch surface.**
   - What we know: `secret_scan.py main()` is stdin-per-write (secret_scan.py:78-88); it cannot scan a tree or PR diff.
   - What's unclear: whether Phase 6 must mirror the secret hook in CI at all — the CONTEXT/ROADMAP success criteria (4 criteria) name contract-drift/golden/CODEOWNERS/PR-template but **not** a CI secret job. §Q6 maps secret-scan to the write-time hook (already enforced in-session).
   - Recommendation: **Do not add a CI secret job in Phase 6** (out of the 4 success criteria). Document the gap; if desired later, add a batch mode to `secret_scan.py` (reuse `PATTERNS`) or adopt `gitleaks-action`. Flag for user if they expect secret-scan at merge-time.

## Environment Availability

| Dependency | Required By | Available (local) | Available (GH runner) | Version | Fallback |
|------------|------------|-------------------|-----------------------|---------|----------|
| GitHub Actions runner (ubuntu-latest) | all CI | n/a | ✓ | — | — |
| .NET 10 SDK | example golden + xunit corpus | ✗ (egress-blocked locally — SKIPs) | ✓ (this is the deferral resolution) | 10.0.100 | `sdk_bootstrap` install.sh |
| uv | all Python legs + generic jobs | ✓ (0.8.17 → bump per CLAUDE.md) | ✓ (setup-uv) | 8.3.2 action | — |
| check-jsonschema | contract-check | ✓ (0.37.4 in .venv) | ✓ (via uv sync) | 0.37.4 | — |

**Missing dependencies with no fallback:** none.
**Missing (local) with fallback:** .NET 10 — locally SKIPs (`require_dotnet`), on the runner it installs and RUNS (the point of the phase). Local YAML validation (D-B recommended path) does not need .NET.

## Validation Architecture

> `workflow.nyquist_validation: true` (config.json) — section included.

### Test Framework
| Property | Value |
|----------|-------|
| Framework (Python) | pytest 8.4.x (pinned `>=8.4,<9`, pyproject.toml:35); syrupy 5.2.0 |
| Framework (.NET) | xunit.v3 3.2.2 + Microsoft.Testing.Platform (Normalize.Tests.csproj:18); net10.0 |
| Config file | `pyproject.toml [tool.pytest.ini_options]` (testpaths = libs/python, tools) |
| Quick run command | `uv run pytest tools/golden_runner tools/harness_config` |
| Full non-example suite | `uv run pytest` (testpaths) |
| Example suite | `uv run pytest examples/log-parser/tests` (explicit — NOT in testpaths) |
| YAML lint (self-check) | `uv run check-jsonschema --builtin-schema vendor.github-workflows .github/workflows/ci.yml` (check-jsonschema ships a GitHub-workflow builtin schema — validate the workflow itself) |

### Phase Requirements → Test Map
| Req | Behavior | Test Type | Automated Command | File Exists? |
|-----|----------|-----------|-------------------|-------------|
| CI-01 | matrix emitter produces valid JSON from project.toml | unit | `uv run pytest tools/harness_config` (add a test asserting `languages()` shape feeds a matrix) | ⚠️ Wave 0 — add `test_matrix_emit` |
| CI-01 | workflow YAML is structurally valid | smoke | `uv run check-jsonschema --builtin-schema vendor.github-workflows .github/workflows/ci.yml` | ✅ (check-jsonschema builtin) |
| CI-01 | drift CLI accepts `--contracts-dir`/`--baseline` (example manifest) | unit | `uv run pytest tools/contract_drift` (add a test for the new flags) | ⚠️ Wave 0 — add flag test |
| CI-01 | root identity golden passes .NET-free | unit | `uv run pytest tools/golden_runner/tests/test_sample_loop.py` | ✅ |
| CI-01 | example .NET golden parity runs with .NET present | integration | `uv run pytest examples/log-parser/tests` (require_dotnet) | ✅ (RUNS on runner) |
| CI-01 | `test_paths` config field present + consistent | unit | `uv run pytest tools/harness_lint/tests/test_language_config.py` | ⚠️ Wave 0 — extend gate for new field |
| CI-02 | CODEOWNERS covers constitution + example equivalents | manual/review | (GitHub validates CODEOWNERS syntax on push; no local runner) | manual |
| CI-02 | PR template surfaces on new PRs | manual | (GitHub behavior) | manual |

### Sampling Rate
- **Per task commit:** `uv run pytest tools/harness_config tools/contract_drift tools/golden_runner` (fast, no .NET)
- **Per wave merge:** `uv run pytest` (full non-example) + `uv run pytest examples/log-parser/tests` (if .NET available)
- **Phase gate:** the CI workflow itself green on a validation PR (D-B, user-approved) OR full local suite + `check-jsonschema` YAML validation.

### Wave 0 Gaps
- [ ] `tools/harness_config/tests/test_matrix_emit.py` — asserts the matrix JSON shape from `languages()` (covers CI-01)
- [ ] `tools/contract_drift/tests/test_cli_flags.py` — asserts `--contracts-dir`/`--baseline` target the example manifest (covers CI-01 example-drift)
- [ ] Extend `tools/harness_lint/tests/test_language_config.py` — tolerate/verify the new `test_paths` field (A4)
- [ ] Workflow self-validation step wired into the golden/generic job (`check-jsonschema` builtin GitHub-workflow schema)

## Security Domain

> `security_enforcement` not present in config.json → treat as enabled. This phase is CI/infra, not application input-handling; the relevant surface is supply-chain + secrets.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V1 Encoding/Sanitization (CI injection) | yes | No untrusted `${{ github.event.* }}` interpolated into `run:` shells; matrix values come from repo-controlled `project.toml` only (not PR-author input) |
| V6 Cryptography | no | none hand-rolled (JCS/SHA-256 already in `contract_hash`) |
| V10 Malicious Code / Supply Chain | yes | Pin actions to official publishers + version tags (or SHA); no `@main`/`@master` floating refs |
| V14 Configuration | yes | Least-privilege `permissions:` block on the workflow (default `contents: read`); no secrets exposed to matrix jobs |

### Known Threat Patterns for GitHub Actions
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Script injection via PR title/branch into `run:` | Tampering/Elevation | Never interpolate `github.event.*` into shell; use env vars + quoting. Here matrix data is repo-owned config, not event data. |
| Malicious/typosquatted action | Tampering | Official publishers only (`actions/*`, `astral-sh/*`), version-pinned + verified via git ls-remote; optional SHA-pin |
| Over-privileged `GITHUB_TOKEN` | Elevation | Add top-level `permissions: { contents: read }`; the gate jobs need no write scope |
| Secret leakage in logs | Info Disclosure | No secrets required by gate jobs; `GOLDEN_APPROVE_HUMAN` is an in-session token, not a CI secret |

## Sources

### Primary (HIGH confidence)
- `git ls-remote --tags` against github.com/{actions/checkout, actions/setup-dotnet, astral-sh/setup-uv} — latest tags v7.0.0 / v5.4.0 / v8.3.2 [VERIFIED]
- Repo source (file/line evidence cited inline): `tools/harness_config/loader.py`, `tools/contract_drift/{check.sh,drift.py}`, `tools/contract_hash/hash.py`, `tools/golden_runner/runner.py`, `tools/hooks/{commit_gate.py,secret_scan.py}`, `tools/polyglot_lint/lint.py`, `harness/project.toml`, `harness/commands/contract-check.md`, `pyproject.toml`, `examples/log-parser/**` (tree, conftest.py, csproj), `golden/sample/meta.yaml`
- CLAUDE.md — stack pins (.NET SDK 10.0.100 GA 2025-11-11, xunit.v3 3.2.2, check-jsonschema 0.37.x, setup-dotnet@v4/setup-uv@v6 *historical sketch*, CODEOWNERS/JCS drift guidance)
- `.planning/{ROADMAP.md §Phase 6, REQUIREMENTS.md CI-01/CI-02, phases/06-ci-gates/06-CONTEXT.md}`

### Secondary (MEDIUM confidence)
- WebSearch — actions/setup-dotnet v5 supports .NET 10 (dotnet-version 10.0.x); astral-sh/setup-uv no-minor-tags policy; actions/checkout v7 (2026-06)
- [CITED: github.com/actions/setup-dotnet/issues/711] — `10.0.x` wildcard resolves to non-existent patch → pin exact

### Tertiary (LOW confidence)
- WebFetch of setup-dotnet releases page returned suspect (stale) dates — superseded by the authoritative `git ls-remote` tag list; releases-page dates NOT relied upon.

## Metadata

**Confidence breakdown:**
- Standard stack (action versions): HIGH — VERIFIED via git ls-remote against canonical repos
- Tool reuse / entrypoints: HIGH — read from source with line evidence
- Config-derived matrix mechanism: HIGH (GitHub-native pattern) — but gated on a flagged `test_paths` schema addition (MEDIUM until landed)
- Example-manifest drift: HIGH that `run_gate` supports it; MEDIUM that the CLI wrapper must be added
- Pitfalls: HIGH — grounded in repo constraints (no `.sln`, `uv sync` pruning) + a cited action issue

**Research date:** 2026-07-09
**Valid until:** ~2026-08-09 (30 days; GitHub Actions majors move slowly, but re-verify `setup-uv`/`setup-dotnet` tags at plan time since Astral cuts frequent minors)
