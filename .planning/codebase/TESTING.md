# Testing Patterns

**Analysis Date:** 2026-07-14

**Scope:** harness CORE (`tools/**`, `libs/python/**`) with the CI-level view into
`examples/log-parser/**` (.NET side + cross-language golden parity) since the gates are wired
together in `.github/workflows/ci.yml`.

## Test Framework

**Runner:**
- pytest, pinned `>=8.4,<9` in root `pyproject.toml` (`[dependency-groups] dev`). Pin rationale
  (commented in `pyproject.toml`): syrupy 5.2.0 compatibility with pytest 9.x is unverified —
  do not let resolution drift to 9.x.
- Config: `[tool.pytest.ini_options]` in root `pyproject.toml`:
  ```toml
  minversion = "8.4"
  testpaths = ["libs/python", "tools"]
  addopts = "-ra"
  python_files = ["test_*.py", "*_test.py"]
  ```
  Note `testpaths` covers only the harness CORE — `examples/log-parser/tests` is run
  explicitly by name in CI, not swept by a bare `uv run pytest`.

**Snapshot/approval library (Python side):** syrupy `==5.2.0`, pinned exact (not `~=`).

**Schema validation CLI:** `check-jsonschema==0.37.4` (drives the `contract-check` CI job and the
`/contract-check` command).

**Run commands:**
```bash
uv run pytest                          # full harness-core suite (root testpaths)
uv run pytest libs/python -x -q        # scoped: normalize core only
uv run pytest tools/golden_runner      # scoped: one package
uv run pytest --collect-only -q        # count/list without running
uv run pytest examples/log-parser/tests  # the example instance's own suite (not in root testpaths)
```

**Current baseline:** **568 tests collected** via `uv run pytest --collect-only -q` over the
root `testpaths` (`libs/python` + `tools`). Treat a collected-count regression as a signal —
`tools/harness_lint/tests/test_ci_stale_derived.py` and the GEN-04/GEN-05 guard tests
(`tools/harness_lint/tests/test_core_no_example_dep.py`,
`test_core_no_workspace_member_dep.py`) exist specifically to keep this count meaningful, not
just large.

## Test File Organization

**Location — always co-located, package-local `tests/`:**
```
tools/<pkg>/tests/test_<thing>.py
tools/<pkg>/tests/conftest.py            # present in nearly every package
tools/<pkg>/tests/__snapshots__/*.ambr   # syrupy snapshots, where golden/determinism is proven
libs/python/normalize/tests/test_<thing>.py
examples/log-parser/tests/test_<thing>.py    # instance-level: cross-language golden parity
examples/log-parser/tests/conftest.py
examples/log-parser/tests/recorded/          # recorded fixtures for the example's tests
```
There is no top-level `tests/` for unit tests — `/tests/fixtures/workspace/...` at repo root is
a **cross-repo workspace fixture tree** (member-a / member-b synthetic repos with their own
`contracts/`, `.hashes/manifest.json`, `golden/`), used only by the `workspace` CI job's
cross-repo drift/golden tests (`tools/workspace_config/tests`,
`tools/golden_runner/tests/test_workspace_golden.py`,
`tools/contract_drift/tests/test_workspace_drift.py`) — not a general fixtures dir.

**Naming:** `test_<verb_or_concern>.py`; test function names read as an assertion, e.g.
`test_clean_tree_exits_zero`, `test_dotnet_absent_skips_golden_not_fail`,
`test_render_matches_committed_snapshot`.

## Test Structure

**Module docstring states what invariant the file proves, not just what it covers** — same
discipline as the source docstrings (spec-ID tags, `(GEN-04/GEN-05 ...)`, `(CONTRACT-03 ...)`).
Example shape (`tools/golden_runner/tests/test_sample_loop.py`):
```python
"""Generic default instance end-to-end (GEN-02, 05-02 Task 2).

Exercises the FULL contract→hash→drift→golden loop over the committed domain-neutral sample —
WITHOUT .NET — proving the machinery runs on a blank domain (Phase 5 success criterion 2): ...
"""
from __future__ import annotations
import tempfile
from pathlib import Path
from tools.contract_drift.drift import run_gate
from tools.contract_hash.hash import CONTRACTS_DIR, build_manifest
from tools.golden_runner.runner import run_golden_case


def test_sample_case_passes_via_identity_no_dotnet() -> None:
    """golden/sample runs the generic loop (identity converter, no .NET) -> PASS, no .received."""
    out = Path(tempfile.mkstemp(suffix=".tsv")[1])
    try:
        result = run_golden_case("sample", out, converter="identity")
        assert result.passed, f"sample case should PASS; diff:\n{result.diff}"
        assert result.received_path is None  # PASS never proposes a .received baseline
    finally:
        out.unlink(missing_ok=True)
```

