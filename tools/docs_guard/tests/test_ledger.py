"""DOCSUP-03 disposition/digest coherence — the adversarial table, the forbidden-key table, and
the structural proof that the guard cannot write the ledger.

``COHERENCE_CASES`` is the load-bearing artifact and ``paste_live_digest`` is its centrepiece: an
agent or a hurried human sees ``STALE_REQUIRED``, pastes the LIVE source digest into the ledger,
writes ``disposition = "updated"``, and leaves the target document untouched. After that paste the
stored digests and the live digests agree by construction, so a digest-equality-only checker reports
the ledger CLEAN. Only a comparison against the PREVIOUS COMMITTED ledger can see it. The table was
authored and confirmed RED against exactly such a digest-only checker BEFORE the coherence rule
landed; the verbatim failure output is recorded in ``28-04-SUMMARY.md``.

``new_binding_self_blessed`` is the sibling attack: a brand-new ``[[binding]]`` landed together with
a ``reviewed-no-change`` row carrying the exact live digests is consistent by construction and has
nothing in history to contradict it. Its closure — ``first_seen-unratified`` — is deliberately a
HISTORY test, not a content test, because the self-blessed row and an honest first-ever seed row are
byte-identical. ``new_binding_second_commit`` is its non-degradation control and must be GREEN
throughout: without it the rule could be implemented as "a new binding can never be green", which
passes the attack row while making the registry unusable. ``honest_update`` plays the same role for
the ``updated`` half, and ``binding_deleted_outside_corpus`` proves ``binding_min`` is independently
necessary rather than redundant with the uncovered ratchet.

No test mocks ``git``. Every history row runs against a real ``git init`` tree — the ``docs_repo``
fixture from ``conftest.py``, or the local ``empty_repo`` fixture for the no-``HEAD`` rows.
"""

from __future__ import annotations

import hashlib
import inspect
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from tools.docs_guard import ledger as ledger_module
from tools.docs_guard.digest import compute, resolve
from tools.docs_guard.ledger import LedgerError, check_coherence, load_ledger, previous_ledger
from tools.docs_guard.tests.conftest import git

LEDGER_REL = "docs/.docs-review-ledger.toml"

# id -> (source selectors, target selectors, severity)
Bindings = dict[str, tuple[list[str], list[str], str]]

# The tree every case starts from, on top of the ``docs_repo`` seed (docs/a.md, docs/nested/b.md,
# src/one.py). ``src/two.py`` gives the advisory binding its own source.
_EXTRA_SEED = {"src/two.py": "TWO = 2\n"}

_BASE: Bindings = {
    "one": (["src/one.py"], ["docs/a.md"], "required"),
    "two": (["src/two.py"], ["docs/nested/b.md"], "advisory"),
}


# ── helpers ───────────────────────────────────────────────────────────────────────────────────


def _write(repo: Path, rel: str, text: str) -> None:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _seed_extra(repo: Path) -> None:
    for rel, text in _EXTRA_SEED.items():
        _write(repo, rel, text)


def _live(repo: Path, bindings: Bindings) -> dict[str, tuple[str, str]]:
    """The live (source, target) digest pair per binding, computed off the working tree."""
    return {
        bid: (compute(resolve(src, repo), root=repo), compute(resolve(tgt, repo), root=repo))
        for bid, (src, tgt, _sev) in bindings.items()
    }


def _severities(bindings: Bindings) -> dict[str, str]:
    return {bid: spec[2] for bid, spec in bindings.items()}


def _ledger_text(
    rows: list[tuple[str, str, str, str]],
    *,
    uncovered_max: int | None = None,
    binding_min: int | None = None,
) -> str:
    parts: list[str] = []
    coverage: list[str] = []
    if uncovered_max is not None:
        coverage.append(f"uncovered_max = {uncovered_max}")
    if binding_min is not None:
        coverage.append(f"binding_min = {binding_min}")
    if coverage:
        parts.append("[coverage]\n" + "\n".join(coverage) + "\n")
    for bid, source, target, disposition in rows:
        parts.append(
            "[[reviewed]]\n"
            f'id = "{bid}"\n'
            f'source_digest = "{source}"\n'
            f'target_digest = "{target}"\n'
            f'disposition = "{disposition}"\n'
        )
    return "\n".join(parts)


def _commit_ledger(repo: Path, text: str) -> None:
    """Land ``text`` as the PREVIOUS COMMITTED ledger — the only thing history rows read."""
    _write(repo, LEDGER_REL, text)
    assert git(repo, "add", "-A").returncode == 0
    done = git(repo, "commit", "-m", "ledger")
    assert done.returncode == 0, done.stderr


def _rows_for(repo: Path, bindings: Bindings, disposition: str) -> list[tuple[str, str, str, str]]:
    """One ledger row per binding carrying its CURRENT live digests."""
    live = _live(repo, bindings)
    return [(bid, live[bid][0], live[bid][1], disposition) for bid in sorted(bindings)]


