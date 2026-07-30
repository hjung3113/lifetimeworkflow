# Drafted review-ledger rows — HUMAN LANDS THESE, NOT AN AGENT

**ADR-0010 §3b:** an agent may PROPOSE a registry row; only a **human** may author a
`docs/.docs-review-ledger.toml` disposition, because the ledger — not the registry — is the
greenness authority. Nothing in phase 36 wrote to that file, and no
`GOLDEN_APPROVE_HUMAN` / `HARNESS_DEV_BYPASS` token was set at any point.

Both ids already have a `[[reviewed]]` row in `docs/.docs-review-ledger.toml`; these **replace**
those rows in place, they are not additions. `disposition = "updated"` is correct for row 1 and only
for row 1: `updated` is verified against the previous committed ledger and requires a target-digest
delta, which row 1 has (`fc10ff30f431…` → `da7694462b91…`) and row 2 does not.

Row shape read from the shipped `tools/docs_guard/ledger.py::_ROW_KEYS` at authoring time:
`{id, source_digest, target_digest, disposition}` — no more, no fewer; `ledger.py:198-203` rejects
both an extra and a missing key **by name**.

---

## Row 1 — `task-control-cli-howto` (required, currently the repo's known red)

**What the human is attesting.** That `docs/how-to/task-lifecycle.md` now describes the
task-control CLI accurately, including the discipline gate this phase added: which lanes owe which
disciplines, the `uv run python -m tools.discipline` invocation and its 0/1/3 exit routing, the
verbatim `FAIL: missing required disciplines: …` refusal, the `discipline: <id>` phase-gate refresh
reason, and what a discipline record must contain. The bounded edit is one new subsection under
step 2 (`### The lane's disciplines are refused, not suggested`); nothing else in the document was
touched.

**Prior state, disclosed.** This binding was **already** `STALE_REQUIRED` before phase 36 began —
phase 34's autofix moved a bound source digest and the ledger row was never landed. Phase 36 did not
cause that staleness and did not attempt to repair it; it did, however, genuinely change what the
target documents, so the target was updated rather than left to be reviewed against a document that
no longer matched the code.

```toml
[[reviewed]]
id            = "task-control-cli-howto"
source_digest = "86f06703852d84668f7b862ff93b994624c60bf1d3b03a0ffdac75cb2e6aaacd"
target_digest = "da7694462b913305638c113e9be6648b794c0b56d22df5e0b99211f4c0812f44"
disposition   = "updated"
```

---

## Row 2 — `lifecycle-eval-shadow-metrics` (advisory)

**What the human is attesting.** That none of the five shadow-metric definitions in
`docs/explanation/task-lifecycle-shadow-metrics.md` is falsified by this phase's changes to
`tools/risk_router/router.py` and `tools/lifecycle_eval/runner.py`.

**The review, stated so it can be disagreed with.** `lane_override` is untouched — human-override
validation and the override audit record are byte-identical. `gate_failure_reason`,
`evidence_completeness` and `handoff_reconstruction_time` have no relationship to the change.
`ceremony_count` is the only one worth arguing about: it counts **user-visible** checkpoints from the
evaluator's event list, and the runner's event list is unchanged — discipline materialization emits
no event. So the definition still matches its source. The document was therefore **not edited**;
manufacturing a diff to look diligent would be the dishonest option.

```toml
[[reviewed]]
id            = "lifecycle-eval-shadow-metrics"
source_digest = "2a12b08e54a6a95fefd6dfb5136922d67ea0cafa4ed9bca1c5e072c2f91f36dd"
target_digest = "d9ecd613c1c83ee2c00570bce81250cd3ea7de8376ee84f707331e0415653d20"
disposition   = "reviewed-no-change"
```

---

## Recomputing the digests at landing time

The digests above were computed at phase-36 HEAD. **Any later commit that touches a bound source or
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

Then `uv run python -m tools.docs_guard` should report both bindings `FRESH`, and its exit code
should be 0 provided no other binding has gone stale.

**Do not land these rows in the same commit as the change they ratify** if that commit is authored by
an agent: `first_seen-unratified` exists precisely to catch a binding blessed in the change that
created it.
