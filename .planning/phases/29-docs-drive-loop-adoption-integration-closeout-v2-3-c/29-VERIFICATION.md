---
phase: 29-docs-drive-loop-adoption-integration-closeout-v2-3-c
verified: 2026-07-21T00:00:00Z
verified_at_commit: 1e1ef3b
status: human_needed
score: 2/4 success criteria verified (SC-1, SC-2); SC-3 blocked on a human-only write; SC-4 partial
re_verification:
  previous_status: none
  note: "initial verification; no prior 29-VERIFICATION.md existed"
human_verification:
  - test: "RAT-1 — hand-author `docs/.docs-review-ledger.toml` from the byte-exact proposal in `29-04-SUMMARY.md`, outside an agent session, then run `uv run python -m tools.docs_guard`."
    expected: "exit 0; all 8 bindings FRESH (or exactly dispositioned). Verifier RECOMMENDS Option B (two rounds), not Option A: Option A satisfies SC-3's literal text but never observes the gate transition on a real doc edit, and this milestone's recurring defect is exactly a control that ships green without ever being seen to move."
    why_human: "ADR-0010 clause 3b. Three enforcement layers deny the agent write, all verified live in this report. A self-blessed row and an honest seed row are byte-identical; only the human commit separates them. No agent action can satisfy SC-3."
  - test: "RAT-2 — review ADR-0010 and flip `- **Status:** proposed` to accepted, filling Date and Deciders (both are em-dashes at `docs/adr/0010-human-docs-review-obligation-model.md:5-7`)."
    expected: "ADR-0010 status accepted; `registry._adr_status` stops treating it as a rejection."
    why_human: "ADRs are append-only once accepted; Phase 29 cannot amend it. Verified live: line 5 still reads `proposed`."
  - test: "DECISION — `lifecycle-eval` CI step 2 (`uv run pytest tools/lifecycle_eval`, ci.yml:194): repair now, or accept as recorded Phase-23 debt?"
    expected: "A one-line `conftest.py` (matching eighteen sibling tools members) makes the job command green. Deliberately NOT repaired by the closeout per T-29-21."
    why_human: "SC-4 names `lifecycle` as a fan-in item and that job's step 2 is red as written. It is a correctly-recorded pre-existing condition, not a Phase-29 regression — but SC-4 is not literally green until it is decided."
  - test: "DECISION — `examples/log-parser` golden parity (`IsConfined`, `examples/log-parser/components/toy-converter/Program.cs:163-183`): accept as host-only, or fix the comparison?"
    expected: "Green on `ubuntu-latest` (the job's runner); red on this macOS host. The underlying `StringComparison.Ordinal` against an unresolved `Path.GetTempPath()` is a genuine latent portability defect in the reference instance."
    why_human: "Cannot be settled without a decision about whether an example-instance portability bug is in v2.3's scope."
  - test: "RAT-3 / RAT-4 / RAT-5 — the provenance backlog (eight seeded binding dispositions; the Phase-28 `HARNESS_DEV_BYPASS` constitution write; four ADRs unmerged to `main` behind a CODEOWNERS gate that structurally cannot fire)."
    expected: "RAT-3 discharged together with RAT-1. RAT-4/RAT-5 need repo-config: flip the GitHub default branch back to `main`."
    why_human: "Ratification and repo administration; neither is an agent action."
---

# Phase 29: Docs Drive Loop + Adoption Integration + Closeout (v2.3 C) — Verification Report

**Phase Goal:** bounded 사람 대면 docs 워크플로를 추가하고 adoption seeding을 연결하며 세 테마를 전체 게이트 fan-in으로 닫는다.
**Verified:** 2026-07-21, at commit `1e1ef3b`, working tree clean (`git status --porcelain` empty)
**Status:** `human_needed`
**Re-verification:** No — initial verification.

Every number below was produced by running the command in this session. SUMMARY.md and
`.planning/v2.3-MILESTONE-AUDIT.md` claims were treated as hypotheses to falsify, not as evidence.
The audit's numbers reproduced exactly where I re-ran them; the three known reds all reproduced.

