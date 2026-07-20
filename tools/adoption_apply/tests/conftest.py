"""Import-path wiring for tools/adoption_apply tests.

adoption_apply is a virtual uv-workspace member (not pip-installed), imported by module path
from the repo root. The tests must put the repo root onto sys.path themselves so that
``from tools.adoption_apply import batch`` resolves. Mirrors
``tools/adoption_scan/tests/conftest.py``'s wiring section exactly — this file intentionally
does NOT carry a ``tmp_minirepo``-style fixture; that fixture is scoped to Phase 26's own
scan/plan/destinations tests, not apply.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# tests -> adoption_apply -> tools -> repo root (parents[3]; mirrors adoption_scan/tests/conftest)
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """The repository root."""
    return _REPO_ROOT
