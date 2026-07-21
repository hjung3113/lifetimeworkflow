"""DOCSUP-07 end to end: `/adopt` may PROPOSE a registry row and is structurally unable to author
the review ledger — both facts observed in ONE apply cycle, not asserted twice in two unrelated
unit tests.

That asymmetry is ADR-0010 clause 3b, the ratified boundary this file exercises: a proposed binding
changes what is WATCHED, only a ledger row changes what is GREEN, so an agent extending coverage can
only ever create obligations for itself. Clause 3b names three enforcement layers; this file drives
layers 1 (`tools.hooks.ledger_guard.decide`, the ordinary Write/Edit tool path) and 2
(`refuse_unsafe_destination` -> `ReviewLedgerRefusal`, the adoption-apply write path). Layer 3 — a
write that slips past both still cannot produce green — is
`tools/docs_guard/tests/test_selfgreen_end_to_end.py`.

The SPELLING TABLE for the ledger (dot-segments, case variants, backslash separator) lives in
`test_constitution_refusal.py::REVIEW_LEDGER_DESTINATIONS` and is deliberately NOT duplicated here:
this file asserts the one spelling `/adopt` would realistically emit plus its case variant, and is
about AUTHORITY, not about spelling coverage.

Every control this file asserts already shipped, so a plain pre-fix RED run is impossible. Each
claim therefore carries a MUTATION: a control-shaped assertion with no demonstrable failure mode is
not evidence (T-29-08).

No row shape is restated here. Every ledger/registry literal is built from the shipped source of
truth — the registry payload is validated against the constitution-plane schema, so a fixture cannot
pin a stale shape (T-29-22).
"""

from __future__ import annotations

import builtins
import json
import os
import tomllib
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from jsonschema import Draft202012Validator

from tools.adoption_apply import apply
from tools.adoption_scan import plan
from tools.adoption_scan.destinations import DISPOSITION_ENUM
from tools.hooks import ledger_guard
from tools.hooks._stdin import _REPO_ROOT as REPO_ROOT

REGISTRY_REL = "docs/doc-dependencies.toml"
LEDGER_REL = "docs/.docs-review-ledger.toml"

# The single realistic spelling plus its case variant. See the module docstring for why the full
# table is not repeated.
LEDGER_SPELLINGS = [
    ("plain", LEDGER_REL),
    ("case_variant", "docs/.Docs-Review-Ledger.toml"),
]

_REGISTRY_SCHEMA = json.loads(
    (REPO_ROOT / "contracts" / "harness" / "docs" / "doc-dependencies.schema.json").read_text(
        encoding="utf-8"
    )
)

# A proposal `/adopt` could legally draft: one required binding over an existing runbook. Kept small
# on purpose — the test is about who may write where, not about TOML shape.
REGISTRY_TOML = (
    "[[binding]]\n"
    'id = "adoption-runbook"\n'
    'sources = ["tools/adoption_apply/apply.py"]\n'
    'target = "docs/how-to/task-lifecycle.md"\n'
    'severity = "required"\n'
    'dispositions = ["updated", "reviewed-no-change"]\n'
)
REGISTRY_PAYLOAD = REGISTRY_TOML.encode("utf-8")

# What a self-approving agent would want to land alongside it. Its CONTENT is irrelevant — no layer
# ever parses it, because no layer ever lets it reach the filesystem.
LEDGER_PAYLOAD = b"[coverage]\n"


def _manifest(ledger_destination: str = LEDGER_REL) -> dict:
    """One manifest carrying BOTH destinations, as a single `/adopt` apply cycle would."""
    return {
        "dispositions": [
            {"destination": REGISTRY_REL, "disposition": "create"},
            {"destination": ledger_destination, "disposition": "create"},
        ]
    }


def _payloads(ledger_destination: str = LEDGER_REL) -> dict[str, bytes]:
    return {REGISTRY_REL: REGISTRY_PAYLOAD, ledger_destination: LEDGER_PAYLOAD}


