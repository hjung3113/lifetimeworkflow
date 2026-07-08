"""Import-path wiring for the harness_lint tests (D-02/D-04/D-07).

Mirrors tools/harness_perms/tests/conftest.py: harness_lint is a *virtual* uv-workspace member
(not pip-installed), imported by module path from the repo root, so the tests must put the repo
root onto sys.path themselves. `tools` is a namespace package (no tools/__init__.py) — inserting
the repo root lets `from tools.harness_lint import ...` resolve.
"""

from __future__ import annotations

import sys
from pathlib import Path

# tests -> harness_lint -> tools -> repo root  (parents[3]; mirrors harness_perms/conftest.py)
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
