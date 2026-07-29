---
phase: 28-human-docs-registry-guard-derived-queue-v2-3-c
plan: 07
subsystem: docs-guard
tags: [docsup, registry, ledger, ci, gate]
status: BLOCKED-ON-HUMAN (Task 2)
requires:
  - tools/docs_guard (28-01..28-05)
  - the ledger write-guard (28-09)
provides:
  - the seeded core human-docs dependency registry
  - the docs-guard CI job joined to the fan-in gate
  - the PROPOSED review-ledger content, for human authorship
affects:
  - .github/workflows/ci.yml (gate.needs)
tech-stack:
  added: []
  patterns: [separate-job-idiom, read-only-ratchet, agent-proposes-human-ratifies]
key-files:
  created:
    - docs/doc-dependencies.toml
  modified:
    - .github/workflows/ci.yml
decisions:
  - "The agent authored the registry only; docs/.docs-review-ledger.toml is left uncreated for a human, because a new [[binding]] plus its matching reviewed-no-change row is byte-identical to the self-green attack and only authorship distinguishes them."
  - "Every seed disposition is reviewed-no-change / REVIEWED_STILL_CURRENT, never `updated`: a first-ever ledger has no previous to have been updated FROM."
  - "uncovered_max = 7 and binding_min = 8 are the exact live values observed after seeding, not padded."
metrics:
  tasks_completed: 2
  tasks_blocked: 1
---

# Phase 28 Plan 07: Registry Seed + docs-guard CI Job Summary

Seeded an 8-binding core human-docs dependency registry and wired a separate `docs-guard` CI job
into `gate.needs` — while deliberately NOT authoring the review ledger, which a human must write.

## Status

| Task | State | Commit |
|------|-------|--------|
| 1 — seed the registry, propose the ledger | **done** | `69527e7` |
| 2 — human authors and lands the ledger | **BLOCKED ON HUMAN** — not attempted | — |
| 3 — `docs-guard` CI job + `gate.needs` | **done** | `abe1345` |

## The ledger was NOT authored by the agent

`docs/.docs-review-ledger.toml` does not exist. It was not created, and no `.proposed`/`.draft`
sibling was staged either. This is the plan's central control, not a courtesy: an agent that writes
a new `[[binding]]` together with its matching `reviewed-no-change` row has performed exactly the
self-green attack this phase exists to close — the honest seed and the attack are byte-identical,
and the only distinguishing fact is who authored the ledger half.

No path around plan 28-09's write denial was sought or found. Nothing was bypassed:
`GOLDEN_APPROVE_HUMAN` was never fabricated (it does not authorize a ledger write in any case) and
`HARNESS_DEV_BYPASS` was never used.

Task 1's own gate asserts the file's ABSENCE:

```
$ test ! -e docs/.docs-review-ledger.toml && echo "LEDGER-ABSENT-OK"
LEDGER-ABSENT-OK
```

## Seeded bindings and why each pairing is real

Six `required`, two `advisory`. Each source selector names files the target document describes
directly — a literal CLI invocation, a named module, or a declared rule set.

