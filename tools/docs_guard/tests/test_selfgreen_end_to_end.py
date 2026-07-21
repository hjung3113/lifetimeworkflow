"""DOCSUP-07, the GREENNESS half: a binding an agent could legally propose is never green.

`tools/adoption_apply/tests/test_docs_binding_proposal.py` proves the two WRITE-side layers of
ADR-0010 clause 3b (the `Write`/`Edit` hook and the adoption-apply choke point). This file is
layer 3: a ledger write that slipped past both still cannot produce green, because greenness is
decided by history, not by the row's content.

Four claims, each with the mutation that flips it (T-29-08 — a control-shaped assertion with no
demonstrable failure mode is not evidence):

1. A registry row with NO `[[reviewed]]` row is BROKEN when `required` and never FRESH when
   `advisory`. This is the state an agent CAN reach by itself, and it is the amber ADR-0010
   clause 3b records as an accepted cost.
2. A binding and a matching `reviewed-no-change` row carrying its exact live digests, introduced
   TOGETHER, are caught by `first_seen-unratified` — the byte-identical-to-the-attack case, which
   no inspection of the row's CONTENT can tell apart from an honest first seed.
3. Repointing an ALREADY-RATIFIED id at a different `(sources, target)` pair is likewise a new
   obligation (ADR-0010 clause 4, as corrected by 28-REVIEW CR-03). The registry is agent-writable
   by design, so without this a single registry edit launders an old ratification onto arbitrary
   new content.
4. Both are load-bearing: neutralize the history lookup each depends on and the same tree reports
   FRESH.

"Previous COMMITTED" means `git show HEAD:./<path>`, so the fulcrum is HEAD vs. the WORKING TREE:
the change under review is the uncommitted one, and HEAD is the last ratified state. Every fixture
below is staged exactly that way, against the real `git init` `docs_repo` fixture — no mocked git,
and no second fixture (conftest.py owns it).

Digests are always computed by CALLING the shipped `digest.compute`/`digest.resolve`, never
hand-hashed: a hand-computed digest that disagreed with the gate would make these tests assert
their own arithmetic. Ledger rows are built from `ledger._ROW_KEYS` as shipped, so no fixture pins a
stale row shape (T-29-22).
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from tools.docs_guard import guard
from tools.docs_guard.digest import compute, resolve
from tools.docs_guard.ledger import _ROW_KEYS
from tools.docs_guard.tests.conftest import git

REG_REL = "docs/doc-dependencies.toml"
LED_REL = "docs/.docs-review-ledger.toml"

_SOURCE = "src/one.py"
_TARGET = "docs/how-to/one.md"
_OTHER_SOURCE = "src/two.py"
_OTHER_TARGET = "docs/how-to/two.md"


# ── helpers (local by design: test_guard.py's are private to that module) ──────────────────────


def _write(repo: Path, rel: str, text: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _commit(repo: Path, message: str) -> None:
    assert git(repo, "add", "-A").returncode == 0
    done = git(repo, "commit", "-m", message)
    assert done.returncode == 0, done.stderr


def _binding_toml(
    *,
    id: str,
    sources: tuple[str, ...],
    target: str,
    severity: str = "required",
) -> str:
    return (
        "[[binding]]\n"
        f"id = {json.dumps(id)}\n"
        f"sources = [{', '.join(json.dumps(s) for s in sources)}]\n"
        f"target = {json.dumps(target)}\n"
        f"severity = {json.dumps(severity)}\n"
        'dispositions = ["updated", "reviewed-no-change"]\n'
    )


def _row_toml(**fields: str) -> str:
    """One `[[reviewed]]` row, built from the SHIPPED `_ROW_KEYS`.

    The key set is read from `ledger.py`, never restated: a fixture that hardcoded today's keys
    would keep passing after the shape changed, or would go red for the wrong reason. A missing or
    surplus key here fails loudly at authoring time rather than silently producing a row the gate
    would reject.
    """
    assert set(fields) == set(_ROW_KEYS), (
        f"the shipped ledger row shape is {sorted(_ROW_KEYS)}, this fixture supplies "
        f"{sorted(fields)}"
    )
    body = "".join(f"{key} = {json.dumps(fields[key])}\n" for key in sorted(fields))
    return "[[reviewed]]\n" + body


def _ledger_toml(*rows: str) -> str:
    return "\n".join(("[coverage]\n", *rows)) if rows else "[coverage]\n"


def _digests(repo: Path, sources: tuple[str, ...], target: str) -> tuple[str, str]:
    """The live `(source, target)` digest pair, computed the way the guard computes it."""
    return compute(resolve(sources, repo), repo), compute(resolve([target], repo), repo)


def _clean_gate() -> dict:
    """A `run_gate`-shaped result with nothing drifted.

    The DRIFTED case is deliberately absent from this file: 28-REVIEW CR-01 owns that fixture
    (`test_self_blessed_binding_is_not_rescued_by_a_drifted_source`), and duplicating it here would
    re-assert someone else's control instead of consuming it.
    """
    return {"ok": True, "drifted": []}


def _classify(repo: Path) -> dict:
    return guard.classify(
        registry_path=repo / REG_REL,
        ledger_path=repo / LED_REL,
        root=repo,
        drift_gate=_clean_gate,
    )


def _state_of(result: dict, binding_id: str) -> str:
    for entry in result["bindings"]:
        if entry["id"] == binding_id:
            return entry["state"]
    raise AssertionError(f"binding {binding_id!r} absent from the result")


def _reasons(result: dict, binding_id: str) -> list[str]:
    return [
        finding["reason"] for finding in result["findings"] if finding["binding_id"] == binding_id
    ]


def _propose_binding(repo: Path, *, severity: str = "required") -> None:
    """What `/adopt` can legally do on its own: extend the registry, and nothing else."""
    _write(repo, _TARGET, "how-to one\n")
    _write(repo, LED_REL, _ledger_toml())  # a committed ledger that lacks every row
    _commit(repo, "seed the target and an empty ledger")
    _write(
        repo,
        REG_REL,
        _binding_toml(id="proposed", sources=(_SOURCE,), target=_TARGET, severity=severity),
    )


def _self_bless(repo: Path) -> None:
    """The attack: the binding AND its own `reviewed-no-change` row, in one change.

    The row carries the binding's EXACT live digests, so it is consistent by construction — the
    honest first seed and this are byte-identical, which is why the control has to be a history
    test.
    """
    _propose_binding(repo)
    source_digest, target_digest = _digests(repo, (_SOURCE,), _TARGET)
    _write(
        repo,
        LED_REL,
        _ledger_toml(
            _row_toml(
                id="proposed",
                source_digest=source_digest,
                target_digest=target_digest,
                disposition="reviewed-no-change",
            )
        ),
    )


# ── 1. what an agent can reach by itself is not green ─────────────────────────────────────────


def test_registry_row_without_ledger_row_is_not_green(docs_repo: Path) -> None:
    """A `required` binding an agent proposed and nobody reviewed is BROKEN, and fails the gate.

    This is the whole propose/ratify asymmetry at the greenness end: extending the registry creates
    an obligation for the proposer and discharges nothing.
    """
    _propose_binding(docs_repo)

    result = _classify(docs_repo)

    assert _state_of(result, "proposed") == "BROKEN"
    assert "broken-binding" in _reasons(result, "proposed")
    assert result["ok"] is False


def test_advisory_row_without_ledger_row_is_not_fresh(docs_repo: Path) -> None:
    """The advisory twin. It does not fail the gate — advisory never flips `ok` — but it is not
    FRESH either, so an agent cannot manufacture green by choosing the softer severity."""
    _propose_binding(docs_repo, severity="advisory")

    result = _classify(docs_repo)

    assert _state_of(result, "proposed") == "STALE_ADVISORY"
    assert _state_of(result, "proposed") != "FRESH"


# ── 2. the self-blessed row ───────────────────────────────────────────────────────────────────


def test_same_commit_self_blessing_is_caught(docs_repo: Path) -> None:
    """The exact case 28-07 refused to author: a binding blessed in the change that introduces it.

    Every digest agrees, so a digest-only rule reports FRESH. `first_seen-unratified` fires because
    the row has no counterpart in the PREVIOUS COMMITTED ledger — the human review commit that
    lands the row IS the ratification, and it has not happened yet.
    """
    _self_bless(docs_repo)

    result = _classify(docs_repo)

    entry = next(item for item in result["bindings"] if item["id"] == "proposed")
    assert (entry["source_digest"], entry["target_digest"]) == (
        entry["live_source_digest"],
        entry["live_target_digest"],
    ), "fixture sanity: the self-blessed row must be digest-consistent, or it proves nothing"
    assert entry["state"] != "FRESH"
    assert "first_seen-unratified" in _reasons(result, "proposed")
    assert result["ok"] is False


def test_first_seen_is_load_bearing(docs_repo: Path, monkeypatch) -> None:
    """MUTATION: point the previous-committed-ledger lookup at the WORKING TREE ledger.

    The same tree, the same digests, the same row — and now FRESH. That isolates which control
    stops the attack: not the digests, which agreed all along, but the question "has a human
    committed this row before?".
    """
    _self_bless(docs_repo)
    working_tree_ledger = tomllib.loads((docs_repo / LED_REL).read_text(encoding="utf-8"))
    monkeypatch.setattr(guard, "previous_ledger", lambda *_args, **_kwargs: working_tree_ledger)

    result = _classify(docs_repo)

    assert _state_of(result, "proposed") == "FRESH"
    assert "first_seen-unratified" not in _reasons(result, "proposed")


# ── 3. the repointed binding (ADR-0010 clause 4, as corrected by 28-REVIEW CR-03) ──────────────


def _ratify_then_repoint(repo: Path) -> None:
    """Land a genuinely ratified binding in history, then repoint it in the working tree.

    Two commits, because a ratification is a fact about history: the first introduces the binding
    and its row, the second is the human review commit that makes it green. Only then is there
    something for the repoint to try to inherit.
    """
    _write(repo, _SOURCE, "ONE = 1\n")
    _write(repo, _OTHER_SOURCE, "TWO = 2\n")
    _write(repo, _TARGET, "how-to one\n")
    _write(repo, _OTHER_TARGET, "how-to two\n")
    _write(repo, REG_REL, _binding_toml(id="ratified", sources=(_SOURCE,), target=_TARGET))
    _commit(repo, "propose the binding")

    source_digest, target_digest = _digests(repo, (_SOURCE,), _TARGET)
    _write(
        repo,
        LED_REL,
        _ledger_toml(
            _row_toml(
                id="ratified",
                source_digest=source_digest,
                target_digest=target_digest,
                disposition="reviewed-no-change",
            )
        ),
    )
    _commit(repo, "human review: ratify the binding")

    # THE REPOINT — same id, a different (sources, target) pair, with the ledger digests rewritten
    # to the new pair's live values in the same uncommitted change. One registry edit, and the old
    # ratification would otherwise cover content nobody ever reviewed.
    _write(
        repo, REG_REL, _binding_toml(id="ratified", sources=(_OTHER_SOURCE,), target=_OTHER_TARGET)
    )
    new_source_digest, new_target_digest = _digests(repo, (_OTHER_SOURCE,), _OTHER_TARGET)
    _write(
        repo,
        LED_REL,
        _ledger_toml(
            _row_toml(
                id="ratified",
                source_digest=new_source_digest,
                target_digest=new_target_digest,
                disposition="reviewed-no-change",
            )
        ),
    )


def test_ratified_binding_is_green_before_the_repoint(docs_repo: Path) -> None:
    """Non-degradation control: the second cycle DOES turn an honestly ratified binding green.

    Without this row the two tests below would pass against a gate that simply never reports FRESH,
    which is not a gate — it is a broken one.
    """
    _write(docs_repo, _TARGET, "how-to one\n")
    _write(docs_repo, REG_REL, _binding_toml(id="ratified", sources=(_SOURCE,), target=_TARGET))
    _commit(docs_repo, "propose the binding")
    source_digest, target_digest = _digests(docs_repo, (_SOURCE,), _TARGET)
    _write(
        docs_repo,
        LED_REL,
        _ledger_toml(
            _row_toml(
                id="ratified",
                source_digest=source_digest,
                target_digest=target_digest,
                disposition="reviewed-no-change",
            )
        ),
    )
    _commit(docs_repo, "human review: ratify the binding")

    result = _classify(docs_repo)

    assert _state_of(result, "ratified") == "FRESH"
    assert result["ok"] is True


def test_repointing_a_ratified_binding_is_a_new_obligation(docs_repo: Path) -> None:
    """An already-ratified id repointed at different content is amber again (clause 4).

    A ledger row states nothing about WHAT was reviewed beyond the id, so identity is the pair
    `(id, the binding's committed (sources, target))`. A renamed id was always caught — a new name
    is absent from history — but a repointed one carried its ratification forward until CR-03.
    """
    _ratify_then_repoint(docs_repo)

    result = _classify(docs_repo)

    assert _state_of(result, "ratified") != "FRESH"
    assert "first_seen-unratified" in _reasons(result, "ratified")
    assert result["ok"] is False


def test_repoint_detection_is_load_bearing(docs_repo: Path, monkeypatch) -> None:
    """MUTATION: make the previous-committed-REGISTRY lookup unreadable.

    With no committed registry the repointed set is empty, the history test falls back to the id
    alone, and the same repointed tree reports FRESH — the pre-CR-03 behaviour. That is what the
    committed-registry comparison buys, and it is why the ledger row needs no third digest.
    """
    _ratify_then_repoint(docs_repo)
    monkeypatch.setattr(guard, "previous_document", lambda *_args, **_kwargs: None)

    result = _classify(docs_repo)

    assert _state_of(result, "ratified") == "FRESH"
    assert "first_seen-unratified" not in _reasons(result, "ratified")
