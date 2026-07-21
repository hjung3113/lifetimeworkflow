# TERRA implementation plan — constitution-plane enforcement drift

## 1. Exact file list and ownership

The repository is currently clean on `claude/data-pipeline-harness-8aypct`; `docs/.docs-review-ledger.toml` is absent both from the worktree and from Git history.  The list below is therefore the complete execution surface identified from the current checkout.  Generated runtime files are outputs, not hand-edit targets.

### A. Align enforcement, configuration, and explanatory surfaces with ADR-0001

| File | Current lines / key | Change | Authority |
|---|---:|---|---|
| `tools/hooks/contract_guard.py` | 1-5, 40-43, 78-80 | Add the exact file glob `docs/glossary.md` to `CONSTITUTION_GLOBS`; update the module/constant prose and deny reason so all four plane members are named. | Agent-writable code, but this enforces a constitution-plane rule. |
| `tools/hooks/tests/test_contract_guard.py` | 1-16, 46-69, 75-98, 163-198, 227-258 | Add glossary rows to the direct, absolute-path, `main()`, approved-byte-hygiene, and dev-bypass cases; update the three-glob prose. | Agent-writable test. |
| `harness/permission-matrix.json` | 2, 27-34 (`path_deny_globs`) | Insert `docs/glossary.md` in the constitution subset, retaining secret and ledger domains as separate entries. | Agent-writable source configuration. |
| `tools/harness_perms/tests/test_resolver.py` | 56-72 | Add a direct matrix-resolver denial assertion for `docs/glossary.md`. | Agent-writable test. |
| `tools/harness_perms/tests/test_order_resolution.py` | 6-10, 105-128 | Add `docs/glossary.md` to the parameterized constitution/secret proof and correct its prose. | Agent-writable test. |
| `tools/harness_lint/tests/test_agents.py` | 41-45, 189-199 | Add `docs/glossary.md` to `_CONSTITUTION_DENY_GLOBS` and its explanatory assertion text. | Agent-writable test. |
| `tools/docs_guard/tests/test_exclusions.py` | constitution-row table near 47-119; deletion proof 168-180 | Add a glossary constitution row so `exclusion_reason()` returns `constitution-plane`, and prove that deleting the imported home glob makes that exact row draftable. | Agent-writable test. |
| `.github/CODEOWNERS` | 1-5, 24-28 | Add the root-anchored `/docs/glossary.md    @hjung3113` entry and change the comments from three paths to the four-member plane. | **Constitution-plane governance surface / human owner required.** |
| `AGENTS.md` | 22-25, 74-75 | Make the monorepo map and non-negotiable #3 explicitly say that `docs/glossary.md` is agent-denied alongside the other three members. | Agent-writable instruction surface; do not alter the generated block at 99-107. |
| `harness/skills/gate-model/SKILL.md` | 4-6, 16-27 | Change the trigger prose, “three top-level trees,” list, and `path_deny_globs` explanation to the four-member plane. | Agent-writable authored source. |
| `.claude/skills/gate-model/SKILL.md` | 14-25 | **Generated output:** refresh only via `uv run python -m tools.harness_emit`; never hand-edit. | Generated runtime surface. |
| `.opencode/skill/gate-model/SKILL.md` | 14-25 | **Generated output:** refresh only via the same emitter; never hand-edit. | Generated runtime surface. |
| `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` | 3291-3315 | Accept/update the deterministic emitter snapshot to match the regenerated skill text (including its rendered frontmatter description if it is changed). | Agent-writable test fixture, generated-test oracle; update through the repository’s snapshot workflow, not ad hoc prose editing. |
| `.memory/README.md` | 29-31 only | Replace the obsolete “NOT built in this phase” wording with a statement that the live Phase-4 `contract_guard` enforces the declared plane. Keep the correct four-member table and list at 13 and 20-25 unchanged. | Agent-writable hand-authored memory declaration; **not derived**. |

`tools/docs_guard/guard.py:100-108` already includes `docs/glossary.md` in `HUMAN_CORPUS`; do not change it. `tools/docs_guard/exclusions.py:46, 94-100` imports the exact `CONSTITUTION_GLOBS` object, so it will automatically exclude the glossary from drafting after A. This does **not** change the corpus denominator, uncovered count, `uncovered_max`, or `binding_min`: corpus membership and drafting exclusion are distinct, and the existing `normalize-spec-glossary` binding at `docs/doc-dependencies.toml:88-93` already covers the glossary.

