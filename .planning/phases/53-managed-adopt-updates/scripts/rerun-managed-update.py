"""Compare one managed-adopt apply cycle without writing into its target.

Adapted from Phase 52's ``compare-worktree-writes.py``: porcelain-v2 parsing and
the harness-managed lock-sidecar allowlist retain that script's established shape.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
PHASE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.adoption_apply.apply import HARNESS_MANAGED_LOCK_SIDECARS  # noqa: E402
from tools.adoption_apply.installed import (  # noqa: E402
    INSTALLED_REL,
    installed_path,
    read_installed_record,
)

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


def expected_disposition_paths(manifest: dict) -> set[str]:
    return {
        record["destination"]
        for record in manifest.get("dispositions", [])
        if record.get("disposition") in ("create", "update", "marker-merge")
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--before-tree", type=Path)
    parser.add_argument("--after-tree", type=Path)
    parser.add_argument("--require-no-writes", action="store_true")
    args = parser.parse_args(argv)
    if not args.out.resolve().is_relative_to(PHASE_ROOT):
        parser.error(f"--out must stay under {PHASE_ROOT}")

    changed_paths = sorted(
        parse_porcelain_v2_paths(args.after.read_text())
        - parse_porcelain_v2_paths(args.before.read_text())
    )

    # 53-CONTEXT.md's "before/after tree hash": the porcelain delta above is a PATH-SET
    # difference and is therefore blind to a file whose CONTENT was rewritten while its path
    # stayed in the set — which, after the first cycle, is every managed destination. The
    # per-file digest maps below are what actually decide the no-op claim; `changed_paths`
    # alone would report a rewrite-everything run as clean.
    content_changed_paths: list[str] | None = None
    if args.before_tree and args.after_tree:
        before_tree = json.loads(args.before_tree.read_text())
        after_tree = json.loads(args.after_tree.read_text())
        content_changed_paths = sorted(
            path
            for path in set(before_tree) | set(after_tree)
            if before_tree.get(path) != after_tree.get(path)
        )
    # The union is what every downstream verdict is computed from: a path that appeared AND a
    # path whose bytes changed are both "written". Falls back to the path-set delta alone when
    # no tree digests were supplied, so older invocations keep their meaning.
    effective_changed = sorted(set(changed_paths) | set(content_changed_paths or []))

    manifest = json.loads(args.manifest.read_text())
    expected_paths = expected_disposition_paths(manifest)
    unexpected_paths = sorted(
        path
        for path in effective_changed
        if path not in expected_paths
        and path not in HARNESS_MANAGED_LOCK_SIDECARS
        and path != INSTALLED_REL
    )
    records = read_installed_record(args.target)
    record_path = installed_path(args.target)
    result = {
        "changed_paths": changed_paths,
        "content_changed_paths": content_changed_paths,
        "effective_changed_paths": effective_changed,
        "expected_disposition_paths": sorted(expected_paths),
        "expected_lock_sidecars": sorted(HARNESS_MANAGED_LOCK_SIDECARS),
        "unexpected_paths": unexpected_paths,
        "product_code_paths": sorted(
            path for path in effective_changed if path.startswith(("apps/", "packages/", "src/"))
        ),
        "matches": not unexpected_paths,
        "disposition_counts": dict(
            sorted(
                Counter(
                    record["disposition"] for record in manifest.get("dispositions", [])
                ).items()
            )
        ),
        "installed_record_sha256": hashlib.sha256(record_path.read_bytes()).hexdigest(),
        "installed_record_destinations": sorted(record["destination"] for record in records),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.require_no_writes and set(effective_changed) - HARNESS_MANAGED_LOCK_SIDECARS:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
