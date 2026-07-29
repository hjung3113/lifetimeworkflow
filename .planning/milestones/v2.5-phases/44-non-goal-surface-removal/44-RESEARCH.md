# Phase 44: Non-Goal Surface Removal - Research

**Researched:** 2026-07-29
**Domain:** In-repo deletion + cross-workspace-boundary package relocation (uv workspace, pytest collection scope, emitted-tree projection)
**Confidence:** HIGH — every number below came from a command executed in a scratch clone; nothing is inferred from reading.

## How this was measured

Four scratch clones of `HEAD` (`f353ff1`) under
`/private/tmp/claude-501/.../scratchpad/{w1,w2,w3,w4,w5}`. The real tree was never mutated —
`git status --porcelain` is empty and `git log --oneline -1` is `f353ff1` both before and after.

| Clone | What was applied |
|---|---|
| `w1`, `w2` | CER-09 relocation only (`tools/golden_runner` → `examples/log-parser/golden_runner`) |
| `w3` | CER-08 deletions (committed), then CER-09 on top, then `[pipeline]` |
| `w4` | `[pipeline]` slot removal in isolation |
| `w5` | `secret_scan` removal in isolation; then contract deletions in isolation |

**Baseline on the real tree:** `uv run pytest -q` → **983 tests collected**, green.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `examples/**` is NOT a uv workspace member. Root `pyproject.toml:34` declares
  `members = ["libs/python", "tools/*"]` with `exclude = ["tools/bootstrap"]` — root-scoped globs
  only. Moving `tools/golden_runner` under `examples/log-parser/` therefore removes it from the
  workspace: it stops being installed, and `uv run python -m tools.golden_runner...` stops resolving.
  This is the single hardest thing in the phase and **no other CER-08 deletion has this property**.
- **D-02:** Four live importers already exist in the example and they import the *core* path
  today: `examples/log-parser/tests/{test_value_regression,test_repr_only,test_compare_recorded}.py`
  and `conftest.py:28` all do `from tools.golden_runner.runner import ...`. `conftest.py:3` records
  that these tests were already moved out of `tools/golden_runner/tests/` by an earlier phase — so
  CER-09 finishes a migration that is half-done, it does not start one.
- **D-03:** Relocate to `examples/log-parser/golden_runner/`, NOT to
  `examples/log-parser/tools/golden_runner/`. A second directory named `tools/` under the example
  creates two roots for the same `tools.*` import namespace — an ambiguity that resolves by
  `sys.path` order and would fail differently in CI than locally. A distinct top-level package name
  removes the class of bug entirely.
- **D-04:** Add the relocated package to `[tool.uv.workspace] members` as an explicit path entry.
  This is a DATA row in an existing config key, not a new mechanism — the same reasoning that
  settled Phase 42's D-07 (`tools/**` glob: "a data row, not a mechanism"). It is not surface growth:
  no new gate, tool, contract, or dependency. ⚠ `tools/harness_lint/workspace_check.py` and
  `test_workspace_member_completeness.py` read that glob — the relocated dir MUST carry a
  `pyproject.toml` in the same commit that adds the member, or every `uv` invocation in the repo
  fails and the PreToolUse guards take the session down.
- **D-05:** Root `golden/` (4 files, 16K) folds into `examples/log-parser/golden/`, which already
  exists. The CI `golden` job's step 1 is labelled "root identity golden (converter-agnostic,
  .NET-free)"; once the core makes no parity promise there is no core-side golden to run, so the two
  steps collapse into the example's. Preserve history with `git mv` where the path allows it.
- **D-06:** `secret_scan` is a live PreToolUse hook, not a package. It is `tools/hooks/secret_scan.py`
  + `tools/hooks/tests/test_secret_scan.py` + `harness/plugins/secret-scan.ts` + a
  `HARNESS_SIGNATURES` entry (`merge.py:91`) + an emitted hook-group literal (`merge.py:180`) + prose
  in `harness/commands/review.md:24`. All of it goes, **with no replacement**.
- **D-07:** `merge.py`'s `RETIRED_SIGNATURES` must gain `"tools.hooks.secret_scan"` and must NOT be
  cleared afterwards. `merge.py:111` now carries `("tools.hooks.resume_gate",)` as a permanent
  tombstone — **append, never clear.**
- **D-08:** `tools/adoption_scan` keeps its own secret patterns (`scan.py:54,60`). Deleting the hook
  must not touch adoption's redaction; the proof is that adoption's redaction tests pass **unchanged**.
- **D-09:** `deny-domains.*` deletion self-clears two stale declarations. Both debts close for free;
  do not open a separate task for them.
- **D-10:** `gate-registry.json` finally goes, together with its `DATA_CONTRACT_PATHS` entry
  (`hash.py:32`) and the 5 hyphenated provenance docstrings in `tools/adoption_scan/**`.
- **D-11:** `/component` loses its SECOND "Mandated order" section only.
- **D-12:** `[pipeline]` removal has the widest blast radius in the phase. ⚠ `[[components]]` and the
  TOPO-02 `[contract_graph.relationships]` slot **survive**.
- **D-13:** `tools/memory_ui` (1756 LOC) has no consumer outside itself.
- **D-14:** Every live-tree-rendering test is repaired in the SAME commit as the deletion that
  invalidates it.
- **D-15:** delete/move → `git add` → `git commit -- <pathspec>` → verify → amend-if-red. That red is
  intra-commit and expected; **no commit may END red.**
- **D-16:** `git commit -m "<msg>" -- <pathspec>` — message BEFORE `--`. Never `git add -A` /
  `git add .` / `git commit -a` / `git checkout <ref> -- .`.
- **D-17:** Source-first: edit `harness/**`, then `python -m tools.harness_emit`. Never hand-edit
  `.opencode/**`, `.claude/**`, or root `opencode.json`.
- **D-18:** Run things, don't read them.
- **D-19:** Done-condition as stated in CONTEXT (CER-08 paths gone, stale-checkout drop asserted,
  contracts clean + manifest rebaselined + drift 0, golden stack resolving under
  `examples/log-parser/` with BOTH CI jobs repointed YAML-resolved, `uv run pytest -q` green at every
  commit, emit-drift / stale-derived / ruff ratchet clean, `uv.lock` refreshed).
- **D-20:** No mutation-proof table is owed, except D-19's stale-checkout assertion.
- **D-21:** Report whole-phase LOC from `git diff --shortstat` (measured, not estimated).

### Claude's Discretion

- Plan/task decomposition and wave count (CER-08 deletions and the CER-09 relocation are largely
  independent and may parallelize; the relocation is the long pole).
- Whether the contract deletions ride with their package deletions or take their own commit.
- The exact new package name under `examples/log-parser/` (D-03 fixes the shape, not the spelling).

### Deferred Ideas (OUT OF SCOPE)

- **Projection repair** — `caps.py` frozensets, `emit-manifest.json`, `HARNESS_SIGNATURES` hygiene,
  `docs/reference/**`, `AGENTS.md:52-62`'s golden-path table, `.memory/derived/**` → **Phase 45**.
- **Stale prose in human-owned docs** (`docs/how-to/task-lifecycle.md`, two `docs/explanation/`
  pages, `docs/how-to/README.md`, `docs/adr/README.md`,
  `docs/explanation/agent-workflow-skillset-design-guide.md`) → **Phase 45**.
- **ADR-0008 supersession** → Phase 45, or a human call at milestone close.
- **ROADMAP SC-1 wording (Phase 43)** — should be corrected rather than hand-waived.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CER-08 | Delete the non-goal surface — `secret_scan`, `deny-domains.*`, `gate-registry.json` + their `DATA_CONTRACT_PATHS` entries, `tools/memory_ui`, `tools/strangler_guard` + `/strangler-step`, `/pipeline` + skill `pipeline-map` + `[pipeline].edges`, skill `gate-model`, `/component`'s topology-registration half | §"CER-08 blast radius, measured" gives the exact 26-failure attribution + `file:line` + literal for each repair; §"The `[pipeline]` correction" reverses the stated blast radius |
| CER-09 | Relocate the golden stack to `examples/log-parser/` | §"CER-09: the relocation, proven end-to-end" gives the working `members` spelling, the `uv.lock` recovery command, the three `parents[N]` anchors, the import rewrite, and the two unnamed core consumers (`commit_gate`, `verify-work.md`) that make it a gate deletion, not just a move |
</phase_requirements>

---

## Summary

The phase has **one genuinely hard problem and four surprises**, and the surprises are all in the
same class Phase 43 was burned by: a committed artifact that renders the live tree and carries a
hardcoded expectation, in a place the requirement prose never looked.

**The hard problem is not what CONTEXT thinks it is.** D-01 frames CER-09 as a workspace-membership
problem. Workspace membership turns out to be the *easy* half — one `members` entry, one `uv.lock`
line, and a specific recovery command (`uv lock --upgrade-package`, because plain `uv lock` and
`uv sync` both **hard-fail** after the move and leave the repo uv-dead). The genuinely hard half is
that **`tools/hooks/commit_gate.py:42` — a core PreToolUse guard — imports `tools.golden_runner.runner`
at module level.** GEN-04's `test_core_no_example_dep.py` forbids any core file from referencing
`examples/`, which I verified by mutation. So CER-09 is not a relocation; it is a **relocation plus
the deletion of `commit_gate`'s golden-parity component** — a third of a live gate that neither
CER-08 nor CER-09 names. All 15 `test_commit_gate.py` tests are coupled to it.

