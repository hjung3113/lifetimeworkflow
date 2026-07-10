"""The shared session-start injection assembler (HOOK-05, D-01/D-02/D-07).

`assemble()` is the ONE payload source both runtimes honor (D-01, single injection contract):

* Claude (implemented now)  — `.claude/hooks/memory-inject.sh` wraps stdout in
  ``{hookSpecificOutput:{additionalContext}}`` (non-ignorable SessionStart injection, D-02).
* opencode (authored, deferred) — ``harness/plugins/session-inject.ts`` shells out to this SAME
  module (``python -m tools.memory_regen.inject``) from ``chat.system.transform``.

The payload is a capped (~1k-token / ≤4000-char, D-07), banner-first, drift-aware, pointer-only
orientation string. Priority order:

    (0) provisional banner   — NEVER dropped (D-02)
    (1) live drift summary   — NEVER dropped (reuses tools.contract_drift.run_gate)
    (2) contracts-index summary   (head of .memory/derived/contracts-index.md if present)
    (3) repo-map top-N            (head of .memory/derived/repo-map.md if present, else omitted)
    (4) activeContext POINTER     (path + one-line note — never the file body, P13)

Over budget → whole low-priority sections are dropped in reverse-priority order
(priority-truncate, NOT blind mid-line cutting, D-07). The payload injects index summaries and
pointers only — never a full contract schema body (T-02-06). No timestamps, no secrets, so the
output is deterministic (delete+regen identical).
"""

from __future__ import annotations

import sys
from pathlib import Path

from tools.contract_drift.drift import run_gate

# --- paths (derived plane is gitignored + regenerated; state plane is committed) --------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
DERIVED_DIR = _REPO_ROOT / ".memory" / "derived"
STATE_DIR = _REPO_ROOT / ".memory" / "state"

# How many head lines of a derived summary file to fold into the payload (budget still caps).
_HEAD_LINES = 20

# --- section constants (stable text — part of the injection contract) -------------------------
BANNER = (
    "PROVISIONAL — volatile session state below is a hint, not truth. "
    "contracts/ and docs/adr/ (ADR) ALWAYS override .memory/ on conflict."
)
DRIFT_HEADER = "## Contract drift (live)"
CONTRACTS_HEADER = "## Contracts index (summary)"
REPO_MAP_HEADER = "## Repo map (top-N)"
ACTIVE_HEADER = "## Active context (pointer)"


# --- section builders -------------------------------------------------------------------------


def _drift_summary() -> str:
    """Compact live drift status via tools.contract_drift.run_gate — never any schema body."""
    try:
        gate = run_gate()
    except Exception:  # pragma: no cover - degrade gracefully if the gate is unavailable
        return f"{DRIFT_HEADER}\ncontract-drift: unknown (gate unavailable)"
    if gate["ok"]:
        return f"{DRIFT_HEADER}\ncontract-drift: clean (live manifest matches baseline)"
    lines = [f"- {rel} [{kind}/{cls}]" for rel, kind, cls in gate["drifted"]]
    return (
        f"{DRIFT_HEADER}\ncontract-drift: DRIFT — {len(gate['drifted'])} schema(s):\n"
        + "\n".join(lines)
    )


def _read_head(path: Path) -> str:
    """Return the first _HEAD_LINES lines of a text file, or '' if unreadable/absent."""
    try:
        return "\n".join(path.read_text(encoding="utf-8").splitlines()[:_HEAD_LINES])
    except OSError:  # pragma: no cover - absent file is the common (pending) path
        return ""


def _contracts_summary(derived_dir: Path = DERIVED_DIR) -> str:
    """Head of the contracts-index derived file if present, else a short 'pending' pointer."""
    head = _read_head(Path(derived_dir) / "contracts-index.md")
    if head:
        return f"{CONTRACTS_HEADER}\n{head}"
    return (
        f"{CONTRACTS_HEADER}\n"
        "(contracts-index pending — run `python -m tools.memory_regen.contracts_index`)"
    )


def _repo_map_topN(derived_dir: Path = DERIVED_DIR) -> str:
    """Head of the repo-map derived file if present, else '' (section omitted entirely)."""
    head = _read_head(Path(derived_dir) / "repo-map.md")
    return f"{REPO_MAP_HEADER}\n{head}" if head else ""


def _active_context_pointer(state_dir: Path = STATE_DIR) -> str:  # noqa: ARG001 (path is fixed)
    """A POINTER to activeContext — path + one-line note, NEVER the file body (P13)."""
    return (
        f"{ACTIVE_HEADER}\n"
        ".memory/state/activeContext.md — volatile; confirm against contracts/ADR before trusting."
    )


# --- the shared contract ----------------------------------------------------------------------


def assemble(
    budget_chars: int = 4000,
    derived_dir: Path = DERIVED_DIR,
    state_dir: Path = STATE_DIR,
) -> str:
    """Assemble the capped, banner-first, priority-truncated injection payload.

    ``budget_chars`` is a soft ~1k-token cap (char/4 heuristic, D-07). Sections are emitted in
    priority order; any section that is NOT the banner or drift is skipped whole when including it
    would exceed the budget (priority-truncate, never mid-line). Banner (0) and drift (1) are
    always present — even below their combined size — because they carry the non-ignorable
    provisional invariant and the live safety signal.
    """
    sections = [
        ("banner", BANNER),
        ("drift", _drift_summary()),
        ("contracts", _contracts_summary(derived_dir)),
        ("repomap", _repo_map_topN(derived_dir)),
        ("active", _active_context_pointer(state_dir)),
    ]
    out: list[str] = []
    used = 0
    for name, text in sections:
        if not text:
            continue
        addition = len(text) + (1 if out else 0)  # +1 for the joining newline
        if name not in ("banner", "drift") and used + addition > budget_chars:
            continue  # priority-truncate this whole low-priority section
        out.append(text)
        used += addition
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    """CLI: print the assembled payload to stdout (`python -m tools.memory_regen.inject`)."""
    argv = sys.argv[1:] if argv is None else argv  # noqa: F841 (reserved for future flags)
    sys.stdout.write(assemble())
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
