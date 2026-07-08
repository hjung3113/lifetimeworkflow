"""CMD-06 /strangler-step baseline-refusal gate (D-05, Pitfall P10, ASVS-style safety gate).

Proves the "machines gate, humans ratify" discipline for migration: a strangler extraction is
REFUSED unless a captured legacy golden ``.verified`` baseline exists for the target path. The
load-bearing assertions are the REFUSALS (both the raised :class:`StranglerRefused` and the
non-zero CLI exit) — the affirmative case exists purely to show the gate is not dead. The gate must
NEVER fabricate a baseline: the golden/human plane provides it, this module only checks and refuses.

All cases parameterize ``golden_dir`` onto a ``tmp_path`` so no real ``golden/`` case is touched.
"""

from __future__ import annotations

import pytest

from tools.strangler_guard.guard import (
    StranglerRefused,
    baseline_path,
    main,
    require_baseline,
)

_TARGET = "src/legacy/Parser.cs"


def _write_baseline(golden_dir, target):
    """Materialize a captured legacy .verified baseline for ``target`` under ``golden_dir``."""
    path = baseline_path(target, golden_dir)  # deterministic derived location
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"col\napproved-legacy-value\n")
    return path


# --- refusal (the core P10 guarantee) ---------------------------------------------------------


def test_require_baseline_refuses_without_baseline(tmp_path):
    """No captured baseline under golden_dir → StranglerRefused (nothing to gate the migration)."""
    with pytest.raises(StranglerRefused, match="REFUSED: no captured legacy golden baseline"):
        require_baseline(_TARGET, golden_dir=tmp_path)


def test_main_returns_nonzero_without_baseline(tmp_path, capsys):
    """CLI refusal maps to a non-zero exit (3) and prints REFUSED — mirrors approve.py exit 3."""
    rc = main([_TARGET, "--golden-dir", str(tmp_path)])
    assert rc != 0
    assert rc == 3
    assert "REFUSED" in capsys.readouterr().out


def test_require_baseline_does_not_fabricate(tmp_path):
    """The gate must not create a baseline as a side effect of being asked for one.

    (machines gate).
    """
    with pytest.raises(StranglerRefused):
        require_baseline(_TARGET, golden_dir=tmp_path)
    # Nothing was written under the (empty) golden dir.
    assert not any(tmp_path.rglob("*.verified*"))


# --- affirmative (mechanism proof — the gate is not dead) --------------------------------------


def test_require_baseline_returns_path_when_present(tmp_path):
    """With a captured .verified baseline for the target, require_baseline returns its Path."""
    expected = _write_baseline(tmp_path, _TARGET)
    got = require_baseline(_TARGET, golden_dir=tmp_path)
    assert got == expected
    assert got.exists()


def test_main_returns_zero_when_baseline_present(tmp_path, capsys):
    """With a baseline present the CLI accepts (exit 0)."""
    _write_baseline(tmp_path, _TARGET)
    rc = main([_TARGET, "--golden-dir", str(tmp_path)])
    assert rc == 0
    assert "OK" in capsys.readouterr().out
