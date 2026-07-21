---
phase: 29-docs-drive-loop-adoption-integration-closeout-v2-3-c
plan: 04
subsystem: docs-review-gate
status: PARTIAL — tasks 1 and 3 executed; tasks 2 and 4 BLOCKED-ON-HUMAN by design
tags: [docs-guard, ledger, gate-model, human-ratification, ADR-0010]
requires:
  - tools/docs_guard (28-05)
  - tools/hooks/ledger_guard.py (28-CR-02)
  - harness/commands/docs-update.md + harness/skills/docs-upkeep (29-03)
provides:
  - the re-derived, paste-ready docs/.docs-review-ledger.toml content for HUMAN authorship
  - corrected harness/skills/gate-model/SKILL.md deny-domain + hook-surface prose
affects:
  - harness/skills/gate-model/SKILL.md and both emitted twins
key-files:
  created: []
  modified:
    - harness/skills/gate-model/SKILL.md
    - .opencode/skill/gate-model/SKILL.md
    - .claude/skills/gate-model/SKILL.md
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
decisions:
  - "CR-03 landed WITHOUT a binding_digest column; the shipped _ROW_KEYS is the 4-key shape and is authoritative over the plan's <interfaces> prose"
  - "the task-3 edit was executed BEFORE the human authored the ledger, so the human authors against POST-edit state — see 'What the human must do'"
metrics:
  tasks_executed: 2 of 4
  tasks_blocked_on_human: 2
  commits: 1
---

# Phase 29 Plan 04: Docs Drive Loop — Agent Half Summary

The agent half of SC-3: every ledger digest re-derived by calling the shipped guard, and the
`gate-model` deny-domain prose corrected so the human ratifies against complete prose. **No ledger
file was created, drafted, staged, or committed** — that write is the control the milestone
converges on and it belongs to a human.

## Absolute-prohibition compliance

- `docs/.docs-review-ledger.toml` **does not exist**. `test ! -e docs/.docs-review-ledger.toml` →
  `LEDGER-ABSENT-OK`, verified at the start of task 1 and again after the task-3 commit.
- No `.proposed` / `.draft` / scratch sibling was created anywhere — not in the repo, not in the
  scratchpad. See "Deviation D-2" for the one observation this cost.
- `GOLDEN_APPROVE_HUMAN` and `HARNESS_DEV_BYPASS` were never set, read, or forged.
- `tools/hooks/ledger_guard.py` was never invoked or probed for a bypass. No path around it was
  sought; none is reported.

---

## Task 1 — re-derived ledger content (EXECUTED)

### Shape read from shipped code, not from the plan

```
$ uv run python -c "from tools.docs_guard.ledger import _ROW_KEYS, _COVERAGE_KEYS; ..."
ROW_KEYS ['disposition', 'id', 'source_digest', 'target_digest']
COV ['binding_min', 'uncovered_max']
```

**The plan's `<external_dependency>` says to STOP if `binding_digest` is absent from `_ROW_KEYS`.
It is absent, and stopping would be wrong.** `28-FIXES.md` records that CR-03 was fixed
(`2b504a6`) by a *deliberately different* design: `registry.identity_digest(sources, target)` +
a previous-committed-**registry** comparison (`repointed_ids`, a required argument on
`check_coherence`), explicitly rejecting the reviewer's `binding_digest` column so that "a human
ratifier still hand-writes only the two content digests and never a third derived value". The
dependency's *purpose* — do not ask a human to sign a shape that is about to be rejected — is
satisfied: the shipped 4-key shape IS the post-CR-03 shape. Proceeded; flagged as deviation D-1.

### Digests

Every value below was produced by calling `tools.docs_guard.guard.classify(registry_path=…)` —
the same entry point the gate uses. Nothing was hand-hashed and no separate hashing command was
run.

### Diff against `28-07-SUMMARY.md`'s proposed ledger

