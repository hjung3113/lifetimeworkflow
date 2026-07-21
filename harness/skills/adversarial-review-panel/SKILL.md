---
name: adversarial-review-panel
description: >-
  Use when a high-risk change needs more than one reviewer's angle before it can be verified — runs
  several distinct adversarial frames over the same change through the existing fan-out substrate,
  lands each seat's findings as real evidence, and refuses to count repeated agreement as review.
  Consult when a lane declares the adversarial review panel discipline.
---

# adversarial-review-panel

One reviewer finds what one reviewer is looking for. This is the multi-seat version, and in STRICT
and above it is a **declared lane requirement** (`harness/risk-policy.toml`): a transition into
`VERIFY` is refused without a valid panel record. The empirical case is this repo's own v2.3 —
four of its ten phases exist because adversarial review found real defects, one of them a phase
whose own fix turned out to be inert at runtime.

`/review` is not superseded. It remains the single-seat entry point to the read-only
`code-reviewer` persona, invoked whenever you want it. The panel is the thing a lane can *require*.

## 1. Assign seats — a seat is a frame, not a person

Each seat gets **one question it is not allowed to leave**. That constraint is the entire value: a
reviewer holding one frame notices things a general reviewer skims past. Three seats reading the
same diff with the same question is one opinion typed three times, and the gate rejects it
(`panel carries N distinct expert seat(s), declaration requires M`).

An illustrative default set — extend or replace it to fit the change:

| Seat | The question it refuses to leave |
|------|----------------------------------|
| contract | does this agree with `contracts/`, and does anything cross a boundary in a new shape? |
| security & gating | what can an untrusted or mistaken caller now do that it could not before? Is any gate weakened, bypassable, or merely claimed? |
| failure modes | what happens on the second call, the empty input, the partial write, the crash between two steps? |
| evidence integrity | would these tests still pass if the change were absent? What is asserted vs merely executed? |
| simplicity | what here is not required by anything, and what would this cost the next reader? |

The minimum number of seats and the accepted verdict vocabulary are **data** in
`harness/disciplines.toml`, not numbers written into this page. Read them there; changing what the
panel requires must not require editing a skill.

## 2. Fill each seat from the capability allowlist — not from a name you remember

A seat declares the **capability** it needs, never a persona: `harness/disciplines.toml` routes this
discipline to `adversarial-review`, and `harness/capabilities.toml` holds the closed allowlist of
personas that may serve it. Today that resolves to the two read-only personas (`code-reviewer`,
`explorer`); if the allowlist changes, this page does not.

Check a route before you take it, and record which agent filled each seat:

```
uv run python -m tools.capability list                                  # the vocabulary
uv run python -m tools.capability route adversarial-review <agent>      # 0 allowed, 3 REFUSED
```

The capability is declared `read_only = true`, and that is the substance of the rule rather than an
annotation: an agent that can edit the change it is judging is the author wearing a second hat. A
seat filled by an agent outside the allowlist makes the whole panel record invalid, so the `VERIFY`
transition is refused — the same refusal as having written no panel at all.

## 3. Dispatch through the existing fan-out substrate — no second dispatcher

The panel is an application of `fan-out-synthesize`, not a new engine. Follow its rules exactly:
dispatch each seat as a subtask via the runtime's own affordance (`task` / `Task`) to an allowlisted
read-only provider — `explorer` (`harness/agents/explorer.md` — Read/Grep/Glob, `edit: deny`) or
`code-reviewer`. Do **not** build a dispatch tool, and do **not** invent a reviewer persona per
seat; the frame lives in the seat's prompt, and the return contract is enforced by the prompt, not
by frontmatter.

Give every seat the same change under review and a different frame. Require the return to conform to
`references/panel-seat.schema.json`: an `expert`, its `frame`, a `verdict`, and `findings` that are
terse claims with citations — never pasted file bodies.

A seat that finds nothing returns an empty `findings` array. That is a real result and it is not the
same as not having looked.

## 4. Land the findings as evidence, not as prose

Synthesize the returns without re-reading the raw files (`fan-out-synthesize` step 4), then write
every finding worth keeping into the task packet's `evidence.json` `findings` with a severity and a
disposition. This is the step that makes the panel load-bearing rather than decorative:

- the panel record's cited finding ids **must exist** in `evidence.json`, or the record is invalid;
- an open `blocker` or `major` finding already refuses `COMPLETE` through the shipped evidence
  machinery — the panel does not need, and must not grow, a second enforcement path.

Duplicate findings from two seats collapse to one evidence finding. Disagreement between seats does
not: record both, and let the disposition say which was accepted and why.

## 5. Record the panel

Write `<task_dir>/discipline/adversarial-review-panel.json` with the seats, their verdicts, the
`agent` that filled each seat, and the evidence finding ids each cited, plus the synthesis document
in `outputs`. The `agent` is checked **per seat** — a panel routed three ways is three routing
decisions, and the refusal names the offending seat. Then:

`uv run python -m tools.discipline <task_dir>` — 0 when the panel is satisfied, 1 while it is not,
3 when the declaration or packet is malformed.

A `block` verdict is not discharged by writing the record. It is discharged by resolving the finding
that caused it, which is the whole point of having asked.
