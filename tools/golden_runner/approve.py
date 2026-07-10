"""``/golden-approve`` — Phase-1 minimal human-ratification gate (CONTRACT-03, Pitfall P9).

"Machines gate, humans ratify." The runner (and any agent) may write ``baseline.received.tsv``.
Promotion to the human-approved ``baseline.verified.tsv`` is REFUSED unless ALL of:

  1. an explicit human ``--approve`` flag,
  2. an ``--adr`` reference (every baseline change must cite a decision — the smell we make
     impossible), and
  3. a human confirmation token matching the ``GOLDEN_APPROVE_HUMAN`` env var (a value an agent is
     instructed never to fabricate) — models "not auto-passable by the agent".

Any missing signal raises :class:`GoldenApprovalRefused` (CLI exit 3). The REFUSAL path is the
automated test surface (test_approve_gate.py); the affirmative promotion is a human-only action
(01-VALIDATION.md §Manual-Only). Hard enforcement (contract-guard deny + CODEOWNERS) lands in
Phase 4/5 — Phase 1 ships the executable refusal + the .received/.verified separation so the audit
surface exists.
"""

from __future__ import annotations

import os
from pathlib import Path

from tools.golden_runner.runner import received_path, verified_path

HUMAN_TOKEN_ENV = "GOLDEN_APPROVE_HUMAN"


class GoldenApprovalRefused(Exception):
    """Promotion .received → .verified refused (missing human sign-off / ADR / received file)."""


def promote(
    case: str,
    *,
    approve: bool = False,
    adr: str | None = None,
    human_token: str | None = None,
) -> Path:
    """Promote a case's ``.received`` baseline to ``.verified`` — or refuse (P9).

    Raises :class:`GoldenApprovalRefused` unless the explicit human flag, an ADR reference, and a
    matching human confirmation token are all present AND a ``.received`` file exists.
    Returns the promoted ``.verified`` path on success.
    """
    if not approve:
        raise GoldenApprovalRefused(
            "REFUSED: promotion requires an explicit human --approve flag "
            "(agents must not self-bless the golden baseline, P9)."
        )
    if not adr:
        raise GoldenApprovalRefused(
            "REFUSED: promotion requires an --adr reference "
            "(every baseline change cites a decision, P9)."
        )

    expected_token = os.environ.get(HUMAN_TOKEN_ENV)
    if not expected_token or human_token != expected_token:
        raise GoldenApprovalRefused(
            f"REFUSED: promotion requires the human confirmation token ({HUMAN_TOKEN_ENV}); "
            "an agent must not fabricate it."
        )

    received = received_path(case)
    if not received.exists():
        raise GoldenApprovalRefused(f"REFUSED: no {received.name} to promote for case '{case}'.")

    verified = verified_path(case)
    verified.write_bytes(received.read_bytes())
    received.unlink()  # consumed: a promoted proposal is no longer pending
    return verified


def main(argv: list[str] | None = None) -> int:
    """CLI: refuse (exit 3) unless a human explicitly approves with an ADR + confirmation token."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Promote a golden .received baseline to .verified (human-only, P9)."
    )
    parser.add_argument("case", help="golden case id (e.g. value-regression)")
    parser.add_argument("--approve", action="store_true", help="explicit human approval (required)")
    parser.add_argument("--adr", default=None, help="ADR reference for the change (required)")
    parser.add_argument(
        "--confirm",
        default=None,
        help=f"human confirmation token; must match ${HUMAN_TOKEN_ENV} (required)",
    )
    args = parser.parse_args(argv)

    try:
        verified = promote(args.case, approve=args.approve, adr=args.adr, human_token=args.confirm)
    except GoldenApprovalRefused as exc:
        print(str(exc))
        return 3

    print(f"PROMOTED: {verified} (ADR: {args.adr}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
