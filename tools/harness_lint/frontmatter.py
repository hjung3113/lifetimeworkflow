"""Shared markdown YAML-frontmatter parser (D-02/D-04/D-07).

The single frontmatter reader every downstream structural validator reuses (Plans 03/04/05 —
agent, command, and skill lints). Parsing lives here ONCE so the agent/command/skill validators
never re-implement fence slicing (Don't-Hand-Roll: one shared parser, not string slicing per test).

Uses ruamel.yaml (already resolved in the workspace env via check-jsonschema) — NOT pyyaml, which
is absent from the lock. The ``safe`` loader is used: no arbitrary object construction from
untrusted markdown frontmatter (V5 input validation).

Public API::

    from tools.harness_lint import parse_frontmatter
    frontmatter_dict, body_text = parse_frontmatter(md_text)
"""

from __future__ import annotations

import io

from ruamel.yaml import YAML

_FENCE = "---"


def parse_frontmatter(md_text: str) -> tuple[dict, str]:
    """Split a markdown document into (frontmatter_dict, body_text).

    The frontmatter is the YAML block delimited by a leading ``---`` fence and a closing ``---``
    fence. When no leading fence is present, returns ``({}, md_text)`` unchanged.

    Args:
        md_text: full markdown source, optionally starting with a ``---`` YAML frontmatter block.

    Returns:
        (frontmatter, body) where ``frontmatter`` is the parsed mapping (``{}`` when absent or
        empty) and ``body`` is everything after the closing fence.
    """
    # Normalize line endings so the fence scan is CRLF-safe (boundary invariant §4.3).
    text = md_text.replace("\r\n", "\n").replace("\r", "\n")

    lines = text.split("\n")
    if not lines or lines[0].strip() != _FENCE:
        return {}, md_text

    # Find the closing fence (first `---` on its own line after the opening fence).
    for idx in range(1, len(lines)):
        if lines[idx].strip() == _FENCE:
            yaml_block = "\n".join(lines[1:idx])
            body = "\n".join(lines[idx + 1 :])
            data = _load_yaml(yaml_block)
            return data, body

    # Opening fence with no closing fence — treat as no frontmatter (fail safe, don't guess).
    return {}, md_text


def _load_yaml(block: str) -> dict:
    """Parse a YAML block into a plain dict via ruamel's safe loader ( ``{}`` on empty)."""
    yaml = YAML(typ="safe")
    loaded = yaml.load(io.StringIO(block))
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError("frontmatter block did not parse to a mapping")
    # ruamel returns plain dict for typ="safe"; coerce defensively for a stable public contract.
    return dict(loaded)
