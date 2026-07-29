#!/usr/bin/env bash
# Apply the human-gated v2.5 leftovers to the constitution plane.
#
# Run this YOURSELF. It is the human performing the write — the contract-guard PreToolUse hook
# gates the AGENT's Write/Edit tool, and this script deliberately does NOT set
# GOLDEN_APPROVE_HUMAN or HARNESS_DEV_BYPASS. CODEOWNERS at the merge stays the real ratification.
#
#   bash .planning/quick/260729-wdi-close-v2-5-handoff-leftovers-adr-superse/apply.sh
#
# Every edit asserts its target text occurs EXACTLY ONCE before replacing it, and aborts otherwise.
# Nothing is written until all four files pass their preflight check.

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

if [ -e docs/adr/0013-task-control-plane-retirement.md ]; then
  echo "ERROR: docs/adr/0013-task-control-plane-retirement.md already exists — refusing to overwrite." >&2
  exit 1
fi

ADR13="docs/adr/0013-task-control-plane-retirement.md"

# ── A. the new record ─────────────────────────────────────────────────────────────────────────
cat > "$ADR13" <<'ADR_EOF'
# 13. Task-Control-Plane Retirement and the Append-Only Citation Rule

*MADR 4.x · plane: constitution (human-owned, immutable, append-only)*

- **Status:** accepted
- **Date:** 2026-07-29
- **Deciders:** kimhyojung (CODEOWNERS)
- **Supersedes:** 0008
- **Superseded by:** —
- **Complements:** [ADR-0012](0012-ci-and-merge-as-decision-authority.md), [ADR-0003](0003-pipeline-topology-slot-and-instance-overlay.md)

## Context and Problem Statement

ADR-0012 made CI and the merge the decision authority for v2.5 and superseded ADR-0001 and ADR-0010
by name. It did not name **ADR-0008**, whose entire subject — the `.workflow/tasks/<task-id>/`
task-control plane, its six-phase lifecycle, and its instance risk overlays — Phase 43 deleted
(CER-07, commit `7b72e6e`, −12,383 LOC).

That omission is not cosmetic. This repo's stated precedence is that accepted ADRs win a data
conflict against code. ADR-0008 currently reads `Status: Accepted` / `Superseded by: —`, so as
written it tells every agent that the deletion was the error and the plane should be restored. The
record must be corrected the only way an append-only log allows: a new record.

A second, narrower gap surfaced in Phase 45 (D-14) and needs deciding with it. Two accepted ADRs
cite documents whose subject matter this milestone removed:

- `docs/adr/0008-task-control-plane-lifecycle.md:50` cites
  `docs/explanation/next-milestone-task-control-plane.md` as its "Design authority".
- `docs/adr/0003-pipeline-topology-slot-and-instance-overlay.md:95` cites
  `harness/agents/templates/component-engineer.md`.

Because ADRs are append-only and their text cannot be corrected after ratification, deleting a cited
target creates a **permanently uncorrectable** dangling reference. Phase 45 handled both by keeping
the targets — one with a HISTORICAL header, one corrected in place — rather than deleting them, but
did so as an executor judgment call with no ratified rule behind it. This ADR supplies the rule.

## Decision Drivers

- Accepted ADRs outrank code in a data conflict, so a stale `Accepted` status actively misdirects
  agents — the opposite of what the record exists for.
- Supersede-don't-edit: a past decision is changed by writing a new record, never by rewriting the
  old one's reasoning.
- v2.5's binding constraint — do not answer a gap by adding ceremony. The remedy here is one
  record and two header lines, not a new gate or a link-checking tool.
- An append-only log cannot repair its own citations, so citation targets need a durable rule rather
  than a per-phase judgment call.

## Considered Options

1. **Leave ADR-0008 as `Accepted` and rely on ADR-0012's general thesis.** *Rejected:* ADR-0012
   never names 0008, and the precedence rule then reads the deletion as the defect.
2. **Edit ADR-0008's body to describe the retirement.** *Rejected:* violates append-only; the
   historical record of what was decided on 2026-07-19 must survive intact.
