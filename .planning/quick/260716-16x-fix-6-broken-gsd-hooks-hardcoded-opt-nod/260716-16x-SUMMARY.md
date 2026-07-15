---
quick_id: 260716-16x
type: execute
status: complete
completed: 2026-07-16
tasks_completed: 2
tasks_total: 2
requirements: [QUICK-260716-16x]
key-files:
  modified:
    - .claude/settings.json
commits:
  - 085064c: "fix(quick-260716-16x): resolve node via PATH in 6 GSD hook commands"
metrics:
  files_modified: 1
  lines_changed: 6 insertions / 6 deletions
---

# Quick Task 260716-16x: Fix 6 Broken GSD Hooks (hardcoded /opt/node22) — Summary

Restored six silently-inert GSD guard hooks by replacing the container-only interpreter path
`/opt/node22/bin/node` with `$(command -v node || echo /opt/node22/bin/node)`, mirroring the
`memory-inject.sh:18-20` precedent so the remote Linux container keeps working.

## What Changed

`.claude/settings.json` — 6 `command` strings, edited in place via targeted Edit calls
(each anchored on its unique script filename):

| Line | Event | Hook |
|------|-------|------|
| 8 | SessionStart `*` | `gsd-check-update.js` |
| 43 | PostToolUse `Bash\|Edit\|Write\|MultiEdit\|Agent\|Task` | `gsd-context-monitor.js` |
| 53 | PostToolUse `Read` | `gsd-read-injection-scanner.js` |
| 85 | PreToolUse `Write\|Edit` | `gsd-prompt-guard.js` |
| 95 | PreToolUse `Write\|Edit` | `gsd-read-guard.js` |
| 105 | PreToolUse `Write\|Edit` | `gsd-workflow-guard.js` |

Untouched: the `bash ...` hooks, the `uv run python ...` hooks, all `timeout` values, key order,
indentation. No keys added or removed. File was **not** re-serialized.

## Verification

**Task 1 — structural gate: PASS**

```
bare "/opt/node22/bin/node" form ....... 0   (want 0)
command -v node fallback expression .... 6   (want 6)
python3 json.load ...................... VALID JSON
git diff --numstat ..................... 6  6  .claude/settings.json
```

The 6/6 numstat is the load-bearing proof that only the 6 command strings changed — a
read-modify-write or `json.dump` re-serialization would have flapped ~274 lines
(`_merge_settings_json` omits `sort_keys` precisely because the file is insertion-ordered).

**Task 2 — behavioral gate: PASS**

A grep-only check would pass even on a still-broken hook, since the bug's signature was
"looked configured, silently did nothing". So execution was proven directly.

Interpreter resolution, extracted from settings.json and evaluated the same way the shell does —
all 6 resolve to a real node:

```
gsd-check-update.js            -> /opt/homebrew/opt/node@22/bin/node   v22.22.2
gsd-context-monitor.js         -> /opt/homebrew/opt/node@22/bin/node   v22.22.2
gsd-read-injection-scanner.js  -> /opt/homebrew/opt/node@22/bin/node   v22.22.2
gsd-prompt-guard.js            -> /opt/homebrew/opt/node@22/bin/node   v22.22.2
gsd-read-guard.js              -> /opt/homebrew/opt/node@22/bin/node   v22.22.2
gsd-workflow-guard.js          -> /opt/homebrew/opt/node@22/bin/node   v22.22.2
```

All 6 `.js` files confirmed present on disk (a renamed script cannot masquerade as a fixed hook).

**Before/after control** — isolates the fix as the cause of the behavior change:

```
OLD form: "/opt/node22/bin/node" .../gsd-read-guard.js
  -> no such file or directory: /opt/node22/bin/node   (rc=127)

NEW form: all 6 hooks invoked end-to-end over stdin with a real hook payload
  -> ran (rc=0), no interpreter error
```

**Proof the guard reaches a real decision** (not merely a different flavor of no-op): every hook
initially returned rc=0 with no output. Investigation of `gsd-read-guard.js:53-61` showed this is a
*deliberate* early-exit — the hook detects Claude Code via `session_id` / `CLAUDE_CODE_ENTRYPOINT`
and exits 0 by design. The verification shell inherits that env, so rc=0 was correct behavior, not
failure. With the detection env cleared, the hook emits its real advisory:

```json
{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":
"READ-BEFORE-EDIT REMINDER: You are about to modify \"AGENTS.md\" which already exists..."}}
```

The guard rails are live on this host.

## Portability

The fix is not macOS-only — it inverts nothing. `command -v node` resolves PATH node on macOS;
where PATH has no node (the remote Linux container), it falls back to `/opt/node22/bin/node`.
Both environments work from one string.

`_merge_settings_json` (`tools/harness_emit/generate.py:270-288`) append-or-replaces only
harness-signature hook groups and never touches or reorders GSD hooks, so a `harness_emit`
re-emit will not revert this fix.

## Deviations from Plan

None — plan executed exactly as written. No deviation rules triggered.

## Out of Scope / Untouched

- `tools/harness_emit` snapshot test `test_projected_tree_matches_committed_snapshot` remains red:
  **1 failed / 46 passed**, identical to the pre-existing clean-tree state. Inherited from Phase 12's
  deferred re-emit; belongs to Phase 15. Not fixed, `.ambr` not regenerated.
- `.claude/hooks/memory-inject.sh` — the precedent, not a target. Unmodified.
- `harness/` — these GSD hooks are not emitted from there. Unmodified.
- `.planning/phases/02-*/02-RESEARCH.md`, `.planning/phases/04-*/04-RESEARCH.md` — historical
  records mentioning `/opt/node22`. Unmodified.
- `.planning/config.json` was already dirty before execution began (not from this task; not staged).

## Threat Model Outcome

| Threat ID | Disposition | Outcome |
|-----------|-------------|---------|
| T-16x-01 (EoP via command substitution) | accept | Substitution contains only literals, no tool/user-controlled input; `command -v` is a shell builtin. Same trust level as existing `bash`/`uv run` hooks. |
| T-16x-02 (PATH tampering) | accept | Attacker able to prepend PATH already controls the session; identical exposure to the `uv run python` hooks and the `memory-inject.sh` precedent. |
| T-16x-03 (silent hook no-op — the bug) | mitigate | **Mitigated and verified.** Task 2's behavioral gate + before/after control prove execution; a string-only fix could not have passed. |
| T-16x-SC (package installs) | n/a | No packages installed; JSON config edit only. |

No new threat surface introduced.

## Self-Check: PASSED

- `.claude/settings.json` exists and is valid JSON — verified
- Commit `085064c` exists in `git log` — verified
- `git diff --stat` for the commit touches only `.claude/settings.json` — verified
- No file deletions in the commit — verified
