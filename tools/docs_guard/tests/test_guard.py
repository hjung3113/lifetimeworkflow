"""DOCSUP-03 adversarial tables for the five-state classifier, both ratchets, and drift suppression.

The phase's anti-pattern fence: every table below was authored BEFORE ``guard.py`` and shown RED
against a THROWAWAY classifier that (a) checked staleness before brokenness, (b) counted the
uncovered corpus with a plain filesystem walk, and (c) ignored ``run_gate`` entirely. The verbatim
failure output is recorded in ``28-05-SUMMARY.md`` under ``## RED evidence``.

Three tables, and each row is constructed so a NAIVE evaluation order gets it wrong:

``STATE_ORDER_CASES``
    First-match-wins with ``BROKEN`` ordered before every staleness check (D-05).
    ``broken_beats_stale`` and ``broken_zero_expansion`` prove the ORDER, not merely the state set;
    ``advisory_no_ledger_row`` is the negative control that keeps "no row" from collapsing into
    "always broken". ``first_seen_never_fresh`` is the SELF-GREEN CLOSURE at the classifier level —
    digest equality is NECESSARY but not SUFFICIENT for green — and ``second_commit_is_fresh`` is
    its non-degradation
    control, so the rule cannot become "a new binding can never be green".

``RATCHET_CASES`` (+ their structural siblings)
    Both ratchets are READ-ONLY (D-06). ``ratchet_not_written`` asserts the ledger file is
    BYTE-IDENTICAL after a full classify and backs it with a static no-write scan carrying a live
    planted-token negative control, so the scan is known-live rather than vacuously green.
    ``binding_deleted_outside_corpus`` proves the two ratchets are NOT interchangeable.
    ``uncovered_untracked_file`` is Phase 26's CR-01: an untracked working-tree file must not move
    the count, or CI's clean checkout disagrees with a developer's tree.

``SUPPRESSION_CASES``
    D-13. Contract-drift and golden stay LEADING and authoritative, so a binding whose source is a
    currently-drifted contract reports ``SUPPRESSED``, never ``STALE_REQUIRED`` — with a negative
    control proving suppression is conditional, and a test proving ``run_gate``'s findings are never
    carried forward into this gate's output.

No test mocks ``git``. Every history row runs against the real ``docs_repo`` tree (conftest.py).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from tools.adoption_scan.destinations import DERIVED_GLOBS
from tools.docs_guard import guard
from tools.docs_guard.digest import compute, resolve
from tools.docs_guard.tests.conftest import git

REG_REL = "docs/doc-dependencies.toml"
LED_REL = "docs/.docs-review-ledger.toml"

# The corpus files every ratchet case seeds on top of the docs_repo seed tree. Six tracked files,
# one per D-07 corpus category, so a miscount is attributable to a category rather than a total.
_CORPUS_SEED: dict[str, str] = {
    "docs/how-to/one.md": "how-to one\n",
    "docs/how-to/two.md": "how-to two\n",
    "docs/tutorials/first.md": "tutorial\n",
    "docs/explanation/why.md": "why\n",
    "docs/glossary.md": "glossary\n",
    ".memory/README.md": "memory readme\n",
}


# ── helpers ─────────────────────────────────────────────────────────────────────────────────────


def _write(repo: Path, rel: str, text: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed(repo: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        _write(repo, rel, text)


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
    dispositions: tuple[str, ...] = ("updated", "reviewed-no-change"),
) -> str:
    return (
        "[[binding]]\n"
        f"id = {json.dumps(id)}\n"
        f"sources = [{', '.join(json.dumps(s) for s in sources)}]\n"
        f"target = {json.dumps(target)}\n"
        f"severity = {json.dumps(severity)}\n"
        f"dispositions = [{', '.join(json.dumps(d) for d in dispositions)}]\n"
    )


def _ledger_toml(
    rows: tuple[tuple[str, str, str, str], ...] = (),
    coverage: dict[str, int] | None = None,
) -> str:
    parts: list[str] = []
    if coverage is not None:
        body = "".join(f"{key} = {value}\n" for key, value in sorted(coverage.items()))
        parts.append("[coverage]\n" + body)
    for row_id, source_digest, target_digest, disposition in rows:
        parts.append(
            "[[reviewed]]\n"
            f"id = {json.dumps(row_id)}\n"
            f"source_digest = {json.dumps(source_digest)}\n"
            f"target_digest = {json.dumps(target_digest)}\n"
            f"disposition = {json.dumps(disposition)}\n"
        )
    return "\n".join(parts) if parts else "[coverage]\n"


def _digests(repo: Path, sources: tuple[str, ...], target: str) -> tuple[str, str]:
    """The live ``(source, target)`` digest pair for a binding, computed the way the guard does."""
    return (
        compute(resolve(sources, repo), repo),
        compute(resolve([target], repo), repo),
    )


def _clean_gate() -> dict:
    """A ``run_gate``-shaped result with nothing drifted."""
    return {"ok": True, "drifted": []}


@dataclass(frozen=True)
class Setup:
    """One table row's expected outcome, produced by its builder after it has staged the tree."""

    binding_id: str
    expected_state: str
    expected_ok: bool
    drift_gate: Callable[[], dict] = _clean_gate
    reason_fragment: str = ""
    notes: tuple[str, ...] = field(default_factory=tuple)


