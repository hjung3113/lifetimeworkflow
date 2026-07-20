"""test_constitution_refusal.py — proves apply.py's constitution-plane refusal is structural.

RESEARCH's Pitfall 1: a test suite that only exercises ``apply.py`` via a simulated Claude
``PreToolUse`` tool-call event never proves the refusal is independent of that hook. Every test
here calls ``apply`` functions as bare Python — no Claude event object anywhere in the chain.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest

from tools.adoption_apply import apply


@pytest.mark.parametrize(
    "destination",
    [
        "contracts/widget.schema.json",
        "docs/adr/0099-example.md",
        "golden/y/baseline.verified.tsv",
    ],
)
def test_refuses_before_mutation(tmp_path, monkeypatch, destination):
    """Zero-call spy proof: refused BEFORE any open()/os.link()/os.replace() call."""
    open_spy = MagicMock(wraps=os.open)
    link_spy = MagicMock(wraps=os.link)
    replace_spy = MagicMock(wraps=os.replace)
    monkeypatch.setattr(os, "open", open_spy)
    monkeypatch.setattr(os, "link", link_spy)
    monkeypatch.setattr(os, "replace", replace_spy)

    record = {"destination": destination, "disposition": "create"}

    with pytest.raises(apply.ConstitutionRefusal):
        apply.apply_disposition(record, tmp_path, payload=b"content")

    assert open_spy.call_count == 0
    assert link_spy.call_count == 0
    assert replace_spy.call_count == 0
    # The refused destination must never land on disk under target_root either.
    assert not (tmp_path / destination).exists()


def test_refuses_bare_cli_invocation():
    """Bare function call, no Claude tool-call event object anywhere in the chain."""
    with pytest.raises(apply.ConstitutionRefusal):
        apply.refuse_if_constitution("contracts/example.schema.json")


def test_non_constitution_destination_allowed():
    apply.refuse_if_constitution("src/widget.py")  # must not raise


def test_atomic_create_collision(tmp_path):
    target = tmp_path / "src" / "widget.py"
    apply.atomic_create(target, b"first\n")
    with pytest.raises(apply.CollisionError):
        apply.atomic_create(target, b"second\n")
    assert target.read_bytes() == b"first\n"


def test_refuse_if_outside_root_allows_in_root(tmp_path):
    root = tmp_path / "artifacts" / "adoption" / "batch1"
    root.mkdir(parents=True)
    apply.refuse_if_outside_root(root / "inventory.json", root)  # must not raise
