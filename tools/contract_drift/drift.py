"""Contract-drift gate + breaking/non-breaking classification (CONTRACT-04, D-07).

``run_gate`` recomputes the live JCS SHA-256 manifest (via :mod:`tools.contract_hash`), diffs it
against the committed baseline ``contracts/.hashes/manifest.json``, and — for each changed schema —
classifies the change breaking vs non-breaking by diffing the two schema documents. Any divergence
(including a §4-5 convention flip in ``format-conventions.schema.json``, PITFALLS P14) trips the
gate. The CLI (``check.sh`` → ``python -m tools.contract_drift.drift``) exits 0 iff the live tree
matches the baseline.

Classification (seed change_policy — the instance's change-policy catalog):
  * purely additive (new optional property / new enum case) → ``non-breaking``
  * removed/renamed required field, or a changed/narrowed fixed value (const/enum) → ``breaking``
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from tools.contract_hash.hash import (
    CONTRACTS_DIR,
    MANIFEST_PATH,
    REPO_ROOT,
    build_manifest,
)
from tools.workspace_config import edges, load_workspace, members, split_endpoint

# ---- baseline / diff -----------------------------------------------------------------------


def load_baseline(baseline_path: str | Path = MANIFEST_PATH) -> dict[str, str]:
    """Load the committed per-schema JCS SHA-256 baseline manifest."""
    return json.loads(Path(baseline_path).read_text(encoding="utf-8"))


def diff_manifests(live: dict[str, str], baseline: dict[str, str]) -> dict[str, list[str]]:
    """Split the live-vs-baseline delta into changed / added / removed relative paths."""
    changed = sorted(k for k in live if k in baseline and live[k] != baseline[k])
    added = sorted(k for k in live if k not in baseline)
    removed = sorted(k for k in baseline if k not in live)
    return {"changed": changed, "added": added, "removed": removed}


# ---- classification ------------------------------------------------------------------------


def _hashable(value: object) -> object:
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
    return value


def _index(schema: object, path: tuple = ()) -> dict[tuple, tuple]:
    """Index a schema document into comparable constraints keyed by JSON path.

    Emits ``prop`` markers (property presence), plus ``const`` / ``enum`` / ``required``
    constraints, recursing through nested subschemas (so nested convention consts like
    ``float_compare.tolerance`` and the top-level ``bom`` const are both captured).
    """
    out: dict[tuple, tuple] = {}
    if isinstance(schema, dict):
        if "const" in schema:
            out[path + ("const",)] = ("const", _hashable(schema["const"]))
        if isinstance(schema.get("enum"), list):
            out[path + ("enum",)] = ("enum", frozenset(_hashable(v) for v in schema["enum"]))
        if isinstance(schema.get("required"), list):
            out[path + ("required",)] = ("required", frozenset(schema["required"]))
        props = schema.get("properties")
        if isinstance(props, dict):
            for name in props:
                out[path + ("properties", name)] = ("prop", None)
        for key, val in schema.items():
            if isinstance(val, (dict, list)):
                out.update(_index(val, path + (key,)))
    elif isinstance(schema, list):
        for i, item in enumerate(schema):
            out.update(_index(item, path + (i,)))
    return out


def classify(old: dict, new: dict) -> str:
    """Classify an old→new schema edit ``breaking`` or ``non-breaking``.

    Breaking iff any of: a property is removed/renamed, a required field is dropped, a fixed
    ``const`` value changes, or an ``enum`` narrows (drops a previously-allowed value). Purely
    additive edits (new optional property, new enum case) are non-breaking (seed change_policy).
    """
    old_idx = _index(old)
    new_idx = _index(new)
    for key, (kind, val) in old_idx.items():
        if kind == "prop":
            if key not in new_idx:
                return "breaking"  # removed / renamed field
            continue
        if key not in new_idx:
            return "breaking"  # a fixed constraint was dropped (loosened expected value)
        _nkind, nval = new_idx[key]
        if kind == "const":
            if nval != val:
                return "breaking"  # changed expected value
        elif kind == "enum":
            if not val.issubset(nval):
                return "breaking"  # removed/changed enum case (additive superset is fine)
        elif kind == "required":
            if val - nval:
                return "breaking"  # a previously-required field is no longer required
    return "non-breaking"


# ---- gate ----------------------------------------------------------------------------------


def _git_show(rel_path: str) -> dict | None:
    """Return the HEAD-committed schema document for ``rel_path``, or None if unavailable.

    Used to fetch the *old* content for classification when the drift is on a copied tmp tree.
    ``shell=False`` (argv list) — no shell interpolation.
    """
    try:
        proc = subprocess.run(
            ["git", "show", f"HEAD:{rel_path}"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            check=True,
            shell=False,
        )
        return json.loads(proc.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError, OSError):
        return None


def run_gate(
    contracts_dir: str | Path = CONTRACTS_DIR,
    baseline_path: str | Path = MANIFEST_PATH,
) -> dict:
    """Compare the live manifest against the baseline and classify each drifted schema.

    Returns ``{"ok": bool, "drifted": [(rel_path, kind, classification), ...]}`` where ``kind`` is
    ``changed`` | ``added`` | ``removed``. ``ok`` is True iff nothing drifted.
    """
    baseline = load_baseline(baseline_path)
    live = build_manifest(contracts_dir)
    delta = diff_manifests(live, baseline)
    base = Path(contracts_dir).resolve().parent

    drifted: list[tuple[str, str, str]] = []
    for rel in delta["changed"]:
        old = _git_show(rel)
        new_path = base / rel
        try:
            new = json.loads(new_path.read_bytes())
        except (OSError, json.JSONDecodeError):
            new = None
        cls = classify(old, new) if isinstance(old, dict) and isinstance(new, dict) else "unknown"
        drifted.append((rel, "changed", cls))
    for rel in delta["added"]:
        drifted.append((rel, "added", "non-breaking"))  # a new schema is purely additive
    for rel in delta["removed"]:
        drifted.append((rel, "removed", "breaking"))  # a removed contract is breaking

    return {"ok": not drifted, "drifted": drifted}


# ---- cross-repo (workspace) gate (MREPO-03) ------------------------------------------------


def workspace_drift(ws_path: str | Path | None = None) -> dict:
    """Cross-repo contract-drift over every declared workspace member + edge (MREPO-03).

    Two independent checks, both derived from ``workspace.toml`` at runtime (member roots are
    resolved via :mod:`tools.workspace_config` — NEVER hardcoded, so this stays clean under the
    GEN-04 core→workspace-member guard):

    1. **Per-member drift** — VERBATIM reuse of :func:`run_gate` for each member against its OWN
       ``contracts/.hashes/manifest.json``. Member manifests are NEVER merged: ``build_manifest``
       keys are ``.parent``-relative, so the ``contracts/...`` keys collide across members
       (Pitfall 2). Each member is gated against its own baseline exactly like the CI ``drift`` job
       gates two trees.
    2. **Cross-repo edge resolution** — for every ``[pipeline].edges`` edge, resolve the PRODUCER
       member (the repo half of the ``repo:stage`` ``from`` endpoint) and assert the edge
       ``contract`` is tracked as ``<producer>/contracts/**/<contract>.schema.json``. An edge whose
       contract is absent from its producer is reported (fail loud, naming the edge).

    Returns ``{"members": {id: run_gate_result}, "edges_checked": int,
    "unresolved_edges": [(edge, reason), ...], "ok": bool}`` where ``ok`` is True iff EVERY member
    is clean AND EVERY edge resolves. A zero-edge workspace resolves vacuously (the CLI prints a
    VISIBLE SKIP — a silent no-op is never mistaken for a pass, Pitfall 5 / T-11-08).
    """
    cfg = load_workspace(ws_path) if ws_path is not None else load_workspace()
    # Member roots are repo-relative; a member MAY carry an absolute root (e.g. a tmp test tree),
    # in which case ``REPO_ROOT / root`` yields the absolute root unchanged (pathlib semantics).
    by_id = {m["id"]: (REPO_ROOT / m["root"]) for m in members(cfg)}

    member_results: dict[str, dict] = {}
    for mid, mroot in by_id.items():
        cdir = mroot / "contracts"
        member_results[mid] = run_gate(
            contracts_dir=cdir,
            baseline_path=cdir / ".hashes" / "manifest.json",
        )

    edge_list = edges(cfg)
    unresolved: list[tuple[dict, str]] = []
    for edge in edge_list:
        producer_id, _stage = split_endpoint(edge["from"])
        producer_root = by_id.get(producer_id)
        if producer_root is None:
            unresolved.append((edge, f"producer {producer_id!r} is not a declared member"))
            continue
        schemas = {
            p.name.removesuffix(".schema.json")
            for p in (producer_root / "contracts").rglob("*.schema.json")
        }
        if edge["contract"] not in schemas:
            unresolved.append(
                (edge, f"contract {edge['contract']!r} not tracked in producer {producer_id!r}")
            )

    members_ok = all(res["ok"] for res in member_results.values())
    ok = members_ok and not unresolved
    return {
        "members": member_results,
        "edges_checked": len(edge_list),
        "unresolved_edges": unresolved,
        "ok": ok,
    }


def _run_workspace_gate() -> int:
    """Run :func:`workspace_drift` and print a per-member + per-edge report; exit non-zero on any
    member drift or unresolved edge."""
    result = workspace_drift()

    for mid, mres in result["members"].items():
        if mres["ok"]:
            print(
                f"contract-drift [workspace]: OK — member {mid!r} matches its committed baseline."
            )
        else:
            print(f"contract-drift [workspace]: DRIFT — member {mid!r}:", file=sys.stderr)
            for rel, kind, cls in mres["drifted"]:
                print(f"  [{kind:7}] [{cls:12}] {rel}", file=sys.stderr)

    if result["edges_checked"] == 0:
        print(
            "SKIP: workspace declares zero cross-repo edges — no edge-contract resolution to "
            "gate (no-op)."
        )
    elif result["unresolved_edges"]:
        print("contract-drift [workspace]: UNRESOLVED EDGE(S):", file=sys.stderr)
        for edge, reason in result["unresolved_edges"]:
            print(f"  {edge!r}: {reason}", file=sys.stderr)
    else:
        print(
            f"contract-drift [workspace]: OK — all {result['edges_checked']} edge contract(s) "
            "resolve in their producer member."
        )

    if result["ok"]:
        print("contract-drift [workspace]: OK — all members clean and every edge resolved.")
        return 0
    print(
        "contract-drift [workspace]: FAIL — cross-repo drift or an unresolved edge contract.",
        file=sys.stderr,
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(
        prog="python -m tools.contract_drift.drift",
        description="Gate the live contracts tree against its committed JCS SHA-256 baseline.",
    )
    parser.add_argument(
        "--contracts-dir",
        default=CONTRACTS_DIR,
        help="Contracts subtree to hash (default: the root contracts/ tree).",
    )
    parser.add_argument(
        "--baseline",
        default=MANIFEST_PATH,
        help="Committed manifest to diff against (default: contracts/.hashes/manifest.json).",
    )
    parser.add_argument(
        "--workspace",
        action="store_true",
        help=(
            "Run the cross-repo workspace gate (MREPO-03): per-member drift over every "
            "workspace.toml member + edge-contract resolution in the producer member. Additive — "
            "ignores --contracts-dir/--baseline."
        ),
    )
    args = parser.parse_args(argv)

    if args.workspace:
        return _run_workspace_gate()

    result = run_gate(contracts_dir=args.contracts_dir, baseline_path=args.baseline)
    if result["ok"]:
        print("contract-drift: OK — live manifest matches the committed baseline.")
        return 0
    print("contract-drift: DRIFT DETECTED — unapproved schema change(s):", file=sys.stderr)
    for rel, kind, cls in result["drifted"]:
        print(f"  [{kind:7}] [{cls:12}] {rel}", file=sys.stderr)
    is_root = Path(args.contracts_dir).resolve() == CONTRACTS_DIR.resolve()
    if is_root:
        rebaseline = "`python -m tools.contract_hash.hash --write`"
    else:
        rebaseline = (
            "`python -m tools.contract_hash.hash --write "
            f"--contracts-dir {args.contracts_dir} --manifest {args.baseline}`"
        )
    print(
        f"\nIf intended, update the baseline ({rebaseline}) "
        "and pair it with a golden/ADR update (CODEOWNERS-gated).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