def _classify(repo: Path, setup: Setup) -> dict:
    return guard.classify(
        registry_path=repo / REG_REL,
        ledger_path=repo / LED_REL,
        root=repo,
        drift_gate=setup.drift_gate,
    )


def _state_of(result: dict, binding_id: str) -> str:
    for entry in result["bindings"]:
        if entry["id"] == binding_id:
            return entry["state"]
    raise AssertionError(f"binding {binding_id!r} absent from the result")


# ── STATE_ORDER_CASES builders ──────────────────────────────────────────────────────────────────

_ONE = ("src/one.py",)
_TARGET = "docs/how-to/one.md"


def _setup_broken_beats_stale(repo: Path) -> Setup:
    """Target DELETED *and* digests stale. A staleness-first classifier says STALE_REQUIRED."""
    _write(repo, _TARGET, "v1\n")
    _commit(repo, "seed target")
    source_digest, target_digest = _digests(repo, _ONE, _TARGET)
    _write(repo, "src/one.py", "ONE = 2\n")  # source moves -> the ledger row is genuinely stale
    (repo / _TARGET).unlink()  # ... and the target is gone, which must WIN
    _write(repo, REG_REL, _binding_toml(id="how-to-one", sources=_ONE, target=_TARGET))
    _write(
        repo,
        LED_REL,
        _ledger_toml((("how-to-one", source_digest, target_digest, "reviewed-no-change"),)),
    )
    return Setup("how-to-one", "BROKEN", False, reason_fragment="target")


def _setup_broken_zero_expansion(repo: Path) -> Setup:
    """A selector expanding to ZERO paths while every digest matches. Digest-first says FRESH."""
    _write(repo, _TARGET, "v1\n")
    _commit(repo, "seed target")
    sources = ("libs/gone/**",)
    # compute([]) is a perfectly well-formed digest, so the ledger row below is digest-CONSISTENT.
    # That is the whole point of the row: consistency is not coverage.
    source_digest, target_digest = _digests(repo, sources, _TARGET)
    _write(repo, REG_REL, _binding_toml(id="how-to-one", sources=sources, target=_TARGET))
    _write(
        repo,
        LED_REL,
        _ledger_toml((("how-to-one", source_digest, target_digest, "reviewed-no-change"),)),
    )
    return Setup("how-to-one", "BROKEN", False, reason_fragment="zero")


def _setup_broken_no_ledger_row_required(repo: Path) -> Setup:
    _write(repo, _TARGET, "v1\n")
    _commit(repo, "seed target")
    _write(repo, REG_REL, _binding_toml(id="how-to-one", sources=_ONE, target=_TARGET))
    return Setup("how-to-one", "BROKEN", False, reason_fragment="reviewed")


def _setup_advisory_no_ledger_row(repo: Path) -> Setup:
    """Negative control for the row above — 'no row' must not collapse into 'always broken'."""
    _write(repo, _TARGET, "v1\n")
    _commit(repo, "seed target")
    _write(
        repo,
        REG_REL,
        _binding_toml(id="how-to-one", sources=_ONE, target=_TARGET, severity="advisory"),
    )
    return Setup("how-to-one", "STALE_ADVISORY", True)


def _setup_fresh(repo: Path) -> Setup:
    _write(repo, _TARGET, "v1\n")
    _commit(repo, "seed target")
    source_digest, target_digest = _digests(repo, _ONE, _TARGET)
    _write(repo, REG_REL, _binding_toml(id="how-to-one", sources=_ONE, target=_TARGET))
    _write(
        repo,
        LED_REL,
        _ledger_toml((("how-to-one", source_digest, target_digest, "reviewed-no-change"),)),
    )
    return Setup("how-to-one", "FRESH", True)


