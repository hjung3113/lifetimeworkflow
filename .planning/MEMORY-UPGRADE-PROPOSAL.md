# Memory-Model Upgrade — Design Proposal (next milestone)

> **Status:** design / scoping doc for the next milestone. **Not** an ADR yet, **not** implementation.
> Nothing here has been built. All claims are cited to real files (path:line).
> Working title for the milestone: **MEM2 — Process Memory & Provenance Reframe**.

---

## 1. Diagnosis — one framing is doing two jobs

The harness's context-memory system collapses **two unrelated concerns** into a single
"provisional / don't-trust / verify-before-trusting" tone, and it has **no channel at all** for
one whole category.

### 1a. What IS modeled (and is correct — keep it): data-provenance trust

The three-plane model (`.memory/README.md:9-15`) is fundamentally a **provenance / authority**
model: which artifact wins when two artifacts disagree. Its rule — *a derived/volatile artifact
must never override the constitution* — is correct and contract-first:

- `.memory/README.md:50-53` — state is "committed (so it survives), but it is **provisional**… a
  banner declaring that `contracts/` and `docs/adr/` always override `.memory/state/` on conflict."
- `harness/skills/two-plane-memory/SKILL.md:31-33` — state "is **provisional**: contracts/ and
  docs/adr/ always override it on conflict."
- `harness/skills/gate-model/SKILL.md:11-13` — the invariant behind all of it: "**machines gate,
  humans ratify.**"

This is a statement about **data authority on conflict**. It is right. Nothing below removes it.

### 1b. What is NOT modeled (the gap): work-execution behavior + process feedback

There is **no durable channel** for *how an agent should work* — how confidently to act, when to
verify vs proceed, and critically the user's **mid-work process/methodology feedback** ("stop
overstepping", "proceed when grounded, don't self-cancel valid work", "do it this way"). Today
that feedback has nowhere to live:

- `.memory/state/` holds only `activeContext.md` ("what is in flight", `activeContext.md:7-9`) and
  `progress.md` ("terse running log", `progress.md:1`). Both are **progress**, not **process**.
- Decisions are pushed to append-only ADRs (`AGENTS.md:82`, `two-plane-memory/SKILL.md:54`) — but
  an ADR is a heavyweight architecture record, not a lightweight "how to work with me" agreement,
  and ADRs are human-gated + immutable (`docs/adr/README.md:12-18`).
- So process feedback either evaporates at session end or gets mis-filed as a "decision."

### 1c. The concrete harm: the provenance tone bleeds into behavior

Because there is no behavior channel, the **provenance-distrust wording gets read as a general
behavioral directive**. The trigger, injected at **every** session start:

- `tools/memory_regen/inject.py:41-44` — the `BANNER` constant (priority 0, "NEVER dropped",
  `inject.py:118-124`, `:131`):
  > `"PROVISIONAL — volatile session state below is a hint, not truth. contracts/ and docs/adr/
  > (ADR) ALWAYS override .memory/ on conflict."`
- `tools/memory_regen/inject.py:96-99` — the activeContext pointer:
  > `".memory/state/activeContext.md — volatile; confirm against contracts/ADR before trusting."`

The clause is *scoped to data* ("override … on conflict"), but the words "a hint, not truth" and
"**confirm before trusting**" read as a blanket epistemic instruction. Reinforced verbatim in
`.memory/state/activeContext.md:3-5`, `.memory/state/progress.md:3-4`,
`two-plane-memory/SKILL.md:31-33`, and `AGENTS.md:87-88`. An agent absorbing "confirm before
trusting" at session start is nudged to reflexively **retract, hedge, or self-cancel grounded
work** — the exact overstepping-in-reverse the missing channel would correct.

### 1d. Secondary defect: progress goes stale silently

`activeContext.md` / `progress.md` mix "what's in flight/done" with nothing for "how to work," and
the injector surfaces only a **pointer** with no freshness signal (`inject.py:96-99`). The payload
is deliberately timestamp-free for determinism (`inject.py:20-22`), so a state file frozen for
months is injected with the same confidence as one written today — no staleness is visible.

---

## 2. Proposed model — a 4th channel: PROCESS / working-agreements