**Four other surprises.** (1) `uv run pytest -q` **does not collect `examples/**` at all** — root
`testpaths = ["libs/python", "tools"]`. D-19's "green at every commit" gate is therefore blind to
every example importer; only the CI `golden` job step 2 sees them. This is precisely the
half-landing risk, and it is worse than CONTEXT states. (2) Removing the `[pipeline]` **slot** breaks
**3 tests, none of them in `harness_lint`** — the eight `harness_lint` tests D-12 names go
**vacuously green** instead (`test_pipeline_config.py:59,83` iterate `pipeline(cfg).get("edges", [])`,
so an empty slot means the loop body never runs). Removing the `pipeline()` **loader function** is
the separate, harder change, and it breaks the *instance* at collection. (3)
`test_install_completeness.py`'s module floor is `>= 12` against a live post-CER-08 value of exactly
**12** — zero slack — and CER-09 drives it to **11**. (4) The existing
`test_retired_signature_group_is_dropped_from_a_stale_checkout` reads `RETIRED_SIGNATURES[0]` only; I
proved by mutation that **deleting `secret_scan` from the tuple leaves the test green**. D-07's
"one line plus one assertion" is wrong.

**Primary recommendation:** sequence the phase as six commits with CER-08's independent deletions
first and the CER-09 relocation last, and treat `commit_gate`'s golden component + the
`examples/**`-invisible test set as first-class scope, not incidental repair.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Golden equivalence execution | Instance (`examples/log-parser/`) | — | ADR-0002(b); `resolve_dotnet()` is language-specific |
| Golden constitution data (`.verified` baselines) | Instance constitution plane | CODEOWNERS | `/examples/*/golden/` already in CODEOWNERS |
| Pre-commit gating (drift + polyglot) | Core (`tools/hooks/commit_gate.py`) | — | Language-neutral; survives |
| Pre-commit gating (golden parity) | **Deleted** | — | Cannot live in core (GEN-04) and must not be re-homed in the instance (hooks are core-emitted) |
| Topology DATA (`[pipeline].edges`) | Instance `project.toml` | — | Core default slot removed; instance keeps 3 edges |
| Topology MECHANISM (`loader.pipeline()`) | Core `tools/harness_config` | — | **Must survive** — the instance imports it |
| Workspace member resolution | Root `pyproject.toml` + `workspace_check.py` | — | Explicit path entry works; glob logic handles it unchanged |
| Emitted runtime projection | Core `tools/harness_emit` | — | `emit-manifest.json` self-prunes |

---

## CER-09: the relocation, proven end-to-end

### 1. The `members` spelling works, but `uv.lock` blocks it first

**Command run** (clone `w2`, from clean `f353ff1`):

```bash
git mv tools/golden_runner examples/log-parser/golden_runner
# pyproject.toml:34
members = ["libs/python", "tools/*", "examples/log-parser/golden_runner"]
```

Then `uv sync --all-packages`:

```
error: Failed to generate package metadata for `logparser-golden-runner==0.0.0 @ virtual+tools/golden_runner`
  Caused by: Distribution not found at: .../w2/tools/golden_runner
```

`uv.lock:254` pins `source = { virtual = "tools/golden_runner" }`. **Both `uv lock` and
`uv sync --all-packages` fail with the same error** — `uv lock` does *not* self-heal. In that state
every `uv` invocation in the repo is dead, which is the same self-sealing outage
`workspace_check.py:22-27` documents, reached by a different route (stale lock, not missing
`pyproject.toml`). `workspace_check.py` **will not detect it** — it only checks for a missing
`pyproject.toml`.

**The recovery command, verified as the first `uv` command after the move:**

```bash
uv lock --upgrade-package logparser-golden-runner   # → "Resolved 52 packages in 5ms"
uv sync --all-packages                              # → succeeds
```

Resulting diff: `uv.lock | 2 +-` — **exactly one line** (`source = { virtual = "examples/log-parser/golden_runner" }`).
`rm uv.lock && uv lock` also works but rewrites the whole file; prefer the targeted flag.

> **Planner note:** this is a hard ordering constraint. The `git mv`, the `members` edit, **and**
> `uv lock --upgrade-package` must be one atomic step. Between the `git mv` and the lock refresh,
> the agent's own PreToolUse guards are down.

**[VERIFIED: executed in scratch clone w2]**

### 2. The relocated package's `pyproject.toml` survives verbatim

`tools/golden_runner/pyproject.toml` is `name = "logparser-golden-runner"`, `dependencies = []`,
`[tool.uv] package = false`. **It needs no change at all** — `uv sync --all-packages` succeeded with
it byte-identical after the move. Only its two comment lines (`:10-11`, naming
`python -m tools.golden_runner.runner`) are stale prose.

Because `package = false`, workspace membership confers **no import resolution whatsoever** — nothing
is installed. `import golden_runner` works only via `sys.path`. Membership buys dependency
resolution and `uv sync` participation, nothing more.

**[VERIFIED: `uv sync --all-packages` exit 0 with unmodified member pyproject]**

### 3. `workspace_check.py` and its pytest twin handle an explicit path entry unchanged

`unresolvable_members()` (`workspace_check.py:113-122`) does `for candidate in sorted(repo_root.glob(pattern))`.
`Path.glob()` with a wildcard-free pattern returns the literal path when it exists, so an explicit
entry is checked exactly like a globbed one: it must contain `.py` files and a `pyproject.toml`, or
it is reported BROKEN. **No code change is needed in either file for the explicit entry to be
covered.** `stale_excludes()` is untouched (`exclude` still names only `tools/bootstrap`, which
still exists).

Two **prose** repairs are owed in these same two files, and they are `secret_scan`'s, not the
relocation's:

| File:line | Current text | After |
|---|---|---|
| `tools/harness_lint/workspace_check.py:22` | `` (``contract_guard``, ``secret_scan``, ``commit_gate``) `` | drop `secret_scan` |
| `tools/harness_lint/tests/test_workspace_member_completeness.py:13` | `` (``contract_guard``, ``secret_scan``, ``commit_gate``) `` | drop `secret_scan` |

Neither is functional; no test fires on them. (Phase 43's WR-08 made the identical repair for
`resume_gate` in these same two lines.)

**[VERIFIED: read + glob semantics confirmed by the passing `uv sync` in w2]**

### 4. The four example importers DO resolve under `uv run pytest` — after three edits

Post-move with imports untouched, `uv run pytest examples/log-parser/tests -q`:

```
ImportError while loading conftest '.../examples/log-parser/tests/conftest.py'
examples/log-parser/tests/conftest.py:28: in <module>
    from tools.golden_runner.runner import resolve_dotnet
E   ModuleNotFoundError: No module named 'tools.golden_runner'
```

It fails **loudly at conftest load**, taking all example tests with it. Good — this one cannot half-land.

The three edits that make it pass:

**(a) Three `parents[N]` anchors, all off by one after the move.** This is the item CONTEXT never
names and it is load-bearing for security, not just imports:

| File:line | Now | After move | Why it matters |
|---|---|---|---|
| `golden_runner/runner.py:29` | `parents[2]  # golden_runner -> tools -> repo root` | `parents[3]` | `REPO_ROOT` feeds `_LIBS_PYTHON` (sys.path), `GOLDEN_DIR`, the **T-06-02 path-confinement allowlist** (`runner.py:98`), and `run_workspace_golden_case`'s `member_root` resolution (`:283`, which resolves `workspace.toml` member paths **relative to repo root**). Left at `parents[2]` it silently becomes `examples/` — a *narrowed* confinement root and a broken workspace-member resolution. |
| `golden_runner/tests/conftest.py:27` | `parents[3]` | `parents[4]` | `repo_root` fixture |
| `golden_runner/tests/test_workspace_golden.py:33` | `parents[3]` | `parents[4]` | `_REPO_ROOT` |

**(b) Import rewrite `tools.golden_runner` → `golden_runner`** in 11 files (script-verified):
`examples/log-parser/tests/{conftest,test_value_regression,test_repr_only,test_compare_recorded}.py`
and `examples/log-parser/golden_runner/{runner,approve}.py` +
`golden_runner/tests/{conftest,test_approve_gate,test_sample_loop,test_identity_converter,test_workspace_golden}.py`.

**(c) `sys.path` gains the instance root.** Both conftests currently insert `_REPO_ROOT` and
`_LIBS_PYTHON`; they need `_REPO_ROOT / "examples" / "log-parser"` as a third entry. This is the
same `sys.path.insert` idiom already in use — **not a new mechanism**.

**Result, both suites, under `uv run`:**

```
uv run pytest examples/log-parser/tests -q            → 14 passed in 3.80s
uv run pytest examples/log-parser/golden_runner -q    → 17 passed in 0.02s
```

**[VERIFIED: executed in scratch clone w2]**

### 5. ⚠ The `sys.path` idiom does NOT mask a broken membership — but `testpaths` does something worse

