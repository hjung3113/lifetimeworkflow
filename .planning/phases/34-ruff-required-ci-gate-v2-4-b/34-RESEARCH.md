# Phase 34 Research — Ruff as a Required CI Gate (DEBT-01)

**Researched:** 2026-07-22
**Confidence:** HIGH on every number below — each was reproduced in this repo at `8cb8458`, not
carried over from a planning document. See §1.0 for one reading that was wrong and is retracted.

---

## 1. Measurement — and a correction to an earlier reading of it

`.planning/REQUIREMENTS.md:53-56` and `.planning/research/v2.4-scoping-FINAL.md:85-87` state
**617** findings and **~180** in the vendored tree. The 617 reproduces exactly; the ~180 does not
— the vendored tree owns **193**.

### 1.0 A correction, recorded rather than quietly fixed

An earlier draft of this section claimed the repo's ruff cache was serving stale results, because
runs minutes apart returned 617 and then 620. That claim was **wrong** and is retracted. The cause
was a **concurrent agent committing to this same branch**: commit `8cb8458`
(*perf(docs-guard): compile the contract graph once per report*) landed mid-measurement and moved
three `E501` findings in `tools/docs_guard/impact.py` / `test_impact.py`. Warm and cold runs at
the same commit agree exactly (both `Found 424 errors.` after the exclusion, verified).

Two things follow, and both are kept:

1. **The gate still passes `--no-cache`.** Not because the cache was caught misbehaving — it was
   not — but because CI is always cold and local is usually warm, and removing the cache as a
   variable costs nothing at this repo's size (a full cold run is ~1s). A gate should have one
   fewer thing that can differ between the two places it runs.
2. **The baseline is a moving target while sibling phases are in flight.** Phases 30–35 commit to
   this branch. This is not a defect of the design: a sibling commit that *removes* findings
   lowers a count, which the ratchet accepts, and one that *adds* findings is exactly what the
   ratchet exists to catch. But the recorded baseline must be generated immediately before it is
   committed, and re-verified at phase close.

All numbers below are measured at `8cb8458`+ with ruff **0.15.20**, `--no-cache`, and are stable
across three consecutive runs.

### 1.1 Full breakdown (617 total)

| Rule | Count | Fixable |
|---|---:|---|
| E501 line-too-long | 304 | no |
| E702 multiple-statements-on-one-line-semicolon | 202 | no |
| E701 multiple-statements-on-one-line-colon | 65 | no |
| I001 unsorted-imports | 22 | **safe fix** |
| E401 multiple-imports-on-one-line | 7 | **safe fix** |
| F401 unused-import | 6 | **safe fix** |
| UP017 datetime-timezone-utc | 4 | **safe fix** |
| E722 bare-except | 2 | no |
| B007 unused-loop-control-variable | 1 | no |
| B904 raise-without-from-inside-except | 1 | no |
| B905 zip-without-explicit-strict | 1 | no |
| F841 unused-variable | 1 | no |
| UP034 extraneous-parentheses | 1 | **safe fix** |

### 1.2 By directory (top buckets, full tree)

Measured before commit `8cb8458` landed, so `tools/docs_guard` is 3 higher here than it is now;
the shape is what matters.

| Path bucket | Findings |
|---|---:|
| `docs/references/opencode-matt-workflows` | **193** |
| `tools/task_control/tests` | 90 |
| `tools/evidence/capture.py` | 89 |
| `tools/task_control/__main__.py` | 49 |
| `tools/harness_lint/tests` | 30 |
| `tools/task_control/manager.py` | 27 |
| `tools/lifecycle_eval/runner.py` | 20 |
| `tools/task_control/phase_gate.py` | 13 |
| `tools/risk_router/router.py` | 11 |
| everything else | ≤ 9 each |

### 1.3 The vendored tree, exactly

193 findings — **not** the ~180 the requirement estimated. Per-rule inside the vendored tree:
E702 100, E701 45, E501 30, E401 7, I001 7, E722 2, UP017 2. It is 7 third-party `*.py` files
(`configure-models.py`, `doctor.py`, and five under subdirectories) vendored as reference material.
Notably it owns **all** 7 E401 and **both** E722 findings in the repo — the two rule classes that
disappear entirely once it is excluded.

### 1.4 The three states, measured

| State | Total | Composition |
|---|---:|---|
| today | 617 | — |
| after `extend-exclude` of the vendored tree | **424** | −193 |
| after the 24 safe autofixes | **400** | −24 (I001 15, F401 6, UP017 2, UP034 1) |