### B. Correct the template/instance explanation

| File | Current lines / key | Change | Authority |
|---|---:|---|---|
| `docs/explanation/template-and-instances.md` | 64-69 | Keep “one sanctioned exception,” but define it correctly as one `harness/project.toml` instance config slot containing `root`, `persona`, and `test_paths` pointer-line classes. | Agent-writable documentation. |
| `tools/harness_lint/tests/test_core_no_example_dep.py` | 73-85, 109-113 | No behavioral change expected. Use these as the source of truth; add/update a narrow assertion only if the present tests do not explicitly pin all three accepted keys. Do not broaden `_INSTANCE_POINTER_LINE`. | Agent-writable test, conditional only after checking current coverage. |

### C. Repoint the advisory shadow-metrics binding

| File | Current lines / key | Change | Authority |
|---|---:|---|---|
| `docs/doc-dependencies.toml` | 95-100 (`lifecycle-eval-shadow-metrics`) | Add `tools/risk_router/router.py` to `sources`; retain the ID, target, advisory severity, and disposition list. | Agent-writable registry; not constitution-plane. |
| `tools/docs_guard/tests/test_guard.py` | 692-780 | No new guard behavior is needed: this existing adversarial REPOINT test is the execution proof. Run it directly. Do not weaken it or create a ledger. | Agent-writable test; unchanged unless a real coverage gap is demonstrated. |

`docs/adr/0001-walking-skeleton-golden-core.md:48` is accepted authority and must not be edited. `docs/adr/0002-...:77-81` confirms the config slot is `[instance] root` plus `[[languages]]`, not a reason to change the guard. `docs/adr/0010-human-docs-review-obligation-model.md` remains `proposed`; do not edit it during this repair.

## 2. Ordering and digest rationale

1. **Write the RED tests first (A and B) and run them before touching production/config/docs.** The missing glossary rows must fail because pre-fix `CONSTITUTION_GLOBS` (line 43) and `path_deny_globs` (lines 27-34) omit it. The existing documentation mismatch in B is prose-only, so its verification is a targeted textual/semantic assertion rather than an invented runtime control.
2. **Land A’s enforcement/config source changes, then regenerate runtime projections.** Update `contract_guard`, its tests, matrix, matrix/lint tests, CODEOWNERS, root instructions, source skill, `.memory/README.md`, and snapshot expectation. Run `uv run python -m tools.harness_emit`, inspect `git status --porcelain`, and retain only the expected `.claude/skills/gate-model/SKILL.md`, `.opencode/skill/gate-model/SKILL.md`, and any manifest/snapshot changes that the emitter/test workflow genuinely produces. The four A documentation targets change their content digests for the already-declared bindings `memory-plane-declaration` and `gate-model-permission-surface`; no ledger exists, so no stale ledger row is created.
3. **Land B after A.** This changes the target digest of the required `gen04-core-instance-split` binding (`docs/doc-dependencies.toml:46-54`). No source selector changes and no constitution artifact changes.
4. **Land C after B.** Adding `tools/risk_router/router.py` changes the source digest **and** `identity_digest(sources, target)` for `lifecycle-eval-shadow-metrics`; `tools/docs_guard/registry.py:78-98` sorts sources for identity, but adding a new selector is still a new meaning. The target digest does not move unless the target document is separately changed (it is out of scope).
5. **Only after A→B→C are committed and reviewed, a human ratifies ADR-0010 through the append-only constitution path; only after that human authors the first `docs/.docs-review-ledger.toml`.** A ledger authored earlier immediately records stale target/source digests as A/B/C move their files, and treating it as ratification while ADR-0010 is proposed reverses the authority order.

With no current ledger, C is advisory and `uv run python -m tools.docs_guard` should remain non-blocking (exit 0, at most advisory/staleness output). Once a ledger has been committed, a C repoint is deliberately amber for one commit cycle: `guard.py:335-347` marks the ID repointed and `ledger.py:398-420` reports `first_seen-unratified` even if someone supplies matching digests. The human review commit that first lands the new-shape row is the ratification; a subsequent cycle can be green. Never create a ledger merely to make this plan green.

## 3. Gate impact per step

