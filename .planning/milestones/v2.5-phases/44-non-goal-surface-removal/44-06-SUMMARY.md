---
phase: 44-non-goal-surface-removal
plan: 06
wave: 6
subsystem: phase-closeout / evidence
tags: [CER-08, CER-09, closeout, evidence, d-18, d-19, d-20, d-21, gates]
requires: ["44-05"]
provides:
  - "executed evidence for all eight ROADMAP Phase 44 success criteria"
  - "the ten-commit greenness table with a gate result per commit"
  - "the measured whole-phase LOC (D-21)"
  - "the phase's accepted consequences, residuals, and the Phase 45 deferral list"
affects:
  - ".planning/phases/44-non-goal-surface-removal/44-06-SUMMARY.md"
tech-stack:
  added: []
  patterns: []
key-files:
  created:
    - ".planning/phases/44-non-goal-surface-removal/44-06-SUMMARY.md"
  modified: []
decisions: [D-18, D-19, D-20, D-21]
metrics:
  commits: 1
  duration: single session
  completed: 2026-07-29
---

# Phase 44 Plan 06: Non-Goal Surface Removal Closeout Summary

The phase closes with every gate green, a measured net of **−6,067 LOC**, all ten code commits
verified green, SC-1 through SC-8 evidenced by executed commands — and **SC-6 recorded as not met as
worded**, because a live structure diagram in `README.ko.md` still labels a directory this phase
deleted.

**No code changes.** This plan ran read-only gates and wrote this file.

---

## 1. Gate sweep — observed exit codes

Every command below was executed at `HEAD = 9e0559b`, working tree clean. Commands resolved from
`.github/workflows/ci.yml`, not guessed (D-19).

| CI job | Command | Observed output | Exit |
|---|---|---|---|
| `core-suite` | `uv run pytest -q` | `880 passed in 10.97s`, `7 snapshots passed` | **0** |
| `golden` step 2 + `workspace` | `uv run pytest examples/log-parser/tests examples/log-parser/golden_runner -q` | `31 passed in 3.00s` | **0** |
| `emit-drift` (a) | `uv run python -m tools.harness_emit` | `69 artifact(s) emitted to .opencode/ + .claude/ + opencode.json` | **0** |
| `emit-drift` (b) | `git diff --exit-code -- .opencode opencode.json .claude/agents .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json tools/harness_emit/emit-manifest.json` | no diff | **0** |
| `stale-derived` (a) | `uv run python -m tools.docs_sync` | `docs-sync: 6 reference page(s) regenerated from contracts/` | **0** |
| `stale-derived` (b) | `uv run python -m tools.memory_regen.contracts_index` | `wrote .memory/derived/contracts-index.md (6 contract(s) indexed)` | **0** |
| `stale-derived` (c) | `git diff --exit-code -- docs/reference .memory/derived/contracts-index.md` | no diff | **0** |
| `contract-check` / `drift` | `uv run python -m tools.contract_drift.drift` | `contract-drift: OK — live manifest matches the committed baseline.` | **0** |
| `lint` (a) | `uv run python -m tools.ruff_baseline` | `ruff ratchet: 73 findings (baseline 84)` / `improved E501: baseline 84 -> found 73` / `PASS — and findings went DOWN` | **0** |
| `lint` (b) | `uv run pytest tools/ruff_baseline -q` | `27 passed` | **0** |
| `workspace` | `python3 tools/harness_lint/workspace_check.py` | `workspace-check: OK — every globbed Python member has a pyproject.toml.` | **0** |

**Red gates: none.** No gate was absorbed, repaired, or re-run to green.

`gate.needs` resolves to exactly **10** entries with `set(needs) - set(jobs)` empty (asserted by
count, not by the subset-only `test_every_job_is_in_the_fan_in`, per Phase 43 IN-03):

```
needs = ['setup', 'lang-tests', 'contract-check', 'drift', 'golden',
         'core-suite', 'lint', 'emit-drift', 'stale-derived', 'workspace']
```

`git status --porcelain -- . ':(exclude).planning'` → empty. `emit-manifest.json` did **not** appear
dirty at closeout, so no prior commit's pathspec was short (no D-15 violation).

---

## 2. ROADMAP success-criteria evidence table

