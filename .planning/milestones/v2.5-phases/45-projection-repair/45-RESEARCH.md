# Phase 45: Projection Repair - Research

**Researched:** 2026-07-29
**Domain:** Repo self-description integrity — dead controls, duplicated declarations, dangling prose
**Confidence:** HIGH (every number below came from a command run in a scratch clone at HEAD `1b4929a`)

**Measurement environment:** `/private/tmp/claude-501/-Users-hyojung-Desktop-2026-lifetimeworkflow/3dbf62bb-71f5-4875-ba8c-2e143f3f1ac2/scratchpad/wt45`
(`git clone --shared`, checked out `1b4929a`, `uv sync --all-extras --all-packages`).
Real tree verified clean (`git status --porcelain` → empty) before and after.

**Baseline reproduced:** `uv run pytest -q` → **880 passed, 7 snapshots**. `uv run pytest examples/log-parser -q` → **31 passed**. Both match the brief.

---

<user_constraints>
## User Constraints (from 45-CONTEXT.md)

### Locked Decisions

- **D-01:** `golden/**` is REMOVED from the constitution plane, not repointed. ADR-0012 clause (d) supersedes ADR-0001's four-member declaration; Phase 44 made the code move, so the removal is due and needs no new ADR.
- **D-02:** The constitution plane becomes **three members**: `contracts/**`, `docs/adr/**`, `docs/glossary.md`. Update every copy of that list together, in one commit.
- **D-03:** The relocated baselines stay gated at the merge, not in-session. `CODEOWNERS:36` (`/examples/*/golden/`) already covers them. Do NOT add an in-session hook.
- **D-04:** Remove the `*.env` deny rows and the assertion together. Re-adding an enforcer is forbidden.
- **D-05:** Three categories are legitimate and must survive: (a) the relocated `examples/log-parser/golden_runner/**` package, (b) history notes that name a retired artifact in order to record its retirement (`caps.py:124,134`, `test_coexist.py:56`, `test_commands.py:42`), (c) append-only ADR text. Sweep by meaning, never by token.
- **D-06:** Real staleness is a **live file describing a control, path, or command that no longer exists**.
- **D-07…D-13:** The enumerated surface (see Blast Radius below — corrected against measurement).
- **D-14:** ADR-0008 needs a superseding ADR — human-gated; surface at the milestone-close PR, record the gap either way.
- **D-15:** Phase 43's SC-1 wording can never pass as literally written; correct the wording.
- **D-16:** Every live-tree-rendering test is repaired in the SAME commit as the change that invalidates it.
- **D-17:** `git commit -m "<msg>" -- <pathspec>` — message BEFORE `--`. `git rm`/`git mv` already stage. Never `git add -A` / `git add .` / `git commit -a` / `git checkout <ref> -- .`.
- **D-18:** Source-first: edit `harness/**`, then `python -m tools.harness_emit`. Never hand-edit `.opencode/**`, `.claude/**`, or root `opencode.json`. ⚠ But the `AGENTS.md` sites are OUTSIDE the managed block — hand-editing them is correct.
- **D-19:** Run things, don't read them. Verify per commit.
- **D-20:** `uv run pytest -q` does NOT collect `examples/**` (`testpaths = ["libs/python", "tools"]`).
- **D-21:** Done = no glob/deny/CODEOWNERS route matches zero paths while claiming a plane; the constitution list is three members everywhere; no test asserts a deny nothing performs or a drained tautology; `AGENTS.md`, both READMEs and `docs/` name no deleted surface outside ADR text or an explicit history note; `emit-drift`, `stale-derived`, `contract-drift`, ruff ratchet green with an empty diff; `uv run pytest -q` green at every commit.
- **D-22:** No mutation-proof table is owed.
- **D-23:** Report whole-phase LOC from `git diff --shortstat`.

### Claude's Discretion

- Plan/task decomposition and wave count. Tier 1 (D-01…D-04) should land first and separately.
- Whether whole-file deletions under `docs/` ride with their tier or take one commit.
- Exact replacement wording, provided no successor mechanism appears.

### Deferred Ideas (OUT OF SCOPE)

- **PROD-02…05** — the product lifecycle → Phase 46.
- **ADR-0008's superseding ADR** (D-14) — human-gated; surface at the milestone-close PR.
- **A general prose-freshness gate** — explicitly refused.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CER-10 | Both runtime trees re-emit clean; `caps.py`, `emit-manifest.json`, `HARNESS_SIGNATURES`, `contracts/.hashes/manifest.json`, `docs/reference/**`, `.memory/derived/contracts-index.md`, syrupy snapshots regenerated; `gate.needs` repaired; `emit-drift` + `stale-derived` green with an empty diff | **MEASURED ALREADY SATISFIED** — see §"CER-10 is already done". Only residue: a stale `.ruff-baseline` total. |
| CER-11 | Prose naming deleted surface is scrubbed, including the claims outside the emitter's managed block | Full enumerated, measured blast radius below. ⚠ CER-11:105's own citation `AGENTS.md:52-62` is stale — corrected below. |
</phase_requirements>

---

## Summary

The phase is **smaller than CONTEXT thinks in one half and larger in the other**, and both deltas are measured.

**Smaller:** CER-10 requires no work. Running `harness_emit`, `contract_hash.hash`, `docs_sync.generate` and `memory_regen.contracts_index` against a clean HEAD produces an **empty** `git status --porcelain`. `gate.needs` lists all 10 CI jobs and all 10 exist. Phases 43–44 genuinely kept the derived plane green per-commit. CER-10 is a verification step, not a task tier.

**Larger:** the constitution-plane declaration is duplicated in **eleven** places, not four. The four CONTEXT names are correct but incomplete — five more are code/test sites that go red when the data changes (measured: 7 failures across 5 modules, all runtime assertions, **zero collection errors**), and two more are prose sites on the constitution plane itself (`docs/glossary.md:20`, `.github/CODEOWNERS:6-7,27`), which `contract_guard` denies writing in-session without `GOLDEN_APPROVE_HUMAN`. There is a **second** dead CODEOWNERS route (`/approvals/`) nobody has named, and a **third** dead glob (`destinations.py:144`). CONTEXT's D-13 cites a file that does not exist, and D-10 asks to delete a file that is already gone.

**Primary recommendation:** Land Tier 1 as **one commit of 7 files** — validated green in the scratch clone at **874 passed** — then treat everything else as prose commits whose blast radius is now fully enumerated below. Do not attempt the "zero-match assertion": measurement shows it can only be built as a new gate module (§SC-8 verdict).

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Constitution-plane membership | `tools/hooks/contract_guard.py` `CONSTITUTION_GLOBS` | `harness/permission-matrix.json` (inert data) | The Python constant is the **only** thing enforced. The matrix row is read by no production code. |
| Merge-time plane gating | `.github/CODEOWNERS` | — | ADR-0012's thesis; D-03's answer for instance goldens. |
| Emitted runtime surface | `harness/**` source → `tools.harness_emit` | `.opencode/`, `.claude/`, `opencode.json` | Only `harness/skills/two-plane-memory/SKILL.md` among Phase-45 targets reaches the emitted trees. |
| Root rules prose | `AGENTS.md` lines 1–99 (hand-owned) | `AGENTS.md` 100–109 (emitter-owned) | Measured exact boundary. |
| Instance evidence | `examples/log-parser/**` | CODEOWNERS `/examples/*/golden/` | Not collected by `uv run pytest`. |

---

## The Constitution-Plane Declaration: All Eleven Copies

`[VERIFIED: git grep + scratch-clone test run]`