| Binding | source_digest | target_digest |
|---|---|---|
| adoption-tooling-brownfield-skill | **MOVED** `b701b560…` → `c8b6660d…` | unchanged |
| contract-graph-adr-0009 | unchanged | unchanged |
| gate-model-permission-surface | unchanged | **MOVED by task 3** `4568f3a9…` → `8df85e6e…` |
| gen04-core-instance-split | unchanged | unchanged |
| lifecycle-eval-shadow-metrics | unchanged | unchanged |
| memory-plane-declaration | unchanged | unchanged |
| normalize-spec-glossary | unchanged | unchanged |
| task-control-cli-howto | unchanged | unchanged |

- **`adoption-tooling-brownfield-skill` source moved** because Phase 28's own review fixes touched
  a binding source: `tools/adoption_apply/apply.py` changed in `ef793a8` (CR-02, importing
  `ledger_guard.REVIEW_LEDGER_GLOBS`) and `1810085` (IN-02). Not caused by 29-01..29-03.
- **The plans the task asked me to check against — 29-01..29-03 — moved NOTHING.** They touched
  `tools/docs_guard/**`, `tools/harness_lint/caps.py` and `tools/harness_emit/**`; none of those
  paths is named by any binding's source selector. `gen04-core-instance-split` sources
  `tools/harness_lint/tests/test_core_no_example_dep.py` + `harness/project.toml`, **not**
  `caps.py`, so it is correctly unchanged. Recording "unchanged" explicitly, as the plan requires.

### Ratchets, re-derived live

- `uncovered_max = 7` — the EXACT live uncovered count (`classify()['uncovered']['live'] == 7`).
  No padding. Paths: `AGENTS.md`, `CLAUDE.md`, `docs/explanation/README.md`,
  `docs/explanation/agent-workflow-skillset-design-guide.md`,
  `docs/explanation/next-milestone-task-control-plane.md`, `docs/how-to/README.md`,
  `docs/tutorials/README.md`.
- `binding_min = 8` — the EXACT number of `[[binding]]` rows in `docs/doc-dependencies.toml`.

### Paste-ready ledger — POST-edit (recommended: one authoring round)

Use this if you take Option A below. `gate-model-permission-surface` carries the POST-edit target
digest `8df85e6e…`, which is what is in the tree at `af9739b`.

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
# Catches a human-authored document DRIFTING OUT of coverage. Set to the exact live uncovered
# count. The guard never raises it.
uncovered_max = 7
# Catches a BINDING BEING DELETED — which uncovered_max cannot see when the deleted binding's
# target lies outside D-07's human corpus. Set to the exact number of [[binding]] rows in the
# registry. The guard never lowers it.
binding_min = 8

[[reviewed]]
id            = "adoption-tooling-brownfield-skill"
source_digest = "c8b6660d6cc62ee8cf2911c9702bb91f0d510edd1ced5309c26ca2420387e60d"
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
target_digest = "8df85e6ef8c0365638d9613c9c7d5047482a78e35f0f4860f960ccd55a1c4451"
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

### The one-line variant for Option B

If you take Option B (two rounds, to observe the loop literally), the **only** difference in round
one is that `gate-model-permission-surface` carries the PRE-edit target digest:

```toml
target_digest = "4568f3a971ba78fba60dc5b021b6a34e12c6c7280e00f3ac3ce01573641d85cc"
```

and round two replaces that row with:

```toml
[[reviewed]]
id            = "gate-model-permission-surface"
source_digest = "c314791d60fedd32667fb5b1c0a3215ab29989db37498f4f4111907195e8d01a"
target_digest = "8df85e6ef8c0365638d9613c9c7d5047482a78e35f0f4860f960ccd55a1c4451"
disposition   = "updated"
```

`disposition = "updated"` is correct in round two and only in round two: there IS a previous
committed ledger, the source digest is unchanged and the target digest genuinely moved, so
`_check_updated` finds `source_moved=False, target_moved=True` and returns no finding.

---

## Task 2 — BLOCKED-ON-HUMAN (`checkpoint:human-verify`, `gate="blocking-human"`)

Not attempted. The agent does not write, stage, or draft this file.

---