### SC-1 — CER-08 paths gone, no surviving file invokes them — **MET**

CER-08 name sweep across `tools harness libs examples .github contracts`:

| Name | Hits |
|---|---|
| `memory_ui` | 0 |
| `strangler_guard` | 0 |
| `strangler-step` | 0 |
| `gate-model` | 0 |
| `deny-domains` | 0 |
| `gate-registry` | 0 |
| `secret_scan` | 0 |
| `secret-scan` | 0 |
| `pipeline-map` | 0 |

Retired artifact paths, by `test -e`: `harness/commands/golden.md`, `harness/commands/golden-approve.md`,
`harness/skills/golden-testing`, `harness/skills/golden-debug`, `.claude/commands/golden.md`,
`.claude/commands/golden-approve.md`, `tools/golden_runner` — **all gone**.

**Proxy correction.** SC-1's wording is "…do not exist, and no surviving file **invokes** them." The
`golden-*` grep is a *proxy* for that criterion and it over-matches. Narrowing a proxy so it tests
the criterion as written is legitimate; rewriting the criterion to match an observation is not — so
SC-1 itself is unchanged, and the proxy is narrowed to invocation-shaped references. The raw
`git grep -n "golden-approve\|golden-debug\|golden-testing" -- tools harness libs examples .github contracts`
returns **14 hits**, classified in full rather than silently excluded:

**Bucket A — not invocations, the implementation (5).**
`examples/log-parser/golden_runner/__init__.py:5`, `approve.py:1`, `pyproject.toml:4`,
`runner.py:76`, `tests/test_approve_gate.py:1`.
This is the relocated package that *implements* the minimal approve gate. CER-09 relocates it
deliberately. A grep that flags these is conflating the **retired command artifact**
(`harness/commands/golden-approve.md`, confirmed absent) with the **surviving module**
(`approve.py`, deliberately moved into the instance). The command retired; the module relocated.
Those are different objects and the criterion names only the first.

**Bucket B — not invocations, retirement records (4).**
`tools/harness_emit/tests/test_coexist.py:56`, `tools/harness_lint/caps.py:124`,
`tools/harness_lint/caps.py:134`, `tools/harness_lint/tests/test_commands.py:42`.
These name the retired artifacts *precisely in order to record that they are retired*. Stripping
them to force a clean grep would delete the history the repo keeps on purpose — the same mistake the
Wave-3 executor correctly refused with `caps.py:125`.

**Bucket C — genuine staleness, deferred to Phase 45 (5).**
`tools/hooks/contract_guard.py:9`, `:75`, `:89`, plus `tools/hooks/tests/test_contract_guard.py:51`
and `:288`; and separately `contract_guard.py:55`'s stale `tools/golden_runner/approve.py` path
citation. These point a **live, user-facing refusal message** at a command that no longer exists.
**Real staleness, owned by Phase 45 (CER-11), not repaired here.** Recorded as a named deferral, not
as an exclusion.

The instance plane **is** in scope and **is** repaired for the command/skill artifacts themselves —
plan 04's sweep is what makes the retired `.md` artifacts absent from `harness/` and `.claude/`.
The pre-plan anchor's claim that the raw grep over `harness examples` "returns nothing" was measured
before plan 05's relocation and is **stale**; see §6, divergence 1.

**Scope note, stated rather than silently narrowed.** `.planning/` and `docs/adr/**` are historical
and append-only. `docs/**` beyond the ADRs is deferred to Phase 45 (CER-11) by consequence 7. Three
live `docs/` carriers of `/golden-approve` remain and are named here rather than left for the reader
to trip over: **`docs/glossary.md:20`**, **`docs/how-to/README.md:11`**, and
**`docs/how-to/approve-a-golden.md`** itself. Known, deferred, named — not repaired here.

### SC-2 — a stale checkout drops the `secret_scan` group on re-emit — **MET**

`uv run pytest tools/harness_emit/tests/test_settings_merge.py -q` → **8 passed**, exit 0.

Mutation result cited from plan 02 rather than re-run: removing either tombstone from
`RETIRED_SIGNATURES` turns the file red; `secret_scan` reds at `test_settings_merge.py:171`.

### SC-3 — contracts clean, `DATA_CONTRACT_PATHS` reduced, manifest rebaselined, drift 0 — **MET**