| Step | `uv run pytest -q` | `uv run python -m tools.contract_drift.drift` | `uv run python -m tools.harness_emit` + `git status --porcelain` | `uv run pytest tools/harness_lint -q` | `uv run python -m tools.docs_guard` |
|---|---|---|---|---|---|
| Baseline / RED-test commit | Full suite otherwise green; the newly added glossary control tests intentionally fail pre-fix. | Green: no `contracts/**/*.schema.json` change. | Not run before source changes (it writes generated files). | Existing suite green; new matrix assertion intentionally fails pre-fix. | Exit 0 with no ledger; it does not police the omitted runtime glob. |
| A after implementation | Green, including `tools/hooks/tests/test_contract_guard.py`, `tools/harness_perms/tests`, `tools/docs_guard/tests/test_exclusions.py`, and emitter tests. | Green. | Emitter exits 0; status must show only intentional generated gate-model copies (and any owned manifest change), never an edited ledger. A second emitter run must leave no further diff. | Green; its changed global-glob assertion proves the matrix contains the glossary. | Exit 0. The glossary remains in `HUMAN_CORPUS`; it is excluded only from agent drafting. Existing required bindings with no ledger must be checked against the actual CLI behavior before claiming an exit code. |
| B after implementation | Green. | Green. | No expected emitter output unless an authored harness input also changed. | Green; run `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -q` specifically. | Exit 0/no ledger; the required binding’s target digest has changed but no reviewed row exists. |
| C after implementation | Green; run `uv run pytest tools/docs_guard/tests/test_guard.py -q` and specifically `-k repointing_a_ratified_binding_is_not_fresh`. | Green. | No expected emitter output. | Green (registry remains core-neutral). | Current no-ledger checkout: advisory/non-blocking. **After a committed ledger exists:** legitimately red/amber for the repointed binding with `first_seen-unratified` until the human ratification commit; do not mask it by changing `uncovered_max` or `binding_min`. |

Run the named commands from repository root. Also run `git diff --check` before handoff and inspect `git diff --name-only` to enforce the exact file list.

## 4. Adversarial inputs authored before the fix

| Behavioral change | Test to write/extend first | Input rows | Required pre-fix RED and reason |
|---|---|---|---|
| Contract guard denies the exact glossary file | `tools/hooks/tests/test_contract_guard.py`: add direct and absolute-path cases plus a `main()` case | `docs/glossary.md`, absolute `${REPO_ROOT}/docs/glossary.md`, unapproved clean content | `decide(...)` returns `None` / `main()` emits no deny, because line 43 has only three globs. A generic `docs/*.md` row is forbidden: it could pass without proving the literal authoritative file. |
| Approval never weakens glossary byte hygiene | Same module: add approved BOM and CRLF glossary rows and dev-bypass clean/BOM rows | clean `docs/glossary.md`; BOM content; CRLF content; `HARNESS_DEV_BYPASS=1` | Pre-fix clean and malformed glossary writes are all treated as off-plane (`None`), so the expected denial fails. This proves both access and byte-hygiene paths use the same expanded glob set. |
| Matrix and its downstream callers deny glossary | `tools/harness_perms/tests/test_resolver.py`, `test_order_resolution.py`, and `tools/harness_lint/tests/test_agents.py` | literal `docs/glossary.md` in each matrix test | `resolve_path(...)=allow` and missing-set assertion identifies `docs/glossary.md`, because the data row is absent. |
| Drafting exclusion consumes the shared glob object | `tools/docs_guard/tests/test_exclusions.py` | literal target `docs/glossary.md`; then monkeypatch `exclusions.CONSTITUTION_GLOBS=[]` | Before A it returns `None`, not `constitution-plane`; after A, the deletion proof must make it return `None`. This prevents a local retyped list or a special-case from passing. |
| Instance-slot prose names all actual exemptions | Add a focused assertion in `tools/harness_lint/tests/test_core_no_example_dep.py` only if missing | `root =`, `persona =`, `test_paths =` accepted; a near miss such as `roots =` rejected | It must be RED only if the test first demonstrates a real coverage gap. The production regex already supports all three, so do not add a test that falsely claims pre-fix runtime behavior is broken; the RED artifact here is the inaccurate document text at `template-and-instances.md:67-68`. |
| Repoint cannot inherit ratification | Re-run existing `tools/docs_guard/tests/test_guard.py::test_repointing_a_ratified_binding_is_not_fresh` before C | same ID, original source/target and committed ledger; new source list with the added risk-router source; matching live content digests | The existing test is the adversarial proof: a defective ID-only identity implementation yields `FRESH`/`ok=True`; the current implementation correctly produces `first_seen-unratified`. No new ledger fixture in the real repo. |

## 5. Mutation proofs

