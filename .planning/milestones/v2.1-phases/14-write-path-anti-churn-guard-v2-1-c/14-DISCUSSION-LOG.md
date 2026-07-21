# Phase 14: Write Path + Anti-Churn Guard (v2.1 C) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-16
**Phase:** 14-write-path-anti-churn-guard-v2-1-c
**Mode:** `--auto` — no AskUserQuestion. Claude selected the recommended option for every area and
logged each choice below for operator audit. Single pass.
**Areas discussed:** Provenance stamp shape, Lint delivery surface, `/agree` refusal contract,
Anti-invent honest scope, Emit boundary, ADR-0006 seed discrepancy

---

## Provenance stamp shape

| Option | Description | Selected |
|--------|-------------|----------|
| Presence + non-empty | `provenance:` key exists and is not blank. Cheapest. | |
| Structural regex over frontmatter (recommended) | `status` ∈ {active,retired}; `added:` ISO date as a **quoted string**; `provenance:` matches `^added because \S`. Mirrors `_TEMPLATE.md` exactly. | ✓ |
| Signed / attested stamp | Cryptographic origin proof. | |

**[auto] Selected:** Structural regex (recommended default) → D-01, D-02
**Notes:** Signing was rejected as theater — it proves an author, not that the user actually said
the thing, so it does not touch the real threat (see Anti-invent below). Mere presence was rejected
as too weak to catch a malformed stamp.

**Surfaced during analysis (not a menu choice):** `_TEMPLATE.md:3` ships `added: YYYY-MM-DD`
**unquoted**, which YAML parses to a `datetime.date`, not a `str`. This is the identical defect
Phase 13 hit on the `updated:` stamp and settled by quoting (13-01, open-Q A6). Recorded as D-02:
fix the template, and make the lint require `str` so a bare date object FAILS rather than being
silently coerced.

---

## Lint delivery surface

| Option | Description | Selected |
|--------|-------------|----------|
| pytest-only | A test under `tools/harness_lint/tests/`. CI gate only, no local signal. | |
| Runnable module + `/lint` + pytest (recommended) | `tools/harness_lint/provenance.py` cloning `polyglot_lint`'s `Violation`/`lint_file`/`main` shape, wired into `/lint`, plus a pytest gate. | ✓ |
| PreToolUse hook | Block the write at tool-call time. | |

**[auto] Selected:** Runnable module + `/lint` + pytest (recommended default) → D-04
**Notes:** The hook option was not merely deprioritized — it was **rejected on the merits** (D-03):
a hook cannot distinguish a genuine stamp from a fabricated one, so it buys no security while
costing real complexity. `tools/harness_lint/` currently has no runnable lint (only `caps.py`,
`frontmatter.py`, `tests/`), so `polyglot_lint/lint.py` is the shape to clone rather than invent.

**Also decided (D-05):** the fail-closed file-selection predicate must be **shared with
`inject.py`**, not copied. Two hand-kept copies would drift, and drift means the lint and the
injector disagree about what an agreement is. Extraction preferred; a fixture-parity test is the
fallback if extraction proves invasive.

---

## `/agree` refusal contract

| Option | Description | Selected |
|--------|-------------|----------|
| Require `--because "<verbatim feedback>"`, refuse exit 3 (recommended) | Mirrors `approve.py`'s `GoldenApprovalRefused`. Blank/whitespace never satisfies it. The value becomes the provenance tail. | ✓ |
| Prose-only discipline | The command doc says "only on user feedback"; nothing enforces it. | |
| Require `GOLDEN_APPROVE_HUMAN` | Treat an agreement like a constitution write. | |

**[auto] Selected:** `--because` + exit-3 refusal (recommended default) → D-07
**Notes:** The `GOLDEN_APPROVE_HUMAN` option was rejected on design grounds, not convenience (D-08):
agreements are deliberately **not** constitution plane (Q1 = committed-but-writable). Requiring the
human token reintroduces exactly the capture friction §2's "Location & gating" section rejected —
"the trigger is a user typing feedback mid-work" — and would mislabel a working-style note as
constitution ratification, eroding the token's audit meaning the way ADR-0007 was careful not to.
Retire semantics were not a gray area: locked to `status: retired`, never delete, by Q5/§7b (D-09).

---

## Anti-invent honest scope

| Option | Description | Selected |
|--------|-------------|----------|
| Claim the lint prevents invention | Matches ROADMAP SC2's literal wording. | |
| Record honestly: shape-not-truth (recommended) | The lint catches omitted/malformed stamps; a fabricated-but-well-formed stamp passes. Invention becomes a visible, deliberate act — not impossible. | ✓ |

