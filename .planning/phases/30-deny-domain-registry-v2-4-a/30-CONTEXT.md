# Phase 30: Deny-Domain Registry *(v2.4 A)* — Context

**Gathered:** 2026-07-22
**Status:** Ready for planning
**Mode:** Autonomous smart-discuss — grey areas decided at planning time per the milestone's
"run to close without intermediate stops" instruction (`.planning/research/v2.4-scoping-FINAL.md:5-6`).
Every decision below adopts `30-RESEARCH.md`'s stated finding; none is a novel invention.

<domain>
## Phase Boundary

Declare — once, as a gated contract — every path-deny domain the harness enforces, with the field
that makes the uncovered bash surface visible as **data**, and gate the declaration against the live
constants so it cannot rot.

Requirement: SEAL-01 (`.planning/REQUIREMENTS.md:18-25`).
Roadmap entry: `.planning/ROADMAP.md:109-113`. DAG: `30 → 31 → 32` hard chain; `33` depends on 30
only (`.planning/ROADMAP.md:139-141`).

**IN scope:** the deny-domain contract (schema + instance), its loader, and a `harness_lint` drift
test that fails when a hook's live constant, its bypass behaviour, or its runtime tool surfaces
disagree with the declaration — each proven by an actual mutation.

**OUT of scope:** any change to what the hooks *enforce*; any bash-surface enforcement (SEAL-02/03,
phases 31–32); making `secret_scan` read its content patterns from a contract (SEAL-04, phase 33);
the posture ADR (phase 31); merging any two domains (forbidden — ADR-0010
`docs/adr/0010-human-docs-review-obligation-model.md:152,163-175`).
</domain>

<decisions>
## Implementation Decisions