def _observed(findings) -> list[tuple[str, str, str]]:
    return [(f.binding_id, f.reason, f.level) for f in findings]


@dataclass(frozen=True)
class Case:
    """One adversarial (or control) row: which fixture it needs, and what it sets up."""

    name: str
    fixture: str
    setup: Callable[[Path], tuple[Bindings, list[tuple[str, str, str]]]]


def _run(repo: Path, bindings: Bindings, repointed: frozenset[str] = frozenset()):
    """The production call sequence — load, retrieve previous committed, check.

    ``repointed`` is the CR-03 input: the ids whose ``(sources, target)`` meaning differs from the
    previous COMMITTED registry. These cases author no registry at all, so the default is empty —
    the same degrade-to-no-check posture an unreadable history takes everywhere else in this
    module. ``test_repointed_binding_is_unratified`` supplies it explicitly.
    """
    _coverage, rows = load_ledger(repo / LEDGER_REL)
    previous = previous_ledger(LEDGER_REL, repo)
    return check_coherence(rows, previous, _live(repo, bindings), _severities(bindings), repointed)


# ── the case setups ───────────────────────────────────────────────────────────────────────────


def _setup_paste_live_digest(repo: Path):
    """THE ATTACK. Previous committed row is (S0, T0, reviewed-no-change). The source is edited to
    S1; the ledger is edited to (S1, T0, "updated"); the TARGET DOCUMENT IS UNTOUCHED.

    Both live digests now equal the stored ones, so a digest-equality-only checker reports FRESH.
    """
    _commit_ledger(repo, _ledger_text(_rows_for(repo, _BASE, "reviewed-no-change")))
    _write(repo, "src/one.py", "ONE = 1  # edited\n")  # source moves S0 -> S1
    live = _live(repo, _BASE)
    rows = [
        ("one", live["one"][0], live["one"][1], "updated"),  # the pasted live source digest
        ("two", live["two"][0], live["two"][1], "reviewed-no-change"),
    ]
    _write(repo, LEDGER_REL, _ledger_text(rows))
    return _BASE, [("one", "disposition-incoherent", "fail")]


def _setup_new_binding_self_blessed(repo: Path):
    """THE SIBLING ATTACK. A brand-new required binding lands together with a matching
    ``reviewed-no-change`` row. Nothing in history contradicts it; both digests match."""
    _commit_ledger(repo, _ledger_text(_rows_for(repo, _BASE, "reviewed-no-change")))
    _write(repo, "src/four.py", "FOUR = 4\n")
    _write(repo, "docs/four.md", "four\n")
    bindings: Bindings = {**_BASE, "four": (["src/four.py"], ["docs/four.md"], "required")}
    _write(repo, LEDGER_REL, _ledger_text(_rows_for(repo, bindings, "reviewed-no-change")))
    return bindings, [("four", "first_seen-unratified", "fail")]


def _setup_new_binding_self_blessed_advisory(repo: Path):
    """Same shape, advisory severity — WARN, not FAIL."""
    _commit_ledger(repo, _ledger_text(_rows_for(repo, _BASE, "reviewed-no-change")))
    _write(repo, "src/five.py", "FIVE = 5\n")
    _write(repo, "docs/five.md", "five\n")
    bindings: Bindings = {**_BASE, "five": (["src/five.py"], ["docs/five.md"], "advisory")}
    _write(repo, LEDGER_REL, _ledger_text(_rows_for(repo, bindings, "reviewed-no-change")))
    return bindings, [("five", "first_seen-unratified", "warn")]


def _setup_new_binding_second_commit(repo: Path):
    """THE NON-DEGRADATION CONTROL. Same new binding, but its row IS in the previous committed
    ledger. Must be GREEN — otherwise ``first_seen-unratified`` has degraded into "a new binding
    can never be green", which passes the attack row while making the registry unusable."""
    _write(repo, "src/four.py", "FOUR = 4\n")
    _write(repo, "docs/four.md", "four\n")
    bindings: Bindings = {**_BASE, "four": (["src/four.py"], ["docs/four.md"], "required")}
    text = _ledger_text(_rows_for(repo, bindings, "reviewed-no-change"))
    _commit_ledger(repo, text)
    _write(repo, LEDGER_REL, text)
    return bindings, []


def _setup_honest_update(repo: Path):
    """NEGATIVE CONTROL for the ``updated`` half: source AND target both moved, ledger follows.
    Without this row the control could be "reject every ``updated``", which is not a control."""
    _commit_ledger(repo, _ledger_text(_rows_for(repo, _BASE, "reviewed-no-change")))
    _write(repo, "src/one.py", "ONE = 1  # edited\n")
    _write(repo, "docs/a.md", "alpha rewritten\n")
    live = _live(repo, _BASE)
    rows = [
        ("one", live["one"][0], live["one"][1], "updated"),
        ("two", live["two"][0], live["two"][1], "reviewed-no-change"),
    ]
    _write(repo, LEDGER_REL, _ledger_text(rows))
    return _BASE, []


