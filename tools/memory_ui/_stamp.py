"""Progress ``updated:`` stamp writer (Phase 16, MEM2-07, D-16-04 / RESEARCH Open-Q1).

The single write-path helper that refreshes the ``updated:`` frontmatter stamp on a committed
state file (``.memory/state/*.md``) when the UI saves an edit. It is composed from the shared
:func:`tools.harness_lint.parse_frontmatter` splitter plus a quoted-scalar YAML dump that mirrors
:func:`tools.agree.write._dump_frontmatter`, but quotes only the ``updated`` **value** (via
``DoubleQuotedScalarString``) — matching ``harness/commands/checkpoint.md``'s ``updated: "YYYY-MM-DD"``
form (unquoted key, quoted value) rather than the agreements' all-scalar-quoted style. The date
round-trips as a *string*, never a YAML date object.

Tier / determinism contract (T-16-12): the date is a **WRITE-path** value supplied by the caller
as ``today=``. This module NEVER reads a wall-clock at import time and is deliberately kept OUT of
any code path imported by :mod:`tools.memory_regen.inject` — the read path (``assemble``) stays
clock-free so delete-and-regenerate remains byte-identical.
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

from tools.harness_lint import parse_frontmatter


def _dump_frontmatter(frontmatter: dict) -> str:
    """Round-trip YAML dump preserving explicit ``DoubleQuotedScalarString`` value quoting.

    Mirrors :func:`tools.agree.write._dump_frontmatter` but leaves keys and untouched string
    values in their natural style so only the ``updated`` value carries quotes (checkpoint.md form).
    """
    yaml = YAML(typ="rt")
    yaml.default_flow_style = False
    stream = StringIO()
    yaml.dump(frontmatter, stream)
    dumped = stream.getvalue()
    if dumped.startswith("---\n"):
        dumped = dumped.removeprefix("---\n")
    return dumped.removesuffix("...\n")


def stamp_progress(path: str | Path, body_text: str, *, today: str) -> Path:
    """Rewrite a state file: set a quoted ``updated: "<today>"`` and replace the body.

    Reads the file, splits its frontmatter, sets ``updated`` to ``today`` (dumped as a quoted
    string so it does not deserialize into a YAML date object), preserves every other frontmatter
    key, and replaces the body with ``body_text``. ``today`` is injected by the caller — no
    wall-clock read lives here.

    Args:
        path: the state file to rewrite (must already exist).
        body_text: the new markdown body (everything after the closing fence).
        today: the ISO ``YYYY-MM-DD`` stamp, supplied by the write-path caller.

    Returns:
        The path written.
    """
    target = Path(path)
    frontmatter, _old_body = parse_frontmatter(target.read_text(encoding="utf-8"))
    frontmatter["updated"] = DoubleQuotedScalarString(today)
    target.write_text(
        f"---\n{_dump_frontmatter(frontmatter)}---\n\n{body_text}",
        encoding="utf-8",
        newline="\n",
    )
    return target
