"""scan.py — confined, read-only, deterministic enumeration + exclusion classification + hashing.

The reuse-at-function-level core recommended by D-07 (26-RESEARCH.md): assembled from four
existing repo primitives, never a fresh scanning engine and never built on any primitive that
executes subprocesses or mutates task state — both are forbidden here (see the plan's own
must_haves.truths), which is what keeps this module read-only and deterministic.

1. Confined + symlink-guarded walk idiom — copied from ``tools/memory_regen/repo_map.py`` (the
   ``root_resolved not in resolved.parents`` containment check), never re-derived.
2. Secret pattern set — owned locally as the ``SECRET_CONTENT_PATTERNS`` module-level tuple,
   byte-identical to the Phase-42 task-control registry contract's ``secret_patterns``
   array at the time it was inlined — that contract was deleted in Phase 44 (CER-08), which this
   module is unaffected by (no filesystem read at scan time; see ``SECRET_PATH_GLOBS``
   for the same "own the constant locally" idiom this module already used for secret-path globs).
3. Last-wins glob resolution — ``tools.harness_perms.resolve_path`` for the secret-path check
   (this module's OWN ``SECRET_PATH_GLOBS`` constant — not the hook-specific
   ``tools.hooks.secret_scan.SECRET_PATH_GLOBS``, since ``scan.py`` is not a hook).
4. ``hashlib.sha256`` for raw file bytes — never RFC-8785 (that is JSON schema canonicalization
   only, see ``tools.contract_hash``).

``enumerate_target()`` prefers ``git -C <target> ls-files -z --cached --others --exclude-standard``
(fixed argv, ``shell=False``, D-09) and falls back to a confined builtin walk on any failure —
never raising, always self-describing via the returned ``mode``.

``classify_exclusions()`` decides, in path-first order (never opening a file to decide by path
alone; ``stat()`` always runs before ``open()``): symlink-escape confinement guard -> vendored
segment -> generated segment -> size cap (source-dump vs size-capped) -> binary (NUL/decode) ->
generated content marker -> secret-path glob -> source-dump banner marker -> secret-content
pattern. Every exclusion is *recorded* as ``{path, size, excluded}`` — D-10: never a content hash,
never an excerpt, so a secret-flagged file's matched bytes can never leak into the artifact.

``build_inventory()`` is pure and injectable (``_paths``) so a seeded-shuffled enumeration order
proves inventory-level output is byte-identical regardless of filesystem walk order (D-06).
"""

from __future__ import annotations

import functools
import hashlib
import json
import re
import subprocess
from pathlib import Path

from tools.adoption_scan import detect
from tools.harness_perms import resolve_path

# scan.py -> adoption_scan -> tools -> repo root (parents[2]).
_REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_MAX_FILE_BYTES = 256 * 1024

# This plan's OWN secret-path glob constant (T-26-02 threat model) — deliberately NOT imported
# from tools.hooks.secret_scan.SECRET_PATH_GLOBS, which is hook-specific.
SECRET_PATH_GLOBS = ["*.env", "**/*.env", "*.pem", "*.key", "id_rsa*", ".npmrc", ".netrc"]

