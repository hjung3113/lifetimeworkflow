# 5. Golden Comparator Is Structural-Only Pending Column-Aware Canonicalization

*MADR 4.x · plane: constitution (human-owned, immutable, append-only)*

- **Status:** accepted
- **Date:** 2026-07-14
- **Deciders:** full-harness audit (findings H2, M1, L1, L2), operator-delegated decision
- **Supersedes:** —
- **Superseded by:** —
- **Complements:** [ADR-0001](0001-walking-skeleton-golden-core.md) (walking-skeleton golden core) — scopes the compare step it introduced; [ADR-0002](0002-general-template-de-specialization.md) (core is domain-neutral) — the reason the core comparator cannot know column kinds.

## Context and Problem Statement

The harness's headline promise is that it **automatically absorbs polyglot representation differences**
(decimal locale, timezone, float last-digit, CRLF, BOM, row order — the §4.3-4.6 / normalize-spec
rules) so a golden comparison catches **value** regressions, not representation noise. The golden
comparator (`tools/golden_runner/runner.py::compare`) is where that promise is meant to be delivered.

The full-harness audit found the comparator only partially delivers it:

- **H2** — `compare()` normalizes both sides with `libs/python/normalize/core.py::normalize_tsv`, which
  applies only **R1 (BOM strip) + R2 (LF) + R8 (row sort)** — structural rules. It never splits rows
  into cells, so the **cell-level** rules **R3 (decimal/InvariantCulture) and R5 (datetime→UTC)** are
  never applied at compare time. `normalize_cell` / `_norm_decimal` / `_norm_datetime` exist and are
  unit-tested, but are **dead relative to the compare path** (exercised only by the corpus-parity test).
- **M1** — `contracts/normalization/format-conventions.schema.json` declares `float_compare.mode =
  "tolerance"`, `tolerance = 1e-9`, and `libs/normalize-spec.md` (R4) says the tolerance "applies at
  **compare time** in the golden runner." No tolerance-aware numeric compare exists anywhere; the
  runner compares with string `==`. The declared knob is wired to nothing.
- **L1 / L2** — the same root: the R3/R5 lint rules are never invoked with real column `kinds`; and
  `_norm_datetime` emits second precision (contract-conformant, latent masking risk).

The load-bearing constraint that shapes the fix: **the core is domain-neutral (ADR-0002).** The core
comparator cannot know which column is a decimal/datetime/float — the per-column **kinds** live in the
**instance** overlay (`examples/log-parser/contracts/log-specs/standard-log.spec.yaml`), never under
the GEN-04-scanned core roots. So "make the comparator canonicalize cells" is not a one-line patch —
it requires a **column-kind source** the comparator can read, plus (because it changes what compares
equal) **golden re-approval**. That is an architecture decision, not a bug-fix.

Compounding the timing: there is **no live .NET converter** in this environment (BOOT-01: the .NET 10
SDK install is egress-denied), and the shipped default is the byte-identical `identity` converter. So
today **no case actually emits a non-canonical decimal/datetime cell** — the gap is **latent**: the
current goldens pass, but the day a real .NET converter emits `1,5` or `+09:00`, the comparator would
false-RED an equivalent value (or mask a representation-differing regression).

## Decision Drivers

- **Deliver the Core Value, but don't build ahead of a consumer.** Column-aware compare is only
  *exercised* once a real converter emits non-canonical cells — which needs BOOT-01 resolved. Building
  it now would ship an unexercised, unverifiable code path and force a speculative golden re-baseline.
