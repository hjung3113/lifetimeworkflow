"""RFC 8785 (JCS) canonicalize + SHA-256 per-schema hasher → manifest (CONTRACT-04, D-07).

``schema_hash`` canonicalizes one ``.schema.json`` with ``rfc8785`` (Trail of Bits, spec-exact
number canonicalization) and SHA-256s the canonical bytes — NEVER hand-rolling either the
canonicalization or the hash (RESEARCH §Don't Hand-Roll). ``build_manifest`` maps every
``contracts/**/*.schema.json`` relative path to its hash; the ``--write`` CLI emits the committed
baseline ``contracts/.hashes/manifest.json``.

The manifest deliberately includes ``format-conventions.schema.json`` so a §4-5 cross-cutting
convention change trips the drift gate exactly like a column reorder (PITFALLS P14).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import rfc8785

# tools/contract_hash/hash.py → parents[2] == repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_DIR = REPO_ROOT / "contracts"
MANIFEST_PATH = CONTRACTS_DIR / ".hashes" / "manifest.json"

# Glob confined to the contracts/ subtree — no path traversal outside the repo.
SCHEMA_GLOB = "**/*.schema.json"


def schema_hash(path: str | Path) -> str:
    """Return the stable SHA-256 hex of the RFC 8785 (JCS) canonical form of a schema file.

    Same JSON input → same hash, regardless of key order or insignificant whitespace, because
    ``rfc8785.dumps`` produces the canonical byte serialization.
    """
    obj = json.loads(Path(path).read_bytes())
    canon = rfc8785.dumps(obj)  # bytes, RFC 8785 canonical form
    return hashlib.sha256(canon).hexdigest()


def build_manifest(contracts_dir: str | Path = CONTRACTS_DIR) -> dict[str, str]:
    """Map every ``contracts/**/*.schema.json`` (repo-relative POSIX path) → its JCS SHA-256.

    Keys are relative to ``contracts_dir``'s parent so both the real repo tree and a copied tmp
    tree (used by the drift tests) yield identical ``contracts/...`` keys. The glob is confined to
    ``contracts_dir`` — no traversal outside that subtree.
    """
    root = Path(contracts_dir).resolve()
    base = root.parent
    manifest: dict[str, str] = {}
    for p in sorted(root.glob(SCHEMA_GLOB)):
        resolved = p.resolve()
        # Defense-in-depth: ignore anything a symlink might point outside the subtree.
        if root != resolved and root not in resolved.parents:
            continue
        rel = resolved.relative_to(base).as_posix()
        manifest[rel] = schema_hash(resolved)
    return manifest


def write_manifest(
    manifest_path: str | Path = MANIFEST_PATH,
    contracts_dir: str | Path = CONTRACTS_DIR,
) -> Path:
    """Build the manifest over ``contracts_dir`` (defaults to the real tree) and write it.

    Threading ``contracts_dir`` lets ``--write --contracts-dir <D>`` rebaseline the flagged tree
    with D-rooted hashes instead of silently writing root-tree content into it.
    """
    manifest = build_manifest(contracts_dir)
    out = Path(manifest_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(
        prog="python -m tools.contract_hash.hash",
        description="Emit or (re)write the per-schema JCS SHA-256 manifest for a contracts tree.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the manifest to --manifest (default: contracts/.hashes/manifest.json).",
    )
    parser.add_argument(
        "--contracts-dir",
        default=CONTRACTS_DIR,
        help="Contracts subtree to hash (default: the root contracts/ tree).",
    )
    parser.add_argument(
        "--manifest",
        default=MANIFEST_PATH,
        help="Manifest path to write when --write is given.",
    )
    args = parser.parse_args(argv)

    if args.write:
        out = write_manifest(manifest_path=args.manifest, contracts_dir=args.contracts_dir)
        manifest = json.loads(out.read_text(encoding="utf-8"))
        try:
            shown = out.resolve().relative_to(REPO_ROOT)
        except ValueError:
            shown = out  # --manifest may target a path outside the repo (e.g. a tmp rebaseline)
        print(f"wrote {shown} ({len(manifest)} schemas hashed)")
    else:
        print(
            json.dumps(build_manifest(contracts_dir=args.contracts_dir), indent=2, sort_keys=True)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
