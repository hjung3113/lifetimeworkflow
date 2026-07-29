# Phase 42: Adoption Decoupling + Install-Set Repair - Research

**Researched:** 2026-07-28
**Domain:** Removing an in-repo coupling (Python import + env-gated human-token check) and adding
one glob row to an install-set catalog. No new library, framework, or pattern involved — this is a
file:line-precise coupling map plus test-blast-radius accounting.
**Confidence:** HIGH (every claim below is grep/read-verified against the live tree at commit
matching `.planning/STATE.md`'s `stopped_at: Phase 42 context gathered`, 2026-07-28)

## Summary

Phase 42 is two small, independently-verifiable changes riding in one phase because ADR-0012
bundles them: (1) delete `tools/adoption_apply/approval.py` (the whole ADOPT-06 gate) and its one
`from tools.task_control.manager import show` import (`approval.py:37`), leaving `apply.py`'s two
stale docstrings (`:207`, `:241`) as the only remaining "task_control" residue — the ~60-LOC atomic
create/replace sequence they describe is **already** inlined, not something this phase needs to
port; and (2) add one `"tools/**"` row to `_CATEGORY_GLOBS` (`destinations.py:142-181`) so a target
monorepo receives the Python its own installed commands and CI invoke. Both changes are small in
diff size; the actual **cost center of this phase is test and prose blast radius**, not code. The
`approval` gate is exercised by ~10 tests in `test_cli.py` (most of which call a `_promote` helper
before `apply` — that helper and its precondition go away) plus the entire 435-line
`test_approval_invalidation.py` (deleted outright), plus one non-obvious break:
`test_scan_exclusions.py:211` reads `scan._GATE_REGISTRY_PATH` directly as an independent
cross-check and will raise `AttributeError` once that constant is inlined away — this is a
functional test dependency, not prose, and must be rewritten to point at the new local tuple.

Three tree-vs-prose divergences the ROADMAP itself flags were re-verified and confirmed: (1) the
requirement prose says 7 secret patterns, the live `gate-registry.json` has exactly **8** (counted
directly); (2) the atomic create/replace sequence in `apply.py` is **already inlined** — only its
two docstrings still say "mirrors task_control"; (3) the coupling is in `approval.py`, not
`apply.py`. A fourth, smaller divergence not previously flagged: CONTEXT.md's canonical-refs list
cites `.claude/skills/adopt/SKILL.md` — **no such file exists**; only
`harness/skills/brownfield-adoption/SKILL.md` documents the adoption lifecycle. Plan against
`brownfield-adoption`, not a nonexistent `adopt` skill.

**Primary recommendation:** Delete `approval.py` + its two CLI call sites + its dedicated test
file; leave `apply.py`'s inlined sequence untouched except its two docstring sentences; rewrite
(not delete) `test_cli.py`'s ~7 surviving apply-path tests to drop their `_promote` precondition
calls; inline the 8 `secret_patterns` as a module-level tuple in `scan.py` next to
`SECRET_PATH_GLOBS` and fix the one test that reads the old path constant directly; add exactly one
`"tools/**"` glob row to `_CATEGORY_GLOBS`; prove PROD-01 with one new fixture-install test that
walks `harness/commands/**/*.md` + `.github/workflows/*.yml` for every `python -m tools.X`
reference and asserts the module exists post-apply, not by inspection.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Delete the ADOPT-06 approval gate whole — `approval.py`, the `promote` subcommand
  (`cli.py:222-243`, `:266`), the `check_valid` refusal that gates `apply` (`cli.py:146-155`), the
  `approval` imports (`cli.py:41-46`), and the approval-gate tests.
- **D-02:** The orphaned contract goes with it — delete `contracts/harness/adoption/approval.schema.json`
  and rebaseline `contracts/.hashes/manifest.json` in the same commit (Phase-41 procedure). The
  other three adoption contracts (`inventory`, `plan`, `manifest`) stay.
- **D-03:** `apply` no longer refuses on a missing promotion. `draft → apply`; the review is the PR.
  Do not invent a replacement local gate.
- **D-04:** Secret patterns become a module-level tuple in `scan.py`, adjacent to
  `SECRET_PATH_GLOBS` (`:52-54`) — follow that precedent, not a new idiom. Keep the
  `functools.lru_cache`-compiled combined regex and `re.IGNORECASE` as-is (`scan.py:108-113`).
- **D-05:** There are **8** patterns, not 7 (verified). Copy byte-identical. Proof of fidelity is
  that the existing secret-redaction tests pass **unchanged** — do not edit a redaction test to fit
  the move; if one fails, the copy is wrong.
- **D-06:** `gate-registry.json` itself is NOT deleted here (Phase 44 owns it). Only
  `scan.py:48`'s `_GATE_REGISTRY_PATH` read goes away.
- **D-07:** Use a blanket `tools/**` glob, not an enumerated package list — a data row, robust to
  Phases 43/44 deleting packages later.
- **D-08:** Prove PROD-01 with a fixture-install test: for every `uv run python -m tools.X`
  referenced by an emitted command or `.github/workflows/**`, assert module `X` exists in the
  installed target tree. A test that walks the references is the deliverable.
- **D-09:** Shipping the packages' `tests/` directories along with them is accepted (D-07: data
  row, not a mechanism).
- **D-10:** `apply.py`'s docstrings at `:207`/`:241` must stop pointing at task-control — the
  sequence is already inlined, only the prose is stale.
- **D-11:** Same sweep applies to `cli.py:6`'s module docstring and any test docstring naming the
  approval/task-revision binding.
- **D-12:** Per task: delete → `git add` → `git commit -- <pathspec>` → verify → amend-if-red.
  `destinations.py:217` reads `git ls-files`, so tracked deletions red until staged AND committed.
- **D-13:** `git commit -- <pathspec>` every time; `git diff --cached --name-only` inspected first.
  Never `git add -A`/`git add .`/`git commit -a`. Never `git checkout <ref> -- .`.
- **D-14:** Run things rather than reading them.
- **D-15:** Done = `uv run pytest -q` green; the two named greps return nothing; `draft → apply`
  completes with `GOLDEN_APPROVE_HUMAN` unset; the fixture-install test passes; `emit-drift`,
  `stale-derived`, `contract-drift` (rebaselined), and the ruff ratchet clean.
- **D-16:** No mutation-proof table is owed — this phase removes a gate and adds no control.
- **D-17:** Report changed LOC from `git diff --stat`, not estimated.

### Claude's Discretion

