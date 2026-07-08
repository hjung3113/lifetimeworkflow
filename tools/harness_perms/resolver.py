"""Pure, stdlib-only permission resolver (CONFIG-02, D-03).

The harness's access-control core. Two pure functions plus a thin loader, no I/O beyond reading
the matrix JSON, **no ``eval``, no ``subprocess``, no shell** (T-03-04). Reused verbatim by the
Phase-4 contract-guard / secret hooks — keep the signatures stable.

Semantics:
  * ``resolve_bash`` — opencode last-wins glob: iterate the authored (insertion-ordered) rules and
    keep the decision of the LAST pattern that matches the command line. The catch-all ``*`` is
    authored FIRST so specifics override it; never end the matrix with a broad ``allow`` (P3).
  * ``resolve_path`` — path-scoped deny for the constitution/secret planes (``contracts/**``,
    ``docs/adr/**``, ``golden/**``, ``*.env``): ``deny`` if any glob matches, else ``allow``.

Default posture is deny-by-caution: an unmatched command falls through to the ``default`` verb
(``"ask"``), so nothing is silently allowed.
"""

from __future__ import annotations

import json
from fnmatch import fnmatchcase
from pathlib import Path

# "allow" | "ask" | "deny"
Decision = str

# Repo-root-anchored default so the loader works regardless of the caller's cwd.
# resolver.py -> harness_perms -> tools -> repo root (parents[2]).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_MATRIX = _REPO_ROOT / "harness" / "permission-matrix.json"


def resolve_bash(rules: dict[str, Decision], command: str, default: Decision = "ask") -> Decision:
    """Return the last-matching glob's decision for ``command`` (opencode last-wins semantics).

    ``rules`` is an insertion-ordered mapping of ``glob -> decision`` (Python 3.7+ dicts preserve
    order); author ``*`` first and specifics after. Iterates ALL rules — never breaks on the first
    match — so a later, more specific pattern overrides an earlier one. Unmatched ⇒ ``default``.
    """
    decision = default
    for pattern, verb in rules.items():
        if fnmatchcase(command, pattern):
            decision = verb  # LAST match wins — deliberately do not break.
    return decision


def resolve_path(deny_globs: list[str], path: str) -> Decision:
    """``"deny"`` if ``path`` matches any constitution/secret deny glob, else ``"allow"``."""
    return "deny" if any(fnmatchcase(path, glob) for glob in deny_globs) else "allow"


def load_matrix(path: str | Path = _DEFAULT_MATRIX) -> dict:
    """Load the CONFIG-02 permission matrix JSON. Shared by tests and Phase-4 hooks so there is
    exactly one loader. Preserves key order (last-wins depends on it)."""
    return json.loads(Path(path).read_text(encoding="utf-8"))
