# DRAFT — proposed human review disposition for `task-control-cli-howto`

**Status: NOT APPLIED. This is a proposal for a human to author.**

`docs/.docs-review-ledger.toml` is human-authored only — its own header says so, and the rule is
ADR-0010 §3b: the ledger, not the registry, is the greenness authority, and `[[reviewed]]` carries
no reviewer field precisely because *the committing hand is the whole record*. An agent that lands
its own reviewed row has self-blessed a binding. So this file exists instead of the edit.

## What went stale, and why

Phase 34's commit `3bc21ea` (*style(tools): apply ruff's safe autofixes*) touched two of this
binding's three source files, which moved the combined source digest:

```
source 54e3b89ec1ed -> 4876a7c947a5
target fc10ff30f431 -> fc10ff30f431   (unchanged)
```

`git log` over the three sources confirms `3bc21ea` is the only commit since the recorded review,
so the staleness is entirely phase 34's.

## The review, performed

**Claim: the target document needs no edit.** The whole of `3bc21ea`'s diff to these files is
import statements:

- `tools/task_control/__main__.py` — one over-long `from tools.task_control.manager import ...`
  line wrapped into parenthesised form. **Identical set of names**: `TaskControlError, attest,
  block, create, refresh_ref, resume, show, transition, validate`.
- `tools/task_control/phase_gate.py` — the same wrapping, plus removal of `import json` and
  `from typing import Any`, both genuinely unused (grepped: nothing imports either name *from*
  this module).
- `tools/risk_router/intake.py` — **not touched at all** by `3bc21ea`.

`docs/how-to/task-lifecycle.md` is 71 lines and documents CLI invocations —
`uv run python -m tools.risk_router.intake --input ... --output ...` (:10),
`uv run python -m tools.task_control attest ... --attestation ...` (:20). No subcommand, flag,
argument or exit code changed, so there is nothing in the prose that has been left behind.

The correct disposition is therefore `reviewed-no-change`, not a document edit. Note also that
`updated` would be wrong here on the gate's own terms: it is verified against a **target**-digest
delta, and the target digest did not move.

Draftability was checked with the classifier rather than from memory:
`exclusion_reason("docs/how-to/task-lifecycle.md")` → `None`.

## The exact change for a human to make

In `docs/.docs-review-ledger.toml`, the row at line 86 — replace **only** the `source_digest`
line. Everything else stays byte-identical.

```diff
 id            = "task-control-cli-howto"
-source_digest = "54e3b89ec1ed4d2d45d1523568d1a2fa260431a983ffe123a1259a8788dfd98f"
+source_digest = "4876a7c947a51de7bd77374e9de09306f2d8044fc75c6cb9914ede2290a3b207"
 target_digest = "fc10ff30f431f0305b924d4ee03ad2a059c646248d1b037b3aeae9958fe67588"
 disposition   = "reviewed-no-change"
```

Both digests were read live, not copied from the report's 12-character prefixes:

```
uv run python -c "
from pathlib import Path
from tools.docs_guard.digest import compute
print(compute([Path(p) for p in ['tools/task_control/__main__.py','tools/task_control/phase_gate.py','tools/risk_router/intake.py']]))
print(compute([Path('docs/how-to/task-lifecycle.md')]))"
```
→ `4876a7c947a51de7...` and `fc10ff30f431f030...`, matching the guard's `4876a7c947a5` /
`fc10ff30f431`.

**Caveat on timing:** the source digest is a function of the working tree. If any of the three
source files changes again before the human commits, recompute with the command above rather than
pasting the value here.

## Deliberately NOT proposed

`[STALE_ADVISORY] lifecycle-eval-shadow-metrics` — also moved by `3bc21ea`
(`tools/lifecycle_eval/runner.py`), but advisory findings go to stderr and do not change the exit
code. The docs-upkeep loop is bounded to the exit-1 set; chasing advisory blocks turns it into a
backlog. Flagged, not acted on.

Nothing under `contracts/`, `docs/adr/`, `golden/` or `docs/glossary.md` is implicated.