- `tools/contract_hash/hash.py:33` → `DATA_CONTRACT_PATHS: tuple[Path, ...] = ()` (reduced to empty).
- `contracts/` tree, 8 files: `.hashes/manifest.json`, `harness/adoption/{inventory,manifest,plan}.schema.json`,
  `harness/topology/relationship.schema.json`, `normalization/format-conventions.schema.json`,
  `README.md`, `sample/greeting.schema.json`. No `gate-registry.json`, no `deny-domains`.
- `uv run python -m tools.contract_drift.drift` → `OK — live manifest matches the committed baseline.`, exit 0.
- `git grep -n "gate-registry.json" -- tools harness contracts` → **no hits** (exit 1). Scoped to
  those three planes because `docs/adr/0012-…:114` names the file permanently and ADRs are append-only.

### SC-4 — `[pipeline]` slot and its consistency-gate assertions gone, no vacuous topology assertion — **MET**

- `uv run pytest tools/harness_lint/tests/test_pipeline_config.py -q` → **2 passed**, exit 0.
- `uv run pytest examples/log-parser/tests/test_pipeline_topology.py -q` → **5 passed**, exit 0,
  with `_CORE_RESOLUTION_DOCS` repointed (`test_pipeline_topology.py:115` →
  `harness/agents/templates/component-engineer.md`). Not dangling, not vacuous.

### SC-5 — golden stack under `examples/log-parser/`, core free of golden/parity .NET resolution — **MET**

Asserted with the **corrected** commands (see §6, and consequence 6):

| Command | Result |
|---|---|
| `test ! -e tools/golden_runner` | exit **0** (absent) |
| `git grep -nE "^[[:space:]]*(from\|import)[[:space:]]+tools\.golden_runner" -- tools harness libs` | exit **1**, clean |
| `git grep -n "run_golden_case\|GOLDEN_DIR\|run_identity_converter" -- tools harness libs` | exit **1**, clean |

Both CI jobs repointed, YAML-resolved via ruamel (plan 05); `gate.needs` = 10 with no dangling entry.

**`git grep -n "resolve_dotnet" -- tools harness libs` was deliberately NOT used as the criterion.**
It returns 3 legitimate hits, all in `tools/hooks/format_on_write.py` (`:57` def, `:61` docstring,
`:96` call). The original criterion wording was a defect: CER-09's ADR-0002(b) ground is that .NET
**golden/parity evidence** belongs in the instance, whereas `format_on_write` resolves `dotnet` in
order to run `dotnet format` — a language-toolchain concern that is legitimate in a polyglot
template core and has nothing to do with golden equivalence. **`format_on_write::resolve_dotnet` is
deliberately retained** (consequence 6). The matching ROADMAP wording correction is the developer's,
made separately; `.planning/ROADMAP.md` was not edited here.

### SC-6 — no hyphenated `gate-registry.json` provenance docstring survives — **NOT MET AS WORDED**

`git grep -n "gate.registry\|gate_registry" -- . ':(exclude).planning'` returns **2 hits**, where
the criterion requires "only legitimate history":

| Hit | Verdict |
|---|---|
| `docs/adr/0012-ci-and-merge-as-decision-authority.md:114` | **Legitimate.** ADRs are append-only; naming a removed artifact is the record working as designed. |
| `README.ko.md:79` — `harness/task-control/  # gate-registry` | **NOT legitimate history.** A live structure diagram labelling a directory that no longer exists — `test -d harness/task-control` → MISSING. |

No hyphenated provenance **docstring** survives in code, and the scoped
`git grep -n "gate-registry.json" -- tools harness contracts` is clean. But the criterion as written
is about the whole sweep returning only legitimate history, and it does not.

**Recorded as missed rather than laundered.** Calling a stale live diagram "legitimate history"
would be precisely the self-description defect this milestone was convened to remove. `README.ko.md`
is deferred to Phase 45 **as a whole file** (deferral item 12) — it also carries stale `golden/` and
`tools/…golden_runner` lines, and fixing one stale line while leaving two would be worse than
deferring all three together.

### SC-7 — suite green, drift gates clean, ratchet clean, `uv.lock` refreshed — **MET**

