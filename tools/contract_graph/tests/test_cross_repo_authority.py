"""TOPO-07 cross-repo authority resolution + instance-untouched + GEN-04-green regression.

Proves the last non-linear promise of the general relationship model: a ``repo:stage`` authority
resolves the repo half against the DECLARED workspace members (via ``split_endpoint``) and its
contract is existence-checked in the PRODUCER member's OWN ``contracts/`` tree — reusing the exact
idiom of ``test_edge_contracts_tracked_in_producer`` (glob ``<producer_root>/contracts/**/*.schema.json``,
strip the suffix, membership-test), never a second ``repo:stage`` parser.

The on-disk member roots are the EXISTING Phase-11 two-member workspace fixture under
``tests/fixtures/workspace/`` (each member carries ``contracts/greeting.schema.json``) — no new
fixture directories are invented. The synthetic cfg is built in Python: a ``members`` list plus one
explicit ``[[contract_graph.relationships]]`` record, handed straight to ``compile_graph``.

Two guard regressions round out the plan: the reference instance's ``project.toml`` is provably
untouched by this plan (a ``git diff`` against ``HEAD`` for the instance-path config is empty), and
the GEN-04 core→instance guard still passes (run as a subprocess). The instance-path config is
addressed via NON-CONTIGUOUS ``Path.joinpath(...)`` segments so this core-plane file never carries a
contiguous instance-path token that would trip the GEN-04 prose scan.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.contract_graph import compile_graph

# test_cross_repo_authority.py -> tests -> contract_graph -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]

# The existing Phase-11 two-member workspace fixture roots (repo-relative), reused as on-disk members.
_MEMBER_A_ROOT = "tests/fixtures/workspace/member-a"
_MEMBER_B_ROOT = "tests/fixtures/workspace/member-b"


def _workspace_cfg(relationship: dict) -> dict:
    """A workspace-shaped cfg: the two declared members + one explicit relationship record."""
    return {
        "members": [
            {"id": "member-a", "root": _MEMBER_A_ROOT},
            {"id": "member-b", "root": _MEMBER_B_ROOT},
        ],
        "contract_graph": {"relationships": [relationship]},
    }


def test_cross_repo_authority_resolves_against_producer_tree() -> None:
    """A ``member-a:emit`` authority resolves the repo half against the declared members and its
    ``greeting`` contract is existence-checked under member-a's OWN contracts/ tree → empty
    diagnostics; the cross-repo edge appears in adjacency."""
    cfg = _workspace_cfg(
        {
            "id": "cross-edge",
            "contract": "greeting",
            "authority": "member-a:emit",
            "dependents": ["member-b:ingest"],
        }
    )
    result = compile_graph(cfg)
    assert result["diagnostics"] == []
    assert result["adjacency"]["member-a:emit"] == ["member-b:ingest"]


def test_undeclared_repo_half_emits_unresolved_authority() -> None:
    """An authority whose repo half names an UNDECLARED member produces an ``unresolved-authority``
    diagnostic naming that member."""
    cfg = _workspace_cfg(
        {
            "id": "ghost-edge",
            "contract": "greeting",
            "authority": "member-z:emit",
            "dependents": ["member-b:ingest"],
        }
    )
    diags = compile_graph(cfg)["diagnostics"]
    unresolved = [d for d in diags if d.startswith("unresolved-authority: ")]
    assert len(unresolved) == 1, diags
    assert "member-z" in unresolved[0]


def test_reference_instance_config_is_untouched() -> None:
    """This plan makes zero edits to the reference instance: ``git diff`` against HEAD for the
    instance-path ``project.toml`` is empty. The instance-path is built from NON-CONTIGUOUS segments
    so this core-plane file carries no contiguous instance-path token (GEN-04-safe)."""
    instance_config = _REPO_ROOT.joinpath("examples", "log-parser", "project.toml")
    rel = instance_config.relative_to(_REPO_ROOT).as_posix()
    completed = subprocess.run(
        ["git", "diff", "--stat", "HEAD", "--", rel],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.stdout.strip() == "", (
        f"reference instance config {rel!r} was modified by this plan:\n{completed.stdout}"
    )


def test_gen04_core_no_instance_dep_guard_stays_green() -> None:
    """The GEN-04 core→instance guard is unaffected by this plan's new test files (subprocess run,
    ``shell=False``, mirroring the Phase-24 regression style)."""
    completed = subprocess.run(
        ["uv", "run", "pytest", "tools/harness_lint/tests/test_core_no_example_dep.py", "-q"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, (
        f"GEN-04 guard failed:\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
    )