def _setup_stale_required(repo: Path) -> Setup:
    _write(repo, _TARGET, "v1\n")
    _commit(repo, "seed target")
    source_digest, target_digest = _digests(repo, _ONE, _TARGET)
    _write(repo, "src/one.py", "ONE = 2\n")
    _write(repo, REG_REL, _binding_toml(id="how-to-one", sources=_ONE, target=_TARGET))
    _write(
        repo,
        LED_REL,
        _ledger_toml((("how-to-one", source_digest, target_digest, "reviewed-no-change"),)),
    )
    return Setup("how-to-one", "STALE_REQUIRED", False)


def _setup_stale_advisory(repo: Path) -> Setup:
    _write(repo, _TARGET, "v1\n")
    _commit(repo, "seed target")
    source_digest, target_digest = _digests(repo, _ONE, _TARGET)
    _write(repo, "src/one.py", "ONE = 2\n")
    _write(
        repo,
        REG_REL,
        _binding_toml(id="how-to-one", sources=_ONE, target=_TARGET, severity="advisory"),
    )
    _write(
        repo,
        LED_REL,
        _ledger_toml((("how-to-one", source_digest, target_digest, "reviewed-no-change"),)),
    )
    return Setup("how-to-one", "STALE_ADVISORY", True)


_ADR_TARGET = "docs/adr/0009-accepted.md"
_ADR_PAIR = ("REVIEWED_STILL_CURRENT", "SUPERSEDING_ADR_REQUIRED")


def _setup_superseding_adr_never_fresh(repo: Path) -> Setup:
    """An OPEN OBLIGATION with both digests matching. Discharged by a superseding ADR, never by
    the digests agreeing (D-09)."""
    _write(repo, _ADR_TARGET, "# 9. Accepted\n\n- **Status:** accepted\n")
    _commit(repo, "seed adr")
    source_digest, target_digest = _digests(repo, _ONE, _ADR_TARGET)
    _write(
        repo,
        REG_REL,
        _binding_toml(id="adr-nine", sources=_ONE, target=_ADR_TARGET, dispositions=_ADR_PAIR),
    )
    _write(
        repo,
        LED_REL,
        _ledger_toml((("adr-nine", source_digest, target_digest, "SUPERSEDING_ADR_REQUIRED"),)),
    )
    return Setup("adr-nine", "STALE_REQUIRED", False, reason_fragment="superseding-adr-required")


def _setup_first_seen_never_fresh(repo: Path) -> Setup:
    """THE self-green closure at the classifier level.

    A brand-new binding whose only ledger row is a ``reviewed-no-change`` carrying that binding's
    exact LIVE digests. The row is consistent by construction and history holds nothing to
    contradict it, so a classifier keying FRESH on digest equality alone reports FRESH and re-opens
    the hole ``ledger.py`` closed.
    """
    _write(repo, _TARGET, "v1\n")
    _write(repo, LED_REL, _ledger_toml())  # a committed ledger that LACKS this row
    _commit(repo, "seed target and an empty ledger")
    source_digest, target_digest = _digests(repo, _ONE, _TARGET)
    _write(repo, REG_REL, _binding_toml(id="how-to-one", sources=_ONE, target=_TARGET))
    _write(
        repo,
        LED_REL,
        _ledger_toml((("how-to-one", source_digest, target_digest, "reviewed-no-change"),)),
    )
    return Setup("how-to-one", "STALE_REQUIRED", False, reason_fragment="first_seen-unratified")


def _setup_second_commit_is_fresh(repo: Path) -> Setup:
    """Non-degradation control for the row above: once a human commit has LANDED the ledger row,
    the same binding is green. The rule must not become 'a new binding can never be green'."""
    _write(repo, _TARGET, "v1\n")
    _commit(repo, "seed target")
    source_digest, target_digest = _digests(repo, _ONE, _TARGET)
    _write(repo, REG_REL, _binding_toml(id="how-to-one", sources=_ONE, target=_TARGET))
    _write(
        repo,
        LED_REL,
        _ledger_toml((("how-to-one", source_digest, target_digest, "reviewed-no-change"),)),
    )
    _commit(repo, "land the reviewed row")
    return Setup("how-to-one", "FRESH", True)