- `uv run pytest -q` → 880 passed, 7 snapshots, exit 0.
- `emit-drift`, `stale-derived`, `contract-drift` → all exit 0 (§1).
- `uv.lock` refreshed — see SC-8 diff.
- **Ratchet criterion is "exits 0 with NO rule class above baseline", not "the line reads 84/84".**
  Observed verbatim:

  ```
  ruff ratchet: 73 findings (baseline 84)
    improved    E501: baseline 84 -> found 73

  PASS — and findings went DOWN. Record the shrink so it cannot come back:
      uv run python -m tools.ruff_baseline --update
  ```

  Exit **0**. No rule class above baseline. **`--update` was NOT run** (every other plan in this
  phase forbids it, and the baseline stays at 84). A total below 84 is the expected consequence of
  deleting code — the deletions remove `E501` findings — and is a **PASS**, not a skipped cleanup.

  **Observed shrink is 84 → 73.** The plan's `<measured_anchors>` and `must_haves.truths` predicted
  84 → 77; that is a **stale mid-replay figure**, superseded here. The criterion passes on either
  number. The four pre-empted regressions (`F401` ×3 plan 03, `F401` ×1 plan 05 Task 1, `I001` ×3
  plan 05 Task 2) all held — no class went above baseline.

### SC-8 — net surface change is deletion or relocation only, +0 gates/tools/contracts/deps — **MET**

`git diff 7dbfb3a..HEAD -- uv.lock pyproject.toml`:

- `pyproject.toml`: exactly one changed line —
  `members = ["libs/python", "tools/*"]` → `members = ["libs/python", "tools/*", "examples/log-parser/golden_runner"]`.
- `uv.lock`: **removals only** (`logparser-memory-ui`, `logparser-strangler-guard` dropped from
  `members` and their `[[package]]` blocks deleted) plus **one source relocation** —
  `logparser-golden-runner` `source = { virtual = "tools/golden_runner" }` →
  `{ virtual = "examples/log-parser/golden_runner" }`.
- **No added distribution.**

`git diff --name-status --diff-filter=A 7dbfb3a..HEAD -- . ':(exclude).planning'` → **empty**. Zero
files added anywhere outside the planning plane across the whole phase. Therefore: no new file under
`contracts/`, no new entry in `.claude/settings.json` hooks, no new `tools/` package, no new
`harness/commands/` or `harness/skills/` entry. **+0 gates, +0 tools, +0 contracts, +0 dependencies.**

---

## 3. The ten-commit greenness table

Two commits per plan across plans 01–05, oldest first. Gate results taken from the five prior
SUMMARYs; the phase-end state re-verified in §1.

| # | Plan | SHA | Subject | Gate result at commit |
|---|---|---|---|---|
| 1 | 01 | `374f991` | `chore(44): delete memory_ui, strangler_guard, /strangler-step, gate-model` | green |
| 2 | 01 | `1e79bf6` | `chore(44): delete deny-domains + gate-registry contracts` | green |
| 3 | 02 | `a494cd3` | `test(44-02): cover every RETIRED_SIGNATURES tombstone, not entry [0]` | green |
| 4 | 02 | `ddfa6af` | `chore(44-02): delete secret_scan whole and append its permanent tombstone` | green |
| 5 | 03 | `f28a9cd` | `refactor(44-03): remove /component's topology-registration half` | green |
| 6 | 03 | `18124d3` | `chore(44-03): delete the core [pipeline] data, /pipeline and pipeline-map` | green |
| 7 | 04 | `8b5bc41` | `test(44-04): assert every CI pytest path argument resolves to a real path` | green |
| 8 | 04 | `8678b45` | `chore(44-04): retire the /golden + /golden-approve commands and the golden-testing + golden-debug skills` | green |
| 9 | 05 | `fc69d10` | `refactor(44-05): delete commit_gate's golden-parity component` | green |
| 10 | 05 | `df4675c` | `refactor(44-05)!: relocate the golden stack into the instance overlay` | green |

**Every one of the ten commits ended green. None ended red.**

A pre-revision replay of this plan set had **six of ten** commits ending red. Every one of those six
causes was pre-empted in the plan that causes it: `GOLDEN_DIR`, `_CORE_RESOLUTION_DOCS`, three ruff
regressions (`F401` ×3, `F401` ×1, `I001` ×3), and the `emit-manifest.json` pathspec omission. All
six are confirmed fixed — `emit-manifest.json` was clean at closeout, `_CORE_RESOLUTION_DOCS`
resolves, and the ratchet reports no class above baseline.

