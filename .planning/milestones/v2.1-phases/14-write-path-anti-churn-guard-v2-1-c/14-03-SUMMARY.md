# Plan 14-03 — Summary

**Status:** complete · **Executed by:** Codex (gpt-5.6-terra, medium)
**Commits:** `f7958ec` feat: add refusal-first agreement writer · `d977277` test: cover agreement write refusal · `104cecd` feat: add agree command source
**Follow-up by Claude:** `fa1aea8` test: bump emitted-command count 19 → 20 (see Deviation below)

## What shipped

New `tools/agree/` uv member (D-19 — `tools/memory_regen` is forbidden as the writer by the tier's
own contract, `.memory/agreements/README.md:4-5`). `write.py` exposes `add()` / `retire()` /
`AgreementRefused` / `main()`, mirroring `approve.py`'s refusal-then-exit-3 convention.
`harness/commands/agree.md` authored — SOURCE ONLY.

## Verified by execution, not only by tests

Exercised against a temp dir (never the real `.memory/agreements/`):

- **D-07:** `--because` omitted / empty / whitespace-only → all three **REFUSED**, exit 3.
- **D-08:** no `GOLDEN_APPROVE_HUMAN` required — `--because` is the gate. Agreements are
  deliberately not constitution plane.
- **D-15:** injecting `x"\nstatus: "retired` through `--because` yields frontmatter keys exactly
  `[added, provenance, status]` with `status: 'active'` — **the forged sibling key does not appear.**
  `ruamel.yaml` serialization, never an f-string.
- **D-02 round-trip:** output carries `"added": "2026-07-16"` (quoted → `str`), and the writer's own
  output passes the 14-02 lint.
- **D-09:** `retire()` flips `status` in place; the file survives.
- **D-11:** no `EXPECTED_COMMANDS` invented — it does not exist. `test_commands.py` is glob-driven
  and covered `agree.md` with zero test edits, as designed.

## Deviation — D-10 was wrong, and the error was mine (Claude's, in CONTEXT)

D-10 claimed staying source-only would hold `test_coexist` at 19 emitted commands. **False.**
`_emit(tmp_path)` projects from the runtime-neutral SOURCE into a temp dir and counts there — it
never reads the committed trees. So authoring `harness/commands/agree.md` bumps the count to 20
immediately, emit or no emit. The suite went to **2 failed** the moment the command existed.

Resolved (operator-ratified) by bumping the count 19 → 20 here rather than deferring to Phase 15:
the change is *forced* by Phase 14's own source edit, and it does **not** touch the `.ambr` snapshot.
Phase 15's actual gate — `test_projected_tree_matches_committed_snapshot` — remains red on purpose.

Process note: the planner planned around D-10 and the plan-checker "verified" it; both read the
`== 19` assertion without tracing `_emit`. It surfaced only when the code ran. This is the same
claimed-but-unverified failure mode this phase keeps cataloguing — this time committed by the
orchestrator.
