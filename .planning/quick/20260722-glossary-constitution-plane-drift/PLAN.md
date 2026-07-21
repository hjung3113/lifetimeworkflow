---
quick_id: 260722-1iq
slug: glossary-constitution-plane-drift
date: 2026-07-22
status: in-progress
---

# Quick: repair the constitution-plane enforcement drift for `docs/glossary.md`

## Problem

`docs/adr/0001-walking-skeleton-golden-core.md:48` — **accepted, unsuperseded** — declares the
constitution plane as `contracts/`, `golden/`, `docs/adr/`, **`docs/glossary.md`**. The Phase-4
enforcement stack shipped with only three of the four. Verified live:

```
contracts/x.schema.json  -> DENY
docs/adr/0001-x.md       -> DENY
golden/x.verified        -> DENY
docs/glossary.md         -> ALLOW      <-- drift
```

This is **enforcement drift from an existing accepted decision**, not stale prose. The repair
direction is to bring enforcement UP to ADR-0001; ADR-0001 is never edited (append-only — removing
the glossary from the plane would require a superseding ADR).

Two smaller corrections ride along, both found in the same binding audit.

## How it was decided

Two Claude audits recommended the OPPOSITE (delete the glossary from `.memory/README.md`'s plane
table, i.e. treat the hook as authoritative). That recommendation was **wrong**: it cited ADR-0010,
which is still `Status: proposed`, over ADR-0001, which is `accepted`. An external audit (codex sol,
medium) caught the inversion and supplied the governing principle:

> **Constitution ownership and review obligation are ORTHOGONAL.** Constitution status controls
> *who may edit* a document. A review binding controls *when a human owes a review*. A
> constitution-plane file can legitimately carry a review binding — `contract-graph-adr-0009`
> already does exactly that, with a `docs/adr/**` target.

The implementation plan is `TERRA-PLAN.md` in this directory (codex terra, medium).

## Scope

- **(A)** Align enforcement + config + explanatory surfaces with ADR-0001 (add the literal
  `docs/glossary.md`, never a broad `docs/**`).
- **(B)** `docs/explanation/template-and-instances.md:64-69` says the GEN-04 guard has one sanctioned
  exception (`root`); the guard exempts three key classes (`root|persona|test_paths`). Document-only
  fix — see Resolved below.
- **(C)** `docs/doc-dependencies.toml` `lifecycle-eval-shadow-metrics`: add
  `tools/risk_router/router.py` to `sources`. Its target defines `lane_override`, which has zero
  occurrence in the currently-bound `tools/lifecycle_eval/runner.py`, but `router.py:203` genuinely
  defines human-override validation, audit preservation and policy hashes. Keep the metric row.

## Measured before starting

| Check | Value |
|---|---|
| `uv run pytest -q` | 1480 passed, 8 snapshots |
| `uv run python -m tools.docs_guard` | **exit 1** — 6 × broken-binding, 2 × STALE_ADVISORY |
| `exclusion_reason("docs/glossary.md")` | `None` |
| `guard.classify()` uncovered live / findings | 7 / 6 |

Simulated the highest-risk interaction (append the glossary to `CONSTITUTION_GLOBS` in-process):
uncovered **7 → 7**, findings **6 → 6**, `exclusion_reason` `None` → `constitution-plane`. Corpus
membership and drafting exclusion are distinct; the ratchets do not move. This is the one thing that
could have silently broken the docs gate, and it does not.

> Corrects TERRA-PLAN §3, which predicted `docs_guard` exit 0 at baseline. It is exit 1. The plan
> hedged that cell ("must be checked against the actual CLI behavior before claiming an exit code")
> and the hedge earned its place.

## Resolved before starting (TERRA-PLAN §8 Q4)

`tools/harness_lint/tests/test_core_no_example_dep.py` already carries independent positive coverage
for all three exempted key classes — `:185` root, `:191` persona, `:200` test_paths. **(B) is a
documentation-only correction; no test is added.** Adding one would assert a runtime defect that
does not exist.

## Execution order

RED tests first, then A → B → C. Each step its own commit, staged by explicit pathspec
(`git commit -- <paths>`) with `git diff --cached --name-only` inspected first — the shared index
sweeps everything otherwise, which is how plan 28-01's file set landed in a sibling's commit.

1. **RED** — author the adversarial rows and run them against unfixed code; each must fail for its
   stated reason.
2. **A** — `contract_guard.CONSTITUTION_GLOBS`, `harness/permission-matrix.json`,
   `.github/CODEOWNERS`, `AGENTS.md`, `harness/skills/gate-model/SKILL.md`, `.memory/README.md`
   (`:29-31` only — the plane table at `:13` is correct and stays), then re-emit both runtime trees.
3. **B** — `docs/explanation/template-and-instances.md` prose only.
4. **C** — `docs/doc-dependencies.toml` sources.

## Out of scope / must not touch

- `docs/adr/0001-*.md` — accepted authority.
- `docs/adr/0010-*.md` — still `proposed`; ratifying it is the human's, and it comes AFTER this task.
- `docs/.docs-review-ledger.toml` — must not exist when this task ends. Human-authored only;
  `ledger_guard` denies the write under **every** token.
- `tools/docs_guard/guard.py` `HUMAN_CORPUS` and the `uncovered_max` / `binding_min` ratchets — not
  the defect, and must never be used to force green.
- `.claude/**` / `.opencode/**` emitted copies — regenerate via `tools.harness_emit`, never by hand.

## Done when

- The four-member plane is enforced, and each member's denial is pinned by a test that goes red when
  that member alone is deleted.
- `uv run pytest -q`, `contract_drift.drift`, `harness_emit` round-trip and `tools/harness_lint` are
  green; `docs_guard` still exits 1 for the designed pre-ratification reason (no ledger) and for no
  other reason.
- The human can then ratify ADR-0010 and author the first ledger against final digests.
