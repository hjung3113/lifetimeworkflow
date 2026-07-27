"""destinations.py — the RULE-DERIVED Authoritative Harness Destination Catalog + the total,
7-step disposition resolution chain (ADOPT-03, D-03/D-04).

``destination_catalog()`` is NOT a fixed-size hand-picked sample. It enumerates every REAL file in
THIS harness checkout (``_REPO_ROOT``) matching one of the named destination categories in
``_CATEGORY_GLOBS``, sorted and deduplicated — so the catalog grows and shrinks with the harness's
actual file tree instead of a curated 40-row guess (26-VERIFICATION.md gap 2). Running it against
this repo yields a catalog row for every real contract schema, ADR, harness command/skill/agent
file, emitted `.opencode`/`.claude` artifact, and nested `AGENTS.md` — never a fixed representative
sample per category, and never one of the confirmed-nonexistent placeholder paths a prior static
sample contained (e.g. ``harness/agents/widget-engineer.md``).

Every non-GSD-owned catalog row resolves to EXACTLY ONE of the 6 `dispositionEnum` values
(``create``/``preserve``/``conflict``/``marker-merge``/``derived-regenerate``/
``human-ratification-required``) — totality, proven by
``tools/adoption_scan/tests/test_dispositions.py::test_total``. A GSD-owned row (``is_gsd_owned``)
is EXCLUDED from disposition resolution, never assigned a disposition (recorded in
``manifest["excluded"]`` instead).

Deliberately excluded from the enumeration: ``.workflow/tasks/**``. 26-CONTEXT.md's own locked
`<domain>` "NOT this phase" line is the authoritative source for this exclusion (quoted verbatim
above ``_CATEGORY_GLOBS`` below) — task-local batches under ``.workflow/tasks/`` are Phase 27's
concern (ADOPT-04..07), not this plan's to enumerate. As corroborating (not authoritative) detail:
task-plane content is session-local, per-run data with no static template, so enumerating it would
make the destination set drift with every GSD session and break the committed snapshot's
reproducibility.

This module NEVER retypes ``CONSTITUTION_GLOBS`` or ``is_gsd_owned`` — both are imported from
their authoritative sources (26-RESEARCH.md "Don't Hand-Roll"):

- ``tools.hooks.contract_guard.CONSTITUTION_GLOBS`` — the CODEOWNERS-gated constitution plane.
- ``tools.harness_emit.manifest.is_gsd_owned`` — the GSD-owned-lane exclusion predicate.

The marker-capable set (D-03) is a plain 3-item literal here, cited against its provenance in
``tools.harness_emit.merge`` (``BEGIN_MARKER``/``END_MARKER`` for root ``AGENTS.md``/``CLAUDE.md``;
``merge_settings`` for ``.claude/settings.json``) — this tool never performs a merge itself
(Phase 27 does), so it only needs to know WHICH 3 paths are marker-capable, not how to merge them.

CR-01 fix (26-VERIFICATION.md gap 1, this plan — 26-07): ``destination_catalog()``'s enumeration
loop calls :func:`_tracked_repo_files` ONCE and skips any candidate whose repo-relative destination
is not git-tracked. Without this filter, a gitignored/untracked file present only on a developer's
working tree (e.g. a regenerated ``.memory/derived/*`` artifact) silently entered the catalog,
making it non-reproducible on a clean checkout (`actions/checkout` in CI has no such file) — the
exact "fully CI-testable" violation 26-VERIFICATION.md gap 1 identified. The filter is
failure-tolerant (git binary missing or the invocation failing both degrade to unfiltered
enumeration, per D-09's "MUST NOT depend on git" rule) rather than raising. This is a DIFFERENT
CR-01 from the one two paragraphs below (that one is about ``harness_proposed_hash``/target-vs-
template independence, from an earlier review round) — both share the CR-01 label because
26-REVIEW.md numbers findings per-round, not globally; do not conflate them.

CR-01 fix (26-REVIEW.md, prior round): steps 6/7 of the disposition chain compare the TARGET's
existing content
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
import subprocess
from pathlib import Path

from tools.adoption_scan import scan
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

# Rule-derived category globs (26-RESEARCH.md "Authoritative Harness Destination Catalog" — same
# categories, glob patterns instead of literal per-category sample rows), relative to _REPO_ROOT,
# passed to Path.glob(). Order matters for dedup (first-match-wins, see destination_catalog()):
# literal single-file patterns (e.g. "AGENTS.md") are listed BEFORE any nested glob that could
# also match them (e.g. "**/AGENTS.md") so the root file's row is produced by the intended entry.
#
# NOT this phase: the /adopt command, the brownfield-adoption skill, task-local batches under
# .workflow/tasks/, apply/marker-merge execution, human ratification checkpoint, the three
# application fixtures — all Phase 27 (ADOPT-04..07). [26-CONTEXT.md <domain> "NOT this phase"
# line, quoted verbatim.] `.workflow/tasks/**` is therefore deliberately OMITTED from
# _CATEGORY_GLOBS below — that scope boundary, not an invented rationale, is why. (Corroborating,
# non-authoritative detail: task-plane content is session-local per-run data with no static
# template, so enumerating it would make the catalog drift with every GSD session and break the
# committed snapshot's reproducibility.) `destination_catalog()` also applies a belt-and-suspenders
# structural skip of any path starting with (".workflow", "tasks") so a future glob addition can
# never silently reintroduce it.
_CATEGORY_GLOBS: tuple[str, ...] = (
    "contracts/**/*",
    "golden/**/*",
    "docs/adr/**/*",
    "docs/tutorials/**/*",
    "docs/how-to/**/*",
    "docs/explanation/**/*",
    "docs/glossary.md",
    "docs/reference/**/*",
    ".memory/state/**/*",
    ".memory/derived/**/*",
    ".memory/agreements/**/*",
    ".memory/README.md",
    "harness/project.toml",
    "workspace.toml",
    "harness/permission-matrix.json",
    "harness/risk-policy.toml",
    "harness/opencode.json",
    "harness/opencode.config.schema.json",
    "harness/agents/**/*",
    "harness/commands/**/*",
    "harness/skills/**/*",
    "harness/plugins/**/*",
    "harness/git-hooks/**/*",
    ".opencode/**/*",
    ".claude/agents/**/*",
    ".claude/commands/**/*",
    ".claude/skills/**/*",
    "opencode.json",
    ".claude/settings.json",
    "AGENTS.md",
    "CLAUDE.md",
    "**/AGENTS.md",
    ".github/CODEOWNERS",
    ".github/workflows/**/*",
    "pyproject.toml",
    "**/pyproject.toml",
    "tools/**/*",
    "libs/normalize-spec.md",
    "libs/normalize-fixtures/**/*",
    ".gitignore",
)

# The path-segment prefix a future glob must never be allowed to reintroduce (26-CONTEXT.md-cited
# exclusion, enforced structurally, independent of _CATEGORY_GLOBS' contents).
_EXCLUDED_PREFIX: tuple[str, str] = (".workflow", "tasks")

# GEN-04 core->instance independence: this catalog must never cross into the domain instance tree
# nested under this checkout's top-level instance directory (a moved-asset AGENTS.md/pyproject.toml
# there is legitimately matched by the "**/AGENTS.md"/"**/pyproject.toml" nested globs above, but
# core planes must not depend on or enumerate instance content). Named as a bare directory segment
# (no path separator) so this module never carries the GEN-04-forbidden contiguous path-token
# substring itself.
_INSTANCE_DIR_NAME = "examples"

# WR-02 (26-REVIEW.md): belt-and-suspenders reuse of scan.py's own vendor/generated path-segment
# denylists (never re-derived) — a second layer of defense for the git-unavailable fallback path,
# where _tracked_repo_files() cannot filter and an untracked vendor/build directory could otherwise
# slip into the catalog.
#
# 42-REVIEW.md Fix 1: also skips any "tests" path segment. This is what keeps the "tools/**/*" row
# (added by this same phase so an adopted target receives the Python its emitted commands invoke)
# from also shipping dev-only test suites, `__snapshots__` fixtures, and the fixture mini-repos
# under tools/adoption_apply/tests/fixtures/** — the latter deliberately embed secret-shaped
# literals (AKIA…, PEM headers, ghp_…) as red-check inputs for the secret scanner, which must never
# ride into a stranger's repo. No other _CATEGORY_GLOBS row currently matches a path with a "tests"
# segment (verified: only `libs/python/normalize/tests/**`, which is not catalogued at all), so
# this is a no-op for every category besides `tools/**/*`.
_SKIP_SEGMENTS: frozenset[str] = (
    frozenset(scan._VENDOR_SEGMENTS) | frozenset(scan._GENERATED_SEGMENTS) | frozenset({"tests"})
)


def _tracked_repo_files() -> frozenset[str] | None:
    """CR-01: the set of repo-relative, POSIX-style paths ``git`` considers tracked at
    ``_REPO_ROOT``, or ``None`` when git is unavailable/fails (D-09 — this function MUST NOT make
    the catalog depend on git; ``None`` signals the caller to fall back to unfiltered enumeration).

    Failure-tolerant by design (unlike ``tools/harness_lint/tests/test_core_no_example_dep.py``'s
    ``_tracked_core_files()``, which this mirrors and is allowed to hard-fail for its own guard
    purpose): catches ``OSError`` (git binary missing) and inspects ``returncode`` explicitly
    (``check=False``) rather than raising on a non-zero exit.
    """
    try:
        completed = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "ls-files"],
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return frozenset(completed.stdout.decode("utf-8", "surrogateescape").splitlines())


def destination_catalog() -> list[dict]:
    """Rule-derived enumeration of every real, git-tracked file in this checkout matching a named
    ADOPT-03 destination category, sorted and deduplicated by destination.

    For each pattern in :data:`_CATEGORY_GLOBS`, resolves ``sorted(_REPO_ROOT.glob(pattern))``,
    keeps only real files, applies the repo's confined-walk idiom (defense in depth even though the
    source is this checkout, not an external target), and derives ``destination`` from the
    ENUMERATED ``candidate`` path (``candidate.relative_to(_REPO_ROOT)``), never from ``resolved``
    (WR-04 — ``resolved`` is used ONLY for the containment check; deriving identity from it would
    collapse two distinct symlinks pointing at the same target into one deduplicated row). Skips a
    candidate whose parts start with :data:`_EXCLUDED_PREFIX`, whose first part is
    :data:`_INSTANCE_DIR_NAME`, whose parts intersect :data:`_SKIP_SEGMENTS` (WR-02), or — the CR-01
    fix this plan (26-07) adds — whose destination is not git-tracked (per
    :func:`_tracked_repo_files`, called ONCE up front and reused across the whole loop for both
    determinism and performance; when git is unavailable, the filter is a no-op and enumeration
    falls back to unfiltered, per D-09). Deduplicates across overlapping glob patterns keyed by the
    destination string in ``_CATEGORY_GLOBS`` iteration order (first match wins). Each row is
    ``{"destination": <repo-relative POSIX str>}`` — the old ``num``/``plane``/``marker_capable``
    keys are gone; they were never consumed by :func:`disposition`/:func:`build_manifest`
    (``MARKER_CAPABLE``/``DERIVED_GLOBS``/``CONSTITUTION_GLOBS`` already carry the equivalent
    classification at call time). Returns the deduplicated rows sorted by destination.
    """
    root_resolved = _REPO_ROOT.resolve()
    tracked = _tracked_repo_files()
    rows: dict[str, dict] = {}

    for pattern in _CATEGORY_GLOBS:
        for candidate in sorted(_REPO_ROOT.glob(pattern)):
            if not candidate.is_file():
                continue
            resolved = candidate.resolve()
            if root_resolved != resolved and root_resolved not in resolved.parents:
                continue
            destination = candidate.relative_to(_REPO_ROOT).as_posix()
            parts = destination.split("/")
            if tuple(parts[: len(_EXCLUDED_PREFIX)]) == _EXCLUDED_PREFIX:
                continue
            if parts[0] == _INSTANCE_DIR_NAME:
                continue
            if any(seg in _SKIP_SEGMENTS for seg in parts):
                continue
            if tracked is not None and destination not in tracked:
                continue
            if destination not in rows:
                rows[destination] = {"destination": destination}

    return [rows[key] for key in sorted(rows)]


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


def build_manifest(
    inventory: dict,
    target_root: Path,
    proposed_hashes: dict[str, str],
    *,
    catalog: list[dict] | None = None,
) -> dict:
    """Assemble the ``manifest.schema.json``-conformant document over the destination catalog.

    ``proposed_hashes`` maps a catalog destination -> proposed sha256 — the content the HARNESS
    TEMPLATE would install there (CR-01: :func:`harness_proposed_hashes`), never derived from the
    scanned target itself. A destination with no entry passes ``proposed_sha=None`` to
    :func:`disposition`, which can then never hit ``preserve`` via step 6 (safe).

    ``catalog`` (CR-02, 26-VERIFICATION.md gap 1): when ``None`` (every existing caller —
    ``cli.py``, this module's own live-catalog tests), the live :func:`destination_catalog` is used,
    unchanged. When provided (a ``list[dict]`` of ``{"destination": str}`` rows, the same shape
    :func:`destination_catalog` returns), that fixed list is iterated instead — decoupling a
    committed manifest snapshot from the live repo's file count, so an unrelated harness file
    add/remove never reds a snapshot test built over an explicit fixed catalog.

    WR-03: the existing-file hash used for the step-6/7 comparison is sourced from ``inventory``
    when available — the already-computed ``sha256`` for an ``included`` destination, or the
    :data:`_EXCLUDED_SENTINEL` (never a real hash) for an ``excluded`` one — rather than an
    unconditional re-read of the target file inside :func:`disposition`.
    """
    included_hashes = {entry["path"]: entry["sha256"] for entry in inventory.get("included", [])}
    excluded_paths = {entry["path"] for entry in inventory.get("excluded", [])}

    dispositions: list[dict] = []
    excluded: list[dict] = []

    for row in catalog if catalog is not None else destination_catalog():
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