The specific risk the prompt asked about (conftest `sys.path` masking broken workspace membership in
a local run while `uv run` fails in CI) **does not exist**, because membership never provided import
resolution for a `package = false` member in the first place. Local and `uv run` behave identically.

**The real masking is different and larger.** Root `pyproject.toml:38`:

```toml
testpaths = ["libs/python", "tools"]
```

```
$ uv run pytest --collect-only -q | grep -c "examples/"
0
```

**`uv run pytest -q` (983 tests) collects ZERO tests from `examples/**`.** Every example importer,
including all four golden importers and `test_pipeline_topology.py`, is invisible to the command
D-19 names as the per-commit gate. They run **only** in CI `golden` step 2
(`uv run pytest examples/log-parser/tests`, `ci.yml:170`) and CI `workspace`
(`ci.yml:320`).

**Planner implication:** D-19's "`uv run pytest -q` green at every commit" is **not sufficient** for
this phase. Any commit touching `examples/**` or `tools/harness_config` must additionally run:

```bash
uv run pytest examples/log-parser/tests examples/log-parser/golden_runner -q
```

**[VERIFIED: `pytest --collect-only -q | grep -c examples/` → 0 on the real tree]**

### 6. 🔴 `commit_gate` — a core PreToolUse guard — imports `golden_runner`. This is the phase's biggest unnamed item.

`tools/hooks/commit_gate.py:42`:

```python
from tools.golden_runner.runner import GOLDEN_DIR, resolve_dotnet, run_golden_case
```

HOOK-03 composes **three** components (`:240`): `check_drift()`, `check_polyglot()`, `check_golden()`.
The third is `golden_runner`. After the move, the full core suite dies **at collection** — the only
collection error the entire phase produces:

```
ERROR collecting tools/hooks/tests/test_commit_gate.py
tools/hooks/commit_gate.py:42: ModuleNotFoundError: No module named 'tools.golden_runner'
!!!! Interrupted: 1 error during collection !!!!
```

**Option "just repoint the import at the example" is forbidden, and I proved it.** I edited
`commit_gate.py:42` to `sys.path`-insert `examples/log-parser` and import `golden_runner.runner`,
then ran GEN-04:

```
FAILED tools/harness_lint/tests/test_core_no_example_dep.py::test_core_has_no_example_dependency
E  AssertionError: core→example dependency/prose leak:
E    tools/hooks/commit_gate.py:42: ... / "examples/log-parser"))
```

`_PATH_TOKENS = ("examples/", "components/toy-converter")` over `_CORE_ROOTS = ("tools","harness","libs")`
(`test_core_no_example_dep.py:47,53`). There is no exemption available: the only sanctioned
instance-pointer file is `harness/project.toml`.

**Therefore the golden-parity component of `commit_gate` must be deleted.** Surface:

| Item | `file:line` |
|---|---|
| Import | `commit_gate.py:42` |
| `discover_golden_cases()` | `commit_gate.py:199-203` |
| `check_golden()` | `commit_gate.py:206-228` |
| Composition list | `commit_gate.py:240` — `[check_drift(), check_polyglot(staged_files()), check_golden()]` |
| Module docstring, component 3 | `commit_gate.py:14-17` |
| Docstring cross-refs | `commit_gate.py:9,10,157` ("polyglot and golden stay HARD") |
| Test module docstring | `tools/hooks/tests/test_commit_gate.py:8,13` |
| Dedicated tests | `test_dotnet_absent_skips_golden_not_fail` (`:117`), `test_golden_skip_does_not_suppress_drift` (`:130`) |

⚠ **All 15 `test_commit_gate.py` tests are coupled**, not just the two named. They monkeypatch
module-level names on `commit_gate`; my crude removal reddened all 15. The planner should budget the
whole file, and must preserve the `GOLDEN_APPROVE_HUMAN` drift-ratification path (`:155-171`) — that
is `contract_guard`'s precedent and is **not** golden-specific despite the env-var name.

This is a **gate reduction the ROADMAP's "+0 gates" success criterion #8 should be read against**:
it is a removal, so it does not violate "+0", but it is a third gate component disappearing without
being named in either requirement. Worth a recorded consequence line.

**[VERIFIED: collection error reproduced; GEN-04 failure reproduced by mutation in w3]**

### 7. The second unnamed core consumer: `verify-work.md`, and the module-floor trap it sits on

Two core files still name `tools.golden_runner` after the commands/skills are relocated:

| `file:line` | Content |
|---|---|
| `harness/commands/verify-work.md:44` | the `!`-prefixed golden loop: `cases=(golden/*/) … uv run python -m tools.golden_runner.runner "$c"` |
| `harness/skills/python-conventions/SKILL.md:35` | `` Invoke tools by module path (`python -m tools.golden_runner.runner`) `` — a *style example* |

These two are coupled to `test_install_completeness.py` in a way that traps you either direction.
`_discover_module_refs` (`:31-49`) globs `harness/commands/**/*.md`, `harness/skills/**/*.md`,
`.github/workflows/*.yml`; `test_every_referenced_tools_module_lands_in_applied_target` (`:116-120`)
**resolves** each ref to a real `.py`; `test_..._floor` (`:103`) asserts `>= 12` distinct top-level
packages.

Measured, three states:

| State | top-level count | Result |
|---|---|---|
| Real tree `f353ff1` | 12 | floor passes |
| After CER-08 deletions only | **12** | floor passes — **zero slack** |
| After CER-09, both refs left in place | 12 | floor passes, but **`tools.golden_runner.runner` fails to resolve** → `test_every_referenced_tools_module_lands_in_applied_target` FAILS |
| After CER-09, both refs removed | **11** | resolve passes, **floor `>= 12` FAILS** |

Verbatim resolve failure:

```
E AssertionError: tools.golden_runner.runner does not resolve to any real .py file in this checkout
  (tried .../tools/golden_runner/runner.py, .../runner/__main__.py, .../runner/__init__.py)
```

**Both refs must go AND the floor must drop 12 → 11 in the same commit.** The floor's own docstring
(`:98-100`) already licenses this: *"This is a vacuity guard, not a census — do not raise it back
toward the live value."* Lowering is sanctioned; raising is not.

For `verify-work.md:44` specifically: after D-05 folds root `golden/` away, the glob `cases=(golden/*/)`
matches nothing and the step prints `SKIP: no golden cases — no-op (exit 0)`. It would degrade
**silently and greenly** if merely left alone — a permanently no-op gate step. Delete the block
rather than let it become a claimed control that does nothing. Note `harness/commands/verify-work.md`
edits invalidate `test_emit_determinism.ambr` (§ below) and `verify-work.md:25`'s bare `ruff check .`
is a *pre-existing* separate defect (Phase 43 IN-05) — do not fix it here.

**[VERIFIED: all four counts measured in w3 by executing `_discover_module_refs`]**

### 8. `golden/` fold: no filename collision, but two real consequences

```
golden/                              examples/log-parser/golden/
  README.md                            repr-only/
  sample/{meta.yaml,input/,expected/}  value-regression/
```

**No collision** — `sample` vs `repr-only`/`value-regression` are distinct. `git mv golden/sample
examples/log-parser/golden/sample` is clean.

**Consequence A — a constitution-plane downgrade, measured:**

```python
resolve_path(CONSTITUTION_GLOBS, 'golden/sample/meta.yaml')                      -> 'deny'
resolve_path(CONSTITUTION_GLOBS, 'examples/log-parser/golden/repr-only/meta.yaml') -> 'allow'
```

`CONSTITUTION_GLOBS = ["contracts/**", "docs/adr/**", "golden/**", "docs/glossary.md"]`
(`tools/hooks/contract_guard.py:53`) is repo-root-anchored. Moving the 4 files takes them from
**agent-write-denied to agent-write-allowed** — an agent could edit a `.verified` baseline directly
after the fold, which is exactly what P9 "machines gate, humans ratify" exists to prevent. The
example's existing golden tree already has this property today, so it is not a regression *for the
example*, but it **is** a loss for the 4 moved files. CODEOWNERS already covers it at merge time
(`.github/CODEOWNERS`: `/examples/*/golden/  @hjung3113`), so the merge-time gate holds; only the
in-session gate is lost. Recommend recording it as an accepted consequence rather than widening
`CONSTITUTION_GLOBS` (widening would be surface growth against SC-8).

**Consequence B — `/golden/` becomes a stale CODEOWNERS entry** (`.github/CODEOWNERS`, the
`/golden/  @hjung3113` line) and **ADR-0001:48 is contradicted**: it declares the constitution plane
as `contracts/`, `golden/`, `docs/adr/`, `docs/glossary.md`, and `.github/CODEOWNERS`'s header says
"this file must not drift from that list." This is the **Phase-43 CR-03 class** (an accepted ADR left
describing a deleted structure). ADRs are append-only + CODEOWNERS-gated → **raise in the PR, do not
edit**; the ADR repair belongs with Phase 45's ADR-0008 work.

**[VERIFIED: `resolve_path` executed against live `CONSTITUTION_GLOBS`; CODEOWNERS + ADR-0001:48 read]**

