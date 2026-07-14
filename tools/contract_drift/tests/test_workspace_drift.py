"""Cross-repo contract-drift gate over the workspace manifest (MREPO-03).

Proves ``tools.contract_drift.drift.workspace_drift`` (and the ``--workspace`` CLI):

* the committed 2-member fixture gates CLEAN (all members match their own baseline, the one edge
  resolves in its producer) → ``ok=True``;
* a per-member drift (a mutated schema over a stale baseline) is DETECTED → ``ok=False``;
* an edge whose ``contract`` is absent from its producer is flagged UNRESOLVED → ``ok=False``.

GEN-04 core-plane invariant (this file lives under ``tools/``): the member roots it needs are
resolved at RUNTIME via ``tools.workspace_config.members()``/``load_workspace()`` — NEVER as a
hardcoded member-root path literal — so it passes the 11-02 generalized GEN-04 guard
(``test_core_no_workspace_member_dep.py``). The committed fixture is never mutated; drift/unresolved
cases are constructed in tmp trees pointed at by tmp ``workspace.toml`` manifests.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

# Make the repo-root `tools` package importable (virtual uv workspace members, not pip-installed).
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.contract_drift.drift import main, workspace_drift  # noqa: E402
from tools.workspace_config import load_workspace, members  # noqa: E402


def _first_member_root() -> tuple[str, Path]:
    """Resolve (id, absolute root) of the first declared member from the manifest at runtime.

    The root is derived from ``members(load_workspace())`` — not a hardcoded fixtures path — so this
    test tracks the manifest and passes the GEN-04 workspace-member guard.
    """
    m = members(load_workspace())[0]
    return m["id"], (_REPO_ROOT / m["root"]).resolve()


def _write_workspace_toml(path: Path, members_tbl: list[dict], edges: list[dict]) -> None:
    """Materialize a minimal tmp ``workspace.toml`` (absolute member roots + optional edges)."""
    lines = ["[workspace]", 'id = "test-ws"', ""]
    for m in members_tbl:
        lines += ["[[members]]", f'id = "{m["id"]}"', f'root = "{m["root"]}"', ""]
    lines.append("[pipeline]")
    if edges:
        rendered = ", ".join(
            f'{{ from = "{e["from"]}", to = "{e["to"]}", contract = "{e["contract"]}" }}'
            for e in edges
        )
        lines.append(f"edges = [ {rendered} ]")
    else:
        lines.append("edges = []")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_committed_fixture_gates_clean() -> None:
    """The real 2-member fixture: every member clean + the edge resolves → ok=True."""
    result = workspace_drift()
    assert result["ok"], f"committed workspace fixture should gate clean: {result}"
    assert result["members"], "at least one member must be gated"
    assert all(res["ok"] for res in result["members"].values())
    assert not result["unresolved_edges"]


def test_workspace_cli_exits_zero_on_clean_fixture(capsys) -> None:
    """``drift --workspace`` exits 0 against the committed fixture and prints per-member OK."""
    rc = main(["--workspace"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "OK" in out


def test_per_member_drift_is_detected(tmp_path: Path) -> None:
    """A mutated schema over a stale baseline in a member tree → that member drifts → ok=False."""
    _mid, src_root = _first_member_root()
    member_root = tmp_path / "drifted-member"
    shutil.copytree(src_root, member_root)

    # Mutate one schema WITHOUT re-baselining → live hash diverges from the committed manifest.
    schema = next((member_root / "contracts").rglob("*.schema.json"))
    doc = json.loads(schema.read_text(encoding="utf-8"))
    doc["x-drift-marker"] = "unapproved-edit"  # any content change bumps the JCS SHA-256
    schema.write_text(json.dumps(doc, indent=2), encoding="utf-8")

    ws = tmp_path / "workspace.toml"
    _write_workspace_toml(ws, [{"id": "m", "root": str(member_root)}], edges=[])

    result = workspace_drift(ws)
    assert not result["ok"], "a per-member schema drift must fail the workspace gate"
    assert not result["members"]["m"]["ok"], "the mutated member must report drift"


def test_unresolved_edge_contract_is_flagged(tmp_path: Path) -> None:
    """An edge whose contract is not tracked in its producer member → ok=False (fail loud)."""
    _mid, src_root = _first_member_root()
    member_root = tmp_path / "clean-member"
    shutil.copytree(src_root, member_root)  # pristine copy → the member itself gates clean

    ws = tmp_path / "workspace.toml"
    _write_workspace_toml(
        ws,
        [{"id": "producer", "root": str(member_root)}],
        edges=[{"from": "producer:emit", "to": "producer:ingest", "contract": "no-such-contract"}],
    )

    result = workspace_drift(ws)
    assert result["members"]["producer"]["ok"], "the member tree itself is clean"
    assert not result["ok"], "an unresolved edge contract must fail the workspace gate"
    assert result["unresolved_edges"], "the missing-contract edge must be reported"
    edge, reason = result["unresolved_edges"][0]
    assert edge["contract"] == "no-such-contract"
    assert "no-such-contract" in reason
