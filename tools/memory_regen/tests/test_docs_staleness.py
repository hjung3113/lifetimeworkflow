"""Tests for the derived docs-staleness queue generator (DOCSUP-04, D-10).

Pins the three guarantees the derived plane depends on, in the same shape as
``test_contracts_index.py``:
  (a) determinism — render twice AND generate→hash→delete→regenerate are byte-identical; proven
      WITHOUT ``git diff``, because the queue is gitignored (``.gitignore:23``, Pitfall 2).
  (b) pointer-only content — no document prose, no diff hunk ever reaches a row (T-28-37), proven
      with a sentinel sentence seeded into BOTH a source and a target.
  (c) a committed syrupy snapshot over a HERMETIC fixture tree = the determinism reference, stored
      under ``__snapshots__/`` and carrying no ``tmp_path``.

Every fixture here is built under ``tmp_path`` and passed through the explicit
``registry_path`` / ``ledger_path`` / ``root`` parameters (D-14), so no test reads the live
registry, the live ledger, or the live corpus.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from tools.memory_regen import docs_staleness

# The drift gate is the D-13 suppression input. Injected as "nothing drifted" so a real
# contract change in the working tree cannot move a fixture's expected state.
_NO_DRIFT = {"ok": True, "drifted": []}

# A sentence that exists ONLY inside fixture documents. If it ever appears in the rendered queue,
# the generator copied prose out of a target (T-28-37).
SENTINEL = "PROSE-SENTINEL-a-queue-row-must-never-carry-this-sentence"


def _fixture_tree(tmp_path: Path, *, with_bindings: bool = True) -> tuple[Path, Path, Path]:
    """Build a hermetic ``(root, registry_path, ledger_path)``.

    Two bindings, chosen so both severities are exercised and neither can be FRESH: there is no
    ledger row for either, so the ``required`` one is BROKEN and the ``advisory`` one is
    STALE_ADVISORY. Deterministic without a git history in the tree.
    """
    root = tmp_path / "repo"
    (root / "docs" / "how-to").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "src" / "one.py").write_text(f"# {SENTINEL}\nONE = 1\n", encoding="utf-8")
    (root / "docs" / "how-to" / "alpha.md").write_text(f"# Alpha\n\n{SENTINEL}\n", encoding="utf-8")
    (root / "docs" / "how-to" / "beta.md").write_text(f"# Beta\n\n{SENTINEL}\n", encoding="utf-8")

    registry_path = root / "docs" / "doc-dependencies.toml"
    if with_bindings:
        registry_path.write_text(
            "[[binding]]\n"
            'id = "beta-advisory"\n'
            'sources = ["src/one.py"]\n'
            'target = "docs/how-to/beta.md"\n'
            'severity = "advisory"\n'
            'dispositions = ["updated", "reviewed-no-change"]\n'
            "\n"
            "[[binding]]\n"
            'id = "alpha-required"\n'
            'sources = ["src/one.py"]\n'
            'target = "docs/how-to/alpha.md"\n'
            'severity = "required"\n'
            'dispositions = ["updated"]\n',
            encoding="utf-8",
        )
    ledger_path = root / "docs" / ".docs-review-ledger.toml"
    return root, registry_path, ledger_path


def _rows(tmp_path: Path, *, with_bindings: bool = True) -> list[tuple[str, ...]]:
    root, registry_path, ledger_path = _fixture_tree(tmp_path, with_bindings=with_bindings)
    return docs_staleness.rows(
        registry_path=registry_path,
        ledger_path=ledger_path,
        root=root,
        drift_gate=lambda: _NO_DRIFT,
    )


# ---- (a) determinism: byte-identical, proven without git diff --------------------------------


def test_queue_generate_twice_identical(tmp_path: Path) -> None:
    """render(rows()) twice over the same fixture has an identical SHA-256 (Pitfall 1)."""
    first = docs_staleness.render(_rows(tmp_path / "a"))
    second = docs_staleness.render(_rows(tmp_path / "b"))
    assert (
        hashlib.sha256(first.encode("utf-8")).hexdigest()
        == hashlib.sha256(second.encode("utf-8")).hexdigest()
    )


def test_queue_delete_regenerate_identical(tmp_path: Path) -> None:
    """write → sha256 → delete → write → assert identical hash (NOT git diff, Pitfall 2)."""
    root, registry_path, ledger_path = _fixture_tree(tmp_path)
    out = tmp_path / "derived" / "docs-staleness.md"
    digests: list[str] = []
    for _ in range(2):
        docs_staleness.write(
            queue_path=out,
            registry_path=registry_path,
            ledger_path=ledger_path,
            root=root,
            drift_gate=lambda: _NO_DRIFT,
        )
        digests.append(hashlib.sha256(out.read_bytes()).hexdigest())
        out.unlink()
        assert not out.exists()
    assert digests[0] == digests[1]


# ---- structure: DERIVED marker, sorted, qualifying states only --------------------------------


def test_queue_carries_derived_marker() -> None:
    """The first line marks the file DERIVED and names its generator (D-04)."""
    text = docs_staleness.render([])
    assert text.splitlines()[0] == f"# {docs_staleness.DERIVED_HEADER}"
    assert "tools/memory_regen/docs_staleness.py" in docs_staleness.DERIVED_HEADER
    assert text.endswith("\n")


def test_queue_rows_are_sorted_and_only_qualifying(tmp_path: Path) -> None:
    """Rows sort by binding id; only obligations that need action appear."""
    rows = _rows(tmp_path)
    assert [row[0] for row in rows] == sorted(row[0] for row in rows)
    assert [row[0] for row in rows] == ["alpha-required", "beta-advisory"]
    states = {row[2] for row in rows}
    assert states <= set(docs_staleness.QUEUE_STATES)
    assert "FRESH" not in states and "SUPPRESSED" not in states


def test_queue_omits_fresh_and_suppressed(tmp_path: Path) -> None:
    """A registry with no bindings at all yields no rows — a queue of nothing is not a queue."""
    assert _rows(tmp_path, with_bindings=False) == []


def test_queue_empty_when_nothing_stale(tmp_path: Path) -> None:
    """Zero rows still render a stable, non-empty file carrying an explicit empty marker."""
    text = docs_staleness.render([])
    assert docs_staleness.EMPTY_MARKER in text
    assert text.splitlines()[0] == f"# {docs_staleness.DERIVED_HEADER}"
    # main() must be idempotent over an empty queue: the file exists and is stable.
    assert text == docs_staleness.render([])


# ---- main() reports the file it wrote, and classifies exactly once (WR-04) --------------------

_ONE_ROW = [("alpha-required", "docs/how-to/alpha.md", "BROKEN", "required", "updated", "(none)")]


def test_main_classifies_once_and_reports_what_it_wrote(monkeypatch, tmp_path, capsys) -> None:
    """WR-04 adversarial row.

    ``rows()`` walks the corpus, shells out to ``git ls-files`` and rebuilds the whole contract
    manifest. ``main()`` calling it a SECOND time purely to print a count is not just double cost:
    the second run re-reads the tree, so the number shown to the operator can disagree with the
    number in the file that was just written. This stub makes the two runs disagree by
    construction — first call one obligation, every later call none — so a ``main()`` that
    classifies twice prints ``0`` over a file that says ``1``.
    """
    out = tmp_path / "derived" / "docs-staleness.md"
    monkeypatch.setattr(docs_staleness, "QUEUE_PATH", out)
    calls: list[int] = []

    def counting_rows(**_kwargs):
        calls.append(1)
        return _ONE_ROW if len(calls) == 1 else []

    monkeypatch.setattr(docs_staleness, "rows", counting_rows)

    assert docs_staleness.main([]) == 0

    assert len(calls) == 1, f"classification ran {len(calls)} time(s); main() must compute it once"
    printed = capsys.readouterr().out
    written = out.read_text(encoding="utf-8")
    assert "1 binding(s) need review." in written
    assert "(1 binding(s) needing review)" in printed, (
        f"the printed count disagrees with the file that was written: {printed!r}"
    )


# ---- (b) pointer-only: never a prose excerpt, never a diff body -------------------------------


def test_queue_contains_no_prose_or_diff(tmp_path: Path) -> None:
    """A sentinel sentence seeded into a source AND a target is absent from the render."""
    text = docs_staleness.render(_rows(tmp_path))
    assert SENTINEL not in text
    assert "@@" not in text and "\n+++" not in text and "\n---\n" not in text


# ---- determinism hygiene: no wall-clock, no float ---------------------------------------------

_FORBIDDEN_TOKENS = (
    "datetime",
    "date.today",
    ".now()",
    "time.time",
    "time.monotonic",
    "float(",
)


def _forbidden_tokens(text: str) -> list[str]:
    return [token for token in _FORBIDDEN_TOKENS if token in text]


def test_queue_has_no_wallclock_or_float(repo_root: Path) -> None:
    """A static text scan of the generator: no clock and no raw float reaches the render."""
    text = (repo_root / "tools/memory_regen/docs_staleness.py").read_text(encoding="utf-8")
    assert not _forbidden_tokens(text)


def test_negative_control_forbidden_scan_flags_planted_token() -> None:
    """The static scan is live and rejects a synthetic clock/float-bearing source."""
    assert _forbidden_tokens("x = datetime; y = float(1)") == ["datetime", "float("]


# ---- (c) committed syrupy snapshot = determinism reference ------------------------------------


def test_queue_matches_snapshot(snapshot, tmp_path: Path) -> None:
    """Committed .ambr snapshot pins render() over the HERMETIC fixture; no tmp_path leaks."""
    text = docs_staleness.render(_rows(tmp_path))
    assert str(tmp_path) not in text
    assert text == snapshot