Plan summary commits (not part of the ten): `da9d816`, `81f8dea`, `bd6957c`, `7cde263`, `9e0559b`.

---

## 4. D-21 — whole-phase LOC, measured not estimated

`git diff --shortstat 7dbfb3a..HEAD -- . ':(exclude).planning'`:

```
 161 files changed, 481 insertions(+), 6548 deletions(-)
```

**Net: −6,067 LOC.**

Base-commit note: the plan's `<measured_anchors>` names `1a0bad1`; the phase base is `7dbfb3a`.
The three commits between them are `.planning/`-only, so under the `':(exclude).planning'` pathspec
both bases produce a **byte-identical** shortstat. Verified, not assumed — no discrepancy to resolve.

Per-plan figures, so the total is auditable:

| Plan | Range | Shortstat |
|---|---|---|
| 01 | `7dbfb3a..1e79bf6` | 65 files, +55 / −3,135 |
| 02 | `1e79bf6..ddfa6af` | 24 files, +86 / −553 |
| 03 | `ddfa6af..18124d3` | 28 files, +112 / −1,620 |
| 04 | `18124d3..8678b45` | 58 files, +190 / −1,044 |
| 05 | `8678b45..df4675c` | 31 files, +84 / −242 |

**−6,067 is a smaller net deletion than Phase 43's −12,383, as expected** — CER-09 relocates the
golden stack rather than deleting it, so plan 05 contributes only −242 net-of-insertions. Nothing was
deleted that should have moved.

---

## 5. Accepted consequences and residuals

Twelve items, all measured, none discovered late.

**1. Constitution-plane downgrade for 4 files.**
`resolve_path(CONSTITUTION_GLOBS, 'golden/sample/meta.yaml')` returned `deny`;
`resolve_path(CONSTITUTION_GLOBS, 'examples/log-parser/golden/repr-only/meta.yaml')` returns `allow`.
`CONSTITUTION_GLOBS` (`tools/hooks/contract_guard.py:53`) is repo-root-anchored, so folding root
`golden/` moves those 4 files from agent-write-**denied** to agent-write-**allowed**. Merge-time
CODEOWNERS holds (`/examples/*/golden/  @hjung3113`); only the in-session gate is lost.
**Accepted** rather than widening `CONSTITUTION_GLOBS`, which would be surface growth against SC-8.

**2. `/golden/` is now a stale CODEOWNERS entry, and ADR-0001:48 is contradicted.**
ADR-0001 declares the constitution plane as `contracts/`, `golden/`, `docs/adr/`, `docs/glossary.md`,
and `.github/CODEOWNERS`'s own header says it must not drift from that list. This is the Phase-43
CR-03 class: an accepted ADR left describing a deleted structure. ADRs are append-only and
supersede-don't-edit → **raised in the PR; the ADR was not edited and CODEOWNERS was not edited
here.** The repair belongs with Phase 45's ADR-0008 work or a human call at milestone close.

**3. A gate component disappeared without either requirement naming it.**
`commit_gate`'s golden-parity component is gone (ROADMAP recorded the scope extension). It is a
**removal**, so it does not violate "+0 gates", but it is stated plainly rather than left implicit.
`commit_gate` now composes two components (drift, polyglot).

**4. `secret_scan` has no replacement**, by design (D-06). Secret detection at the tool boundary
stops existing; ADR-0012 already records it as a permanent residual caught at CI/PR review. Adopted
repos lose a hook they may believe is protecting them.

**5. .NET SDK 10 is absent locally.** `require_dotnet` golden cases SKIP; the converter spawn path
runs only in CI's `golden` job. Local verification cannot prove it — stated as a residual rather than
claimed as full local proof.

**6. `format_on_write::resolve_dotnet` is deliberately retained** (SC-5 above). It is a
`dotnet format` toolchain probe, not golden/parity evidence, and it is legitimate in a polyglot
template core. Three hits: `tools/hooks/format_on_write.py:57` (def), `:61` (docstring), `:96`
(call). A future reader grepping for `resolve_dotnet` and expecting zero hits is reading the
pre-correction criterion.