**Fixtures / mocking:** `pytest`-native fixtures (`monkeypatch`, `tmp_path`, `capsys`) — no
separate mocking framework. Reused-asset composition (e.g. `commit_gate`) is tested by
monkeypatching the imported names on the module under test (`monkeypatch.setattr(commit_gate,
"run_gate", ...)`), not by patching the underlying library.

**Determinism tests (3-part pattern)** used for every derived-artifact generator (`docs_sync`,
`memory_regen.repo_map`, `memory_regen.contracts_index`, `harness_emit`):
1. `render()` twice over the same input is byte-identical (no timestamp/float leak).
2. `generate → sha256 → delete → regenerate` over a `tmp_path` produces identical hashes
   (proves reproducibility **without** relying on `git diff`, since the target can be
   gitignored).
3. `render()` over the **real** tree matches a **committed syrupy snapshot** — the actual
   determinism reference checked into git.
```python
def test_render_is_deterministic_over_real_tree() -> None:
    for name, schema in docs_sync.iter_schemas():
        assert docs_sync.render(name, schema) == docs_sync.render(name, schema)

def test_generate_delete_regenerate_is_byte_identical(tmp_path: Path) -> None:
    out = tmp_path / "reference"
    first = docs_sync.write(out=out)
    digest_1 = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in first}
    for p in first:
        p.unlink()
    second = docs_sync.write(out=out)
    digest_2 = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in second}
    assert digest_1 == digest_2

def test_render_matches_committed_snapshot(snapshot) -> None:
    combined = "\n".join(f"===== {name} =====\n{docs_sync.render(name, schema)}"
                          for name, schema in docs_sync.iter_schemas())
    assert combined == snapshot
```

**"Guard" / architecture-fitness tests** — a distinct category, not behavioral unit tests.
They scan the tracked file tree (via `git ls-files`, `subprocess`, `shell=False`) for forbidden
patterns and RED the suite if a structural invariant is violated:
- `tools/harness_lint/tests/test_core_no_example_dep.py` (GEN-04/GEN-05) — no file under
  `tools/`, `harness/`, `libs/` may `import examples` / reference an `examples/` path / carry
  demoted domain-vocabulary tokens (two-tier: SCOPE-A code deps, GEN-05 prose purity). Includes
  **negative-control tests** that deliberately inject a violation to prove the scanner is live
  (tamper-evidence, T-05-13/T-055-06 discipline).
- `tools/harness_lint/tests/test_core_no_workspace_member_dep.py` — analogous guard for the
  cross-repo workspace boundary.
- `tools/harness_lint/tests/test_ci_stale_derived.py`, `test_derived_freshness.py` — assert the
  committed derived plane matches its regeneration.
- `tools/harness_lint/tests/test_orchestrator_topology.py`,
  `test_fan_out_return_contract.py`, `test_agent_referential_integrity.py` — structural checks
  over the harness's own agent/command/skill definitions.

When adding a new core-vs-instance or core-vs-derived invariant, follow this pattern: scan
`git ls-files`-enumerated tracked files with a narrow, documented token list (avoid over-broad
matches — see the explicit exclusion note for bare terms like `dotnet`/`parser`/`converter` in
`test_core_no_example_dep.py`), and pair it with a negative-control test.

## Golden / Approval Testing

Two independent snapshot mechanisms, one per language side, plus a **canonicalizing
equivalence comparator** that is the actual cross-language gate (this is the more important
concept than either snapshot tool individually):

**syrupy (Python side)** — proves **determinism of a single language's derived output**
(`.ambr` files under `tools/<pkg>/tests/__snapshots__/`):
- `tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr`
- `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr`
- `tools/memory_regen/tests/__snapshots__/test_repo_map_determinism.ambr`
- `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr`
- Update: `uv run pytest --snapshot-update` (re-approves in place — a human-reviewed diff via
  `git diff`, same "review before commit" discipline as any other test-fixture change; syrupy
  itself has no separate ratification gate — that's what the golden-runner's `.received` /
  `.verified` split adds on top for cross-language equivalence, below).

