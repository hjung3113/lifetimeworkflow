"""/golden-approve refusal gate (CONTRACT-03, Pitfall P9, ASVS V4).

Automates the REFUSAL path (01-VALIDATION.md §Manual-Only leaves the affirmative promotion as a
human action). Proves an agent cannot self-bless the golden baseline: promotion is refused unless
an explicit human --approve flag, an --adr reference, AND a matching human confirmation token are
ALL present and a .received file exists. The affirmative case is covered on a tmp copy purely to
show the mechanism is not dead — the load-bearing assertions here are the refusals.
"""

from __future__ import annotations

import pytest

from tools.golden_runner import approve
from tools.golden_runner.approve import GoldenApprovalRefused, promote

_ADR = "docs/adr/0001-walking-skeleton-golden-core.md"


def test_default_agent_path_is_refused():
    """No flags at all (the agent default) → refuse. This is the core P9 guarantee."""
    with pytest.raises(GoldenApprovalRefused, match="explicit human --approve"):
        promote("value-regression")


def test_approve_without_adr_is_refused():
    with pytest.raises(GoldenApprovalRefused, match="--adr reference"):
        promote("value-regression", approve=True)


def test_approve_and_adr_without_human_token_is_refused(monkeypatch):
    """Even with --approve + --adr, a missing/unset human confirmation token refuses."""
    monkeypatch.delenv(approve.HUMAN_TOKEN_ENV, raising=False)
    with pytest.raises(GoldenApprovalRefused, match="human confirmation token"):
        promote("value-regression", approve=True, adr=_ADR, human_token="guessed")


def test_wrong_human_token_is_refused(monkeypatch):
    monkeypatch.setenv(approve.HUMAN_TOKEN_ENV, "real-human-secret")
    with pytest.raises(GoldenApprovalRefused, match="human confirmation token"):
        promote("value-regression", approve=True, adr=_ADR, human_token="wrong")


def test_full_signoff_without_received_file_is_refused(tmp_path, monkeypatch):
    """All human signals present but no .received to promote → refuse (nothing to ratify)."""
    monkeypatch.setenv(approve.HUMAN_TOKEN_ENV, "real-human-secret")
    monkeypatch.setattr(approve, "received_path", lambda case: tmp_path / "baseline.received.tsv")
    monkeypatch.setattr(approve, "verified_path", lambda case: tmp_path / "baseline.verified.tsv")
    with pytest.raises(GoldenApprovalRefused, match="no baseline.received.tsv"):
        promote("dummy", approve=True, adr=_ADR, human_token="real-human-secret")


def test_full_human_signoff_promotes(tmp_path, monkeypatch):
    """Mechanism proof (human-simulated): full sign-off + a .received file → promote + consume."""
    rec = tmp_path / "baseline.received.tsv"
    ver = tmp_path / "baseline.verified.tsv"
    rec.write_bytes(b"col\nnew-approved-value\n")
    ver.write_bytes(b"col\nold-value\n")
    monkeypatch.setenv(approve.HUMAN_TOKEN_ENV, "real-human-secret")
    monkeypatch.setattr(approve, "received_path", lambda case: rec)
    monkeypatch.setattr(approve, "verified_path", lambda case: ver)

    out = promote("dummy", approve=True, adr=_ADR, human_token="real-human-secret")

    assert out == ver
    assert ver.read_bytes() == b"col\nnew-approved-value\n"  # promoted
    assert not rec.exists()  # consumed
