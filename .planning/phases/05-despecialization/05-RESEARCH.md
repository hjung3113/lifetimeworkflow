# Phase 5: De-specialization & Template Extraction - Research

**Researched:** 2026-07-09
**Domain:** Monorepo refactor / `git mv` extraction + core-tool instance-parametrization + runtime-gate approval-path (no new external code)
**Confidence:** HIGH (all claims verified against source at `file:line`; two CONTEXT premises corrected against source)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01 — 이동 대상 & 목적지 (GEN-01):** Move `contracts/log-specs/`, `contracts/reference-data/`, `contracts/normalization/`, `contracts/state/`, `libs/python/normalize/`, `libs/dotnet/Normalize/`, `libs/dotnet/Normalize.Tests/`, `libs/normalize-fixtures/`, `components/toy-converter/`, and referencing `golden/` cases → under `examples/log-parser/` (preserving tree: `examples/log-parser/contracts/...`). **`tools/` does NOT move** (core); domain paths hardcoded in it get **parametrized/config-ized** so core does not know about `examples/`. `contracts/.hashes/manifest.json` is **regenerated** (rebaselined) so the live drift gate is clean after the move.
- **D-02 — generic 기본 인스턴스 (GEN-02):** Root `contracts/` gets a domain-neutral minimal sample (e.g. `contracts/sample/greeting.schema.json`) + companion golden case (`golden/sample/...`). Zero semiconductor vocabulary. Proves the core machinery (hash·drift·golden·docs-sync·polyglot-lint) runs on an empty domain. Derived artifacts regenerated.
- **D-03 — 언어 설정 슬롯 (GEN-03):** Single SSOT `harness/project.toml` (or `.json`): `[languages]` list (id, tool-command glob, SDK bootstrap ref, test/format commands). Permission-matrix `dotnet */uv */pytest *` scopes, engineer personas, `/build`·`/test`·`/lint` bodies derive from it. **Minimal impl**: config file + thin loader + example supplies .NET+Python values; current hardcoded values reinterpreted as "the example instance's values." Full codegen is overkill.
- **D-04 — 코어→예시 단방향 의존 가드 (GEN-04):** Guard test: nothing in `tools/`·`harness/`·`libs/` (core) imports/path-references `examples/**`. Non-example pytest suite stays green. Example's own tests move to `examples/log-parser/` (.NET stays egress-deferred skip).
- **D-05 — 게이트 정본 경로 (핵심):** Add `GOLDEN_APPROVE_HUMAN` bypass to commit-gate (consistent with contract-guard): non-empty token → drift failure becomes **warn+pass, not block**. **Must NOT weaken polyglot/secret** — at minimum the drift component honors approval. Operational flow: human exports token → agent lands intended contract change → ADR records it. It is an *approval path*, not a gate *off*. Executor must set token via session env / temp settings.json env / run-script — **bash-bypassing the gate is forbidden**. Extends commit-gate tests (04-05): token present → drift bypassed/warned; absent → still blocks.
- **D-06 — ADR:** New ADR (0002-general-template-de-specialization or next number), MADR, Status accepted, complements (not supersedes) ADR-0001. Writing it is a constitution-plane write → lands via the D-05 approval path.

### Claude's Discretion
Exact `examples/` tree, generic sample contract content, `harness/project.toml` schema, loader/consumption mechanism, guard-test impl (grep vs import-scan), and the exact commit-gate bypass semantics (which components) are researcher/planner discretion. **Fixed (non-negotiable):** core→example no-dependency · post-move-drift-clean · generic-default-instance-works · gate-approval-path (not off) · normalization-logic-unchanged · ADR.