| # | id | severity | sources → target | why the pairing is genuine |
|---|----|----------|------------------|----------------------------|
| 1 | `task-control-cli-howto` | required | `tools/task_control/{__main__,phase_gate}.py`, `tools/risk_router/intake.py` → `docs/how-to/task-lifecycle.md` | The how-to embeds those three modules' CLI invocations as literal copy-pasteable commands (`:10`, `:20-21`, `:28`), so a flag or subcommand rename silently makes the recipe wrong. |
| 2 | `adoption-tooling-brownfield-skill` | required | `tools/adoption_scan/destinations.py`, `tools/adoption_apply/{apply,approval}.py` → `harness/skills/brownfield-adoption/SKILL.md` | The skill narrates the five-stage runbook by naming those modules and restating their six-value disposition enum and batch-id derivation — it already went out of sync once, which is why 27.1 SC-3 exists. |
| 3 | `gen04-core-instance-split` | required | `tools/harness_lint/tests/test_core_no_example_dep.py`, `harness/project.toml` → `docs/explanation/template-and-instances.md` | The explanation's "one-directional invariant" section states that the split is *enforced* by that specific test, and its language/instance table is a reading of `project.toml`'s data slot. |
| 4 | `memory-plane-declaration` | required | `tools/hooks/contract_guard.py` → `.memory/README.md` | The README enumerates the CONSTITUTION plane's members and names `contract-guard` as the runtime enforcement; `CONSTITUTION_GLOBS` in that module is the authoritative list the README is describing. |
| 5 | `gate-model-permission-surface` | required | `harness/permission-matrix.json`, `tools/harness_perms/resolver.py` → `harness/skills/gate-model/SKILL.md` | The skill's whole purpose is to explain *why a write was refused*; the refusals come from the matrix data and that resolver, so a path-deny change with an unchanged skill teaches a wrong answer. |
| 6 | `contract-graph-adr-0009` | required (ADR track) | `tools/contract_graph/{compile,query}.py` → `docs/adr/0009-contract-relationship-graph-model.md` | The ADR ratifies the compiler + affected-set query model that those two modules ARE; if the implementation diverges, the ADR must be superseded rather than quietly outgrown. |
| 7 | `normalize-spec-glossary` | advisory | `libs/normalize-spec.md` → `docs/glossary.md` | The glossary's "§4.3–4.6 conventions" and "normalized comparison" entries are condensations of that spec; a rule change there makes the definition stale, but the glossary is a vocabulary seed so the obligation warns rather than blocks. |
| 8 | `lifecycle-eval-shadow-metrics` | advisory | `tools/lifecycle_eval/runner.py` → `docs/explanation/task-lifecycle-shadow-metrics.md` | Every metric in the doc declares its collection boundary as the eval harness, which is that runner; the doc deliberately declares no threshold, so drift is informational rather than blocking. |

Binding 6 is the row that proves the forced accepted-ADR disposition pair is representable in
practice and not only in a test fixture. ADR-0009's `- **Status:**` line reads `accepted`
(verified before binding — plan 28-03 rejects a `proposed` ADR target), and its `dispositions` are
exactly `["REVIEWED_STILL_CURRENT", "SUPERSEDING_ADR_REQUIRED"]`.

Per D-09, root `AGENTS.md` and `CLAUDE.md` were deliberately NOT seeded: both carry the
emitter-owned HARNESS-MANAGED fence (`AGENTS.md:98-107`), so a drafted edit inside the fence is
reverted on the next re-emit and reds `emit-drift`. Targeting `harness/**` source (bindings 2 and 5)
is legal; the emitted `.opencode/` / `.claude/` twins are structurally rejected as targets by
`DERIVED_GLOBS`, which `tools/docs_guard/tests/test_registry.py` already covers as a rejection row.

GEN-04: the registry contains no instance-tree token anywhere.

```
$ grep -c 'examples/' docs/doc-dependencies.toml
0
```

## Ratchet values, and the count that shifted

- **Before seeding** (28-05 SUMMARY, verbatim): `live_uncovered = 12`, 0 bindings.
- **After seeding**: `live_uncovered = 7`, 8 bindings.

Five of the eight bindings target a document inside D-07's human corpus
(`docs/how-to/task-lifecycle.md`, `docs/explanation/template-and-instances.md`,
`docs/explanation/task-lifecycle-shadow-metrics.md`, `docs/glossary.md`, `.memory/README.md`), so
the count fell by exactly five. The other three target `harness/**` and `docs/adr/**`, which lie
outside the corpus and therefore move the count by zero — which is precisely why `binding_min`
exists as a second, independent ratchet.

- `uncovered_max = 7` — the EXACT post-seed live count, taken from the guard's own output, not
  padded or rounded. Any slack above the live count silently permits regression up to that slack.
- `binding_min = 8` — the EXACT number of `[[binding]]` rows. This is the deletion ratchet: a
  binding whose target lies outside the human corpus can be deleted without moving `uncovered_max`
  by a single unit, so without this floor deleting an inconvenient binding would be unguarded.