STATE_ORDER_CASES: tuple[tuple[str, Callable[[Path], Setup]], ...] = (
    ("broken_beats_stale", _setup_broken_beats_stale),
    ("broken_zero_expansion", _setup_broken_zero_expansion),
    ("broken_no_ledger_row_required", _setup_broken_no_ledger_row_required),
    ("advisory_no_ledger_row", _setup_advisory_no_ledger_row),
    ("fresh", _setup_fresh),
    ("stale_required", _setup_stale_required),
    ("stale_advisory", _setup_stale_advisory),
    ("superseding_adr_never_fresh", _setup_superseding_adr_never_fresh),
    ("first_seen_never_fresh", _setup_first_seen_never_fresh),
    ("second_commit_is_fresh", _setup_second_commit_is_fresh),
)


@pytest.mark.parametrize(
    ("name", "builder"), STATE_ORDER_CASES, ids=[c[0] for c in STATE_ORDER_CASES]
)
def test_state_order(docs_repo: Path, name: str, builder: Callable[[Path], Setup]) -> None:
    setup = builder(docs_repo)
    result = _classify(docs_repo, setup)

    assert _state_of(result, setup.binding_id) == setup.expected_state, (
        f"{name}: expected {setup.expected_state}"
    )
    assert result["ok"] is setup.expected_ok, f"{name}: expected ok={setup.expected_ok}"
    if setup.reason_fragment:
        rendered = json.dumps(result)
        assert setup.reason_fragment in rendered, (
            f"{name}: expected the reason to name {setup.reason_fragment!r}"
        )


@pytest.mark.parametrize(
    "name",
    ["superseding_adr_never_fresh", "first_seen_never_fresh"],
)
def test_digest_equality_is_not_sufficient_for_fresh(docs_repo: Path, name: str) -> None:
    """The load-bearing rule, asserted directly rather than only via the state table: both rows
    below have MATCHING digests and still must not be green."""
    builder = dict(STATE_ORDER_CASES)[name]
    setup = builder(docs_repo)
    result = _classify(docs_repo, setup)
    entry = next(e for e in result["bindings"] if e["id"] == setup.binding_id)
    assert entry["source_digest"] == entry["live_source_digest"]
    assert entry["target_digest"] == entry["live_target_digest"]
    assert entry["state"] != "FRESH"


# ── RATCHET_CASES ───────────────────────────────────────────────────────────────────────────────


def _seed_corpus(repo: Path, *, binding_targets: tuple[str, ...] = (_TARGET,)) -> None:
    """Seed and COMMIT the six-file corpus plus a registry covering ``binding_targets``.

    The covering bindings are ``advisory`` deliberately: a ``required`` binding with no
    ``[[reviewed]]`` row is BROKEN (STATE_ORDER_CASES owns that rule), which would flip ``ok`` in
    every ratchet row and make the ratchet assertions untestable. Advisory keeps ``ok`` a pure
    function of the ratchet under test.
    """
    _seed(repo, _CORPUS_SEED)
    _write(repo, "AGENTS.md", "agents\n")
    _write(repo, "CLAUDE.md", "claude\n")
    rows = "".join(
        _binding_toml(id=f"cover-{index}", sources=_ONE, target=target, severity="advisory")
        for index, target in enumerate(binding_targets)
    )
    _write(repo, REG_REL, rows)
    _commit(repo, "seed corpus")


# Eight tracked corpus files: the six in _CORPUS_SEED plus root AGENTS.md and CLAUDE.md.
_CORPUS_SIZE = len(_CORPUS_SEED) + 2


def _ratchet_result(repo: Path, uncovered_max: int | None) -> dict:
    coverage = {} if uncovered_max is None else {"uncovered_max": uncovered_max}
    _write(repo, LED_REL, _ledger_toml(coverage=coverage or None))
    return guard.classify(
        registry_path=repo / REG_REL,
        ledger_path=repo / LED_REL,
        root=repo,
        drift_gate=_clean_gate,
    )


RATCHET_CASES: tuple[tuple[str, int, bool, bool], ...] = (
    # (name, uncovered_max, expect_ok, expect_tighten_suggestion)
    ("uncovered_regression", _CORPUS_SIZE - 2, False, False),
    ("uncovered_equal", _CORPUS_SIZE - 1, True, False),
    ("uncovered_tightened", _CORPUS_SIZE, True, True),
)