def _setup_reviewed_no_change_exact(repo: Path):
    """D-04 half 1 is CONTENT-BOUND and therefore HISTORY-FREE: this runs in a tree with NO
    commits at all (``previous_ledger`` -> None) and must still be green."""
    _write(repo, LEDGER_REL, _ledger_text(_rows_for(repo, _BASE, "reviewed-no-change")))
    return _BASE, []


def _setup_reviewed_still_current_exact(repo: Path):
    """``REVIEWED_STILL_CURRENT`` is the ADR-facing alias of ``reviewed-no-change`` (D-09) and takes
    the same content-bound branch — ratified here by a previous committed row."""
    text = _ledger_text(_rows_for(repo, _BASE, "REVIEWED_STILL_CURRENT"))
    _commit_ledger(repo, text)
    _write(repo, LEDGER_REL, text)
    return _BASE, []


def _setup_reviewed_no_change_stale(repo: Path):
    """Ordinary staleness — and it must be DISTINGUISHABLE from ``disposition-incoherent``."""
    text = _ledger_text(_rows_for(repo, _BASE, "reviewed-no-change"))
    _commit_ledger(repo, text)
    _write(repo, "src/one.py", "ONE = 1  # edited\n")
    _write(repo, LEDGER_REL, text)  # ledger still carries S0
    return _BASE, [("one", "stale-digest", "fail")]


def _setup_updated_but_row_is_new(repo: Path):
    """An ``updated`` claim with NO corresponding row in the previous committed ledger — there is
    nothing to compute a target delta against, so it is unverifiable, not silently accepted."""
    _commit_ledger(
        repo,
        _ledger_text([r for r in _rows_for(repo, _BASE, "reviewed-no-change") if r[0] == "two"]),
    )
    live = _live(repo, _BASE)
    rows = [
        ("one", live["one"][0], live["one"][1], "updated"),
        ("two", live["two"][0], live["two"][1], "reviewed-no-change"),
    ]
    _write(repo, LEDGER_REL, _ledger_text(rows))
    return _BASE, [("one", "unverified-disposition", "fail")]


def _setup_unknown_id(repo: Path):
    """Blessing a binding that does not exist (research Q5 corollary)."""
    rows = _rows_for(repo, _BASE, "reviewed-no-change")
    _commit_ledger(repo, _ledger_text(rows))
    ghost = "0" * 64
    _write(repo, LEDGER_REL, _ledger_text([*rows, ("ghost", ghost, ghost, "reviewed-no-change")]))
    return _BASE, [("ghost", "unknown-binding", "fail")]


def _setup_unverifiable_history_required(repo: Path):
    """D-08: no ``HEAD`` at all — ``git show`` cannot retrieve any previous ledger."""
    live = _live(repo, _BASE)
    _write(repo, LEDGER_REL, _ledger_text([("one", live["one"][0], live["one"][1], "updated")]))
    return _BASE, [("one", "unverified-disposition", "fail")]


def _setup_unverifiable_history_advisory(repo: Path):
    live = _live(repo, _BASE)
    _write(repo, LEDGER_REL, _ledger_text([("two", live["two"][0], live["two"][1], "updated")]))
    return _BASE, [("two", "unverified-disposition", "warn")]


def _setup_superseding_adr_required(repo: Path):
    """An OPEN OBLIGATION can never contribute a green state, digest-exact or not — otherwise it
    would be a rubber stamp with extra syllables (D-09)."""
    rows = _rows_for(repo, _BASE, "reviewed-no-change")
    _commit_ledger(repo, _ledger_text(rows))
    live = _live(repo, _BASE)
    _write(
        repo,
        LEDGER_REL,
        _ledger_text(
            [
                ("one", live["one"][0], live["one"][1], "SUPERSEDING_ADR_REQUIRED"),
                ("two", live["two"][0], live["two"][1], "reviewed-no-change"),
            ]
        ),
    )
    return _BASE, [("one", "superseding-adr-required", "fail")]


def _setup_binding_count_regression(repo: Path):
    """The committed ratchet demands 3 bindings; the live registry has 2 — a deletion."""
    _commit_ledger(repo, _ledger_text(_rows_for(repo, _BASE, "reviewed-no-change"), binding_min=3))
    _write(repo, LEDGER_REL, _ledger_text(_rows_for(repo, _BASE, "reviewed-no-change")))
    return _BASE, [("", "binding-count-regression", "fail")]


def _setup_binding_count_equal(repo: Path):
    _commit_ledger(repo, _ledger_text(_rows_for(repo, _BASE, "reviewed-no-change"), binding_min=2))
    _write(repo, LEDGER_REL, _ledger_text(_rows_for(repo, _BASE, "reviewed-no-change")))
    return _BASE, []


