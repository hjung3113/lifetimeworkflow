# Phase 42: Adoption Decoupling + Install-Set Repair - Context

**Gathered:** 2026-07-28
**Status:** Ready for planning
**Mode:** `--auto` (all gray areas auto-resolved to the recommended option; see `42-DISCUSSION-LOG.md`)

<domain>
## Phase Boundary

Two things, both required by ADR-0012's DEV/PRODUCT boundary:

1. **CER-06 — adoption becomes standalone.** `draft → apply → PR review`, with no
   `tools.task_control` import, no task-revision binding, and no `GOLDEN_APPROVE_HUMAN`; and
   `adoption_scan` stops reading its secret patterns out of a task-control contract.
2. **PROD-01 — the product stops being inert.** `_CATEGORY_GLOBS` ships commands that shell
   `uv run python -m tools.X`, ships `.github/workflows/**` running the same modules, ships
   `pyproject.toml` stubs — and ships none of the Python. Add the surviving `tools/**`.

**Not in this phase:** deleting `tools/task_control`, `gate-registry.json`, or `secret_scan`
(Phases 43/44 own those). This phase severs adoption's *dependence* on them; the packages themselves
survive until their own phase.

</domain>

<decisions>
## Implementation Decisions

### The approval gate — how deep the removal goes

- **D-01:** **Delete the ADOPT-06 approval gate whole.** `tools/adoption_apply/approval.py` is not a
  module that merely *imports* task-control — it IS the human-ratification gate, binding
  `(draft_hash, task_revision, git_ref)` (`approval.py:11-16`) behind `HUMAN_TOKEN_ENV =
  "GOLDEN_APPROVE_HUMAN"` (`:45`). CER-06 removes both the task-revision element and the env token;
  what remains would gate on nothing. Delete: `approval.py`, the `promote` subcommand
  (`cli.py:222-243`, `:266`), the `check_valid` refusal that gates `apply` (`cli.py:146-155`), the
  `approval` imports (`cli.py:41-46`), and the approval-gate tests.
- **D-02:** **The orphaned contract goes with it.** `contracts/harness/adoption/approval.schema.json`
  has no other reader once `approval.py` is gone. Delete it and **rebaseline
  `contracts/.hashes/manifest.json` in the same commit** — the Phase-41 procedure, already proven.
  The other three adoption contracts (`inventory`, `plan`, `manifest`) stay: they describe artifacts
  `draft` still produces.
- **D-03:** **`apply` no longer refuses on a missing promotion.** After D-01 the sequence is
  `draft → apply`; the review is the PR. This is the ROADMAP's recorded accepted consequence, not a
  regression — do not invent a replacement local gate to "soften" it (the milestone's binding
  constraint forbids it).

### Secret patterns — where they live after inlining

- **D-04:** **A module-level tuple in `tools/adoption_scan/scan.py`, adjacent to `SECRET_PATH_GLOBS`
  (`:52-54`)** — that constant is already owned locally for exactly this reason, so follow the
  precedent rather than inventing a second idiom. Keep the `functools.lru_cache`-compiled combined
  regex and the `re.IGNORECASE` flag as-is (`scan.py:108-113`).
- **D-05:** **There are 8 patterns, not 7** (the requirement prose says 7; the live
  `gate-registry.json` has 8 — verified 2026-07-28). Copy all 8 **byte-identical**. The proof that the
  inline is faithful is that the existing secret-redaction tests pass **unchanged** — do not edit a
  redaction test to accommodate the move. If one fails, the copy is wrong, not the test.
- **D-06:** `gate-registry.json` itself is NOT deleted here (Phase 44 / CER-08 owns it). Only
  `scan.py:48`'s `_GATE_REGISTRY_PATH` read goes away.

### Install-set repair

- **D-07:** **Use a blanket `tools/**` glob, not an enumerated package list.** PROD-01's own framing
  is "a data row, not a mechanism". A glob is also *robust to phases 43/44*: it resolves at install
  time against the then-current tree, so the packages those phases delete simply stop shipping — an
  explicit list would have to be re-edited twice more this milestone.
