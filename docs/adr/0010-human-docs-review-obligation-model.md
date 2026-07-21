# 10. Human-Docs Review Obligation Model: Plane Split, Agent-Authority Boundary, Digest, Disposition Coherence, and Ratchets

*MADR 4.x · plane: constitution (human-owned, immutable, append-only)*

- **Status:** accepted
- **Date:** 2026-07-22
- **Deciders:** kimhyojung (CODEOWNERS)
- **Supersedes:** —
- **Superseded by:** —
- **Complements:** [ADR-0009](0009-contract-relationship-graph-model.md) (the graph this model's impact
  ids consume), [ADR-0007](0007-constitution-gate-dev-enforce-decoupling.md) (the constitution gate
  and its dev/enforce decoupling, whose token semantics this record deliberately does NOT extend),
  [ADR-0002](0002-general-template-de-specialization.md) (core/instance one-directional invariant)

## Context and Problem Statement

Derived documentation (`docs/reference/**`, `.memory/derived/**`) regenerates and is gated by
`stale-derived`. **Human-authored** documentation — tutorials, how-tos, explanations, the glossary,
the skills that teach an operator why a write was refused, and the ADRs themselves — has no
generator and therefore no such gate. It drifts silently: a module is renamed, a flag changes, a
disposition enum grows, and the prose that describes it stays green forever because nothing is
watching.

The harness needed a gate that detects **human-doc review obligations** precisely, with three
properties that are in tension:

1. It must be **agent-extensible** — a brownfield `/adopt` run (DOCSUP-07, Phase 29) has to be able
   to PROPOSE new source→doc bindings, or the registry never grows past what a human hand-seeds.
2. It must be **unfalsifiable by the agent that extends it** — if the same actor that proposes a
   binding can also declare it reviewed, the gate reports green by construction and teaches
   rubber-stamping, which is worse than no gate at all.
3. It must **never claim more than it knows**. It compares digests. It cannot read prose. A gate
   that reads as "the documentation is correct" manufactures false assurance.

Those three, plus the exit-code and state vocabulary Phase 29's `/docs-update` binds to, form a
single surface. Because ADRs here are **append-only / supersede-don't-edit**, a partial record would
force a second full human ratification to add whatever was left out. This record therefore fixes the
whole model as ONE ratified unit (D-15), including the agent-authority boundary that Phase 29 depends
on (29-CONTEXT D-13) and would otherwise have to pay for twice.

## Decision Drivers

- Machines gate, humans ratify. A gate that can bless its own inputs is not a gate.
- `tools/hooks/contract_guard.py:44` denies agent writes under `contracts/**` — any placement
  decision that puts an agent-extensible artifact there is unimplementable downstream.
- `GOLDEN_APPROVE_HUMAN` authorizes **constitution** writes. Nothing may be built that could teach an
  operator to reach for it in order to legitimize a review disposition.
- `contract_guard.py:16-20` records a **provably-disjoint-domain** composition invariant between the
  constitution gate and secret_scan. A new deny domain must preserve it, not dilute it.
- Contract-drift and golden stay **leading and authoritative**; one change must not fail two gates
  with two different remedies (DOCSUP-05).
- Fail-closed where the evidence is unreadable, and say so in a distinguishable way — an
  indistinguishable failure teaches the wrong fix.
- Under-deliver rather than fabricate: an unmappable impact set is empty, never invented.

## Considered Options

1. **Registry under `contracts/`, as a constitution-plane artifact.** *Rejected:* `contract_guard`
   denies agent writes there, so DOCSUP-07's "`/adopt` proposes bindings" becomes implementable only
   by handing agents `GOLDEN_APPROVE_HUMAN`. The requirement and the placement are incompatible.
2. **Registry and ledger both as plain config, with no write-side control.** *Rejected:* an agent
   that lands a new `[[binding]]` together with its own matching `reviewed-no-change` row has
   performed the self-green attack; the honest seed and the attack are byte-identical.
3. **Widen `CONSTITUTION_GLOBS` to cover the ledger.** *Rejected:* it makes
   `GOLDEN_APPROVE_HUMAN` — a token that exists to authorize constitution writes — appear to
   authorize a ledger disposition, for which no legitimizing token exists or should exist. It also
   breaks the `contract_guard.py:16-20` disjoint-domain invariant.