| # | Grey area | Decision | Rationale |
|---|-----------|----------|-----------|
| D-01 | Is the registry a contract, and what shape? | **Yes — a schema + instance PAIR** at `contracts/harness/security/deny-domains.schema.json` + `deny-domains.json`, with the instance registered in `tools/contract_hash/hash.py` `DATA_CONTRACT_PATHS`. | `gate-registry.json` is the named precedent but is schema-less; this registry has per-domain records with three enums (bypass token, tool surface, runtime), which is exactly what a schema constrains. A pair also makes CI's `contract-check` job non-vacuous for the first time — today it prints its SKIP line because the repo has zero pairs (`ci.yml:108-127`, `:121-123`). Cost: one derived reference page + contracts-index row + two snapshots, all in the same atomic commit (28-01's shape). |
| D-02 | Does the registry become the source of truth for the globs? | **NO. The hooks stay the SSOT; the registry is the CLAIM.** The hooks import nothing from it. | If a hook read its globs from the registry, the drift test degenerates to `x == x` and detects nothing. Drift detection requires two independently-authored copies. This is the inverse of the repo's usual import-don't-retype rule, and the plan must carry that reasoning into a code comment or a reviewer will "fix" it. |
| D-03 | Where does the loader live? | A new virtual uv member `tools/deny_domains/` (`registry.py`), **not** inside `tools/harness_lint/`. | Phases 31–33 consume the registry. A hook or a threat-model tool importing a *lint* package inverts the dependency direction. One new member, zero external deps, `package = false` — mirrors `tools/harness_perms`. Requires a `uv sync --all-packages` lockfile touch (`uv.lock` lists workspace members). |
| D-04 | Where does the drift test live? | `tools/harness_lint/tests/test_deny_domain_registry.py` — the repo's existing home for structural drift gates. | Team-lead instruction and house precedent (`test_contract_graph_config.py`, `test_ci_emit_drift.py`). |
| D-05 | Do the three domains merge? | **Never.** Three separate records with distinct ids, distinct owner modules, distinct bypass sets. The schema forbids two records sharing an `owner_constant`. | ADR-0010 `:163-175` gives the two reasons: `GOLDEN_APPROVE_HUMAN` authorizes *constitution* writes and must never be taught as reachable for the ledger; and `contract_guard.py:16-20` documents a provably-disjoint-domain invariant that widening would break. `.planning/REQUIREMENTS.md:105` lists merging as out of scope. |
| D-06 | The fourth `SECRET_PATH_GLOBS` (`tools/adoption_scan/scan.py:54`) | Declared in a separate **`non_enforcing_glob_sets`** array with an explicit `reason`, never as a domain. | It is a wider, deliberately module-own **classification** set (`scan.py:14-15,53`). Omitting it leaves a reader to conclude `*.pem` is denied on write — it is not. Listing it as a domain would be a fabricated control. The registry's job is an honest inventory, so it names both what is enforced and what merely looks like it. |
| D-07 | `commit_gate` | **Not modelled**, and the registry says so in a one-line note. | `commit_gate.py:1-24` enumerates no paths: it composes contract-drift + polyglot §4.3–4.6 over staged `*.tsv` + golden parity. Team-lead constraint, confirmed against source. |
| D-08 | The bash gap's representation | Each domain carries `covered_tool_surfaces` **and** `uncovered_tool_surfaces`, both explicit arrays. Every domain's `uncovered_tool_surfaces` includes `"Bash"` today. | SEAL-01's whole point: "the field that makes the bash gap visible as DATA". An absence is not data — a reader cannot tell an omitted surface from an unexamined one. Phase 31 reads this field as its input; phase 32 shrinks it and the drift test proves the shrink. |
| D-09 | `secret_scan`'s content axis | A `content_axis` object per domain: `{ "kind": "regex-patterns", "source": "hardcoded", "location": "tools/hooks/secret_scan.py:44", "carried_debt": "SEAL-04" }`. Constitution's is `{ "kind": "byte-hygiene", "source": "tools.polyglot_lint.lint_bytes" }`; the ledger has none. | A registry that lists only `SECRET_PATH_GLOBS` under-describes its own owner module — `secret_scan` denies on content too (`secret_scan.py:44-48`), and that list is a *fork* of `gate-registry.json:10-19` (3 patterns vs 8). Same argument as D-08: carried debt becomes data. |
| D-10 | How bypass semantics are verified | **By driving the hook**, never by reading its source. The test sets `GOLDEN_APPROVE_HUMAN` / `HARNESS_DEV_BYPASS` via `monkeypatch.setenv` and asserts the decision each hook actually returns. | 28-RESEARCH P4: a static token scan goes green on an unused import. Constitution declares both tokens (`contract_guard.py:114-115`); secret and ledger declare **none** and must be proven to still deny with **both** env vars set. |
| D-11 | How runtime adapters are verified | Claude side against `tools.harness_emit.merge.HARNESS_HOOK_GROUPS` (the emitter source), **not** `.claude/settings.json`. opencode side by **parsing** the adapter's `input.tool !== "…"` chain out of the `.ts` source. | The emitter is the source and `emit-drift` (`ci.yml:218`) already gates its projection — asserting against the projection would double-gate the wrong artifact. There is no opencode runtime in this container (`.opencode/plugin/ledger-guard.ts:4-8`), so the opencode side is necessarily a source parse; it is still falsifiable, and D-12 requires the mutation that proves it. |
| D-12 | Proof standard | Every check ships with a **mutation that makes it RED**, run in-suite via `monkeypatch`, following `test_contract_guard.py:352-381`'s delete-each-member idiom. Seven checks, seven mutations (`30-RESEARCH.md` §"what it can actually falsify"). | "Proven by an actual mutation, not asserted" is the requirement's own wording (`REQUIREMENTS.md:24-25`). |
| D-13 | Matrix reconciliation | The test asserts `harness/permission-matrix.json:path_deny_globs` equals the union of the declared domains' globs in **both directions**. | Today the equality holds (7 entries = 4+2+1) and is asserted **nowhere**. The reverse direction is the one that matters: an unowned matrix row is precisely the ADR-0010 `:154-160` inert-data failure recurring. |
| D-14 | Do the hooks get edited? | **No hook is edited in Phase 30.** Zero production behaviour change. | Keeps the phase's own claim falsifiable (the registry is compared against untouched constants), and `docs/doc-dependencies.toml` binds `tools/hooks/contract_guard.py` → `.memory/README.md` at `severity = "required"` — an editorial comment would fire a real review obligation for no enforcement gain. Verified: nothing this phase touches is a bound source. |
| D-15 | Does Phase 30 need an ADR? | **No.** The registry implements decisions ADR-0001 and ADR-0010 already made; it records no new architecture. Phase 31 owns the milestone's ADR. | An ADR per inventory would dilute the append-only record. If the drift test's *proof standard* proves contentious, phase 31's posture ADR is the place to state it. |
| D-16 | The registry's own docs binding | **Proposed in the final plan** — a `[[binding]]` row binding the registry instance to `harness/skills/gate-model/SKILL.md`, and the resulting `first_seen-unratified` obligation carried as an explicit **blocking-human** ledger disposition with the exact draft row. | A control declaration that no document is obliged to follow is the thing this milestone exists to stop. The obligation is an acknowledged ratification row, not implementation debt (`.planning/research/v2.4-scoping-FINAL.md:50-51`). The alternative — defer the binding to phase 33 — is recorded in Open Questions. |
| D-17 | Constitution-plane commit budget | **One atomic commit**, human-ratified: schema + instance + `hash --write` + `docs_sync` + `contracts_index` + both syrupy snapshots + the `DATA_CONTRACT_PATHS` edit. No `HARNESS_DEV_BYPASS`, no fabricated token. | 28-D-18 / 27.1-03 template. Half-landing reds `drift` (`ci.yml:133`) or `stale-derived` (`ci.yml:227`). |
| D-18 | Module set (anti-sprawl) | **One** new uv member (`tools/deny_domains/`), **one** new test file in `harness_lint`, **one** new contract pair, **one** line added to `hash.py` `DATA_CONTRACT_PATHS`, **one** proposed registry row. Nothing else. | Documented anti-sprawl bias — prefer extending. No new command, no new skill, no new agent, no new CI job (the test rides the existing `pytest` job). |

