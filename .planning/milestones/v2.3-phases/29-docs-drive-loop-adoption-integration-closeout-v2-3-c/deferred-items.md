# Phase 29 — deferred items (out of scope for the plan that found them)

- **Pre-existing `E501` in `tools/harness_emit/tests/test_coexist.py`** (the
  `test_gsd_owned_claude_files_untouched_and_unlisted` docstring, 101 > 100 chars). Present at
  `HEAD` before plan 29-03 touched the file — verified by running ruff against the committed
  revision. 29-03 edits three unrelated literals in that file and deliberately does not reflow the
  docstring: it is not caused by this task's change. Same class as the pre-existing `I001` on
  `tools/adoption_apply/cli.py` carried in 29-CONTEXT D-15. Route to the v2.3 milestone audit's
  `tech_debt`.

- **Constitution-plane write-denies are spelled per-tool, and `bash."uv *"` is an unprompted
  `allow`.** Found by the phase-29 re-verification (2026-07-22), recorded nowhere before that.
  The ledger deny fires only on the `Write|Edit` tool matcher — `.claude/settings.json:160-168`
  registers `tools.hooks.ledger_guard` under `"matcher": "Write|Edit"`, and
  `.opencode/plugin/ledger-guard.ts:70` returns early unless `input.tool` is `write`/`edit`. But
  `harness/permission-matrix.json:9` grants `"uv *": "allow"`, so
  `resolve_bash(..., "uv run python -c \"open('docs/.docs-review-ledger.toml','w')...\"")`
  resolves to **`allow`** — the same write, spelled through bash, is not denied. `contract_guard`
  shares the shape, so `contracts/**` and `golden/**` inherit the identical route.
  **Scope of the finding:** SC-2 is unaffected (it is about `/adopt`, which refuses in code) and
  SC-3 is unaffected (the gate itself is green and was observed moving). The one statement that IS
  overclaimed is the prior 29-VERIFICATION.md line "no agent action can satisfy SC-3" — true of
  `Write`/`Edit`, not of every tool.

  **CORRECTION (2026-07-22, external review by codex sol).** This entry originally also accused
  ADR-0010 clause 3b of "universal phrasing". That accusation was WRONG and is withdrawn. Clause 3b
  names the surface each of its three layers covers and scopes layer 1 explicitly to
  `PreToolUse(Write|Edit)` (`docs/adr/0010-human-docs-review-obligation-model.md:144-152`); it makes
  no universal claim, and it even records the principle this finding rests on — "a layer that is
  only a data row is a claimed control that does not exist". The defect is therefore a **missing
  FOURTH deny layer for the bash surface**, and the remedy is a new layer plus a superseding ADR
  that states the residual, NOT a correction to clause 3b's wording.
  **Disposition (human, 2026-07-22): record only; repair in the next milestone.** Repairing a gate
  during its own closeout is the wrong discipline, and the fix is harness-wide (a PreToolUse `Bash`
  hook that denies constitution-plane writes independent of spelling), not phase-29-shaped. Route to
  the v2.3 milestone audit's `tech_debt`. Per the correction above, the paired ADR work is a
  SUPERSEDING ADR that records the newly covered surface and the residual — not an edit to, or a
  reproach of, clause 3b.

  **Sol's caution on the remedy (2026-07-22), carried into v2.4 planning.** "A Bash hook cannot
  generally resolve the effective write target" of arbitrary shell — interpreters, build tools,
  subprocesses, symlinks and generated scripts all defeat static command-text inference. So
  "spelling-independent" must NOT be adopted as an acceptance criterion without first choosing an
  enforceable posture: filesystem-level enforcement, a constrained command allowlist, protected
  command wrappers, or an explicitly documented residual boundary. Otherwise the negative-control
  suite proves only the spellings its authors happened to remember.