Keep the three planes. **Add a fourth memory channel** whose properties are the *inverse* of the
volatile state plane.

| Channel | Location | Ownership | Authority | Lifecycle | Injected as |
|---|---|---|---|---|---|
| CONSTITUTION | `contracts/`, `docs/adr/`, `golden/` | human, CODEOWNERS-gated | source of truth | append-only / gated | pointers (drift + index) |
| DERIVED | `.memory/derived/` | machine (`tools/memory_regen`) | regenerable | every session | index/repo-map summaries |
| STATE (progress) | `.memory/state/` | agent-authored | **provisional** (data) | turns over each session | pointer |
| **PROCESS (new)** | **`.memory/working-agreements.md`** | **user-authored via feedback** | **authoritative directive** | **curated: add on feedback, retire explicitly** | **full body, as a directive** |

**Properties of the PROCESS channel (the whole point — it is NOT the state plane):**

1. **Durable & authoritative, not provisional.** Injected as a **directive to honor**, not a
   hedged pointer. It never carries "a hint, not truth / confirm before trusting." It is the
   standing answer to "how do I work in this repo / with this operator."
2. **User-authored via feedback.** Entries exist because the user gave process feedback. An agent
   **must not invent** entries; the user's explicit in-session instruction *is* the ratification
   (the user is the human in "machines gate, humans ratify", `gate-model/SKILL.md:11-13`).
3. **Curated lifecycle, separate from progress.** Entries are **added** when feedback arrives and
   **explicitly retired** when obsolete — never auto-churned, never silently rotated like the
   progress log. Each entry stamps *when* and *why* it was added.
4. **Injected full-body at SessionStart.** Directives must be *present*, not *pointed at* — so the
   payload includes the body (it is small and committed), unlike the activeContext pointer. This
   respects lazy-load because working-agreements are behavior, not contract data.

### Location & gating — recommendation

**Recommendation: a new committed tier at `.memory/working-agreements.md`, human-directed but NOT
under `path_deny_globs`.** Rationale:

- It must be **frictionless to capture** — the trigger is a user typing feedback mid-work. If it
  were path-denied like `contracts/**`/`docs/adr/**` (`gate-model/SKILL.md:24-27`), every capture
  would need the `GOLDEN_APPROVE_HUMAN` token dance (`gate-model/SKILL.md:44-51`) — too heavy for a
  running conversation, and the feedback would be lost.
- It is **not contract truth** — it governs agent behavior, not data shapes, so it does not need
  the golden/drift machinery that guards `contracts/`.
- Authority comes from **provenance + injection wording**, not from a write-lock: entries are
  written **only in response to explicit user feedback** (enforced by discipline + a provenance
  lint, MEM2-04), and injected as directives. The user directing the write *is* the gate.

**Trade-off (record as an open question, §6):** a committed-but-agent-writable file means an agent
*could* append an unsolicited entry. Mitigation is the provenance stamp + a `harness_lint` check
that every entry has an "added because <user said>" origin, plus retirement being an explicit act.
The alternative — putting it in the constitution plane (path-denied, CODEOWNERS-gated) — buys
tamper-resistance but costs capture friction; deferred to the operator at kickoff.

---

## 3. Reframe the injector — scope "provisional/verify" to DATA only

Split the single banner into **two distinct blocks**: an authoritative directive block for process,
and a **data-scoped** provenance banner that can no longer be misread as "distrust your own work."

### Banner — before / after

**BEFORE** (`tools/memory_regen/inject.py:41-44`):

```
PROVISIONAL — volatile session state below is a hint, not truth. contracts/ and
docs/adr/ (ADR) ALWAYS override .memory/ on conflict.
```

**AFTER** — two sections (new `WORKING_AGREEMENTS` block at priority 0, reworded data banner after):

```
## Working agreements (authoritative — honor these)
<full body of .memory/working-agreements.md, or "none recorded yet">

DATA PROVENANCE — the derived/state summaries below are auto-generated context, not the
source of truth. On a DATA conflict, contracts/ and docs/adr/ (ADR) always win over
.memory/. This is about which artifact wins a contradiction — NOT a reason to distrust,
retract, or re-verify your own grounded working context.
```