3. **Delete ADR-0008 and its cited design document.** *Rejected:* removes the record of a real
   ratified decision and creates exactly the uncorrectable dangling citation this ADR forbids.
4. **New superseding ADR + status-header update on 0008 + a durable citation rule.** *Chosen* —
   matches the precedent ADR-0012 set for 0001 and 0010.

## Decision Outcome

**Ratified by human/CODEOWNERS on 2026-07-29.**

### (a) ADR-0008 is superseded in full

The `.workflow/tasks/<task-id>/` namespace, the `INTAKE`/`CLARIFY`/`SPEC`/`PLAN`/`EXECUTE`/`REVIEW`/
`VERIFY`/`COMPLETE` lifecycle with revision-CAS transitions, and the escalate-only instance risk
overlays are **retired**. They were harness machinery for verifying the harness's own process —
precisely what ADR-0012 replaces with CI and the merge. Phase 43 executed the removal; this record
is the decision that removal cites.

Retired with it, and confirmed absent from the tree: `.workflow/`, `tools/task_packet/`,
`tools/risk_router/`, `tools/task_control/`, `tools/evidence/`, and `tools/handoff/`. ADR-0008's
"Links" section still names all six. That text is immutable and is now **historical**: it records
what once existed, not what an agent should expect to find. Reading it as live is the error this
record corrects.

The product-side lifecycle is **not** retired by this ADR — ADR-0012 clause (c) already drew that
boundary, and Phase 46 shipped the four routes plus `/flow` that occupy it. This clause retires the
*harness's* task-control plane only.

### (b) A cited target of an accepted ADR is never deleted

Once an accepted ADR cites a path, that path may be **corrected** or **marked historical**, but not
removed, because the citing text can never be repaired. Concretely, and ratifying what Phase 45 did:

- `docs/explanation/next-milestone-task-control-plane.md` is **kept** under a HISTORICAL header
  stating that the controls, paths, and commands it describes no longer exist.
- `harness/agents/templates/component-engineer.md` is **kept and corrected in place**; two live
  gates depend on it independently of ADR-0003.

ADR-0003's citation at `:95` therefore stands as written and needs no correction — the target is
live and accurate. This clause exists so the next deletion phase does not have to re-derive that.

This is a rule about **cited targets**, not a general no-delete rule: a document no ADR cites is
deleted normally.

### (c) No new enforcement

No link checker, no citation gate, no CI job is added. Per ADR-0012 the merge is the authority, and
per v2.5's binding constraint the default answer to "should we also gate this?" is no. Clause (b) is
a rule for humans and agents to follow at review, enforced by CODEOWNERS on the constitution plane.

### Consequences

- **Good:** the ADR log stops asserting that a deleted plane is current, so the precedence rule now
  points agents at the truth instead of away from it.
- **Good:** deletion phases get a ratified answer to "may I delete this cited file?" instead of
  re-deriving it, as Phases 43-45 each had to.
- **Bad / accepted:** the repository permanently keeps at least one document whose only remaining
  purpose is to satisfy an append-only citation. That cost is the price of an immutable log, and it
  is bounded — one file today.
- **Bad / accepted:** clause (b) is unenforced by machine, so a future deletion can still break a
  citation. Detection is CODEOWNERS review at the PR, consistent with ADR-0012.

## Links

- Supersedes: [ADR-0008](0008-task-control-plane-lifecycle.md) — the retired record.
- Authority for the retirement: [ADR-0012](0012-ci-and-merge-as-decision-authority.md), whose thesis
  this applies to the one plane it did not name.
- Executed by: Phase 43 (Lifecycle Plane Removal, `7b72e6e`); the citation targets were settled in
  Phase 45 (Projection Repair, `41d0c92`) and are ratified here.
ADR_EOF

echo "created $ADR13"

# ── B/C/D. exact-match replacements, each asserted to occur exactly once ───────────────────────
# If the preflight below aborts, the record created above is removed so a failed run leaves no
# half-applied constitution plane. Disarmed once the edits land.
trap 'rm -f "$ADR13"; echo "rolled back $ADR13" >&2' ERR