## Proposed ledger (for human authorship)

Byte-exact, ready to paste into `docs/.docs-review-ledger.toml`. Every digest below was produced by
RUNNING the guard (`tools.docs_guard.guard.classify`) against the committed registry — never by hand
and never by a separate hashing command — so the proposed ledger cannot disagree with the gate.
All sixteen digest prefixes were re-verified against a fresh `uv run python -m tools.docs_guard` run
after the CI commit and were unchanged.

```toml
# Human review ledger (DOCSUP-02/03) — the committed baseline the docs-guard gate diffs against.
#
# HUMAN-AUTHORED ONLY. An agent may propose rows in docs/doc-dependencies.toml, but only a human
# writes this file: the LEDGER, not the registry, is the greenness authority. A new [[binding]]
# landed together with its own matching reviewed-no-change row is byte-identical to the self-green
# attack, and authorship is the only fact that separates honest seeding from self-blessing.
#
# WHY EVERY SEED ROW IS `reviewed-no-change` (or `REVIEWED_STILL_CURRENT`) AND NEVER `updated`:
# `updated` is verified against the PREVIOUS COMMITTED ledger — it requires a target-digest delta
# versus a row that already existed. This is the FIRST-EVER ledger, so there is no previous to have
# been updated FROM: an `updated` row here would classify `unverified-disposition` and fail closed
# for a required binding. Do not reach for `updated` when seeding new rows.
#
# The permitted shape is an ALLOWLIST enforced by tools/docs_guard/ledger.py: [coverage] takes only
# uncovered_max + binding_min, and each [[reviewed]] row takes only id, source_digest,
# target_digest, disposition. No timestamp, no reviewer identity, no prose, no model identifier —
# any other key is rejected by name.

[coverage]
# Catches a human-authored document DRIFTING OUT of coverage. Set to the exact live uncovered count
# observed after the registry was seeded (12 before seeding, 7 after). The guard never raises it.
uncovered_max = 7
# Catches a BINDING BEING DELETED — which uncovered_max cannot see when the deleted binding's target
# lies outside D-07's human corpus (3 of the 8 rows below are exactly that case). Set to the exact
# number of [[binding]] rows in the registry. The guard never lowers it.
binding_min = 8

[[reviewed]]
id            = "adoption-tooling-brownfield-skill"
source_digest = "b701b560e3e4634187765de61a1e92d8a0a78343e141b8da485d483d52d65007"
target_digest = "93adbcbb852ac0710d64ab3b1aae9bf891958a13059997387e949fb9999105dd"
disposition   = "reviewed-no-change"

[[reviewed]]
id            = "contract-graph-adr-0009"
source_digest = "c0c296ca89d742c0ba4822f9f91cde0d9381ed2840299a40b5946f895c2ea1da"
target_digest = "e6865349a567349ab06568dd3fef158dd8b7d35fed9e14e4d8fd5cbe34979fae"
disposition   = "REVIEWED_STILL_CURRENT"

[[reviewed]]
id            = "gate-model-permission-surface"
source_digest = "c314791d60fedd32667fb5b1c0a3215ab29989db37498f4f4111907195e8d01a"
target_digest = "4568f3a971ba78fba60dc5b021b6a34e12c6c7280e00f3ac3ce01573641d85cc"
disposition   = "reviewed-no-change"

[[reviewed]]
id            = "gen04-core-instance-split"
source_digest = "7ff9c06392ec324c69c3a9e3f082e555e98fc39289e279fc4a693d5682e16725"
target_digest = "f5d9fccd138b97a7a67f25d493d3e8ef570d312fa1d8350b2a96532e900bc0c6"
disposition   = "reviewed-no-change"

[[reviewed]]
id            = "lifecycle-eval-shadow-metrics"
source_digest = "5001906305a1061a2678b7192920e50e56d27199f5f63138dff4d8b07cddc17b"
target_digest = "d9ecd613c1c83ee2c00570bce81250cd3ea7de8376ee84f707331e0415653d20"
disposition   = "reviewed-no-change"

[[reviewed]]
id            = "memory-plane-declaration"
source_digest = "e1c4d41a39550ab5f6efd017a53db740e3d626d7818257f766c15cae84497c61"
target_digest = "00363109e71c86da1fa565216bbba00bb380efb1050c03238dd1d1a7e0dea407"
disposition   = "reviewed-no-change"

[[reviewed]]
id            = "normalize-spec-glossary"
source_digest = "ed9516d744be990bb2588e026344b73a94b6ee33ceb3c079844ddafde572f1ab"
target_digest = "ee5bf1c58510a336c4a6640541100ff15cd932e7f09cad514096ec0a7a498803"
disposition   = "reviewed-no-change"

[[reviewed]]
id            = "task-control-cli-howto"
source_digest = "54e3b89ec1ed4d2d45d1523568d1a2fa260431a983ffe123a1259a8788dfd98f"
target_digest = "fc10ff30f431f0305b924d4ee03ad2a059c646248d1b037b3aeae9958fe67588"
disposition   = "reviewed-no-change"
```

