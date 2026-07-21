# Phase 30 — orchestrator's independent verification of the drafts

Not a substitute for `30-VERIFICATION.md` (which comes at phase end). This records what the
orchestrator re-ran by hand against `drafts/`, because the drafting agent's own report is a
hypothesis, not evidence.

## What was re-run, and the result

| Check | Command | Result |
|-------|---------|--------|
| Schema is a valid Draft 2020-12 schema | `Draft202012Validator.check_schema(...)` | **OK** |
| Instance validates against it | `Draft202012Validator(sch).iter_errors(inst)` | **0 errors** |
| `constitution` globs vs live `contract_guard.CONSTITUTION_GLOBS` | element-wise, ordered | **match** |
| `secret` globs vs live `secret_scan.SECRET_PATH_GLOBS` | element-wise, ordered | **match** |
| `review-ledger` globs vs live `ledger_guard.REVIEW_LEDGER_GLOBS` | element-wise, ordered | **match** |
| Every domain declares `uncovered_tool_surfaces` containing `Bash` | instance read | **yes, all three** |
| `bypasses` values | driven, see below | **correct as declared** |

## The bypass claims were DRIVEN, not read

`ledger_guard.decide('docs/.docs-review-ledger.toml')` was called under four environments —
`{}`, `GOLDEN_APPROVE_HUMAN=tok`, `HARNESS_DEV_BYPASS=1`, and both together. **DENY in all four.**
`bypasses: []` for `review-ledger` is behaviourally true, not merely documented.

`secret_scan.py` and `ledger_guard.py` read **no** bypass environment variable anywhere in their
code — the only occurrences of `GOLDEN_APPROVE_HUMAN` / `HARNESS_DEV_BYPASS` in either file are in
docstrings explaining why they are NOT honoured. `bypasses: []` for `secret` is likewise true.

## A trap this exposed, for whoever executes 30-03

**`contract_guard`'s bypass does not live in `decide()`.** `decide(file_path, content, approved)`
takes `approved` as an ordinary parameter and reads no environment at all. The env → `approved`
mapping happens in `main()`:

```
tools/hooks/contract_guard.py:114-115
    token_present = bool((os.environ.get(APPROVAL_ENV) or "").strip())
    approved = token_present or dev_bypassed()
```

So a first attempt at driving this from the orchestrator — `monkeypatch.setenv(...)` then call
`decide(...)` — reported **DENY under both tokens**, which reads as "constitution honours no
bypass" and would have contradicted the draft. It is an artefact of calling the wrong function:
`decide(..., approved=True)` returns **ALLOW**, and `main()` is what turns the token into
`approved`.

`30-03-PLAN.md`'s check 5 says to prove bypass semantics by "DRIVING the hook:
`monkeypatch.setenv` then call the hook's own `decide()`/`main()` path". For `ledger_guard` and
`secret_scan`, `decide()` is sufficient — they read the environment nowhere, so any env-sensitivity
would have to appear there. **For `contract_guard`, `decide()` is NOT sufficient and must not be
used for this check**: it would prove only that a parameter the test itself passed was honoured.
Check 5 must drive `main()` for the constitution domain.

This is the same failure shape the phase-28 research recorded as P4 ("a token scan goes green on an
unused import") — a test that cannot fail when the thing under test is wrong. Recording it here so
the mutation proof for check 5 is written against `main()` and actually bites.

## Status

The drafts are **correct as far as they can be verified without landing them**. What remains is a
human write: `contracts/harness/security/deny-domains.{schema.json,json}` are on the constitution
plane, `contract_guard` denies the agent write, and the phase-30 plan explicitly refuses
`HARNESS_DEV_BYPASS` for it — that bypass is what produced RAT-4, which this milestone exists to
discharge. See `drafts/LANDING.md`.