### Deferred Ideas (OUT OF SCOPE)
- Config-driven CI matrix → Phase 6.
- Additional domain examples → later.
- opencode runtime actual execution → after opencode install.
- No scope creep.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GEN-01 | Move log-parser domain seed → `examples/log-parser/`; new ADR + rebaselined manifest; live drift clean after move | Q1 hardcoding inventory + Q2 drift mechanics (corrected) + Q4 `git mv`/rebaseline order. Manifest is **keyed by path** (`hash.py:57`) so moved files change keys — rebaseline reflects generic only. |
| GEN-02 | Domain-neutral default instance at root; full contract→hash→drift→golden loop runs with zero semiconductor | Q7 sample contract + golden case. **normalize core must stay in core** (Open Q #1) for the generic loop to normalize. Golden actual-run needs a generic converter or accepts .NET-absent SKIP. |
| GEN-03 | Languages read from single config slot; permission-matrix scopes / personas / `/build`·`/test`·`/lint` derive from it | Q5 `harness/project.toml` schema + thin loader + consistency-test approach (config = SSOT, no full codegen). |
| GEN-04 | Core→example single-direction guard test; non-example suite green; root docs templatized | Q6 grep/import-scan test mirroring `harness_lint` idiom. **normalize + fixtures staying core is what makes GEN-04 satisfiable** (polyglot_lint/golden_runner import them). |
</phase_requirements>

## Summary

This is a **pure refactor/move phase — zero new external packages**. The work is: (1) `git mv` the semiconductor domain seed under `examples/log-parser/`, (2) parametrize the handful of places core `tools/` hardcode a domain root, (3) add a generic default instance at root, (4) turn the hardwired .NET+Python assumption into a `harness/project.toml` slot, (5) add a core→example no-dependency guard test, and (6) add the `GOLDEN_APPROVE_HUMAN` approval bypass to commit-gate's drift component. An accompanying ADR lands through that same approval path.

Two CONTEXT/ROADMAP premises were **verified against source and corrected**, and they materially change the plan:

1. **The drift gate does NOT compare against git HEAD.** `run_gate` compares the **working-tree** `contracts/` glob (`build_manifest`, `hash.py:52`) against the **working-tree `manifest.json` file on disk** (`load_baseline`, `drift.py:32-34`) — never git HEAD. `_git_show` touches HEAD only to *classify* an already-detected change breaking/non-breaking (`drift.py:114-130`). Consequence: if the executor regenerates `manifest.json` in the same working tree as the move **before committing**, the drift component is already clean at commit time. The claim "moving contracts out (HEAD still has old manifest) → drift → block" is false for this gate.

2. **The moved golden fixtures do NOT trip the polyglot component — because `git mv` is a rename, and `staged_files()` filters renames out.** `commit_gate.staged_files()` runs `git diff --cached --name-only --diff-filter=ACM` (`commit_gate.py:70-71`). A verbatim `git mv` is detected as **R (rename)**, which `--diff-filter=ACM` **excludes** (verified empirically in a scratch repo). So the intentionally-dirty golden inputs (`golden/**/input/seed.tsv` carry a real UTF-8 BOM `ef bb bf` + CRLF — verified via `od`) are not re-linted on a pure-rename move. **Caveat:** this holds only for verbatim renames; any content edit during the move drops similarity and re-classifies the file as A/M, which WOULD be linted and blocked.

**Primary recommendation:** Land the D-05 commit-gate bypass as a **first, standalone core-code commit** (touches only `tools/`, no constitution write, no drift — lands clean with no token). Then perform the move + generic-instance + ADR as subsequent commits with the human `GOLDEN_APPROVE_HUMAN` exported in the **Claude Code process environment** (so both the `contract_guard` and `commit_gate` PreToolUse hook subprocesses inherit it). Keep the **§4.3-4.6 normalize core (`libs/python/normalize`, `libs/dotnet/Normalize`, `libs/normalize-fixtures`) in core** — moving it is mechanically incompatible with GEN-02 + GEN-04 (Open Question #1).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Domain contract schemas (log-specs, equipment, state, correction-rules) | Example instance (`examples/log-parser/contracts/`) | — | Semiconductor-specific content; the slot a project fills |
| §4.3-4.6 canonicalizing comparator (`normalize.core`, `.NET Normalize`, fixtures) | **Core** (`libs/`) | — | Domain-NEUTRAL machinery (CONTRACT-02); imported by core `polyglot_lint` + `golden_runner`. Zero semiconductor vocabulary (verified `core.py`, `decimal_locale.json`). |
| Contract hashing / drift / docs-sync / memory-regen | Core (`tools/`) | reads active-instance root via param/config | Generic engines; only their *scan root* is instance-specific |
| Golden runner + toy-converter spawn | Core engine (`tools/golden_runner`) + Example converter (`examples/.../toy-converter`) | instance config supplies converter command + golden root | Engine is generic; the specific converter is domain |
| Commit-gate / contract-guard / secret-scan hooks | Core (`tools/hooks/`) | — | Runtime enforcement; domain-agnostic |
| Language/toolchain identity | Config (`harness/project.toml`) | Example supplies .NET 10 + uv values | GEN-03: languages are a slot, not hardcoded |

## Standard Stack (Reused Assets — zero new packages)

### Core (already present; all verified in `git ls-files` + `pyproject.toml`)
| Asset | Version | Purpose | Why Reused |
|-------|---------|---------|------------|
| `rfc8785` | 0.1.4 (pinned, `pyproject.toml`) | JCS canonicalization for contract hashing | Already the drift-gate hasher; no change |
| `jsonschema` | 4.26.0 (pinned) | Schema validation | Unchanged |
| `pytest` | >=8.4,<9 | Test runner | Existing suite; new guard/bypass tests use it |
| `syrupy` | 5.2.0 | Snapshot tests (`.ambr`) | Existing determinism snapshots MUST be regenerated post-move (see Pitfalls) |
| `networkx` | 3.x | repo-map PageRank | Unchanged engine; source-dir set may need config |
| `uv` | 0.11.x | Workspace/lockfile | **Workspace membership changes** — see Pitfall P1 |
| `git mv` | system git | History-preserving move | Verified: renames excluded from `--diff-filter=ACM` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `harness/project.toml` | `harness/project.json` | JSON matches existing `permission-matrix.json`/`opencode.json` precedent and needs no new parser; TOML reads more naturally for humans. Either satisfies D-03. **Recommend JSON** for parser-free consistency with existing config precedent, OR TOML via stdlib `tomllib` (py3.11+, no dep). |
| Full codegen of personas/commands from config | Consistency test (config == hardcoded values) | Codegen is explicitly "overkill" (D-03). A test asserting the hardcoded scopes match the config satisfies "derived, not hardcoded" at minimal cost. |

**Installation:** none — no packages added. `tomllib` (if TOML chosen) is stdlib in Python 3.11 (`requires-python = ">=3.11"`).

## Package Legitimacy Audit

**Not applicable — this phase installs zero external packages.** It moves files and edits existing core Python/JSON/Markdown. No registry interaction. slopcheck/npm/pip verification is vacuously satisfied.

## Q1 — Domain-Path Hardcoding Inventory (the core that must not know `examples/`)

Every location where a core `tools/` module pins a domain root, and what it must become. All line numbers verified.

| Tool / file | Hardcoded root | Line(s) | What it must become |
|-------------|----------------|---------|---------------------|
| `tools/contract_hash/hash.py` | `CONTRACTS_DIR = REPO_ROOT/"contracts"`; `MANIFEST_PATH` | 24-25 | Keep default = root `contracts/` (now the **generic** instance — correct). `build_manifest(contracts_dir)` is **already parametrized** (42). But `write_manifest()` hardcodes the real tree via no-arg `build_manifest()` (63) and `main --write` (73-76). Add an optional root arg so the example's manifest (`examples/log-parser/contracts/.hashes/manifest.json`) can also be regenerated. |
| `tools/contract_drift/drift.py` | imports `CONTRACTS_DIR`, `MANIFEST_PATH`, `REPO_ROOT` | 22-27 | `run_gate(contracts_dir, baseline_path)` **already parametrized** (133). `main()` calls `run_gate()` no-arg → generic `contracts/` (167). Add CLI target so `run_gate` can also gate `examples/log-parser/contracts`. `_git_show` uses `REPO_ROOT` for HEAD lookup (114-130) — fine (repo-relative). |
| `tools/golden_runner/runner.py` | `GOLDEN_DIR = REPO_ROOT/"golden"` (36); `TOY_CONVERTER_PROJECT = REPO_ROOT/"components/toy-converter/ToyConverter.csproj"` (37); `sys.path` shim `REPO_ROOT/"libs/python"` (30-32) | 30-37 | **`GOLDEN_DIR` and the converter project are DOMAIN** and must come from the active-instance config (`harness/project.toml [instance]`). The `libs/python` shim → `normalize.core` **stays** (normalize is core — Open Q #1). `case_dir` (57), `run_converter` default `project` (151-172) inherit the parametrization. |
| `tools/polyglot_lint/lint.py` | `sys.path` shim `REPO_ROOT/"libs/python"` → `normalize.core` | 31-41 | **No change IF normalize stays core.** Pure §4.3-4.6 rule engine; no domain path otherwise. |
| `tools/polyglot_lint/tests/test_corpus_parity.py` | `_FIXTURES = parents[3]/"libs"/"normalize-fixtures"` | 24 | This is a **core test** referencing `libs/normalize-fixtures`. If fixtures move to `examples/`, this core test path-references `examples/` → **GEN-04 violation**. → fixtures **stay core**. |
| `tools/docs_sync/generate.py` | `CONTRACTS_DIR = REPO_ROOT/"contracts"` (28); `REFERENCE_DIR = REPO_ROOT/"docs/reference"` (29) | 28-29 | `iter_schemas(contracts)` / `write(contracts, out)` **already parametrized** (204,222). `main()` → generic `contracts/`→`docs/reference/` (245) — correct for the template. Example gets its own reference under `examples/log-parser/docs/reference/` by passing both args. `_confine` (187) unchanged. |
| `tools/memory_regen/contracts_index.py` | imports `CONTRACTS_DIR`, `MANIFEST_PATH` (25); `KIND` maps domain families `log-specs/normalization/reference-data/state` (36-41) | 25, 36-41 | `index_rows(contracts_dir, baseline_path)` parametrized (51). `KIND` is domain-flavored but has `"other"` fallback (79) — generic `sample/` → `"other"` (works). Optionally add `"sample"`. |
| `tools/memory_regen/repo_map.py` | `DEFAULT_SOURCE_DIRS = ("libs/python","libs/dotnet","tools","components")` | 39 | `components/` empties after toy-converter moves; non-existent roots are skipped (57-58) so no crash. To map the example's code you'd add `examples/**` → that is **core referencing examples** (GEN-04 tension). Recommend: source dirs stay core-only OR come from config. |
| `tools/memory_regen/inject.py` | uses `run_gate()`; `.memory/` paths only | 30, 33-35 | **No domain hardcoding** — no change. |
| `tools/hooks/commit_gate.py` | imports `GOLDEN_DIR` from golden_runner (38); `discover_golden_cases` uses it (162-166) | 38, 162-166 | After golden moves + `GOLDEN_DIR` re-points to active instance, discovery follows. **Primary D-05 change target** (see Q2). |
| `tools/strangler_guard/guard.py` | `DEFAULT_GOLDEN_DIR = REPO_ROOT/"golden"` | 23 | Already CLI-parametrized (`--golden-dir`, 101-103). No blocking change. |

**Pattern:** most engines are *already* parametrized (`build_manifest`, `run_gate`, `iter_schemas`, `index_rows` all take a root arg). The real work is (a) an **active-instance resolver** (default = repo root generic instance; `harness/project.toml [instance] root` may point at `examples/log-parser`), and (b) de-hardcoding `golden_runner`'s `GOLDEN_DIR` + converter project, which are the only genuinely domain-pinned roots.

## Q2 — Drift-Gate Mechanics & the D-05 Fix (corrected against source)

### Verified mechanics
- `commit_gate.check_drift()` → `run_gate()` no-arg (`commit_gate.py:139`).
- `run_gate()`: `baseline = load_baseline(MANIFEST_PATH)` then `live = build_manifest(contracts_dir)` (`drift.py:142-143`).
- `load_baseline` = `json.loads(Path(baseline_path).read_text())` — reads the **working-tree `contracts/.hashes/manifest.json` file** (`drift.py:32-34`). **Not git HEAD.**
- `build_manifest` globs the **working-tree** `contracts/` filesystem (`hash.py:52`).
- `_git_show("HEAD:rel")` (`drift.py:114-130`) is used ONLY inside `classify()` for the *old* schema body, to label an already-detected change breaking/non-breaking.

**Therefore:** drift = (working-tree contracts) vs (working-tree manifest.json). Regenerating `manifest.json` in the working tree before commit makes drift clean. The commit-gate blocks on drift only when live ≠ the on-disk manifest (i.e., you changed a schema but forgot to rebaseline).

### The commit-gate has no approval bypass (the real D-05 gap)
`commit_gate.py` contains **no reference to `GOLDEN_APPROVE_HUMAN`** (verified). `contract_guard.py` is the precedent: `APPROVAL_ENV = "GOLDEN_APPROVE_HUMAN"` (46) and `approved = bool((os.environ.get(APPROVAL_ENV) or "").strip())` (91) — a non-empty, non-whitespace value authorizes.

### D-05 fix — exact change surface
Mirror the contract-guard token check inside commit-gate's **drift component only**:

```python
# tools/hooks/commit_gate.py
APPROVAL_ENV = "GOLDEN_APPROVE_HUMAN"

def _human_approved() -> bool:
    return bool((os.environ.get(APPROVAL_ENV) or "").strip())  # mirror contract_guard.py:91

def check_drift() -> GateResult:
    result = run_gate()
    if result["ok"]:
        return GateResult("contract-drift", "PASS", "live manifest matches the committed baseline")
    listed = ", ".join(f"{rel} ({kind}/{cls})" for rel, kind, cls in result["drifted"])
    if _human_approved():
        # WARN + PASS, not FAIL — "machines gate, humans ratify" (consistent with contract_guard)
        return GateResult("contract-drift", "PASS",
                          f"drift present but GOLDEN_APPROVE_HUMAN set — WARN (ratified): {listed}")
    return GateResult("contract-drift", "FAIL", f"unapproved schema change(s): {listed}")
```

- **Only `check_drift` changes.** `check_polyglot` (146-159) and `check_golden` (169-191) are untouched. If secret-scan participates in commit-flow it is a separate hook — untouched.
- `GateResult.blocked` is `status == "FAIL"` (55-56); returning `PASS` makes it non-blocking while still logging the WARN detail via `run_composition` (207).

### Which components honor the token — recommendation
- **Drift only** (intentional-contract-change) honors the token. **Polyglot stays hard** (a BOM/CRLF/locale breach in a *wire* file is never "intended"), **golden stays hard** (a real equivalence regression is never "approved away" — promotion goes through `/golden-approve`), **secret stays hard**. This matches D-05's explicit "must NOT weaken polyglot/secret" and the CONTEXT's "at minimum the drift component."

### Test extension (04-05 → `tools/hooks/tests/test_commit_gate.py`)
Existing idiom monkeypatches `run_gate`/`resolve_dotnet`/`staged_files` on the module (`test_commit_gate.py:36-48`). Add, using `monkeypatch.setenv`/`delenv`:
- `test_drift_present_with_approval_warns_not_blocks`: `_drift_present`; `monkeypatch.setenv("GOLDEN_APPROVE_HUMAN","yes")`; assert `commit_gate.main([]) == 0` and "WARN"/"ratified" in stdout.
- `test_drift_present_without_approval_still_blocks`: `_drift_present`; `monkeypatch.delenv("GOLDEN_APPROVE_HUMAN", raising=False)`; assert `!= 0` (guards the existing `test_drift_present_blocks`).
- `test_empty_token_does_not_bypass`: setenv to `""` / `"  "`; assert still blocks (mirrors contract-guard Q1 resolution).
- `test_approval_does_not_bypass_polyglot`: approval set + a staged BOM/CRLF `.tsv` (reuse `test_polyglot_violation_blocks` setup, 71-83) → assert still blocks (proves token does not weaken polyglot).

## Q3 — Landing the Move Commit Through the Live Bash-PreToolUse Commit-Gate

### The env-visibility constraint (verified)
`.claude/settings.json` wires the gate as a `PreToolUse` `Bash` hook: `uv run python -m tools.hooks.commit_gate --from-hook` (`settings.json:141-149`), and `contract_guard` as a `PreToolUse` `Write|Edit` hook (`124-129`). Both are spawned by Claude Code and read `os.environ` of **their own subprocess**, which inherits the **Claude Code process environment**. An inline `GOLDEN_APPROVE_HUMAN=x git commit` sets the variable only on the *git* process; the hook fires as a **separate process before** git runs and never sees it. Confirmed by Anthropic hook docs: hook commands run in a subprocess that inherits Claude Code's environment; `env` is set from the Claude Code process / settings, not from the tool command's inline prefix. `[CITED: docs.claude.com/en/docs/claude-code/hooks]`

### Recommended mechanism (ordered)
1. **Sequence the D-05 code change FIRST, as its own commit.** It edits only `tools/hooks/commit_gate.py` + its test — **core code, not the constitution plane** (`contract_guard` `CONSTITUTION_GLOBS` = `contracts/**`, `docs/adr/**`, `golden/**` only — `contract_guard.py:42`). Staging a `.py` means: polyglot skips non-`.tsv`; drift is unaffected (no contract change); golden SKIPs (dotnet absent). → **this commit lands clean with no token.** After it lands, the drift-approval path is live for the subsequent move commits.
2. **Human exports the token into the Claude Code process env before/for the move.** Two viable ways, in order of preference:
   - **(preferred) Export before launching the session:** `export GOLDEN_APPROVE_HUMAN=<value>` then start Claude Code. Every PreToolUse hook subprocess (`contract_guard`, `commit_gate`) inherits it. Only a human with shell access can set it — this *is* "machines gate, humans ratify." Unset / restart the session to remove it after the move.
   - **(alternative) `env` block in a gitignored `.claude/settings.local.json`:** add `"env": {"GOLDEN_APPROVE_HUMAN": "<value>"}`, perform the move, then delete it. Claude Code merges `settings.local.json` and injects its `env` into the session (and hooks). Prefer `.local` (gitignored) so the token is never committed. Note a settings change may require a session reload to take effect. `[CITED: docs.claude.com/en/docs/claude-code/settings]`
3. **Why the token is needed at all for the move:** the executor writes the new ADR (`docs/adr/000X-*.md`), the generic sample contract (`contracts/sample/*.schema.json`), and the generic golden fixtures (`golden/sample/**`) **via the Write/Edit tool** → `contract_guard` DENIES these constitution-plane writes unless the token is set (`contract_guard.py:60-69`). The same session env then also satisfies the new commit-gate drift bypass. (The `git mv` and `python -m tools.contract_hash --write` steps are **Bash**, so `contract_guard`'s `Write|Edit` matcher never fires on them — manifest regen is not gated.)

### Forbidden
- **Never bash-bypass the gate** (`git commit --no-verify`, editing `.claude/settings.json` to drop the hook, or `HUSKY`/hook-disable tricks). D-05 is an *approval path*, not a gate-off. The token is the only sanctioned mechanism.

### Order of operations (recommended)
1. Commit A (core only): D-05 commit-gate bypass + tests. Lands clean, no token.
2. Set `GOLDEN_APPROVE_HUMAN` in the session env (human).
3. `git mv` domain trees → `examples/log-parser/...` (Bash; verbatim renames).
4. `python -m tools.contract_hash.hash --write` → rebaseline root `manifest.json` to the generic instance.
5. Write generic sample contract + golden fixtures + new ADR (Write tool; token allows).
6. Regenerate derived docs/memory (`docs-sync`, `contracts_index`, `repo_map`) + update the broken syrupy snapshots (Pitfall P3).
7. Commit B: the move + generic instance + ADR + regenerated artifacts. commit-gate: drift clean (rebaselined) / drift-warn-if-any (token) · polyglot clean (renames excluded; new generic `.tsv` byte-clean) · golden SKIP.

## Q4 — `git mv` History Preservation + Re-baseline Order

- **Manifest is keyed by PATH.** `build_manifest` sets `rel = resolved.relative_to(base).as_posix()` with `base = contracts_dir.parent` (`hash.py:49,57`) → keys like `contracts/log-specs/standard-log.schema.json` (verified in `manifest.json`). Moving a file changes its key (it leaves the `contracts/` glob; a rebuild over `examples/log-parser/contracts` yields `examples/log-parser/contracts/...` keys). So the manifest is **path-keyed, not content-keyed** — the move necessarily rewrites it. Rebaseline is mandatory, not optional.
- **Exact sequence:** (1) `git mv contracts/log-specs contracts/reference-data contracts/state contracts/normalization/correction-rules.* examples/log-parser/contracts/...` (verbatim, 100% rename → history preserved, excluded from `--diff-filter=ACM`); (2) add the generic sample under `contracts/sample/`; (3) `python -m tools.contract_hash.hash --write` → root `manifest.json` now lists only the generic sample; (4) build the example's own manifest (`--write` with the example root) so `examples/log-parser/contracts/.hashes/manifest.json` exists for the example's drift gate; (5) after this, `python -m tools.contract_drift.drift` (root) reads clean.
- **`format-conventions.schema.json`** (`contracts/normalization/`) is generic §4.3-4.6 convention material, not semiconductor — consider keeping it at root as part of the generic instance's conventions (or duplicate a minimal one). `correction-rules.*` and `standard-log.*`/`equipment-*`/`equipment-progress.*` are domain → move.

## Q5 — `harness/project.toml` Config Slot (GEN-03)

**Precedent:** `harness/permission-matrix.json` is "pure data — NO enforcement logic ... consumed by `tools/harness_perms/resolver.py`" (`permission-matrix.json:2`); `harness/opencode.json` and `harness/opencode.config.schema.json` are authored config. So the repo already has the "config-as-data + thin consumer" pattern.

**Recommended minimal schema** (`harness/project.toml`; TOML via stdlib `tomllib`, or `.json` for parser-free parity):

```toml
[instance]
# active instance whose contracts/golden/converter the core tools target by default.
# root "" = the generic default instance at repo root; the example overrides via its own config.
root = ""

[[languages]]
id = "dotnet"
bash_scope = "dotnet *"          # → permission-matrix allow scope
build = "dotnet build"
test  = "dotnet test"
format = "dotnet format"
sdk_bootstrap = "tools/bootstrap/install.sh"   # BOOT-01
persona = "harness/agents/dotnet-engineer.md"

[[languages]]
id = "python"
bash_scope = "uv *"
test  = "uv run pytest"
format = "ruff format"
persona = "harness/agents/python-engineer.md"
# (pytest also carries its own allow scope "pytest *")
```

**Minimal consumption mechanism (no full codegen — D-03):**
- A thin loader `tools/harness_config/` (new virtual uv member; mirrors `tools/harness_perms/`) exposes `load_project()` → the parsed config.
- **Satisfy "derived, not hardcoded" via a consistency test**, not generation: `tools/harness_lint/tests/test_language_config.py` asserts that the `bash` allow-scopes in `harness/permission-matrix.json` (and `harness/opencode.json`) exactly equal the set of `languages[*].bash_scope` (+ `pytest *`), and that a persona file exists for each language. This makes the config the SSOT (any hardcoded value that diverges fails the test) at near-zero cost. The existing `harness_lint` suite (`test_opencode_json.py`, `test_agents.py`, `test_commands.py`) is the idiom to mirror.
- `/build`·`/test`·`/lint` bodies (currently literal `uv run pytest` / `dotnet test`, `test.md:16,23`) can, minimally, gain a one-line note "commands derived from `harness/project.toml [[languages]]`" and be covered by the same consistency test — avoiding a runtime templating engine while still making the config authoritative.

## Q6 — Core→Example Single-Direction Guard (GEN-04)

**Recommended shape:** a grep/scan pytest mirroring the `harness_lint` structural idiom (which already walks `harness/` files and asserts properties). New test, e.g. `tools/harness_lint/tests/test_core_no_example_dep.py`:

- Walk every tracked file under `tools/`, `harness/`, `libs/` (the core planes).
- **Fail** if any line contains an `examples/` path reference or a Python `import`/`from` of an `examples` package, **excluding**: comments that are the guard's own docstring, and config values that are explicitly an instance-root pointer (if `[instance] root` is allowed to name `examples/log-parser`, that single config datum is the sanctioned exception — treat `harness/project.toml` as exempt, or assert the only occurrence is there).
- Complement with an **import-scan**: attempt to import each core module and assert none resolves a module path under `examples/`.

This is greppable and fast, matches the repo's existing "structural test without a runtime" pattern (`test_commands.py:3`), and directly encodes the D-04 invariant. Keep the generic default instance's files (`contracts/sample`, `golden/sample`) OUT of the scan set (they're root, not `examples/`).

## Q7 — Generic Default Instance (GEN-02)

**Reuse the existing formats exactly:**
- Contract: `contracts/sample/greeting.schema.json` — a trivial JSON Schema (draft 2020-12) with `properties: {name: {type: string}, greeting: {type: string, const: "hello"}}`, `required: [name]`. Zero semiconductor vocabulary. Exercises hash (JCS), drift (const/enum/required classification paths in `drift.classify`), and docs-sync (`iter_schemas` → one reference page).
- Golden: `golden/sample/{meta.yaml, input/seed.tsv, expected/baseline.verified.tsv}` mirroring `golden/repr-only/` structure (`meta.yaml` + `input/` + `expected/`). Use a domain-neutral 2-column TSV (e.g. `name\tgreeting`). To prove the normalize path, include a benign representation diff (e.g. a trailing-zero decimal column) — **but keep the file byte-clean of BOM/CRLF** so the added `.tsv` (status A, not R) passes `check_polyglot` on the generic-instance commit.

**The golden-loop-actually-runs problem:** `golden_runner.run_golden_case` always spawns the .NET toy-converter (`runner.py:180-189`), which is (a) domain and (b) absent in this env (`resolve_dotnet` → no binary → commit-gate golden SKIPs, `commit_gate.py:177-178`). Two options for GEN-02's "loop runs with zero semiconductor":
- **(recommended) Parametrize the converter command** (ties into GEN-03 `[instance]`/`[languages]`): let the generic instance declare a trivial converter (e.g. a stdlib Python identity script or `cp`), so `contract→hash→drift→golden` runs end-to-end **without .NET**. This genuinely proves the machinery on a blank domain in-env.
- **(fallback) Accept the .NET-absent SKIP:** the generic instance proves `contract→hash→drift` for real and the golden case is present + discovered (`discover_golden_cases`, `commit_gate.py:162-166`) but its actual spawn SKIPs until a converter is configured. Consistent with current behavior, but weaker against the literal GEN-02 wording "the full loop runs."

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Detecting the move as history-preserving | A copy+delete + custom rename tracker | `git mv` | 100% renames auto-detected; history preserved; excluded from `--diff-filter=ACM` (verified) |
| Re-hashing contracts after move | A second hasher | `python -m tools.contract_hash.hash --write` | One canonical JCS hasher; a second impl could disagree with the drift gate (the project's stated anti-pattern) |
| Approval token semantics | A new bespoke bypass flag | Reuse `GOLDEN_APPROVE_HUMAN` + the exact `bool((os.environ.get(...) or "").strip())` check | Consistency with `contract_guard.py:91` / `approve.py`; agents already instructed never to fabricate it |
| Config parsing | A hand-written TOML parser | stdlib `tomllib` (py3.11) or JSON | No new dep; `requires-python >=3.11` guarantees `tomllib` |
| Normalize core relocation | Duplicating a §4.3-4.6 normalizer per instance | Keep ONE core normalizer | "정규화 로직 불변 — 이동만"; a second normalizer is the built-once anti-pattern |

**Key insight:** almost everything this phase needs already exists and is already parametrized — the discipline is to *route through* the existing engines (rebaseline via the real hasher, approve via the existing token, move via `git mv`) rather than reimplement.

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `contracts/.hashes/manifest.json` is a **path-keyed** committed baseline (`hash.py:57`) — it caches the OLD domain paths. | Data migration: regenerate via `--write` after the move (rebaseline). Mandatory. |
| Live service config | None — no external services (n8n, schedulers, DBs) hold the domain paths. Verified: no service configs in repo; `.claude/settings.json` hooks reference only `tools.hooks.*` module names (stable). | None. |
| OS-registered state | `.claude/settings.json` SessionStart runs `tools/bootstrap/install.sh` + `memory-inject.sh` — reference stable paths, not domain contract paths. | None. |
| Secrets/env vars | `GOLDEN_APPROVE_HUMAN` is a **runtime approval token**, not a stored secret; must be present in the Claude Code process env for the move session only (Q3). No key rename. | Set for the move session; unset after. |
| Build artifacts | `libs/dotnet/**/bin,obj` and `.dotnet/` are gitignored (`.gitignore`); `.memory/derived/**` is gitignored and regenerated. Committed **syrupy snapshots** (`.ambr`) cache OLD domain schema names/paths → stale after move. `uv.lock` encodes workspace members. | Regenerate `.ambr` snapshots (Pitfall P3); re-resolve `uv.lock` after workspace-member change (Pitfall P1). |

## Common Pitfalls

### P1: uv workspace member breakage
**What goes wrong:** `pyproject.toml` sets `members = ["libs/python", "tools/*"]` and `libs/python` has its own `pyproject.toml` (`logparser-normalize`). If `libs/python` is moved under `examples/`, the member glob `libs/python` no longer resolves → `uv sync` fails and the whole Python suite can't run.
**Why:** uv requires every `members` dir to exist and contain a `pyproject.toml`.
**How to avoid:** This is decisive evidence for **keeping `libs/python/normalize` in core** (Open Q #1). If a future decision does move it, `pyproject.toml [tool.uv.workspace] members` and `testpaths` (`pyproject.toml`) MUST be updated and `uv.lock` re-resolved in the same commit.
**Warning signs:** `uv sync` "member not found"; `pytest` collection error.

### P2: content-edited move re-triggers polyglot
**What goes wrong:** if the executor edits a golden `input/seed.tsv` (which carries intentional BOM+CRLF) while moving it, git similarity drops, git reports it as A/M (not R), it enters `staged_files()` (ACM), `check_polyglot` lints it, and the BOM/CRLF trips R1/R2 → commit blocked.
**How to avoid:** move golden fixtures **verbatim** (pure `git mv`, no content edits). Do domain-path edits (if any) in a *separate* commit that does not touch the dirty fixtures. Consider (orthogonal) excluding `**/golden/**/input/**` from `check_polyglot` since deliberately-noisy representation inputs are not A-model wire files — a latent scope gap surfaced by this move (they were committed pre-commit-gate in Phase 1, so never linted).
**Warning signs:** commit-gate `FAIL [polyglot] ... R1-BOM/R2-CRLF` on a `golden/**/input/*.tsv`.

### P3: stale syrupy snapshots (Phase 1-4 test breakage — MUST sequence)
**What goes wrong:** these committed snapshots encode the 5 domain schema names/paths and will fail after the move:
- `tools/docs_sync/tests/test_docs_sync_determinism.py` — `EXPECTED_PAGES` hardcodes `standard-log, correction-rules, format-conventions, equipment-master, equipment-progress` + `test_render_matches_committed_snapshot` over the real tree.
- `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr` — lists all 5 `contracts/...` paths.
- `tools/memory_regen/tests/__snapshots__/test_repo_map_determinism.ambr` — graph changes when `components/toy-converter` (and `libs/dotnet/Normalize` if moved) leave the source dirs.
**How to avoid:** in the same move commit, update `EXPECTED_PAGES` to the generic instance's page set and regenerate snapshots (`pytest --snapshot-update`). Verify determinism tests still pass. These are the concrete Phase 1-4 tests the planner must sequence a fix for.
**Warning signs:** `syrupy` snapshot mismatch; `test_five_seed_schemas...` assertion error.

### P4: core tests that reference moved domain assets
**What goes wrong:** `tools/golden_runner/tests/{test_repr_only,test_value_regression,test_compare_recorded}.py` and `tools/golden_runner/tests/recorded/*.tsv` are keyed to the domain `repr-only`/`value-regression` cases; `tools/polyglot_lint/tests/test_corpus_parity.py` references `libs/normalize-fixtures`. If those assets move but the tests stay in core `tools/`, the core suite references `examples/` → **GEN-04 self-violation** and red tests.
**How to avoid:** golden-case-specific tests (repr-only/value-regression) move **with the cases** to `examples/log-parser/`. The corpus-parity test stays green **because fixtures stay core** (Open Q #1). Re-point `golden_runner`'s `GOLDEN_DIR`/converter via the instance resolver so the *engine* tests use a generic/tmp fixture, not the domain case.
**Warning signs:** post-move `pytest` red in `tools/golden_runner/tests` referencing missing `golden/repr-only`.

## Code Examples

### Rebaseline order (verified commands)
```bash
# 1. verbatim history-preserving move (rename → excluded from --diff-filter=ACM)
git mv contracts/log-specs        examples/log-parser/contracts/log-specs
git mv contracts/reference-data   examples/log-parser/contracts/reference-data
git mv contracts/state            examples/log-parser/contracts/state
git mv components/toy-converter   examples/log-parser/components/toy-converter
git mv golden/repr-only           examples/log-parser/golden/repr-only
git mv golden/value-regression    examples/log-parser/golden/value-regression
# 2. add generic instance (Write tool; needs GOLDEN_APPROVE_HUMAN via contract_guard)
#    contracts/sample/greeting.schema.json ; golden/sample/{meta.yaml,input,expected}
# 3. rebaseline root manifest → generic only (Bash; not contract_guard-gated)
uv run python -m tools.contract_hash.hash --write
# 4. verify live drift clean (working-tree contracts vs working-tree manifest)
uv run python -m tools.contract_drift.drift    # → "contract-drift: OK"
```

### Verified: renames are excluded from the gate's staged-file view
```
$ git mv golden/repr-only/input/seed.tsv examples/.../seed.tsv
$ git diff --cached --name-only --diff-filter=ACM      # what commit_gate.staged_files() runs
(empty)                                                 # ← R (rename) excluded → not linted
$ git status --short
R  golden/repr-only/input/seed.tsv -> examples/log-parser/golden/repr-only/input/seed.tsv
```

## State of the Art

| Old (Phase 1-4) | Current (Phase 5 target) | Impact |
|-----------------|--------------------------|--------|
| `contracts/` = semiconductor domain | `contracts/` = generic default instance; domain under `examples/log-parser/` | Core is domain-neutral |
| `.NET+Python` hardcoded in permission-matrix/personas/commands | `harness/project.toml [[languages]]` SSOT | GEN-03: languages are a slot |
| commit-gate drift: no human path | commit-gate drift honors `GOLDEN_APPROVE_HUMAN` (warn+pass) | GEN-01 landing path; template completeness |
| Golden inputs never linted (committed pre-gate) | Move re-exposes them (only if content-edited) | Handle via verbatim rename / input-scope exclusion |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The §4.3-4.6 normalize core + fixtures should **stay in core**, narrowing ROADMAP SC1 / D-01's literal `libs/{...}` list. | Open Q #1 | If the user insists normalize MUST move, GEN-04 requires a heavier instance-injection refactor and GEN-02 needs a normalize core at root anyway — contradiction to resolve before planning. |
| A2 | Claude Code hook subprocesses inherit the Claude Code process env / `settings.json env`, and an inline `VAR=x git commit` does not reach the PreToolUse hook. | Q3 | If hook env behavior differs, the token-delivery mechanism changes; verify against installed Claude Code version before the move. |
| A3 | `harness/project.toml` (TOML via `tomllib`) vs `.json` is discretion; a **consistency test** (not codegen) satisfies GEN-03 "derived not hardcoded." | Q5 | If a reviewer reads GEN-03 as requiring literal generation, the minimal test-only approach may be judged insufficient. |
| A4 | Parametrizing the generic golden converter (identity/`cp`) is acceptable to make GEN-02's loop actually run without .NET. | Q7 | If disallowed, GEN-02 falls back to drift-only proof + golden SKIP in-env. |
| A5 | Excluding `golden/**/input/**` from `check_polyglot` is a legitimate scope fix (not a weakening). | P2 | If judged a weakening, must instead guarantee verbatim renames only. |

## Open Questions

1. **Does the §4.3-4.6 normalize core actually move, or stay in core? (BLOCKING — resolve before planning)**
   - What we know: ROADMAP Success Criterion 1 and CONTEXT D-01 **explicitly list** `libs/{python/normalize, dotnet/Normalize, normalize-fixtures}` as relocating under `examples/log-parser/`.
   - What's unclear / the conflict: core `tools/polyglot_lint/lint.py` (31-41) and `tools/golden_runner/runner.py` (30-34) **import `from normalize.core`** via a `sys.path` shim to `libs/python`; `tools/polyglot_lint/tests/test_corpus_parity.py` (24) references `libs/normalize-fixtures`. If these move to `examples/`, **core references `examples/` → GEN-04 (locked) is violated**; and the uv workspace member `libs/python` breaks `uv sync` (P1). Separately, **GEN-02** needs a normalize core at root for the generic golden/polyglot loop — if the only copy is under `examples/`, the generic loop can't normalize. `normalize.core` and the fixtures contain **zero semiconductor vocabulary** (verified `core.py`, `decimal_locale.json`) — they are the generic CONTRACT-02 "canonicalizing comparator," not domain seed.
   - Recommendation: **keep `libs/python/normalize`, `libs/dotnet/Normalize`(+`.Tests`), `libs/normalize-fixtures` in core.** Move only genuinely semiconductor content (`contracts/{log-specs,reference-data,state}`, `contracts/normalization/correction-rules.*`, `components/toy-converter`, domain `golden/` cases). This is the only reading consistent with the LOCKED GEN-02 + GEN-04 and "정규화 로직 불변." It **narrows the literal SC1/D-01 enumeration**, so it needs explicit user ratification. `[ASSUMED]`

2. **Which components honor the token — drift only, or also golden?**
   - Recommendation: **drift only** (per D-05 "must not weaken polyglot/secret"; golden regressions go through `/golden-approve`). Confirm the planner does not extend it to golden.

3. **Generic golden converter — parametrize (identity) or accept SKIP?**
   - Recommendation: parametrize a trivial converter so GEN-02's loop runs in-env (Q7); fallback is SKIP. Needs a one-line decision.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| git (with rename detection) | `git mv` history + gate rename-exclusion | ✓ | system git | — |
| uv | workspace resolve, run tools/tests | ✓ | 0.11.x | — |
| Python | tools, tomllib, tests | ✓ | 3.11 | — |
| pytest + syrupy | test/guard + snapshot regen | ✓ | 8.4.x / 5.2.0 | — |
| .NET 10 SDK | golden actual-run + `libs/dotnet` build/tests | ✗ | — | golden SKIPs (existing behavior); .NET tests stay egress-deferred (D-04) |

**Missing with fallback:** .NET SDK — golden-parity SKIPs and `libs/dotnet`/`examples/.../Normalize.Tests` stay skipped, exactly as in Phases 1-4. Does not block GEN-01/03/04; affects only GEN-02's actual golden run (Q7).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.x (`pyproject.toml [tool.pytest.ini_options]`) + syrupy 5.2.0 snapshots |
| Config file | root `pyproject.toml` (`testpaths = ["libs/python", "tools"]`) |
| Quick run | `uv run pytest tools/hooks/tests/test_commit_gate.py -x` |
| Full suite | `uv run pytest` |

### Phase Requirements → Test Map
| Req | Behavior | Type | Automated Command | Exists? |
|-----|----------|------|-------------------|---------|
| GEN-01 | Live drift clean after move + rebaseline | integration | `uv run python -m tools.contract_drift.drift` (exit 0) | ✅ engine exists; assertion is new |
| GEN-01 | Move is a history-preserving rename | unit | `git log --follow examples/log-parser/contracts/log-specs/standard-log.schema.json` | manual/CI |
| GEN-02 | Generic contract→hash→drift loop runs on blank domain | integration | `uv run python -m tools.contract_hash.hash` + `...contract_drift.drift` over root `contracts/sample` | ❌ Wave 0 (new sample + assertion) |
| GEN-03 | Permission scopes/personas derive from `harness/project.toml` | unit | `uv run pytest tools/harness_lint/tests/test_language_config.py` | ❌ Wave 0 |
| GEN-04 | No core file references `examples/**` | unit | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py` | ❌ Wave 0 |
| GEN-04 | Non-example suite green after extraction | suite | `uv run pytest` (excluding `examples/`) | ✅ (must stay green) |
| D-05 | drift + token → warn/pass; absent → block; token ≠ weaken polyglot | unit | `uv run pytest tools/hooks/tests/test_commit_gate.py` | ⚠️ extend existing file |

### Sampling Rate
- **Per task commit:** `uv run pytest tools/hooks/tests/test_commit_gate.py -x` (+ the touched module's test).
- **Per wave merge:** `uv run pytest` (full non-example suite) + `python -m tools.contract_drift.drift`.
- **Phase gate:** full suite green + drift clean before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tools/harness_lint/tests/test_core_no_example_dep.py` — GEN-04 guard.
- [ ] `tools/harness_lint/tests/test_language_config.py` — GEN-03 consistency (config == hardcoded scopes/personas).
- [ ] `harness/project.toml` + `tools/harness_config/` loader (+ its `pyproject.toml` as a uv member).
- [ ] `contracts/sample/greeting.schema.json` + `golden/sample/**` — GEN-02 default instance.
- [ ] Extend `tools/hooks/tests/test_commit_gate.py` — D-05 approval cases.
- [ ] Update `tools/docs_sync/tests/test_docs_sync_determinism.py` `EXPECTED_PAGES` + regen 3 `.ambr` snapshots.

## Security Domain

`security_enforcement` is not disabled in `.planning/config.json`, so it is treated as enabled — but this phase changes **no attack surface**: no new inputs, endpoints, authn/authz, or crypto. It *touches* two security-relevant runtime gates, and the controls are about **not weakening** them.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes (indirect) | commit-gate polyglot (§4.3-4.6) MUST stay hard for wire `.tsv`; token bypasses **drift only** |
| V4 Access Control | yes | `GOLDEN_APPROVE_HUMAN` is a human-only ratification token (agents instructed never to fabricate); constitution-plane writes stay `contract_guard`-gated |
| V6 Cryptography | no | JCS+SHA-256 hashing unchanged; nothing hand-rolled |
| V2/V3 Auth/Session | no | n/a |

### Known Threat Patterns for this change
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Agent self-approves a contract change (fabricates token) | Elevation of Privilege | Token comes only from human-set process env; non-empty check mirrors `contract_guard.py:91`; drift-only scope |
| Gate bypass via `--no-verify` / settings edit | Tampering / Repudiation | Explicitly forbidden (Q3); ADR records the intended change; append-only ADR is tamper-evident |
| Token weakens polyglot/secret checks | Tampering | D-05 change is confined to `check_drift`; add `test_approval_does_not_bypass_polyglot` |
| Token leaked into git | Info Disclosure | Deliver via process env or gitignored `.claude/settings.local.json`, never committed |

## Sources

### Primary (HIGH — repo source, verified at file:line)
- `tools/contract_hash/hash.py` (23-25, 42-68) — path-keyed manifest, parametrized `build_manifest`, hardcoded `write_manifest`.
- `tools/contract_drift/drift.py` (22-27, 32-34, 114-130, 133-162) — working-tree baseline vs working-tree glob; `_git_show` for classification only.
- `tools/hooks/commit_gate.py` (37-41, 62-71, 137-143, 162-192, 197-229) — components; `staged_files` ACM filter; no `GOLDEN_APPROVE_HUMAN`.
- `tools/hooks/contract_guard.py` (42, 46, 60-69, 91) — `CONSTITUTION_GLOBS`, token precedent.
- `tools/golden_runner/runner.py` (30-37, 79-103, 151-189) — `GOLDEN_DIR`/converter/normalize shim.
- `tools/polyglot_lint/lint.py` (31-41) + `tests/test_corpus_parity.py` (24) — normalize import + fixtures ref.
- `tools/docs_sync/generate.py` (28-29, 204-239) + `tests/test_docs_sync_determinism.py` — parametrized generator + hardcoded `EXPECTED_PAGES`/snapshot.
- `tools/memory_regen/{contracts_index.py(25,36-41,79), repo_map.py(39,57-58), inject.py}` — scan roots.
- `libs/python/normalize/core.py`, `libs/normalize-fixtures/decimal_locale.json` — normalize is domain-neutral (zero semiconductor).
- `pyproject.toml` (`[tool.uv.workspace] members`, `testpaths`), `libs/python/pyproject.toml` — workspace membership risk.
- `.claude/settings.json` (79-149) — PreToolUse hook wiring (contract_guard 124-129; commit_gate 141-149).
- `harness/permission-matrix.json`, `harness/opencode.json`, `harness/agents/{dotnet,python}-engineer.md`, `harness/commands/{build,test}.md` — GEN-03 hardcoded language targets.
- `golden/{repr-only,value-regression}/**` — verified BOM (`ef bb bf`) + CRLF (`od`, CRcount=3) in seed inputs.
- Empirical scratch-repo test — `git mv` → `R` status, excluded from `--diff-filter=ACM`.
- `.planning/ROADMAP.md §Phase 5`, `.planning/REQUIREMENTS.md §GEN`, `.planning/PROJECT.md`, CONTEXT.md — requirements/decisions.

### Secondary (MEDIUM — official docs, training)
- `[CITED: docs.claude.com/en/docs/claude-code/hooks]` — PreToolUse hooks run as subprocesses inheriting Claude Code env; command stdin carries `tool_input`, not process env.
- `[CITED: docs.claude.com/en/docs/claude-code/settings]` — `env` block + `settings.local.json` (gitignored) merge behavior. **Re-verify against the installed Claude Code version before the move (A2).**

## Metadata

**Confidence breakdown:**
- Domain-path inventory (Q1): HIGH — every root cited at file:line.
- Drift/polyglot gate mechanics (Q2, Q3): HIGH — verified against source AND empirically (scratch repo, `od`); corrected two CONTEXT premises.
- Config slot / guard / generic instance (Q5-Q7): MEDIUM-HIGH — mechanism verified against existing precedent; exact schema is discretion.
- normalize-stays-vs-moves (Open Q #1): HIGH confidence in the *conflict*; the *resolution* needs user ratification.

**Research date:** 2026-07-09
**Valid until:** ~2026-08-09 (stable; refactor of a static repo — only Claude Code hook/settings env behavior (A2) is externally versioned).
