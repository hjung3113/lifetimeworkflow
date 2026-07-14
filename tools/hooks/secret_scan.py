"""HOOK-02 secret_scan — PreToolUse gate that denies writing/reading secret material.

Two independent deny paths (either trips the gate):

1. **Path deny** — the target ``file_path`` is a secret file (``*.env`` / ``**/*.env``). This
   reuses the CONFIG-02 resolver (:func:`tools.harness_perms.resolve_path`) verbatim over a
   SECRET-SPECIFIC subset ``SECRET_PATH_GLOBS`` — **never** a hand-rolled glob matcher (D-02).

2. **Content deny** — the write ``content`` matches a shape-anchored secret pattern (AWS access
   key, PEM private-key header, or a conservative ``secret|token|api_key = <16+ chars>``
   assignment). Shape-anchored (not generic entropy) so the repo's own high-entropy fixtures do
   not trip it (Pitfall 5 / T-04-04); an ``ALLOWLIST_PREFIXES`` for ``tests/``, ``golden/``,
   ``libs/normalize-fixtures/`` further exempts fixture locations.

Composition invariant (04-06, Blocker-1 fix): secret_scan feeds the resolver only the SECRET
subset, NOT the full matrix constitution-plane deny list (which also lists ``contracts/**``,
``docs/adr/**``, ``golden/**``). The constitution plane is contract-guard's gate (04-03) and it
honors the GOLDEN_APPROVE_HUMAN bypass; if secret_scan denied that plane too, any-deny-wins
aggregation would shadow the bypass. So a constitution write with NO secret content is allowed
here. This module deliberately reads only ``SECRET_PATH_GLOBS`` — never the full matrix deny key.

Boundary: stdlib only (``re``/``json``/``sys``) + the reused resolver. No shell, no ``subprocess``
in the decision path (T-03-04 posture inherited). Malformed stdin is handled by ``_stdin`` and
maps to "no decision" (fail-open for THIS advisory gate — a broken payload has no file to guard).
"""

from __future__ import annotations

import json
import re

from tools.harness_perms import resolve_path
from tools.hooks._stdin import emit_deny, parse_event, read_stdin, repo_relative

# SECRET-specific path denies — the *.env subset ONLY. NOT the full matrix constitution deny key
# (see the composition invariant in the module docstring). Fed to the reused resolver (D-02).
SECRET_PATH_GLOBS = ["*.env", "**/*.env"]

# Fixture locations whose high-entropy sample data must NOT be flagged (Pitfall 5 / T-04-04).
ALLOWLIST_PREFIXES = ("tests/", "golden/", "libs/normalize-fixtures/")

# Shape-anchored secret patterns (A3). Anchored on structure, not Shannon entropy, to keep false
# positives near zero on the repo's own fixtures.
PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key id
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),  # PEM private-key header
    re.compile(r"(?i)(secret|token|api[_-]?key)\s*[:=]\s*\S{16,}"),  # assignment of a long value
]


def _allowlisted(file_path: str) -> bool:
    """True if ``file_path`` lives under a fixture allow-list prefix (leading ``./`` tolerated)."""
    normalized = file_path[2:] if file_path.startswith("./") else file_path
    return normalized.startswith(ALLOWLIST_PREFIXES)


def decide(file_path: str, content: str) -> dict | None:
    """Return a PreToolUse deny dict if ``file_path``/``content`` carries a secret, else ``None``.

    Deny when EITHER the path is a secret file (``resolve_path(SECRET_PATH_GLOBS, path) == "deny"``)
    OR the content matches a shape-anchored pattern and the path is not allow-listed. Constitution
    -plane paths with no secret content return ``None`` — that plane is not this gate's job.
    """
    # Normalize Claude's absolute file_path to repo-relative so both the *.env path-deny and the
    # tests/golden/fixtures allow-list match on a real absolute write (not just relative test input).
    relative_path = repo_relative(file_path)
    if relative_path and resolve_path(SECRET_PATH_GLOBS, relative_path) == "deny":
        return emit_deny(f"secret_scan: refusing to touch secret file path '{file_path}' (*.env)")

    if content and not _allowlisted(relative_path):
        for pattern in PATTERNS:
            if pattern.search(content):
                return emit_deny(
                    "secret_scan: content matches a secret shape "
                    f"({pattern.pattern[:24]}…); refusing to write it into '{file_path}'"
                )

    return None


def main() -> int:
    """PreToolUse entrypoint: parse stdin, apply :func:`decide`, print deny JSON on a hit.

    Always exits 0. On a hit, prints the deny decision to stdout (Claude blocks the tool call);
    otherwise prints nothing (normal permission flow). Malformed stdin -> safe sentinel -> no hit.
    """
    event = parse_event(read_stdin())
    result = decide(event.file_path, event.content)
    if result is not None:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
