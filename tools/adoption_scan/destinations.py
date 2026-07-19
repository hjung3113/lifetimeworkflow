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

CR-01 fix (26-REVIEW.md): steps 6/7 of the disposition chain compare the TARGET's existing content
against ``proposed_sha`` — content the HARNESS TEMPLATE would install at that destination. That
must never be derived from the scanned target itself (comparing a file to itself makes ``conflict``
unreachable). :func:`harness_proposed_hash`/:func:`harness_proposed_hashes` hash THIS repo's own
checkout — the harness template source — at each catalog destination's relative path, independent
of any scanned target. A catalog row whose destination has no file in this checkout (a placeholder
row standing in for target-specific content with no universal template, e.g.
``harness/agents/widget-engineer.md``, or a per-instance file such as
``.workflow/tasks/T-0001/task.json``) yields ``proposed_sha=None``; step 6 can then never fire for
it (``None`` never equals a real sha256 hex digest), so an existing target file at that destination
always resolves to ``conflict`` — never a silently-invented ``preserve``. This is the honest,
D-03-consistent ("no automatic overwrite, ever") answer for the no-template-source case.

WR-03 fix (26-REVIEW.md): :func:`disposition`'s existing-file hash (step 6/7) no longer
unconditionally re-reads the target file via :func:`_existing_hash`. :func:`build_manifest` passes
an ``existing_sha`` hint sourced from the inventory that ``scan.py`` already produced for the same
target: the already-computed ``sha256`` when the destination was ``included`` (no double I/O, no
cap/binary-check bypass), or a sentinel that can never match any real sha256 when the destination
was ``excluded`` (binary/oversized/secret/etc. — never re-read a file the scanner already refused
to hash, which forces the safe ``conflict`` outcome without opening it). :func:`_existing_hash` is
only invoked as a fallback when a destination path was not part of the scanned inventory at all —
which, given a correctly-wired pipeline, should be rare-to-never — and it remains available for
:func:`harness_proposed_hash`, which reads bounded, self-controlled harness-repo files, not
arbitrary target content.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from tools.harness_emit.manifest import is_gsd_owned
from tools.harness_perms import resolve_path
from tools.hooks.contract_guard import CONSTITUTION_GLOBS  # noqa: F401 (re-exported for callers)

# destinations.py -> adoption_scan -> tools -> repo root (parents[2]) — the harness TEMPLATE's own
# checkout, i.e. the source of "proposed" content (CR-01). Mirrors cli.py/scan.py's own _REPO_ROOT.
_REPO_ROOT = Path(__file__).resolve().parents[2]

# WR-03: a sentinel that can never equal a real sha256 hex digest (which is always exactly 64
# lowercase hex chars) — used to force `conflict` for a destination the scanner already classified
# as `excluded`, without re-reading it.
_EXCLUDED_SENTINEL = "excluded-by-scan"

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
    for documentation purposes but is EXCLUDED from disposition resolution (see
    :func:`disposition`).
    """
    return [dict(row) for row in _CATALOG]


def _existing_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def harness_proposed_hash(destination: str) -> str | None:
    """CR-01: the sha256 of THIS harness checkout's own content at ``destination`` — the content
    the harness template would install there — independent of any scanned target.

    Returns ``None`` when this checkout has no file at that path: either a catalog placeholder row
    standing in for target-specific content with no single universal template (e.g.
    ``harness/agents/widget-engineer.md``), or a genuinely per-instance/per-target file (e.g.
    ``.workflow/tasks/T-0001/task.json``). ``None`` deliberately can never equal a real sha256, so
    :func:`disposition` step 6 never fires for such a row — an existing target file there resolves
    to ``conflict`` (human decides), never a silently-invented ``preserve``.
    """
    candidate = _REPO_ROOT / destination
    if not candidate.is_file():
        return None
    resolved = candidate.resolve()
    if resolved != _REPO_ROOT and _REPO_ROOT not in resolved.parents:
        return None
    return _existing_hash(resolved)


def harness_proposed_hashes() -> dict[str, str]:
    """CR-01: ``{destination: proposed_sha256}`` over every catalog row that has real content in
    this harness checkout. Rows with no shippable template content are simply absent — see
    :func:`harness_proposed_hash`."""
    hashes: dict[str, str] = {}
    for row in destination_catalog():
        destination = row["destination"]
        proposed = harness_proposed_hash(destination)
        if proposed is not None:
            hashes[destination] = proposed
    return hashes


def disposition(
    rel: str,
    target_root: Path,
    proposed_sha: str | None,
    *,
    existing_sha: str | None = None,
) -> str | None:
    """The total, ordered 7-step disposition rule chain (D-03/D-04).

    1. ``is_gsd_owned(rel)``                              -> ``None`` (excluded, not a destination)
    2. constitution-plane (``CONSTITUTION_GLOBS`` deny, or the ``libs/normalize-spec.md`` special
       case) -> ``human-ratification-required`` — wins over everything, including hash-equal.
    3. ``DERIVED_GLOBS`` deny                              -> ``derived-regenerate``
    4. ``rel in MARKER_CAPABLE``                           -> ``marker-merge``
    5. no existing file at ``target_root / rel``           -> ``create``
    6. ``sha256(existing) == proposed_sha``                -> ``preserve``
    7. otherwise                                           -> ``conflict``

    ``existing_sha`` (WR-03) is an optional caller-supplied hash for the existing target file at
    ``rel``, reused instead of a fresh (cap/binary-check-bypassing) re-read via
    :func:`_existing_hash`. :func:`build_manifest` supplies this from the scan's already-computed
    inventory; a bare call (as in most of this module's own unit tests) falls back to
    :func:`_existing_hash`, preserving prior direct-call behavior.
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
    if existing_sha is None:
        existing_sha = _existing_hash(existing)
    if existing_sha == proposed_sha:
        return "preserve"
    return "conflict"


def build_manifest(inventory: dict, target_root: Path, proposed_hashes: dict[str, str]) -> dict:
    """Assemble the ``manifest.schema.json``-conformant document over the 40-row catalog.

    ``proposed_hashes`` maps a catalog destination -> proposed sha256 — the content the HARNESS
    TEMPLATE would install there (CR-01: :func:`harness_proposed_hashes`), never derived from the
    scanned target itself. A destination with no entry passes ``proposed_sha=None`` to
    :func:`disposition`, which can then never hit ``preserve`` via step 6 (safe).

    WR-03: the existing-file hash used for the step-6/7 comparison is sourced from ``inventory``
    when available — the already-computed ``sha256`` for an ``included`` destination, or the
    :data:`_EXCLUDED_SENTINEL` (never a real hash) for an ``excluded`` one — rather than an
    unconditional re-read of the target file inside :func:`disposition`.
    """
    included_hashes = {entry["path"]: entry["sha256"] for entry in inventory.get("included", [])}
    excluded_paths = {entry["path"] for entry in inventory.get("excluded", [])}

    dispositions: list[dict] = []
    excluded: list[dict] = []

    for row in destination_catalog():
        destination = row["destination"]
        if destination in included_hashes:
            existing_sha = included_hashes[destination]
        elif destination in excluded_paths:
            existing_sha = _EXCLUDED_SENTINEL
        else:
            existing_sha = None
        result = disposition(
            destination,
            target_root,
            proposed_hashes.get(destination),
            existing_sha=existing_sha,
        )
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