**Verify.XunitV3 (.NET side)** — the `.received`/`.verified` snapshot workflow for the .NET
components living in `examples/log-parser/libs/dotnet/` and
`examples/log-parser/components/toy-converter/`. Referenced by name in
`harness/skills/golden-testing/SKILL.md` and `CLAUDE.md`'s stack table
(`Verify.XunitV3 31.20.0`); the example instance's `.csproj` files pull the package. This
document's scope is the harness core, so treat the .NET-side test mechanics as owned by
`examples/log-parser/AGENTS.md` — the core only defines the *comparator contract* both sides
must satisfy.

**The actual cross-language equivalence gate: `tools.golden_runner.runner`**
(`tools/golden_runner/runner.py`) — this is the golden/approval mechanism that matters most in
this repo, and it is NOT a byte-diff:
1. Resolves the .NET executable via an **explicit absolute path**
   (`$DOTNET_ROOT/dotnet` → `$HOME/.dotnet/dotnet`) — never a bare `PATH` lookup.
2. Spawns the .NET converter as `subprocess.run([list], shell=False)`, passing `--in`/`--out`
   file paths (the A-model boundary is a **file**, not stdout).
3. Normalizes **both** the converter's output file and the approved `expected/baseline.verified.tsv`
   through the shared `libs/python/normalize/core.py:normalize_tsv` §4.3–4.6 canonicalization
   core — **never a raw diff** (BOM/CRLF/locale/float-repr differences must PASS; only a value
   regression FAILs).
4. Diffs the two normalized strings: equal → `GoldenResult(passed=True)`; differ → writes a
   machine-proposed `expected/baseline.received.tsv` and returns `passed=False`. The
   human-approved `baseline.verified.tsv` is **never** overwritten by the runner.

Directory shape per case, under `golden/<case>/` (core) or
`examples/log-parser/golden/<case>/` (instance):
```
golden/<case>/input/seed.tsv
golden/<case>/expected/baseline.verified.tsv   # human-approved — never machine-written
golden/<case>/expected/baseline.received.tsv   # machine-proposed on FAIL only
```

**Promotion is a separate, human-gated tool — `tools.golden_runner.approve`**
(`/golden-approve` command wraps this):
```bash
uv run python -m tools.golden_runner.approve <case> --approve --adr <id> --confirm <token>
```
Refuses (raises `GoldenApprovalRefused`, CLI **exit 3**) unless **all three** are present:
1. explicit `--approve` flag,
2. an `--adr <id>` reference,
3. a `--confirm` value matching the `GOLDEN_APPROVE_HUMAN` environment variable (a human-set
   escape hatch an agent must never fabricate).
This is the "machines gate, humans ratify" invariant in executable form — see
`harness/skills/gate-model/SKILL.md` and `harness/skills/golden-testing/SKILL.md`.

**When a golden goes red:** it is a signal, not a chore — either fix the code (regression) or
capture the case + get human approval + an ADR (intentional behavior change). Never hand-edit
`.verified` to silence red.

## Gate Structure (contract-drift, schema-hash, emit-drift)

**Contract-drift gate** (`tools/contract_drift/drift.py`, wrapped by `tools/contract_drift/check.sh`):
- Recomputes the live per-schema **JCS (RFC 8785) SHA-256** manifest over `contracts/**/*.schema.json`
  (via `tools.contract_hash.hash.build_manifest`), diffs it against the committed baseline
  `contracts/.hashes/manifest.json`.
- Classifies each changed schema **breaking vs non-breaking** by structurally indexing
  `const`/`enum`/`required`/`properties` paths (`_index` in `drift.py`): purely-additive
  (new optional property, new enum case) = non-breaking; removed/renamed required field or a
  narrowed const/enum = breaking.
- Exit 0 = clean; exit 1 = drift detected (any divergence, including a §4-5 convention flip,
  trips the gate).