def _setup_binding_count_grew(repo: Path):
    _commit_ledger(repo, _ledger_text(_rows_for(repo, _BASE, "reviewed-no-change"), binding_min=1))
    _write(repo, LEDGER_REL, _ledger_text(_rows_for(repo, _BASE, "reviewed-no-change")))
    return _BASE, [("", "binding-count-can-tighten", "note")]


def _setup_binding_deleted_outside_corpus(repo: Path):
    """``binding_min`` is INDEPENDENTLY NECESSARY, not redundant with ``uncovered_max``.

    The deleted binding's target (``src/two.py``'s doc twin, here ``notes/side.md``) sits OUTSIDE
    D-07's human corpus, so the uncovered ratchet would not move by a single count. Only the
    binding-count ratchet sees the deletion at all.
    """
    _write(repo, "notes/side.md", "side\n")
    wide: Bindings = {**_BASE, "side": (["src/two.py"], ["notes/side.md"], "required")}
    _commit_ledger(
        repo,
        _ledger_text(_rows_for(repo, wide, "reviewed-no-change"), uncovered_max=0, binding_min=3),
    )
    # The attacker deletes the `side` binding from the registry AND its ledger row. Nothing in the
    # human corpus changed, so an uncovered-count ratchet observes exactly nothing.
    _write(repo, LEDGER_REL, _ledger_text(_rows_for(repo, _BASE, "reviewed-no-change")))
    return _BASE, [("", "binding-count-regression", "fail")]


COHERENCE_CASES: tuple[Case, ...] = (
    Case("paste_live_digest", "docs_repo", _setup_paste_live_digest),
    Case("new_binding_self_blessed", "docs_repo", _setup_new_binding_self_blessed),
    Case(
        "new_binding_self_blessed_advisory", "docs_repo", _setup_new_binding_self_blessed_advisory
    ),
    Case("new_binding_second_commit", "docs_repo", _setup_new_binding_second_commit),
    Case("honest_update", "docs_repo", _setup_honest_update),
    Case("reviewed_no_change_exact", "empty_repo", _setup_reviewed_no_change_exact),
    Case("reviewed_still_current_exact", "docs_repo", _setup_reviewed_still_current_exact),
    Case("reviewed_no_change_stale", "docs_repo", _setup_reviewed_no_change_stale),
    Case("updated_but_row_is_new", "docs_repo", _setup_updated_but_row_is_new),
    Case("unknown_id", "docs_repo", _setup_unknown_id),
    Case("unverifiable_history_required", "empty_repo", _setup_unverifiable_history_required),
    Case("unverifiable_history_advisory", "empty_repo", _setup_unverifiable_history_advisory),
    Case("superseding_adr_required", "docs_repo", _setup_superseding_adr_required),
    Case("binding_count_regression", "docs_repo", _setup_binding_count_regression),
    Case("binding_count_equal", "docs_repo", _setup_binding_count_equal),
    Case("binding_count_grew", "docs_repo", _setup_binding_count_grew),
    Case("binding_deleted_outside_corpus", "docs_repo", _setup_binding_deleted_outside_corpus),
)


# ── fixtures ──────────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def empty_repo(tmp_path: Path) -> Path:
    """A REAL ``git init`` tree with NO commits — ``git show HEAD:./...`` genuinely cannot resolve.

    Needed by the two D-08 rows and by ``reviewed_no_change_exact``'s history-free proof. The
    ``docs_repo`` fixture always seeds a commit, so this is its no-``HEAD`` sibling; both use the
    same real-git posture (fixed argv, per-invocation identity, never a mock).
    """
    repo = tmp_path / "empty"
    repo.mkdir()
    assert git(repo, "init", "--initial-branch=main").returncode == 0
    _write(repo, "docs/a.md", "alpha\n")
    _write(repo, "docs/nested/b.md", "bravo\n")
    _write(repo, "src/one.py", "ONE = 1\n")
    _seed_extra(repo)
    return repo


@pytest.fixture
def prepared_repo(docs_repo: Path) -> Path:
    """``docs_repo`` plus the extra seed file, committed — the uniform starting tree."""
    _seed_extra(docs_repo)
    assert git(docs_repo, "add", "-A").returncode == 0
    assert git(docs_repo, "commit", "-m", "extra seed").returncode == 0
    return docs_repo


# ── the coherence table ───────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("case", COHERENCE_CASES, ids=[c.name for c in COHERENCE_CASES])
def test_coherence_case(request: pytest.FixtureRequest, case: Case) -> None:
    repo: Path = request.getfixturevalue(
        "prepared_repo" if case.fixture == "docs_repo" else case.fixture
    )
    bindings, expected = case.setup(repo)

    findings = _run(repo, bindings)

    assert _observed(findings) == sorted(expected), (
        f"{case.name}: finding set mismatch — expected {sorted(expected)}, "
        f"got {_observed(findings)}"
    )