- **The spec already points at the target.** `normalize-spec.md` R4 says tolerance applies *at compare
  time* — so the eventual direction is a **column-aware comparator** (not "producer canonicalizes,
  comparator stays structural forever"). This ADR records that direction, it does not reverse it.
- **Latent ≠ ignored.** A silent partial no-op in the flagship feature must become an explicit,
  time-boxed decision so a future maintainer wiring .NET is not surprised.
- **Machines gate, humans ratify.** Changing compare semantics shifts golden baselines → the
  `/golden-approve` human gate. That work belongs in a planned phase with a human in the loop, not an
  opportunistic patch.

## Considered Options

1. **Implement the column-aware comparator now (findings H2+M1, "direction A").** *Rejected for now:*
   no live converter exercises it (BOOT-01), so it would be unverified code + a speculative golden
   re-baseline. Correct direction, wrong time.
2. **Declare cell canonicalization the producer's job forever; comparator stays structural (option B).**
   *Rejected:* contradicts `normalize-spec.md` R4 ("tolerance at compare time") and the
   `format-conventions` contract's declared tolerance knob — it would demote a stated contract to a
   no-op and push the burden onto every future converter.
3. **Record the scope + defer implementation to when a real converter lands (chosen).** The comparator
   is **structural-only for now** (R1/R2/R8), by ratified decision; the column-aware extension
   (R3/R5 + tolerance at compare time) is the **committed direction**, scheduled for when a real .NET
   converter is wired (BOOT-01 unblocked) and can exercise + re-baseline it.

## Decision Outcome

**Chosen: Option 3.** The golden comparator's compare-time normalization is **intentionally
structural-only (R1 BOM / R2 LF / R8 row-order) for the current template state**, and the audit's
H2 / M1 / L1 findings are **accepted, deferred** — NOT silently closed:

**(a) Scope recorded.** `compare()` neutralizes only representation differences that are
column-kind-independent. Cell-level decimal (R3) / datetime (R5) canonicalization and tolerance-aware
float compare (R4) are **not applied at compare time today.** `normalize_cell` and its helpers remain
in the core as **tested primitives** (usable by an instance's converter/tests), not as compare-path
logic.

**(b) Committed direction = column-aware comparator ("A").** When a real .NET converter is wired
(BOOT-01 resolved), a planned phase (`/gsd:plan-phase`) will: add a per-case **column-kind source**
(e.g. `golden/<case>/meta.yaml` gains a `columns: [{name, kind}]` field, or the runner reads the
instance column contract), have `compare()` apply `normalize_cell` per kind + implement the declared
`tolerance` numeric compare, and **re-approve** the affected goldens via `/golden-approve`.

**(c) Trigger + owner.** The trigger is "a converter that emits non-canonical decimal/datetime/float
cells" (in practice: BOOT-01 unblocked + a real converter). Until then this is an **accepted, documented
limitation**, tracked in `.planning/AUDIT-FINDINGS.md` (H2/M1) and here.

**(d) No spec reversal.** `normalize-spec.md` R4's "tolerance at compare time" stays as the **target**
statement; this ADR records that it is **not yet implemented**, with the implementation deferred per
(b) — rather than editing the spec to match today's partial state.

### Consequences

- **Good:** the flagship feature's real state is explicit and time-boxed; no unexercised
  column-aware code ships ahead of a converter that would exercise it; the eventual golden re-baseline
  happens once, with real data, under the human gate.
- **Good:** the audit's most significant finding is neither silently patched nor silently ignored —
  it is a ratified, referenced decision.
- **Neutral / accepted:** while structural-only, a converter emitting a non-canonical decimal/datetime
  cell would false-RED an equivalent value (or mask a representation-differing regression). This is
  acceptable **only** because the shipped `identity` converter emits byte-identical output and no live
  .NET converter exists (BOOT-01); the limitation is bounded to that window.
- **Bad / accepted:** the declared `format-conventions` `tolerance` knob is inert until (b) lands —
  documented here so it is not mistaken for a working guarantee.

## Links

- Audit findings (H2, M1, L1, L2) + dispositions: `.planning/AUDIT-FINDINGS.md`.
- Compare path: `tools/golden_runner/runner.py::compare`; structural core:
  `libs/python/normalize/core.py::normalize_tsv`; unused cell primitives: `normalize_cell` /
  `_norm_decimal` / `_norm_datetime` (same file).
- Declared-but-inert knob: `contracts/normalization/format-conventions.schema.json` (`float_compare`);
  target statement: `libs/normalize-spec.md` (R3/R4/R5).
- Blocking trigger: BOOT-01 (.NET 10 SDK install egress-denied) — see `.planning/STATE.md` blockers.
- Column-kind source (instance, today): `examples/log-parser/contracts/log-specs/standard-log.spec.yaml`.