@pytest.mark.parametrize(
    ("name", "uncovered_max", "expect_ok", "expect_tighten"),
    RATCHET_CASES,
    ids=[case[0] for case in RATCHET_CASES],
)
def test_uncovered_ratchet(
    docs_repo: Path, name: str, uncovered_max: int, expect_ok: bool, expect_tighten: bool
) -> None:
    _seed_corpus(docs_repo)
    result = _ratchet_result(docs_repo, uncovered_max)

    live = result["uncovered"]["live"]
    assert live == _CORPUS_SIZE - 1, f"{name}: one corpus file is covered by the single binding"
    assert result["uncovered"]["max"] == uncovered_max
    assert result["ok"] is expect_ok, f"{name}: expected ok={expect_ok}"

    suggestion = f"ratchet can tighten: set uncovered_max = {live}"
    messages = [finding["message"] for finding in result["findings"]]
    assert (suggestion in messages) is expect_tighten, f"{name}: tighten suggestion mismatch"


def test_uncovered_max_comes_from_the_committed_ledger(docs_repo: Path) -> None:
    """WR-01 adversarial row: the SAME uncommitted edit must not be able to raise its own ceiling.

    ``binding_min`` is read from the previous COMMITTED ledger precisely so "the same edit that
    deletes a binding cannot also lower the bar" (``ledger.py:435-439``). ``uncovered_max`` was read
    from the freshly-parsed WORKING-TREE ledger, so the mirror-image move was unguarded: drop a
    document out of coverage and raise the ceiling in one uncommitted change. The two ratchets are
    now symmetric.
    """
    _seed_corpus(docs_repo)
    strict = _ledger_toml(coverage={"uncovered_max": 0})
    _write(docs_repo, LED_REL, strict)
    _commit(docs_repo, "commit the strict ratchet")

    # Baseline: the committed ceiling of 0 is genuinely violated by the live uncovered count.
    baseline = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=_clean_gate,
    )
    assert baseline["uncovered"]["live"] > 0
    assert baseline["ok"] is False

    # THE BYPASS: raise the ceiling in the working tree only, changing nothing about coverage.
    _write(docs_repo, LED_REL, _ledger_toml(coverage={"uncovered_max": 99}))
    raised = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=_clean_gate,
    )

    assert raised["uncovered"]["max"] == 0, "the enforced ceiling must be the COMMITTED one"
    assert raised["ok"] is False, "a working-tree edit raised its own ratchet — self-blessing"


def test_uncovered_max_falls_back_to_the_working_tree_without_history(docs_repo: Path) -> None:
    """Non-degradation control: with no committed ledger there IS no committed ceiling, so the
    working-tree value is the only one available — and honouring it can only ADD a constraint,
    never relax one. Without this row the fix could degrade into "no ratchet unless committed",
    which would silently disable the gate in a fresh checkout."""
    _seed_corpus(docs_repo)
    result = _ratchet_result(docs_repo, 0)

    assert result["uncovered"]["max"] == 0
    assert result["ok"] is False


def test_uncovered_no_ledger_means_no_ratchet(docs_repo: Path) -> None:
    """``max is None`` (no ledger seeded yet) is not a failure — plan 28-07 seeds the threshold."""
    _seed_corpus(docs_repo)
    result = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=_clean_gate,
    )
    assert result["uncovered"]["max"] is None
    assert result["ok"] is True


def test_uncovered_untracked_file(docs_repo: Path) -> None:
    """P6 / Phase 26 CR-01 — a filesystem-walk implementation counts this file and CI's clean
    checkout then disagrees with a developer's working tree."""
    _seed_corpus(docs_repo)
    before = _ratchet_result(docs_repo, _CORPUS_SIZE - 1)["uncovered"]

    _write(docs_repo, "docs/how-to/untracked.md", "not committed\n")
    after = _ratchet_result(docs_repo, _CORPUS_SIZE - 1)["uncovered"]

    assert after["live"] == before["live"], "an untracked file moved the uncovered count"
    assert "docs/how-to/untracked.md" not in after["paths"]


# The instance-tree fixture path, ASSEMBLED from segments rather than written as one literal: a
# core-plane file may not carry an instance path token (GEN-04,
# tools/harness_lint/tests/test_core_no_example_dep.py), and this fixture must PROVE the instance
# tree is excluded from HUMAN_CORPUS without itself becoming the leak that guard exists to catch.
_INSTANCE_TREE_DOC = "/".join(("examples", "log-parser", "docs", "how-to", "instance.md"))