**7. Deferred, unchanged, to Phase 45** — see §7 for the assembled list.

**8. Q3 is closed, with its answer.** `tools/memory_regen/tests/test_agents_md.py` was run at plan
time in a fully-relocated scratch tree and re-confirmed in the full replay: **5 passed**. It does not
red, because `:49` is an `any()` over three alternatives (two of which survive) and the monorepo-map
check is a substring test on committed text, not a filesystem check. This is why Phase 44 leaves
`AGENTS.md`'s non-managed prose to Phase 45.

**9. The six-commit sequence in RESEARCH.md was never replayed end-to-end by the researcher** (its
own MEDIUM confidence). This phase executed a **ten-commit** variant (§3), all green.

**10. A gate lost coverage silently, and it is recorded rather than repaired.**
`tools/harness_lint/tests/test_tests_are_isolatable.py`'s `_members_needing_wiring()` (`:86`) globs
`tools/*/tests`, so once CER-09 relocated the golden runner out of the core tree the relocated
package **permanently drops out of the isolatability gate**. Nothing breaks today — the relocated
suite passes standalone via its own conftest, **measured at closeout: `uv run pytest
examples/log-parser/golden_runner/tests -q` → 17 passed** — and the module docstring's now-stale
citation of the scoped CI command was corrected in plan 05 Task 2 step 7, in the same commit as the
move. Widening the glob to reach the instance tree would be a gate change against SC-8 **and** would
put an instance path token in a core-plane file, which GEN-04 hard-fails
(`tools/harness_lint/tests/test_core_no_example_dep.py`). **Accepted and written down** so the next
reader does not discover it by finding an un-gated package. If a future phase wants the coverage
back, it needs an instance-side gate, not a wider core glob.

**11. `README.md:58` was corrected in plan 02, `README.md:119` was not.** The front page's "Runtime
hooks" row listed `secret-scan` as a shipped control; leaving it would have directly contradicted
consequence 4, so plan 02 dropped it in the same commit as the deletion. `README.md:119`'s
`tools/golden_runner` path spelling is a different residual and remains deferred to Phase 45.

**12. `README.ko.md` is stale in three places and was in no prior deferral list.** `:79` labels
`harness/task-control/  # gate-registry` — a directory that no longer exists (`test -d` → MISSING) —
and the same diagram still lists `golden/` as a root constitution-plane directory and
`tools/…golden_runner`. This is what makes SC-6 not-met-as-worded. **The gap that let it survive four
phases: every prior deferral list names `README.md` (the English file); none names `README.ko.md`.**
Deferred to Phase 45 as a whole file — fixing one of the three stale lines and leaving two would be
worse than deferring them together.

---

## 6. Divergences from the plan's `<measured_anchors>`

Recorded rather than silently absorbed. **None is a red gate**; all three are stale figures or
stale claims in the plan document itself.

1. **The `golden-*` grep anchor is stale.** The plan states plan 04's sweep makes
   `git grep -n "golden-approve\|golden-debug\|golden-testing" -- harness examples` return nothing.
   It returns **5 hits**, all under `examples/log-parser/golden_runner/`; across the full stated
   scope it returns **14**. The anchor was measured before plan 05 relocated the package *into*
   `examples/`. SC-1 itself is unchanged and met; the proxy was narrowed and all 14 hits classified
   (§2, SC-1). 5 of the 14 are genuine staleness owned by Phase 45.
2. **SC-6's "only legitimate history" does not hold** — `README.ko.md:79`. Recorded as not met as
   worded (§2, SC-6; consequence 12).
3. **The ratchet shrink figure is stale**: anchor predicted 84 → 77, observed **84 → 73**. Criterion
   passes either way; the wrong number is not left in the record.

---

## 7. Phase 45 (CER-11) deferral list — assembled

Carried forward unchanged from consequence 7, plus the items surfaced during Waves 4–6:

1. `caps.py` narrative reconciliation beyond what each commit needed.
2. `HARNESS_SIGNATURES` hygiene.
3. `docs/reference/**`.
4. Root `AGENTS.md` outside the HARNESS-MANAGED markers — including `:8-9`'s "the true backstop"
   claim and the golden-path table at `:66-67`.
