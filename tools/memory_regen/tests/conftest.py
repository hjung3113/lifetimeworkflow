"""Shared fixtures for the memory_regen tests (MEM-02/03, HOOK-05).

Import-path wiring mirrors tools/golden_runner/tests/conftest.py exactly: memory_regen is a
*virtual* uv-workspace member (not pip-installed), invoked by module path from the repo root, so
the tests must put the repo root (and libs/python) onto sys.path themselves. `tools` is a namespace
package (no tools/__init__.py) — inserting the repo root lets `import tools.memory_regen...` and
`from tools.contract_hash... import ...` (Wave-2 reuse) resolve.

Fixtures:
- ``repo_root``        — the repository root (Path).
- ``tmp_source_tree``  — a throwaway tree with tiny .py/.cs/.sh files, each carrying one
                         definition + one reference, for the Wave-2 tree-sitter parse / repo-map
                         determinism tests.
- ``tmp_contracts_tree`` — a throwaway tree with a couple of real ``contracts/**/*.schema.json``
                         copied in, for the Wave-2 contracts-index tests. Skips if none on disk.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

# --- import path wiring (virtual uv workspace member, not pip-installed) ----------------------
# tests -> memory_regen -> tools -> repo root  (parents[3]; mirrors golden_runner/conftest.py)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_LIBS_PYTHON = _REPO_ROOT / "libs" / "python"
for _p in (str(_REPO_ROOT), str(_LIBS_PYTHON)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return _REPO_ROOT


@pytest.fixture()
def tmp_source_tree(tmp_path: Path) -> Path:
    """A tiny polyglot source tree — one def + one ref per language — for parse/repo-map tests."""
    src = tmp_path / "src"
    src.mkdir()
    # Python: define `helper`, reference it from `main`.
    (src / "mod.py").write_text(
        "def helper():\n    return 1\n\n\ndef main():\n    return helper()\n",
        encoding="utf-8",
    )
    # C#: define `Helper`, reference it from `Main`.
    (src / "Mod.cs").write_text(
        "class Mod {\n"
        "    static int Helper() { return 1; }\n"
        "    static int Main() { return Helper(); }\n"
        "}\n",
        encoding="utf-8",
    )
    # Bash: define `helper`, reference it from the body.
    (src / "mod.sh").write_text(
        "#!/usr/bin/env bash\nhelper() { echo 1; }\nhelper\n",
        encoding="utf-8",
    )
    return src


@pytest.fixture()
def tmp_contracts_tree(tmp_path: Path, repo_root: Path) -> Path:
    """A throwaway copy of a couple of real contract schemas, for contracts-index tests."""
    schemas = sorted((repo_root / "contracts").glob("**/*.schema.json"))
    if not schemas:
        pytest.skip("no contracts/**/*.schema.json on disk to sample")
    dest = tmp_path / "contracts"
    dest.mkdir()
    for schema in schemas[:2]:
        rel = schema.relative_to(repo_root / "contracts")
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(schema, target)
    return dest


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
