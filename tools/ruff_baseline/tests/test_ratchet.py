"""DEBT-01 ratchet proof — the adversarial table for `tools.ruff_baseline.ratchet`.

Every row here is hermetic: `compare_counts` is a pure function over two dicts, so no row runs
ruff, touches the working tree, or depends on how many findings the repo happens to have today.
That matters twice over — the real tree is a moving target while sibling phases commit to this
branch, and a test that shelled out to ruff would make `core-suite` and the `lint` CI job report
the same regression with two different remedies.

The four non-table cases cover the seams a pure comparison cannot reach: diagnostic bucketing
(including ruff's `null` code for syntax errors), the subprocess contract (ruff's exit 2 is a
BROKEN INVOCATION and must never be read as "no findings"), and the update path's refusal to
raise its own baseline.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tools.ruff_baseline import ratchet

# ── the ratchet table ────────────────────────────────────────────────────────────────────────
# (case_id, baseline, current, expect_ok, expect_mentions)
RATCHET_CASES = [
    ("identical", {"E501": 10, "E702": 2}, {"E501": 10, "E702": 2}, True, ()),
    ("one-rule-shrank", {"E501": 10}, {"E501": 7}, True, ()),
    ("one-rule-grew", {"E501": 10}, {"E501": 11}, False, ("E501",)),
    # A code the baseline has never seen is baseline 0 — a ruff bump that adds a check under
    # E/F/I/UP/B, or a genuinely new violation class, must fail on first appearance rather than
    # being silently absorbed (D-05).
    ("unknown-code-appears", {"E501": 10}, {"E501": 10, "B008": 1}, False, ("B008",)),
    ("known-code-fixed-to-zero", {"E501": 10, "F401": 3}, {"E501": 10}, True, ()),
    # The RULE is the unit, not the total. Both of the next two rows keep (or lower) the overall
    # count while one class grows, and both must fail — a per-total ratchet would pass them.
    ("wash-one-up-one-down", {"E501": 10, "E702": 5}, {"E501": 11, "E702": 4}, False, ("E501",)),
    (
        "total-shrinks-one-class-grows",
        {"E501": 10, "E702": 5},
        {"E501": 11, "E702": 1},
        False,
        ("E501",),
    ),
    ("empty-both", {}, {}, True, ()),
    ("empty-baseline-any-finding", {}, {"E501": 1}, False, ("E501",)),
    ("everything-fixed", {"E501": 10, "E702": 5}, {}, True, ()),
    ("several-grew", {"E501": 1, "E702": 1}, {"E501": 2, "E702": 3}, False, ("E501", "E702")),
]


@pytest.mark.parametrize(
    ("baseline", "current", "expect_ok", "expect_mentions"),
    [pytest.param(*case[1:], id=case[0]) for case in RATCHET_CASES],
)
def test_compare_counts(
    baseline: dict[str, int],
    current: dict[str, int],
    expect_ok: bool,
    expect_mentions: tuple[str, ...],
) -> None:
    result = ratchet.compare_counts(baseline, current)
    assert result.ok is expect_ok
    for code in expect_mentions:
        assert code in result.regressions, f"{code} should be reported as a regression"
    if expect_ok:
        assert result.regressions == {}


def test_regression_report_names_both_numbers() -> None:
    """A failure an operator cannot act on is a failure they will disable."""
    result = ratchet.compare_counts({"E501": 10}, {"E501": 13})
    assert result.regressions["E501"] == (10, 13)
    rendered = ratchet.render(result)
    assert "E501" in rendered
    assert "10" in rendered and "13" in rendered


def test_shrink_is_reported_so_the_baseline_can_be_lowered() -> None:
    result = ratchet.compare_counts({"E501": 10, "E702": 5}, {"E501": 4})
    assert result.ok is True
    assert result.improvements == {"E501": (10, 4), "E702": (5, 0)}


# ── diagnostic bucketing ─────────────────────────────────────────────────────────────────────


def test_counts_from_diagnostics_buckets_by_code() -> None:
    diagnostics = [
        {"code": "E501", "filename": "a.py"},
        {"code": "E501", "filename": "b.py"},
        {"code": "F401", "filename": "a.py"},
    ]
    assert ratchet.counts_from_diagnostics(diagnostics) == {"E501": 2, "F401": 1}


def test_counts_from_diagnostics_keeps_null_code_diagnostics() -> None:
    """Ruff reports syntax errors with `code: null`. Dropping them would hide a broken file."""
    diagnostics = [{"code": None, "filename": "a.py"}, {"code": "E501", "filename": "a.py"}]
    counts = ratchet.counts_from_diagnostics(diagnostics)
    assert counts == {ratchet.SYNTAX_ERROR_CODE: 1, "E501": 1}
    assert ratchet.SYNTAX_ERROR_CODE not in ("E501", "F401")


def test_counts_from_diagnostics_is_empty_for_a_clean_tree() -> None:
    assert ratchet.counts_from_diagnostics([]) == {}


# ── the subprocess contract ──────────────────────────────────────────────────────────────────


class _FakeCompleted:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_run_ruff_accepts_exit_0_and_exit_1(monkeypatch: pytest.MonkeyPatch) -> None:
    """0 = clean, 1 = findings. Both are valid results, not errors."""
    payload = json.dumps([{"code": "E501", "filename": "a.py"}])
    for code in (0, 1):
        monkeypatch.setattr(subprocess, "run", lambda *a, _c=code, **k: _FakeCompleted(_c, payload))
        assert ratchet.run_ruff() == [{"code": "E501", "filename": "a.py"}]


def test_run_ruff_raises_on_exit_2(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ruff's exit 2 is a usage/internal error.

    Reading it as "zero findings" would turn the gate permanently green — the exact defect this
    phase exists to remove — so it must raise instead of returning an empty list.
    """
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: _FakeCompleted(2, "", "ruff: unknown option")
    )
    with pytest.raises(ratchet.RuffInvocationError) as excinfo:
        ratchet.run_ruff()
    assert "unknown option" in str(excinfo.value)


