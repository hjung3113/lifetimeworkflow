---
description: >-
  Use when you want to check formatting and lint before committing — runs ruff lint plus a
  ruff format check on the Python tree and, when the .NET SDK is present, a dotnet format check.
  Invoke to catch style/format drift that the format-on-write hook would otherwise enforce.
agent: python-engineer
subtask: true
---

# /lint — lint + format check (dotnet-gated)

Thin macro over the canonical linters/formatters. Wraps the existing tools; adds no new rules.

## Python side

!`ruff check .`

!`ruff format --check .`

## .NET side (gated — skips gracefully when the SDK is absent, D-05)

Resolved via the explicit absolute bootstrap path (`$HOME/.dotnet/dotnet`). Absent SDK →
**announce and skip, never fail hard**:

!`if [ -x "$HOME/.dotnet/dotnet" ]; then "$HOME/.dotnet/dotnet" format --verify-no-changes; else echo "SKIP: .NET SDK not found at \$HOME/.dotnet/dotnet — skipping 'dotnet format' check (non-fatal)."; fi`

## Notes

- `ruff format --check` reports drift without rewriting; use the format-on-write hook to fix.
- The dotnet format check is **presence-gated** (announced skip when the SDK is absent).