## Goal Achievement

### Observable Truths (the four ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC-1 | `/docs-update` + `docs-upkeep` emit byte-identically to both runtimes; the five exclusions are a TESTED gate | ✓ VERIFIED | Identity assertions present AND mutation-proven — see below |
| SC-2 | `/adopt` can propose a binding but cannot self-review it to green | ✓ VERIFIED | All three ADR-0010 clause-3b layers live; 306 tests green; registry stays writable |
| SC-3 | required seed documents are fresh or exactly dispositioned | ✗ NOT SATISFIED — human-only | `uv run python -m tools.docs_guard` exits **1**: 8 bindings, **0 FRESH, 0 dispositioned, 6 × `broken-binding`**. `docs/.docs-review-ledger.toml` does not exist |
| SC-4 | the full fan-in is green | ⚠️ PARTIAL | 12 of 14 executed commands exit 0; two red (one by design, one pre-existing) — table below |

**Score:** 2/4 verified, 1 partial, 1 blocked on a human-only write.

### SC-1 — verified, and mutation-proven

The lead's key question was whether `tools/docs_guard/exclusions.py` asserts IDENTITY rather than
equality, so that a locally retyped list cannot keep monkeypatch proofs green (Phase 28's CR-02).
It does — `tools/docs_guard/tests/test_exclusions.py:152,156,160`:

```
assert exclusions.CONSTITUTION_GLOBS is contract_guard.CONSTITUTION_GLOBS
assert exclusions.DERIVED_GLOBS   is destinations.DERIVED_GLOBS
assert exclusions.ADR_GLOBS       is registry.ADR_GLOBS
```

I did not take that on trust. I deleted each glob **at its home** and re-ran the test file, then
reverted with `git checkout`:

| Mutation at the home | Result |
|---|---|
| drop `"golden/**"` from `contract_guard.CONSTITUTION_GLOBS:43` | **1 failed** — `test_exclusion_reason_table[golden-plain]`, `assert None == 'constitution-plane'` |
| drop `"docs/reference/**"` from `destinations.DERIVED_GLOBS:105` | **1 failed** — `test_exclusion_reason_table[derived-docs-reference]` |
| drop `"docs/adr/**"` from `contract_guard.CONSTITUTION_GLOBS:43` | **3 failed** — `[adr-plain]`, `[adr-dot-segment]`, `test_accepted_adr_reason_is_distinct_from_constitution` |

The "delete a glob at its home and named rows red repo-wide" claim is **true as written**. Tree
restored to `1e1ef3b` after each run.

Five exclusion classes all covered: `contracts/**`, `docs/adr/**`, `golden/**` (constitution home),
`docs/reference/**` and `.memory/derived/**` (derived home).

Emit: `EXPECTED_SKILLS` is the 13-name frozenset including `docs-upkeep`
(`tools/harness_lint/caps.py:131-145`); `test_coexist.py:65-66` asserts exactly 25 commands in
BOTH runtime trees. Re-emit is a fixed point — `uv run python -m tools.harness_emit` wrote 100
artifacts and `git status --porcelain` came back **empty**. `docs-upkeep/SKILL.md` is byte-identical
across `.claude/` and `.opencode/` (`diff -r` clean); `docs-update.md` differs only by the two
opencode-specific frontmatter keys (`agent:`, `subtask:`), which is the emitter's per-runtime
contract, not drift. All four artifacts are git-tracked (checked with `git ls-files` — the bare-`git
diff` untracked blind spot did not bite here).

### SC-2 — verified, all three layers live and non-bypassable

| Layer | Artifact | Status |
|---|---|---|
| 1 — ordinary `Write`/`Edit` tool path | `tools/hooks/ledger_guard.py`, owns `REVIEW_LEDGER_GLOBS` | ✓ WIRED into `.claude/settings.json:165` PreToolUse(`Write|Edit`) and `.opencode/plugin/ledger-guard.ts` via `merge.py:91,154` |
| 2 — adoption-apply write path | `refuse_unsafe_destination` → `ReviewLedgerRefusal` (`apply.py:228`), importing the constant from layer 1 (`apply.py:65`) | ✓ WIRED; raised type is `ReviewLedgerRefusal`, not `ConstitutionRefusal` |
| 3 — greenness | `first_seen-unratified` history test (`ledger.py:54,378-421`), keyed on binding IDENTITY with the `repointed` half | ✓ WIRED |

No bypass exists in either the Python gate or the TS plugin — neither module reads
`GOLDEN_APPROVE_HUMAN` nor `HARNESS_DEV_BYPASS`, and `test_constitution_refusal.py:508-513` sets
**both** env vars and asserts `ledger_guard.decide(...)` still denies. That is a test that can fail,
not prose.

`docs/doc-dependencies.toml` stays agent-WRITABLE — confirmed by running the resolvers directly:
`resolve_path(REVIEW_LEDGER_GLOBS, 'docs/doc-dependencies.toml')` → `allow`, and
`resolve_path(CONSTITUTION_GLOBS, ...)` → `allow`, while the ledger path itself → `deny`. DOCSUP-07
is not caught by the refusal. The permission matrix `_note` states the same carve-out explicitly.

`uv run pytest tools/adoption_apply/tests/test_docs_binding_proposal.py
tools/adoption_apply/tests/test_constitution_refusal.py tools/docs_guard/tests/` → **306 passed**.

### SC-3 — NOT satisfied; the honest answer is that it requires the human

Live gate output at `1e1ef3b`:

```
docs-guard: 8 binding(s); 7 uncovered human-authored document(s) (no ratchet).
docs-guard: FAILED          # exit 1
```

Every one of the 8 bindings is `[BROKEN]`, reason `has no [[reviewed]] row in the ledger`. Zero are
FRESH; zero are dispositioned. SC-3's predicate is a LEDGER STATE, and there is no ledger.

**On 29-04's deviation D-2 — the lead's specific question.** The evidence offered in place of the
`0 → 1` leg is that `gate-model-permission-surface`'s target digest moved `4568f3a9… → 8df85e6e…`.
I confirmed that independently: the live gate prints
`target : harness/skills/gate-model/SKILL.md@8df85e6ef8c0`. So the bounded edit **is** visible to
the gate, and that claim is true.

But it does not suffice for SC-3, and I do not think it is close. What it proves is that the
digest pipeline observes a real edit — a property SC-1/DOCSUP-02 already establish. What SC-3 asks
is whether the review obligation resolves, and that is a statement about a file that does not
exist. The binding was BROKEN before and after the edit for the strictly prior reason, so no
`fresh → stale` transition was ever expressed; the "0" in "0 → 1 → 0" was never the same 0.

**Recommendation: the human should take Option B, not Option A.** Option A (one authoring round
straight to exit 0) satisfies SC-3's literal text and is defensible. But Phase 29's own narrative —
and the reason this criterion exists — is the drive loop, and Option B is the only version in which
anyone watches the gate go green → red → green on a real document edit. This milestone's recurring
defect, in 26, 27, 27.1, 27.2 and 28, has been a control that ships green while never being seen to
move. Choosing the cheaper option here would be that pattern one more time.

### SC-4 — fan-in, my independently observed numbers

Run at `1e1ef3b`, clean tree, on this macOS host. Nothing was repaired during the run.

| # | SC-4 item | Command | Exit | Observed |
|---|---|---|---|---|
| 1 | full pytest | `uv run pytest -q` | **0** | **1473 passed, 8 snapshots passed** in 72.49s |
| 2 | contract-drift (root) | `tools.contract_drift.drift` | **0** | clean |
| 2b | contract-drift (example) | same, `--contracts-dir examples/log-parser/contracts` | **0** | clean |
| 3 | golden (root identity) | `uv run pytest tools/golden_runner` | **0** | **17 passed** |
| 3b | golden (example .NET parity) | `uv run pytest examples/log-parser/tests` | **1** | **2 failed, 10 passed** — `toy-converter exited 3: path confinement violation` |
| 4 | workspace drift | `tools.contract_drift.drift --workspace` | **0** | clean |
| 4b | cross-repo pytest set | the five paths at `ci.yml:312` | **0** | **31 passed** |
| 5 | stale-derived | `docs_sync && memory_regen.contracts_index`, then porcelain | **0** | porcelain over `docs/reference` + `.memory/derived` **empty** |
| 6 | lifecycle (runner) | `tools.lifecycle_eval.runner` | **0** | green |
| 6b | lifecycle (tests) | `uv run pytest tools/lifecycle_eval` | **2** | **RED — 1 error at collection**, `ModuleNotFoundError: No module named 'tools'` |
| 7 | GEN-04 twin + model-id + injector | `uv run pytest -k "model_id or injector or budget or core_no_example"` | **0** | **42 passed** |
| 7b | full harness lint | `uv run pytest tools/harness_lint -q` | **0** | **316 passed** |
| 8 | docs guard | `uv run python -m tools.docs_guard` | **1** | 8 bindings, 6 × broken-binding — by design, RAT-1 |
| 9 | emit-drift | `tools.harness_emit` then `git status --porcelain` | **0** | **100 artifacts, porcelain EMPTY** |
| 12 | `git diff --check` | `git diff --check` | **0** | clean |

**Every audit number I re-ran reproduced exactly** — 1473, 17, 31, 316, 100 artifacts, 8 bindings /
7 uncovered. The audit is accurate; I found no inflated claim in it.

Disposition of the three reds:

**(a) `docs-guard` exit 1 — NOT a Phase 29 gap.** Correct-by-design, and the same blocker as SC-3.
The gate is doing exactly what Theme C built it to do: refuse to call a binding fresh without a
human-committed row. Marking this green would require the agent to write the ledger, which is the
thing the phase exists to prevent.

**(b) `lifecycle-eval` step 2 — a REAL red in a named SC-4 fan-in item, correctly recorded as
pre-existing.** I reproduced it (`ModuleNotFoundError: No module named 'tools'`, exit 2) and
confirmed the diagnosis: `tools/lifecycle_eval/tests/` has neither `__init__.py` nor a
root-inserting `conftest.py`, unlike its siblings, and the full suite is green only because a
sibling conftest already inserted the root. Origin is Phase 23, not Phase 29, and T-29-21
deliberately left it unrepaired — which I endorse as the right closeout discipline; a closeout that
repairs on the way past reports a state that never existed. **But it does mean SC-4 is not
literally green,** so I am not calling SC-4 verified. Escalated as a human decision rather than
silently accepted.

**(c) `golden` step 2 — host condition, NOT a Phase 29 gap, but a genuine latent defect.** I
reproduced it and confirmed the mechanism from the failure output: pytest's `tmp_path` realpaths to
`/private/var/folders/...` while .NET's `Path.GetTempPath()` returns the `/var/folders/...`
spelling, and `IsConfined` (`Program.cs:163-183`) compares `StringComparison.Ordinal` against an
unresolved root. On `ubuntu-latest` both are `/tmp`. The "host artifact" framing is correct for CI
purposes, but the underlying code is a real portability bug in the reference instance — a confinement
check that depends on which OS spells temp which way is weak in the same way the audit criticizes
elsewhere. Escalated as a decision, not folded into a pass.

### Residual set — independently spot-checked, complete and durable

I verified a sample of the audit's residuals against the live tree rather than accepting the list:

| Residual | Live check | Result |
|---|---|---|
| `emit-drift` uses bare `git diff --exit-code` (15-REVIEW CR-01) | `sed -n '213p' .github/workflows/ci.yml` | ✓ still bare — untracked-blind, as claimed |
| `tools/hooks/secret_scan.py:44-47` PATTERNS hardcoded, not read from contract | read the module | ✓ present and unchanged |
| pre-existing ruff `I001` on `tools/adoption_apply/cli.py` | `uv run ruff check` | ✓ `Found 1 error`, 1 fixable |
| ADR-0010 still `proposed` | `docs/adr/0010-...md:5-7` | ✓ `- **Status:** proposed`, Date and Deciders are em-dashes |
| `examples/**` docs-registry overlay seam left open (28 D-14) | audit `tech_debt` | ✓ recorded, not built |

28-REVIEW's CR-01..03 / WR-01..04 / IN-01..03, 27.2's AD-01/AD-02/`I001`, 27.1's IN-02/WR-08,
`secret_scan.py:44-47`, the `examples/**` overlay seam and `emit-drift`'s bare-`git diff` blindness
are **each present in `.planning/v2.3-MILESTONE-AUDIT.md` with a fixed-plus-commit-hash or
accepted-with-rationale disposition. None is silently dropped.** The audit also disambiguates the
two same-named `IN-02` findings (28's backslash-destination vs 27.1's flock/NFS), which is the kind
of collision that usually loses one of them.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|---|---|---|---|
| `harness/permission-matrix.json` `path_deny_globs` | `docs/reference/**` and `.memory/derived/**` are NOT in the deny list, and no PreToolUse hook denies them | ⚠️ WARNING | Two of SC-1's five exclusion classes are enforced only at the DECISION layer (`exclusion_reason` + the wiring lint on the command prose). The write-side backstop is the `stale-derived` CI job, which is DETECTIVE (regenerate-and-diff after the fact), not preventive like `contract_guard`/`ledger_guard`. Not a Phase-29 defect — SC-1 asks for a tested classifier gate and that is what shipped, mutation-proven — but the asymmetry is worth recording so nobody later reads "five exclusions are gated" as "five exclusions have a runtime deny". |
| `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` | 983 committed trailing-whitespace lines | ℹ️ INFO | Syrupy generator artifact in a derived snapshot. `git diff --check` is clean only because the tree is clean; it surfaces on regeneration. Already recorded in the audit. |

No debt-marker gate violations: no unreferenced `TBD`/`FIXME`/`XXX` in the phase's modified files.

### Requirements Coverage

| Requirement | Status | Evidence |
|---|---|---|
| DOCSUP-06 | ⚠️ machinery complete, BLOCKED on RAT-1 | `exclusions.py` mutation-proven; `/docs-update` + `docs-upkeep` emitted to both runtimes; skills 12→13 and commands 24→25 moved in the same change. The gate cannot report satisfied while `docs-guard` exits 1. |
| DOCSUP-07 | ✓ SATISFIED | All three enforcement layers live and mutation-proven; registry stays agent-writable; 306 tests green. This is SC-2 and it holds independently of the ledger. |

### Gaps Summary

Phase 29 built everything an agent can build, and the parts I could attack held up: the identity
assertions are real, the deletion proofs bite, the ledger gate honours no token, and every audit
number reproduced. I went looking for this milestone's recurring defect — a control that ships
green while bypassable — and did not find a new instance of it in Phase 29's own surface.

The phase does not close, for one structural reason and one recorded one:

1. **SC-3 cannot be satisfied by any agent action.** It needs RAT-1 (and RAT-2 for Phase 28's own
   closure). The digest-movement evidence proves edit visibility but not the SC-3 predicate; my
   call is that the human should take **Option B**, so the drive loop is actually observed rather
   than inferred.
2. **SC-4 is not literally green** — `lifecycle-eval` step 2 is red as written. Pre-existing to
   Phase 29 and correctly recorded rather than repaired on the way past, but it needs an explicit
   accept-or-fix decision rather than a silent carry.

Status is `human_needed` rather than `gaps_found`: no agent-actionable item in Phase 29's scope is
outstanding, and the two blocking items are a human ratification and a human decision.

---

_Verified: 2026-07-21 at commit `1e1ef3b`_
_Verifier: gsd-verifier (goal-backward, adversarial stance)_