def _write_spies(monkeypatch) -> dict[str, MagicMock]:
    """The 27.1 SC-2 zero-write idiom, widened to `builtins.open` and `tempfile.mkstemp`.

    `apply.py` publishes through `tempfile.mkstemp` -> `os.fdopen` -> `os.link`/`os.replace`, so
    `os.open` alone would not see a plain `open(..., "wb")` if a future writer used one. Spying the
    superset means the assertion stays true of the CLAIM ("nothing was written") rather than of
    today's call sequence.
    """
    import tempfile

    spies = {
        "builtins.open": MagicMock(wraps=builtins.open),
        "os.open": MagicMock(wraps=os.open),
        "os.link": MagicMock(wraps=os.link),
        "os.replace": MagicMock(wraps=os.replace),
        "tempfile.mkstemp": MagicMock(wraps=tempfile.mkstemp),
    }
    monkeypatch.setattr(builtins, "open", spies["builtins.open"])
    monkeypatch.setattr(os, "open", spies["os.open"])
    monkeypatch.setattr(os, "link", spies["os.link"])
    monkeypatch.setattr(os, "replace", spies["os.replace"])
    monkeypatch.setattr(tempfile, "mkstemp", spies["tempfile.mkstemp"])
    return spies


def test_registry_payload_is_a_real_proposal() -> None:
    """Fixture sanity: the proposed registry bytes satisfy the ratified shape contract.

    Read from `contracts/harness/docs/doc-dependencies.schema.json` rather than restated, so the
    fixture follows the contract instead of pinning a snapshot of it (T-29-22). Without this the
    apply cycle below could pass while proposing nonsense.
    """
    document = tomllib.loads(REGISTRY_TOML)
    errors = sorted(
        error.message for error in Draft202012Validator(_REGISTRY_SCHEMA).iter_errors(document)
    )
    assert errors == [], errors
    assert "create" in DISPOSITION_ENUM, "the manifest records use a real disposition value"


def test_registry_applied_and_ledger_refused_in_one_cycle(tmp_path: Path) -> None:
    """SC-2, both halves, ONE cycle: the registry proposal lands and the ledger record is refused.

    Two unit tests in two unrelated modules cannot establish this. The asymmetry is a property of a
    single apply cycle, and `apply_manifest` buckets per record — so the same call that writes the
    registry must refuse the ledger.
    """
    summary = apply.apply_manifest(_manifest(), tmp_path, payloads=_payloads())

    assert summary["applied"] == [REGISTRY_REL]
    assert summary["refused"] == [LEDGER_REL]
    assert (tmp_path / REGISTRY_REL).read_bytes() == REGISTRY_PAYLOAD
    assert not (tmp_path / LEDGER_REL).exists(), "the ledger was authored by an agent"


@pytest.mark.parametrize(
    ("case_name", "destination"),
    LEDGER_SPELLINGS,
    ids=[case_name for case_name, _ in LEDGER_SPELLINGS],
)
def test_ledger_refused_before_any_write(tmp_path: Path, monkeypatch, case_name, destination):
    """The refusal happens BEFORE any filesystem write, and carries its OWN exception type.

    `ReviewLedgerRefusal` is deliberately not a `ConstitutionRefusal`: `GOLDEN_APPROVE_HUMAN`
    authorizes constitution writes, and no token authorizes an agent-authored review disposition
    (ADR-0010 clause 3b). Conflating them would teach an operator the wrong remedy.
    """
    spies = _write_spies(monkeypatch)

    record = {"destination": destination, "disposition": "create"}
    with pytest.raises(apply.ReviewLedgerRefusal) as excinfo:
        apply.apply_disposition(record, tmp_path, payload=LEDGER_PAYLOAD)

    assert not isinstance(excinfo.value, apply.ConstitutionRefusal), case_name
    for name, spy in spies.items():
        assert spy.call_count == 0, f"{case_name}: {name} was called before the refusal"
    assert not (tmp_path / destination).exists(), case_name


