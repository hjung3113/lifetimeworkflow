# Drafted review-ledger rows — HUMAN LANDS THESE, NOT AN AGENT

**ADR-0010 §3b:** an agent may PROPOSE a registry row; only a **human** may author a
`docs/.docs-review-ledger.toml` disposition, because the ledger — not the registry — is the
greenness authority. Nothing in phase 37 wrote to that file, and no `GOLDEN_APPROVE_HUMAN` /
`HARNESS_DEV_BYPASS` token was set at any point.

**These SUPERSEDE the two rows drafted in `.planning/phases/36-*/drafts/ledger-rows.md`.** Both
bindings were already the repo's known red before phase 37 began (phase 34's autofix moved a source
digest and the row was never landed); phase 37 did not cause that staleness and did not repair it.
It did, however, move both bindings again — one source digest and one target digest — so the
phase-36 drafts would now be refused as stale. Land these, not those. Both ids already have a
`[[reviewed]]` row in the ledger; these **replace** those rows in place.

Row shape read from the shipped `tools/docs_guard/ledger.py::_ROW_KEYS`:
`{id, source_digest, target_digest, disposition}` — no more, no fewer; an extra or missing key is
rejected by name.

---

## Row 1 — `task-control-cli-howto` (required, the repo's known red)

**What changed since the phase-36 draft.** The three bound *sources*
(`tools/task_control/__main__.py`, `tools/task_control/phase_gate.py`, `tools/risk_router/intake.py`)
are **untouched by phase 37** — the source digest is byte-identical to the phase-36 draft
(`86f06703…`). Only the *target* moved, because phase 37 made a bounded edit to it.

**What the human is attesting.** That `docs/how-to/task-lifecycle.md` describes the task-control CLI
accurately, including — new in phase 37 — that a discipline record must name the `agent` that did
the work, that the declaration names a **capability** rather than a persona, that
`harness/capabilities.toml` holds the allowlist, that
`uv run python -m tools.capability route <capability> <agent>` exits 3 when refused, and the
verbatim per-seat refusal an out-of-allowlist panel seat produces.

**The bounded edit, stated so it can be checked.** One paragraph in
`### The lane's disciplines are refused, not suggested` gained `agent`/per-seat wording, followed by
one new paragraph and two new code blocks. Nothing else in the document was touched; no other
section, heading or example moved.

```toml
[[reviewed]]
id            = "task-control-cli-howto"
source_digest = "86f06703852d84668f7b862ff93b994624c60bf1d3b03a0ffdac75cb2e6aaacd"
target_digest = "f38938e154e2214ec2ab0ac303a75a73816ba6d9b0eb21be9449cba0333a89d6"
disposition   = "updated"
```

`updated` is correct and is verified against the previous committed ledger: it requires a
target-digest delta, which this row has.

---

## Row 2 — `lifecycle-eval-shadow-metrics` (advisory)

**What changed since the phase-36 draft.** The bound source `tools/lifecycle_eval/runner.py` moved
again in phase 37 (`2a12b08e…` → `023368e3…`): `_materialize_required_disciplines` now resolves the
record's `agent` from the declared capability's allowlist instead of omitting it.
`tools/risk_router/router.py` is untouched. The target is unchanged.

**The review, stated so it can be disagreed with.** None of the five shadow-metric definitions in
`docs/explanation/task-lifecycle-shadow-metrics.md` is falsified by that change.

- `lane_override` — untouched; human-override validation and the override audit record are
  byte-identical.
- `ceremony_count` — the one worth arguing about. It counts **user-visible** lifecycle checkpoints
  from the evaluator's event list. Materializing a record's `agent` field emits no event and adds no
  checkpoint, so the count is unchanged. Capability routing does not introduce a new gate a user
  passes through; it constrains who may pass through an existing one.
- `gate_failure_reason` — arguably touched, and it is not. The new refusal
  (`… not allowed to serve capability …`) is a new *message*, but the definition is "stable tool
  error category emitted by an existing gate", and the category is the existing
  `missing required disciplines` from the existing transition gate. No new category exists.
- `evidence_completeness`, `handoff_reconstruction_time` — no relationship to the change.

The document was therefore **not edited**. Manufacturing a diff to look diligent would be the
dishonest option.

```toml
[[reviewed]]
id            = "lifecycle-eval-shadow-metrics"
source_digest = "023368e34a1be7b84fce15d199858e96cf16ae9e83755b599fd9674d72da12c8"
target_digest = "d9ecd613c1c83ee2c00570bce81250cd3ea7de8376ee84f707331e0415653d20"
disposition   = "reviewed-no-change"
```

---

## Recomputing the digests at landing time

The digests above were computed at phase-37 HEAD. **Any later commit that touches a bound source or
target moves them**, and a row landed with a stale digest is refused. Recompute immediately before
landing:

```sh
uv run python - <<'PY'
from pathlib import Path
from tools.docs_guard import digest
root = Path(".").resolve()
rows = {
 "task-control-cli-howto": (
   ["tools/task_control/__main__.py", "tools/task_control/phase_gate.py",
    "tools/risk_router/intake.py"],
   "docs/how-to/task-lifecycle.md"),
 "lifecycle-eval-shadow-metrics": (
   ["tools/lifecycle_eval/runner.py", "tools/risk_router/router.py"],
   "docs/explanation/task-lifecycle-shadow-metrics.md"),
}
for name, (sources, target) in rows.items():
    print(name)
    print('  source_digest = "%s"' % digest.compute(digest.resolve(sources, root), root))
    print('  target_digest = "%s"' % digest.compute(digest.resolve([target], root), root))
PY
```

Then `uv run python -m tools.docs_guard` should report both bindings `FRESH` and exit 0, provided no
other binding has gone stale.

**Do not land these rows in the same commit as the change they ratify** if that commit is authored by
an agent: `first_seen-unratified` exists precisely to catch a binding blessed in the change that
created it.