def test_corpus_excludes_and_includes(docs_repo: Path) -> None:
    """D-07/A4 — this pins the RATCHET'S MEANING, so it is asserted, not inferred from a loop."""
    _seed_corpus(docs_repo)
    _seed(
        docs_repo,
        {
            "docs/reference/generated.md": "derived\n",
            ".memory/derived/repo-map.md": "derived\n",
            ".planning/STATE.md": "gsd owned\n",
            _INSTANCE_TREE_DOC: "instance\n",
        },
    )
    _commit(docs_repo, "seed excluded trees")
    paths = set(_ratchet_result(docs_repo, None)["uncovered"]["paths"])

    for excluded in (
        "docs/reference/generated.md",
        ".memory/derived/repo-map.md",
        ".planning/STATE.md",
        _INSTANCE_TREE_DOC,
    ):
        assert excluded not in paths, f"{excluded} must not enter the uncovered corpus"
    for glob in DERIVED_GLOBS:
        prefix = glob.split("*", 1)[0]
        assert not any(path.startswith(prefix) and "*" in glob for path in paths), (
            f"a DERIVED_GLOBS path ({glob}) entered the corpus"
        )
    for included in (
        "docs/how-to/two.md",
        "docs/tutorials/first.md",
        "docs/explanation/why.md",
        "docs/glossary.md",
        "AGENTS.md",
        "CLAUDE.md",
        ".memory/README.md",
    ):
        assert included in paths, f"{included} must be part of the uncovered corpus"


def test_ratchet_not_written(docs_repo: Path) -> None:
    """D-06 / T-28-24 — a guard-authored bump must be structurally IMPOSSIBLE, not merely
    unobserved. Byte-identity plus a static no-write scan with a live planted-token control."""
    _seed_corpus(docs_repo)
    _write(docs_repo, LED_REL, _ledger_toml(coverage={"uncovered_max": _CORPUS_SIZE}))
    ledger = docs_repo / LED_REL
    before = hashlib.sha256(ledger.read_bytes()).hexdigest()

    result = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=ledger,
        root=docs_repo,
        drift_gate=_clean_gate,
    )
    assert result["ok"] is True  # the tightening suggestion is a NOTE, never an applied edit

    after = hashlib.sha256(ledger.read_bytes()).hexdigest()
    assert after == before, "classify() mutated the ledger"

    source = Path(guard.__file__).read_text(encoding="utf-8")
    write_tokens = ("write_text", "write_bytes", 'open("w"', "'w')", "shutil.copy")
    for token in write_tokens:
        assert token not in source, f"guard.py contains the write token {token!r}"
    # Live negative control: the same scan MUST fire on a source that does contain a write call,
    # otherwise a typo in `write_tokens` would make the assertion above vacuously green.
    planted = "def bump(path):\n    path.write_text('uncovered_max = 0')\n"
    assert any(token in planted for token in write_tokens), "the no-write scan is not live"


def test_binding_count_ratchet_regression(docs_repo: Path) -> None:
    """``binding_min`` fails naming BOTH numbers, and the threshold comes from the COMMITTED
    ledger — reading it from the working tree would let the same edit that deletes a binding also
    lower the bar (28-04)."""
    _seed_corpus(docs_repo, binding_targets=(_TARGET, "docs/how-to/two.md"))
    _write(docs_repo, LED_REL, _ledger_toml(coverage={"binding_min": 2}))
    _commit(docs_repo, "land the binding_min ratchet")

    _write(docs_repo, REG_REL, _binding_toml(id="cover-0", sources=_ONE, target=_TARGET))
    result = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=_clean_gate,
    )
    assert result["ok"] is False
    message = " ".join(finding["message"] for finding in result["findings"])
    assert "binding-count-regression" in message
    assert "1 binding" in message and "binding_min = 2" in message


def test_binding_count_ratchet_equal_and_grew(docs_repo: Path) -> None:
    _seed_corpus(docs_repo, binding_targets=(_TARGET, "docs/how-to/two.md"))
    _write(docs_repo, LED_REL, _ledger_toml(coverage={"binding_min": 2}))
    _commit(docs_repo, "land the binding_min ratchet")

    equal = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=_clean_gate,
    )
    messages = [finding["message"] for finding in equal["findings"]]
    assert not any(
        message.startswith("ratchet can tighten: set binding_min") for message in messages
    )

    _write(
        docs_repo,
        REG_REL,
        _binding_toml(id="cover-0", sources=_ONE, target=_TARGET)
        + _binding_toml(id="cover-1", sources=_ONE, target="docs/how-to/two.md")
        + _binding_toml(id="cover-2", sources=_ONE, target="docs/tutorials/first.md"),
    )
    grew = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=_clean_gate,
    )
    grew_messages = [finding["message"] for finding in grew["findings"]]
    assert "ratchet can tighten: set binding_min = 3" in grew_messages


