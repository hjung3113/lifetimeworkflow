---
description: >-
  Use when you want to check formatting and lint before committing — runs ruff lint plus a
  ruff format check on the Python tree, a dotnet format check when the .NET SDK is present, and
  the POLY-01 polyglot boundary check (§4.3-4.6) over tracked *.tsv wire files. Invoke to catch
  style/format drift that the format-on-write hook would otherwise enforce, plus §4.3-4.6
  boundary violations (BOM/CRLF/column-shift/non-canonical cells) on the A-model wire files.
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

## Polyglot boundary (§4.3-4.6) — POLY-01

The in-session call site for the single POLY-01 rule engine (`tools.polyglot_lint.lint`) — the
SAME engine the on-write hook and the commit-gate call (one engine, three sites). It loops over
tracked `*.tsv` wire files and **fails loud** (non-zero) if any breaches §4.3-4.6 (BOM / CRLF /
column-shift / non-canonical decimal|datetime / leaked null sentinel). **Presence-safe**: zero
tracked `*.tsv` files → the loop is a no-op and the step exits 0 (never a false failure).

!`fail=0; files=$(git ls-files '*.tsv'); if [ -z "$files" ]; then echo "SKIP: no tracked *.tsv wire files — polyglot §4.3-4.6 check is a no-op (exit 0)."; else printf '%s\n' "$files" | while IFS= read -r f; do echo "polyglot-lint: $f"; done; for f in $files; do uv run python -m tools.polyglot_lint.lint "$f" || fail=1; done; if [ "$fail" -ne 0 ]; then echo "FAIL: polyglot §4.3-4.6 boundary violation(s) above — fix before committing (POLY-01)."; exit 1; fi; echo "OK: all tracked *.tsv wire files pass §4.3-4.6 (POLY-01)."; fi`

## Notes

- `ruff format --check` reports drift without rewriting; use the format-on-write hook to fix.
- The dotnet format check is **presence-gated** (announced skip when the SDK is absent).
- The polyglot §4.3-4.6 check reuses the POLY-01 engine (`tools.polyglot_lint.lint`) — the same
  engine wired on-write (contract-guard/format-on-write) and into the commit-gate; CI is Phase 5.
