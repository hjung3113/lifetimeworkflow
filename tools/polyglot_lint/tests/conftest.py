"""Import-path wiring for the polyglot_lint tests (POLY-01, D-03).

Mirrors tools/golden_runner/tests/conftest.py: polyglot_lint is a *virtual* uv-workspace
member (not pip-installed), imported by module path from the repo root, and it reuses the
§4-5 normalization core in ``libs/python`` (the SAME shim golden_runner uses). ``tools`` is a
namespace package (no ``tools/__init__.py``), so the tests must put BOTH the repo root (for
``from tools.polyglot_lint import ...``) and ``libs/python`` (for ``from normalize.core import
...`` in the corpus-parity check) onto ``sys.path`` themselves.
"""

from __future__ import annotations

import sys
from pathlib import Path

# tests -> polyglot_lint -> tools -> repo root  (parents[3]; mirrors golden_runner/conftest.py)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_LIBS_PYTHON = _REPO_ROOT / "libs" / "python"
for _p in (str(_REPO_ROOT), str(_LIBS_PYTHON)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
