#!/usr/bin/env bash
# memory-inject.sh — Claude SessionStart injector (HOOK-05, D-01/D-02).
#
# The 4th SessionStart slot (coexists with gsd-check-update.js, gsd-session-state.sh,
# tools/bootstrap/install.sh — overwrites nothing). Best-effort regenerates the derived plane,
# assembles the single injection contract (`tools.memory_regen.inject`), and emits the
# non-ignorable Claude envelope {hookSpecificOutput:{additionalContext}}.
#
# Command-injection defense (T-02-04): `set -euo pipefail`; the payload is passed to node via
# argv, NEVER interpolated into the shell/JSON string (mirrors gsd-session-state.sh discipline).
set -euo pipefail

# Resolve the project dir: prefer Claude's env var, else derive from this script's location so the
# hook is runnable standalone (tests, manual `bash .claude/hooks/memory-inject.sh`).
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && cd .. && pwd)}"
cd "$PROJECT_DIR"

# node: existing hooks use /opt/node22; fall back to PATH `node`.
NODE=node
command -v node >/dev/null 2>&1 || NODE=/opt/node22/bin/node

# Best-effort regenerate the derived plane. A missing Wave-2 generator (repo_map / contracts_index
# authored in 02-03/02-04) must NEVER break the hook — hence `|| true`. The assembler degrades
# gracefully when the derived files are absent.
uv run python -m tools.memory_regen.repo_map        >/dev/null 2>&1 || true
uv run python -m tools.memory_regen.contracts_index >/dev/null 2>&1 || true

# Assemble the capped, banner-first, priority-truncated payload (single injection contract, D-01).
PAYLOAD="$(uv run python -m tools.memory_regen.inject 2>/dev/null || echo '')"

# Node-encode so embedded newlines/quotes escape correctly; PAYLOAD via argv (no interpolation).
"$NODE" -e 'process.stdout.write(JSON.stringify({hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:process.argv[1]}}))' "$PAYLOAD"

exit 0