400 is the genuine remainder the baseline must hold:
`E501 274, E702 102, E701 20, B007 1, B904 1, B905 1, F841 1`.

---

## 2. Where ruff is configured

Root `pyproject.toml:43-49` — one `[tool.ruff]` block for the whole workspace:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"
extend-exclude = [".dotnet", ".venv", "bin", "obj"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

No per-member `[tool.ruff]` overrides exist (grepped: `tools/*/pyproject.toml` and
`libs/python/pyproject.toml` declare only `[project]` + `[tool.uv]`). There is **no**
`.pre-commit-config.yaml` in this repo, so pre-commit is not a second wiring site to keep in sync.

`ruff~=0.15` is pinned in the root dev dependency group (`pyproject.toml:19`); the installed
version resolves from `uv.lock`.

---

## 3. Ruff today is not a gate anywhere

Grepped for `ruff` across `.github/workflows/`: **zero hits**. `ci.yml` has 11 jobs
(`setup`, `lang-tests`, `contract-check`, `drift`, `golden`, `core-suite`, `lifecycle-eval`,
`emit-drift`, `stale-derived`, `docs-guard`, `workspace`) fanning into `gate` at `ci.yml:340`.
None of them runs a linter.

Ruff appears only in:
- `harness/commands/lint.md` — the in-session `/lint` command, `!`ruff check .`` — advisory, and
  currently *always* red, which is worse than absent: an operator who runs `/lint` learns to
  ignore it.
- per-plan verification steps in `.planning/**` (`ruff check <the touched files>`), i.e. scoped to
  a plan's own diff, never repo-wide.

That is the whole of DEBT-01: a lint that has never been able to fail anything.

---

## 4. Design of the ratchet

### 4.1 What the counts are keyed by — decided: **per-rule totals, repo-wide**

Three candidates were considered:

| Keying | Catches | Brittleness |
|---|---|---|
| single global total | a net increase | none |
| **per-rule totals** | a net increase *in any rule class*, and any brand-new rule class | none — rename-proof |
| per-(file, rule) | also a same-rule swap between files | **high** — every file rename is an "increase" |

Per-(file, rule) is the strictest and was rejected. A rename produces a new key with a non-zero
count, which the ratchet must read as an increase; the only escape is a `--update` that can raise
counts, which is precisely the escape hatch that makes a ratchet decorative. Per-rule totals are
rename-proof, so `--update` can be made structurally incapable of raising a count — a stronger
overall control than a stricter key with a soft update path.

The residual gap is honest and small: deleting one E501 in file A while adding one in file B is a
wash the gate permits. It is recorded as a known limit, not hidden.

### 4.2 New rule classes fail closed

A rule code **absent from the baseline** is treated as baseline 0. A ruff minor bump that adds a
check under `E`/`F`/`I`/`UP`/`B`, or a genuinely new violation class, therefore reds the gate on
first appearance rather than being silently absorbed. This is the intended behaviour: the remedy
is to fix it or to record it in a reviewed baseline commit.

### 4.3 `--update` cannot be used to silence a regression

`--update` recomputes and rewrites the baseline, but **refuses (exit 3) if any rule's count would
increase**. Combined with 4.1's rename-proof keying, there is no ordinary path by which the
committed baseline grows. Growing it requires hand-editing a committed JSON file, which is visible
in review — the same posture the repo already takes with `uncovered_max` in the docs-guard ledger
(`tools/docs_guard` never raises its own ratchet either).

### 4.4 Invocation shape

`[sys.executable, "-m", "ruff", "check", ".", "--no-cache", "--output-format=json"]` run with
`cwd=REPO_ROOT`.

- `python -m ruff` rather than a bare `ruff` on `PATH`: the ruff wheel ships `ruff/__main__.py`,
  so this resolves through the same interpreter the workspace already selected and cannot pick up
  a different ruff from the ambient environment.
- `--no-cache`: §1.0 — CI is always cold, local usually warm; removing the cache as a variable
  costs ~1s and removes a class of "green here, red there".
- JSON, not `--statistics`: parsing a table of right-aligned integers is fragile, and JSON gives
  the per-diagnostic `code` directly. `--statistics` and JSON agree on totals at a fixed commit;
  JSON is preferred because it needs no parsing of a right-aligned text table.
- Ruff exits **1** when findings exist and **2** on a usage/internal error. The tool must
  distinguish these: exit 2 is a broken invocation and must not be reported as "0 findings".
- `code` can be `null` in ruff's JSON (syntax errors). Bucket those under an explicit key rather
  than dropping them.

### 4.5 Package layout

`tools/ruff_baseline/` as a virtual uv workspace member, matching `tools/docs_guard` and
`tools/harness_lint` exactly: `pyproject.toml` (`package = false`, `dependencies = []`),
`__init__.py`, `__main__.py`, the implementation module, `baseline.json`, and `tests/` with a
`conftest.py` that inserts the repo root on `sys.path` (`parents[3]`), copied from
`tools/harness_lint/tests/conftest.py`. `members = ["libs/python", "tools/*"]`
(`pyproject.toml:34`) already globs it in — no members-list edit is needed, but `uv sync
--all-packages` must be re-run and `uv.lock` must stay unchanged (zero new external deps).

---

## 5. CI wiring

New job **`lint`**, placed after `core-suite` in `ci.yml`, shaped like `docs-guard` (its closest
analogue: a tool CLI whose exit code is the gate, plus that tool's own unit tests):

```yaml
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7.0.0
      - uses: astral-sh/setup-uv@v8.3.2
      - name: Sync workspace (all packages)
        run: uv sync --all-packages
      - name: Ruff ratchet — no rule class may grow
        run: uv run python -m tools.ruff_baseline
      - name: Ruff baseline unit tests
        run: uv run pytest tools/ruff_baseline -q
```

and added to `gate.needs` (`ci.yml:340`).

**The job must NOT run a bare `uv run ruff check .`.** That is red today and would make the job
permanently red, which is the same non-gate as having no job at all. The bare check becomes a step
only when the baseline reaches zero.

### 5.1 The unit tests stay out of `core-suite`

`tools/ruff_baseline/tests` is named explicitly in the `lint` job. It is *also* collected by the
root `pytest` run in `core-suite` (root `testpaths = ["libs/python", "tools"]`,
`pyproject.toml:39`) — that is unavoidable and harmless, because the unit tests are hermetic
(they operate on synthetic diagnostic lists and temp baselines, never on the real tree). What is
deliberately **not** written is a pytest that runs the real ratchet: that would make a lint
regression red `core-suite` and `lint` with two different remedies in the output, breaking the
repo's separate-job legibility idiom (`ci.yml:174-176`, `:277-279`).

---

## 6. Proving the gate fails

DEBT-01's thesis is that an unobserved gate is not a gate, so the phase owes a recorded
fail→pass cycle. GitHub Actions cannot be run for this branch on demand here, so the observation
is made against the **same command CI runs**, locally:

1. RED: append a line-too-long to a tracked non-vendored file → `uv run python -m tools.ruff_baseline`
   must exit non-zero and name `E501` with the before/after counts.
2. GREEN: revert → the same command exits 0.

Both runs' verbatim output goes in the plan summary. This is stronger evidence than a green CI
run, which only shows the passing half.

---

## 7. Out of scope, recorded

- **`ruff format --check`** is red today: **25 files would be reformatted**, 248 already
  formatted. DEBT-01 names `ruff check` only. Adding a format gate means either reformatting 25
  files (a large mechanical diff that would collide with in-flight phases 30–33) or a second
  ratchet. Recorded as carried debt, not silently skipped.
- Fixing the 400 genuine findings. E501×274 in particular is a reflow of nearly every long line in
  `tools/`; the requirement explicitly says the remainder is *held*, not fixed.
- `E722`, `E401` — both vanish with the vendored exclusion; nothing to do.
- A pre-commit mirror of the ratchet. No `.pre-commit-config.yaml` exists to mirror into.

---

## 8. Risks

| # | Risk | Mitigation |
|---|---|---|
| R-1 | The baseline is stale by the time it merges, because sibling phases 30–35 commit to this branch | Generate the baseline immediately before committing it and re-verify at phase close. A sibling that removes findings only shrinks a count (accepted); a sibling that adds them is what the ratchet is for (§1.0) |
| R-2 | A ruff minor bump changes counts and reds the gate | Intended (§4.2). The baseline records the ruff version it was generated under, printed on mismatch so the operator sees *why* the numbers moved |
| R-3 | `--update` used to paper over a regression | Structurally refused (§4.3) |
| R-4 | The safe autofixes change behaviour | Only ruff-classified **safe** fixes are applied (`--fix`, never `--unsafe-fixes`); the full 1500-test suite must stay green across that commit, and the 3 hidden unsafe fixes are deliberately left |
| R-5 | The autofix commit collides with phases 30–33 running in parallel | 24 fixes across 16 files, all under `tools/`; it lands as its own atomic commit so a conflict is trivially resolvable |
