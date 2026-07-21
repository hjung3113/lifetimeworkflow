"""HOOK-06 ledger-guard — PreToolUse(Write|Edit) deny for the human-review ledger.

ADR-0010 clause 3b names three enforcement layers for the docs-plane agent-authority boundary, and
this module IS layer 1: the ordinary agent ``Write``/``Edit`` tool path. Layer 2
(``tools/adoption_apply/apply.py``'s ``refuse_unsafe_destination``) guards only the adoption-apply
module — a plain tool call never enters it — and layer 3
(``tools/docs_guard/ledger.py``'s ``first_seen-unratified``) guards only GREENNESS, i.e. it stops a
slipped-through write from producing green rather than stopping the write.

Before this module existed, layer 1 was INERT DATA: the ``path_deny_globs`` entry for the ledger was
read by no hook, and ``tools/harness_emit/permissions.py`` strips ``path_deny_globs`` from the
emitted ``opencode.json`` as a resolver-only key. Every OTHER entry in that list is separately
re-declared inside a hook (``contract_guard.CONSTITUTION_GLOBS``, ``secret_scan.SECRET_PATH_GLOBS``)
— the ledger entry was the first that was not, so the ADR asserted a control that did not exist.

**A THIRD, DISJOINT DENY DOMAIN — and NO bypass of any kind.**

``contract_guard.py:16-20`` records a provably-disjoint-domain invariant between the constitution
gate and secret_scan. This module preserves it by owning its OWN constant
(:data:`REVIEW_LEDGER_GLOBS`) rather than widening ``CONSTITUTION_GLOBS``, for the reason ADR-0010
clause 3b gives: ``GOLDEN_APPROVE_HUMAN`` authorizes CONSTITUTION writes, and there is **no token**
that legitimizes an agent-authored review disposition — none exists and none should be invented.
Folding the ledger into the constitution domain would teach an operator to reach for a token that
must never apply here.

For the same reason this gate honours **neither** ``GOLDEN_APPROVE_HUMAN`` **nor**
``HARNESS_DEV_BYPASS``. Both are opt-outs for the constitution plane; the ledger is not the
constitution plane, it is the docs plane's GREENNESS AUTHORITY. A human authors a ledger
disposition directly, outside an agent session — there is nothing for a session-scoped opt-out to
express.

Boundary: stdlib only (``json``) + the reused CONFIG-02 resolver. No shell, no ``subprocess`` in the
decision path. Malformed stdin is handled by ``_stdin`` and maps to a safe sentinel -> no decision.
"""

from __future__ import annotations

import json

from tools.harness_perms import resolve_path
from tools.hooks._stdin import emit_deny, parse_event, read_stdin, repo_relative

# The human-review ledger — the THIRD path-deny domain, disjoint from the constitution plane
# (``contract_guard.CONSTITUTION_GLOBS``) and from the secret plane
# (``secret_scan.SECRET_PATH_GLOBS``). This module is its single authoritative home;
# ``tools/adoption_apply/apply.py`` IMPORTS it rather than declaring a second copy, so the write
# path and the tool path can never disagree about what the ledger is.
REVIEW_LEDGER_GLOBS = ["docs/.docs-review-ledger.toml"]

DENY_REASON = (
    "ledger-guard: '{path}' is the human-review ledger — only a HUMAN may author a review "
    "disposition, because a ledger row is what makes a binding FRESH. GOLDEN_APPROVE_HUMAN does "
    "NOT apply here and no token does: a human edits this file directly, outside an agent session. "
    "Agents may propose registry rows in docs/doc-dependencies.toml instead — that changes what is "
    "WATCHED, never what is GREEN (ADR-0010 clause 3b). Refusing the write."
)


def decide(file_path: str) -> dict | None:
    """Return a PreToolUse deny dict iff ``file_path`` resolves onto the review ledger.

    Returns ``None`` for every other path.

    Claude's ``file_path`` is absolute and the deny globs are repo-relative, so the path is
    normalized at this seam — without it the prefix-anchored globs never match a real write and the
    gate silently no-ops, which is the failure shape the AUDIT-FINDINGS entry for ``contract_guard``
    records.
    """
    relative_path = repo_relative(file_path)
    if not relative_path or resolve_path(REVIEW_LEDGER_GLOBS, relative_path) != "deny":
        return None
    return emit_deny(DENY_REASON.format(path=file_path))


def main() -> int:
    """PreToolUse entrypoint: parse stdin, apply :func:`decide`, print deny JSON on a hit.

    Always exits 0. On a hit, prints the deny decision to stdout (the runtime blocks the tool call);
    otherwise prints nothing (normal permission flow). There is no approved/bypass branch to take —
    see the module docstring.
    """
    event = parse_event(read_stdin())
    result = decide(event.file_path)
    if result is not None:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