- Plan/task decomposition and wave count.
- Whether the contract deletion (D-02) rides with the `approval.py` deletion or gets its own commit.
- The fixture-install test's exact location and fixture shape.

### Deferred Ideas (OUT OF SCOPE)

- Delete `gate-registry.json`, `secret_scan`, `deny-domains.*` → Phase 44 (CER-08).
- Delete `tools/task_control` and the lifecycle plane → Phase 43 (CER-07).
- Filtering `tests/` out of the shipped install set → follow-up only if D-09's accepted bloat
  proves objectionable.

</user_constraints>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CER-06 | `adoption_apply` decoupled from task-control: no `task_control.manager.show`, no task-revision binding, no `GOLDEN_APPROVE_HUMAN`; secret patterns inlined from `gate-registry.json` | §Coupling Map, §Blast Radius, §Secret-Pattern Rebaseline below — the one live import (`approval.py:37`), the one live consumer (`scan.py:110-113`), and the full test-file inventory that must change |
| PROD-01 | `_CATEGORY_GLOBS` ships the `tools/**` Python its own commands/CI invoke | §Install-Set Mechanics — confirms today's glob list has zero `tools/**` entry, enumerates the 21 distinct `tools.X` modules actually invoked, and confirms no existing snapshot/count test breaks from the addition |

## Project Constraints (from CLAUDE.md)

- `harness/` is the runtime-neutral SOURCE; `.opencode/` and `.claude/` are EMITTED by
  `python -m tools.harness_emit`. Never hand-edit an emitted tree.
- `contracts/**` is the constitution plane. `git rm` (Bash) does not trigger `contract_guard`'s
  `Write|Edit`-only matcher — re-confirmed below (§Rebaseline Procedure), matching Phase 41's
  finding verbatim.
- Python is a `uv` workspace (`members = ["libs/python", "tools/*"]`); `tools/adoption_apply` and
  `tools/adoption_scan` both declare `dependencies = []` and `package = false` (virtual members,
  shared venv) — removing the `task_control` import needs **no** `pyproject.toml`/`uv.lock` edit,
  unlike Phase 41's actual member removal.
- GSD workflow enforcement: route through `/gsd:plan-phase` → `/gsd:execute-phase`, not direct edits.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Adoption draft/apply pipeline | DEV tooling (`tools/adoption_*`, imported at dev-time, never installed as a runtime service) | PRODUCT install-set (`_CATEGORY_GLOBS` ships the Python) | Runs inside this checkout during `/adopt`, but per ADR-0012(c) the *code itself* (`tools/adoption_apply/**`, `tools/adoption_scan/**`) is also a shipped PRODUCT artifact once installed into a target — the dual nature is exactly why PROD-01 exists |
| Human ratification of an adoption batch | Removed — was DEV-session gate (`GOLDEN_APPROVE_HUMAN`) | PR review (GitHub) | D-03: CI + merge are the authority (ADR-0012a); no in-process token check replaces it |
| Secret-pattern redaction during scan | DEV/PRODUCT shared library (`tools/adoption_scan/scan.py`, ships as part of `tools/**`) | — | Pure data + regex, no external service; owned locally after this phase, same as `SECRET_PATH_GLOBS` |
| Install-set catalog (`_CATEGORY_GLOBS`) | DEV tooling authoring the list | PRODUCT is the actual receiver | The catalog is computed and read at DEV-time (`/adopt` runs in this checkout) but its *output* — what row appears in `_CATEGORY_GLOBS` — determines what the PRODUCT receives; ADR-0012(c)'s operative rule is precisely about this list |

## Coupling Map (CER-06)

Every path from `tools/adoption_apply/**` / `tools/adoption_scan/**` into `tools.task_control`,
`GOLDEN_APPROVE_HUMAN`, or `contracts/harness/task-control/gate-registry.json`, classified.

