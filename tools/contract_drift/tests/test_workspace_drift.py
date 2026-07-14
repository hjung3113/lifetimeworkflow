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
import subprocess
import sys
from pathlib import Path

# Make the repo-root `tools` package importable (virtual uv workspace members, not pip-installed).
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.contract_drift.drift import main, run_gate, workspace_drift  # noqa: E402
from tools.contract_hash.hash import write_manifest  # noqa: E402
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


def _init_member_git_repo(member_root: Path, schema_doc: dict) -> Path:
    """Materialize a standalone git repo playing a member root: commit ``schema_doc`` under
    ``contracts/greeting.schema.json`` so ``_git_show`` can recover it from HEAD, then baseline it.

    Returns the member's ``contracts/`` dir. The schema is committed BEFORE the baseline manifest is
    written so HEAD holds the pre-drift content (what classification diffs the on-disk edit against).
    """
    contracts = member_root / "contracts"
    contracts.mkdir(parents=True)
    schema = contracts / "greeting.schema.json"
    schema.write_text(json.dumps(schema_doc, indent=2), encoding="utf-8")

    def _git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=str(member_root), check=True, capture_output=True)

    _git("init", "-q")
    _git("config", "user.email", "regression@test.local")
    _git("config", "user.name", "regression")
    _git("add", "-A")
    _git("commit", "-qm", "seed member schema")

    write_manifest(manifest_path=contracts / ".hashes" / "manifest.json", contracts_dir=contracts)
    return contracts


# The pre-drift baseline schema every classification-regression case starts from.
_BASE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {"greeting": {"type": "string"}, "name": {"type": "string"}},
    "required": ["greeting", "name"],
}


def test_member_breaking_change_is_classified_not_unknown(tmp_path: Path) -> None:
    """Regression (CR-01): a member-root-relative schema change is classified ``breaking`` — NOT the
    silent ``unknown`` produced when ``_git_show`` queried the top-level repo root instead of the
    member root. A breaking edit (drop a required property) must be recovered + classified.
    """
    contracts = _init_member_git_repo(tmp_path / "member", _BASE_SCHEMA)

    breaking = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {"greeting": {"type": "string"}},  # 'name' removed → breaking
        "required": ["greeting"],  # 'name' no longer required → breaking
    }
    (contracts / "greeting.schema.json").write_text(
        json.dumps(breaking, indent=2), encoding="utf-8"
    )

    result = run_gate(
        contracts_dir=contracts, baseline_path=contracts / ".hashes" / "manifest.json"
    )
    assert not result["ok"], "the mutated member schema must trip the gate"
    classes = {rel: cls for rel, kind, cls in result["drifted"]}
    assert classes.get("contracts/greeting.schema.json") == "breaking", (
        f"member drift must classify as 'breaking', not 'unknown': {result['drifted']}"
    )


def test_member_non_breaking_change_is_classified_not_unknown(tmp_path: Path) -> None:
    """Regression (CR-01): a purely additive member schema edit (new optional property) classifies
    ``non-breaking`` — proving ``_git_show`` recovered the member's HEAD schema (not ``unknown``).
    """
    contracts = _init_member_git_repo(tmp_path / "member", _BASE_SCHEMA)

    additive = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "greeting": {"type": "string"},
            "name": {"type": "string"},
            "locale": {"type": "string"},  # new OPTIONAL property → non-breaking
        },
        "required": ["greeting", "name"],
    }
    (contracts / "greeting.schema.json").write_text(
        json.dumps(additive, indent=2), encoding="utf-8"
    )

    result = run_gate(
        contracts_dir=contracts, baseline_path=contracts / ".hashes" / "manifest.json"
    )
    assert not result["ok"], "the additive member schema edit must still trip the gate (hash drift)"
    classes = {rel: cls for rel, kind, cls in result["drifted"]}
    assert classes.get("contracts/greeting.schema.json") == "non-breaking", (
        f"additive member drift must classify as 'non-breaking', not 'unknown': {result['drifted']}"
    )


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