### 9. CI: `gate.needs` is unchanged at 10 — ruamel-resolved

```python
from ruamel.yaml import YAML          # ruamel 0.19.1, already resolved — no PyYAML added
d = YAML().load(open('.github/workflows/ci.yml'))
```

```
jobs:       ['setup','lang-tests','contract-check','drift','golden','core-suite','lint',
             'emit-drift','stale-derived','workspace','gate']
gate.needs: ['setup','lang-tests','contract-check','drift','golden','core-suite','lint',
             'emit-drift','stale-derived','workspace']   count = 10
needs - jobs: set()
```

**Because the `golden` job is repointed rather than deleted, `gate.needs` stays exactly as-is —
10 entries, no edit.** If a future plan deletes the job instead, `needs` drops to 9 and
`test_every_job_is_in_the_fan_in` (`test_ci_lint_gate.py:72-80`) would **not** catch a stale entry —
it is `declared <= fan_in`, subset-only (Phase 43 IN-03). Assert `needs` count explicitly.

Two `run:` lines need repointing:

| `ci.yml` | From | To |
|---|---|---|
| `:168` | `uv run pytest tools/golden_runner` | `uv run pytest examples/log-parser/golden_runner` |
| `:320` | `… tools/golden_runner/tests/test_workspace_golden.py …` | `… examples/log-parser/golden_runner/tests/test_workspace_golden.py …` |