5. `.memory/derived/**` narrative.
6. The remaining ~17 prose/path spellings of `tools/golden_runner`: `README.md:119`,
   `tools/docs_sync/generate.py:14`, `tools/hooks/contract_guard.py:56`,
   `tools/hooks/format_on_write.py:36`, two `conftest.py:3` docstrings, 5 `pyproject.toml` comments.
7. Stale prose in `docs/how-to/task-lifecycle.md` and the two `docs/explanation/` pages.
8. `docs/glossary.md:20`, `docs/how-to/README.md:11`, and `docs/how-to/approve-a-golden.md` — all
   still naming `/golden-approve`.
9. ADR-0008's supersession (and the ADR-0001 / CODEOWNERS repair from consequence 2).
10. **`tools/hooks/contract_guard.py` `/golden-approve` staleness** — `:9`, `:75`, `:89` plus the
    `GOLDEN_APPROVE_HUMAN` refusal text, and `:55`'s stale `tools/golden_runner/approve.py` path;
    with `tools/hooks/tests/test_contract_guard.py:51` and `:288` asserting that text. Flagged by
    the Wave-4 executor as out of scope there. **(SC-1 bucket C.)**
11. **NEW — `tools/adoption_scan/tests/test_install_completeness.py:196`**: the floor assertion now
    reads `>= 11` but its function is still named `test_discovers_at_least_twelve_modules`. Same
    stale-self-description class this milestone targets; a mechanical rename with no callers.
    Flagged by the Wave-5 executor; **this plan does not claim it.**
12. **NEW — `README.ko.md`, whole file**: `:79`'s `harness/task-control/  # gate-registry` (directory
    deleted), plus its stale `golden/` and `tools/…golden_runner` lines. **This is the SC-6 miss.**
    Note the gap that let it survive four phases: prior deferral lists name `README.md`, never
    `README.ko.md`.

`README.md:58` is **not** deferred — plan 02 removed the `secret-scan` entry (consequence 11).

---

## 8. D-20 — no mutation-proof table is owed

**This phase removes a gate and adds no control**, so D-20 owes no mutation-proof table. Recorded
explicitly rather than left as an absence a reader might mistake for an omission.

Two sanctioned exceptions, both **coverage of retained behavior, extended rather than newly
invented**, each carrying its own recorded mutation result:

| Coverage extension | Plan | Recorded mutation result |
|---|---|---|
| Stale-checkout assertion (`test_settings_merge.py`) | 02 | Removing **either** tombstone from `RETIRED_SIGNATURES` turns the file red; `secret_scan` reds at `test_settings_merge.py:171` |
| CI-path resolution assertion | 04 | Carries its own recorded mutation result, for the same reason |

---

## 9. Deviations from plan

**Execution deviations: none.** No code was changed, no Rule 1–3 auto-fix was applied, no
architectural question arose. This plan ran read-only gates and wrote one file.

Two **plan-document** corrections were escalated to the coordinator rather than decided unilaterally,
because both required choosing between rewriting a criterion and rewriting an observation:

- SC-1's over-matching `golden-*` proxy → resolved as "narrow the proxy, keep the criterion, classify
  all 14 hits" (§2, SC-1).
- SC-6's `README.ko.md:79` → resolved as "record NOT MET AS WORDED, defer the whole file" (§2, SC-6).

`.planning/ROADMAP.md`, `.planning/STATE.md`, `.github/CODEOWNERS`, and `docs/adr/**` were **not**
edited. `GOLDEN_APPROVE_HUMAN` was not forged. `docs/.docs-review-ledger.toml` was not authored.

## Threat Flags

None. This plan introduced no network endpoint, auth path, file-access pattern, or schema change.

---

## Self-Check: PASSED

- `.planning/phases/44-non-goal-surface-removal/44-06-SUMMARY.md` — FOUND
- Working tree outside `.planning/` — clean (`git status --porcelain -- . ':(exclude).planning'` empty)
- All eleven gate commands — exit 0, none red
- Ten code commits `374f991`, `1e79bf6`, `a494cd3`, `ddfa6af`, `f28a9cd`, `18124d3`, `8b5bc41`,
  `8678b45`, `fc69d10`, `df4675c` — all FOUND in `git log`