| Control | Mutation that must make the named test red |
|---|---|
| `contract_guard.CONSTITUTION_GLOBS` glossary member | Delete only `docs/glossary.md`; the new direct, absolute, `main()`, BOM/CRLF, and dev-bypass glossary rows in `test_contract_guard.py` fail. |
| Matrix glossary member | Delete only the matrix entry; `test_resolver.py`, `test_order_resolution.py`, and `test_agents.py::test_constitution_paths_denied_globally` fail. |
| `docs_guard.exclusions` imports rather than copies the guard list | Delete the glossary member at the guard home; the glossary row in `test_exclusions.py` fails. Replace the import with a locally copied list; the existing `is`-identity test at 151-152 fails. |
| Emitter round trip | Revert one generated `gate-model` copy after emission; run `uv run python -m tools.harness_emit` and verify it restores that file, then run the deterministic emitter test/snapshot assertion. |
| Three-key instance exemption | Delete `persona` or `test_paths` from `_INSTANCE_POINTER_LINE`; its corresponding positive fixture must fail. Change it to an overbroad `\w+`; the near-miss negative fixture must fail. |
| Repoint identity check | Mutate the classifier to compare only `binding.id` (or force `repointed_ids` empty); `test_repointing_a_ratified_binding_is_not_fresh` must report `FRESH`/`ok=True` and fail its assertions. |

## 6. Blast radius and rollback

- An overbroad glob (for example `docs/**`) would deny normal agent-authored documentation and alter drafting exclusions. Roll back only the added literal `docs/glossary.md` entries and rerun the literal allow/deny rows; never compensate with a broad `HARNESS_DEV_BYPASS` policy.
- Updating authored skill text without emitting both runtime copies creates runtime drift. Roll back the authored skill change and rerun the emitter, rather than hand-reverting one emitted copy.
- Incorrectly changing `HUMAN_CORPUS` or its ratchets would alter coverage accounting. This plan intentionally does neither; if an executor does, revert that change before touching the human ledger.
- A bad C selector can make the advisory binding watch an unrelated source. Restore the original one-source list; do not delete the metric row, rename the ID, or rewrite history to evade the repoint rule.
- Documentation rollback is ordinary for `docs/explanation/...`, `AGENTS.md`, and `.memory/README.md`; CODEOWNERS/glossary/ADR governance changes require the relevant human review path. No rollback includes changing ADR-0001 or manufacturing a ledger row.

## 7. Must not touch

- `docs/adr/0001-walking-skeleton-golden-core.md`: accepted, unsuperseded authority; do not edit, supersede, or reinterpret it in this repair.
- `docs/.docs-review-ledger.toml`: do not create, edit, stage, or use as a test artifact in the repository. It is absent today and is human-authored-only.
- `docs/adr/0010-human-docs-review-obligation-model.md`: do not treat its proposed status as ratified and do not edit it as part of A/B/C.
- `tools/docs_guard/guard.py:100-108` (`HUMAN_CORPUS`) and any live `uncovered_max`/`binding_min`: they are not the defect and must not be used to force green.
- `tools/docs_guard/ledger.py`, `tools/docs_guard/registry.py`, `tools/risk_router/router.py`, and `tools/lifecycle_eval/runner.py`: existing behavior is sufficient; only C’s registry selector changes.
- `.claude/skills/gate-model/SKILL.md`, `.opencode/skill/gate-model/SKILL.md`, and all other harness-emitted paths: no hand edits; use `uv run python -m tools.harness_emit`.
- Constitution content itself (`contracts/`, `golden/`, `docs/glossary.md`) and all derived `.memory/derived/` files.

## 8. Human decisions required before execution

1. **Constitution/governance writes:** authorize the human-owned `.github/CODEOWNERS` change and determine whether the executor may use the documented `GOLDEN_APPROVE_HUMAN` path for any protected write surface. The code/config repair can be prepared without it, but the governance change must not be bypassed.
2. **ADR-0010 ratification:** decide when and by whom the proposed ADR will be accepted. Until that occurs, do not author the first ledger.
3. **First-ledger timing and baseline:** after A/B/C and ADR-0010 are committed, a human must choose the reviewed dispositions and record then-current digests. The new/repointed binding’s one-cycle history rule is intentional; do not demand same-commit green.
4. **B-test scope:** confirm whether the existing `test_core_no_example_dep.py` already has positive coverage for all `root`/`persona`/`test_paths` classes. If it does, make B a documentation-only correction; if it does not, add the narrowly specified test before changing prose.