4. **Digest-only coherence (compare the reviewed digest to the live digest).** *Rejected:* after a
   paste of the live digest the ledger is consistent by construction. Digests alone cannot see a
   claim of `updated` over an untouched document.
5. **Split planes; own deny domain for the ledger; disposition/history coherence on top of digests;
   read-only ratchets.** *Proposed.*

## Decision Outcome

Adopted as ONE ratified unit (D-15). The ten clauses below ship and are fixed together.

### 1. The plane split (D-01) — forced, not preferential

Registry **DATA** lives at `docs/doc-dependencies.toml` as plain reviewed config (the
`harness/project.toml` precedent). Registry **SHAPE** lives at
`contracts/harness/docs/doc-dependencies.schema.json` on the constitution plane, hash-gated, costing
exactly one ratification.

This split is **forced**. `contract_guard.py:44` denies agent writes under `contracts/**`, and
DOCSUP-07 requires `/adopt` to PROPOSE registry entries. A registry under `contracts/` makes the
downstream requirement unimplementable without handing agents the human token — the split is the only
shape in which both requirements hold. It mirrors the Phase 26/27 `manifest.schema.json` split.

### 2. The registry's single validator (D-16 / A7)

`/contract-check` step 1 pairs a schema with a sibling `.yaml` / `.yml` / `.json` instance. The
registry is `.toml` and lives under `docs/`, so **CI silently skips it**. `tools.docs_guard.registry`
is its **ONLY** validator: it applies the schema itself and then enforces the five DOCSUP-01 semantic
rejections the schema provably cannot express (path escape, duplicate id, empty required selector,
derived/reference target, accepted-ADR disposition policy).

Stated plainly so no later reader assumes double validation: **there is exactly one validator, and it
is not CI's generic schema step.** The schema's own description repeats this so the contract cannot
be mistaken for a complete validator.

**Selectors are constrained to exclude control characters and `|`.** The registry is agent-writable
by design, and its `target` and `sources` values are interpolated into the derived staleness queue's
markdown table — whose `"| "`-prefixed line count is what the SessionStart pointer reports as "N
human doc(s) need review". A TOML multi-line basic string permits a real newline, so an
unconstrained selector could forge queue rows and inflate that count. The constraint is stated in
the schema as a `pattern`, restated by `tools.docs_guard.registry` for an operator-facing message
(a printed regex teaches nothing), and neutralized defensively at the other end by
`tools.memory_regen.docs_staleness.render` — a renderer that can be made to emit a forged row is a
renderer bug regardless of who validated its input.

### 3. The digest algorithm (D-03) — a deliberate divergence

The binding digest **interleaves the POSIX path with that file's own hex digest**, over the sorted,
root-confined resolved set. This is deliberately **NOT** the raw-byte concatenation at
`tools/adoption_apply/approval.py:57-63`.

Reason, recorded so a future reviewer does not "fix" it back toward the precedent: concatenation is
safe only for a **fixed** file tuple. A registry selector expands to a **variable** set, and over a
variable set raw concatenation makes two real changes invisible — moving a byte from the end of one
file to the start of the next, and adding an empty file. Interleaving the path binds each digest to
its filename and to the set's cardinality, so both are detected. A four-row adversarial table proves
the divergence is load-bearing, and was RED against a throwaway implementation of the precedent
algorithm before the divergent one was written.

**No §4.3–4.6 normalization runs before hashing**, and this is intentional: the digest must agree
with what a human sees in `git diff`. A normalizing digest would call a CRLF-only change "no change"
while the reviewer's diff shows every line touched.

Two related refusals are part of the algorithm: a root escape (selector or in-tree symlink pointing
outside the repo) **raises** rather than being silently skipped — a review-obligation digest that
silently drops a file would UNDER-report staleness — and each path is hashed by its label **relative
to the root**, so a ledger digest never depends on the checkout location.

### 3b. The docs-plane agent-authority boundary — a named, first-class decision

**Agents may PROPOSE registry rows. Only a HUMAN may author a ledger disposition. The LEDGER — not
the registry — is the greenness authority.**

A proposed binding changes what is **WATCHED**. Only a ledger row changes what is **GREEN**. That
asymmetry is the whole reason the plane split of clause 1 is safe: an agent extending coverage can
only ever create obligations for itself, never discharge them.

This boundary is enforced in **three layers, and no single layer suffices**:

| Layer | Surface it covers | Why the others cannot cover it |
|-------|-------------------|-------------------------------|
| `tools/hooks/ledger_guard.py` — a PreToolUse(`Write`\|`Edit`) deny gate owning `REVIEW_LEDGER_GLOBS` and feeding it to the CONFIG-02 resolver, wired into both runtimes by `tools.harness_emit` | the ordinary agent `Write`/`Edit` tool path | a plain tool call never enters the adoption-apply module |
| `refuse_unsafe_destination` → `ReviewLedgerRefusal` (`tools/adoption_apply/apply.py`) | the adoption-apply write path, i.e. Phase 29's `/adopt` writing through a manifest | the permission matrix is not consulted inside a bare `python -m tools.adoption_apply apply` invocation |
| `first_seen-unratified` (`tools/docs_guard/ledger.py`) | the **greenness** side | a write that slips past both write-side layers still cannot produce green |

**The `path_deny_globs` matrix row is DATA, not the layer.** `harness/permission-matrix.json` still
carries `docs/.docs-review-ledger.toml`, and `tools.harness_emit.permissions` strips
`path_deny_globs` from the emitted `opencode.json` as a resolver-only key — so the matrix entry has
no enforcement of its own and never did. Every *other* entry in that list is separately re-declared
inside a hook (`contract_guard.CONSTITUTION_GLOBS`, `secret_scan.SECRET_PATH_GLOBS`), and the ledger
entry is now no exception: `tools/hooks/ledger_guard.py` is its enforcer and its single
authoritative home for `REVIEW_LEDGER_GLOBS`, which `tools/adoption_apply/apply.py` IMPORTS rather
than re-declaring. This is recorded explicitly because a layer that is only a data row is a claimed
control that does not exist — worse than a missing layer, because it reads as covered. The test that
proves layer 1 drives the hook's `decide()` and asserts a deny; a test that only re-reads the matrix
proves the file's content, not the enforcement.

`ledger_guard` honours **no** opt-out — not `GOLDEN_APPROVE_HUMAN`, and not the ADR-0007
`HARNESS_DEV_BYPASS` local-dev path. Both are constitution-plane opt-outs; the ledger is a different
domain, and a human authors a disposition outside an agent session, so there is nothing for a
session-scoped opt-out to express.

The write side uses its **OWN constant** (`REVIEW_LEDGER_GLOBS`) and its **OWN exception type**
(`ReviewLedgerRefusal`, explicitly not a subclass of `ConstitutionRefusal`) rather than widening
`CONSTITUTION_GLOBS`, for two reasons:

1. `GOLDEN_APPROVE_HUMAN` authorizes **constitution** writes. There is **no token** that legitimizes
   an agent-authored ledger disposition, and none should be invented. Folding the ledger into the
   constitution domain would teach an operator to reach for a token that must never apply here. The
   ledger is therefore **DENY**, not **ask**.
2. `contract_guard.py:16-20` documents a provably-disjoint-domain invariant between the constitution
   gate and secret_scan's `SECRET_PATH_GLOBS`. Widening would break it.

The review ledger is consequently a **THIRD path-deny domain**, alongside constitution and secret,
disjoint from both.

**Accepted cost, recorded rather than engineered around:** a genuinely new binding is **amber for
exactly one commit cycle**. `first_seen-unratified` keys on the PREVIOUS COMMITTED ledger *and on
the binding's meaning in the previous COMMITTED registry* (clause 4), so a row's first appearance —
and equally a REPOINTED binding's first appearance in its new shape — can never be green. That is
correct, because the human review commit that lands the row **IS** the ratification. The second
cycle turns it green. Any mechanism that removed this amber window would also remove the only fact
that separates an honest first seed from a self-blessed one.

### 4. Disposition coherence (D-04) — the anti-rubber-stamp control, and its closure

Two halves, both required:

- **`reviewed-no-change` is content-bound and history-free.** It is valid only against the exact live
  digest. No history is consulted, so the rule holds in a tree with no readable `HEAD`.
- **`updated` additionally requires a target-digest delta** versus the **previous COMMITTED ledger**,
  retrieved through the `git show HEAD:./<path>` shape at `tools/contract_drift/drift.py:129-147`.

The attack this defeats: paste the live digest into the ledger, claim `updated`, leave the document
untouched. Digests alone **cannot** detect it — after the paste the ledger and the tree agree by
construction. Only "did the target's digest actually MOVE since the last committed ledger?" separates
a real update from a pasted one. `disposition-incoherent` is the reason string.