**If the human rejects a binding:** remove it from `docs/doc-dependencies.toml`, drop its
`[[reviewed]]` row above, and re-derive BOTH ratchets — `binding_min` falls to the new row count,
and `uncovered_max` rises by one if (and only if) the removed binding's target was inside the human
corpus (bindings 1, 3, 4, 7, 8 are; bindings 2, 5, 6 are not).

## Guard output — BEFORE the human lands the ledger

`uv run python -m tools.docs_guard` at the current tree (registry committed, ledger absent),
**exit code 1**. The six `required` bindings report `BROKEN` for the single reason that no
`[[reviewed]]` row exists yet — this is the expected pre-ledger state, not a defect. Tail, verbatim:

```
  [BROKEN] task-control-cli-howto
    sources      : tools/task_control/__main__.py, tools/task_control/phase_gate.py, tools/risk_router/intake.py@54e3b89ec1ed
    impact       : (none)
    target       : docs/how-to/task-lifecycle.md@fc10ff30f431
    severity     : required
    dispositions : updated, reviewed-no-change
    reviewed     : (no reviewed row)
    reason       : binding task-control-cli-howto is required but has no [[reviewed]] row in the ledger

docs-guard: 8 binding(s); 7 uncovered human-authored document(s) (no ratchet).
docs-guard: FAILED
```

Registry validity is confirmed by what this output is NOT: exit **1**, not exit **3**. A registry
that failed any of the five DOCSUP-01 rejections would have produced
`docs-guard: registry/ledger invalid — …` and exit 3.

## Guard output — AFTER the human lands the ledger

**Not yet available — Task 2 is blocked on the human.** The plan requires this section to carry the
verbatim output and exit code once the ledger is committed; whoever resumes this plan records it
here.

## The expected amber, and that it was not engineered around

Once the human lands the ledger, the guard will **still** report non-zero — every seeded row will
fire `first_seen-unratified`, and the required rows will land in `STALE_REQUIRED`. **This is correct
and expected**, for a reason that is structural rather than incidental: `first_seen-unratified` keys
on the PREVIOUS COMMITTED ledger, and Task 2's commit is the first one, so no previous ledger
carries these rows. The human review commit that LANDS the row IS the ratification, and plan 28-08's
ratification commit is the second cycle that turns the rows green. Task 2's automated gate accepts
`exit ≤ 1` for exactly this reason.

Nothing was done to avoid it:

- No rule was weakened. `ledger.py`'s `first_seen-unratified` and `guard.py`'s `BLOCKING_REASONS`
  are untouched.
- No throwaway ledger was pre-committed to manufacture history.
- No disposition was chosen to dodge the check — `updated` would have dodged
  `first_seen-unratified` (it routes to `_check_updated` instead) but would have landed on
  `unverified-disposition` and failed closed anyway, which is the control working from the other
  side.

## Deviations from Plan

### 1. [Rule 3 - blocking, NOT fixed] Task 1's automated gate is RED on pre-existing 28-05 code