| # | Site | Exact current text (abridged) | In CONTEXT? | What breaks on change |
|---|------|-------------------------------|-------------|------------------------|
| 1 | `tools/hooks/contract_guard.py:52` | `CONSTITUTION_GLOBS = ["contracts/**", "docs/adr/**", "golden/**", "docs/glossary.md"]` | ✅ D-02 | **the source of all 7 failures** |
| 2 | `harness/permission-matrix.json:30` | `"golden/**",` inside `path_deny_globs` | ✅ D-02 | 2 runtime assertions (#5, #7) |
| 3 | `harness/permission-matrix.json:2` (`_note`) | *"The constitution subset is the FOUR members declared by docs/adr/0001-…:48 — contracts/\*\*, docs/adr/\*\*, golden/\*\* and the literal file docs/glossary.md"* | ✅ D-02/`<specifics>` | nothing (prose) |
| 4 | `.github/CODEOWNERS:30` | `/golden/           @hjung3113` | ✅ D-02 | nothing |
| 5 | `tools/harness_perms/tests/test_resolver.py:60` | `assert resolve_path(matrix["path_deny_globs"], "golden/case.verified") == "deny"` (`test_golden_write_denied`) | ✅ D-02 | **runtime assertion** `assert 'allow' == 'deny'` |
| 6 | `tools/hooks/tests/test_contract_guard.py:352-381` | `test_every_declared_plane_member_is_independently_enforced`; probes dict `:361` + set-equality `:364` + message *"ADR-0001:48 declares exactly these four members"* `:365` | ✅ D-02 | **runtime assertion** at `:364` |
| 7 | **`tools/harness_lint/tests/test_agents.py:44`** | `_CONSTITUTION_DENY_GLOBS = ("contracts/**", "docs/adr/**", "golden/**", "docs/glossary.md")` — asserted at `:198` | ❌ **NEW** | **runtime assertion** `:198` `constitution globs missing from path_deny_globs: ['golden/**']` |
| 8 | **`tools/adoption_apply/tests/test_constitution_refusal.py:48`** | parametrized case `"golden/y/baseline.verified.tsv"` | ❌ **NEW** | **runtime** `Failed: DID NOT RAISE ConstitutionRefusal` |
| 9 | **`AGENTS.md:27-28`** | ``…`contracts/`, `docs/adr/`, `golden/`, or `docs/glossary.md` (the four members declared by [ADR-0001](…) §Decision)`` | ❌ **NEW** | nothing (prose, outside managed block) |
| 10 | **`docs/glossary.md:20`** | `\| **Constitution plane** \| Human-owned, gated source of truth: `contracts/`, `golden/`, `docs/adr/`, `docs/glossary.md`. …` | partial (D-10 names `:20` only for `/golden-approve`) | nothing — ⚠ **but the file is constitution-plane; the write is gated** |
| 11 | **`.github/CODEOWNERS:6-7,27`** | `:6-7` *"The plane's four members are declared by docs/adr/0001-…:48; this file must not drift from that list."* · `:27` *"The fourth member is a single FILE, not a tree"* | ❌ **NEW** | nothing (prose) |

**Near-copies that do NOT need the member list changed** (they name `golden/**` incidentally, in docstrings describing the resolver's *shape*, not the plane's membership) — decide by D-06:
`tools/harness_perms/resolver.py:12`, `tools/harness_perms/tests/test_order_resolution.py:9`, `tools/hooks/_stdin.py:51`, `tools/hooks/contract_guard.py:4,17-18`, `tools/hooks/tests/test_contract_guard.py:3,10`.
Each of these is a **live file describing a control that no longer exists** once `golden/**` is dropped, so by D-06 they are stale. Cheap, zero-risk edits — no test asserts their text.

### A twelfth site that reaches the emitted trees

`harness/skills/two-plane-memory/SKILL.md:17` — ``- **What:** `contracts/**`, `docs/adr/**`, `golden/**`, plus the language-neutral spec``

**MEASURED:** this is the **only** Phase-45 target whose repair touches derived artifacts. Editing it + `python -m tools.harness_emit` produces:
```
 M .claude/skills/two-plane-memory/SKILL.md
 M .opencode/skill/two-plane-memory/SKILL.md
 M harness/skills/two-plane-memory/SKILL.md
```
and then **1 failure**: `tools/harness_emit/tests/test_emit_determinism.py::test_projected_tree_matches_committed_snapshot` (runtime, syrupy). Closed by `uv run pytest tools/harness_emit/tests/test_emit_determinism.py --snapshot-update -q` → 1 snapshot updated, then `uv run pytest -q` → **880 passed**. **This is a 4-file commit** (source + 2 emitted + `.ambr`).

---

## Tier 1 — Measured Experiment Results

### Experiment A: remove `golden/**` from both data sites, repair nothing

```bash
# CONSTITUTION_GLOBS 4→3 ; permission-matrix path_deny_globs drops "golden/**"
uv run pytest -q
→ 7 failed, 873 passed
```

| Failing test | file:line | Failure kind | Message |
|---|---|---|---|
| `test_refuses_before_mutation[golden/y/baseline.verified.tsv]` | `tools/adoption_apply/tests/test_constitution_refusal.py:48` | **runtime** | `DID NOT RAISE ConstitutionRefusal` |
| `test_constitution_paths_denied_globally` | `tools/harness_lint/tests/test_agents.py:198` | **runtime** | `constitution globs missing from path_deny_globs: ['golden/**']` |
| `test_constitution_and_secret_paths_denied[golden/repr-only/…]` | `tools/harness_perms/tests/test_order_resolution.py:122` | **runtime** | `assert 'allow' == 'deny'` |
| `test_golden_write_denied` | `tools/harness_perms/tests/test_resolver.py:60` | **runtime** | `assert 'allow' == 'deny'` |
| `test_unapproved_golden_write_denied` | `tools/hooks/tests/test_contract_guard.py:63` | **runtime** | `assert None is not None` |
| `test_approved_constitution_with_crlf_still_denied` | `tools/hooks/tests/test_contract_guard.py:125` | **runtime** | `assert None is not None` |
| `test_every_declared_plane_member_is_independently_enforced` | `tools/hooks/tests/test_contract_guard.py:364` | **runtime** | set-equality: `Extra items in the right set: 'golden/**'` |

**Zero collection errors. All seven are runtime assertions.** No module fails to import.

⚠ Note `test_contract_guard.py:125` (`test_approved_constitution_with_crlf_still_denied`) is a **byte-hygiene** test that merely happened to use a `golden/` probe path. It is not about goldens. Repair = swap the probe to `contracts/x.schema.json`, not delete it.

### Experiment B: D-04 alone — remove `*.env`, `**/*.env` only

```bash
uv run pytest -q  →  3 failed, 877 passed
```

| Failing test | file:line | Kind |
|---|---|---|
| `test_constitution_and_secret_paths_denied[config/prod.env]` | `test_order_resolution.py:122` (param at `:117`) | runtime |
| `test_constitution_and_secret_paths_denied[components/collector/.env]` | `test_order_resolution.py:122` (param at `:118`) | runtime |
| `test_dotenv_denied` | `test_resolver.py:64` | runtime |

`test_order_resolution.py:130` (`test_ordinary_source_paths_allowed`) is **unaffected** — its params are `libs/python/foo.py`, `components/parser/Program.cs`, `tools/hooks/commit_gate.py`. CONTEXT flagged `:130`; measurement says no change needed there.

### Experiment C: full Tier 1 in one commit (data + all test repairs)

7 files changed: `harness/permission-matrix.json`, `tools/hooks/contract_guard.py`, `tools/hooks/tests/test_contract_guard.py`, `tools/harness_perms/tests/test_resolver.py`, `tools/harness_perms/tests/test_order_resolution.py`, `tools/harness_lint/tests/test_agents.py`, `tools/adoption_apply/tests/test_constitution_refusal.py`

```
uv run pytest -q                    → 874 passed, 7 snapshots
uv run python -m tools.harness_emit → git status shows NO emitted-tree change
uv run ruff check .                 → 73 errors (== unmodified baseline; pre-existing)
uv run python -m tools.ruff_baseline→ PASS (73 vs baseline 84)
uv run pytest examples/log-parser -q→ 31 passed
```

**880 → 874** is fully accounted: 3 whole tests deleted (`test_golden_write_denied`, `test_dotenv_denied`, `test_unapproved_golden_write_denied`) + 3 parametrize cases removed from `test_constitution_and_secret_paths_denied`.

### Does Tier 1 touch the emitted trees? **No.**

`[VERIFIED: run]` `tools/harness_emit/permissions.py:23` — `_RESOLVER_ONLY_KEYS = ("_note", "path_deny_globs")`; `generate.py:206` documents the strip. Confirmed empirically: after editing `permission-matrix.json` and re-running `python -m tools.harness_emit`, `git status --porcelain` showed **only the two source files**. Root `opencode.json` contains no occurrence of `golden`, `.env`, or `path_deny`.

---

## D-04, Extended: the whole `path_deny_globs` array is enforcer-less

`[VERIFIED: git grep over non-test `.py`]`

**No production module reads `path_deny_globs`.** The only readers are:
- `tools/harness_emit/permissions.py` — which **strips** it before emit
- three test modules: `test_resolver.py`, `test_order_resolution.py`, `test_agents.py:196`

Every production `resolve_path` caller uses a module-level constant instead:
```
tools/hooks/contract_guard.py:66        resolve_path(CONSTITUTION_GLOBS, …)
tools/adoption_apply/apply.py:87        resolve_path(CONSTITUTION_GLOBS, …)   # imported :51 from contract_guard
tools/adoption_scan/destinations.py:353 resolve_path(CONSTITUTION_GLOBS, …)   # imported :87
tools/adoption_scan/scan.py:269         resolve_path(SECRET_PATH_GLOBS, …)    # its own constant
```

So the honest answer to *"is any other `path_deny_globs` row enforcer-less?"* is: **all of them are, in the strict sense.** The three constitution rows survive scrutiny only because an *identical* list is separately hardcoded in `contract_guard.CONSTITUTION_GLOBS`, which **is** enforced. The `*.env` rows had no such twin — that is the precise asymmetry D-04 names.

**Planning consequence:** after D-04 lands, `path_deny_globs` becomes an exact duplicate of `CONSTITUTION_GLOBS` with no independent enforcer. `test_agents.py:188-198` is the only thing keeping them in sync. That is worth a one-line comment in the `_note`, not a new mechanism (SC-8).

---

## Zero-Match Glob Audit (SC-1) — Measured

Two matchers exist in this repo and they behave differently. `resolve_path` (`resolver.py:47`) is `fnmatchcase`, where `*` crosses `/` and `**` is just `*`. `destination_catalog` (`destinations.py:263`) is `pathlib.Path.glob`, where `**` is recursive. **Any SC-1 assertion must use each declaration's own matcher** — my first probe produced 13 false DEAD verdicts by applying `fnmatchcase` to `_CATEGORY_GLOBS`.

### Genuinely dead declarations in this repo

| Declaration | Site | Matcher | Verdict |
|---|---|---|---|
| `golden/**` | `permission-matrix.json:30` | `fnmatchcase` | **DEAD** |
| `golden/**` | `contract_guard.py:52` | `fnmatchcase` | **DEAD** |
| `*.env` | `permission-matrix.json:32` | `fnmatchcase` | **DEAD** |
| `**/*.env` | `permission-matrix.json:33` | `fnmatchcase` | **DEAD** |
| `golden/**/*` | **`tools/adoption_scan/destinations.py:144`** (`_CATEGORY_GLOBS`) | `pathlib.glob` | **DEAD** — ❌ not in CONTEXT |
| `/golden/` | `.github/CODEOWNERS:30` | git pathspec | **DEAD** (dir missing) |
| `/approvals/` | **`.github/CODEOWNERS:32`** | git pathspec | **DEAD** — ❌ **not in CONTEXT or ROADMAP** |

`destinations.py:144` removal measured: **880 passed, zero failures.** Free.

`/approvals/` — verified `approvals/` does not exist in the tree and is untracked. SC-1's literal wording ("no CODEOWNERS route … matches zero paths while claiming to protect a plane") covers it. It sits in the `# ── Constitution plane (core) ──` block, so it *does* claim a plane.

### NOT dead — do not "fix" these

- **`tools/adoption_scan/scan.py` `SECRET_PATH_GLOBS`** (`*.env`, `**/*.env`, `*.pem`, `*.key`, `id_rsa*`, `.npmrc`, `.netrc`) — all match zero paths *here*, but their subject is a **scanned brownfield target repo**, not this checkout. Matching zero paths here is correct behavior, not a dead control. Any SC-1 assertion must scope to declarations whose subject is *this* repo. **This is the single most important guardrail on SC-1's wording.**
- The other 47 `_CATEGORY_GLOBS` rows — all live under `pathlib.glob`.

---

## The SC-8 Verdict on the Zero-Match Assertion

**Honest answer: it can only be built as a new gate module. SC-8 therefore forbids it as specified.**

What I checked:

| Candidate home | Already scans | Verdict |
|---|---|---|
| `tools/harness_lint/tests/test_agents.py:188-198` (`test_constitution_paths_denied_globally`) | reads `harness/permission-matrix.json`, compares `path_deny_globs` against `_CONSTITUTION_DENY_GLOBS` | **Best fit.** Adding a `git ls-files`-grounded assertion here is coverage of an existing declaration in a module that already loads it. **No new file, no new gate.** |
| `tools/harness_perms/tests/test_resolver.py` | loads the matrix via a `matrix` fixture | Second-best; same argument. |
| `tools/hooks/tests/test_contract_guard.py:352` | mutation-proves `CONSTITUTION_GLOBS` | Fits `CONSTITUTION_GLOBS` only. |
| any module reading `.github/CODEOWNERS` **as a file** | **none exist** | `test_contract_guard.py`, `test_commands.py`, `test_detect.py` all only match the *string* `"CODEOWNERS"` or use fixtures. `.github/CODEOWNERS` is read as a path by `destination_catalog()` (`_CATEGORY_GLOBS:157`) but its **routes are parsed nowhere.** |

**Precedent for the *shape* exists** — `tools/harness_lint/tests/test_core_no_example_dep.py` and `test_core_no_workspace_member_dep.py` both shell out to `git ls-files` and assert over the tracked set. So a `git ls-files`-grounded assertion is an established idiom here, not an invention.

**Recommendation:** split the criterion.
1. **The glob half is safe and cheap.** Add ~6 lines to `test_agents.py` asserting every `path_deny_globs` entry matches ≥1 tracked file under `fnmatchcase`, and ~6 lines to `test_contract_guard.py:352` doing the same for `CONSTITUTION_GLOBS`. Both are *inside existing test functions' modules, over declarations those modules already load*. Net new modules: 0. Net new gates: 0. This is coverage, not surface.
2. **The CODEOWNERS half requires a new parser** with no existing home. Recommend **declining it** and satisfying SC-1's CODEOWNERS clause by *removing* the two dead routes (`:30`, `:32`) — a removal, which is what this milestone does. Record the residual honestly: nothing will mechanically prevent a future dead CODEOWNERS route.
3. **Do not** attempt to cover `_CATEGORY_GLOBS` or `SECRET_PATH_GLOBS` — their subject is a target repo (see above).

---

## CER-10 Is Already Done — Measured

`[VERIFIED: run at clean HEAD in scratch clone]`
```bash
uv run python -m tools.harness_emit
uv run python -m tools.contract_hash.hash
uv run python -m tools.docs_sync.generate
uv run python -m tools.memory_regen.contracts_index
git status --porcelain   →   (empty)
```

`gate.needs` (`.github/workflows/ci.yml:329`) lists `[setup, lang-tests, contract-check, drift, golden, core-suite, lint, emit-drift, stale-derived, workspace]`. All 10 job names exist at `ci.yml:38,79,108,140,157,177,209,235,271,310`. **Nothing to repair.**

**One residual CER-10 item, unnamed anywhere:** `tools/ruff_baseline/baseline.json` records `"total": 84`; the live count is **73**. The ratchet **passes** (shrink is allowed) and prints:
```
ruff ratchet: 73 findings (baseline 84)
  improved    E501: baseline 84 -> found 73
PASS — and findings went DOWN. Record the shrink so it cannot come back:
    uv run python -m tools.ruff_baseline --update
```
This is a claimed count that no longer describes reality — D-06's exact test. `uv run python -m tools.ruff_baseline --update` is a one-command fix that also *tightens* the ratchet. Recommend including it. CI does not currently fail on it.

---

## Blast Radius, Enumerated (D-07 … D-13, corrected against measurement)

### D-07 — Root `AGENTS.md`

**Managed-block boundary, measured exactly:**
```
AGENTS.md:100  <!-- BEGIN HARNESS-MANAGED (generated by tools.harness_emit — do not hand-edit) -->
AGENTS.md:109  <!-- END HARNESS-MANAGED -->
```
**Lines 1–99 are hand-owned. Lines 100–109 are emitter-owned.** Every D-07 site is therefore **outside**; hand-editing is correct and a re-emit will not revert it. `[VERIFIED: applied the edits + `python -m tools.harness_emit` → `git status` showed only ` M AGENTS.md`, unchanged.]`

| Line | Exact current text | Why stale | Breaks |
|---|---|---|---|
| `:7-8` | *"Prose is advisory — the backstop is the SessionStart injector plus the hooks (contract-guard, polyglot-boundary linter)."* | CONTEXT/ROADMAP call this "`:8-9` … the true backstop". **The literal phrase "the true backstop" does not appear in the file.** The stale part is only the enumeration — `secret_scan` is gone but was never listed here. This line is **arguably already correct**; both named hooks still exist. Recommend a light correction, not a rewrite. | nothing |
| `:27-28` | ``…`contracts/`, `docs/adr/`, `golden/`, or `docs/glossary.md` (the four members declared by [ADR-0001](docs/adr/0001-…) §Decision)`` | **copy #9 of the plane list** — must move with D-02 | nothing |
| `:66` | `\| Golden equivalence runner … \| `python -m tools.golden_runner.runner` \|` | module deleted | nothing |
| `:67` | `\| Promote a golden baseline (human-gated) \| `python -m tools.golden_runner.approve --approve --adr <id>` \|` | module deleted | nothing |
| `:79` | `golden/       Constitution plane. Approved equivalence baselines (.verified). Human-promoted only.` | dir deleted; in the **CORE** map block | nothing |
| `:84` | `tools/        The engine (Python): contract_hash, contract_drift, golden_runner, harness_config,` | `golden_runner` relocated | nothing |

⚠ **The gate that almost catches this:** `tools/memory_regen/tests/test_agents_md.py:44` requires the literal `"golden/"` in `AGENTS.md`, and `:48-50` requires `any(("tools.contract_drift", "tools.golden_runner", "uv run pytest"))`.
**MEASURED:** deleting `:66`, `:67`, `:79` keeps it green — `"golden/"` still comes from `:88` (`examples/<instance>/   Own contracts/, golden/, …`, an instance-scoped and correct usage) and `uv run pytest` at `:64` satisfies the `any()`. `uv run pytest tools/memory_regen -q` → **82 passed**; full suite → **880 passed**.
⚠ But this means the gate now pins a structural claim about the *core* map using a line from the *instance* map. Worth a comment; not worth a change (SC-8).

⚠ **ROADMAP/REQUIREMENTS cite the wrong lines.** `.planning/ROADMAP.md:245` and `REQUIREMENTS.md:105` both say **`AGENTS.md:52-62`** ("golden-path table"). Measured: `:52-62` is §B *Working agreements* and is **not stale**; the golden-path table is `:62-71`. The planner should use the line table above, not the requirement's citation.

### D-08 — `tools/hooks/contract_guard.py`

| Line | Exact current text | Issue |
|---|---|---|
| `:4` | ``…the CONSTITUTION plane (``contracts/**`` · ``docs/adr/**`` · ``golden/**`` · ``docs/glossary.md``):`` | plane list |
| `:9` | ``The deny reason names the ``/golden-approve`` + CODEOWNERS ratification path.`` | `/golden-approve` retired |
| `:17-18` | ``NOT the full matrix ``path_deny_globs`` union (which also carries ``*.env``). ``*.env`` is outside this gate's domain`` | after D-04 the union carries no `*.env` — this whole caveat becomes false |
| `:55` | `# GOLDEN_APPROVE_HUMAN precedent (tools/golden_runner/approve.py) — agents must not fabricate it.` | path relocated → `examples/log-parser/golden_runner/approve.py` |
| `:75` | ``* On the constitution plane and NOT ``approved`` -> deny (… names the ``/golden-approve`` + CODEOWNERS ratification path).`` | as `:9` |
| `:89` | `"only be changed via /golden-approve with a human GOLDEN_APPROVE_HUMAN token. "` | **live refusal text**, user-visible |

**MEASURED (Experiment D):** rewriting `:89` to drop `/golden-approve` (→ *"…only be changed by a human who sets GOLDEN_APPROVE_HUMAN, ratified at the PR."*) and repointing `:55` yields exactly **2 failures**, both **runtime**:
```
tools/hooks/tests/test_contract_guard.py:51   assert 'golden-approve' in reason   (test_unapproved_contracts_write_denied)
tools/hooks/tests/test_contract_guard.py:288  assert 'golden-approve' in reason   (test_unapproved_glossary_write_denied)
```
Both must be repaired in the same commit (D-16). `:52` and `:289` (`assert "CODEOWNERS" in reason`) stay green — keep `CODEOWNERS` in the message.
Also `contract_guard.py:87` embeds `(contracts/ · docs/adr/ · golden/ · docs/glossary.md)` in the refusal text — **a thirteenth copy of the plane list, inside a live user-visible string.** Must move with D-02.

### D-09 — READMEs

**`README.md` has 4 stale lines, not 1.** `[VERIFIED: grep]`

| Line | Text | Issue |
|---|---|---|
| `:119` | `uv run python -m tools.golden_runner.runner` | module deleted |
| `:123` | ``…`/verify-work`, `/golden`, `/golden-approve`, `/contract-check`, `/refresh-memory`,`` | `/golden` **and** `/golden-approve` both retired |
| `:124` | ``…`/fan-out-synthesize`, `/pipeline`, `/checkpoint`, and `/review`.`` | **`/pipeline` deleted in Phase 44** — ❌ not in CONTEXT |
| `:141` | `tools/               # Python tooling: harness_emit, contract_drift, golden_runner, memory_regen,` | `golden_runner` relocated |
| `:163` | ``- **Machines gate, humans ratify** — `/golden-approve` refuses to promote a baseline without an`` | command retired |

Live command set (`ls harness/commands/*.md`, 17): `add-language, adopt, adr, agree, build, checkpoint, component, contract-check, docs-sync, fan-out-synthesize, lint, new-contract-rule, orient, refresh-memory, review, test, verify-work`. `/golden`, `/golden-approve`, `/pipeline` are all absent.

**`README.ko.md` — 5 stale lines** (114 lines total; not a whole-file corpse):

| Line | Text | Issue |
|---|---|---|
| `:45` | ``\| **두 평면 메모리** \| *헌법*(`contracts/`·`docs/adr/`·`golden/`)…`` | plane list (copy #14) |
| `:49` | ``\| **기계 게이트, 사람 비준** \| `/golden-approve`는 …`` | command retired |
| `:79` | `  harness/task-control/  # gate-registry` | **dir deleted Phase 43; `gate-registry.json` deleted Phase 44** |
| `:80` | `golden/              # 헌법 평면 — 승인된 등가 baseline` | dir deleted |
| `:82` | `tools/               # Python 도구: harness_emit·contract_drift·golden_runner·memory_regen·` | relocated |

`:81` (`docs/ … + how-to/task-lifecycle.md`) is correct **only if** `task-lifecycle.md` survives — see D-10.
No test reads either README. `[VERIFIED: git grep 'README' in tests → no file reads]` Both are pure prose commits.

### D-10 — `docs/`

⚠ **`docs/how-to/approve-a-golden.md` DOES NOT EXIST.** `[VERIFIED: ls]` CONTEXT D-10 and ROADMAP both call it a "whole file" to delete. It was already removed. The actual live defect is the **dangling inbound link**:
```
docs/how-to/README.md:11  - `approve-a-golden.md` — the `/golden-approve` flow: review a `.received`, promote to `.verified` (machines gate, humans ratify).
```

⚠⚠ **`docs/references/opencode-matt-workflows/` is a vendored third-party bundle — 79 tracked files.** It contains 29 files matching `handoff`, `discipline`, `/handoff` etc. **It is not this repo's account of itself and must be excluded from every `docs/` sweep.** Any instruction of the form "grep `docs/` for X" will produce ~29 false positives without `--exclude docs/references/`. This is the single largest false-positive source in the phase.

| File | Lines | Verdict | Inbound links | Notes |
|---|---|---|---|---|
| `docs/glossary.md` | 37 | **prose correction** (`:20` plane list + `:19` `/golden-approve`) | — | ⚠ **constitution plane.** `resolve_path(CONSTITUTION_GLOBS, "docs/glossary.md") == "deny"` — an in-session Write/Edit is REFUSED without `GOLDEN_APPROVE_HUMAN`, and `CODEOWNERS:31` gates it at merge. Plan for this explicitly. |
| `docs/how-to/README.md` | 16 | **prose correction** | — | `:11` dangling link (file gone); `:14` links `task-lifecycle.md`; `:3` claims *"Hand-authored (constitution plane)"* — **FALSE**, `docs/how-to/**` is not in `CONSTITUTION_GLOBS` and `test_resolver.py:79` explicitly asserts `docs/how-to/task-lifecycle.md` → `allow`. A live false plane claim. |
| `docs/how-to/task-lifecycle.md` | 106 | **CORPSE — delete** (8 command blocks over deleted `tools.risk_router`, `tools.task_control`, `tools.evidence`) | `docs/how-to/README.md:14`, `README.ko.md:81`, `next-milestone-…:330` | ⚠ used as a **negative-control string** at `tools/harness_perms/tests/test_resolver.py:79` and `tools/hooks/tests/test_contract_guard.py:326`. Glob resolution never touches disk, so **deleting the file does NOT red either test** — but both fixtures then name a nonexistent path. Cosmetic; flag, don't necessarily change. |
| `docs/explanation/task-lifecycle-shadow-metrics.md` | 13 | **CORPSE — delete** (metrics for a deleted plane) | **none** | Clean delete. |
| `docs/explanation/next-milestone-task-control-plane.md` | 504 | **CORPSE by subject** — but see blocker | **`docs/adr/0008-task-control-plane-lifecycle.md:50`** — *"Design authority: `docs/explanation/next-milestone-task-control-plane.md` §Phase 6."* | ⚠⚠ **BLOCKER.** Deleting it creates a dangling reference **from an append-only, accepted, constitution-plane ADR** that cannot be edited without a superseding ADR — which D-14 defers as human-gated. **Recommend: do NOT delete this file in Phase 45.** Either keep it with a header note ("historical — the plane it designs was deleted in Phase 43; see ADR-0012") or defer the deletion to the ADR-0008 supersede. State the choice explicitly. |
| `docs/adr/README.md` | 43 | **NOT stale prose** — the index is accurate (0001 & 0010 correctly show `superseded by 0012`). Its only defect is ADR-0008 showing `accepted`, which is **exactly D-14** and human-gated. | — | ⚠ **constitution plane** (`docs/adr/**` → deny). CONTEXT D-10 lists it as carrying "Phase-43 plane prose" — measurement does not support that. Recommend: no change here; the fix belongs to the D-14 superseding ADR. |
| `docs/explanation/agent-workflow-skillset-design-guide.md` | 791 | **prose correction** — matches `handoff`, `/intake` | — | Large file; needs a targeted read, not a whole-file verdict. Only occurrences describing *this repo's* commands are stale. |

**Also unnamed:** `.memory/README.md:25` — ``- `golden/` — approved equivalence baselines (`.verified`), promoted only by human `/golden-approve`.`` Deleted dir + retired command, in the two-plane declaration CONTEXT cites as a *convention reference*. D-06 applies.

**Also unnamed:** `.gitignore:14` — ``# Golden machine-proposed baselines (transient; promoted to .verified only by /golden-approve, P9).`` (`:17` `**/golden/**/baseline.received.tsv` is still correct — it matches the instance path.)

**Also unnamed:** `CLAUDE.md:42,48,73` name `/golden-approve`. ⚠ These sit in the **GSD-managed `## Technology Stack` block** generated from PROJECT.md, not in the HARNESS-MANAGED block (`CLAUDE.md:213-219`). Editing them may be reverted by a GSD regeneration. Recommend leaving them and recording the reason.

### D-11 — Drained assertions

| Item | file:line | Exact text | Verdict |
|---|---|---|---|
| `[] == []` | **`tools/harness_config/tests/test_topology_relationships.py:54-57`** ⚠ **CONTEXT says `tools/harness_lint/tests/` — WRONG PATH** `[VERIFIED: ls tools/*/tests/test_topology_relationships.py]` | `def test_output_is_deterministic() -> None:` / `cfg = load_project()` / `assert effective_relationships(cfg) == effective_relationships(cfg)` | Confirmed drained. Repair = point at a synthetic multi-edge cfg (REVIEW WR-04 supplies one). Sibling `test_accessor_returns_empty_on_linear_default` (`:34`) is similarly weakened but its name is still literally true. |
| name/assert mismatch | `tools/adoption_scan/tests/test_install_completeness.py:196` | `def test_discovers_at_least_twelve_modules(repo_root: Path) -> None:` … `assert len(top_level_packages) >= 11` | **Live count measured = 11** (`adoption_apply, adoption_scan, agree, contract_drift, contract_hash, docs_sync, harness_emit, harness_lint, memory_regen, polyglot_lint, ruff_baseline`). Docstring already explains the 20→12→11 history, so this is a **rename only**. ⚠ **Two** sites: the `def` at `:196` and a comment reference at `:222` (`# non-vacuous, backstopped by test_discovers_at_least_twelve_modules above`). No other callers. |
| `SKIP` vocabulary | `tools/hooks/commit_gate.py:18,60,203` | `:18` *"``main`` exits 0 iff every non-skipped component passes"* · `:60` `"""One component's outcome: ``PASS`` \| ``FAIL`` \| ``SKIP`` + a human-readable detail."""` · `:203` *"A SKIP never blocks and never suppresses a sibling FAIL (T-04-13)."* | Narrow all three to `PASS \| FAIL`. No test asserts these strings — `git grep 'SKIP' tools/hooks/tests/` returns nothing relevant. Pure docstring commit. |

### D-12 — `harness/agents/templates/component-engineer.md`

**Dependents, measured (`git grep`, excluding emitted trees and `.planning/`):**

| Dependent | Suite | Nature |
|---|---|---|
| `tools/harness_lint/tests/test_agent_templates.py:33` | **core** (`uv run pytest`) | `EXPECTED_TEMPLATES = frozenset({"engineer", "component-engineer"})` — exact-set; deleting the file **reds the core suite** |
| `examples/log-parser/tests/test_pipeline_topology.py:115` | **instance only** — ⚠ NOT collected by `uv run pytest` (D-20) | `_CORE_RESOLUTION_DOCS = (_REPO_ROOT / "harness" / "agents" / "templates" / "component-engineer.md",)` |
| `docs/adr/0003-pipeline-topology-slot-and-instance-overlay.md:95` | — | ⚠ **accepted, append-only ADR** describes `/component` copying this template — the step Phase 44 deleted. **ADR-0003 has the same defect as ADR-0008 and nobody has named it.** Add to the D-14 gap record. |

**Stale self-description inside the template:**
- `:6-7` — *"`/component` instantiates a COPY of this file into the active instance's own agents/ directory"* — the step is gone.
- `:12-14` — *"`<STAGE>` (its ordinal in the `[pipeline]`)"* — the core `[pipeline]` table was deleted in Phase 44.

**Verdict: do not delete.** Two live gates depend on it (one core, one instance) and an accepted ADR describes it. The in-scope Phase-45 action is D-06 prose correction of `:6-7` and `:12-14`. Re-wiring `/component` (REVIEW WR-03's alternative) is product work → Phase 46 territory; flag, don't do.

### D-13 — Core suite's dependency on the instance

⚠ **`tools/harness_lint/tests/test_ci_paths.py` DOES NOT EXIST.** `[VERIFIED: ls → No such file]` The test D-13 describes is `test_every_ci_pytest_path_argument_resolves` in **`tools/adoption_scan/tests/test_install_completeness.py`** (REVIEW WR-06 has the correct location; CONTEXT D-13 and ROADMAP do not).

**MEASURED — `git rm -r examples/` then `uv run pytest -q`:**
```
6 failed, 874 passed
```

| Failing test | file:line | Kind | Cause |
|---|---|---|---|
| `test_every_ci_pytest_path_argument_resolves` | `tools/adoption_scan/tests/test_install_completeness.py` | runtime | 3 of 8 `ci.yml` pytest paths are `examples/**` |
| `test_reference_instance_config_is_untouched` | `tools/contract_graph/tests/test_cross_repo_authority.py` | runtime | reads instance config |
| `test_persona_files_exist_on_disk` | `tools/harness_config/tests/test_loader.py` | runtime | `harness/project.toml` `[[languages]].persona` → `examples/…` |
| `test_instance_config_needs_no_explicit_records` | `tools/harness_config/tests/test_topology_relationships.py` | runtime | reads instance config |
| `test_each_configured_persona_exists` | `tools/harness_lint/tests/test_language_config.py:52` | runtime | `'dotnet': persona examples/log-parser/agents/dotnet-engineer.md not found on disk` |
| `test_each_configured_language_has_test_paths` | `tools/harness_lint/tests/test_language_config.py:85` | runtime | `'dotnet': test_paths examples/…/Normalize.Tests.csproj not found on disk` |

**Zero collection errors.** The coupling is **6 tests across 4 modules**, not one — CONTEXT understates it 6×.

**Important distinction for the planner:** 4 of the 6 (`test_loader`, `test_topology_relationships`, `test_language_config` ×2, `test_cross_repo_authority`) fail because `harness/project.toml`'s `[instance]` / `[[languages]]` slot **points at** the instance — which is exactly ADR-0002's design (the instance is DATA in a slot). Deleting `examples/` without also clearing that slot is a half-migration; those failures are arguably *correct*. Only `test_install_completeness`'s `ci.yml` coupling is accidental.

**Recommendation:** Phase 45 should **record** this measured extent (SC-1 does not require fixing it; the ROADMAP files it under Tier 3 "flag"). Fixing it properly = making `harness/project.toml`'s instance slot optional, which is a design change, not projection repair. Fixing only `test_install_completeness` (REVIEW WR-06's patch) would create a **false sense** that the core is instance-independent while 5 other tests still aren't — arguably worse than leaving it recorded. State the choice.

`tools/harness_lint/tests/test_core_no_example_dep.py:44` — `_CORE_ROOTS = ("tools", "harness", "libs")`. Confirmed it scans neither `pyproject.toml` nor `.github/`, so it cannot see either coupling.

### D-15 — Phase 43's SC-1 wording

⚠ **CONTEXT calls it "Phase 43's ROADMAP SC-1 wording". It is not in the ROADMAP.** `[VERIFIED: read .planning/ROADMAP.md:227-233]` The live Phase 43 entry has no numbered success criteria — only a one-line `**Success:** no module imports a deleted package; test_capability_wiring.py is gone with capabilities.toml; the suite is green.` There is no v2.5 milestone archive (`ls .planning/milestones/` → v2.0, v2.1, v2.3, v2.4 only).

**The unsatisfiable wording exists only at `.planning/phases/43-lifecycle-plane-removal/43-VERIFICATION.md:8`:**
```yaml
- must_have: "SC-1 — the ROADMAP's literal bare-token grep over tools/ harness/ contracts/ .github/ .claude/ .opencode/ returns nothing"
```
with the override recorded at `:9-21` (11 matches, all inside a pre-declared `<surviving_residue>` table, negative controls at `tools/contract_graph/tests/test_query.py:70-80`). The verification record itself says *"The literal wording is unsatisfiable-by-construction and should be reworded in the ROADMAP; see WARNING-1."* — but the ROADMAP text it refers to no longer exists.

**Recommendation:** correct the `must_have` string in `43-VERIFICATION.md:8` to the executable-invocation form already recorded at `:16-17`, and note in the phase summary that the ROADMAP half of D-15 is moot. Confirm `tools/contract_graph/tests/test_query.py:70-80` — the forbidden strings there are a **negative control** (`assert forbidden not in source`); stripping them deletes the control. Do not touch.

---

## Recommended Commit Sequence (every commit ends green)

`uv run pytest -q` collects `libs/python` + `tools` only. The instance leg is flagged per commit.

| # | Commit | Files | Expected green | Why |
|---|---|---|---|---|
| **1** | `fix(45): drop golden/** and *.env from the constitution plane (ADR-0012(d))` | `harness/permission-matrix.json` (`:2` `_note`, `:30`, `:32-33`), `tools/hooks/contract_guard.py` (`:52` + `:4,:9,:17-18,:55,:75,:87,:89`), `tools/hooks/tests/test_contract_guard.py` (`:51`, `:61-64` del, `:124` probe swap, `:288`, `:361` del, `:365` msg), `tools/harness_perms/tests/test_resolver.py` (`:59-64` del), `tools/harness_perms/tests/test_order_resolution.py` (`:9` docstring, `:113,117,118` params), `tools/harness_lint/tests/test_agents.py` (`:44`), `tools/adoption_apply/tests/test_constitution_refusal.py` (`:48` param) | **`uv run pytest -q` → 874 passed, 7 snapshots** | **MEASURED (Experiment C).** All 7 test repairs ride with the data change per D-16. Emit verified unchanged — **no `harness_emit` run needed**. Instance leg unaffected (31 passed, verified). |
| **2** | `fix(45): remove dead CODEOWNERS routes and adoption catalog glob` | `.github/CODEOWNERS` (`:6-7` prose, `:27` prose, `:30` del, `:32` del), `tools/adoption_scan/destinations.py:144` (del) | **880−6 = 874 passed** | **MEASURED:** `destinations.py:144` removal alone → 880 passed, 0 failures. CODEOWNERS is read by no test's route parser. Safe to merge into commit 1 if preferred, but keeping it separate isolates the security-relevant half. |
| **3** | `docs(45): correct the two-plane skill's constitution list` | `harness/skills/two-plane-memory/SKILL.md:17`, `.claude/skills/two-plane-memory/SKILL.md`, `.opencode/skill/two-plane-memory/SKILL.md`, `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` | **874 passed, 7 snapshots** | **MEASURED:** requires `python -m tools.harness_emit` **and** `pytest tools/harness_emit/tests/test_emit_determinism.py --snapshot-update`. Without the snapshot regen: 1 failure at `test_emit_determinism.py:81`. The **only** commit in this phase that touches emitted trees. |
| **4** | `docs(45): repair root AGENTS.md and both READMEs` | `AGENTS.md` (`:7-8,:27-28,:66,:67,:79,:84`), `README.md` (`:119,:123,:124,:141,:163`), `README.ko.md` (`:45,:49,:79,:80,:82`) | **874 passed** | **MEASURED:** AGENTS.md edits keep `tools/memory_regen` green (82 passed) and survive a re-emit unchanged. No test reads either README. Hand-edit is correct — all sites are outside `AGENTS.md:100-109`. |
| **5** | `docs(45): delete lifecycle-plane doc corpses; fix dangling index links` | `git rm docs/how-to/task-lifecycle.md docs/explanation/task-lifecycle-shadow-metrics.md`; edit `docs/how-to/README.md` (`:3` false plane claim, `:11` dangling link, `:14` removed link), `.memory/README.md:25`, `.gitignore:14`, `docs/explanation/agent-workflow-skillset-design-guide.md` | **874 passed** | ⚠ **`README.ko.md:81` links `task-lifecycle.md` — must be fixed in this same commit or it becomes a new dangling reference.** ⚠ `docs/explanation/next-milestone-task-control-plane.md` **NOT deleted** (blocked by ADR-0008:50). ⚠ Verify `docs/references/**` is untouched. |
| **6** | `test(45): re-subject drained assertions; align test name with floor` | `tools/harness_config/tests/test_topology_relationships.py:54-57`, `tools/adoption_scan/tests/test_install_completeness.py:196,222`, `tools/hooks/commit_gate.py:18,60,203` | **874 passed** | Rename is mechanical (2 sites, no external callers, verified). `commit_gate` is docstring-only. Re-subjecting the determinism test *strengthens* it. |
| **7** | `docs(45): correct component-engineer template self-description` | `harness/agents/templates/component-engineer.md:6-7,12-14` | **874 passed** + ⚠ **`uv run pytest examples/log-parser -q` → 31 passed** | ⚠ **Requires the explicit instance leg (D-20)** — `examples/log-parser/tests/test_pipeline_topology.py:115` reads this file and is NOT collected by `uv run pytest`. This is the one commit in the phase that needs it. |
| **8** | `chore(45): record the record — ratchet, verification wording, ADR gaps` | `tools/ruff_baseline/baseline.json` (via `uv run python -m tools.ruff_baseline --update`), `.planning/phases/43-lifecycle-plane-removal/43-VERIFICATION.md:8` | **874 passed**, ratchet PASS at 73/73 | Also record the D-14 gap for **ADR-0008 *and* ADR-0003** (both accepted, both describe deleted surface). Do not author either ADR — human-gated. |

**Commits needing the explicit instance leg (D-20):** #7 only. Commit #1 was verified against the instance anyway (31 passed) and is unaffected.

**Commits touching the constitution plane** (in-session write DENIED without `GOLDEN_APPROVE_HUMAN`; CODEOWNERS-gated at merge): `docs/glossary.md:19-20` — **not scheduled above.** The planner must decide whether to (a) fold it into commit #4 accepting the gate, or (b) defer it to the milestone-close human PR alongside D-14. Recommend (b): it is one table row, it is on the plane whose own rules say a human ratifies, and bundling it with the ADR-0008 supersede is coherent. Record it either way — SC-5 names `docs/` explicitly.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Detecting a dead glob | a new `tools/glob_audit/` package | ~6 lines added to `test_agents.py` / `test_contract_guard.py:352` using `git ls-files` | SC-8: +0 gates/tools. Precedent: `test_core_no_example_dep.py`, `test_core_no_workspace_member_dep.py` already use this idiom. |
| Detecting stale prose | a prose-freshness checker / re-adding `docs_guard` | nothing | Explicitly refused by CONTEXT `<deferred>` and ROADMAP non-goals. It is the class this milestone removes. |
| Re-covering instance goldens in-session | widening `CONSTITUTION_GLOBS` to `examples/*/golden/**` (REVIEW CR-01's proposed fix) | `CODEOWNERS:36` | **D-01/D-03 supersede CR-01.** ADR-0012(d) removed the member; CR-01 predates that reading. Do not implement CR-01's patch. |
| Regenerating derived artifacts | manual edits to `.opencode/`, `.claude/`, `opencode.json`, `.ambr`, `contracts/.hashes/` | `python -m tools.harness_emit`; `pytest … --snapshot-update` | `emit-drift` reds on hand-edits. Only commit #3 needs either. |
| YAML edits to `ci.yml` | ad-hoc ruamel config | **not needed this phase** — `gate.needs` verified correct | Avoids Phase 44's measured 162-line spurious rewrite entirely. |

---

## Common Pitfalls

### Pitfall 1: Sweeping `docs/` by token
**What goes wrong:** `git grep handoff -- docs/` returns 29 files, 25 of them inside `docs/references/opencode-matt-workflows/` — a vendored third-party bundle (79 tracked files) that is not this repo's self-description.
**How to avoid:** every `docs/` command must carry `':!docs/references/'`. Also exclude `docs/adr/` (append-only, D-05c).
**Warning sign:** a file count above ~10 for any single token.

### Pitfall 2: Assuming a listed site exists
**What goes wrong:** `docs/how-to/approve-a-golden.md` (D-10, ROADMAP) and `tools/harness_lint/tests/test_ci_paths.py` (D-13, ROADMAP) **do not exist**. A plan that says "delete X" for a missing X either no-ops silently or `git rm` exits non-zero.
**How to avoid:** `ls` every path in the plan before the first commit.

### Pitfall 3: Trusting the requirement's own line numbers
**What goes wrong:** `REQUIREMENTS.md:105` and `ROADMAP.md:245` both cite `AGENTS.md:52-62` as the stale golden-path table. Measured: `:52-62` is §B *Working agreements* and is not stale; the table is `:62-71`. `AGENTS.md:8-9` similarly does not contain the phrase "the true backstop" that CONTEXT quotes.
**How to avoid:** use the measured table in this document.

### Pitfall 4: Editing the wrong side of the managed-block boundary
**Measured boundary:** `AGENTS.md:100` BEGIN … `:109` END. All Phase-45 `AGENTS.md` targets are `:7-84`, i.e. **outside**. Hand-edit them. Verified: `python -m tools.harness_emit` after the edits leaves them intact.

### Pitfall 5: Two matchers, one word "glob"
`resolve_path` = `fnmatchcase` (`*` crosses `/`, `**` ≡ `*`). `destination_catalog` = `pathlib.Path.glob` (`**` recursive). Probing one declaration with the other's matcher produced 13 false DEAD verdicts in my first pass.

### Pitfall 6: Reporting a `SECRET_PATH_GLOBS`-style declaration as dead
Its subject is a **scanned target repo**, not this checkout. Zero matches here is correct behavior.

### Pitfall 7: Deleting a doc an accepted ADR cites
`docs/adr/0008:50` cites `next-milestone-task-control-plane.md`; `docs/adr/0003:95` cites `component-engineer.md`. ADRs are append-only and constitution-plane — you cannot repair the reference. Deleting either target creates a permanent dangling reference from the constitution plane.

---

## Runtime State Inventory

Rename/refactor phase — all five categories answered.

| Category | Items found | Action required |
|---|---|---|
| **Stored data** | None — verified: no database or datastore in this repo (`git ls-files` shows no `.db`/`.sqlite`; `contracts/.hashes/manifest.json` is the only content-addressed store and re-hashing it produced an empty diff). | none |
| **Live service config** | None — verified: no external service integration. `.mcp.json` exists but declares MCP servers for the developer's editor, not repo state. | none |
| **OS-registered state** | None — verified: `harness/git-hooks/` matches zero tracked files (measured in the glob audit); no `launchd`/`systemd`/pm2 artifacts tracked. | none |
| **Secrets / env vars** | `GOLDEN_APPROVE_HUMAN` (`contract_guard.py:56`) and `HARNESS_DEV_BYPASS` — **both keep their names**; only prose describing them changes. `*.env` deny rows are being deleted but no `.env` file is tracked (`git ls-files '*.env'` → empty). | none |
| **Build artifacts** | `tools/ruff_baseline/baseline.json` records `total: 84` while live ruff yields **73** — a stale committed derived count. `uv.lock` unaffected (no dependency change). No `.egg-info` tracked. | `uv run python -m tools.ruff_baseline --update` (commit #8) |

---

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|---|---|---|---|---|
| `uv` | every test leg | ✓ | resolves 50 pkgs | — |
| Python | core + instance suites | ✓ | 3.11.15 (uv-managed) | — |
| `tree-sitter`, `networkx` | `tools/memory_regen` tests | ✓ **only after `uv sync --all-extras --all-packages`** | tree-sitter 0.25.2, networkx 3.6.1 | — |
| `ruff` | ratchet | ✓ | 0.15.20 (per `baseline.json`) | — |
| `.NET` SDK | `examples/log-parser` .NET twin | not probed | — | instance Python leg (31 tests) passed without it |

⚠ **A plain `uv sync` is insufficient.** In a fresh clone, `uv run pytest -q` fails with **2 collection errors** (`ModuleNotFoundError: tree_sitter`, `networkx`) in `tools/memory_regen/tests/`. `uv sync --all-extras --all-packages` fixes it. If the executor works in a fresh worktree, this must be the first command.

---

## Validation Architecture

### Test framework

| Property | Value |
|---|---|
| Framework | pytest 8.x + syrupy (`.ambr` snapshots) |
| Config | `pyproject.toml` `[tool.pytest.ini_options] testpaths = ["libs/python", "tools"]` |
| Quick run | `uv run pytest -q` (~11 s, 880 tests at HEAD) |
| Instance leg | `uv run pytest examples/log-parser -q` (~3 s, 31 tests) — **not** covered by the quick run |
| Snapshot update | `uv run pytest <path> --snapshot-update -q` |
| Ratchet | `uv run python -m tools.ruff_baseline` |
| Emit determinism | `uv run python -m tools.harness_emit` then `git status --porcelain` |

### Requirements → test map

| Req | Behavior | Type | Automated command | Exists? |
|---|---|---|---|---|
| CER-10 | derived plane re-emits clean | integration | `uv run python -m tools.harness_emit && git status --porcelain` (expect empty) | ✅ + `test_emit_determinism.py` |
| CER-10 | contract hashes current | integration | `uv run python -m tools.contract_hash.hash && git status --porcelain` | ✅ |
| CER-11 | plane list is 3 members everywhere enforced | unit | `uv run pytest tools/hooks/tests/test_contract_guard.py -x -q` | ✅ `:352` |
| CER-11 | matrix ↔ guard stay in sync | unit | `uv run pytest tools/harness_lint/tests/test_agents.py -x -q` | ✅ `:188` |
| CER-11 | AGENTS.md structural claims hold | unit | `uv run pytest tools/memory_regen -q` | ✅ `test_agents_md.py` |
| SC-1 | no declared glob matches zero paths | unit | **none** | ❌ — see SC-8 verdict; recommend extending `test_agents.py` + `test_contract_guard.py:352` |
| D-12 | template still resolvable by the instance | integration | `uv run pytest examples/log-parser/tests/test_pipeline_topology.py -q` | ✅ but **not in the default run** |

### Sampling rate
- Per commit: `uv run pytest -q` (expect **874** from commit 1 onward).
- Commit #7 additionally: `uv run pytest examples/log-parser -q` (expect 31).
- Commit #3 additionally: `uv run python -m tools.harness_emit && git status --porcelain` must show only the 4 intended files.
- Phase gate: `uv run pytest -q` + instance leg + `harness_emit` empty diff + `ruff_baseline` PASS.

### Wave 0 gaps
None — the framework, config, and fixtures all exist. The only *new* test code recommended is the ~12-line zero-match extension inside two existing modules (see SC-8 verdict).

---

## Security Domain

`security_enforcement` is not set in `.planning/config.json`; treating as enabled.

### Applicable ASVS categories

| ASVS | Applies | Standard control in this repo |
|---|---|---|
| V2 Authentication | no | no auth surface |
| V3 Session Management | no | — |
| **V4 Access Control** | **yes** | `contract_guard` PreToolUse deny + `GOLDEN_APPROVE_HUMAN` + CODEOWNERS. **Phase 45 narrows this control's scope by design (D-01).** |
| V5 Input Validation | yes | `tools.polyglot_lint.lint_bytes` on constitution writes — unchanged |
| V6 Cryptography | yes | JCS SHA-256 in `contract_hash` — untouched |

### Threat patterns

| Pattern | STRIDE | Mitigation after Phase 45 |
|---|---|---|
| Agent self-blesses a golden baseline (Pitfall P9) | Tampering | ⚠ **In-session enforcement is being removed by D-01.** Residual = `CODEOWNERS:36` (`/examples/*/golden/`) at the PR. ADR-0012 ratifies this posture. ⚠ CODEOWNERS is **advisory** unless "Require review from Code Owners" is enabled (documented at `.github/CODEOWNERS:9-14`) — that toggle is not verifiable from the repo. **This is the phase's one genuine risk increase and it should be stated in the summary, not buried.** |
| Agent writes a secret to a `.env` | Info Disclosure | ⚠ **The deny row is being removed by D-04 and was already unenforced.** No new exposure — the control was already fictional. Residual per ADR-0012: caught at CI/PR review. |
| Agent edits the guard to bypass a deny | Tampering | `AGENTS.md:31-32` prohibition (prose) + `docs/adr/**` gating on the ADR that authorizes changes. Unchanged. |
| Constitution write with BOM/CRLF | Tampering | `contract_guard.decide` byte-hygiene path. Unchanged — but ⚠ `test_approved_constitution_with_crlf_still_denied` currently probes via a `golden/` path; if the repair *deletes* rather than *re-subjects* it, this control loses its only test. **Re-subject, don't delete.** |

---

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|---|---|---|
| A1 | `docs/explanation/agent-workflow-skillset-design-guide.md` (791 lines) needs prose correction rather than deletion | D-10 | I matched tokens but did not read all 791 lines. A planner should read it before assigning a verdict. Low — worst case is one extra correction pass. |
| A2 | `docs/how-to/task-lifecycle.md` and `task-lifecycle-shadow-metrics.md` are whole-file corpses | D-10 | I read the headers and confirmed the modules they invoke are deleted, but did not read all 106+13 lines. Low. |
| A3 | The exact replacement wording for `contract_guard.py:89` (`"…changed by a human who sets GOLDEN_APPROVE_HUMAN, ratified at the PR."`) is acceptable | Commit 1 | CONTEXT grants wording discretion; I verified only that the 2 asserting tests are the sole constraint. Low. |
| A4 | CI's `golden` and `workspace` jobs pass at HEAD | Ordering | Not run (requires GitHub Actions + .NET). The instance Python leg passed locally (31). Medium — a planner should not assert CI green without running it. |
| A5 | `CLAUDE.md:42,48,73` are regenerated by GSD and should be left alone | D-10 addendum | Inferred from the `## Technology Stack` heading and the generator note at `:207`. Low — worst case is 3 uncorrected prose lines in a GSD-managed file. |

---

## Open Questions

1. **Should `docs/glossary.md:19-20` be corrected in-phase or deferred to the human PR?**
   - Known: it is constitution-plane; `resolve_path(CONSTITUTION_GLOBS, "docs/glossary.md") == "deny"`; SC-5 names `docs/` and would fail without it.
   - Unclear: whether the executor has `GOLDEN_APPROVE_HUMAN` available.
   - Command that answers it: `env | grep GOLDEN_APPROVE_HUMAN` in the executor's session, or `HARNESS_DEV_BYPASS=1` (`contract_guard.py` dev path, `test_contract_guard.py:228`).
   - Recommendation: defer to the milestone-close PR with D-14; record the deferral.

2. **Is `docs/explanation/next-milestone-task-control-plane.md` deletable given ADR-0008:50?**
   - Known: deleting it dangles an append-only, accepted ADR.
   - Unclear: whether the owner considers a dangling link from a to-be-superseded ADR acceptable.
   - Command that answers it: none — this is a human decision. Surface at the PR.
   - Recommendation: keep the file with a one-line historical header in Phase 45.

3. **Does branch protection have "Require review from Code Owners" enabled?**
   - Known: without it, D-03's compensating control for instance goldens is advisory only (`.github/CODEOWNERS:9-14` documents this).
   - Command that answers it: `gh api repos/:owner/:repo/branches/main/protection --jq '.required_pull_request_reviews.require_code_owner_reviews'`.
   - Recommendation: run it and record the answer in the phase summary. If `false`, D-01 is a net reduction in enforcement with no compensating control — the owner should know before merge.

4. **Should the 5 non-`test_install_completeness` core→instance couplings be fixed, recorded, or both?**
   - Known: 6 tests across 4 modules fail when `examples/` is deleted; 4 of them are driven by `harness/project.toml`'s `[instance]` slot, which is ADR-0002's intended design.
   - Unclear: whether "the core depends on no instance" is meant to hold with the slot *populated*.
   - Command that answers it: read `docs/adr/0002-general-template-de-specialization.md` §Decision and `docs/explanation/template-and-instances.md` for the slot's intended semantics.
   - Recommendation: record the measured extent; do not partially fix.

---

## Sources

### Primary (HIGH — commands run in the scratch clone)
- `uv run pytest -q` — baseline and 5 mutation experiments (880 / 873 / 877 / 874 / 879 / 874)
- `uv run pytest examples/log-parser -q` — 31 passed
- `uv run python -m tools.harness_emit` + `git status --porcelain` — emit-drift measurement
- `uv run pytest … --snapshot-update` — syrupy blast radius
- `uv run ruff check .` + `uv run python -m tools.ruff_baseline` — 73 vs baseline 84
- `git rm -r examples && uv run pytest -q` — D-13 coupling (6 failures)
- `uv run python` glob-audit script over `git ls-files` with both matchers
- `git grep -n` across `CONSTITUTION_GLOBS`, `path_deny_globs`, `golden/**`, `/golden-approve`, deleted-token list
- `ls` existence checks on every path named by CONTEXT D-07…D-13

### Secondary (HIGH — repo documents read directly)
- `.planning/phases/45-projection-repair/45-CONTEXT.md`
- `.planning/ROADMAP.md` §Phase 45 (SC-1…SC-8) and §Phase 43/44
- `.planning/REQUIREMENTS.md` CER-10, CER-11
- `docs/adr/0012-ci-and-merge-as-decision-authority.md:139-152` — clause (d), the authority for D-01
- `.planning/phases/44-non-goal-surface-removal/REVIEW.md` — CR-01, CR-02, WR-01…WR-09
- `.planning/phases/43-lifecycle-plane-removal/43-VERIFICATION.md:1-21`
- `CLAUDE.md`, root `AGENTS.md`, `.github/CODEOWNERS`

### Tertiary
None. No web search was used; every claim is grounded in this repository.

---

## Metadata

**Confidence breakdown:**
- Tier 1 blast radius: **HIGH** — every failure reproduced with file:line and failure kind.
- Zero-match audit: **HIGH** — run with each declaration's own matcher, false positives corrected.
- CER-10 status: **HIGH** — regeneration produced an empty diff.
- Doc corpse verdicts: **MEDIUM** — token-matched and header-read; two large files not read end-to-end (A1, A2).
- CI job status: **MEDIUM** — local legs verified; GitHub Actions not run (A4).

**Research date:** 2026-07-29
**Valid until:** until the next commit to `harness/`, `tools/`, `docs/`, or `.github/` — every measurement is HEAD-`1b4929a`-specific.