**The sibling problem and its closure.** Content-binding is right for an existing binding, but it
means a **brand-new** binding landed together with a matching `reviewed-no-change` row is consistent
by construction, with nothing to contradict it. `first_seen-unratified` closes that hole: a
content-bound disposition whose id has **no PREVIOUS COMMITTED row** is not green.

This is deliberately a **HISTORY test, not a content test** — because the self-blessed row and an
honest first-ever seed row are **byte-identical**. No inspection of the row's content can tell them
apart. Only "has a human committed this row before?" can.

**The history test keys on the binding's MEANING, not on its NAME.** A ledger row records no
statement about *what* was reviewed beyond the id, so "has a human committed this row before?" is
asked of the pair `(id, the binding's committed (sources, target))`, retrieved from the previous
COMMITTED REGISTRY through the same `git show HEAD:./<path>` shape clause 4 uses for the ledger. An
id alone is not an identity: a *renamed* id is caught trivially (a new name is absent from history),
but a *REPOINTED* id — same name, different source/target pair — would otherwise carry its earlier
ratification to whatever the registry later decides that name means, and the registry is
agent-writable by design (clause 3b). **Repointing a binding is a NEW obligation**, indistinguishable
in weight from introducing one, and it is reported as `first_seen-unratified` for exactly that
reason.

Comparing against the committed REGISTRY rather than storing an identity digest IN the row is
deliberate: it keeps the ledger's clause-1 shape unchanged, so a human ratifier still hand-writes
only the two content digests and never a third derived value. A pure reordering of the `sources`
list is **not** a repoint — the identity digest sorts its selectors — so the rule cannot degrade
into "any registry edit de-ratifies everything".

At the classifier level the same closure is restated: digest equality is **necessary but not
sufficient** for `FRESH`. `FRESH` requires digest equality AND an empty blocking-finding set.

### 5. The two ratchets (D-06) — read-only, never self-lowering

Both live in the ledger's `[coverage]` table:

- **`uncovered_max`** — catches a human-authored document DRIFTING OUT of coverage.
- **`binding_min`** — catches a binding being DELETED.

**The guard NEVER writes either.** Raising `uncovered_max` or lowering `binding_min` is a human edit,
because a gate that can lower its own threshold is self-blessing. The read-only property is proven
structurally, not asserted: a public-surface allowlist, a static write scan, and a live
planted-token negative control that keeps the scan from passing vacuously.

`binding_min` is **not redundant** with `uncovered_max`, and the reason is concrete: a binding whose
target lies **outside** the clause-7 human corpus can be deleted without moving the uncovered count by
a single unit. Three of the eight seeded bindings are exactly that case (they target `harness/**` and
`docs/adr/**`). Without the second ratchet, deleting an inconvenient binding would be entirely
unguarded.

**BOTH thresholds are read from the PREVIOUS COMMITTED ledger, never the working tree** — otherwise
the same edit that deletes a binding could also lower the bar in the same breath, and the same edit
that drops a document out of coverage could raise the ceiling it is about to breach. The two
ratchets are symmetric in this respect, and deliberately so: an asymmetry here is not a smaller
version of the hole, it IS the hole, on whichever side is read from the working tree. The
working-tree value is consulted only when there is no committed ledger to read at all — with no
history there is no committed threshold, so honouring the working-tree one can only ADD a
constraint, never relax one.

### 6. The unverifiable-history posture (D-08)

When git history is unreadable, the gate **fails closed for `required`** bindings and **warns for
`advisory`** ones, with the **distinct reason string `unverified-disposition`** — never reused for
real staleness.

The distinct string is mandatory, not cosmetic: an operator who cannot tell "your doc is stale" from
"I could not read history" applies the wrong fix. Only the `updated` half can raise it; the
content-bound half stays history-free by clause 4.

### 7. The five states and the exit-code contract (D-05) — pinned

States: `BROKEN` · `STALE_REQUIRED` · `STALE_ADVISORY` · `FRESH` · `UNCOVERED`, evaluated
**first-match-wins with `BROKEN` ordered before any staleness check** — a missing file must never be
reported as merely stale.

Exit codes: **0** clean · **1** obligations outstanding · **3** registry/ledger invalid. Three is
separate because the **operator action differs**: exit 1 means review a document, exit 3 means the
registry itself does not parse or does not validate. This mirrors the `approve.py` / `StranglerRefused`
exit-3 precedent.