def test_paste_live_digest_names_the_binding(prepared_repo: Path) -> None:
    """The attack's finding must NAME the binding id and say what is wrong — a bare reason string
    would leave an operator guessing which row to look at."""
    bindings, _ = _setup_paste_live_digest(prepared_repo)

    findings = _run(prepared_repo, bindings)

    assert findings, "expected a `disposition-incoherent` finding, got none"
    incoherent = [f for f in findings if f.reason == "disposition-incoherent"]
    assert incoherent, "expected a `disposition-incoherent` finding, got none"
    assert incoherent[0].binding_id == "one"
    assert "one" in incoherent[0].message
    assert "target digest is unchanged" in incoherent[0].message


def test_new_binding_self_blessed_names_the_binding(prepared_repo: Path) -> None:
    bindings, _ = _setup_new_binding_self_blessed(prepared_repo)

    findings = _run(prepared_repo, bindings)

    first_seen = [f for f in findings if f.reason == "first_seen-unratified"]
    assert first_seen, "expected a `first_seen-unratified` finding, got none"
    assert first_seen[0].binding_id == "four"
    assert "four" in first_seen[0].message


def test_binding_count_regression_names_both_counts(prepared_repo: Path) -> None:
    bindings, _ = _setup_binding_count_regression(prepared_repo)

    findings = _run(prepared_repo, bindings)
    regressions = [f for f in findings if f.reason == "binding-count-regression"]

    assert regressions, "DID NOT report a binding-count regression"
    assert "2" in regressions[0].message and "3" in regressions[0].message, (
        "the message must name BOTH the live count and the committed ratchet"
    )


def test_binding_count_grew_suggests_tightening(prepared_repo: Path) -> None:
    bindings, _ = _setup_binding_count_grew(prepared_repo)

    findings = _run(prepared_repo, bindings)

    assert not [f for f in findings if f.level == "fail"], "growing the registry must not fail"
    assert any("ratchet can tighten: set binding_min = 2" in f.message for f in findings), (
        "DID NOT emit the exact tighten suggestion"
    )


def test_binding_deleted_outside_corpus_is_invisible_to_uncovered(prepared_repo: Path) -> None:
    """The independence proof: the deleted binding's target is outside D-07's corpus, so the
    uncovered ratchet stored in the ledger does not move AT ALL — yet the deletion is caught."""
    bindings, _ = _setup_binding_deleted_outside_corpus(prepared_repo)
    previous = previous_ledger(LEDGER_REL, prepared_repo)
    coverage, _rows = load_ledger(prepared_repo / LEDGER_REL)

    assert previous is not None
    assert previous["coverage"]["uncovered_max"] == 0
    assert coverage.get("uncovered_max") is None, (
        "fixture sanity: the working ledger carries no uncovered signal for this deletion"
    )
    assert [f.reason for f in _run(prepared_repo, bindings)] == ["binding-count-regression"]


def test_the_three_reason_constants_are_pairwise_distinct() -> None:
    """``unverified-disposition`` (history unreadable), ``first_seen-unratified`` (never ratified)
    and the staleness reason have three DIFFERENT remedies. An indistinguishable failure teaches
    the wrong fix (D-08), so the constants must be pairwise distinct string literals."""
    constants = [
        ledger_module.REASON_UNVERIFIED,
        ledger_module.REASON_FIRST_SEEN,
        ledger_module.REASON_STALE,
    ]

    assert all(isinstance(value, str) and value for value in constants)
    assert len(set(constants)) == 3, f"reason constants are not pairwise distinct: {constants}"
    assert ledger_module.REASON_UNVERIFIED == "unverified-disposition"
    assert ledger_module.REASON_FIRST_SEEN == "first_seen-unratified"


def test_reviewed_no_change_consults_no_history(empty_repo: Path) -> None:
    """Explicit restatement of D-04 half 1: content-bound means history-free. Passing ``None`` for
    the previous ledger — the shape a repo with no ``HEAD`` produces — must still be green."""
    bindings, _ = _setup_reviewed_no_change_exact(empty_repo)
    _coverage, rows = load_ledger(empty_repo / LEDGER_REL)

    assert (
        check_coherence(rows, None, _live(empty_repo, bindings), _severities(bindings), frozenset())
        == []
    )


def test_repointed_binding_is_unratified(prepared_repo: Path) -> None:
    """CR-03 at the unit level: an id that IS in the previous committed ledger, whose digests match
    the tree exactly, is still unratified when the registry has repointed it.

    The row and the tree agree by construction — that is the whole difficulty — so nothing in the
    row's CONTENT can contradict it. Only "does the registry still mean by this id what it meant
    when the row was committed?" can. The guard-level fixture
    (``test_repointing_a_ratified_binding_is_not_fresh``) drives the same rule end to end through a
    real repointed registry; this row pins the ledger's half in isolation.
    """
    text = _ledger_text(_rows_for(prepared_repo, _BASE, "reviewed-no-change"))
    _commit_ledger(prepared_repo, text)
    _write(prepared_repo, LEDGER_REL, text)

    assert _observed(_run(prepared_repo, _BASE)) == [], "control: unrepointed and ratified is green"

    observed = _observed(_run(prepared_repo, _BASE, frozenset({"one"})))

    assert observed == [("one", "first_seen-unratified", "fail")]