- **D-08:** **Prove it with a fixture-install test, not by inspection.** SC-4's mechanically-checkable
  form: for every `uv run python -m tools.X` referenced by an emitted command or by
  `.github/workflows/**`, assert module `X` exists in the installed target tree. A test that walks the
  references is the deliverable; a manual check is not.
- **D-09:** Shipping the packages' `tests/` directories along with them is **accepted** — filtering
  them would be a mechanism, and D-07 says data row. If the bloat proves objectionable it is a
  follow-up, not this phase.

### Residue and prose

- **D-10:** **The `apply.py` docstrings must stop pointing at task-control.** `:207` and `:241` say
  "Mirrors `tools.task_control.manager._atomic_create`/`_atomic_replace`'s exact sequence" — the
  sequence is **already inlined** (verified 2026-07-28; the requirement prose predates that), so only
  the prose is stale. Rewrite it to describe the sequence on its own terms. SC-1's grep must return
  nothing, and nothing may point at a module Phase 43 deletes.
- **D-11:** Same sweep applies to `tools/adoption_apply/cli.py:6`'s module docstring and any test
  docstring naming the approval/task-revision binding.

### Ordering and commit discipline (carried from Phase 41 — measured, not stylistic)

- **D-12:** Per task: **delete → `git add` → `git commit -- <pathspec>` → verify → amend-if-red.**
  `tools/adoption_scan/destinations.py:217` reads `git ls-files`, so tracked deletions red until
  staged AND committed. A red before the commit is expected.
- **D-13:** `git commit -- <pathspec>` every time, `git diff --cached --name-only` inspected first.
  Never `git add -A` / `git add .` / `git commit -a`. **Never `git checkout <ref> -- .`** — a Phase-41
  executor did and silently reverted unrelated files.
- **D-14:** Run things rather than reading them. Every Phase-41 wave found consumers its plan had not
  listed, and every one surfaced from a test run or an emitter run, never from a diff.

### Verification / done-condition

- **D-15:** Done = `uv run pytest -q` green; `grep -rn "task_control" tools/adoption_apply/
  tools/adoption_scan/` and `grep -rn "GOLDEN_APPROVE_HUMAN" tools/adoption_apply/ tools/adoption_scan/`
  both return nothing; a `draft → apply` run completes with `GOLDEN_APPROVE_HUMAN` unset; the
  fixture-install test passes; `emit-drift`, `stale-derived`, `contract-drift` (rebaselined) and the
  ruff ratchet clean.
- **D-16:** **No mutation-proof table is owed** — this phase *removes* a gate and adds no control.
  (Distinct from Phase 41 only in that D-08's fixture-install test is genuinely new coverage; it
  asserts a product property, it is not a gate on contributors.)
- **D-17:** Report changed LOC from `git diff --stat`, not estimated.

### Claude's Discretion

- Plan/task decomposition and wave count.
- Whether the contract deletion (D-02) rides with the `approval.py` deletion or gets its own commit.
- The fixture-install test's exact location and fixture shape.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and authority
- `.planning/ROADMAP.md` §"#### Phase 42: Adoption Decoupling + Install-Set Repair" — scope,
  non-goals, accepted consequence, 6 success criteria. Note its scope list records three places where
  the requirement prose diverges from the live tree.
- `.planning/REQUIREMENTS.md` — **CER-06** and **PROD-01**.
- `docs/adr/0012-ci-and-merge-as-decision-authority.md` — accepted; the DEV/PRODUCT boundary and its
  operative rule ("no product capability may be declined because GSD covers it"). PROD-01 is where
  that rule first bites.
- `.planning/research/v2.5-scoping-FINAL.md` — the scoping panel behind the milestone.

### Prior-phase carry-forward
- `.planning/phases/41-docs-review-plane-removal/41-VERIFICATION.md` — the 6/7 verdict, the SC-3
  substance-vs-literal adjudication, and the carried `deny-domains` staleness.
- `.planning/phases/41-docs-review-plane-removal/41-0{1..5}-SUMMARY.md` — the contract-deletion +
  manifest-rebaseline procedure (41-04) this phase reuses, and the ordering rule in D-12.
