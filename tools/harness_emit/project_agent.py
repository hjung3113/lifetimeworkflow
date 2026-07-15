"""Agent frontmatter projection — opencode + Claude shapes (EMIT-02, the sole D-04 divergence).

The authored ``harness/agents/*.md`` frontmatter is DUAL-representation: one block carries BOTH the
opencode keys (``mode`` + the 15-key ``permission`` matrix) AND the Claude key (``tools`` allow).
The emitter's ONLY specialization is SELECTING which keys survive into each runtime's file — never
a transpile. Divergence is confined to the two key-order templates below (Mapping Table, RESEARCH):

| target   | keeps                                      | drops                       |
|----------|--------------------------------------------|-----------------------------|
| opencode | name, description, mode, permission, model | tools (Claude-only)         |
| Claude   | name, description, tools, model            | mode, permission (opencode) |

Selection preserves the SOURCE value verbatim (including the ``permission.bash`` sub-object's
AUTHORED insertion order — that order is semantic last-wins, ``*``-first, and must NOT be sorted,
Pitfall P3). The fixed key order here (not a ruamel round-trip) keeps re-emit byte-stable.
"""

from __future__ import annotations

# Fixed key order per target — the emitted frontmatter follows these sequences exactly so re-emit
# is deterministic (Pitfall P3). ``model`` is optional (placeholder tier only), kept when present.
_OPENCODE_KEYS = ("name", "description", "mode", "permission", "model")
_CLAUDE_KEYS = ("name", "description", "tools", "model")


def _project(fm: dict, keys: tuple[str, ...]) -> dict:
    """Select ``keys`` from ``fm`` in order, dropping absent/None values — values pass unchanged."""
    return {k: fm[k] for k in keys if k in fm and fm[k] is not None}


def to_opencode(fm: dict) -> dict:
    """Project authored frontmatter to the opencode shape (mode + permission; no ``tools``)."""
    return _project(fm, _OPENCODE_KEYS)


def to_claude(fm: dict) -> dict:
    """Project authored frontmatter to the Claude shape (tools; no ``mode``/``permission``)."""
    return _project(fm, _CLAUDE_KEYS)