def test_repointed_updated_claim_is_unratified(prepared_repo: Path) -> None:
    """The ``updated`` half takes the same closure: a prior row exists, but it ratified a DIFFERENT
    pair, so the target delta would compare two unrelated documents."""
    _commit_ledger(
        prepared_repo, _ledger_text(_rows_for(prepared_repo, _BASE, "reviewed-no-change"))
    )
    _write(prepared_repo, "src/one.py", "ONE = 1  # edited\n")
    _write(prepared_repo, "docs/a.md", "alpha rewritten\n")
    live = _live(prepared_repo, _BASE)
    _write(
        prepared_repo,
        LEDGER_REL,
        _ledger_text(
            [
                ("one", live["one"][0], live["one"][1], "updated"),
                ("two", live["two"][0], live["two"][1], "reviewed-no-change"),
            ]
        ),
    )

    assert _observed(_run(prepared_repo, _BASE)) == [], "control: an honest update is green"

    observed = _observed(_run(prepared_repo, _BASE, frozenset({"one"})))

    assert observed == [("one", "first_seen-unratified", "fail")]


def test_stale_is_not_disposition_incoherent(prepared_repo: Path) -> None:
    """The two failures must be tellable apart — same digests-disagree symptom, different fix."""
    bindings, _ = _setup_reviewed_no_change_stale(prepared_repo)

    reasons = {f.reason for f in _run(prepared_repo, bindings)}

    assert reasons == {"stale-digest"}
    assert "disposition-incoherent" not in reasons


# ── the forbidden-key table (DOCSUP-02) ───────────────────────────────────────────────────────

_PERMITTED = _ledger_text(
    [("one", "a" * 64, "b" * 64, "reviewed-no-change")], uncovered_max=0, binding_min=1
)

FORBIDDEN_KEY_CASES: tuple[tuple[str, str, str], ...] = (
    # Wall-clock, in four spellings — a denylist would have to anticipate every one of them.
    ("reviewed_at", 'reviewed_at = "x"', "reviewed_at"),
    ("date", 'date = "x"', "date"),
    ("updated_at", 'updated_at = "x"', "updated_at"),
    ("timestamp", "timestamp = 1", "timestamp"),
    # Human identity.
    ("reviewer", 'reviewer = "x"', "reviewer"),
    ("author", 'author = "x"', "author"),
    ("approved_by", 'approved_by = "x"', "approved_by"),
    # Prose copy — the ledger records a decision, never a paraphrase of the document.
    ("excerpt", 'excerpt = "x"', "excerpt"),
    ("note", 'note = "x"', "note"),
    ("summary", 'summary = "x"', "summary"),
    # Model identity.
    ("model_key", 'model = "x"', "model"),
)


@pytest.mark.parametrize(
    ("case", "extra", "token"), FORBIDDEN_KEY_CASES, ids=[row[0] for row in FORBIDDEN_KEY_CASES]
)
def test_forbidden_key_is_rejected(tmp_path: Path, case: str, extra: str, token: str) -> None:
    """Rejected at load, not merely ignored: a silently-ignored key lets one accumulate."""
    path = tmp_path / "ledger.toml"
    path.write_text(_PERMITTED + extra + "\n", encoding="utf-8")

    with pytest.raises(LedgerError) as excinfo:
        load_ledger(path)

    assert token in str(excinfo.value), f"{case}: DID NOT NAME the offending key"


def test_forbidden_model_identifier_as_a_value(tmp_path: Path) -> None:
    """A model identifier as a VALUE, not a key — a careless paste is the realistic vector, and the
    ledger is the one new committed artifact of this phase.

    The fixture is a SHAPE-matching but NON-EXISTENT id. CLAUDE.md's non-negotiable ("no model
    identifier in a repo artifact") reads on the artifact, not on the author's intent, so a live id
    committed as executable test data violates it exactly as a live id in a comment would."""
    path = tmp_path / "ledger.toml"
    path.write_text(
        _ledger_text([("claude-opus-0-0", "a" * 64, "b" * 64, "reviewed-no-change")]),
        encoding="utf-8",
    )

    with pytest.raises(LedgerError) as excinfo:
        load_ledger(path)

    assert "model identifier" in str(excinfo.value)