- `.planning/phases/40-self-gate-teardown/40-01-SUMMARY.md` — the original measured ordering rule.

### The surface this phase touches
- `tools/adoption_apply/approval.py` — the whole ADOPT-06 gate; `:37` the task-control import, `:45`
  the human token, `:69` the `show(task_dir)["revision"]` binding, `:11-16` the triple.
- `tools/adoption_apply/cli.py` — `:41-46` imports, `:146-155` the apply refusal, `:222-243` + `:266`
  the `promote` subcommand.
- `tools/adoption_apply/apply.py` — `:207`, `:241` the stale docstrings (sequence already inlined).
- `tools/adoption_scan/scan.py` — `:48` `_GATE_REGISTRY_PATH`, `:52-54` `SECRET_PATH_GLOBS`,
  `:108-113` the compiled pattern and its live consumer.
- `contracts/harness/task-control/gate-registry.json` — the 8 `secret_patterns` (NOT deleted here).
- `contracts/harness/adoption/approval.schema.json` + `contracts/.hashes/manifest.json`.
- `tools/adoption_scan/destinations.py:142-181` — `_CATEGORY_GLOBS`.

### Conventions
- `AGENTS.md` (root) — nearest-wins agent rules.
- `.claude/skills/brownfield-adoption/SKILL.md` and `.claude/skills/adopt/SKILL.md` — the adoption
  lifecycle as currently documented; both describe the promotion gate D-01 removes and will need a
  bounded prose edit at source (`harness/skills/**`), then a re-emit.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable assets
- **Phase 41's contract-deletion procedure** (`41-04-SUMMARY.md`): `git rm` the schema + rebaseline
  `contracts/.hashes/manifest.json` in the same commit; `contract_guard`'s PreToolUse hook matches
  only `Write|Edit`, never `Bash`, so `git rm` needs no `HARNESS_DEV_BYPASS`.
- **`SECRET_PATH_GLOBS` (`scan.py:52-54`)** is the precedent for D-04 — locally-owned scan constants
  already exist; the inline follows a pattern rather than establishing one.
- **The emitter** (`python -m tools.harness_emit`) propagates any `harness/skills/**` prose edit into
  both runtime trees; never hand-edit `.opencode/**` or `.claude/**`.

### Established patterns
- Deleting a contract moves the hash manifest → `contract-drift` reds until rebaselined.
- `adoption_scan` reads **git**, not the filesystem (`destinations.py:217`) — hence D-12's ordering.
- Adoption contracts are validated with `jsonschema.Draft202012Validator` in-module.

### Integration points
1. `cli.py` → `approval.py` → `tools.task_control.manager.show` (the coupling being severed).
2. `scan.py` → `contracts/harness/task-control/gate-registry.json` (the data read being inlined).
3. `destinations.py::_CATEGORY_GLOBS` → the installed target tree (PROD-01's fix).
4. `harness/skills/{adopt,brownfield-adoption}` → emitter → both runtime trees (prose).

</code_context>

<specifics>
## Specific Ideas

- The requirement prose is stale in three verified places — 7 vs **8** secret patterns, the atomic
  sequence **already inlined**, and the coupling living in `approval.py` rather than `apply.py`. Plan
  against the tree, not the prose, and re-verify each before writing an acceptance criterion.
- D-08's fixture-install test is the phase's most valuable artifact: it is the first thing that would
  catch the product shipping inert again.

</specifics>

<deferred>
## Deferred Ideas

- **Delete `gate-registry.json`, `secret_scan`, `deny-domains.*`** → Phase 44 (CER-08). Includes the
  stale `deny-domains.json` `ledger_guard` declaration carried out of Phase 41.
- **Delete `tools/task_control` and the lifecycle plane** → Phase 43 (CER-07).
- **Filtering `tests/` out of the shipped install set** → follow-up if D-09's accepted bloat proves
  objectionable; not this phase.

</deferred>

---

*Phase: 42-adoption-decoupling-install-set-repair*
*Context gathered: 2026-07-28*