</decisions>

<code_context>
## Existing Code Insights

Full detail with file:line in `30-RESEARCH.md` (every citation read from source this session).
Load-bearing pointers:

- `tools/hooks/contract_guard.py:53,57,114-115` — the constitution globs and BOTH bypass paths.
- `tools/hooks/secret_scan.py:37,44-48,81-91` — the secret globs, the hardcoded content patterns
  (SEAL-04 debt), and the absence of any bypass branch.
- `tools/hooks/ledger_guard.py:26-30,48,70` — the third domain and its explicit no-token posture.
- `docs/adr/0010-...md:141-152,154-160,163-175` — the three-layer table, "a layer that is only a
  data row is a claimed control that does not exist", and why the ledger must stay separate.
- `harness/permission-matrix.json:27-35` — the 7-entry `path_deny_globs` union, currently unasserted.
- `tools/harness_emit/merge.py:126-158` — the authoritative matcher declarations for all three hooks.
- `.opencode/plugin/{contract-guard,secret-scan,ledger-guard}.ts:70` — the adapter tool guards.
- `tools/contract_hash/hash.py:29-32` + `tests/test_hash.py:93-101` — the data-contract registration
  point, and the verified reason adding a third entry does not break that test.
- `tools/hooks/tests/test_contract_guard.py:352-381` — the mutation idiom D-12 clones.
- `tools/adoption_apply/tests/test_constitution_refusal.py:528-576` — the existing partial
  disjointness/subset assertions this phase generalizes.
- `.github/workflows/ci.yml:108-127,133,218,227,308` — `contract-check`, `drift`, `emit-drift`,
  `stale-derived`, `docs-guard`.

</code_context>

<specifics>
## Specific Ideas

- **The phase's anti-pattern fence** (inherited from 26.1 / 27.1 / 27.2 / 28): the adversarial-input
  table is authored FIRST, and each new assertion is shown failing against the un-mutated tree for
  the stated reason before the registry is declared accurate.
- **The tautology fence (D-02) is the phase's characteristic failure.** A reviewer's instinct here
  is "import the constant instead of restating it" — which is right everywhere else in this repo and
  wrong here. The plan puts that reasoning in the code, not only in the plan.
- **A live drive, not a source read** (D-10) for every behavioural field. The registry's `bypasses`
  arrays are claims about runtime behaviour; only running `decide()`/`main()` tests them.
- Four disagreements between the ratified design and the live code are recorded in
  `30-RESEARCH.md` §Disagreements — stale SEAL-03 line cites, the fourth glob set, `secret_scan`'s
  unmodelled content axis, and the `apply.py:227` lowercasing asymmetry. The first three are
  resolved by D-06/D-09; the fourth is handed to phase 31 rather than fixed here.

</specifics>

<deferred>
## Deferred Ideas

- Bash-surface threat model + posture ADR → Phase 31 (SEAL-02). Consumes D-08's
  `uncovered_tool_surfaces` field as its input.
- Implementing the posture and shrinking `uncovered_tool_surfaces` → Phase 32 (SEAL-03).
- `secret_scan` reading its content patterns from the contract → Phase 33 (SEAL-04); D-09 records
  the debt as data in the meantime.
- The `apply.py:227` vs `ledger_guard.py:70` case-normalization asymmetry → phase 31's threat model.
- An `examples/**` instance-local deny-domain overlay — not built; the loader takes an explicit path
  so the seam stays open (the 28-D-14 idiom).

</deferred>

<open_questions>
## Open Questions

- **OQ-1 — Should D-16's registry binding land in Phase 30 or Phase 33?** Landing it here reds
  `docs-guard` until a human writes the ledger row, which blocks the branch on a human turnaround
  in the middle of the `30 → 31 → 32` chain. Deferring it to Phase 33 (which already carries
  SEAL-05's human-ratification work) batches the human step. **Recommendation: land it here**, as
  the final plan's blocking-human task, because a control declaration nothing is obliged to follow
  is exactly the defect this milestone names. Reversible: drop plan 30-04 Task 3.
- **OQ-2 — Should the drift test become its own CI job?** It rides the existing `pytest` job today
  (D-18, anti-sprawl). If phase 32 makes the registry the acceptance surface for the posture, a
  named job may be worth it then. Not decided here.

</open_questions>