**[auto] Selected:** Record honestly (recommended default) → D-03
**Notes:** This is a **correction to the phase's own requirement wording**, surfaced rather than
papered over. ROADMAP SC2 and MEM2-04 both say the guard means "agents cannot auto-invent entries."
That overclaims: nothing stops an agent from writing a well-formed provenance quoting words the user
never said. The honest claim — accident-prevention plus auditability, with git review as the real
defense — is the same trust model ADR-0007 already accepted in writing for `HARNESS_DEV_BYPASS`
("the guard is accident-prevention, not a sandbox"). Planning to the overclaimed version would
produce security theater (e.g. the rejected hook). Flagged for the operator: if the honest scope is
unacceptable, the remedy is promoting the channel into the constitution plane — i.e. revisiting Q1 —
not adding more runtime guards.

---

## Emit boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Source-only; Phase 15 emits (recommended) | Author `harness/commands/agree.md`; leave `.opencode/`/`.claude/` untouched. | ✓ |
| Emit in this phase | Round-trip `/agree` to both runtimes now. | |

**[auto] Selected:** Source-only (recommended default) → D-10
**Notes:** Load-bearing, not stylistic. `tools/harness_emit/tests/test_coexist.py:53-54` asserts
**exactly 19** emitted commands per runtime. Not emitting keeps that test green; emitting makes it
20 and turns a **currently-passing** test red, pushing `harness_emit` past its sanctioned "no worse
than 1 failed" baseline and muddying Phase 15's gate. Phase 15 owns the round-trip and owes the
19→20 bump. Precedent: Phase 10 (10-01/02 source-only, 10-03 emit). ROADMAP SC3 independently agrees
("its emit round-trip to both runtimes is owned by Phase 15").

**Surfaced during analysis (not a menu choice):** **`EXPECTED_COMMANDS` does not exist.** ROADMAP
SC3 and MEM2-04 both name it; `grep` across `tools/` returns nothing. `test_commands.py` is
glob-driven (auto-covers a new command file), and the only hard count lives in `test_coexist.py`
(Phase 15). Recorded as D-11: satisfy SC3 by authoring the command file, and do **not** invent an
`EXPECTED_COMMANDS` frozenset just to match the mis-worded criterion — that would add the
hand-maintained list the glob design deliberately avoids.

---

## ADR-0006 seed discrepancy

| Option | Description | Selected |
|--------|-------------|----------|
| Dated `## Errata` note appended to ADR-0006 (recommended) | Leaves decision content untouched; records that no seed shipped and that empty is correct. | ✓ |
| Ship a real seed agreement | Make the ADR's claim true retroactively. | |
| Supersede with ADR-0008 | Follow README:16 literally. | |

**[auto] Selected:** Errata note (recommended default) → D-12, D-13
**Notes:** Operator ratified deferral of this item to Phase 14 earlier in the session (2026-07-16);
this discussion picks the resolution. "Ship a seed" was rejected on principle: fabricating an
agreement to make the ADR true would require **inventing user feedback** — the exact T-13-01 /
anti-invent violation this phase exists to prevent. The phase must not open by committing the sin it
closes. "Supersede" was rejected as the wrong instrument: `docs/adr/README.md:16` scopes supersede to
*changing a past decision*, and no decision changed — a factual claim about what shipped was simply
wrong. An appended, dated `## Errata` section is defensible under README:14, which forbids editing
*decision content* only. Landing it is a constitution write → `HARNESS_DEV_BYPASS` (ADR-0007) or raw
shell; **never forge `GOLDEN_APPROVE_HUMAN`**.

---

## Claude's Discretion

- Module/file naming, argument-parser layout, and test decomposition within the fixed shapes above.
- Whether D-05's shared predicate lands as an extraction from `inject.py` or a fixture-parity test —
  decide from what the code permits; extraction preferred.

## Deferred Ideas

- Emit round-trip + `test_coexist` 19→20 + settling the red `harness_emit` snapshot → **Phase 15**.
- `Related:` pointer target resolution / referential integrity → **Phase 16** (MEM2-07, §7d).
- Lint checking `Related:` *presence* → deferred with the above; widening SC2's provenance scope here
  is scope creep.
- Per-instance agreement overlays (§6 Q3) → out of scope; MVP is one global core set.
- PreToolUse provenance hook → **rejected**, not deferred (D-03).