| Site | What it is | Classification |
|------|------------|-----------------|
| `approval.py:37` — `from tools.task_control.manager import show` | The **only** live cross-package import from adoption into task-control | **Delete** (whole file, D-01) |
| `approval.py:45` — `HUMAN_TOKEN_ENV = "GOLDEN_APPROVE_HUMAN"` | The env-token constant | **Delete** (whole file) |
| `approval.py:68` — `"""Delegate to tools.task_control.manager.show..."""` | Docstring naming `show` | **Delete** (whole file) |
| `cli.py:41-47` — `from tools.adoption_apply.approval import (AdoptionApprovalRefused, check_valid)` and `promote as approval_promote` | Two import statements | **Delete** |
| `cli.py:151-157` — `if not check_valid(...): ... return 4` inside `_cmd_apply` | The refusal that gates `apply` on a valid promotion | **Delete** (the whole `if` block; `apply` proceeds straight to reading `manifest.json`) |
| `cli.py:222-241` — `_cmd_promote` function body | Calls `approval_promote`, catches `AdoptionApprovalRefused`, prints, returns 3 | **Delete** (whole function) |
| `cli.py:266-273` — `promote_parser` argparse registration (`subparsers.add_parser("promote", ...)` through `promote_parser.set_defaults(func=_cmd_promote)`) | CLI wiring for the `promote` subcommand | **Delete** |
| `cli.py:1-27` module docstring — "``promote`` mirrors `tools.golden_runner.approve.py::main`'s EXACT refuse-by-default exit-code idiom..." | Prose naming the deleted subcommand | **Edit** (prose-only, D-11) |
| `apply.py:16` module docstring — "Two publish idioms, reused verbatim from `tools.task_control.manager`'s already-audited sequence" | Prose only — the sequence itself is not imported, it is a **copied** implementation | **Edit** (prose-only — the claim "reused verbatim from" is misleading pre-existing prose; consider rewording to "modeled on", not required by D-10 but worth a look) |
| `apply.py:207` — "Mirrors `tools.task_control.manager._atomic_create`'s exact sequence" | Stale docstring, sequence already inlined into `atomic_create()` | **Edit** (prose-only, D-10) |
| `apply.py:241` — "Mirrors `tools.task_control.manager._atomic_replace`'s exact sequence" | Same, for `_atomic_replace()` | **Edit** (prose-only, D-10) |
| `batch.py:4,6,14,59,92` — five docstring/comment mentions of `tools.task_control.manager` | All prose — `batch.py` has **zero** live imports of `task_control` (confirmed: `grep -n "^import\|^from" batch.py` shows only stdlib) | **Edit** (prose-only; not named in CONTEXT.md's canonical-refs list but caught by the D-15 grep `task_control` over `tools/adoption_apply/` — will fail SC-1 if left untouched) |
| `scan.py:48` — `_GATE_REGISTRY_PATH = _REPO_ROOT / "contracts/harness/task-control/gate-registry.json"` | The only live filesystem path into task-control's contract | **Delete** (D-06) |
| `scan.py:108-113` — `_secret_pattern()` reads `_GATE_REGISTRY_PATH`, extracts `registry["secret_patterns"]`, compiles | The live consumer | **Edit** — replace the `json.loads(_GATE_REGISTRY_PATH...)` read with a reference to a new local tuple (D-04) |
| `scan.py:9-14` module docstring, "reuse-at-function-level" list item 2 — "Secret pattern set — read as DATA from `contracts/harness/task-control/gate-registry.json`'s `secret_patterns` array" | Prose describing the old sourcing | **Edit** (prose-only, sweep) |
| `test_scan_exclusions.py:211` — `registry = json.loads(scan._GATE_REGISTRY_PATH.read_text(...))` inside `test_secret_patterns_1_branch_attribution` | **Functional** test dependency on the deleted constant, not prose — will raise `AttributeError` once `_GATE_REGISTRY_PATH` is removed | **Edit** — repoint at the new local tuple (this is a hard break, must be in the plan's task list, not just the prose sweep) |
| `tools/adoption_scan/__init__.py:6` — "registry read as data (`contracts/harness/task-control/gate-registry.json`..." | Module docstring | **Edit** (prose-only, sweep) |
| `tools/adoption_apply/pyproject.toml:4` — `description = "...human-ratification promotion..."` | Project metadata field | **Edit** (prose-only, not code-gated by any test, but stale after D-01; low priority) |
| `harness/commands/adopt.md` | The `/adopt` command's source — frontmatter description, "Sub-verbs" intro, the entire `### promote` subsection (`:46-72`), the "## The human gate" section (`:52-72`) | **Edit** — substantial rewrite, not a one-line prose tweak; then re-emit to `.claude/commands/adopt.md` + `.opencode/command/adopt.md` |
| `harness/skills/brownfield-adoption/SKILL.md` | Frontmatter description ("discover, draft, human review, promote, apply"), body text ("discover→draft→review→promote→apply", "five-stage adoption runbook"), the entire "## Stage 4: promote" section | **Edit** — rewrite to 4 stages (discover/draft/review/apply), renumber the old Stage 5 to Stage 4; then re-emit to both `.claude/skills/` and `.opencode/skill/` twins |
| `contracts/harness/task-control/gate-registry.json` | The 8 `secret_patterns` — verified count | **Not deleted here** (Phase 44); adoption stops reading it |
| `tools/evidence/capture.py` | Also reads `gate-registry.json`'s `secret_patterns` (task-control's own evidence redaction) | **Out of scope** — unrelated consumer, untouched by this phase |
| `tools/contract_hash/hash.py:30-33` `DATA_CONTRACT_PATHS` | Still lists `gate-registry.json` as a ratified data contract | **Not touched** — `gate-registry.json` survives until Phase 44; `contracts/harness/adoption/approval.schema.json` (this phase's deletion, D-02) is picked up by the schema glob (`**/*.schema.json`), **not** `DATA_CONTRACT_PATHS`, so no edit to `DATA_CONTRACT_PATHS` is needed for D-02 |

**Correction to CONTEXT.md's canonical-refs list:** `.claude/skills/adopt/SKILL.md` does not exist
(`find .claude/skills -iname "*adopt*"` returns only `brownfield-adoption/`). Plan against
`harness/skills/brownfield-adoption/SKILL.md` only.

## Blast Radius of Deleting the ADOPT-06 Gate (D-01/D-02)

**`approval.py` itself:** 234 lines, single file, zero external readers beyond `cli.py` (confirmed
— repo-wide grep for `adoption_apply.approval` / `from tools.adoption_apply import approval`
outside `.planning/` returns hits only in `approval.py`, `cli.py`, and the adoption test files
below).

**`cli.py`:** the `promote` subcommand (function + argparse wiring, ~30 lines) and the `check_valid`
refusal inside `_cmd_apply` (~10 lines) are the only two call sites.

**Tests — this is the actual size of the change:**

| File | Lines | What happens |
|------|-------|---------------|
| `tools/adoption_apply/tests/test_approval_invalidation.py` | 435 | **Delete whole file** — every test in it exercises `approval.py`'s `promote`/`check_valid` directly (SC-1 batch-resume/invalidation semantics, WR-06 corrupted-approval handling, WR-04 CAS-defect surfacing) |
| `tools/adoption_apply/tests/test_cli.py` | 659, 10 `def test_` functions | **3 tests deleted outright:** `test_cli_promote_refused_exit_code_3`, `test_cli_promote_refused_exit_code_3_subprocess`, `test_cli_promote_succeeds_with_full_human_signals` (all assert `promote` subcommand behavior that no longer exists). **2 tests deleted outright:** `test_cli_apply_refuses_without_approval`, `test_cli_apply_refuses_on_stale_approval` (both assert the exact refusal D-03 removes). **~5 tests rewritten:** `test_cli_draft_writes_into_batch_root`, `test_cli_apply_end_to_end`, `test_cli_apply_refuses_on_malformed_manifest`, `test_cli_apply_refuses_hostile_destination_cleanly`, `test_cli_apply_refuses_directory_shaped_destination` all call a `_promote(task_dir, batch_id, git_repo, decisions_path, monkeypatch)` helper (defined at `:115-146`) before invoking `apply` — that helper call, and the `_promote` helper function itself, must be removed, and every affected test's `apply` invocation now runs directly after `draft` |
| `tools/adoption_scan/tests/test_scan_exclusions.py` | — | `:211`'s `scan._GATE_REGISTRY_PATH` read must be repointed at the new local tuple (functional break, not prose) — see Coupling Map above |
| `tools/adoption_apply/tests/test_fixtures.py`, `test_atomic_apply.py`, `test_batch_layout.py`, `test_constitution_refusal.py`, `test_manifest_schema_conformance.py` | — | **Not confirmed to touch `approval`/`task_control`/`GOLDEN_APPROVE_HUMAN`** by the D-15 greps — re-run the greps against each file as a verification step, but no direct evidence found during this research that requires editing them |

**CI / contract / fixture surfaces checked and found clean:**

- No CI job references `promote`, `approval.schema.json`, or `GOLDEN_APPROVE_HUMAN` for adoption
  specifically (`ci.yml` greps for `python -m tools.contract_drift`, `ruff_baseline`,
  `lifecycle_eval`, `harness_emit`, `docs_sync` — none touch `adoption_apply`/`adoption_scan`
  directly; adoption is exercised only via `pytest`, which the `core-suite`/`lang-tests` jobs
  already run).
- No `.workflow/` artifact or committed task state depends on a live `approval.json` (adoption
  batches are ephemeral, task-local, not part of any committed fixture).
- `contracts/harness/adoption/approval.schema.json` — grepped repo-wide for readers: only
  `approval.py:40` (`APPROVAL_SCHEMA = REPO_ROOT / "contracts/harness/adoption/approval.schema.json"`)
  and `approval.py:89-97`'s `_validate_against_schema`. Confirmed **genuinely orphaned** once
  `approval.py` is deleted — no other module, test, or doc-generator reads this schema path.

## Secret-Pattern Rebaseline (D-04/D-05)

`contracts/harness/task-control/gate-registry.json`'s `secret_patterns` array, read and counted
directly:

```json
"secret_patterns": [
  "AKIA[0-9A-Z]{16}",
  "(?:api[_-]?key|secret|password|token)\\s*[:=]\\s*(?:...)[^\\s]{20,}",
  "(?:ghp_|gho_|ghu_|ghs_|github_pat_)[A-Za-z0-9_-]+",
  "sk-[A-Za-z0-9_-]{16,}",
  "xox[bp]-[A-Za-z0-9-]+",
  "-----BEGIN [A-Z ]*PRIVATE KEY-----",
  "eyJ[A-Za-z0-9_-]{10,}\\.[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+",
  "Authorization:\\s*Bearer\\s+[^\\s]+"
]
```

**Exactly 8 entries** — confirms D-05 and refutes the requirement prose's "7". Copy this array
byte-identical into a new module-level tuple in `scan.py` (e.g. `SECRET_CONTENT_PATTERNS`),
adjacent to `SECRET_PATH_GLOBS` (`scan.py:52-54`), and change `_secret_pattern()`
(`scan.py:108-113`) to build its compiled regex from that tuple instead of
`json.loads(_GATE_REGISTRY_PATH.read_text(...))["secret_patterns"]`. Keep the
`functools.lru_cache(maxsize=1)` decorator and `re.IGNORECASE` flag exactly as-is (D-04). The proof
of a faithful copy: `tools/adoption_scan/tests/test_scan_exclusions.py`'s existing
`test_secret_patterns_1_*` tests (case-diversity, two-of-three-classes, single-class exclusion) must
pass **unchanged** — except for line 211's direct-registry-read, which is a structural repointing,
not a semantic change to what's being tested.

## Rebaseline Procedure for the Contract Deletion (D-02)

Reusing the exact Phase-41 procedure (`41-04-SUMMARY.md`), re-confirmed against the live tree:

1. `git rm contracts/harness/adoption/approval.schema.json` (Bash `git rm`, **not** `Write`/`Edit`
   — `contract_guard`'s `PreToolUse` hook matches only `Write|Edit`, so this needs no
   `HARNESS_DEV_BYPASS`; Phase 41 confirmed this empirically with a clean commit showing no
   `PreToolUse` denial, and the hook's matcher pattern has not changed since).
2. In the **same commit**: `uv run python -m tools.contract_hash.hash --write` — this rewrites
   `contracts/.hashes/manifest.json` dropping exactly the one `approval` key. **No edit to
   `DATA_CONTRACT_PATHS`** (`tools/contract_hash/hash.py:29-33`) is needed: `approval.schema.json`
   is picked up by the generic `SCHEMA_GLOB = "**/*.schema.json"` over `contracts/`, not by the
   explicit `DATA_CONTRACT_PATHS` tuple (which lists only `transitions.json`,
   `gate-registry.json`, `deny-domains.json` — none of which this phase touches).
3. `uv run python -m tools.contract_drift.drift` before committing — must exit 0.
4. Regenerate the committed-derived plane the schema count feeds: `.memory/derived/contracts-index.md`
   and its syrupy snapshot (`tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr`) —
   Phase 41 discovered this is an **in-scope, direct consequence** of a schema-count change (17→16
   there; here it will drop the adoption-contract count from the current live count by exactly 1).
   Regenerate via `python -m tools.memory_regen.contracts_index` then
   `pytest tools/memory_regen/tests/test_contracts_index.py --snapshot-update`.
5. Confirm `docs/reference/approval.md` (if `docs_sync` generated one for this contract) is also
   pruned — `docs_sync.write()` has prune-then-write semantics (verified in STATE.md's Phase-9
   history), so a re-run of `python -m tools.docs_sync` should remove any orphaned page
   automatically; verify with `git status --porcelain docs/reference/` after the re-run.

No `DATA_CONTRACT_PATHS` edit, no `test_contract_guard.py` edit (that pinned test concerns
`CONSTITUTION_GLOBS`'s four-member list, unrelated to the adoption contract count).

## Install-Set Mechanics (PROD-01)

**Today, `_CATEGORY_GLOBS` (`destinations.py:142-181`) has zero `tools/**` entry** — confirmed by
full read of the 40-line tuple. It ships `contracts/**`, `golden/**`, `docs/**` (several
subdirectories), `.memory/**`, `harness/**` (config + agents/commands/skills/plugins),
`.opencode/**`, `.claude/**`, `opencode.json`, `AGENTS.md`/`CLAUDE.md` (root + nested),
`.github/CODEOWNERS`, `.github/workflows/**`, `pyproject.toml` + `**/pyproject.toml` (stub configs
only, no source), `libs/normalize-spec.md` + `libs/normalize-fixtures/**`, and `.gitignore`. No
pattern matches `tools/`.

**How the glob is consumed:** `destination_catalog()` (`destinations.py:228-274`) iterates
`_CATEGORY_GLOBS` in order, resolves each via `Path.glob(pattern)` against `_REPO_ROOT`, keeps only
real files, applies a symlink-containment check, then three exclusion filters in order:
`_EXCLUDED_PREFIX` (`.workflow/tasks/`, structural), `_INSTANCE_DIR_NAME` (`examples/`, GEN-04),
`_SKIP_SEGMENTS` (union of `scan._VENDOR_SEGMENTS` — includes `__pycache__`, `.venv`, `venv`,
`node_modules`, `vendor`, `third_party`, `site-packages` — and `scan._GENERATED_SEGMENTS` — `dist`,
`build`, `bin`, `obj`, `target`, `out`, `.pytest_cache`, `.ruff_cache`), then a git-tracked filter
(`_tracked_repo_files()`, CR-01) that drops any candidate not in `git ls-files`. Deduplication is
destination-string-keyed, first-glob-match-wins by iteration order — **order of insertion in
`_CATEGORY_GLOBS` does not matter for correctness**, only for which pattern nominally "claims" an
already-produced row (harmless either way since the row shape depends only on the destination
string).

**Landmine already covered by the existing mechanism, not something this phase must add a check
for:** if a future `tools/` package happened to be named `build`, `bin`, `obj`, `target`, `out`, or
`dist`, `_SKIP_SEGMENTS` would silently exclude it from the catalog even under a blanket `tools/**`
glob. Verified: no current `tools/` package collides (`ls tools/` — 28 directories, none matching).
The D-08 fixture-install test (below) would **automatically** catch this class of regression if it
ever occurred, because it asserts actual post-apply existence rather than glob-pattern-string
matching — no additional guard mechanism is needed (would violate the binding constraint anyway).

**One `"tools/**"` row added anywhere in `_CATEGORY_GLOBS`** (position immaterial per the dedup
analysis above; suggest placing it near the existing `pyproject.toml`/`**/pyproject.toml` rows for
readability) is sufficient to make every real, git-tracked file under every `tools/*/` package
(source, tests, fixtures, `pyproject.toml`) a catalog row. `__pycache__` directories are excluded
twice over — by `_SKIP_SEGMENTS` and, independently, because they are gitignored and thus filtered
by the git-tracked check. `.venv` is not present under `tools/` (workspace root only) so it is a
non-issue here regardless.

**Distinct `tools.X` modules actually invoked by emitted commands + CI** (grep-enumerated from
`harness/commands/*.md`, `harness/skills/*/SKILL.md`, and `.github/workflows/ci.yml` — the ground
truth D-08's test must walk):

```
tools.adoption_apply     tools.adoption_scan      tools.agree.write
tools.capability         tools.contract_drift.drift   tools.contract_hash.hash
tools.discipline         tools.docs_sync          tools.evidence.capture
tools.golden_runner.approve   tools.golden_runner.runner   tools.handoff
tools.harness_emit       tools.harness_lint.provenance   tools.lifecycle_eval.runner
tools.memory_regen.contracts_index   tools.memory_regen.inject   tools.memory_regen.pointer_index
tools.memory_regen.repo_map   tools.polyglot_lint.lint   tools.risk_router.intake
tools.ruff_baseline      tools.strangler_guard      tools.task_control
tools.task_packet.validate
```

21 distinct top-level packages. All 21 exist under `tools/` today; `tools/memory_ui` is a real
package but is not directly invoked as `python -m tools.memory_ui` by any command/CI reference
found (it is browsed interactively) — irrelevant to D-08's walk-the-references test, but it still
ships under the blanket `tools/**` glob per D-07 (a data row, not filtered by usage).

**Packages this phase's install-set change will ship that Phase 43/44 later delete** (flagged per
instructions, not acted on): `tools.task_control` and `tools.task_packet` (Phase 43, CER-07);
`tools.golden_runner` (Phase 44, CER-09, relocates to `examples/log-parser/`);
`tools.strangler_guard` (Phase 44, CER-08). Per D-07's own design rationale this is **intentional
and self-correcting** — the glob resolves at install time against the then-current tree, so once
Phase 43/44 delete these directories from the harness checkout, `/adopt` run against a target after
those phases simply stops shipping them, with zero edit to `_CATEGORY_GLOBS` required. No action
needed in Phase 42.

**No existing test breaks from adding the glob:**
- `tools/adoption_scan/tests/test_dispositions.py::test_total` asserts `len(catalog) >=
  _MIN_CATALOG_ROWS` (300) — a floor, not an exact count; growth is safe.
- `tools/adoption_scan/tests/test_dispositions.py::test_no_fictional_placeholder_destinations`
  checks that 10 specific **nonexistent** paths (including `tools/widget_tool/pyproject.toml`) are
  absent from the catalog — none of these paths are real files, so adding `tools/**` (which only
  matches real, git-tracked files) cannot introduce them.
- `tools/adoption_scan/tests/test_snapshots.py::test_artifacts_match_committed_snapshot` renders
  over a hand-picked `_FIXED_CATALOG` tuple, **not** the live `destination_catalog()` — immune to
  catalog growth by construction (this is exactly why `build_manifest(catalog=...)` has an
  injectable parameter, per its own docstring).

## How to Write D-08's Fixture-Install Test

**Model:** `tools/adoption_apply/tests/test_fixtures.py` is the existing full-pipeline
(scan→plan→manifest→apply) integration test, but it drives *checked-in, target-side* fixture trees
(`polyglot-single`, `client-server`, `partial-collision-crlf`) through the pipeline — the wrong
model for this test, because D-08 needs to prove something about the **live harness's own
`destination_catalog()`**, not a synthetic target. `tools/adoption_scan/tests/test_dispositions.py`
is the better structural model: it calls `destinations.destination_catalog()` directly against the
real, live `_REPO_ROOT` with no fixture copy at all (e.g. `test_total`, `test_no_fictional_placeholder_destinations`).

**Recommended shape:**
1. A helper that walks `harness/commands/**/*.md`, `harness/skills/**/*.md`, and
   `.github/workflows/*.yml`, regex-extracting every `python -m tools\.([a-zA-Z0-9_.]+)` reference,
   normalizing each to its top-level package name (`tools.adoption_apply` from
   `tools.adoption_apply` or from a dotted submodule form like `tools.contract_drift.drift`).
2. Run the real pipeline against `tmp_path` as target: `destination_catalog()` +
   `harness_proposed_hashes()` + `build_manifest(inventory={"included": [], "excluded": []},
   target_root=tmp_path, proposed_hashes=...)` (an empty/near-empty inventory is fine — every
   `tools/**` row will resolve to `create` since `tmp_path` starts empty), then `apply_manifest()`
   with `payloads` sourced the same way `cli.py`'s private `_harness_payload()` does (read the
   harness's own checkout bytes at each `destination`) for every `create`-disposition row under
   `tools/`.
3. For each top-level package name discovered in step 1, assert
   `(tmp_path / "tools" / package_name.replace(".", "/")).exists()` (a directory, since these are
   packages, not single files) **after** the apply step.
4. This automatically covers the `_SKIP_SEGMENTS`-collision landmine (see above) and any future
   omission in `_CATEGORY_GLOBS`, without a second dedicated check.

**File location:** `tools/adoption_scan/tests/test_install_completeness.py` is the best fit —
`_CATEGORY_GLOBS`/`destination_catalog()` are `adoption_scan`'s own surface, and the existing
"query the live real harness tree with no fixture" pattern already lives in that package's test
suite (`test_dispositions.py`). The apply step needed for step 2 above means this test also imports
`tools.adoption_apply.apply` — that's fine; `test_fixtures.py` (in `adoption_apply`) already
imports from `adoption_scan`, so a cross-package import in the test tree the other direction is not
a new pattern, just the first instance of it in `adoption_scan`'s own tests. (Claude's Discretion
per CONTEXT.md — this is a recommendation, not a lock.)

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (workspace-shared, `uv run pytest -q`) |
| Config file | root `pyproject.toml` (`[tool.pytest.ini_options]`, not separately re-verified this session — unchanged by this phase) |
| Quick run command | `uv run pytest tools/adoption_apply tools/adoption_scan -q` |
| Full suite command | `uv run pytest -q` (1340 tests collected as of this research session) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CER-06 | No `task_control` import/reference in `tools/adoption_apply/`, `tools/adoption_scan/` | grep (structural) | `grep -rn "task_control" tools/adoption_apply/ tools/adoption_scan/` — must return nothing | N/A (grep, not a test file) |
| CER-06 | No `GOLDEN_APPROVE_HUMAN` reference; `draft → apply` runs unset | integration | `env -u GOLDEN_APPROVE_HUMAN uv run python -m tools.adoption_apply draft ... && uv run python -m tools.adoption_apply apply ...` against a scratch task-dir/target | ✅ existing CLI, no new test file needed — this is a manual/CI-script run, not a pytest case (though `test_cli.py`'s rewritten `test_cli_apply_end_to_end` implicitly proves the unset-env path once `_promote` is removed from it) |
| CER-06 | `scan.py`'s 8 secret patterns match exactly what `gate-registry.json` had | unit | `uv run pytest tools/adoption_scan/tests/test_scan_exclusions.py -x` | ✅ exists, requires the `:211` repoint (see Coupling Map) |
| PROD-01 | Every emitted-command/CI-referenced `tools.X` module lands in an applied target | integration (NEW) | `uv run pytest tools/adoption_scan/tests/test_install_completeness.py -x` | ❌ Wave 0 — this is D-08's required new file |
| CER-06 | `apply.py`/`cli.py` prose no longer names task-control or the approval binding | grep (structural) | `grep -rn "task_control\|approval\|GOLDEN_APPROVE_HUMAN" tools/adoption_apply/*.py` — every remaining hit must be a class/exception name unrelated to the deleted gate (e.g. none expected once the sweep lands) | N/A |

### Sampling Rate
- **Per task commit:** `uv run pytest tools/adoption_apply tools/adoption_scan -q` (fast, scoped)
- **Per wave merge:** `uv run pytest -q` (full suite, 1340 tests as of this research)
- **Phase gate:** full suite green, plus `emit-drift`, `stale-derived`, `contract-drift`
  (rebaselined), ruff ratchet — all before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tools/adoption_scan/tests/test_install_completeness.py` — new file, covers PROD-01/D-08 (the
  fixture-install test; see §How to Write D-08's Fixture-Install Test above for shape)
- [ ] No new fixture directory needed — the recommended test drives `tmp_path` directly against the
  live harness catalog, reusing existing helpers (`destination_catalog`, `harness_proposed_hashes`,
  `build_manifest`, `apply_manifest`) already imported elsewhere in the test tree

*No other gaps — CER-06's test coverage is entirely edit-existing-file work (test_cli.py,
test_scan_exclusions.py), not new-file work.*

## Common Pitfalls

### Pitfall 1: Treating `apply.py`'s docstrings as the coupling
**What goes wrong:** A planner reads the requirement prose ("inline the ~60-LOC atomic
create/replace sequence") literally and schedules a task to port code that is already there.
**Why it happens:** The requirement prose predates the actual state of the tree (verified stale by
ROADMAP itself).
**How to avoid:** The task is "edit two docstring sentences" (`apply.py:207`, `:241`), not "inline a
sequence." Confirmed by direct read: `atomic_create()` and `_atomic_replace()` in `apply.py` are
already complete, self-contained, `tempfile.mkstemp` + `os.link`/`os.replace` + fsync
implementations with zero import of `tools.task_control`.
**Warning signs:** A plan task titled "inline atomic create/replace" that touches more than 2 lines
of `apply.py`.

### Pitfall 2: Underestimating `test_cli.py`'s coupling to `promote`
**What goes wrong:** Deleting `approval.py` and the `cli.py` call sites, then running the suite,
and getting 7+ unexpected failures in `test_cli.py` because most of its apply-path tests call a
`_promote()` helper as a precondition.
**Why it happens:** The helper (`test_cli.py:115-146`) is used by 7 of 10 test functions, not just
the 3 that explicitly test `promote` itself.
**How to avoid:** Read `test_cli.py` in full before writing the plan's test-editing task; budget for
rewriting ~5 tests (removing their `_promote` call and the now-irrelevant `--repo-root`-for-approval
plumbing) in addition to deleting 5 tests outright (3 promote-specific + 2 refusal-specific).
**Warning signs:** A plan task that says "delete approval tests" without a line-by-line accounting
of which of the 10 `test_cli.py` functions survive, which are deleted, and which are edited.

### Pitfall 3: Missing the `_GATE_REGISTRY_PATH` cross-check test
**What goes wrong:** `test_scan_exclusions.py:211`'s `test_secret_patterns_1_branch_attribution`
directly reads `scan._GATE_REGISTRY_PATH` as an independent verification of which regex branch
matched a fixture value. This is easy to miss because it is not "approval" or "task_control" in
name — it is a secret-pattern test, and it will not show up in a grep for `task_control` (it reads
a *sibling* constant, `_GATE_REGISTRY_PATH`, whose name doesn't contain "task_control" or
"GOLDEN_APPROVE_HUMAN" — the two strings D-15's own greps search for).
**Why it happens:** D-15's acceptance greps are scoped to `task_control` and
`GOLDEN_APPROVE_HUMAN` literally; `_GATE_REGISTRY_PATH`'s *value* points into
`contracts/harness/task-control/`, but its *name* does not contain the grepped substring.
**How to avoid:** Explicitly plan the edit to `test_scan_exclusions.py:211` (repoint at the new
local tuple) as its own checklist item, verified by running
`uv run pytest tools/adoption_scan/tests/test_scan_exclusions.py -x` after the inline, not just by
the two D-15 greps.
**Warning signs:** `uv run pytest -q` shows an `AttributeError: module 'tools.adoption_scan.scan'
has no attribute '_GATE_REGISTRY_PATH'` failure after the scan.py edit.

### Pitfall 4: Forgetting the two harness-source prose surfaces need a re-emit
**What goes wrong:** Editing `harness/commands/adopt.md` and
`harness/skills/brownfield-adoption/SKILL.md` at source but forgetting `python -m
tools.harness_emit` afterward — `emit-drift` then reds because the emitted twins
(`.claude/commands/adopt.md`, `.opencode/command/adopt.md`,
`.claude/skills/brownfield-adoption/SKILL.md`, `.opencode/skill/brownfield-adoption/SKILL.md`)
still carry the deleted `promote` sub-verb prose.
**Why it happens:** These two files require substantial rewrites (a whole subsection each), not a
one-line prose tweak — easy to treat as "docs" and skip the re-emit step that code changes
routinely remember.
**How to avoid:** Same ordering rule as every other v2.5 phase (ROADMAP ordering rule 6): every
`harness/` change re-emits in the same commit.
**Warning signs:** `emit-drift` (`python -m tools.harness_emit && git status --porcelain`)
non-empty after committing the `harness/commands/adopt.md` / `SKILL.md` edits.

## Code Examples

### Inlining the secret patterns (D-04/D-05 target shape)
```python
# tools/adoption_scan/scan.py — adjacent to SECRET_PATH_GLOBS (existing precedent at :52-54)

# This plan's OWN secret-path glob constant (T-26-02 threat model) — deliberately NOT imported
# from tools.hooks.secret_scan.SECRET_PATH_GLOBS, which is hook-specific.
SECRET_PATH_GLOBS = ["*.env", "**/*.env", "*.pem", "*.key", "id_rsa*", ".npmrc", ".netrc"]

# Byte-identical copy of gate-registry.json's secret_patterns (CER-06) — owned locally for the
# same reason SECRET_PATH_GLOBS already is; adoption_scan is not a task-control consumer.
SECRET_CONTENT_PATTERNS: tuple[str, ...] = (
    "AKIA[0-9A-Z]{16}",
    "(?:api[_-]?key|secret|password|token)\\s*[:=]\\s*(?:(?=[^\\s]*(?-i:[A-Z]))(?=[^\\s]*(?-i:[a-z]))|(?=[^\\s]*(?-i:[A-Z]))(?=[^\\s]*[0-9])|(?=[^\\s]*(?-i:[a-z]))(?=[^\\s]*[0-9]))[^\\s]{20,}",
    "(?:ghp_|gho_|ghu_|ghs_|github_pat_)[A-Za-z0-9_-]+",
    "sk-[A-Za-z0-9_-]{16,}",
    "xox[bp]-[A-Za-z0-9-]+",
    "-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "eyJ[A-Za-z0-9_-]{10,}\\.[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+",
    "Authorization:\\s*Bearer\\s+[^\\s]+",
)

@functools.lru_cache(maxsize=1)
def _secret_pattern() -> re.Pattern[str]:
    """Compile the locally-owned SECRET_CONTENT_PATTERNS tuple (never retyped, never re-read from
    a task-control contract — CER-06 inlines this from gate-registry.json's former source)."""
    return re.compile("(?:" + "|".join(SECRET_CONTENT_PATTERNS) + ")", re.IGNORECASE)
```
Source: byte-for-byte transcription of `contracts/harness/task-control/gate-registry.json`'s
`secret_patterns` array (read directly this session) into the shape `SECRET_PATH_GLOBS` already
uses (`scan.py:52-54`, read directly this session).

### `_CATEGORY_GLOBS` addition (PROD-01 target shape)
```python
# tools/adoption_scan/destinations.py — one new row in the existing tuple
_CATEGORY_GLOBS: tuple[str, ...] = (
    # ... existing rows unchanged ...
    "pyproject.toml",
    "**/pyproject.toml",
    "tools/**",  # PROD-01: ship the Python the installed commands/CI actually invoke
    "libs/normalize-spec.md",
    "libs/normalize-fixtures/**/*",
    ".gitignore",
)
```
Source: `destinations.py:142-181` read directly this session; exact insertion point is immaterial
per the dedup analysis in §Install-Set Mechanics.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `test_cli.py`'s 5 "rewritten" tests need only the `_promote()` call removed, with no other semantic change to their assertions | §Blast Radius | Low — each test's actual apply-behavior assertions are independent of the promotion step; worst case a slightly larger diff than estimated, not a wrong approach |
| A2 | `tools/adoption_apply/tests/test_fixtures.py`, `test_atomic_apply.py`, `test_batch_layout.py`, `test_constitution_refusal.py`, `test_manifest_schema_conformance.py` need no edits | §Blast Radius | Low-Medium — verified no `approval`/`task_control`/`GOLDEN_APPROVE_HUMAN` string appears in these files via the same greps run against the whole `tools/adoption_apply/` tree, but each file was not individually re-read line-by-line in this session; the planner should re-run the D-15 greps per-file as its own verification step before closing the phase, not just trust this table |
| A3 | The recommended location `tools/adoption_scan/tests/test_install_completeness.py` for D-08's new test is the best fit | §How to Write D-08's Fixture-Install Test | None — explicitly Claude's Discretion per CONTEXT.md; any reasonable location the plan chooses is compliant |

**Risk note:** every row above is LOW or LOW-MEDIUM risk and none touches a compliance/retention/
security-standard judgment call — this phase has no such surface.

## Open Questions

1. **Does any currently-green test assert an exact count of `tools/adoption_apply/tests/test_cli.py`'s
   test functions (e.g. a "10 tests" sanity check elsewhere in the suite)?**
   - What we know: `test_cli.py` itself has no such self-count assertion (read in full).
   - What's unclear: whether any *other* file (e.g. a suite-wide test-count guard) pins a global
     test count that would need updating after 5 tests are deleted from this file.
   - Recommendation: no such guard was found anywhere in this session's research (unlike, e.g., the
     `EXPECTED_SKILLS`/`EXPECTED_PERSONAS`/`EXPECTED_COMMANDS` counters in `caps.py`, which count
     *harness surface* artifacts, not test functions) — treat as unlikely but have the executor spot-check
     `uv run pytest -q --collect-only | tail -3`'s total test count before and after as a cheap sanity
     signal, matching this research session's own `1340 tests collected` baseline.

2. **Should `apply.py:16`'s "reused verbatim from `tools.task_control.manager`'s already-audited
   sequence" wording also be softened, beyond the two docstrings CONTEXT.md names (`:207`, `:241`)?**
   - What we know: line 16 makes the same "reused verbatim from task-control" claim at the module
     level, one level up from the two function docstrings D-10 explicitly names.
   - What's unclear: whether D-10/D-11's sweep is meant to be read as "these exact two lines" or
     "every place this claim appears."
   - Recommendation: include it — SC-1's grep (`grep -rn "task_control" tools/adoption_apply/
     tools/adoption_scan/`) will catch it regardless of whether the planner intends to, since line 16
     literally contains the string `tools.task_control`, so it must be edited to pass SC-1 even if
     D-10/D-11's letter is read narrowly.

## Environment Availability

Skipped — this phase has no external tool/service dependency beyond the already-bootstrapped `uv`
workspace, `git`, and `pytest`, all confirmed present and working in this research session
(`uv run pytest -q --collect-only` succeeded, 1340 tests collected).

## Security Domain

No `security_enforcement: false` override found in `.planning/config.json` context provided to this
research session; however this phase's substance is the **removal** of a human-token check
(ADOPT-06), not the addition of any input-handling, auth, or crypto surface. No ASVS category
applies in the "add a control" sense — the relevant standard here is ADR-0012's own operative rule
(CI + merge are the authority), already ratified, not a fresh security decision this research needs
to source.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | No | N/A — `GOLDEN_APPROVE_HUMAN` was never an authentication mechanism, it was a human-confirmation token for a promotion action; its removal is a ratified scope decision (ADR-0012), not an auth gap |
| V4 Access Control | No | Unchanged — `refuse_if_constitution`/`refuse_unsafe_destination` (the *structural* write-confinement in `apply.py`) are untouched by this phase and remain the actual access-control boundary |
| V5 Input Validation | Yes (unchanged) | `jsonschema.Draft202012Validator` against `manifest.schema.json`/`inventory.schema.json`/`plan.schema.json` — already in place, not touched by this phase |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|----------------------|
| A destination resolving onto the constitution plane via symlink/case-variant spelling | Tampering | `refuse_unsafe_destination` (`apply.py:109-201`) — untouched by this phase, still the sole choke point for every disposition branch |
| Secret leakage into an adoption artifact | Information Disclosure | `classify_exclusions`'s path-first, no-content-echo exclusion recording (`scan.py:190-266`) — untouched; only the *source* of the content-pattern list moves (D-04), not the redaction mechanism itself |

## Sources

### Primary (HIGH confidence — direct file reads / grep this session)
- `tools/adoption_apply/approval.py` (full read) — the deleted module's exact content
- `tools/adoption_apply/cli.py` (full read) — import sites, `_cmd_apply` refusal, `_cmd_promote`,
  `promote_parser` wiring
- `tools/adoption_apply/apply.py` (full read) — confirms the atomic sequences are already inlined
- `tools/adoption_apply/batch.py` imports (grep) — confirms zero live `task_control` import
- `tools/adoption_scan/scan.py` (full read) — `_GATE_REGISTRY_PATH`, `_secret_pattern()`,
  `SECRET_PATH_GLOBS` precedent
- `tools/adoption_scan/destinations.py` (full read) — `_CATEGORY_GLOBS`, `destination_catalog()`,
  `harness_proposed_hashes()`, `build_manifest()`, disposition rule chain
- `contracts/harness/task-control/gate-registry.json` (full read) — 8 `secret_patterns`, counted
  directly
- `tools/contract_hash/hash.py`, `tools/contract_drift/drift.py` (partial read) — rebaseline
  procedure, `DATA_CONTRACT_PATHS` scope
- `tools/adoption_apply/tests/test_cli.py`, `test_approval_invalidation.py`,
  `tools/adoption_scan/tests/test_dispositions.py`, `test_scan_exclusions.py`, `test_snapshots.py`
  (grep + partial read) — test blast radius
- `harness/commands/adopt.md` (full read), `harness/skills/brownfield-adoption/SKILL.md` (partial
  read) — prose sweep scope
- `.github/workflows/ci.yml` (grep across full file) — module invocation list, fan-in `gate.needs`
- `.planning/phases/41-docs-review-plane-removal/41-04-SUMMARY.md`,
  `41-VERIFICATION.md` — reused contract-deletion/rebaseline procedure
- `docs/adr/0012-ci-and-merge-as-decision-authority.md` (full read) — DEV/PRODUCT boundary,
  operative rule, Phase 42's own enumeration entry
- `.planning/phases/42-adoption-decoupling-install-set-repair/42-CONTEXT.md`,
  `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md` (full reads) — locked decisions, requirement
  text, phase detail section

### Secondary / Tertiary
None used — every claim in this document traces to a direct file read or command run in this
session (Primary), consistent with the phase's own instruction to cite `file:line` and prefer
verification over training-data recall.

## Metadata

**Confidence breakdown:**
- Coupling map (CER-06): HIGH — every import, call site, and prose reference traced by direct read
  and grep, not inference.
- Install-set mechanics (PROD-01): HIGH — glob consumption logic read in full; module-invocation
  list is a direct grep enumeration, not estimated.
- Test blast radius: HIGH for file-level classification (delete/edit/untouched), MEDIUM for the
  exact line-by-line diff of the 5 "rewritten" `test_cli.py` tests (not written out function-by-
  function in this research — left as a planning-time task, not a research gap, since the shape of
  the edit — "remove the `_promote` precondition call" — is unambiguous from the read).
- Pitfalls: HIGH — each pitfall traces to a specific, re-verifiable file:line finding from this
  session, not a generic pattern.

**Research date:** 2026-07-28
**Valid until:** Phase 42 execution (this is a point-in-time coupling map of a fast-moving deletion
milestone; re-verify line numbers if execution is delayed and other v2.5 phases land first — none
of Phases 43-46 are expected to touch `tools/adoption_apply/`/`tools/adoption_scan/` per the
ROADMAP's own DAG, but `destinations.py`'s `_CATEGORY_GLOBS` line numbers could shift if an
unrelated commit touches that file first).