def test_binding_id_naming_a_claude_md_target_is_not_a_model_identifier(tmp_path: Path) -> None:
    """NEGATIVE CONTROL for the scan above. D-07's corpus includes root ``CLAUDE.md``, so a binding
    id that names it is ordinary and must load. The scan is anchored on vendor+model SHAPE
    (``claude-opus``, ``gpt-4``, ``anthropic/...``), never on the bare vendor word — mirroring
    ``secret_scan``'s shape-anchored posture rather than a keyword blocklist."""
    path = tmp_path / "ledger.toml"
    path.write_text(
        _ledger_text([("claude-md-vs-agents-md", "a" * 64, "b" * 64, "reviewed-no-change")]),
        encoding="utf-8",
    )

    _coverage, rows = load_ledger(path)

    assert [row.id for row in rows] == ["claude-md-vs-agents-md"]


FORBIDDEN_SHAPE_CASES: tuple[tuple[str, str, str], ...] = (
    ("unknown_top_level_table", "[extras]\nx = 1\n", "extras"),
    ("unknown_coverage_key", "[coverage]\nuncovered_max = 0\nfudge = 1\n", "fudge"),
    (
        "short_digest",
        '[[reviewed]]\nid = "one"\nsource_digest = "abc"\ntarget_digest = "'
        + "b" * 64
        + '"\ndisposition = "updated"\n',
        "source_digest",
    ),
    (
        "unknown_disposition",
        '[[reviewed]]\nid = "one"\nsource_digest = "'
        + "a" * 64
        + '"\ntarget_digest = "'
        + "b" * 64
        + '"\ndisposition = "looks-fine"\n',
        "looks-fine",
    ),
    (
        "missing_required_key",
        '[[reviewed]]\nid = "one"\nsource_digest = "' + "a" * 64 + '"\ndisposition = "updated"\n',
        "target_digest",
    ),
)


@pytest.mark.parametrize(
    ("case", "text", "token"),
    FORBIDDEN_SHAPE_CASES,
    ids=[row[0] for row in FORBIDDEN_SHAPE_CASES],
)
def test_forbidden_shape_is_rejected(tmp_path: Path, case: str, text: str, token: str) -> None:
    path = tmp_path / "ledger.toml"
    path.write_text(text, encoding="utf-8")

    with pytest.raises(LedgerError) as excinfo:
        load_ledger(path)

    assert token in str(excinfo.value), f"{case}: DID NOT NAME the offending element"


def test_permitted_shape_loads_cleanly(tmp_path: Path) -> None:
    """NEGATIVE CONTROL for the whole allowlist, and the ``0`` vs absent distinction: a ratchet of
    zero is a legitimate — indeed the strictest — value and must not read as "unset"."""
    path = tmp_path / "ledger.toml"
    path.write_text(_PERMITTED, encoding="utf-8")

    coverage, rows = load_ledger(path)

    assert coverage["uncovered_max"] == 0
    assert coverage["uncovered_max"] is not None
    assert coverage["binding_min"] == 1
    assert [(r.id, r.disposition) for r in rows] == [("one", "reviewed-no-change")]


def test_missing_ledger_is_not_invalid(tmp_path: Path) -> None:
    """A repo that has not seeded a ledger yet is empty, not broken."""
    assert load_ledger(tmp_path / "absent.toml") == ({}, [])


def test_rows_are_sorted_by_id(tmp_path: Path) -> None:
    path = tmp_path / "ledger.toml"
    path.write_text(
        _ledger_text(
            [
                ("zulu", "a" * 64, "b" * 64, "updated"),
                ("alpha", "c" * 64, "d" * 64, "updated"),
            ]
        ),
        encoding="utf-8",
    )

    _coverage, rows = load_ledger(path)

    assert [row.id for row in rows] == ["alpha", "zulu"]


def test_corrupt_ledger_raises_ledger_error_without_content(tmp_path: Path) -> None:
    """T-28-22: a corrupt ledger must not crash the gate with a traceback, and the message must not
    echo file content back out."""
    path = tmp_path / "ledger.toml"
    path.write_text("[[reviewed]\nid = 'unterminated\n", encoding="utf-8")

    with pytest.raises(LedgerError) as excinfo:
        load_ledger(path)

    assert "unterminated" not in str(excinfo.value)


# ── previous_ledger: the real git path, never mocked ──────────────────────────────────────────


def test_previous_ledger_reads_the_committed_file(prepared_repo: Path) -> None:
    _commit_ledger(prepared_repo, _PERMITTED)
    _write(prepared_repo, LEDGER_REL, _ledger_text([]))  # working tree diverges

    previous = previous_ledger(LEDGER_REL, prepared_repo)

    assert previous is not None
    assert previous["reviewed"][0]["id"] == "one"


def test_previous_ledger_degrades_to_none_without_head(empty_repo: Path) -> None:
    """Retrieval NEVER raises into the gate (T-28-22)."""
    _write(empty_repo, LEDGER_REL, _PERMITTED)

    assert previous_ledger(LEDGER_REL, empty_repo) is None