def test_refusal_is_load_bearing(tmp_path: Path, monkeypatch) -> None:
    """MUTATION proof for the layer-2 refusal (T-29-08).

    The control shipped in 28-09, so no plain pre-fix RED run exists. Neutralizing
    `apply.REVIEW_LEDGER_GLOBS` flips the SAME manifest from refused to applied — which is the
    failure this file would show if the deny domain were ever deleted, and is recorded verbatim in
    `29-02-SUMMARY.md`.
    """
    monkeypatch.setattr(apply, "REVIEW_LEDGER_GLOBS", [])

    summary = apply.apply_manifest(_manifest(), tmp_path, payloads=_payloads())

    assert summary["refused"] == [], "with the deny domain neutralized nothing should be refused"
    assert summary["applied"] == sorted([LEDGER_REL, REGISTRY_REL])
    assert (tmp_path / LEDGER_REL).read_bytes() == LEDGER_PAYLOAD


def test_both_write_side_layers_refuse_the_ledger_and_keep_the_registry_writable() -> None:
    """ADR-0010 clause 3b: no single layer suffices, and neither may spill onto the registry.

    Layer 1 is the ordinary agent `Write`/`Edit` tool path — a plain tool call never enters the
    adoption-apply module, so layer 2 cannot cover it. Layer 2 is the adoption-apply write path —
    the permission resolver is not consulted inside a bare `python -m tools.adoption_apply apply`,
    so layer 1 cannot cover it. Both are probed here against the same two paths.

    The registry half is not decoration: DOCSUP-07 requires `/adopt` to propose rows into
    `docs/doc-dependencies.toml`, so a refusal that also caught the registry would silently break
    the requirement while looking like a stronger control.
    """
    ledger = REPO_ROOT / LEDGER_REL
    registry = REPO_ROOT / REGISTRY_REL

    # Layer 1 — the hook's own decision, driven with the absolute path the runtime passes.
    assert ledger_guard.decide(str(ledger)) is not None, "layer 1 did not deny the ledger"
    assert ledger_guard.decide(str(registry)) is None, "layer 1 spilled onto the registry"

    # Layer 2 — the adoption-apply choke point, as a bare function call with no tool event anywhere.
    with pytest.raises(apply.ReviewLedgerRefusal):
        apply.refuse_unsafe_destination(LEDGER_REL, REPO_ROOT)
    assert apply.refuse_unsafe_destination(REGISTRY_REL, REPO_ROOT) == registry


def test_unknown_ownership_becomes_a_question(tmp_path: Path) -> None:
    """DOCSUP-07's "inferred ownership은 미해결로 남기고": an unresolved docs destination surfaces
    as a questionRecord, never as a fabricated binding (the `OWNER_TBD` never-invent rule).

    Under-delivering is the safe direction: a binding whose sources do not genuinely determine its
    target is noise that trains people to rubber-stamp, which is the failure mode ADR-0010 exists to
    prevent. The proposal below is `unknown`, so the correct output is a question — and a question
    carries no `owner`, no `sources`, and no `severity`.
    """
    proposals = [
        {
            "id": "docs-destination/docs/how-to/task-lifecycle.md",
            "kind": "docs-destination",
            "classification": "unknown",
            "target": "docs/how-to/task-lifecycle.md",
            "evidence": [{"path": "docs/how-to/task-lifecycle.md", "sha256": "a" * 64, "size": 12}],
        }
    ]

    questions = plan.generate_questions({"target_ref": "unknown"}, proposals)

    assert len(questions) == 1
    question = questions[0]
    assert question["kind"] == "docs-destination"
    assert question["classification"] == "unknown"
    assert question["target"] == "docs/how-to/task-lifecycle.md"
    for fabricated in ("owner", "sources", "severity", "dispositions", "binding"):
        assert fabricated not in question, f"a question record invented {fabricated}"

    # And nothing about an unresolved ownership may reach the apply path as a binding proposal.
    summary = apply.apply_manifest({"dispositions": []}, tmp_path)
    assert summary == {"applied": [], "skipped": [], "refused": []}
