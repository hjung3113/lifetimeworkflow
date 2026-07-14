---
phase: 11-multi-repo-workspace-v2-0
plan: 03
subsystem: cross-repo-gates
tags: [MREPO-03, workspace, contract-drift, golden, _confine, ci, separate-job]

# Dependency graph
requires:
  - phase: 11-01
    provides: "workspace.toml manifest + tools.workspace_config loader (load_workspace/members/edges/split_endpoint) + 2-member fixture (baselined manifests + spanning golden case)"
  - phase: 11-02
    provides: "generalized GEN-04 guard (test_core_no_workspace_member_dep.py) — new tools/ test files must resolve member roots via the loader at runtime"
provides:
  - "workspace_drift() cross-repo gate (per-member run_gate reuse + edge-contract resolution) + --workspace CLI"
  - "_confine widened allowlist (threaded allowed_roots) + workspace_golden_case() member-root golden resolution"
  - "separate `workspace` CI job registered in gate.needs"
affects:
  - "Wave-4 (11-04) closeout — re-runs the full core suite + the workspace CI job as the phase gate"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Disciplined reuse: workspace_drift iterates already-parametrized run_gate per member (no new signature, no merged manifest — Pitfall 2)"
    - "Additive confinement widening: _confine gains a threaded allowed_roots param that EXTENDS the base (repo/tmp) allowlist, never removes the escape guard (T-11-06)"
    - "Cross-repo gate as a SEPARATE CI job in gate.needs (mirrors emit-drift/stale-derived), not folded into per-repo drift/golden"
    - "New tools/ test files resolve member roots via members(load_workspace()) at runtime — never path literals — so they pass the 11-02 GEN-04 twin"

key-files:
  created:
    - tools/contract_drift/tests/test_workspace_drift.py
    - tools/golden_runner/tests/test_workspace_golden.py
  modified:
    - tools/contract_drift/drift.py
    - tools/golden_runner/runner.py
    - .github/workflows/ci.yml

key-decisions:
  - "workspace_drift returns {members, edges_checked, unresolved_edges, ok}; ok = all members clean AND every edge resolved; a zero-edge workspace prints a VISIBLE SKIP (T-11-08)"
  - "Member manifests are NEVER merged — each member gated against its OWN contracts/.hashes/manifest.json via verbatim run_gate (Pitfall 2, .parent-relative key collision)"
  - "_confine widening is a threaded param (additive); the negative-control test proves an out-of-all-roots path still raises even with member roots threaded (guard extended, not removed)"
  - "workspace_golden_case reuses the existing golden_dir override + identity converter verbatim; the only new signature surface is the additive allowed_roots thread"
  - "Cross-repo gate is a separate `workspace` CI job added to gate.needs — the emit-drift/stale-derived separate-job idiom, not a fold into drift/golden"

patterns-established:
  - "Cross-repo contract-first + golden equivalence enforced by member-scoped invocation of already-parametrized tools + one edge-resolution check + one confinement widening"

requirements-completed: [MREPO-03]

# Metrics
metrics:
  duration: 7min
  tasks: 3
  files: 5
  completed: 2026-07-14
---

# Phase 11 Plan 03: Cross-Repo Contract-Drift + Workspace-Aware Golden + CI Job Summary

**The contract-first safety net now spans repo boundaries: cross-repo drift iterates each member's own baseline (no merge) and resolves every edge's contract in its producer, the golden runner resolves an edge-spanning case under a member root with a widened-not-removed `_confine` allowlist, and a separate `workspace` CI job in `gate.needs` enforces both (MREPO-03).**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-07-14T00:42:47Z
- **Completed:** 2026-07-14T00:49:33Z
- **Tasks:** 3
- **Files:** 5 (2 created, 3 modified)

## Accomplishments