## Task 3 — drive-loop exercise (EXECUTED)

### Observation point 1 — guard BEFORE the edit

```
  [BROKEN] gate-model-permission-surface
    sources      : harness/permission-matrix.json, tools/harness_perms/resolver.py@c314791d60fe
    impact       : (none)
    target       : harness/skills/gate-model/SKILL.md@4568f3a971ba
    severity     : required
    dispositions : updated, reviewed-no-change
    reviewed     : (no reviewed row)
    reason       : binding gate-model-permission-surface is required but has no [[reviewed]] row in the ledger

docs-guard: 8 binding(s); 7 uncovered human-authored document(s) (no ratchet).
docs-guard: FAILED
guard exit: 1
```

(Full run: 6 `[BROKEN]` required bindings, 2 `[STALE_ADVISORY]`, 6 `fail: broken-binding` findings.)

### The bounded edit

Target document only — `harness/skills/gate-model/SKILL.md`. No other skill touched, no unrelated
prose fixed, no uncovered document expanded into.

Both REQUIRED COVERAGE items landed:

a. The deny-domain prose. The old text called `path_deny_globs` "these" for the three constitution
   trees only. It now states that the list carries **three domains**, and adds a section naming
   `*.env` / `**/*.env` (secret) and `docs/.docs-review-ledger.toml` (the review ledger) — the
   latter as the disjoint third domain, the docs plane's greenness authority, with the explicit
   fact that **no token** legitimizes an agent-authored disposition and that
   `docs/doc-dependencies.toml` is deliberately NOT denied.
b. The hook table gained `ledger_guard`, recorded as blocking the write at PreToolUse and honouring
   **neither** `GOLDEN_APPROVE_HUMAN` **nor** `HARNESS_DEV_BYPASS` — unlike `contract_guard`, which
   the same table shows with its token.

One further line inside the same document: "Reasoning from a block" step 1 previously routed only
contracts/adr/golden, so it would have sent an operator blocked on the ledger toward the
constitution remedy (reach for a token) — the exact wrong answer the third domain exists to
prevent. Corrected in place; still inside the binding's target.

Acceptance:

```
$ grep -c 'ledger_guard' harness/skills/gate-model/SKILL.md   -> 1
$ grep -c '\*\.env'      harness/skills/gate-model/SKILL.md   -> 2
```

### Observation point 2 — guard AFTER the edit

```
  [BROKEN] gate-model-permission-surface
    sources      : harness/permission-matrix.json, tools/harness_perms/resolver.py@c314791d60fe
    impact       : (none)
    target       : harness/skills/gate-model/SKILL.md@8df85e6ef8c0
    severity     : required
    dispositions : updated, reviewed-no-change
    reviewed     : (no reviewed row)
    reason       : binding gate-model-permission-surface is required but has no [[reviewed]] row in the ledger

guard exit: 1
```

**The target digest moved `4568f3a971ba` → `8df85e6ef8c0`: the edit is visible to the gate.** The
binding state did NOT become `STALE_REQUIRED` with a `stale-digest` reason. That is not a defect —
it is arithmetic: `stale-digest` is emitted by `check_coherence` only for a row that EXISTS in the
ledger and whose stored digests disagree with the live ones. With no ledger, the binding is
`BROKEN` for the strictly prior reason "no `[[reviewed]]` row", both before and after. Reported as
deviation D-2 rather than forced.

### Emit + snapshot

```
$ uv run python -m tools.harness_emit
harness-emit: 100 artifact(s) emitted to .opencode/ + .claude/ + opencode.json
$ git status --porcelain
 M .claude/skills/gate-model/SKILL.md
 M .opencode/skill/gate-model/SKILL.md
 M harness/skills/gate-model/SKILL.md
```

Exactly the two gate-model twins moved. `git status --porcelain` (untracked-visible) was used, not
bare `git diff`. **Second emit was a byte no-op** — identical porcelain, no fourth path.

