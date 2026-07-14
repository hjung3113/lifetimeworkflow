"""HOOK-04 contract-guard — PreToolUse(Write|Edit) gate for the constitution plane.

"Machines gate, humans ratify" as a runtime fact (Pitfall P8/P11). Two composed deny paths on
the CONSTITUTION plane (``contracts/**`` · ``docs/adr/**`` · ``golden/**``):

1. **Access control** — a write to the constitution plane is DENIED unless a human-authorized
   ``GOLDEN_APPROVE_HUMAN`` token is present in env (agents are instructed never to fabricate it).
   An empty / whitespace-only value does NOT bypass (Q1 RESOLVED, T-04-06). The deny reason names
   the ``/golden-approve`` + CODEOWNERS ratification path.

2. **On-write byte hygiene** — even an APPROVED constitution write is DENIED if its payload bytes
   fail the reused POLY-01 :func:`tools.polyglot_lint.lint_bytes` (§4.3-4.6: BOM / CRLF). The
   constitution plane must stay byte-pristine even when access-approved (T-04-07, D-04). No second
   normalizer — one §4.3-4.6 engine, reused.

Composition invariants (04-06):
  * CONSTITUTION-ONLY subset (W-1): this gate feeds the reused resolver ``CONSTITUTION_GLOBS`` —
    NOT the full matrix ``path_deny_globs`` union (which also carries ``*.env``). ``*.env`` is
    secret_scan's ``SECRET_PATH_GLOBS`` domain; the two gates' domains are provably disjoint, so a
    ``.env`` write is never mislabeled "constitution plane" here.
  * Allowed-path byte hygiene is NOT this gate's job: a BOM/CRLF payload into a non-constitution
    path returns ``None`` — general byte hygiene is format-on-write's PostToolUse auto-fix (04-04).
    contract-guard must not preempt it.

Boundary: stdlib only (``json``/``os``) + the reused resolver + polyglot lint. No shell, no
``subprocess`` in the decision path (T-03-04 posture inherited). Malformed stdin is handled by
``_stdin`` and maps to a safe sentinel -> no decision.
"""

from __future__ import annotations

import json
import os
import sys

from tools.harness_perms import resolve_path
from tools.hooks._stdin import dev_bypassed, emit_deny, parse_event, read_stdin, repo_relative
from tools.polyglot_lint import lint_bytes

# CONSTITUTION-ONLY subset — the human-owned, CODEOWNERS-gated plane. Deliberately EXCLUDES *.env
# (secret_scan's SECRET_PATH_GLOBS domain) so the two gates are provably non-overlapping (W-1).
# Fed to the reused CONFIG-02 resolver (D-02) — no new glob matcher.
CONSTITUTION_GLOBS = ["contracts/**", "docs/adr/**", "golden/**"]

# Human confirmation token; a NON-EMPTY value == human-authorized session. Reuses the existing
# GOLDEN_APPROVE_HUMAN precedent (tools/golden_runner/approve.py) — agents must not fabricate it.
APPROVAL_ENV = "GOLDEN_APPROVE_HUMAN"


def _on_constitution_plane(file_path: str) -> bool:
    """True iff ``file_path`` resolves onto the CODEOWNERS-gated constitution plane.

    Extracted so both :func:`decide` (the deny logic) and :func:`main` (the dev-note emit) share one
    on-plane test — no logic drift between the gate and its note.
    """
    relative_path = repo_relative(file_path)
    return bool(relative_path) and resolve_path(CONSTITUTION_GLOBS, relative_path) == "deny"


def decide(file_path: str, content: str, approved: bool) -> dict | None:
    """Return a PreToolUse deny dict for a constitution-plane violation, else ``None``.

    * Off the constitution plane -> ``None`` (allowed source path; BOM/CRLF hygiene is format-on-
      write's PostToolUse job — 04-04 — do NOT deny it here).
    * On the constitution plane and NOT ``approved`` -> deny (access control; names the
      ``/golden-approve`` + CODEOWNERS ratification path).
    * On the constitution plane and ``approved`` but the payload bytes fail ``lint_bytes``
      (BOM/CRLF) -> deny (the plane must be byte-pristine even when access-approved, D-04).
    * On the constitution plane, approved, byte-pristine -> ``None`` (the bypass).
    """
    # Claude's file_path is absolute; the deny globs are repo-relative. Normalize at this seam so
    # the prefix-anchored globs actually match a real absolute write (else the gate no-ops).
    if not _on_constitution_plane(file_path):
        return None

    if not approved:
        return emit_deny(
            f"contract-guard: '{file_path}' is on the constitution plane "
            "(contracts/ · docs/adr/ · golden/); it is CODEOWNERS-gated and may only be changed "
            "via /golden-approve with a human GOLDEN_APPROVE_HUMAN token. Refusing the write."
        )

    violations = lint_bytes(content.encode("utf-8"))
    if violations:
        codes = ", ".join(f"[{v.rule}] {v.detail}" for v in violations)
        return emit_deny(
            f"contract-guard: approved constitution write to '{file_path}' fails the polyglot "
            f"§4.3-4.6 on-write rules ({codes}); the constitution plane must be byte-pristine "
            "even when access-approved. Refusing the write."
        )

    return None


def main() -> int:
    """PreToolUse entrypoint: parse stdin, apply :func:`decide`, print deny JSON on a hit.

    Always exits 0. ``approved`` is truthy ONLY on a non-empty, non-blank ``GOLDEN_APPROVE_HUMAN``
    value (empty string does NOT bypass — Q1 RESOLVED). On a hit, prints the deny decision to
    stdout (Claude blocks the tool call); otherwise prints nothing (normal permission flow).
    """
    event = parse_event(read_stdin())
    token_present = bool((os.environ.get(APPROVAL_ENV) or "").strip())
    approved = token_present or dev_bypassed()
    result = decide(event.file_path, event.content, approved)
    if result is not None:
        print(json.dumps(result))
    elif dev_bypassed() and not token_present and _on_constitution_plane(event.file_path):
        # Allowed ONTO the constitution plane via the local-dev opt-out, NOT a human token. Emit a
        # non-blocking dev-only note that never claims human approval — the audit meaning of the
        # token is preserved; CODEOWNERS at merge stays the real gate. On-plane only: source-path
        # writes get no note.
        print(
            f"contract-guard: constitution write to '{event.file_path}' allowed via "
            "HARNESS_DEV_BYPASS (dev-only) — CODEOWNERS still gates merge",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
