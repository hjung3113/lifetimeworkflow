# 2. General Template De-specialization

*MADR 4.x · plane: constitution (human-owned, immutable, append-only)*

- **Status:** accepted
- **Date:** 2026-07-09
- **Deciders:** Phase 5 planning (De-specialization & Template Extraction, GEN-01..04)
- **Supersedes:** —
- **Superseded by:** —
- **Complements:** [ADR-0001](0001-walking-skeleton-golden-core.md) (walking-skeleton golden core) — **not** superseded.

## Context and Problem Statement

ADR-0001 locked a walking-skeleton golden core for a **log-parser-specific** harness: the
semiconductor equipment-log domain (log-spec contracts, correction rules, equipment master, the toy
converter, the .NET normalize twin, the domain goldens) sat at the repo root, intermixed with the
domain-neutral machinery that makes a polyglot pipeline safe (contract-first schemas, the §4.3–4.6
normalization boundary, golden equivalence, the drift/commit gates, two-plane memory).

That machinery is reusable across *any* contract-first polyglot pipeline, but the intermixing made
the repo cloneable only *as a semiconductor log parser*. The problem this ADR records: *how do we
re-scope the repo into a reusable template — a domain-neutral core plus swappable instances — while
keeping every contract / §4.3–4.6 / gate invariant from ADR-0001 intact and enforced?*

## Decision Drivers

- The core machinery is domain-agnostic; a downstream user should clone it for a *different* domain
  without dragging semiconductor specifics along.
- The re-scope must be **enforced, not merely documented** — a core file must not silently grow a
  dependency on a domain instance.
- ADR-0001's guarantees (real A-model boundary, representation-only PASS / real-regression FAIL,
  schema-drift gate, "machines gate, humans ratify") must survive the move unchanged.
- Normalization spans the language boundary; the split of what stays vs moves must be principled
  ("core is language-neutral"), not incidental to packaging.
- An intentional constitution-plane change must land through the *live* gates, not around them.

## Considered Options

1. **Leave it log-parser-specific.** *Rejected:* forecloses reuse; the harness value (the gates and
   the normalization boundary) is generic and wasted if welded to one domain.
2. **Fork a separate generic repo, hand-copying the core.** *Rejected:* two divergent copies, no
   enforced boundary, drift between "the template" and "the instance" guaranteed over time.
3. **In-place de-specialization (chosen).** Demote the domain to `examples/log-parser/`, keep the
   domain-neutral core at the root, and *enforce* the one-directional core→instance dependency with
   a guard test — one repo, one history (history-preserving `git mv`), an enforced invariant.

## Decision Outcome

**Chosen: Option 3 — in-place de-specialization**, with these locked decisions:

**(a) Generic re-scope + domain demotion.** The repo is re-scoped from a log-parser-specific harness
to a **reusable contract-first polyglot agent-harness template**. The semiconductor domain seed is
**demoted to a reference instance** under `examples/log-parser/` (its own `contracts/`, `golden/`,
`components/`, language-side normalize twin, `tests/`, and contract manifest), moved
history-preservingly (GEN-01, 05-03). The root holds the domain-neutral core (`contracts/` generic
default, `libs/python` normalize core + `libs/normalize-{spec.md,fixtures}`, `tools/`, `harness/`,
`docs/`, the gates). The **one-directional invariant** — nothing under `tools/`, `harness/`, `libs/`
imports or path-references `examples/**` — is enforced by the GEN-04 guard
`tools/harness_lint/tests/test_core_no_example_dep.py`, with a live negative-control proving the scan
cannot silently no-op.

**(b) The normalize split — the precise rationale.** Normalization is deliberately split across the
core/instance boundary:

- **`libs/python/normalize` + `libs/normalize-fixtures` STAY in the core** because they are the
  harness's own **language-neutral** §4.3–4.6 tooling: the Python impl is a **uv workspace member
  imported by core tools** (`polyglot_lint`, `golden_runner`), and the shared `(raw, canonical)`
  fixture corpus cross-validates *any* language-side twin. The canonical rule spec
  (`libs/normalize-spec.md`) stays with them.
- **`libs/dotnet/Normalize*` MOVES to `examples/log-parser/`** because it is the **example's
  language-side implementation**: no core Python tool imports it, and "**core is language-neutral**"
  forbids a specific-language (.NET) implementation in the core. It is not a uv member — but that is
  a *consequence* of it being instance-specific, **not** the reason it moves. The reason is
  language-neutrality of the core; the invalid "uv/GEN-04 packaging" rationale is explicitly **not**
  recorded here.

**(c) Language/toolchain config slot.** The core hardcodes no language. The active instance declares
its toolchains as **data** in `harness/project.toml` (`[instance]` root + `[[languages]]`). The
log-parser instance supplies **.NET 10** (parser/converter, CPU-bound) + **Python/uv**
(scheduler/collector). A downstream consumer swaps the instance + this slot; the GEN-03 consistency
test keeps the permission matrix and personas in agreement with it.

**(d) Commit-gate approval path.** This ADR and its index row are constitution-plane writes
(`docs/adr/**`); `contract_guard` denies them unless the **human-set** `GOLDEN_APPROVE_HUMAN` token
is present in the process env. That token is the **canonical, drift-only** route to land an
intentional constitution change through the *live* gates — consistent with contract-guard, requiring
a non-empty/non-blank human-set value, and **never** `--no-verify` or a bash bypass. The §4.3–4.6
polyglot and golden gates stay hard even when the token is set (only schema-drift is approvable).

### Consequences

- **Good:** the repo is cloneable as a domain-neutral template; the core→instance boundary is
  tamper-evident on every test run; ADR-0001's guarantees survive the move; one repo, one history.
- **Good:** adding a new domain is a documented, bounded operation (`examples/<name>/` + a manifest +
  a `harness/project.toml` language set) — see `docs/explanation/template-and-instances.md`.
- **Neutral:** the language-neutral core keeps a Python normalize impl (the reference twin); this is
  harness tooling, not a domain choice — instances supply their own language-side twins.
- **Bad / accepted:** the demotion touches live drift/contract-guard gates, so the move requires a
  deliberate ADR + manifest re-baseline landed through the human approval path (this ADR is that
  record); the .NET side stays egress-deferred (BOOT-01), proven via the recorded-output twin.

## Links

- Complements [ADR-0001](0001-walking-skeleton-golden-core.md) — walking-skeleton golden core (not superseded).
- Narrative: `docs/explanation/template-and-instances.md`. Reference instance: `examples/log-parser/{README.md,AGENTS.md}`.
- Enforced by: `tools/harness_lint/tests/test_core_no_example_dep.py` (GEN-04 guard). Language slot: `harness/project.toml` (GEN-03).
- Sources: `.planning/phases/05-despecialization/{05-CONTEXT.md (D-06), 05-RESEARCH.md (Q3/Q6), 05-05-PLAN.md}`.
