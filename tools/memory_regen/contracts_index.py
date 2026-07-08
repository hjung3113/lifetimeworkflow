"""contracts-index generator — scan contracts/ + REUSE Phase-1 hash/drift → derived index (MEM-03).

This generator is ~80% reuse (RESEARCH §Pattern 3 / Key insight): it imports the Phase-1
:func:`tools.contract_hash.hash.build_manifest` (RFC 8785 JCS + SHA-256, per-schema) and
:func:`tools.contract_drift.drift.run_gate` (live-vs-baseline drift + breaking classification) and
NEVER re-implements hashing or the drift comparison — a second implementation could silently
disagree with the Phase-1 gate (T-02-09, drift laundering). The only new logic is row assembly,
deterministic rendering, and the byte-identical determinism guarantee.

Output: ``.memory/derived/contracts-index.md`` (gitignored, D-03) — one compact row per contract
(path, kind, hash prefix, owner→TBD, live drift status), header-marked ``DERIVED — do not
hand-edit`` (D-04 / T-02-08). No timestamp, no raw float, no full schema body (Pitfall 1 / T-02-06):
delete + regenerate reproduces the file byte-for-byte (success criterion 2, proven by a committed
syrupy snapshot — NOT git diff, because the target is gitignored, Pitfall 2).

Entrypoint: ``python -m tools.memory_regen.contracts_index``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from tools.contract_drift.drift import run_gate
from tools.contract_hash.hash import CONTRACTS_DIR, MANIFEST_PATH, build_manifest

# --- paths (derived plane is gitignored + regenerated every session, D-03) --------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
DERIVED_DIR = _REPO_ROOT / ".memory" / "derived"
INDEX_PATH = DERIVED_DIR / "contracts-index.md"

# --- stable text (part of the derived-plane contract) -----------------------------------------
DERIVED_HEADER = "DERIVED — do not hand-edit (tools/memory_regen/contracts_index.py)"

# contracts/<top>/... segment → human-readable kind (RESEARCH §row assembly). Unknown → "other".
KIND = {
    "log-specs": "log-spec",
    "normalization": "normalization",
    "reference-data": "reference-data",
    "state": "state",
}

# No machine-readable owner today (contracts/README.md: "owner: TBD") → emit TBD,
# never fabricate (A3).
OWNER_TBD = "TBD"

# Length of the hash prefix folded into a row — enough to disambiguate, not the full 64-hex digest.
_HASH_PREFIX = 12


def index_rows(
    contracts_dir: str | Path = CONTRACTS_DIR,
    baseline_path: str | Path = MANIFEST_PATH,
) -> list[tuple[str, str, str, str, str]]:
    """Assemble one sorted row per contract by REUSING build_manifest() + run_gate().

    Each row is ``(rel_path, kind, owner, hash_prefix, drift_status)``:
      * ``rel_path`` — ``contracts/...`` POSIX key (from the reused manifest).
      * ``kind`` — derived from the ``contracts/<top>/`` segment via :data:`KIND` (else
        ``other``).
      * ``owner`` — always :data:`OWNER_TBD` (A3 — no machine-readable owner exists; never
        fabricate).
      * ``hash_prefix`` — first :data:`_HASH_PREFIX` hex chars of the Phase-1 JCS SHA-256
        (no re-hash).
      * ``drift_status`` — ``clean`` unless the schema is in ``run_gate()["drifted"]``, in
        which case ``drift:<kind>:<classification>`` (e.g. ``drift:changed:breaking``).

    Rows are sorted by relative path so the render is deterministic (Pitfall 1).
    """
    manifest = build_manifest(contracts_dir)
    gate = run_gate(contracts_dir, baseline_path)
    drift = {rel: (kind, cls) for rel, kind, cls in gate["drifted"]}

    rows: list[tuple[str, str, str, str, str]] = []
    for rel in sorted(manifest):
        # rel == "contracts/<top>/...": parts[1] is the top-level contract family segment.
        top = Path(rel).parts[1] if len(Path(rel).parts) > 1 else ""
        status = "drift:" + ":".join(drift[rel]) if rel in drift else "clean"
        rows.append((rel, KIND.get(top, "other"), OWNER_TBD, manifest[rel][:_HASH_PREFIX], status))
    return rows


def render(rows: list[tuple[str, str, str, str, str]]) -> str:
    """Render rows into the deterministic DERIVED-marked markdown index.

    Output = the ``DERIVED — do not hand-edit`` header, then a stable markdown table (one
    row per contract, sorted). Contains NO timestamp and NO raw float (Pitfall 1) so
    generating twice is byte-identical. Hash prefixes are content-derived (stable).
    Trailing newline for POSIX-clean text.
    """
    lines = [
        f"# {DERIVED_HEADER}",
        "",
        f"Generated from contracts/ by `python -m tools.memory_regen.contracts_index` "
        f"(reuses tools.contract_hash + tools.contract_drift). {len(rows)} contract(s).",
        "",
        "| contract | kind | owner | hash | drift |",
        "| --- | --- | --- | --- | --- |",
    ]
    for rel, kind, owner, hash_prefix, status in rows:
        lines.append(f"| {rel} | {kind} | {owner} | {hash_prefix} | {status} |")
    return "\n".join(lines) + "\n"


def write(
    index_path: str | Path = INDEX_PATH,
    contracts_dir: str | Path = CONTRACTS_DIR,
    baseline_path: str | Path = MANIFEST_PATH,
) -> Path:
    """Regenerate the derived contracts-index and write it (mkdir parents), returning the path."""
    out = Path(index_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(index_rows(contracts_dir, baseline_path)), encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    """CLI: regenerate ``.memory/derived/contracts-index.md`` (`python -m ...contracts_index`)."""
    argv = sys.argv[1:] if argv is None else argv  # noqa: F841 (reserved for future flags)
    out = write()
    rows = index_rows()
    print(f"wrote {out.relative_to(_REPO_ROOT)} ({len(rows)} contract(s) indexed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