# This module's OWN secret-content pattern tuple (D-04/D-05, Phase 42 Plan 03) — inlined
# byte-identical from the Phase-42 task-control registry contract's "secret_patterns"
# array, which Phase 44 (CER-08) deleted. No filesystem read at scan time; follows the same
# "own the constant locally" idiom as SECRET_PATH_GLOBS above.
SECRET_CONTENT_PATTERNS: tuple[str, ...] = (
    "AKIA[0-9A-Z]{16}",
    "(?:api[_-]?key|secret|password|token)\\s*[:=]\\s*(?:(?=[^\\s]*(?-i:[A-Z]))(?=[^\\s]*(?-i:[a-z]))"
    "|(?=[^\\s]*(?-i:[A-Z]))(?=[^\\s]*[0-9])|(?=[^\\s]*(?-i:[a-z]))(?=[^\\s]*[0-9]))[^\\s]{20,}",
    "(?:ghp_|gho_|ghu_|ghs_|github_pat_)[A-Za-z0-9_-]+",
    "sk-[A-Za-z0-9_-]{16,}",
    "xox[bp]-[A-Za-z0-9-]+",
    "-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "eyJ[A-Za-z0-9_-]{10,}\\.[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+",
    "Authorization:\\s*Bearer\\s+[^\\s]+",
)

# Path-segment denylists (exact segment match, never substring).
_VENDOR_SEGMENTS = {
    "node_modules",
    "vendor",
    "third_party",
    ".venv",
    "venv",
    "site-packages",
    "__pycache__",
}
_GENERATED_SEGMENTS = {
    "dist",
    "build",
    "bin",
    "obj",
    "target",
    "out",
    ".pytest_cache",
    ".ruff_cache",
}

# Content markers (case-insensitive, bounded to the first 2 KiB of a text-decodable prefix).
# Deliberately NARROW: does not include the harness's own "do not hand-edit" marker text — that
# text lives inside root AGENTS.md/CLAUDE.md's BEGIN/END HARNESS-MANAGED comment, a marker-capable
# surface that must stay INCLUDED (never misclassified as "generated") for Plan 03 to consume.
#
# WR-02 (26-REVIEW.md): "derived —" alone (just the common word "derived" followed by an em-dash)
# is NOT anchored to this repo's own generator convention and false-positives on ordinary prose
# that happens to use the same phrasing (e.g. this repo's own
# ".opencode/skill/two-plane-memory/SKILL.md" reads "Gitignored-derived — `.memory/derived/...`").
# Every actual committed-derived generator in this repo emits the SAME literal continuation —
# `DERIVED_HEADER = "DERIVED — do not hand-edit ..."` (tools/docs_sync/generate.py,
# tools/memory_regen/{pointer_index,repo_map,contracts_index}.py) — so the marker is anchored to
# that continuation instead of the bare word, closing the false-positive without weakening
# detection of any real generated file in this repo's own convention.
_GENERATED_MARKERS = ("@generated", "auto-generated", "derived — do not")

# Repomix/gitingest/LLM-input concatenation-dump banner markers (D-08 reading (a)).
_SOURCE_DUMP_BANNER_MARKERS = (
    "generated by repomix",
    "this file is a merged representation",
    "==== repository structure",
)

# Path-segment tokens for D-08 reading (b): over-cap PLUS a dump/snapshot/backup segment.
_SOURCE_DUMP_SEGMENT_TOKENS = ("dump", "snapshot", "backup")

_BINARY_SCAN_BYTES = 8192
_MARKER_SCAN_BYTES = 2048
_CONTENT_PREFIX_BYTES = 64 * 1024


@functools.lru_cache(maxsize=1)
def _secret_pattern() -> re.Pattern[str]:
    """Compile the locally-owned ``SECRET_CONTENT_PATTERNS`` tuple (never retyped elsewhere)."""
    return re.compile("(?:" + "|".join(SECRET_CONTENT_PATTERNS) + ")", re.IGNORECASE)


def _confined(path: Path, base_resolved: Path) -> bool:
    """True if ``path`` resolves inside ``base_resolved`` (the repo_map.py containment idiom)."""
    try:
        resolved = path.resolve()
    except OSError:
        return False
    return base_resolved == resolved or base_resolved in resolved.parents


def enumerate_target(target: Path, *, _force_builtin: bool = False) -> tuple[list[Path], str]:
    """Enumerate candidate files under ``target``.

    Returns ``(paths, mode)`` where ``mode`` is ``"git"`` when
    ``git -C <target> ls-files -z --cached --others --exclude-standard`` exits 0, else
    ``"builtin"``. A non-git target or any git failure (``OSError``, non-zero exit, decode error)
    falls back to a full builtin denylist-capable walk — never raises.
    """
    target = Path(target).resolve()
    if not _force_builtin:
        argv = [
            "git",
            "-C",
            str(target),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ]
        try:
            proc = subprocess.run(argv, capture_output=True, check=False, shell=False)
        except OSError:
            proc = None
        if proc is not None and proc.returncode == 0:
            try:
                names = [
                    name
                    for name in proc.stdout.decode("utf-8", "surrogateescape").split("\0")
                    if name
                ]
            except UnicodeDecodeError:
                names = None
            if names is not None:
                return sorted(target / name for name in names), "git"
    return _builtin_walk(target), "builtin"


def _builtin_walk(target: Path) -> list[Path]:
    """Confined denylist-capable walk: every file AND every symlink (including escaping ones, so
    an escape can be recorded rather than silently vanish), sorted, real directories skipped."""
    candidates: list[Path] = []
    for p in sorted(target.rglob("*")):
        if p.is_symlink() or p.is_file():
            candidates.append(p)
    return candidates


def _file_hash(path: Path) -> str:
    """sha256 hex of the full file bytes (chunked read) — never RFC-8785 (that hashes JSON)."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dump(document: dict) -> bytes:
    """The ONE canonical serialization for adoption artifacts (Plan 03 reuses this, never
    redefines it): sort_keys + indent=2 + ensure_ascii + trailing LF, UTF-8 encoded."""
    return (json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode(
        "utf-8"
    )


def classify_exclusions(path: Path, *, base: Path, max_bytes: int) -> dict | None:
    """Classify ``path`` (relative to ``base``) as excluded (dict) or included (``None``).

    Path-first order (see module docstring); ``stat()`` always runs before ``open()`` so the size
    cap is a real bound. Every exclusion is ``{path, size, excluded}`` — no content hash, no
    content excerpt (D-10).
    """
    base_resolved = Path(base).resolve()
    rel = path.relative_to(base).as_posix()
    parts = path.relative_to(base).parts

    # 0. Confinement / symlink-escape guard — checked FIRST, never followed, never stat()'d via
    #    the link target (lstat only, so an escaping link's OWN metadata is all that is read).
    if path.is_symlink() and not _confined(path, base_resolved):
        try:
            size = path.lstat().st_size
        except OSError:
            size = 0
        return {"path": rel, "size": size, "excluded": "symlink-escape"}

    # 1. Vendored segment (path-only, no open()).
    if any(seg in _VENDOR_SEGMENTS for seg in parts):
        size = path.stat().st_size
        return {"path": rel, "size": size, "excluded": "vendored"}

    # 2. Generated segment (path-only, no open()).
    if any(seg in _GENERATED_SEGMENTS for seg in parts):
        size = path.stat().st_size
        return {"path": rel, "size": size, "excluded": "generated"}

    # 3. Size cap — checked BEFORE any open(). Distinguishes D-08 reading (b) (over-cap + a
    #    dump/snapshot/backup path segment -> source-dump) from a plain over-cap file
    #    (size-capped).
    size = path.stat().st_size
    if size > max_bytes:
        lowered = [seg.lower() for seg in parts]
        if any(token in seg for seg in lowered for token in _SOURCE_DUMP_SEGMENT_TOKENS):
            return {"path": rel, "size": size, "excluded": "source-dump"}
        return {"path": rel, "size": size, "excluded": "size-capped"}

    # Everything below reads a single bounded prefix (never the whole file, never more than
    # _CONTENT_PREFIX_BYTES) and reuses it for every remaining content-based check.
    try:
        with path.open("rb") as handle:
            prefix = handle.read(_CONTENT_PREFIX_BYTES)
    except OSError:
        return {"path": rel, "size": size, "excluded": "binary"}

    # 4. Binary: NUL in the first 8192 bytes, or the prefix fails to decode as UTF-8.
    if b"\x00" in prefix[:_BINARY_SCAN_BYTES]:
        return {"path": rel, "size": size, "excluded": "binary"}
    try:
        text_prefix = prefix.decode("utf-8")
    except UnicodeDecodeError:
        return {"path": rel, "size": size, "excluded": "binary"}

    head = text_prefix[:_MARKER_SCAN_BYTES].lower()

    # 5. Generated content marker (narrow set — never the harness's own "do not hand-edit" text).
    if any(marker in head for marker in _GENERATED_MARKERS):
        return {"path": rel, "size": size, "excluded": "generated"}

    # 6. Secret-path glob (this module's own SECRET_PATH_GLOBS, resolved via the repo's ONE
    #    last-wins glob resolver).
    if resolve_path(SECRET_PATH_GLOBS, rel) == "deny":
        return {"path": rel, "size": size, "excluded": "secret-path"}

    # 7. Source-dump banner marker — D-08 reading (a): a small under-cap concatenation-dump file
    #    identified purely by its first-2KiB banner, independent of any path segment.
    if any(marker in head for marker in _SOURCE_DUMP_BANNER_MARKERS):
        return {"path": rel, "size": size, "excluded": "source-dump"}

    # 8. Secret-content pattern match against the bounded prefix — never echoed into the record.
    if _secret_pattern().search(text_prefix):
        return {"path": rel, "size": size, "excluded": "secret-content"}

    return None


def _target_ref(target: Path) -> str:
    """The scanned target's current git commit hex, or the literal ``"unknown"`` on any failure —
    a fact about the INPUT, never a clock (no-timestamp determinism rule)."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(target), "rev-parse", "HEAD"],
            capture_output=True,
            check=False,
            shell=False,
        )
    except OSError:
        return "unknown"
    if proc.returncode != 0:
        return "unknown"
    try:
        ref = proc.stdout.decode("utf-8").strip()
    except UnicodeDecodeError:
        return "unknown"
    return ref or "unknown"