python3 - <<'PY_EOF'
import sys

EDITS = [
    # (path, old, new)
    (
        "docs/adr/0008-task-control-plane-lifecycle.md",
        "- **Status:** Accepted — ratified by human/CODEOWNERS.\n",
        "- **Status:** superseded by 0013\n",
    ),
    (
        "docs/adr/0008-task-control-plane-lifecycle.md",
        "- **Superseded by:** —\n",
        "- **Superseded by:** [0013](0013-task-control-plane-retirement.md)\n",
    ),
    (
        "docs/adr/README.md",
        "| [0008](0008-task-control-plane-lifecycle.md) | Task Control Plane Namespace, Authority, Lifecycle, and Overlay | accepted |\n",
        "| [0008](0008-task-control-plane-lifecycle.md) | Task Control Plane Namespace, Authority, Lifecycle, and Overlay | superseded by 0013 |\n",
    ),
    (
        "docs/adr/README.md",
        "| [0012](0012-ci-and-merge-as-decision-authority.md) | CI and the Merge as Decision Authority | accepted |\n",
        "| [0012](0012-ci-and-merge-as-decision-authority.md) | CI and the Merge as Decision Authority | accepted |\n"
        "| [0013](0013-task-control-plane-retirement.md) | Task-Control-Plane Retirement and the Append-Only Citation Rule | accepted |\n",
    ),
    (
        "docs/glossary.md",
        "| **`.received` / `.verified`** | The two-file golden split: `.received` is machine-proposed output; `.verified` is the human-promoted, approved baseline. Promotion is the `/golden-approve` step. |\n",
        "| **`.received` / `.verified`** | The two-file golden split: `.received` is machine-proposed output; `.verified` is the human-promoted, approved baseline. Promotion requires a human `GOLDEN_APPROVE_HUMAN` ratification, gated again by CODEOWNERS at merge. |\n",
    ),
    (
        "docs/glossary.md",
        "| **Constitution plane** | Human-owned, gated source of truth: `contracts/`, `golden/`, `docs/adr/`, `docs/glossary.md`. Changed only through review (CODEOWNERS) and the golden/drift gates. |\n",
        "| **Constitution plane** | Human-owned, gated source of truth: `contracts/`, `docs/adr/`, `docs/glossary.md` (ADR-0001's fourth member, root `golden/`, is superseded by ADR-0012 clause (d); instance baselines live at `examples/<instance>/golden/`). Changed only through review (CODEOWNERS) and the golden/drift gates. |\n",
    ),
]

# Preflight: every target must occur exactly once, in the ORIGINAL bytes, before anything is written.
originals = {}
for path, old, _new in EDITS:
    if path not in originals:
        with open(path, encoding="utf-8") as fh:
            originals[path] = fh.read()
    n = originals[path].count(old)
    if n != 1:
        sys.exit(
            f"ABORT: expected exactly 1 occurrence in {path}, found {n}:\n  {old[:90]!r}\n"
            "Nothing was written."
        )

# Apply against the preflighted text, then write once per file.
texts = dict(originals)
for path, old, new in EDITS:
    texts[path] = texts[path].replace(old, new, 1)

for path, text in texts.items():
    if "\ufeff" in text or "\r\n" in text:
        sys.exit(f"ABORT: {path} would carry a BOM or CRLF — the constitution plane must be byte-pristine.")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(f"edited {path}")
PY_EOF

trap - ERR

# ── verify ────────────────────────────────────────────────────────────────────────────────────
echo
echo "── verifying ──"
uv run pytest -q 2>&1 | tail -2
uv run python -m tools.contract_drift.drift >/dev/null && echo "contract-drift: exit 0"
uv run python -m tools.harness_emit >/dev/null && echo "harness-emit:   exit 0"

echo
echo "unsuperseded ADRs (expect 0013 only):"
git grep -n 'Superseded by:\*\* —' -- docs/adr/ || true

echo
echo "constitution-plane diff staged for review:"
git status --short -- docs/
echo
echo "Next: review the diff, then commit. CODEOWNERS ratifies at the merge."