The `UNCOVERED` corpus (D-07 / A4) that gives `uncovered_max` its meaning is stated rather than
inferred: `docs/{tutorials,how-to,explanation}/**` + `docs/glossary.md` + root `AGENTS.md` + root
`CLAUDE.md` + `.memory/README.md`, enumerated from **git-tracked** files only (an untracked
working-tree file must not move the count, or CI's clean checkout disagrees with a developer's tree).
It **excludes** `.planning/**` (the GSD-owned lane), the instance tree (ADR-0002 / GEN-04), and
everything in `DERIVED_GLOBS` — those trees have their own owners and generators, and counting them
would either double-report or make the ratchet meaningless.

Phase 29's `/docs-update` binds to this state vocabulary AND to these exit codes, so both are pinned
by this record.

### 8. The accepted-ADR vocabulary (D-09)

A `docs/adr/**` target is **forced** to exactly `["REVIEWED_STILL_CURRENT", "SUPERSEDING_ADR_REQUIRED"]`
— subset, superset, and `updated` all reject; a non-accepted (`proposed`, or absent `Status`) ADR
cannot be a binding target at all. `SUPERSEDING_ADR_REQUIRED` is an **open obligation that can never
make a binding green**.

The vocabulary is partitioned **both ways** — a non-ADR target may not declare the ADR-only
dispositions either — so Phase 29 can split the two tracks on the disposition alone.

**The report must NEVER suggest an in-place ADR edit.** `contract_guard` would deny the write anyway;
a report that teaches the wrong action is itself the defect.

### 9. Contract and golden stay leading (D-13)

The guard reads `run_gate()` for **SUPPRESSION ONLY**. A binding whose source is a currently-drifted
contract reports `SUPPRESSED (contract-drift leading)` rather than `STALE_REQUIRED`, and its
**staleness** finding is demoted to note level. The guard **never restates another gate's findings**.
Without this, every contract change fails twice with two different remedies.

**Suppression is scoped to what is genuinely downstream of drift, and that scope is part of the
decision, not an implementation detail.** Only `stale-digest` may be demoted: the source moved, so
of course the reviewed digest no longer matches. The ratification-authority findings —
`first_seen-unratified`, `disposition-incoherent`, `unverified-disposition`, `unknown-binding`,
`superseding-adr-required` — are **never** demoted, and a binding carrying any of them **never
reaches the `SUPPRESSED` state at all**. They answer "who ratified what", a question a drifted
source has no bearing on. A blanket demotion would make contract drift a laundering channel for
clause 3b's self-blessed row, and the escape would be **permanent rather than one-cycle**: the
commit the gate would have failed is the commit that lands the row into history, after which
clause 4's history test reports it green unconditionally.

### 10. The derived queue's placement and ignore status (D-10)

The staleness queue's generator lives at `tools/memory_regen/docs_staleness.py`, **not** in the guard
package, because `tools/harness_lint/tests/test_derived_freshness.py:32` pins
`_ALLOWED_TOOL_MODULES = {memory_regen, docs_sync}` for the curator / `/refresh-memory` surface.

The queue file `.memory/derived/docs-staleness.md` stays **gitignored** and does **NOT** join the
`stale-derived` CI job: its content is a function of the files being edited, so committing it would
red every ordinary source commit. Its SessionStart pointer is one conditional, **droppable** section —
empty string when the queue is empty, so the payload stays byte-identical to today, and never added
to the never-drop tuple.

## Consequences

### What this model does NOT claim

**It detects review OBLIGATIONS, not semantic accuracy.** A `FRESH` binding means two things and only
two things: the reviewed digests still match the live ones, AND a human has previously committed that
row. It does **not** mean the document is correct, complete, or even related to its sources. The gate
compares hashes; it cannot read prose. Any reading of a green `docs-guard` as "the documentation is
right" is a false-assurance failure, and this paragraph exists to make that reading unavailable.

The corollary is that **binding quality is a human responsibility**. A binding whose sources do not
genuinely determine its target is noise that trains people to rubber-stamp — the exact failure mode
this model exists to prevent. The remedy is rejecting the binding at review time, not tuning the gate.

### Accepted costs

- **A new binding is amber for exactly one commit cycle** (clause 3b). This is the boundary working,
  not a defect.