def build_inventory(
    target: Path,
    *,
    max_bytes: int = DEFAULT_MAX_FILE_BYTES,
    _paths: list[Path] | None = None,
) -> dict:
    """Pure, injectable inventory builder — the ADOPT-01 artifact shape.

    When ``_paths`` is supplied (a pre-computed, possibly-shuffled candidate list) it is used
    verbatim for classification instead of a fresh :func:`enumerate_target` walk — this is what
    makes the seeded-shuffle determinism proof possible. ``enumeration_mode`` still reflects the
    target's own real enumeration capability (a property of the target/environment, not of the
    particular candidate ordering), so the shuffled and unshuffled runs stay byte-comparable.
    """
    target = Path(target).resolve()
    computed_paths, mode = enumerate_target(target)
    paths = list(_paths) if _paths is not None else computed_paths

    included: list[dict] = []
    excluded: list[dict] = []
    for candidate in paths:
        exclusion = classify_exclusions(candidate, base=target, max_bytes=max_bytes)
        if exclusion is not None:
            excluded.append(exclusion)
            continue
        rel = candidate.relative_to(target).as_posix()
        included.append(
            {
                "path": rel,
                "size": candidate.stat().st_size,
                "sha256": _file_hash(candidate),
            }
        )

    included.sort(key=lambda entry: entry["path"])
    excluded.sort(key=lambda entry: entry["path"])

    return {
        "target_ref": _target_ref(target),
        "enumeration_mode": mode,
        "max_file_bytes": max_bytes,
        "included": included,
        "excluded": excluded,
        "languages": detect.detect_languages(included),
        "manifests": detect.detect_manifests(included),
        "documentation_surfaces": detect.detect_documentation_surfaces(included),
        "ci_surfaces": detect.detect_ci_surfaces(included),
        "test_surfaces": detect.detect_test_surfaces(included),
        "candidate_process_boundaries": detect.detect_candidate_process_boundaries(included),
        "schema_surfaces": detect.detect_schema_surfaces(included),
        "codeowners_surfaces": detect.detect_codeowners_surfaces(included),
    }