def test_previous_ledger_degrades_to_none_when_uncommitted(prepared_repo: Path) -> None:
    """The ledger exists in the working tree but was never committed — history is unreadable, which
    is a DIFFERENT fact from "the row was never ratified"."""
    _write(prepared_repo, LEDGER_REL, _PERMITTED)

    assert previous_ledger(LEDGER_REL, prepared_repo) is None


def test_previous_ledger_uses_fixed_argv_without_a_shell(prepared_repo: Path) -> None:
    """T-28-20: no ledger- or registry-derived value ever reaches a shell."""
    source = inspect.getsource(ledger_module)

    assert "shell=False" in source
    assert "shell=True" not in source
    assert 'f"HEAD:./{' in source, "the ./ prefix keeps resolution working-directory-relative"


# ── D-06: the guard cannot write the ledger, structurally ─────────────────────────────────────

_ALLOWED_PUBLIC_NAMES = frozenset(
    {
        "Finding",
        "LedgerError",
        "ReviewedRow",
        "CONTENT_BOUND_DISPOSITIONS",
        "DISPOSITIONS",
        "LEDGER_PATH",
        "LEVEL_FAIL",
        "LEVEL_NOTE",
        "LEVEL_WARN",
        "REASON_BINDING_COUNT",
        "REASON_BINDING_COUNT_TIGHTEN",
        "REASON_FIRST_SEEN",
        "REASON_INCOHERENT",
        "REASON_OPEN_OBLIGATION",
        "REASON_STALE",
        "REASON_UNKNOWN_BINDING",
        "REASON_UNVERIFIED",
        "check_coherence",
        "load_ledger",
        "previous_document",
        "previous_ledger",
    }
)

_WRITER_NAME_RE = re.compile(r"write|save|update|bump|set_", re.IGNORECASE)

_WRITE_CALL_TOKENS = (
    "write_text",
    "write_bytes",
    "os.replace",
    "shutil",
    "tomli_w",
    "open(",
)


def _module_public_names(module) -> set[str]:
    names: set[str] = set()
    for name, obj in vars(module).items():
        if name.startswith("_") or inspect.ismodule(obj):
            continue
        owner = getattr(obj, "__module__", None)
        if owner is not None and owner != module.__name__:
            continue  # an imported symbol (Path, dataclass, ...), not this module's surface
        names.add(name)
    return names


def _write_call_tokens(text: str) -> list[str]:
    """Every write-shaped token present in ``text`` — the static scan, kept separate so a live
    negative control can prove it is capable of failing."""
    return [token for token in _WRITE_CALL_TOKENS if token in text]


def test_ledger_module_exposes_no_writer() -> None:
    """D-06 is STRUCTURAL: there is no writer to call, not merely no call to a writer."""
    public = _module_public_names(ledger_module)

    assert public == set(_ALLOWED_PUBLIC_NAMES), (
        f"public surface drifted from the allowlist: "
        f"unexpected {sorted(public - _ALLOWED_PUBLIC_NAMES)}, "
        f"missing {sorted(_ALLOWED_PUBLIC_NAMES - public)}"
    )
    offenders = sorted(name for name in public if _WRITER_NAME_RE.search(name))
    assert not offenders, f"writer-shaped public names present: {offenders}"


def test_ledger_module_source_has_no_write_call() -> None:
    """A gate that can lower its own threshold is self-blessing — so the module must contain no
    filesystem write at all. ``uncovered_max`` and ``binding_min`` are HUMAN edits."""
    source = inspect.getsource(ledger_module)

    assert _write_call_tokens(source) == [], (
        f"ledger.py contains write-shaped calls: {_write_call_tokens(source)}"
    )


def test_negative_control_write_scan_flags_planted_token() -> None:
    """LIVE NEGATIVE CONTROL — the scan above is capable of failing. An unfailable test is not
    coverage (mirrors test_inject_determinism.py:87-89)."""
    assert _write_call_tokens('path.write_text("gotcha")') == ["write_text"]
    assert _write_call_tokens("import tomli_w") == ["tomli_w"]


@pytest.mark.parametrize("case", COHERENCE_CASES, ids=[c.name for c in COHERENCE_CASES])
def test_check_coherence_does_not_mutate_ledger(request: pytest.FixtureRequest, case: Case) -> None:
    """Byte-identity across every case: reading the ledger never rewrites it.

    Parametrized rather than looped so each row gets a FRESH repo — ``getfixturevalue`` caches per
    test, and a shared tree would let one case's committed ledger leak into the next.
    """
    repo: Path = request.getfixturevalue(
        "prepared_repo" if case.fixture == "docs_repo" else case.fixture
    )
    bindings, _expected = case.setup(repo)
    ledger_path = repo / LEDGER_REL
    before = hashlib.sha256(ledger_path.read_bytes()).hexdigest()

    _run(repo, bindings)

    after = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
    assert before == after, f"{case.name}: the ledger file changed during a read-only check"