- **CODEOWNERS does NOT cover the ledger**, and CODEOWNERS is advisory unless branch protection is
  enabled. It is therefore **deliberately not relied on** as a control here — the three enforcement
  layers of clause 3b are the control, and they hold without it.
- **Case-sensitivity residual (from the 28-09 write guard).** The adoption-apply choke point folds the
  path with `relative.lower()` before matching, so case-variant spellings are refused there. The
  permission-layer `resolve_path` is `fnmatchcase` (case-**sensitive**), so on the ordinary agent tool
  path a case-variant spelling is denied only if the caller lowers the path first. This is
  pre-existing resolver behaviour shared with `contracts/**` and `golden/**`, not a regression of this
  model; changing it would alter constitution-plane semantics and is out of scope here. Recorded so it
  is a known boundary rather than a surprise.
- **The registry has exactly one validator** (clause 2). If `tools.docs_guard.registry` is bypassed,
  nothing else checks the registry.
- **Impact ids under-deliver by design.** A source that is not a tracked contract yields an **empty**
  impact list, never a fabricated one (the `OWNER_TBD` house rule). Under-delivering is the safe
  direction.

### Good

- One deterministic implementation; the gate consumes contract-drift's result rather than
  re-interpreting it.
- Agent-extensible coverage and unfalsifiable greenness coexist, because they are different artifacts
  with different write rules.
- Phase 29 builds on a single ratified surface — the state vocabulary, the exit codes, and the
  agent-authority boundary are all fixed here, so no second ratification is owed.

### Carried forward, unchanged and NOT closed by this record

- **The D-14 instance-overlay seam** is built (`load_registry` accepts an explicit path) but
  **unused**: only the core registry ships, keeping GEN-04 green.
- **DOCSUP-06 / DOCSUP-07** — the `/docs-update` drive loop with its `docs-upkeep` skill, and `/adopt`
  seeding registry/ledger proposals — are **Phase 29**, not this phase.
- **`tools/hooks/secret_scan.py:44-47`** still hardcodes its pattern list instead of reading it from
  the contract. Carried forward from 26.2 / 27.1 / 27.2 and still open.
- **`harness/skills/gate-model/SKILL.md`'s `path_deny_globs` prose** lists only the three constitution
  trees, omitting `*.env` / `**/*.env` (pre-existing) and now the ledger entry. Deliberately not
  corrected here: that file is the TARGET of the `gate-model-permission-surface` binding, so editing
  it would move a target digest that the human ratification of this phase's ledger is being asked to
  sign. It is a Phase-29 `/docs-update` item — which is precisely the loop this model exists to drive.

## Approval

**Not yet ratified.** This record is `Status: proposed`. A human/CODEOWNERS reviewer flips it to
`accepted` and records the date and deciders at that time. Once ratified it is authoritative and
append-only.

## Links

- Shape contract: `contracts/harness/docs/doc-dependencies.schema.json`; generated reference page
  `docs/reference/doc-dependencies.md`.
- Registry data + ledger: `docs/doc-dependencies.toml`, `docs/.docs-review-ledger.toml`.
- Implementation: `tools/docs_guard/{digest,registry,ledger,guard,impact,cli}.py`; derived queue
  `tools/memory_regen/docs_staleness.py`; SessionStart pointer in `tools/memory_regen/inject.py`.
- Write-side boundary: `tools/hooks/ledger_guard.py` (layer 1 — owns `REVIEW_LEDGER_GLOBS`; opencode
  twin `harness/plugins/ledger-guard.ts`; wired by `tools/harness_emit/merge.py`),
  `tools/adoption_apply/apply.py` (layer 2 — `ReviewLedgerRefusal`), and
  `harness/permission-matrix.json` (`path_deny_globs`, the authored data the hook must agree with).
- Precedents deliberately diverged from or preserved: `tools/adoption_apply/approval.py:57-63`
  (concatenation digest), `tools/contract_drift/drift.py:129-147` (git-show shape),
  `tools/hooks/contract_guard.py:16-20,44` (disjoint domains, constitution deny).
- Design authority: `.planning/phases/28-human-docs-registry-guard-derived-queue-v2-3-c/28-CONTEXT.md`
  (D-01..D-18) and `28-RESEARCH.md`; scope widening rationale in
  `.planning/phases/29-.../29-CONTEXT.md` (D-13).
</content>
