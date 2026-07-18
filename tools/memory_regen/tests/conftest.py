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
- Agreement fixtures are re-exported from harness_lint so both consumers share one corpus.
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

from tools.harness_lint.tests.conftest import (  # noqa: E402, F401
    _AGREEMENTS_CREATION_ORDER,
    tmp_agreements_tree,
)


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
def tmp_pointer_scan_tree(tmp_path: Path) -> Path:
    """A throwaway repo-shaped tree for the pointer-index generator tests (Phase 16, D-16-02).

    Contains the two memory-item KINDS the scanner enumerates (state files + active/retired
    agreements) plus scan-root files (a ``docs/`` tree and a single-file ``AGENTS.md`` root) that
    each reference a memory item by BOTH a ``.memory/...`` path string (``kind="path"``) and a bare
    agreement slug (``kind="slug"``). One decoy line contains ``<slug>ner`` (``planner``) so the
    word-boundary guard is falsifiable: slug ``plan`` must NOT match ``planner``.

    Everything is written ONLY under ``tmp_path`` — no real ``.memory/`` plane is ever touched. The
    returned tree is passed as both ``base_dir`` and (its subpaths) ``scan_roots`` so the random
    ``tmp_path`` never leaks into the generated output.
    """
    tree = tmp_path / "repo"
    state = tree / ".memory" / "state"
    agreements = tree / ".memory" / "agreements"
    derived = tree / ".memory" / "derived"
    docs = tree / "docs"
    for d in (state, agreements, derived, docs):
        d.mkdir(parents=True, exist_ok=True)

    # --- memory items: two state files + one active + one retired agreement (slug "plan") --------
    (state / "activeContext.md").write_text(
        '---\nupdated: "2026-07-18"\n---\n\n# Active context\n\nSession progress log.\n',
        encoding="utf-8",
    )
    (state / "progress.md").write_text(
        '---\nupdated: "2026-07-18"\n---\n\n# Progress\n\nGit holds the full history.\n',
        encoding="utf-8",
    )
    (agreements / "plan.md").write_text(
        "---\nstatus: active\n"
        'added: "2026-07-18"\n'
        'provenance: "synthetic scan fixture"\n---\n\n'
        "# Plan before expanding\n\nUse the agreed plan first.\n",
        encoding="utf-8",
    )
    (agreements / "retire-me.md").write_text(
        "---\nstatus: retired\n"
        'added: "2026-07-18"\n'
        'provenance: "synthetic scan fixture"\n---\n\n'
        "# Retired rule\n\nNo longer in force.\n",
        encoding="utf-8",
    )

    # --- scan roots: a docs tree + a single-file AGENTS.md at the tree root ----------------------
    # docs/guide.md references the active-context PATH and the "plan" SLUG, plus a "planner" decoy.
    (docs / "guide.md").write_text(
        "# Guide\n"
        "See .memory/state/activeContext.md for the live session log.\n"
        "Follow the plan agreement before expanding scope.\n"
        "The planner subsystem is unrelated and must not match the slug.\n",
        encoding="utf-8",
    )
    # AGENTS.md references the agreement file PATH.
    (tree / "AGENTS.md").write_text(
        "# Agents\nRead .memory/agreements/plan.md before acting on working style.\n",
        encoding="utf-8",
    )
    # A derived artifact that MUST be excluded from any walk (self-reference churn guard).
    (derived / "pointer-index.md").write_text(
        "# DERIVED\n.memory/agreements/plan.md self-reference must not be scanned.\n",
        encoding="utf-8",
    )
    return tree


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