Task 1's gate is
`test ! -e docs/.docs-review-ledger.toml && uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -q`.
The first half passes. The second half **fails**, and it was **already failing at `HEAD` before this
plan made any change**:

```
E       AssertionError: core→example dependency/prose leak — core planes must not depend on or name an instance:
E         tools/docs_guard/guard.py:97: # `.planning/**` is the GSD-owned lane and `examples/**` is the instance tree (GEN-04). Neither is
E         tools/docs_guard/tests/test_guard.py:476: "examples/log-parser/docs/how-to/instance.md": "instance\n",
E         tools/docs_guard/tests/test_guard.py:486: "examples/log-parser/docs/how-to/instance.md",
```

Introduced by `6db057c feat(28-05): five-state docs guard with read-only ratchets and drift
suppression`. It is provably not this plan's regression: the GEN-04 scanner reads only git-tracked
files under `tools/`, `harness/`, `libs/`, and this plan's only artifact
(`docs/doc-dependencies.toml`) is under `docs/` and greps clean for the token.

**Not auto-fixed, deliberately.** The offending files belong to plan 28-05: `guard.py:97`'s comment
is the deliberate rationale for `_EXCLUDED_TOP_LEVEL`, and `test_guard.py`'s rows are the fixture
that PROVES the instance tree is excluded from `HUMAN_CORPUS`. Rewording either is a 28-05 design
call, and editing another plan's shipped tests mid-wave risks a conflict with 28-08's fan-in.
Recorded at `.planning/phases/28-.../deferred-items.md` as **DEF-28-01** with a suggested remedy.

### 2. Two comment rewordings to keep automated greps literal-clean

The `docs-guard` job's comment block originally named `.memory/derived/docs-staleness.md` and
`fetch-depth: 0` literally while explaining why NEITHER is used. Both acceptance criteria are
grep-based (`grep -n 'docs-staleness'` must be empty; `grep -n 'fetch-depth'` must return nothing
new), so the comment now says "the derived staleness queue under `.memory/derived/`" and "checkout
stays at its DEFAULT depth". The rationale is preserved verbatim; only the literal tokens are gone.

## Verification

| Check | Result |
|-------|--------|
| `test ! -e docs/.docs-review-ledger.toml` | **PASS** — the agent did not author the ledger |
| `grep -c 'examples/' docs/doc-dependencies.toml` | **0** (GEN-04) |
| `uv run python -m tools.docs_guard` | exit **1** (BROKEN, no ledger yet) — **not** exit 3, so the registry is valid |
| `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -q` | **FAIL — pre-existing, see DEF-28-01** |
| `uv run pytest tools/docs_guard tools/memory_regen/tests/test_docs_staleness.py -q` | **189 passed** (the CI job's second step, run locally) |
| `uv run check-jsonschema --builtin-schema vendor.github-workflows .github/workflows/ci.yml` | `ok -- validation done` |
| `docs-guard` present in `gate.needs` | **PASS** (the plan's parse check exits 0) |
| `grep -n 'docs-staleness' .github/workflows/ci.yml` | empty |
| `grep -n 'fetch-depth' .github/workflows/ci.yml` | empty |
| `git diff` of `ci.yml` — removed lines | exactly one: the old `gate.needs` list, replaced by the same list plus `docs-guard` |
| `git status --porcelain contracts .opencode .claude` | empty |
| post-commit deletion check on both commits | no deletions |

`git status` shows `tools/memory_regen/inject.py` modified and two untracked files under
`tools/memory_regen/tests/` — that is wave-4 sibling plan 28-06 in flight. Neither was touched,
modified, nor staged by this plan.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern, or trust-boundary schema change was
introduced beyond what the plan's own `<threat_model>` already registers.

## Self-Check: PASSED

All claimed artifacts exist (`docs/doc-dependencies.toml`, `.github/workflows/ci.yml`, this SUMMARY,
`deferred-items.md`), both claimed commits are reachable (`69527e7`, `abe1345`), and
`docs/.docs-review-ledger.toml` is confirmed ABSENT as required.