def test_run_ruff_raises_on_unparseable_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _FakeCompleted(1, "not json"))
    with pytest.raises(ratchet.RuffInvocationError):
        ratchet.run_ruff()


def test_run_ruff_command_is_the_current_interpreter_and_uncached() -> None:
    """`python -m ruff` cannot pick up an ambient ruff off PATH; --no-cache keeps a warm local
    run and a cold CI runner from producing different verdicts."""
    cmd = ratchet.ruff_command()
    assert cmd[0].endswith("python") or "python" in Path(cmd[0]).name
    assert cmd[1:3] == ["-m", "ruff"]
    assert "--no-cache" in cmd
    assert "--output-format=json" in cmd


# ── the update path ──────────────────────────────────────────────────────────────────────────


def test_write_baseline_refuses_an_increase_and_leaves_the_file_untouched(tmp_path: Path) -> None:
    """`--update` must not be a way to absorb a regression."""
    path = tmp_path / "baseline.json"
    ratchet.write_baseline(path, {"E501": 10}, ruff_version="0.15.20")
    before = path.read_bytes()

    with pytest.raises(ratchet.BaselineRaiseRefused):
        ratchet.write_baseline(path, {"E501": 11}, ruff_version="0.15.20")

    assert path.read_bytes() == before, "a refused update must not partially write"


def test_write_baseline_accepts_a_shrink(tmp_path: Path) -> None:
    path = tmp_path / "baseline.json"
    ratchet.write_baseline(path, {"E501": 10, "E702": 5}, ruff_version="0.15.20")
    ratchet.write_baseline(path, {"E501": 4}, ruff_version="0.15.20")
    assert ratchet.load_baseline(path) == {"E501": 4}


def test_write_baseline_refuses_a_brand_new_code(tmp_path: Path) -> None:
    path = tmp_path / "baseline.json"
    ratchet.write_baseline(path, {"E501": 10}, ruff_version="0.15.20")
    with pytest.raises(ratchet.BaselineRaiseRefused):
        ratchet.write_baseline(path, {"E501": 10, "B008": 1}, ruff_version="0.15.20")


def test_baseline_roundtrips_and_is_sorted_for_a_legible_diff(tmp_path: Path) -> None:
    path = tmp_path / "baseline.json"
    ratchet.write_baseline(path, {"F401": 2, "B007": 1, "E501": 3}, ruff_version="0.15.20")
    text = path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    document = json.loads(text)
    assert list(document["counts"]) == ["B007", "E501", "F401"]
    assert document["total"] == 6
    assert document["ruff_version"] == "0.15.20"


def test_load_baseline_rejects_a_malformed_document(tmp_path: Path) -> None:
    path = tmp_path / "baseline.json"
    path.write_text('{"counts": "not a mapping"}\n', encoding="utf-8")
    with pytest.raises(ratchet.BaselineError):
        ratchet.load_baseline(path)


def test_load_baseline_rejects_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ratchet.BaselineError):
        ratchet.load_baseline(tmp_path / "absent.json")


# ── the committed baseline ───────────────────────────────────────────────────────────────────


def test_the_committed_baseline_is_loadable_and_nonnegative() -> None:
    """Shape only — deliberately NOT an assertion about the live tree's finding count.

    Asserting the real count here would red `core-suite` for a lint regression that the `lint`
    job already owns, with a different remedy printed by each (D-11).
    """
    counts = ratchet.load_baseline(ratchet.BASELINE_PATH)
    assert counts, "the committed baseline should not be empty while debt remains"
    assert all(isinstance(v, int) and v >= 0 for v in counts.values())
    assert all(code == code.strip() and code for code in counts)