- **Cross-repo contract-drift** (`tools/contract_drift/drift.py`): new `workspace_drift(ws_path=None)` — resolves member roots from `tools.workspace_config` at runtime, gates each member against its OWN `contracts/.hashes/manifest.json` by **verbatim reuse** of `run_gate` (never a merged manifest — `build_manifest` keys are `.parent`-relative so `contracts/...` keys collide across members, Pitfall 2), then resolves every `[pipeline].edges` edge's `contract` in its PRODUCER member (`split_endpoint(from)[0]` → `rglob("*.schema.json")`). Returns `{members, edges_checked, unresolved_edges, ok}` where `ok` = all members clean AND every edge resolved. A new `--workspace` CLI flag runs the gate (visible per-member OK, zero-edge SKIP, fail-loud unresolved edges); the single-tree `--contracts-dir`/`--baseline` path is untouched (additive).
- **Workspace-aware golden** (`tools/golden_runner/runner.py`): `_confine` gains an **additive threaded `allowed_roots`** param that EXTENDS the base `(REPO_ROOT, /tmp, $TMPDIR)` allowlist with declared member roots — a path outside EVERY allowed root still raises `GoldenRunnerError` (the guard is widened, never removed, T-11-06). Threaded through `run_identity_converter`/`run_converter`/`run_golden_case`; a new `workspace_golden_case(case, member_id, ...)` wrapper looks the member root up via the loader, points `run_golden_case` at `<member_root>/golden` (reusing the existing `golden_dir` override), and threads the member root into confinement. Defaults to the `identity` converter (no .NET).
- **Separate `workspace` CI job** (`.github/workflows/ci.yml`): mirrors the `drift`/`emit-drift`/`stale-derived` separate-job idiom (checkout → setup-uv → `uv sync --all-packages`), runs `drift --workspace` + the cross-repo pytest set, and is registered in `gate.needs` so a cross-repo failure fails the required gate. Security posture preserved: pinned actions, `contents: read`, no `${{ github.event.* }}` interpolation.
- Full core suite grows to **563 passed / 4 snapshots** (+8 new tests: 4 workspace-drift + 4 workspace-golden), no regression.

## Task Commits

Each task was committed atomically:

1. **Task 1: Cross-repo drift `workspace_drift()` + `--workspace` CLI + test** — `07d999a` (feat)
2. **Task 2: Workspace-aware golden — widen `_confine` allowlist (threaded) + `workspace_golden_case` + test** — `398281a` (feat)
3. **Task 3: Separate `workspace` CI job + `gate.needs` registration** — `8c24913` (ci)

## Verification

- `uv run pytest tools/contract_drift/tests/test_workspace_drift.py -q` → 4 passed (clean-fixture PASS + per-member drift FAIL + unresolved-edge FAIL).
- `uv run python -m tools.contract_drift.drift --workspace` → exit 0, prints per-member OK + all edges resolve.
- `uv run pytest tools/golden_runner/tests/test_workspace_golden.py tools/golden_runner -q` → 17 passed (edge-spanning case PASS + negative-control out-of-all-roots raises + widening-admits-threaded-root; no regression to the existing golden suite).
- `uv run check-jsonschema --builtin-schema vendor.github-workflows .github/workflows/ci.yml` → `ok`; `gate.needs` includes `workspace`; zero `github.event.` in the workspace job.
- **GEN-04 grep gates (11-02 twin):** `grep -c 'tests/fixtures/workspace'` returns **0** for all four touched non-fixture files (`drift.py`, `runner.py`, and both new test files); `test_core_no_workspace_member_dep.py` stays green.
- `uv run pytest -q` full core suite → **563 passed / 4 snapshots** (up from 555; +8, no regression).

## Deviations from Plan

None — plan executed exactly as written.

The only note: the Task 1 test docstring initially contained the literal `tests/fixtures/workspace/...` (as prose describing the guard invariant), which tripped the plan's strict `grep -c 'tests/fixtures/workspace' == 0` acceptance gate. Reworded to "hardcoded member-root path literal" — no logic change; the test already resolved all member roots via `members(load_workspace())` at runtime.

## Known Stubs

None — `workspace_drift` runs against the real 2-member fixture (per-member baselines + one edge), the golden runner resolves the real spanning `greeting-edge` case, and every negative control (per-member drift, unresolved edge, out-of-all-roots confinement) is a live assertion proving the gates cannot silently no-op.

## Threat Flags

None — no new trust boundary beyond the plan's `<threat_model>`. All subprocess calls stay `shell=False` argv lists (`_git_show`, converter spawn), the CI job interpolates no event input, and `_confine`'s escape guard is extended (not removed) with a negative-control proof.

## Self-Check: PASSED

- Both created files present on disk; all three modified files carry the new surface.
- All three task commits present in git history (07d999a, 398281a, 8c24913).

---
*Phase: 11-multi-repo-workspace-v2-0*
*Completed: 2026-07-14*