`uv run pytest tools/harness_emit -q` failed RED first on
`test_projected_tree_matches_committed_snapshot` (the emit-determinism syrupy snapshot, showing the
gate-model prose delta verbatim); regenerated with `--snapshot-update`; re-run **47 passed**.
`uv run pytest tools/harness_lint -q` → **316 passed** (skill body/description caps still hold).
`uv run pytest tools/docs_guard -q` → **231 passed**.

`git diff --check` reports trailing whitespace inside the `.ambr` — a pre-existing syrupy
generator artifact (980 such lines already committed at HEAD, 983 after), not new hygiene debt and
not in any hand-authored file.

### Commit

`af9739b` — `docs(29-04): correct gate-model path_deny_globs + hook-surface prose`, staged by
explicit pathspec over the four files, `git diff --cached --name-only` inspected before committing.
No `git add -A`/`.`/`-a`. No file deletions in the commit. Working tree clean afterwards. The
message states that docs-guard is RED at this commit by design.

---

## Task 4 — DISCHARGED-VIA-OPTION-A (closed 2026-07-22 at phase-29 re-verification)

Not attempted by the agent session (`checkpoint:human-verify`, `gate="blocking-human"`).

**Disposition: discharged in outcome, not in letter.** Task 4's `done` condition was written as "a
human has *replaced* the `gate-model-permission-surface` row" — that wording presumes **Option B**
below. The human took **Option A**: all eight bindings were seeded in one authoring round
(`c32c08d`), so no row was ever replaced and no `updated` disposition exists. The ledger header
states why an `updated` disposition would have been wrong in a first-ever ledger — `first_seen-
unratified` compares against the *previous committed* ledger, and there was none.

The governing contract is **SC-3**, and SC-3 holds: `uv run python -m tools.docs_guard` exits 0 with
8/8 bindings FRESH, `uncovered_max = 7`. Phase-29 re-verification additionally observed the drive
loop moving green → red → green for real, in a throwaway worktree, which is the substance Option B
was intended to buy. Closed on that basis; Task 2 was already cleanly discharged.

---

## What the human must do, in order

The task-3 edit is already committed (`af9739b`), so **you author against the POST-edit tree**. The
plan assumed the opposite order. Concretely: the digest you sign for
`gate-model-permission-surface` must be `8df85e6e…` (post-edit), not `4568f3a9…` (pre-edit) — with
the one exception of Option B round one, where the pre-edit value is signed *deliberately* in order
to make the gate say `stale-digest` out loud. Every other row's digests are unaffected by the edit.

### Option A — one authoring round (fastest; SC-3 green)

1. Review each of the eight bindings in `docs/doc-dependencies.toml` and satisfy yourself that each
   target document is current with respect to its named sources. **This is the review** — the
   digests only record that you did it. For `gate-model-permission-surface`, that review is
   `git show af9739b -- harness/skills/gate-model/SKILL.md` against
   `harness/permission-matrix.json`.
2. Create `docs/.docs-review-ledger.toml` yourself, outside the agent session, with the POST-edit
   block above. Adjust anything you disagree with — your row, your call.
3. `uv run python -m tools.docs_guard` → expect exit 0 and `docs-guard: OK`.
4. `git add docs/.docs-review-ledger.toml`; inspect `git diff --cached --name-only`; then
   `git commit -- docs/.docs-review-ledger.toml`.

Cost: the loop's `0 → 1` leg is never expressed as a ledger state. The `1 → 0` leg is.

### Option B — two rounds (preserves the plan's observed transition)

1. Review as in A1.
2. Create the ledger with the **PRE-edit** `gate-model-permission-surface` target digest
   `4568f3a971ba78fba60dc5b021b6a34e12c6c7280e00f3ac3ce01573641d85cc`, disposition
   `reviewed-no-change`; all seven other rows exactly as in the block above.
3. `uv run python -m tools.docs_guard` → expect **exit 1** with
   `stale-digest` on `gate-model-permission-surface` and every other binding FRESH. This is the
   loop's `0 → 1` leg, observed for real. Commit it (`git commit -- docs/.docs-review-ledger.toml`,
   index inspected first) — a ledger that is RED by design for exactly one commit.
