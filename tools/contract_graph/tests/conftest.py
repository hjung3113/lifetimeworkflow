"""Import-path wiring for the contract_graph tests (TOPO-04).

Mirrors tools/harness_config/tests/conftest.py: contract_graph is a *virtual* uv-workspace member
(not pip-installed), imported by module path from the repo root, so the tests must put the repo
root onto sys.path themselves. `tools` is a namespace package (no tools/__init__.py) — inserting
the repo root lets `from tools.contract_graph import ...` resolve.
"""

from __future__ import annotations

import sys
from pathlib import Path

# tests -> contract_graph -> tools -> repo root  (parents[3]; mirrors harness_config/conftest.py)
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
