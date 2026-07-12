"""Command frontmatter projection — opencode + Claude shapes (EMIT-02, the sole D-04 divergence).

The authored ``harness/commands/*.md`` frontmatter carries ``description`` (a routing paragraph),
``agent`` (the slug the command routes to), and — when present — ``subtask`` (a boolean). The
``` !`shell` ``` + ``$ARGUMENTS`` body is shared VERBATIM by both runtimes; the emitter's ONLY
specialization is SELECTING which frontmatter keys survive into each runtime's file:

| target   | keeps                        | drops                                    |
|----------|------------------------------|------------------------------------------|
| opencode | description, agent, subtask  | —                                        |
| Claude   | description                  | agent, subtask (no Claude equivalent)    |

Selection preserves each SOURCE value verbatim; the fixed key order here (not a ruamel round-trip)
keeps re-emit byte-stable, exactly like ``project_agent``.
"""

from __future__ import annotations

# Fixed key order per target — the emitted frontmatter follows these sequences exactly so re-emit
# is deterministic (Pitfall P3). ``subtask`` is optional (kept only when the source declares it).
_OPENCODE_KEYS = ("description", "agent", "subtask")
_CLAUDE_KEYS = ("description",)


def _project(fm: dict, keys: tuple[str, ...]) -> dict:
    """Select ``keys`` from ``fm`` in order, dropping absent/None values — values pass unchanged."""
    return {k: fm[k] for k in keys if k in fm and fm[k] is not None}


def to_opencode(fm: dict) -> dict:
    """Project a command's frontmatter to the opencode shape (description + agent + subtask)."""
    return _project(fm, _OPENCODE_KEYS)


def to_claude(fm: dict) -> dict:
    """Project a command's frontmatter to the Claude shape (description only; no agent/subtask).

    Claude slash-commands have no ``agent``/``subtask`` equivalent, so those opencode-only keys are
    dropped — never transpiled to a Claude concept that does not exist.
    """
    return _project(fm, _CLAUDE_KEYS)
