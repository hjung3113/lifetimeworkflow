---
description: >-
  Use when you need to run the full test suite after a change — runs the Python pytest suite and,
  when the .NET SDK is present, the .NET tests too. Invoke before every commit and before promoting
  a golden to confirm the golden/contract gates stay green.
agent: orchestrator
subtask: true
---

# /test — run the full test suite (dotnet-gated)

Thin macro over the canonical test runners. Wraps the existing suites; adds no new test logic.

## Python side

!`uv run pytest`

## .NET side (gated — skips gracefully when the SDK is absent, D-05)

Resolved via the explicit absolute bootstrap path (`$HOME/.dotnet/dotnet`). When the .NET SDK is
absent the command **announces and skips — never fails hard** (BOOT-01 egress deferral):

!`if [ -x "$HOME/.dotnet/dotnet" ]; then "$HOME/.dotnet/dotnet" test; else echo "SKIP: .NET SDK not found at \$HOME/.dotnet/dotnet — run 'bash tools/bootstrap/install.sh' once egress is allowed. Skipping 'dotnet test' (non-fatal)."; fi`

## Notes

- The dotnet path is **presence-gated**: a missing .NET SDK is an announced skip, not a failure.
- `uv run pytest` is the in-container "runtime" gate — it must stay green.
