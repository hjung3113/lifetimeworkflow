---
name: gate-model
description: >-
  Use when a write is blocked or you need to reason about what is gated and why — maps the
  constitution plane, the machines-gate/humans-ratify rule, the exit-3 refusals, the hook surface,
  and the path denies. Consult when an edit to contracts/adr/golden/glossary is refused or a golden won't self-promote.
---

# gate-model

Why the harness stops you, as a map instead of a surprise. Every gate here exists to keep one
invariant true: **machines gate, humans ratify.** An agent may propose a change to the
single-source-of-truth planes, but only a human ratifies it. When a write is refused, find it below
to know the reason and the sanctioned path forward.

## The constitution plane (human-owned, path-denied)

Four members are the single source of truth and are **not agent-writable** — three trees and one
file, declared by [ADR-0001](../../../docs/adr/0001-walking-skeleton-golden-core.md) §Decision:

- `contracts/**` — the contract schemas + instances (single source of truth for shapes/conventions).
- `docs/adr/**` — Architecture Decision Records (append-only; supersede, never edit).
- `golden/**` — the human-approved equivalence baselines.
- `docs/glossary.md` — the ubiquitous-language definitions. A **single file**, not the `docs/` tree:
  the rest of `docs/` is agent-writable human prose.

These four are the CONSTITUTION entries in `path_deny_globs` in
`harness/permission-matrix.json` (pure data; the resolver in `tools/harness_perms` enforces them, and
the Phase-4 hooks import that resolver verbatim). opencode's native `edit` key is not path-globbable,
so the path denies live here as data. The ADR declares the membership and this data implements it —
adding or dropping a member needs a **superseding ADR**, not an edit to the matrix.

> **Gated ≠ unwatched.** A constitution member can also carry a doc-review binding: ownership
> controls *who may edit*, a binding controls *when a human owes a review*. `docs/glossary.md` and
> `docs/adr/0009-*` are both gated **and** review-bound. The two are orthogonal, not contradictory.

## The other two deny domains (disjoint from the constitution plane)

`path_deny_globs` carries three domains, not one, and conflating them teaches the wrong remedy:

- **secret** — `*.env` and `**/*.env`. Environment files never enter the tree; the remedy is to move
  the value out of the repo, not to reach for a token. Enforced on content as well by `secret_scan`.
- **review ledger** — `docs/.docs-review-ledger.toml`. This is the docs plane's **greenness
  authority**: a `[[reviewed]]` row is what makes a doc-dependency binding FRESH, so only a HUMAN may
  author a review disposition, directly and outside an agent session. **No token legitimizes an
  agent-authored one** — `GOLDEN_APPROVE_HUMAN` authorizes constitution writes and does not apply
  here, and none should be invented. Agents may instead propose rows in `docs/doc-dependencies.toml`,
  which is deliberately NOT denied: that changes what is WATCHED, never what is GREEN (ADR-0010
  clause 3b).

## The hook surface (in-session enforcement)

| Hook (`tools/hooks/…`) | Gates | Effect |
|---|---|---|
| `contract_guard` | writes to the constitution plane | blocks the write (PreToolUse), unless a human `GOLDEN_APPROVE_HUMAN` token is set |
| `ledger_guard` | writes to `docs/.docs-review-ledger.toml` | blocks the write (PreToolUse), honouring **neither** `GOLDEN_APPROVE_HUMAN` **nor** `HARNESS_DEV_BYPASS` — unlike `contract_guard`, this domain has no opt-out at all |
| `secret_scan` | writes whose content matches a secret pattern | blocks the write |
| `polyglot_lint` (POLY-01) | `*.tsv` wire files breaching §4.3–4.6 | fails loud (on-write + `/lint` + commit-gate — one engine, three sites) |
| `commit_gate` | a commit while contract-drift / golden / polyglot is red | blocks (exit 2 from the hook wrapper), unless ratified by the token |
| `format_on_write` | style/format drift | auto-fixes on write |

## Exit-3 refusals (proposals a human must ratify)

Two tools **refuse** rather than proceed when an agent tries to self-bless:

- `tools/golden_runner/approve.py` (`/golden-approve`) — refuses (exit 3) without an explicit human
  `--approve` + `--adr <id>` + token. Promoting `.received` → `.verified` is a human act.
- `tools/strangler_guard` — refuses to advance a strangler step without its required baseline.

## The ratification token

`GOLDEN_APPROVE_HUMAN` is the human-set escape hatch: a non-empty value in the environment (set by a
human in a gitignored `.claude/settings.local.json`, removed after) turns a constitution-plane
`FAIL` into a ratified `WARN`. An agent must never set it. Its presence is what distinguishes
"machine tried to write the plane" (blocked) from "human ratified this write" (allowed).

## Reasoning from a block

1. **Which plane?** contracts/adr/golden → constitution, path-denied, needs human ratification.
   `docs/.docs-review-ledger.toml` → the review ledger, path-denied with no token path at all; the
   human writes it themselves. `*.env` → secret; remove the value.
2. **Which signal?** drift hash moved → pair a golden update + ADR; golden red → use `golden-debug`;
   secret hit → remove the secret; polyglot red → fix the §4.3–4.6 violation.
3. **Is a token involved?** If a write "should" be allowed, it is because a human set
   `GOLDEN_APPROVE_HUMAN` — not because the agent may self-approve.

## Related
- `harness/skills/two-plane-memory/SKILL.md` — the plane the gates protect vs the derived plane.
- `harness/skills/golden-testing/SKILL.md` + `golden-debug` — the golden promotion + red-golden path.
