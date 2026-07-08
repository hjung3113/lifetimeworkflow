"""strangler_guard — the CMD-06 ``/strangler-step`` baseline-refusal gate (D-05, Pitfall P10).

A virtual uv-workspace member (sibling of golden_runner/, docs_sync/, contract_hash/), invoked by
module path (``python -m tools.strangler_guard <target-path>``). It is the *runnable* half of
``/strangler-step``: before any legacy path is strangler-extracted it asserts that a captured legacy
golden **.verified** baseline exists for that path, and REFUSES outright (non-zero exit) when it does
not — a migration must never proceed without a trusted equivalence reference (T-03-24).

The refusal shape mirrors ``tools.golden_runner.approve.GoldenApprovalRefused`` (CLI exit 3):
"machines gate, humans ratify". The gate NEVER fabricates or creates a baseline — the human/golden
plane provides it; this module only checks and refuses. Extraction of one path only + mandatory
``/golden`` parity are enforced by the command macro (``harness/commands/strangler-step.md``).

The public API lives in :mod:`tools.strangler_guard.guard` (``require_baseline`` /
``StranglerRefused`` / ``main``); this package stays import-light so the test conftest can wire
``sys.path`` first.
"""