- Run: `bash tools/contract_drift/check.sh` or `uv run python -m tools.contract_drift.drift`
  (add `--workspace` for the cross-repo leg, `--contracts-dir`/`--baseline` to target an
  instance's manifest, e.g. `examples/log-parser/contracts`).

**Schema validation (`contract-check`):** `check-jsonschema --schemafile <schema>.schema.json
<instance>.yaml` over every `<name>.schema.json` + sibling instance pair under `contracts/**`
and `examples/**/contracts/**`. Presence-safe: prints a visible `SKIP` when zero pairs are found
so a no-op is never mistaken for a pass.

**Emit-drift gate:** re-runs `uv run python -m tools.harness_emit` (the single-source →
`.opencode/` + `.claude/` projector) and fails on any diff against the committed generated trees
(`.opencode`, `opencode.json`, `.claude/{agents,commands,skills}`, `AGENTS.md`, `CLAUDE.md`,
`.claude/settings.json`). This is the CI mirror of the "derived plane is never hand-edited" rule
for the harness's own runtime surface.

**Stale-derived gate:** regenerates `docs/reference/**` (`tools.docs_sync`) and
`.memory/derived/contracts-index.md` (`tools.memory_regen.contracts_index`), then fails on any
diff — using `git add -A` before `git diff --cached --exit-code` specifically so a **newly
created** derived page (untracked) is caught, not just a modified one (a deliberate deviation
from the emit-drift job's plain `git diff`, called out in the workflow's own comments as
"Pitfall P1").

## CI Structure (`.github/workflows/ci.yml`)

Single workflow, `on: pull_request`, top-level `permissions: { contents: read }` (least
privilege), pinned action versions (no `@main`), no event-input interpolated into any `run:`
shell. Jobs:

| Job | What it does |
|-----|---------------|
| `setup` | Emits the per-language test matrix from `harness/project.toml` (config-derived, not hardcoded) via `tools.harness_config.loader.languages()`. |
| `lang-tests` | Fans out one leg per configured language (currently `dotnet` + `python`, sourced from `setup`'s matrix) — installs the matching toolchain and runs `matrix.test` over `matrix.test_paths`. |
| `contract-check` | `check-jsonschema` over every schema+instance pair under `contracts/**` and `examples/**/contracts/**`. |
| `drift` | Contract-drift gate, run twice: root manifest, then `--contracts-dir examples/log-parser/contracts --baseline examples/log-parser/contracts/.hashes/manifest.json`. |
| `golden` | Installs .NET 10 for real, then `pytest tools/golden_runner` (converter-agnostic identity case) and `pytest examples/log-parser/tests` (the .NET-backed `require_dotnet` cases, which only run here). |
| `core-suite` | `uv run pytest` — the harness's own full suite (root `testpaths` = `tools/` + `libs/python`), including the GEN-03/GEN-04 guard tests. |
| `emit-drift` | Re-runs `tools.harness_emit`; fails on any hand-edited drift in the generated runtime trees. |
| `stale-derived` | Regenerates `docs/reference/**` + `.memory/derived/contracts-index.md`; fails on any diff (untracked-safe via `git add -A`). |
| `workspace` | Cross-repo (multi-repo workspace) gate — `contract_drift.drift --workspace` + the cross-repo pytest set (`tools/workspace_config`, workspace-config guard tests, `test_workspace_golden.py`, `test_workspace_drift.py`). |
| `gate` | Fan-in. `needs:` every job above, `if: always()`; fails if any upstream `result` is `failure` or `cancelled`. This is the single job a human enables as a **required status check** in branch protection — true enforcement is a repo setting, not something the workflow file alone grants. |

Every job runs `uv sync --all-packages` (bare `uv sync` would prune tool-member deps since each
`tools/*` is its own workspace member with its own `pyproject.toml`).

## Coverage / Test-Type Posture

- **No coverage percentage is enforced** — no `pytest-cov` config or coverage gate found in
  `pyproject.toml` or CI. The enforced posture is **structural**: the 568-test baseline plus the
  GEN-03/GEN-04/emit-drift/stale-derived guard tests, which fail the suite on drift/leak rather
  than on a coverage threshold.
- **Unit tests:** the bulk of `tools/*/tests/` — pure-function logic (`compare`, `_index`,
  `diff_manifests`, `resolve()`), fast, no subprocess/network.
- **Integration tests:** end-to-end loop tests that chain multiple tools without external
  processes (`test_sample_loop.py` chains contract-hash → contract-drift → golden-runner
  end-to-end using the built-in `identity` converter, no .NET required).
- **Golden/E2E across languages:** `examples/log-parser/tests/*` — require a live `dotnet`
  binary (`require_dotnet`-marked cases), only fully exercised in the CI `golden` job (installs
  .NET 10 for real); locally these are skip-safe when `dotnet` is absent (mirrors
  `commit_gate`'s "skip golden, never silently pass" discipline — `dotnet` absent SKIPs and logs,
  it never turns into a false PASS).
- **No E2E browser/UI framework** — not applicable (this is a CLI/tooling harness, no UI).

---

*Testing analysis: 2026-07-14*
