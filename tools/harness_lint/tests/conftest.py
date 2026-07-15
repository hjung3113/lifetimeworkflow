"""Import-path wiring and shared agreement corpus for harness_lint tests.

Mirrors tools/harness_perms/tests/conftest.py: harness_lint is a *virtual* uv-workspace member
(not pip-installed), imported by module path from the repo root, so the tests must put the repo
root onto sys.path themselves. `tools` is a namespace package (no tools/__init__.py) — inserting
the repo root lets `from tools.harness_lint import ...` resolve.

The agreement corpus is built here once and shared by both consumers. Its deliberately
non-alphabetical creation order makes deterministic sorting assertions falsifiable.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# tests -> harness_lint -> tools -> repo root  (parents[3]; mirrors harness_perms/conftest.py)
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


_AGREEMENTS_CREATION_ORDER = (
    "zeta-proceed.md",
    "alpha-ground.md",
    "_TEMPLATE.md",
    "middle-retired.md",
    "README.md",
)


@pytest.fixture()
def tmp_agreements_tree(tmp_path: Path) -> Path:
    """Synthetic agreement entries, deliberately created in non-alphabetical order."""
    agreements = tmp_path / "agreements"
    agreements.mkdir()
    contents = {
        "zeta-proceed.md": """---
status: active
added: "2026-01-02"
provenance: "synthetic test fixture"
---

# Proceed deliberately

Use the agreed plan before expanding scope.

Related: [test](../README.md)
""",
        "alpha-ground.md": """---
status: active
added: "2026-01-02"
provenance: "synthetic test fixture"
---

# Ground claims

State evidence before making a recommendation.

Related: [test](../README.md)
""",
        "_TEMPLATE.md": """---
status: active
---

# Template

<One-line working-style or methodology rule.>
""",
        "middle-retired.md": """---
status: retired
added: "2026-01-02"
provenance: "synthetic test fixture"
---

# Retired rule

Do not render this rule.

Related: [test](../README.md)
""",
        "README.md": "Synthetic fixture documentation.\n",
    }
    for name in _AGREEMENTS_CREATION_ORDER:
        (agreements / name).write_text(contents[name], encoding="utf-8")
    return agreements