def test_binding_deleted_outside_corpus(docs_repo: Path) -> None:
    """WHY the count ratchet is not redundant: deleting a binding whose TARGET lies outside
    HUMAN_CORPUS does not move the uncovered count by a single unit, so only ``binding_min``
    catches it. Without this row the two ratchets look interchangeable."""
    outside = "libs/normalize-spec.md"
    _write(docs_repo, outside, "spec\n")
    _seed_corpus(docs_repo, binding_targets=(_TARGET, outside))
    _write(docs_repo, LED_REL, _ledger_toml(coverage={"binding_min": 2, "uncovered_max": 99}))
    _commit(docs_repo, "land both ratchets")

    before = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=_clean_gate,
    )
    _write(docs_repo, REG_REL, _binding_toml(id="cover-0", sources=_ONE, target=_TARGET))
    after = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=_clean_gate,
    )

    assert after["uncovered"]["live"] == before["uncovered"]["live"], (
        "the uncovered ratchet is supposed to stay green through this deletion"
    )
    assert before["ok"] is True
    assert after["ok"] is False, "only binding_min catches an outside-corpus binding deletion"
    assert any(finding["reason"] == "binding-count-regression" for finding in after["findings"])


# ── SUPPRESSION_CASES (D-13) ────────────────────────────────────────────────────────────────────

_CONTRACT_SOURCE = "contracts/sample/greeting.schema.json"


def _drifted_gate() -> dict:
    return {"ok": False, "drifted": [(_CONTRACT_SOURCE, "changed", "breaking")]}


def _setup_drifted_binding(docs_repo: Path) -> None:
    _write(docs_repo, _CONTRACT_SOURCE, '{"title": "greeting"}\n')
    _write(docs_repo, _TARGET, "v1\n")
    _commit(docs_repo, "seed contract source and target")
    source_digest, target_digest = _digests(docs_repo, (_CONTRACT_SOURCE,), _TARGET)
    _write(
        docs_repo,
        REG_REL,
        _binding_toml(id="greeting-doc", sources=(_CONTRACT_SOURCE,), target=_TARGET),
    )
    _write(
        docs_repo,
        LED_REL,
        _ledger_toml((("greeting-doc", source_digest, target_digest, "reviewed-no-change"),)),
    )
    # The contract moves AFTER the review, so without suppression this is a plain STALE_REQUIRED.
    _write(docs_repo, _CONTRACT_SOURCE, '{"title": "greeting", "type": "object"}\n')


def test_drifted_source_suppressed(docs_repo: Path) -> None:
    _setup_drifted_binding(docs_repo)
    result = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=_drifted_gate,
    )
    assert _state_of(result, "greeting-doc") == "SUPPRESSED"
    assert result["ok"] is True, "a suppressed binding must not contribute to exit 1"


def test_undrifted_source_not_suppressed(docs_repo: Path) -> None:
    """Negative control — suppression is CONDITIONAL, never blanket."""
    _setup_drifted_binding(docs_repo)
    result = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=_clean_gate,
    )
    assert _state_of(result, "greeting-doc") == "STALE_REQUIRED"
    assert result["ok"] is False


def _setup_self_blessed_drifted_binding(docs_repo: Path) -> None:
    """CR-01's exact bypass: a BRAND-NEW binding self-blessed in the same uncommitted change,
    whose single source is a currently-drifted contract.

    The previous committed ledger EXISTS but is empty, so ``previous`` parses (history is readable)
    and ``previous_rows`` lacks the id — which is precisely the ``first_seen-unratified``
    precondition. The row carries the binding's exact LIVE digests, so it is digest-consistent by
    construction and only the history test can contradict it.
    """
    _write(docs_repo, _CONTRACT_SOURCE, '{"title": "greeting"}\n')
    _write(docs_repo, _TARGET, "v1\n")
    _write(docs_repo, LED_REL, "[coverage]\n")
    _commit(docs_repo, "seed contract source, target, and an empty committed ledger")

    source_digest, target_digest = _digests(docs_repo, (_CONTRACT_SOURCE,), _TARGET)
    _write(
        docs_repo,
        REG_REL,
        _binding_toml(id="newbinding", sources=(_CONTRACT_SOURCE,), target=_TARGET),
    )
    _write(
        docs_repo,
        LED_REL,
        _ledger_toml((("newbinding", source_digest, target_digest, "reviewed-no-change"),)),
    )