### activeContext pointer — before / after

**BEFORE** (`tools/memory_regen/inject.py:96-99`):

```
.memory/state/activeContext.md — volatile; confirm against contracts/ADR before trusting.
```

**AFTER**:

```
.memory/state/activeContext.md — session progress log (what was in flight). On a data
conflict, contracts/ADR win. [updated: <stamp from file>]
```

Same reword applied to the human-facing copies: `.memory/state/activeContext.md:3-5`,
`.memory/state/progress.md:3-4`, `two-plane-memory/SKILL.md:31-33`, `AGENTS.md:87-88`,
`.memory/README.md:50-53`.

**Determinism constraint (must honor):** `inject.py:20-22` requires the payload be timestamp-free so
`assemble()` is deterministic (delete+regen identical). Therefore `assemble()` surfaces the state
file's own committed `updated:` stamp **verbatim** (deterministic text), and any "is this stale?"
comparison against wall-clock is done in the **hook wrapper** (`memory-inject.sh`) or left to the
agent (session context already carries today's date) — never inside `assemble()`.

---

## 4. Separate progress vs process, and guard progress staleness

**What belongs where:**

| Belongs in STATE / progress (`.memory/state/`) | Belongs in PROCESS (`working-agreements.md`) |
|---|---|
| What is in flight right now | How to work / when to proceed vs verify |
| What's done / what remains | "Proceed when grounded; don't self-cancel valid work" |
| Turns over every session; freely churned | User methodology feedback; durable until retired |
| Injected as a **pointer** | Injected **full-body as a directive** |
| Provisional (data authority) | Authoritative (behavior) |

**Staleness guard for progress** (MEM2-05): add an `updated: <ISO-date>` stamp to
`activeContext.md` / `progress.md` (written by `/checkpoint`). `assemble()` surfaces the stamp
verbatim (per the determinism constraint above); the hook wrapper or `/checkpoint` emits a freshness
reminder when the stamp is old. This directly fixes 1d — a frozen progress log can no longer be
injected as if fresh. Reuse the existing `/checkpoint` write path (`harness/commands/checkpoint.md`)
and the `stale-derived` gate *pattern* (regenerate → diff, `harness/commands/verify-work.md` step 5)
as the model for a lightweight freshness check.

---

## 5. Milestone scope (GSD-ready)

**Goal statement.** Give the harness a durable, authoritative **process-memory channel** for user
methodology feedback, and reframe the SessionStart provenance wording so "provisional/verify" is
scoped to *data authority* only — so agents act confidently on grounded work instead of reflexively
self-cancelling, while the contract-first provenance rule stays intact.

### Candidate requirements

| ID | Requirement |
|---|---|
| **MEM2-01** | Introduce the PROCESS channel `.memory/working-agreements.md` — committed, user-authored, curated (add-on-feedback / explicit-retire). Define the entry shape: `status` (active/retired), provenance stamp ("added because <user feedback>"), added-date. |
| **MEM2-02** | Reframe `tools/memory_regen/inject.py` — split the banner into (a) a full-body **working-agreements directive** section (new priority-0, never-dropped) and (b) a **data-scoped** provenance banner; reword the activeContext pointer. Preserve determinism (`inject.py:20-22`) and the char budget (`inject.py:105-135`). |
| **MEM2-03** | Reword the distrust framing everywhere it is echoed so it reads as *data authority*, not behavior: `.memory/README.md:50-53`, `.memory/state/activeContext.md:3-5`, `.memory/state/progress.md:3-4`, `harness/skills/two-plane-memory/SKILL.md:31-33`, `AGENTS.md:87-88`. |
| **MEM2-04** | Sanctioned write path + anti-churn guard: extend `/checkpoint` (or add a thin `/agree` command) to append/retire a working-agreement **only on explicit user feedback**; add a `tools/harness_lint` check that every entry carries a provenance stamp and that agents cannot auto-invent entries. |
| **MEM2-05** | Progress staleness guard: add `updated:` stamp to state files (written by `/checkpoint`); `assemble()` surfaces it verbatim; hook wrapper / `/checkpoint` emits a freshness reminder — no wall-clock inside `assemble()`. |
| **MEM2-06** | Record the model change as **ADR-0006** (append-only, next number per `docs/adr/README.md:11-13`); round-trip every new/changed agent/skill/command through the Phase-7 emitter (`tools/harness_emit`) to **both** runtimes with **no model id**; keep GEN-04 core-independence green. |

### Suggested phase breakdown (each reuses existing machinery)

- **Phase A — Model + ADR + doc reframe (MEM2-01, -03, and ADR from -06).** Author ADR-0006
  (via the human-ratified constitution path — `contract-guard` will correctly deny an agent Write
  to `docs/adr/`, as it did for ADR-0004, `.planning/STATE.md:210`); create the empty
  `working-agreements.md` scaffold; reword the echoed provenance prose. *Machinery: `adr` skill /
  `/adr`, CODEOWNERS ratification.*
- **Phase B — Injector reframe + channel wiring (MEM2-02, -05).** Add the `WORKING_AGREEMENTS`
  section builder + reworded `BANNER` to `inject.py`; surface the `updated:` stamp; keep
  determinism + budget. *Machinery: `tools/memory_regen`, its existing determinism test
  (delete+regen byte-identical, `inject.py:20-22`).*
- **Phase C — Write path + anti-churn guard (MEM2-04).** Extend `/checkpoint` or add `/agree`;
  provenance/anti-invent lint in `tools/harness_lint`. *Machinery: `harness/commands/checkpoint.md`,
  `tools/harness_lint`, the `stale-derived` gate pattern (`verify-work.md` step 5).*
- **Phase D — Emit round-trip + gates (MEM2-06).** Re-run `tools/harness_emit` (glob discovery, no
  emitter code change — mirrors Phase-10 close, `.planning/STATE.md:177`) to project any new
  command/skill + updated AGENTS.md managed block to both runtimes; update emit fixtures + counts;
  prove emit-drift clean, GEN-04 green, no model id. *Machinery: Phase-7 emitter.*

### Non-negotiables honored

- **Contract-first / constitution gated:** ADR-0006 lands via the human-ratified path; no agent
  self-edits `docs/adr/` (`gate-model/SKILL.md:11-27`).
- **Machines gate / humans ratify:** working-agreements are written **only** on explicit user
  feedback; the user *is* the ratifier.
- **Emitter round-trip, no model id:** every surface change re-emits to `.opencode/` + `.claude/`
  with placeholder tiers only (`AGENTS.md:97-106`, `.planning/STATE.md:163-169`).
- **Derived never hand-edited:** the new channel is a **committed human-authored tier** (like
  `state/`), NOT a derived artifact — it is never regenerated, so it does not collide with
  `.memory/derived/` (`two-plane-memory/SKILL.md:35-46`).
- **GEN-04 core-independence:** everything added is domain-neutral harness core; no `examples/`
  dependency (`AGENTS.md:16`).

---

## 6. Open questions for the operator (decide at kickoff)

1. **Gating strength.** Keep `working-agreements.md` **committed-but-writable** (frictionless
   capture, provenance-lint as the guard — recommended), or promote it into the **constitution
   plane** (path-denied + CODEOWNERS, tamper-proof but every capture needs the human token)?
2. **Command surface.** Extend `/checkpoint` to also write working-agreements, or add a dedicated
   `/agree` command? (Adding a command means +1 to `EXPECTED_COMMANDS` and an emit round-trip.)
3. **Scope of an agreement.** One global file, or does the channel eventually need per-instance
   overlays (like `project.toml` overlays, ADR-0003) for `examples/*`? MVP recommendation: one
   global core file.
4. **Full-body budget.** Working-agreements inject full-body at priority 0 (never dropped). Cap its
   size (e.g. N entries / M chars) so it can't crowd out drift + index under the ~4000-char budget
   (`inject.py:105`)?
5. **Retirement semantics.** Retire = delete the entry, or keep it with `status: retired` for an
   audit trail (heavier file, but curated history)?
6. **Staleness threshold.** What age makes progress "stale," and where does the wall-clock
   comparison live — hook wrapper, `/checkpoint`, or agent-side (given determinism forbids it in
   `assemble()`)?
