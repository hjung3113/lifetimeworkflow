---
description: >-
  Use when you need to compile the whole polyglot tree before a test or golden run — builds the
  .NET side (gated on the .NET SDK being present) and confirms the Python workspace resolves.
  Invoke after a parser/converter edit or before opening a PR to catch compile breakage early.
agent: orchestrator
subtask: true
---

# /build — compile the polyglot tree (dotnet-gated)

Thin macro over the canonical build commands. This command **wraps** the existing toolchain — it
does not re-implement any build logic.

## .NET side (gated — skips gracefully when the SDK is absent, D-05)

The .NET 10 SDK is resolved via the **explicit absolute bootstrap path** (`$HOME/.dotnet/dotnet`),
never a bare `PATH` lookup (the bootstrap PATH export does not persist across tool invocations).
When the SDK is absent (egress-blocked in this container, BOOT-01) the command **announces and
skips — it never fails hard**:

!`if [ -x "$HOME/.dotnet/dotnet" ]; then "$HOME/.dotnet/dotnet" build; else echo "SKIP: .NET SDK not found at \$HOME/.dotnet/dotnet — run 'bash tools/bootstrap/install.sh' once egress is allowed. Skipping 'dotnet build' (non-fatal)."; fi`

## Python side

The Python components are a `uv` workspace; a resolve/sync verifies the workspace is buildable:

!`uv sync --all-packages`

## Notes

- The dotnet path is **presence-gated** — a missing .NET SDK is an announced skip, not an error.
- No arguments are interpolated into a shell string; the wrapped CLIs run in list form.