4. Read `git show af9739b -- harness/skills/gate-model/SKILL.md` and confirm the prose now matches
   `harness/permission-matrix.json`. **This is the second review.**
5. Replace that one row with the `updated` row given above (target `8df85e6e…`).
6. `uv run python -m tools.docs_guard` → expect **exit 0**. Commit with an explicit pathspec.

Option B is what the plan intended and gives a genuine `updated` disposition verified against a
previous committed ledger. Option A gets to green in one pass. Either way both ledger writes —
or the single one — are yours.

### If a digest is rejected

Re-run task 1 (`classify(registry_path=…)`) rather than hand-editing a value. A hand-computed digest
that disagrees with the gate is exactly the failure T-29-16 exists to prevent.

---

## Deviations from Plan

**D-1 [Rule 3 — blocking issue, resolved by reading shipped code] `_ROW_KEYS` has no
`binding_digest`, and the `<external_dependency>` STOP was correctly NOT taken.**
- Found during: task 1, before any other work.
- Issue: the plan instructs "if the fix has not landed, STOP". `binding_digest` is absent.
- Resolution: `28-FIXES.md` shows CR-03 *did* land (`2b504a6`) and deliberately rejected the
  `binding_digest` column in favour of an `identity_digest` + previous-committed-registry
  comparison, precisely to spare the human a third hand-computed value. The shipped 4-key shape is
  the post-fix shape, so the dependency's purpose is met. The plan's prose was stale, not the code.
- Files modified: none.

**D-2 [reported, not forced] `stale-digest` was not observable, because the ledger does not exist
yet.**
- Found during: task 3, observation point 2.
- Issue: the plan's task 3 step 1 expects `FRESH, exit 0 — the state after task 2`. Task 2 has not
  happened (it is human-only and this agent session cannot perform it), so the binding is `BROKEN`
  before AND after the edit, for the prior reason "no `[[reviewed]]` row". Exit is 1 in both
  states.
- Resolution: reported rather than forced. The plan says "If it does not, the loop is not being
  exercised and the discrepancy is the finding — report it rather than forcing the outcome." The
  edit's visibility to the gate was instead evidenced by the live target digest moving
  `4568f3a9… → 8df85e6e…`, derived from `classify` both times. **No simulated ledger was written
  anywhere** — not in the repo and not in a scratch directory — because a scratch ledger with
  hand-chosen digests is the drafting the prohibition covers in spirit, and observing one reason
  string is not worth blurring that line.
- Consequence for SC-3: the literal `0 → 1 → 0` transition requires the human to take **Option B**
  above. Under Option A only `1 → 0` is observed. This is a sequencing artifact of executing task 3
  before task 2, and it is the phase verifier's call which is sufficient.
- Files modified: none.

**D-3 [Rule 2 — missing critical correctness, in-scope] one extra line in the same target
document.** "Reasoning from a block" step 1 routed only the constitution domain, which would send
an operator blocked by `ledger_guard` toward `GOLDEN_APPROVE_HUMAN` — the one remedy that must
never apply there. Corrected inside the binding's own target document; no scope expansion.

## Scope respected

Not touched: `contracts/`, `docs/adr/`, `golden/`, `docs/doc-dependencies.toml`,
`.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md` (29-05 owns those).
No model identifier in any committed artifact. No wall-clock or human identity. No destructive git
(`git clean`, `git stash`, `git reset --hard`, blanket restore) was run.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern, or schema change was introduced;
the only edit is prose in one skill document plus its two derived twins and a snapshot.

## Self-Check

- `harness/skills/gate-model/SKILL.md` — FOUND (modified)
- `.opencode/skill/gate-model/SKILL.md` — FOUND (modified)
- `.claude/skills/gate-model/SKILL.md` — FOUND (modified)
- `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` — FOUND (modified)
- `docs/.docs-review-ledger.toml` — **ABSENT, as required**
- commit `af9739b` — FOUND in `git log`

## Self-Check: PASSED
