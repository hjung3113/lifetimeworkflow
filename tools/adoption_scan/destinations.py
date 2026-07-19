"""destinations.py — the static 40-row Authoritative Harness Destination Catalog + the total,
7-step disposition resolution chain (ADOPT-03, D-03/D-04).

Every non-GSD-owned catalog row resolves to EXACTLY ONE of the 6 `dispositionEnum` values
(``create``/``preserve``/``conflict``/``marker-merge``/``derived-regenerate``/
``human-ratification-required``) — totality, proven by
``tools/adoption_scan/tests/test_dispositions.py::test_total``. Row 40 (GSD-owned lanes) is
present in the catalog for documentation purposes only; it is EXCLUDED from disposition
resolution, never assigned a disposition (recorded in ``manifest["excluded"]`` instead).

This module NEVER retypes ``CONSTITUTION_GLOBS`` or ``is_gsd_owned`` — both are imported from
their authoritative sources (26-RESEARCH.md "Don't Hand-Roll"):

- ``tools.hooks.contract_guard.CONSTITUTION_GLOBS`` — the CODEOWNERS-gated constitution plane.
- ``tools.harness_emit.manifest.is_gsd_owned`` — the GSD-owned-lane exclusion predicate.

The marker-capable set (D-03) is a plain 3-item literal here, cited against its provenance in
``tools.harness_emit.merge`` (``BEGIN_MARKER``/``END_MARKER`` for root ``AGENTS.md``/``CLAUDE.md``;
``merge_settings`` for ``.claude/settings.json``) — this tool never performs a merge itself
(Phase 27 does), so it only needs to know WHICH 3 paths are marker-capable, not how to merge them.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from tools.harness_emit.manifest import is_gsd_owned
from tools.harness_perms import resolve_path
from tools.hooks.contract_guard import CONSTITUTION_GLOBS  # noqa: F401 (re-exported for callers)

# D-03 — exactly these 3 paths; see tools/harness_emit/merge.py BEGIN_MARKER/END_MARKER (root
# AGENTS.md/CLAUDE.md) and merge_settings (.claude/settings.json). Nested AGENTS.md files are
# ordinary create/preserve/conflict — the emitter splices only the root pair.
MARKER_CAPABLE: frozenset[str] = frozenset({"AGENTS.md", "CLAUDE.md", ".claude/settings.json"})

# D-04 — committed-derived destinations; always derived-regenerate regardless of existing-file
# state (a stale derived file must be regenerated, never "preserved").
DERIVED_GLOBS: list[str] = [
    "docs/reference/**",
    ".memory/derived/**",
    ".memory/state/**",
    ".opencode/**",
    ".claude/agents/**",
    ".claude/commands/**",
    ".claude/skills/**",
    "opencode.json",
]

# The exact 6-value dispositionEnum (contracts/harness/adoption/manifest.schema.json).
DISPOSITION_ENUM: tuple[str, ...] = (
    "create",
    "preserve",
    "conflict",
    "marker-merge",
    "derived-regenerate",
    "human-ratification-required",
)

# The Authoritative Harness Destination Catalog (26-RESEARCH.md "Authoritative Harness
# Destination Catalog", all 40 rows verbatim). Row 40's destination is a representative GSD-owned
# path (rather than the research table's prose label) so disposition() can exercise it directly
# via is_gsd_owned() like every other row.
_CATALOG: tuple[dict, ...] = (
    {
        "num": 1,
        "destination": "contracts/harness/adoption/inventory.schema.json",
        "plane": "constitution",
        "marker_capable": False,
    },
    {
        "num": 2,
        "destination": "contracts/.hashes/manifest.json",
        "plane": "constitution",
        "marker_capable": False,
    },
    {
        "num": 3,
        "destination": "contracts/README.md",
        "plane": "constitution",
        "marker_capable": False,
    },
    {
        "num": 4,
        "destination": "golden/widget/verified/case.txt",
        "plane": "constitution",
        "marker_capable": False,
    },
    {
        "num": 5,
        "destination": "docs/adr/0001-decision.md",
        "plane": "constitution",
        "marker_capable": False,
    },
    {
        "num": 6,
        "destination": "docs/tutorials/getting-started.md",
        "plane": "docs",
        "marker_capable": False,
    },
    {
        "num": 7,
        "destination": "docs/how-to/add-a-contract.md",
        "plane": "docs",
        "marker_capable": False,
    },
    {
        "num": 8,
        "destination": "docs/reference/inventory.md",
        "plane": "derived",
        "marker_capable": False,
    },
    {
        "num": 9,
        "destination": "docs/explanation/architecture.md",
        "plane": "docs",
        "marker_capable": False,
    },
    {"num": 10, "destination": "docs/glossary.md", "plane": "docs", "marker_capable": False},
    {
        "num": 11,
        "destination": ".memory/state/activeContext.md",
        "plane": "derived",
        "marker_capable": False,
    },
    {
        "num": 12,
        "destination": ".memory/derived/contracts-index.md",
        "plane": "derived",
        "marker_capable": False,
    },
    {
        "num": 13,
        "destination": ".memory/derived/repo-map.md",
        "plane": "derived",
        "marker_capable": False,
    },
    {
        "num": 14,
        "destination": ".memory/agreements/0001-widget.md",
        "plane": "memory",
        "marker_capable": False,
    },
    {"num": 15, "destination": ".memory/README.md", "plane": "memory", "marker_capable": False},
    {"num": 16, "destination": "harness/project.toml", "plane": "config", "marker_capable": False},
    {"num": 17, "destination": "workspace.toml", "plane": "config", "marker_capable": False},
    {
        "num": 18,
        "destination": "harness/permission-matrix.json",
        "plane": "config",
        "marker_capable": False,
    },
    {
        "num": 19,
        "destination": "harness/risk-policy.toml",
        "plane": "config",
        "marker_capable": False,
    },
    {"num": 20, "destination": "harness/opencode.json", "plane": "config", "marker_capable": False},
    {
        "num": 21,
        "destination": "harness/agents/widget-engineer.md",
        "plane": "source",
        "marker_capable": False,
    },
    {
        "num": 22,
        "destination": "harness/commands/widget-check.md",
        "plane": "source",
        "marker_capable": False,
    },
    {
        "num": 23,
        "destination": "harness/skills/widget-conventions/SKILL.md",
        "plane": "source",
        "marker_capable": False,
    },
    {
        "num": 24,
        "destination": "harness/plugins/format-on-write.ts",
        "plane": "source",
        "marker_capable": False,
    },
    {
        "num": 25,
        "destination": "harness/git-hooks/pre-commit",
        "plane": "source",
        "marker_capable": False,
    },
    {
        "num": 26,
        "destination": ".opencode/agent/widget-engineer.md",
        "plane": "emitted",
        "marker_capable": False,
    },
    {
        "num": 27,
        "destination": ".claude/agents/widget-engineer.md",
        "plane": "emitted",
        "marker_capable": False,
    },
    {"num": 28, "destination": "opencode.json", "plane": "emitted", "marker_capable": False},
    {"num": 29, "destination": ".claude/settings.json", "plane": "shared", "marker_capable": True},
    {"num": 30, "destination": "AGENTS.md", "plane": "shared", "marker_capable": True},
    {"num": 31, "destination": "CLAUDE.md", "plane": "shared", "marker_capable": True},
    {"num": 32, "destination": "libs/python/AGENTS.md", "plane": "docs", "marker_capable": False},
    {"num": 33, "destination": ".github/CODEOWNERS", "plane": "config", "marker_capable": False},
    {
        "num": 34,
        "destination": ".github/workflows/ci.yml",
        "plane": "config",
        "marker_capable": False,
    },
    {
        "num": 35,
        "destination": ".workflow/tasks/T-0001/task.json",
        "plane": "task",
        "marker_capable": False,
    },
    {"num": 36, "destination": "pyproject.toml", "plane": "config", "marker_capable": False},
    {
        "num": 37,
        "destination": "tools/widget_tool/pyproject.toml",
        "plane": "config",
        "marker_capable": False,
    },
    {
        "num": 38,
        "destination": "libs/normalize-spec.md",
        "plane": "constitution-adjacent",
        "marker_capable": False,
    },
    {"num": 39, "destination": ".gitignore", "plane": "config", "marker_capable": False},
    {
        "num": 40,
        "destination": ".claude/get-shit-done/README.md",
        "plane": "excluded",
        "marker_capable": False,
    },
)


def destination_catalog() -> list[dict]:
    """Return all 40 catalog rows (``{"num", "destination", "plane", "marker_capable"}``),
    verbatim from 26-RESEARCH.md's Authoritative Harness Destination Catalog. Row 40 is present
    for documentation purposes but is EXCLUDED from disposition resolution (see :func:`disposition`).
    """
    return [dict(row) for row in _CATALOG]


def _existing_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def disposition(rel: str, target_root: Path, proposed_sha: str | None) -> str | None:
    """The total, ordered 7-step disposition rule chain (D-03/D-04).

    1. ``is_gsd_owned(rel)``                              -> ``None`` (excluded, not a destination)
    2. constitution-plane (``CONSTITUTION_GLOBS`` deny, or the ``libs/normalize-spec.md`` special
       case) -> ``human-ratification-required`` — wins over everything, including hash-equal.
    3. ``DERIVED_GLOBS`` deny                              -> ``derived-regenerate``
    4. ``rel in MARKER_CAPABLE``                           -> ``marker-merge``
    5. no existing file at ``target_root / rel``           -> ``create``
    6. ``sha256(existing) == proposed_sha``                -> ``preserve``
    7. otherwise                                           -> ``conflict``
    """
    if is_gsd_owned(rel):
        return None
    if resolve_path(CONSTITUTION_GLOBS, rel) == "deny" or rel == "libs/normalize-spec.md":
        return "human-ratification-required"
    if resolve_path(DERIVED_GLOBS, rel) == "deny":
        return "derived-regenerate"
    if rel in MARKER_CAPABLE:
        return "marker-merge"

    existing = Path(target_root) / rel
    if not existing.exists():
        return "create"
    if _existing_hash(existing) == proposed_sha:
        return "preserve"
    return "conflict"


def build_manifest(inventory: dict, target_root: Path, proposed_hashes: dict[str, str]) -> dict:
    """Assemble the ``manifest.schema.json``-conformant document over the 40-row catalog.

    ``proposed_hashes`` maps a catalog destination -> proposed sha256 (typically derived from
    ``inventory["included"]``); a destination with no entry passes ``proposed_sha=None`` (safe —
    step 6 never fires when there is no existing file at that destination, per step 5).
    """
    dispositions: list[dict] = []
    excluded: list[dict] = []

    for row in destination_catalog():
        destination = row["destination"]
        result = disposition(destination, target_root, proposed_hashes.get(destination))
        if result is None:
            excluded.append({"destination": destination, "reason": "gsd-owned"})
            continue
        dispositions.append({"destination": destination, "disposition": result})

    dispositions.sort(key=lambda entry: entry["destination"])
    excluded.sort(key=lambda entry: entry["destination"])

    return {
        "target_ref": inventory["target_ref"],
        "dispositions": dispositions,
        "excluded": excluded,
    }