def _findings_for(result: dict, binding_id: str, reason: str) -> list[dict]:
    return [
        finding
        for finding in result["findings"]
        if finding["binding_id"] == binding_id and finding["reason"] == reason
    ]


def test_self_blessed_binding_is_not_rescued_by_a_drifted_source(docs_repo: Path) -> None:
    """CR-01 adversarial row: drift suppression must never demote a RATIFICATION-AUTHORITY finding.

    Drift suppression exists so one change does not fail two gates with two different remedies
    (D-13). The only finding that is genuinely DOWNSTREAM of contract drift is ``stale-digest``:
    the source moved, so of course the reviewed digest no longer matches. ``first_seen-unratified``
    is a different KIND of claim — it says nobody has ever ratified this binding — and a drifted
    source has nothing to do with who ratified what.

    Demoting it made the self-green attack succeed and the escape PERMANENT: the commit CI would
    have failed is the commit that lands the self-authored row, and once landed the row is history,
    so the next run reports FRESH unconditionally.

    Both halves are asserted: the finding stays fail-level, AND the binding never reaches the
    ``SUPPRESSED`` state at all, so no future reordering of the classifier can re-open the hole.
    """
    _setup_self_blessed_drifted_binding(docs_repo)

    no_drift = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=_clean_gate,
    )
    assert no_drift["ok"] is False, "fixture sanity: unratified is blocking when nothing drifted"
    assert [f["level"] for f in _findings_for(no_drift, "newbinding", "first_seen-unratified")] == [
        "fail"
    ]

    drifted = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=_drifted_gate,
    )

    assert [f["level"] for f in _findings_for(drifted, "newbinding", "first_seen-unratified")] == [
        "fail"
    ], "drift demoted a ratification-authority finding — the self-green escape is open"
    assert _state_of(drifted, "newbinding") != "SUPPRESSED", (
        "a binding carrying a blocking coherence finding must never reach SUPPRESSED"
    )
    assert drifted["ok"] is False, "a self-blessed brand-new binding reported ok under drift"


def test_drift_findings_not_restated(docs_repo: Path) -> None:
    """The guard reads ``run_gate`` for the DECISION and never carries its findings forward —
    contract-drift stays leading and authoritative, and this gate must not double-report it."""
    _setup_drifted_binding(docs_repo)
    result = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=_drifted_gate,
    )
    rendered = json.dumps(result)
    for _rel, kind, classification in _drifted_gate()["drifted"]:
        assert classification not in rendered, "a run_gate classification leaked into this gate"
        assert f'"{kind}"' not in rendered, "a run_gate drift kind leaked into this gate"
    assert "drifted" not in result


def test_drift_gate_called_once_per_classify(docs_repo: Path) -> None:
    """``run_gate`` is a full manifest rebuild — calling it per binding would make the gate's cost
    scale with the registry."""
    calls: list[int] = []

    def counting_gate() -> dict:
        calls.append(1)
        return _clean_gate()

    _seed_corpus(docs_repo, binding_targets=(_TARGET, "docs/how-to/two.md"))
    guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=counting_gate,
    )
    assert len(calls) == 1


# ── structural invariants ───────────────────────────────────────────────────────────────────────


def test_states_are_the_pinned_five(docs_repo: Path) -> None:
    """Phase 29's ``/docs-update`` binds to this vocabulary, so the set is pinned here."""
    assert guard.STATES == (
        "BROKEN",
        "SUPPRESSED",
        "FRESH",
        "STALE_REQUIRED",
        "STALE_ADVISORY",
        "UNCOVERED",
    )


def test_result_is_byte_identical_across_runs(docs_repo: Path) -> None:
    """No ``set`` iteration, no dict-order leakage, no clock (T-28-25)."""
    _seed_corpus(docs_repo, binding_targets=(_TARGET, "docs/how-to/two.md"))
    first = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=_clean_gate,
    )
    second = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=_clean_gate,
    )
    assert json.dumps(first) == json.dumps(second)


def test_missing_registry_is_zero_bindings_not_an_error(docs_repo: Path) -> None:
    """A MISSING registry is exit 0 with zero bindings (plan 28-07 seeds it), never invalid."""
    result = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=_clean_gate,
    )
    assert result["bindings"] == []
    assert result["ok"] is True