Plus the two comment lines at `:155-156` and the step name at `:167` ("Golden — root identity
(converter-agnostic)"), which describes a step that no longer exists. Per D-05 the two golden steps
collapse into one; the job itself and its `setup-dotnet` step stay.

**[VERIFIED: ruamel resolution executed]**

---

## The `[pipeline]` correction — D-12's blast radius is inverted

D-12 says "eight `tools/harness_lint/tests/*` read the topology, including `test_pipeline_config.py`
(the consistency gate, **which dies with the slot**)". **Measured, that is not what happens.**

Clone `w4`, `[pipeline]` table removed from `harness/project.toml`, nothing else changed:

```
FAILED tools/harness_config/tests/test_loader.py::test_pipeline_passthrough
FAILED tools/harness_config/tests/test_topology_relationships.py::test_lowers_linear_default_to_single_relationship
FAILED tools/workspace_config/tests/test_endpoints.py::test_core_pipeline_edges_stay_single_repo
3 failed, 980 passed
```

**Three failures, none in `harness_lint`.** Directly:

```
$ uv run pytest tools/harness_lint/tests/test_pipeline_config.py \
      tools/harness_lint/tests/test_orchestrator_topology.py \
      tools/harness_lint/tests/test_conductor_graph_render.py \
      tools/harness_lint/tests/test_contract_graph_config.py -q
14 passed
```

**They pass VACUOUSLY.** `test_pipeline_config.py:59` and `:83` are
`for edge in pipeline(cfg).get("edges", []):` — with the slot gone the loop body never executes and
the assertions inside are never reached. This is the "claimed control that does not exist" pattern
the milestone was convened to remove, and it would ship **green**. `test_pipeline_edges_are_well_formed`
(`:50`) and `test_edge_contracts_have_a_tracked_schema` (`:73`) must be **deleted with the slot**,
not left passing.

### Three distinct things, three different consequences

| Change | Breaks | Kind |
|---|---|---|
| Delete `[pipeline]` **table** from `harness/project.toml:77-80` | 3 tests (above) | runtime assertion |
| Delete `harness/commands/pipeline.md` | 3× `test_conductor_graph_render.py` — `FileNotFoundError: harness/commands/pipeline.md` (it reads the file at `:29`) | runtime |
| Delete `loader.pipeline()` + the `tools.harness_config` re-export | 🔴 **the instance**, at **collection** | collection error |

The third is the trap. `examples/log-parser/tests/test_pipeline_topology.py:20`:

```python
from tools.harness_config import components, languages, load_project, pipeline
```

`examples/log-parser/project.toml:67-71` declares **3 real `[pipeline]` edges** (parser→converter→
scheduler→collector). The instance legitimately uses the linear-topology model. Removing the loader
function:

```
E ImportError: cannot import name 'pipeline' from 'tools.harness_config'
!!!! Interrupted: 1 error during collection !!!!
```

…and **`uv run pytest -q` never sees it** (§5). It would land green and break only CI `golden` step 2.

**Recommendation:** delete the core `[pipeline]` **DATA** (`harness/project.toml:77-80`), delete
`/pipeline` + `pipeline-map`, and **keep `loader.pipeline()` as a mechanism**. This is symmetric with
D-12's own carve-out for `[[components]]` and `[contract_graph.relationships]` — the slot's *default
data* is the non-goal, not the reader. If the planner insists on removing the passthrough, the
instance test and its 5 assertions must be rewritten in the same commit and the CER-09 CI step must
be run to prove it.

### `effective_relationships()` survives, but returns empty

```python
WITH    [pipeline]: [{'id': 'pipeline/greeting/source->sink', 'contract': 'greeting',
                      'authority': 'source', 'dependents': ['sink']}]
WITHOUT [pipeline]: []
```

**No crash — TOPO-02's seam is structurally intact**, as D-12 requires. But the generic-default
topology's *only* relationship came from the lowered `[pipeline]` edge, so the core default graph
becomes empty. `test_lowers_linear_default_to_single_relationship`
(`tools/harness_config/tests/test_topology_relationships.py`) asserts the non-empty case against the
live config and must be narrowed to its synthetic-fixture half (`:74`, `:95-96` already construct
their own `"pipeline"` dicts — those keep working and are the real control).

**[VERIFIED: all runs executed in w4]**

---

## CER-08 blast radius, measured

### The raw deletion run

Clone `w3`, `git rm` of: `tools/memory_ui`, `tools/strangler_guard`, `tools/hooks/secret_scan.py`,
`tools/hooks/tests/test_secret_scan.py`, `harness/plugins/secret-scan.ts`,
`harness/commands/{strangler-step,pipeline}.md`, `harness/skills/{pipeline-map,gate-model}`,
`contracts/harness/security/deny-domains.{json,schema.json}`,
`contracts/harness/task-control/gate-registry.json`. Then `uv lock && uv sync --all-packages`:

```
26 failed, 898 passed in 11.52s
```

> ⚠ Deleting a workspace member also requires `uv lock` + `uv sync --all-packages`. My first run
> without it produced two *spurious* `ModuleNotFoundError` collection errors for `tree_sitter` /
> `networkx` (deps of the surviving `tools/memory_regen`). A planner reading only that output would
> chase the wrong bug.

### 🔴 `pytest --collect-only` is blind to 26 of the 27 failures

```
$ uv run pytest --collect-only -q      # after all CER-08 deletions
924 tests collected in 0.15s           # ZERO errors
```

**Every CER-08 failure is a runtime assertion or a runtime `FileNotFoundError`, not a collection
error.** The single collection error in the whole phase is `commit_gate` (§6), which belongs to
CER-09. A `--collect-only` smoke check is therefore worthless as this phase's guard rail; only a
full `uv run pytest -q` sees the damage.

### Per-item attribution with `file:line` and literal

Attribution is from **isolated** runs (contracts alone in `w5`; `[pipeline]` alone in `w4`), not from
splitting the combined 26.

#### A. `caps.py` `EXPECTED_SKILLS` — hard-fails the emitter before it writes

`tools/harness_lint/caps.py:132-147` — frozenset of **12**. Loses `pipeline-map`, `gate-model`,
`golden-testing`, `golden-debug` → **8**.

```
$ uv run python -m tools.harness_emit
tools.harness_emit.generate.HarnessEmitError: skill set drift — missing ['gate-model', 'pipeline-map'], unexpected []
  generate.py:362  validate.check_skill_set({name for name, _, _, _ in skills})
  validate.py:187  _fail(...)
$ echo $?
1
$ git status --porcelain .claude .opencode
(empty)
```

**Confirmed: exit 1, zero bytes written.** D-14's claim is exact. Consequence: `caps.py` must be
edited in the **same commit** as the skill deletions, or the emitter cannot run at all and every
downstream emitted-tree test fails as collateral. Also update the comment block at `:125-131`, which
narrates the set's history and currently says "The twelve entries below are the whole set."
Companion assertion: `tools/harness_lint/tests/test_skills.py:56` — `assert names == set(EXPECTED_SKILLS)`
(set equality, not subset — stays strict).

#### B. Emitted-tree tests (13 failures) — all downstream of A

`test_coexist.py` ×5, `test_emit_determinism.py` ×4, `test_manifest.py` ×4, `test_opencode_config.py` ×1.

The count literal:

```python
tools/harness_emit/tests/test_coexist.py:70  assert len(opencode_cmds) == 21, f"expected 21 opencode commands, got {len(opencode_cmds)}"
tools/harness_emit/tests/test_coexist.py:71  assert len(claude_cmds)   == 21, f"expected 21 Claude commands, got {len(claude_cmds)}"
tools/harness_emit/tests/test_coexist.py:41  """21 commands land in ...   <- docstring, same literal
```

Live: `ls harness/commands/*.md | wc -l` → **21**. Removing `pipeline`, `strangler-step`, `golden`,
`golden-approve` → **17**. Three sites (`:41` docstring, `:70`, `:71`).
Skills: `ls -d harness/skills/*/ | wc -l` → **12** → **8**.

**`emit-manifest.json` needs no hand edit.** It carries 19 rows matching the deleted surface, and
`manifest.py:64-80` prunes paths that leave the owned set on re-emit (Phase 43 REVIEW, verified-clean
section). Re-emit handles it.

#### C. `test_emit_determinism.ambr` — the widest-reach snapshot

`tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` renders command/skill/agent
**bodies**. It carries `tools.golden_runner` at **lines 1367, 1374, 1392, 1404, 1411, 1429, 1443,
1452, 1477, 1486, 2236, 2284, 2418, 2477, 2786, 2830, 2872, 2887, 2906, 2910, 2919, 3160** — 22
sites, spanning `/golden`, `/golden-approve`, `/strangler-step`, `/verify-work`, `gate-model`,
`golden-debug`, `golden-testing`, `python-conventions`.

⚠ **Any** edit to `harness/{agents,commands,skills}/**` invalidates it, including the two prose-only
repairs in §7 (`verify-work.md:44`, `python-conventions/SKILL.md:35`). Regenerate with
`--snapshot-update` **in the same commit** as each `harness/` edit. There is no way to batch this
safely across commits.

#### D. `docs_sync` — 3 failures (isolated to the contract deletions)

```
FAILED tools/docs_sync/tests/test_docs_sync_determinism.py::test_render_matches_committed_snapshot
FAILED tools/docs_sync/tests/test_docs_sync_determinism.py::test_seed_schemas_map_one_to_one_to_pages
FAILED tools/docs_sync/tests/test_docs_sync_determinism.py::test_prune_removes_orphan_pages_preserves_readme
```

`tools/docs_sync/tests/test_docs_sync_determinism.py:29-39` — `EXPECTED_PAGES` frozenset of 7,
loses `"deny-domains"` (`:31`) → 6. Compared with `==` at `:118` (set equality — stays strict).
Also: `docs/reference/deny-domains.md` is deleted by `docs_sync`'s prune on regeneration, and
`tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr` needs `--snapshot-update`.

#### E. `contract_hash` — 1 failure, and `DATA_CONTRACT_PATHS` empties completely

`tools/contract_hash/hash.py:30-34` currently:

```python
DATA_CONTRACT_PATHS = (
    Path("harness/task-control/gate-registry.json"),
    Path("harness/security/deny-domains.json"),
)
```

Both entries go → **the tuple is empty**. `test_build_manifest_includes_ratified_data_contracts_and_detects_registry_mutation`
(`tools/contract_hash/tests/test_hash.py:93-111`) — including its `:105` literal
`{"contracts/harness/task-control/gate-registry.json"}` and its `:107-109` negative control — tests a
mechanism with zero data and must be **deleted entirely**, not narrowed again. (Phase 43 already
narrowed it once; there is nothing left to narrow to.)

Manifest **9 → 6 entries**, verified:

```
$ uv run python -m tools.contract_hash.hash > contracts/.hashes/manifest.json
$ # → 6 entries
$ uv run python -m tools.contract_drift.drift
contract-drift: OK — live manifest matches the committed baseline.   (exit 0)
```

Both `contracts/harness/security/` and `contracts/harness/task-control/` **cease to exist** — those
files were their only contents.

Open question for the planner: leave `DATA_CONTRACT_PATHS = ()` as an empty extension seam, or delete
the mechanism? CER-08 says "their `DATA_CONTRACT_PATHS` **entries**" → entries only. Recommend
keeping the empty tuple with a comment, and deleting the test.

#### F. `memory_regen` contracts-index — 1 failure

`tools/memory_regen/tests/test_contracts_index.py::test_render_matches_committed_snapshot` — the
`.memory/derived/contracts-index.md` syrupy snapshot. Regenerate the derived file **and** the `.ambr`.

Second, separate hit: `tools/memory_regen/tests/test_agents_md.py:49` asserts
`"tools.golden_runner"` (among `"tools.contract_drift"`, `"uv run pytest"`) appears in `AGENTS.md`.
CER-09 relocates the golden path table (`AGENTS.md:66-67`) — Phase 45 owns the `AGENTS.md`
reconciliation, but **this assertion goes red the moment those rows move**, so the planner must
either keep the rows until 45 or repair `:49` here. Flagging as a 44/45 boundary collision.

#### G. `test_dispositions.py` — the intra-commit red, confirmed

`tools/adoption_scan/tests/test_dispositions.py::test_catalog_invariant_to_untracked_local_state`
(`:84`) fails with `git rm` staged-but-uncommitted:

```
E AssertionError: assert [...] == [...]
E   At index 204 diff: 'contracts/harness/security/deny-domains.json' != '...relationship.schema.json'
E   Left contains 21 more items, first extra item: 'tools/memory_ui/_stamp.py'
```

After `git commit`:

```
$ uv run pytest tools/adoption_scan/tests/test_dispositions.py -q
20 passed
```

**D-15 is empirically confirmed.** This test is red between `git rm` and `git commit` in every
deletion commit and green after. It is the *only* test with this property that I found.

#### H. `test_conductor_graph_render.py` — 3 failures, file-read not config-read

```
E FileNotFoundError: .../harness/commands/pipeline.md
```

`test_conductor_graph_render.py:29-30` reads `harness/commands/pipeline.md` and
`harness/skills/pipeline-map/SKILL.md` at module scope-adjacent time. Both die with the deletions →
**delete the file**; there is nothing to narrow (its entire subject is the two deleted artifacts).

#### I. `test_commands.py` — 1 failure, from CER-09 not CER-08

```python
tools/harness_lint/tests/test_commands.py:42-44
EXPECTED_GOLDEN_ADJACENT = frozenset(
    {"build", "test", "lint", "golden", "golden-approve", "adr", "checkpoint", "component"}
)
```

Asserted at `:59` (`missing = EXPECTED_GOLDEN_ADJACENT - names`). Relocating `/golden` +
`/golden-approve` drops both → `test_golden_adjacent_commands_present` FAILS. Remove the two members
(the docstring at `:41` says "eight golden-adjacent commands" → six).

#### J. Items CONTEXT names that do NOT break — verified negatives

Recorded so the planner does not spend budget on them.

| Item | CONTEXT claim | Measured |
|---|---|---|
| `tools/hooks/tests/test_contract_guard.py:330` | breaks on `deny-domains` deletion | **Does not break.** `:326-333` is a list of *synthetic path strings* fed to `decide()`; `"docs/reference/deny-domains.md"` is a **negative-control literal** asserting the path is NOT constitution plane. No filesystem access. Leave it, or swap the literal for another docs path. |
| The eight `harness_lint` `[pipeline]` tests | "die with the slot" | **Pass vacuously** — see §"The `[pipeline]` correction". `test_pipeline_config.py`'s two edge tests must be deleted *because* they pass. |
| `tools/adoption_scan` redaction (D-08) | must survive untouched | **Survives.** `scan.py:57`'s patterns are a hand-copy ("byte-identical from … gate-registry.json"), not a read. All 20 `adoption_scan` disposition + exclusion tests pass after the contract deletion. **D-08 confirmed.** |
| ruff ratchet (Phase 43 WARNING-3 / follow-up #4) | 161 findings of slack, owed to 44 or 45 | **Already closed.** `uv run python -m tools.ruff_baseline` → `84 findings (baseline 84) — PASS: every rule class is at its baseline.` No action. |
| `emit-manifest.json` rows | manual edit | **Self-pruning** via `manifest.py:64-80`. |
| `gate.needs` | needs repair | **Unchanged at 10** — the `golden` job survives. |

#### K. The 5 hyphenated `gate-registry.json` provenance docstrings (D-10) — exact list

| `file:line` |
|---|
| `tools/adoption_scan/__init__.py:7` |
| `tools/adoption_scan/scan.py:11` |
| `tools/adoption_scan/scan.py:57` |
| `tools/adoption_scan/tests/conftest.py:50` |
| `tools/adoption_scan/tests/test_scan_exclusions.py:110` |

Exactly 5, as D-10 states. All prose. Note `test_scan_exclusions.py:110` reads *"Until the
gate-registry.json fix lands, this second half of the assertion is expected to FAIL — that is the
intended red state for this task"* — historical prose about a fix that already landed; the test is
green. Rewrite, do not delete the test.

#### L. `/component` — D-11's line numbers, corrected

`harness/commands/component.md` is **78 lines**:

| Lines | Section |
|---|---|
| `:15-30` | `## Mandated order (do not skip a step)` — ① mechanism, **survives** |
| `:31-36` | `## Guard` — **survives** |
| `:37-67` | `## Mandated order (keep the three in sync) — when the package maps to a topology component` — **goes** |
| `:68-78` | `## Guard — component binding` — **goes** |

D-11 says ":37-66 plus its `## Guard` at :68". The correct span is **`:37` to EOF (`:78`)** — there
is nothing after the second guard block. Confirms the shape D-11 fixed; only the endpoints differ.

---

## `secret_scan` removal + the `RETIRED_SIGNATURES` tombstone

### The emit works and the slot count is 7 → 6

Clone `w5`: `HARNESS_SIGNATURES` loses `"tools.hooks.secret_scan"` (`merge.py:91`); the
`{"matcher": "Read|Write|Edit", … "tools.hooks.secret_scan"}` group is removed (`merge.py:177-187`);
`RETIRED_SIGNATURES` gains the entry; `tools/hooks/secret_scan.py`,
`tools/hooks/tests/test_secret_scan.py`, `harness/plugins/secret-scan.ts` deleted.

```
$ uv run python -m tools.harness_emit
harness-emit: 87 artifact(s) emitted ...      exit 0
$ # .claude/settings.json
PreToolUse 6   PostToolUse 4   secret_scan present: False
$ uv run pytest tools/harness_emit/tests/test_settings_merge.py -q
7 passed
```

⚠ Note the matcher is **`Read|Write|Edit`**, not `Write|Edit|Bash`. The literal to repair:

```python
tools/hooks/tests/test_settings_coexist.py:83   ("PreToolUse", "tools.hooks.secret_scan", "Read|Write|Edit"),   # row -> delete
tools/hooks/tests/test_settings_coexist.py:112  """7 PreToolUse (4 GSD + 3 harness) and 4 PostToolUse ..."""   # docstring
tools/hooks/tests/test_settings_coexist.py:114  assert len(hooks["PreToolUse"]) == 7, "expected 7 PreToolUse slots (4 GSD + 3 harness gates)"
tools/hooks/tests/test_settings_coexist.py:3    """The four Phase-4 gates (contract_guard, secret_scan, commit_gate PreToolUse; format_on_write ..."""
```

**Both the count `7` and its message string** (`"expected 7 PreToolUse slots (4 GSD + 3 harness gates)"`)
→ `6` / `"(4 GSD + 2 harness gates)"`. `PostToolUse == 4` is unchanged. Line `:112`'s docstring and
`:3`'s module docstring carry the same numbers.

`tools/harness_emit/tests/test_settings_merge.py` is **byte-for-byte against the live
`.claude/settings.json`** (`:106`, `:152`) — before the re-emit, 3 of its 7 tests fail. Re-emit must
be in the same commit.

### 🔴 D-07 is half right: the append is one line, but the existing test does NOT cover it

**Mutation proof.** With `RETIRED_SIGNATURES = ("tools.hooks.resume_gate", "tools.hooks.secret_scan")`
and everything green, I deleted `"tools.hooks.secret_scan"` from the tuple:

```
$ uv run pytest tools/harness_emit/tests/test_settings_merge.py::test_retired_signature_group_is_dropped_from_a_stale_checkout -q
1 passed
```

**The test stays green with the tombstone missing.** `test_settings_merge.py:131-132`:

```python
assert merge.RETIRED_SIGNATURES, "no retired signature to exercise"
signature = merge.RETIRED_SIGNATURES[0]
```

It reads **entry `[0]` only** — `resume_gate` forever. The Phase-43 defect D-07 exists to prevent is
therefore **still uncovered for `secret_scan`**.

**I also tested the obvious fix and it is insufficient.** Converting the body to
`for signature in merge.RETIRED_SIGNATURES:` makes all 7 tests pass — and *still* passes when
`secret_scan` is removed from the tuple, because the loop only exercises what is listed. No test whose
subject is the tuple's *content* can catch an omission from that tuple.

**Two changes are needed, not one:**

1. **Loop** (`:132` → `for signature in merge.RETIRED_SIGNATURES:`, body extracted to a helper) —
   this genuinely extends the *drop-mechanism* coverage to every entry, which today is `[0]`-only.
   Verified green.
2. **An explicit membership pin** — the only thing that survives the mutation:
   ```python
   assert "tools.hooks.resume_gate" in merge.RETIRED_SIGNATURES   # Phase 43 (CER-07)
   assert "tools.hooks.secret_scan" in merge.RETIRED_SIGNATURES   # Phase 44 (CER-08)
   ```
   This is what makes the tuple append-only in practice: it reds on exactly the "clear it afterwards"
   move that Phase 43 shipped. Cheap, and it is the assertion D-19 actually asks for.

**[VERIFIED: both mutations executed in w5]**

### `merge.py` docstring

`merge.py:109-118`'s `RETIRED_SIGNATURES` docstring already states the permanence rule and cites
Phase 43. Append the Phase-44 line; do not rewrite.

---

## Runtime State Inventory

Required by the rename/refactor/migration trigger. Answered explicitly per category.

| Category | Items Found | Action Required |
|---|---|---|
| **Stored data** | **None in a database.** No ChromaDB / Mem0 / Redis / SQLite in this repo — `git grep` for those and for `.db`/`.sqlite` under tracked paths returns nothing relevant. The nearest analogue is `contracts/.hashes/manifest.json` (9→6 entries) and `.memory/derived/contracts-index.md`, both **derived, regenerated by committed tooling**. | Rebaseline in-commit (`tools.contract_hash.hash`, `tools.memory_regen.contracts_index`) |
| **Live service config** | **None.** No n8n / Datadog / Tailscale / Cloudflare. The only out-of-git runtime config is a developer's own `.claude/settings.json` in a **stale checkout** — which is exactly what `RETIRED_SIGNATURES` addresses (§ above). | The `RETIRED_SIGNATURES` append + the membership pin |
| **OS-registered state** | **None.** No Task Scheduler / pm2 / launchd / systemd registration. Hooks are invoked by the Claude Code / opencode runtime from `.claude/settings.json`, not OS-registered. | None |
| **Secrets / env vars** | `GOLDEN_APPROVE_HUMAN` — read by `golden_runner/approve.py:26`, `hooks/contract_guard.py:56`, `hooks/commit_gate.py:53`. **The name does not change** and the `contract_guard` / `commit_gate` readers are unaffected by CER-09. ⚠ Do not delete the `commit_gate` drift-ratification path (`:155-171`) while removing its golden component — the env var is shared, the semantics are not. | None (verify by keeping the 4 `GOLDEN_APPROVE_HUMAN` tests in `test_commit_gate.py` green) |
| **Build artifacts / installed packages** | **`uv.lock:14,252-254`** — pins `logparser-golden-runner` at `virtual = "tools/golden_runner"`. Stale after `git mv`, and it **hard-fails every `uv` command** (§1). Also `.venv/` and `__pycache__/` under `tools/golden_runner/` (untracked; `tools/golden_runner/__pycache__/*.pyc` present in the live tree). `tools/memory_ui` + `tools/strangler_guard` removal also requires a lock refresh. | `uv lock --upgrade-package logparser-golden-runner` in the move commit; `uv lock && uv sync --all-packages` in the member-deletion commit |

---

## Recommended commit sequence — every commit ends green

Six commits. Rationale for the ordering: (i) `caps.py` hard-fails the emitter, so **any** commit
touching `harness/skills/**` must carry its `caps.py` edit; (ii) `test_emit_determinism.ambr` renders
bodies, so **any** commit touching `harness/**` must carry its `--snapshot-update`; (iii) `commit_gate`
is the only collection-level break and must not straddle a commit boundary; (iv) the CER-09 move
briefly disarms every `uv` command, so it goes last, alone, with nothing else in flight.

**Per-commit verification command** (D-19's is insufficient — §5):

```bash
uv run pytest -q \
  && uv run pytest examples/log-parser/tests examples/log-parser/golden_runner -q \
  && uv run python -m tools.harness_emit && git diff --exit-code --stat \
  && uv run python -m tools.contract_drift.drift \
  && uv run python -m tools.ruff_baseline \
  && python3 tools/harness_lint/workspace_check.py
```

| # | Commit | Contents | Expected green because |
|---|---|---|---|
| **1** | `chore: delete memory_ui + strangler_guard` | `git rm -r tools/memory_ui tools/strangler_guard`; `harness/commands/strangler-step.md`; `harness/skills/gate-model/` (it references `strangler_guard`); `caps.py` `EXPECTED_SKILLS` −`gate-model`; `test_coexist.py:41,70,71` 21→20; `test_commands.py` if it names `strangler-step`; `uv lock && uv sync`; re-emit + `.ambr --snapshot-update` | D-13 measured no external consumer for `memory_ui`. `caps.py` in-commit keeps the emitter runnable. `test_dispositions.py` red only until `git commit`. |
| **2** | `chore: delete deny-domains + gate-registry contracts` | 3 `git rm` under `contracts/`; `hash.py:30-34` → `()`; **delete** `test_hash.py:93-111`; `docs_sync` `EXPECTED_PAGES` −`deny-domains` + its `.ambr`; regenerate `docs/reference/` (prunes `deny-domains.md`) + `.memory/derived/contracts-index.md` + its `.ambr`; rebaseline `contracts/.hashes/manifest.json`; the 5 docstrings (K) | Isolated run measured **exactly these 6 failures**; all repaired here. `contract-drift` exit 0 verified. |
| **3** | `chore: remove secret_scan hook` | `git rm` the 3 files; `merge.py:91` sig, `:177-187` group, `:111` tombstone append; `test_settings_merge.py` loop + membership pin; `test_settings_coexist.py:3,83,112,114` 7→6; `workspace_check.py:22` + `test_workspace_member_completeness.py:13` prose; `review.md:24`; re-emit + `.ambr` | Emit verified exit 0, PreToolUse 6, `test_settings_merge.py` 7 passed. D-08 verified: adoption untouched. |
| **4** | `chore: remove /pipeline + pipeline-map + core [pipeline] data` | `harness/commands/pipeline.md`, `harness/skills/pipeline-map/`; `harness/project.toml:77-80`; `caps.py` −`pipeline-map`; **delete** `test_conductor_graph_render.py`; **delete** `test_pipeline_config.py:50,73` (vacuous); narrow `test_topology_relationships.py` + `test_loader.py::test_pipeline_passthrough` + `test_endpoints.py::test_core_pipeline_edges_stay_single_repo`; `test_orchestrator_topology.py:61` `/pipeline` ref; re-emit + `.ambr`. **Keep `loader.pipeline()`.** | Isolated `[pipeline]` run = 3 failures, all narrowed here; the 3 `conductor_graph_render` FileNotFoundErrors resolved by deleting the file. Instance untouched because the loader survives. |
| **5** | `chore: /component loses the topology-registration half` | `component.md:37-78`; re-emit + `.ambr` | Nothing else reads that section; `test_commands.py` checks presence of `component`, not its body. |
| **6** | `refactor: relocate the golden stack to examples/log-parser` | **Atomic.** `git mv tools/golden_runner examples/log-parser/golden_runner`; `git mv golden/sample examples/log-parser/golden/sample`; `git rm golden/README.md`; `pyproject.toml:34` member; **`uv lock --upgrade-package logparser-golden-runner`**; 3 `parents[N]` +1; 11-file import rewrite; 2 conftest `sys.path` entries; `commit_gate` golden component (§6) + all of `test_commit_gate.py`; `verify-work.md:44` + `python-conventions/SKILL.md:35`; `test_install_completeness.py:103` floor 12→11; `git rm harness/commands/{golden,golden-approve}.md harness/skills/{golden-testing,golden-debug}`; `caps.py` −2; `test_commands.py:42-44` −2; `test_coexist.py:41,70,71` 19→17; `ci.yml:155-156,167,168,320`; re-emit + `.ambr` | Measured: 14 + 17 example tests pass; floor at 11 passes; GEN-04 passes only with the golden component **deleted** from `commit_gate`. |

**Between commit 6's `git mv` and its `uv lock --upgrade-package`, the agent's own PreToolUse guards
are down.** Plan the two as a single Bash invocation (`git mv … && uv lock --upgrade-package …`), not
as separate tool calls.

**Commit-1 caveat:** commits 1, 4, 5 and 6 all edit `harness/**` and each therefore needs its own
`.ambr --snapshot-update` — that is unavoidable, not a planning miss. Do not attempt to batch the
snapshot regeneration into a final commit; commits 1–5 would each end red.

**Alternative parallelization** (Claude's discretion, D): commits 1–5 are mutually independent except
for the shared `caps.py` / `.ambr` files, which serialize them in practice. Commit 6 is genuinely
independent of 1–5 **except** that it also edits `caps.py` and `.ambr`. Recommend **sequential**;
the shared-file contention removes most of the parallelism benefit and every merge would re-run the
emitter anyway.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Repointing CI job paths | grep/sed over `ci.yml` | `ruamel.yaml` (0.19.1, already resolved) | D-19 requires YAML-resolved; `gate.needs` is a flow-seq that sed will mangle |
| Regenerating emitted trees | hand-editing `.claude/**`, `.opencode/**` | `uv run python -m tools.harness_emit` | D-17; `emit-drift` reds on any hand edit |
| Regenerating snapshots | hand-editing `.ambr` | `pytest --snapshot-update` | syrupy owns the format |
| Rebaselining the hash manifest | recomputing SHA-256 | `uv run python -m tools.contract_hash.hash` | RFC 8785 JCS canonicalization |
| Fixing a stale `uv.lock` path | editing `uv.lock` by hand | `uv lock --upgrade-package <name>` | 1-line diff, verified; hand edit risks the whole resolution |
| Detecting a broken workspace | a pytest test | `python3 tools/harness_lint/workspace_check.py` | uv dies before pytest starts — the module's own docstring proves the pytest twin cannot be the gate |

---

## Common Pitfalls

### Pitfall 1: trusting `uv run pytest -q` as the phase gate
**What goes wrong:** `testpaths = ["libs/python", "tools"]`; `examples/**` is never collected. All four
golden importers and `test_pipeline_topology.py` are invisible.
**How to avoid:** append `uv run pytest examples/log-parser/tests examples/log-parser/golden_runner -q`.
**Warning sign:** a commit that touches `examples/**` or `tools/harness_config` and reports green in
one command.

### Pitfall 2: trusting `pytest --collect-only` as a smoke check
**What goes wrong:** 924 collected, **0 errors**, with 26 real failures live.
**How to avoid:** never use `--collect-only` as this phase's guard. Only `commit_gate` (CER-09) breaks
at collection.

### Pitfall 3: `uv lock` after a member move
**What goes wrong:** `uv lock` and `uv sync` both fail with `Distribution not found`, leaving the repo
uv-dead and the PreToolUse guards denying every write. `workspace_check.py` does **not** detect this
(it only checks for a missing `pyproject.toml`).
**How to avoid:** `uv lock --upgrade-package logparser-golden-runner`, in the same shell invocation as
the `git mv`.

### Pitfall 4: a deleted config slot that leaves tests green
**What goes wrong:** removing `[pipeline]` makes `test_pipeline_config.py:50,73` iterate an empty list
and pass while asserting nothing.
**How to avoid:** for each surviving test that reads a deleted slot, ask "does the loop body still
execute?" If not, delete the test.

### Pitfall 5: forgetting a member-deletion needs a lock refresh
**What goes wrong:** deleting `tools/memory_ui` + `tools/strangler_guard` without
`uv lock && uv sync --all-packages` produced two spurious `ModuleNotFoundError` collection errors for
`tree_sitter`/`networkx` — deps of the *surviving* `tools/memory_regen`.
**How to avoid:** `uv sync --all-packages` after every member add or remove.

### Pitfall 6: `parents[N]` after a directory move
**What goes wrong:** silent. `REPO_ROOT` becomes `examples/`, which narrows the T-06-02 path-confinement
allowlist and breaks `workspace.toml` member resolution — with no import error.
**How to avoid:** `grep -rn 'parents\[' <moved-tree>` and re-derive each depth by hand. Three sites here.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---|---|---|
| `uv` | everything | ✓ | resolves CPython 3.11.15 | — |
| Python | test suite | ✓ | 3.11.15 | — |
| `ruamel.yaml` | `gate.needs` resolution | ✓ | 0.19.1 (transitive) | — do NOT add PyYAML |
| `syrupy` | `.ambr` regeneration | ✓ | 5.2.0 | — |
| `git` | `git mv` / `git ls-files` | ✓ | — | — |
| `.NET SDK 10` | `require_dotnet` golden cases | ✗ | — | Cases **SKIP** cleanly (`conftest.py` `require_dotnet`); the 14 + 17 example/runner tests still pass locally. CI installs it via `actions/setup-dotnet@v5.4.0`. |

**Missing dependencies with no fallback:** none.
**Missing with fallback:** .NET 10 — the `.NET`-gated golden cases skip locally and run in CI. This
means **local verification of commit 6 cannot exercise the spawn path**; CI `golden` is the only place
it runs. State this as a residual in the phase summary rather than claiming full local proof.

---

## Validation Architecture

`workflow.nyquist_validation` is `true` in `.planning/config.json`.

### Test Framework

| Property | Value |
|---|---|
| Framework | pytest 8.4.x (pinned `>=8.4,<9`) + syrupy 5.2.0 |
| Config file | root `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["libs/python","tools"]`) |
| Quick run command | `uv run pytest -q` (983 baseline) |
| Full suite command | `uv run pytest -q && uv run pytest examples/log-parser/tests examples/log-parser/golden_runner -q` |

### Phase Requirements → Test Map

| Req | Behavior | Type | Automated command | Exists? |
|---|---|---|---|---|
| CER-08 | Deleted modules have no surviving invoker | structural | `uv run pytest tools/adoption_scan/tests/test_install_completeness.py -x` | ✅ |
| CER-08 | Stale checkout drops the `secret_scan` group | unit | `uv run pytest tools/harness_emit/tests/test_settings_merge.py::test_retired_signature_group_is_dropped_from_a_stale_checkout -x` | ⚠️ exists but **does not cover entry [1]** — needs the loop + membership pin (Wave 0) |
| CER-08 | Contracts gone, manifest rebaselined | integration | `uv run python -m tools.contract_drift.drift` | ✅ |
| CER-08 | PreToolUse slot count 6 | unit | `uv run pytest tools/hooks/tests/test_settings_coexist.py -x` | ✅ (literal edit) |
| CER-08 | Skill/command sets exact | unit | `uv run pytest tools/harness_lint/tests/test_skills.py tools/harness_emit/tests/test_coexist.py -x` | ✅ |
| CER-09 | Golden stack resolves under `examples/` | integration | `uv run pytest examples/log-parser/tests examples/log-parser/golden_runner -q` | ✅ |
| CER-09 | Core has no example dependency | structural | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -x` | ✅ |
| CER-09 | Workspace resolves | smoke | `python3 tools/harness_lint/workspace_check.py` | ✅ |
| CER-09 | CI paths repointed | manual/YAML | ruamel assertion on `ci.yml` job `run:` strings | ❌ **Wave 0** — no test asserts a CI `run:` path resolves to a real directory |
| both | Emitted trees reproduce from source | integration | `uv run python -m tools.harness_emit && git diff --exit-code` | ✅ |

### Sampling Rate

- **Per task commit:** `uv run pytest -q` + the `examples/` leg (§5).
- **Per wave merge:** the full 6-command block in the commit-sequence section.
- **Phase gate:** all six green + `git diff --shortstat` recorded (D-21).

### Wave 0 Gaps

- [ ] `tools/harness_emit/tests/test_settings_merge.py` — loop over `RETIRED_SIGNATURES` + explicit
      membership pins for both `resume_gate` and `secret_scan`. **Proved necessary by mutation.**
- [ ] A CI-path resolution assertion — nothing currently proves `ci.yml`'s `pytest <path>` arguments
      name real directories. `test_install_completeness.py` covers `python -m tools.X` refs in
      workflows, but **not** bare path arguments, which is exactly how `ci.yml:168,320` reference
      `tools/golden_runner`. Without it, a mis-repointed CI path lands green.

---

## Security Domain

`security_enforcement` is not set to `false`; included.

### Applicable ASVS Categories

| Category | Applies | Standard control |
|---|---|---|
| V2 Authentication | no | no auth surface |
| V3 Session Management | no | — |
| V4 Access Control | **yes** | `contract_guard` `CONSTITUTION_GLOBS` + CODEOWNERS. ⚠ **This phase reduces it** (§8 Consequence A: 4 golden files move deny→allow) and **removes `secret_scan` entirely**. |
| V5 Input Validation | yes | JSON Schema Draft 2020-12 + `jsonschema` 4.26.0; unchanged |
| V6 Cryptography | yes | RFC 8785 JCS + SHA-256 via `rfc8785` 0.1.4 — never hand-rolled; unchanged |
| V12 File / Resource | **yes** | `runner.py:91-98` path-confinement allowlist rooted at `REPO_ROOT` — ⚠ **the `parents[2]→[3]` fix is a security fix**, not a cosmetic one |

### Known Threat Patterns

| Pattern | STRIDE | Mitigation status after this phase |
|---|---|---|
| Secret committed at the tool boundary | Information Disclosure | **Mitigation removed** (`secret_scan`). ADR-0012 records it as a permanent residual caught at CI/PR review. Accepted by the ROADMAP. `tools/adoption_scan`'s own redaction is unaffected (D-08, verified). |
| Agent self-blessing a golden baseline | Elevation of Privilege | **Weakened** for the 4 moved files (in-session `contract_guard` deny → allow); merge-time CODEOWNERS `/examples/*/golden/` holds |
| Path traversal out of the repo in golden runs | Tampering | Preserved **only if** `runner.py:29` is corrected to `parents[3]` |
| Stale checkout running a deleted guard module → repo-wide denial | Denial of Service | Mitigated by the `RETIRED_SIGNATURES` append **plus** the membership pin (the append alone is untested — proved by mutation) |
| Command injection in spawns | Tampering | `subprocess.run([list], shell=False)` throughout; unchanged by the move |

---

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|---|---|---|
| A1 | Keeping `loader.pipeline()` while deleting the core `[pipeline]` data satisfies D-12's intent | `[pipeline]` correction | If the planner must delete the passthrough, the instance test + its 5 assertions need rewriting in the same commit, and only the `examples/` test leg catches it |
| A2 | The 4 moved golden files losing in-session `contract_guard` protection is acceptable given CODEOWNERS | §8 | If not, `CONSTITUTION_GLOBS` needs an `examples/*/golden/**` entry — which is surface growth against SC-8 and needs a human call |
| A3 | `DATA_CONTRACT_PATHS = ()` should be kept as an empty seam rather than deleted | §E | Low — either reading satisfies CER-08's "their entries" wording |
| A4 | Deleting `commit_gate`'s golden component is in scope for this phase | §6 | **High if wrong.** It is forced by GEN-04 + CER-09 and has no alternative, but it is a gate-component removal neither requirement names. Worth an explicit human confirmation at plan time. |
| A5 | The `golden` CI job is retained (repointed), so `gate.needs` stays at 10 | §9 | If the job is deleted instead, `needs` → 9 and the subset-only fan-in test will not catch a stale entry |
| A6 | `git mv golden/sample` + `git rm golden/README.md` is the right split (README is core-template prose, not a case) | §8 | Low — the README describes the top-level-`golden/` convention that ceases to exist |

---

## Open Questions

1. **Does `commit_gate` keep a golden component at all, or lose it permanently?**
   - Known: it cannot import from `examples/` (GEN-04, proved). It cannot stay as-is (collection error, proved).
   - Unclear: whether the intent is "the core's commit gate no longer checks golden" (my reading of
     "the core stops promising golden parity") or whether an instance-side hook is wanted.
   - Command that answers it: none — this is a **human/ROADMAP scope call**. Recommend raising it
     before planning; §6 documents the forced consequence either way.

2. **Should `test_pipeline_config.py` survive at all?**
   - Known: with `[pipeline]` gone, 2 of its 4 tests are vacuous; the other 2
     (`test_component_languages_are_declared`, `test_component_ids_unique`) read `[[components]]`, which **survives**.
   - Recommendation: keep the file, delete the two edge tests, rename the module docstring off
     "PIPE-01 topology CONSISTENCY gate".
   - Command: `uv run pytest tools/harness_lint/tests/test_pipeline_config.py -q` after the slot removal
     (measured: 14 passed across the 4 files, i.e. it does not self-report the vacuity).

3. **Does `AGENTS.md:66-67`'s golden-path table move in 44 or 45?**
   - Known: `tools/memory_regen/tests/test_agents_md.py:49` asserts `"tools.golden_runner"` is present
     in `AGENTS.md`. Phase 45 owns `AGENTS.md`; Phase 44 makes the path false.
   - Command that answers it: `uv run pytest tools/memory_regen/tests/test_agents_md.py -q` after
     commit 6 — I did not run it in the fully-relocated tree, so I cannot state whether it reds.
     **Planner should run this before finalizing commit 6's file list.**

4. **What is the actual net LOC (D-21)?**
   - Not measurable until the phase lands. My clones were partial and each carried scratch edits.
   - Command: `git diff --shortstat f353ff1..HEAD -- . ':(exclude).planning'` at phase close.

---

## Sources

### Primary (HIGH — executed in this session)
- Scratch clones `w1`–`w5` of `f353ff1` — every quantitative claim above
- `uv 0.11.x` / `uv lock --upgrade-package`, `uv sync --all-packages` — observed behavior
- `pytest --collect-only`, `pytest -q` — collection scope and failure attribution
- `ruamel.yaml` 0.19.1 — `ci.yml` job/`needs` resolution
- `tools.harness_emit`, `tools.contract_hash.hash`, `tools.contract_drift.drift`,
  `tools.ruff_baseline`, `tools/harness_lint/workspace_check.py` — exit codes and output

### Primary (HIGH — repo documents read)
- `.planning/phases/44-non-goal-surface-removal/44-CONTEXT.md` (D-01…D-21)
- `.planning/ROADMAP.md` §"Phase 44", `.planning/REQUIREMENTS.md` (CER-08, CER-09)
- `.planning/phases/43-lifecycle-plane-removal/REVIEW.md` (CR-01, WR-08, WR-10, IN-01, IN-03, IN-05)
- `.planning/phases/43-lifecycle-plane-removal/43-VERIFICATION.md` (8/8, WARNING-1..4)
- `docs/adr/0001-walking-skeleton-golden-core.md:48`, `.github/CODEOWNERS`
- `CLAUDE.md`, root `AGENTS.md`

### Not used
- No WebSearch / Context7 lookup was needed: every question in scope was answerable against this
  repo's own code and by executing it. No external library version claims are made.

---

## Metadata

**Confidence breakdown:**
- CER-09 relocation mechanics: **HIGH** — end-to-end reproduced twice (`w1`, `w2`), 31 tests green
- CER-08 blast radius: **HIGH** — isolated attribution runs for contracts (`w5`) and `[pipeline]` (`w4`)
- `commit_gate` consequence: **HIGH** — collection error and GEN-04 failure both reproduced
- `RETIRED_SIGNATURES` coverage gap: **HIGH** — proved by mutation in both directions
- Commit sequencing: **MEDIUM** — the constraints are measured, but the six-commit grouping is a
  recommendation, not an executed rehearsal. No clone replayed all six commits in order.
- `test_agents_md.py` behavior after relocation: **LOW** — not run in the fully-relocated tree (Q3)

**Research date:** 2026-07-29
**Valid until:** until `HEAD` moves off `f353ff1` — every line number is anchored to that commit.
