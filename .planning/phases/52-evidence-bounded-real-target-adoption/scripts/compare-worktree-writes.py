"""compare-worktree-writes.py — Phase 52 Plan 05, D-21 phase-local comparison script.

Compares a worktree's `git status --porcelain=v2 --untracked-files=all` capture taken
BEFORE `apply` against the same capture taken AFTER, derives the set of changed paths,
and classifies each against two allowlists:

  - `expected_disposition_paths` — destinations whose manifest disposition record was
    applied with status "applied" (read from the drafted `manifest.json` + the batch's
    recorded apply result is not persisted, so this script re-derives "applied" the same
    way `apply_manifest` does: every `create` and `marker-merge` disposition is a
    candidate destination it may have written; the actual written set is exactly the
    changed-path set intersected with this candidate set).
  - `expected_lock_sidecars` — imported verbatim from `tools.adoption_apply.apply.
    expected_lock_sidecars`/`HARNESS_MANAGED_LOCK_SIDECARS` (never retyped, D-21).

`unexpected_paths` is `changed_paths` minus both allowlists. `matches` is true iff
`unexpected_paths` is empty. `product_code_paths` is any changed path under `apps/`,
`packages/`, `src/`, or otherwise not a harness destination/sidecar — D-06's zero
product-code-write invariant.

This script is deliberately NOT a `tools/` module (D-21): it is phase-local scope, not a
shared, more-widely-imported helper — mirroring Phase 51's plan-inline `matches`/
`unexpected_paths` idiom.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from tools.adoption_apply.apply import expected_lock_sidecars  # noqa: E402
from tools.adoption_scan.destinations import MARKER_CAPABLE  # noqa: E402

# Porcelain v2 lines start with one of: 1 (changed), 2 (renamed/copied), u (unmerged),
# ? (untracked), ! (ignored). Path is the LAST whitespace-separated field for 1/2/u lines
# (renames carry an "orig -> path"-free single trailing path in v2, with the rename score
# and original path as separate fields before it); untracked/ignored lines are "? <path>".
_PORCELAIN_PATH_RE = re.compile(r"^([12u])\s")


def parse_porcelain_v2_paths(text: str) -> set[str]:
    paths: set[str] = set()
    for line in text.splitlines():
        if not line:
            continue
        kind = line[0]
        if kind in ("?", "!"):
            paths.add(line[2:])
        elif kind in ("1", "2", "u"):
            fields = line.split(" ")
            if kind == "2":
                # rename/copy: last field is the new path; the "orig_path" (post-tab in
                # some formats) is not used here since we only need the changed-path set.
                paths.add(fields[-1])
            else:
                paths.add(fields[-1])
    return paths


def compute_expected_disposition_paths(manifest: dict) -> set[str]:
    """Destinations whose disposition is one apply.py ever WRITES (create/marker-merge).

    Mirrors `apply_disposition`'s branch structure: only `create` and `marker-merge`
    dispositions ever reach a filesystem write; `preserve`/`conflict`/`derived-regenerate`/
    `human-ratification-required` are skipped/refused and never touch the target.
    """
    return {
        record["destination"]
        for record in manifest.get("dispositions", [])
        if record.get("disposition") in ("create", "marker-merge")
    }


def is_product_code_path(path: str, expected_paths: set[str], expected_sidecars: set[str]) -> bool:
    if path in expected_paths or path in expected_sidecars:
        return False
    return bool(path.startswith("apps/") or path.startswith("packages/") or path.startswith("src/"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="compare-worktree-writes")
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    before_paths = parse_porcelain_v2_paths(args.before.read_text())
    after_paths = parse_porcelain_v2_paths(args.after.read_text())
    changed_paths = sorted(after_paths - before_paths)

    manifest = json.loads(args.manifest.read_text())
    expected_disposition_paths = compute_expected_disposition_paths(manifest)
    expected_lock_sidecar_paths = expected_lock_sidecars(MARKER_CAPABLE)

    unexpected_paths = sorted(
        p
        for p in changed_paths
        if p not in expected_disposition_paths and p not in expected_lock_sidecar_paths
    )
    product_code_paths = sorted(
        p
        for p in changed_paths
        if is_product_code_path(p, expected_disposition_paths, expected_lock_sidecar_paths)
    )

    result = {
        "changed_paths": changed_paths,
        "expected_disposition_paths": sorted(expected_disposition_paths),
        "expected_lock_sidecars": sorted(expected_lock_sidecar_paths),
        "unexpected_paths": unexpected_paths,
        "matches": len(unexpected_paths) == 0,
        "product_code_paths": product_code_paths,
    }
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
