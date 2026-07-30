"""package-facts generator — derive a committed package + dependency graph (MONO-01/MONO-02,
MONO-05/MONO-06).

Enumerates every git-tracked manifest this checkout recognizes (via
:func:`tools.adoption_scan.detect.detect_manifests`), excludes anything under a
``tests/fixtures`` path segment, then resolves each manifest's declared dependencies (via
:func:`tools.adoption_scan.detect.detect_dependencies`) to OTHER known packages in this same
checkout. An unresolvable dependency (external, or excluded from the scan) is dropped, never
fabricated as an edge. Neither manifest recognition nor dependency parsing is re-implemented
here — both are reused verbatim from ``tools.adoption_scan.detect``.

Enumeration is a light ``git ls-files`` walk, not ``tools.adoption_scan.scan.build_inventory`` —
this generator needs only a manifest's path (to detect its kind) and its content (to parse
declared dependencies), never the hashing/secret-classification machinery that inventory
building performs for every tracked file.

Output: ``.memory/derived/package-facts.md`` — committed-derived (like
``.memory/derived/contracts-index.md``, re-included through ``.gitignore``'s contents-form
glob), NOT gitignored. No timestamp, no raw float: delete + regenerate reproduces the file
byte-for-byte.

Entrypoint: ``python -m tools.memory_regen.package_facts``.
"""

from __future__ import annotations

import json
import posixpath
import re
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

from tools.adoption_scan import detect

# WR-03 (47-REVIEW.md): exceptions raised by the per-kind manifest parsers this module and
# detect.py feed (encoding failures included) — caught per-manifest so one malformed file
# degrades gracefully instead of aborting the whole regeneration run.
_MANIFEST_PARSE_ERRORS = (
    UnicodeDecodeError,
    tomllib.TOMLDecodeError,
    json.JSONDecodeError,
    ET.ParseError,
)

# --- paths (derived plane; this artifact is committed-derived, not gitignored) -----------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
DERIVED_DIR = _REPO_ROOT / ".memory" / "derived"
PACKAGE_FACTS_PATH = DERIVED_DIR / "package-facts.md"

# --- stable text (part of the derived-plane contract) -------------------------------------------
DERIVED_HEADER = "DERIVED — do not hand-edit (tools/memory_regen/package_facts.py)"

# Manifest kind -> language slug, reusing detect.py's own kind vocabulary. `package.json` has no
# language signal in this checkout's one instance (`.claude/package.json` is `{"type":
# "commonjs"}`) — `javascript` is the deliberate default (see 47-CONTEXT.md A3).
_KIND_LANGUAGE: dict[str, str] = {
    "pyproject.toml": "python",
    "package.json": "javascript",
    "*.csproj": "csharp",
    "go.mod": "go",
    "Cargo.toml": "rust",
}

_GO_MODULE_DIRECTIVE = re.compile(r"(?m)^module\s+(\S+)")

_PEP503_SEPARATORS = re.compile(r"[-_.]+")


def _normalize_pep503(name: str) -> str:
    """PEP 503 "Normalized Names": case-fold, collapse runs of ``-_.`` to a single ``-``.

    Comparison-only helper — never used as a rendered id. ``Foo_Bar``, ``foo-bar`` and
    ``foo.bar`` are the same distribution name to any real resolver (pip/uv); WR-02
    (47-REVIEW.md).
    """
    return _PEP503_SEPARATORS.sub("-", name).lower()


def _is_excluded(path: str) -> bool:
    """True when ``path`` contains the consecutive segments ``("tests", "fixtures")`` anywhere.

    A package's own ``tests/`` directory that contains no ``fixtures/`` segment is NOT excluded —
    only manifests living under a fixtures tree (e.g. a fixture manifest used by another
    package's tests) are dropped from the scan.
    """
    parts = PurePosixPath(path).parts
    return any(parts[i] == "tests" and parts[i + 1] == "fixtures" for i in range(len(parts) - 1))


def discover_manifests(repo_root: Path = _REPO_ROOT) -> list[dict]:
    """Enumerate git-tracked manifests under ``repo_root`` via a light ``git ls-files`` walk.

    Builds minimal ``included`` entries (``path``/``size``/``sha256`` — the latter two are dummy
    placeholders, since this generator never renders `evidence`) and hands them to
    ``detect.detect_manifests`` for kind recognition; results falling under a
    ``tests/fixtures/**`` path are then filtered out. Returns the filtered,
    sorted-by-path manifest record list.
    """
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    )
    included = [
        {"path": line.strip(), "size": 0, "sha256": ""}
        for line in completed.stdout.splitlines()
        if line.strip()
    ]
    manifests = detect.detect_manifests(included)
    return [record for record in manifests if not _is_excluded(record["path"])]


def _fallback_id(manifest_path: str) -> str:
    """The directory-name id used when a manifest's declared name is absent OR unreadable."""
    parent = PurePosixPath(manifest_path).parent
    return "." if str(parent) == "." else parent.name


def _package_id(manifest_path: str, kind: str, text: str) -> str:
    """Return the manifest's own declared package name, falling back to its directory name."""
    name: str | None = None
    if kind == "pyproject.toml":
        name = tomllib.loads(text).get("project", {}).get("name")
    elif kind == "package.json":
        name = json.loads(text).get("name")
    elif kind == "*.csproj":
        name = PurePosixPath(manifest_path).stem
    elif kind == "go.mod":
        match = _GO_MODULE_DIRECTIVE.search(text)
        name = match.group(1) if match else None
    elif kind == "Cargo.toml":
        name = tomllib.loads(text).get("package", {}).get("name")

    if name:
        return name
    return _fallback_id(manifest_path)


def build_facts(manifest_paths: list[dict] | None = None, repo_root: Path = _REPO_ROOT) -> dict:
    """Assemble ``{"packages": [...], "edges": [...]}`` — the single public entry point.

    When ``manifest_paths`` is ``None``, discovers manifests via :func:`discover_manifests`;
    otherwise treats the passed value AS the manifest-record list (the test seam that lets
    callers exercise assembly without a real git-tracked tree — same shape
    :func:`discover_manifests` returns).

    Packages are sorted by their ``manifest`` path (the stable key). Dependency edges are
    resolved against the closed set of packages just discovered: a path-based reference
    (``.csproj``/``Cargo.toml``) is normalized relative to the referencing manifest's own
    directory and matched against a known package's manifest path; a name-based reference
    (``pyproject.toml``/``package.json``/``go.mod``) is matched against a known package's id.
    An unresolved or self-referencing dependency is dropped, never fabricated. Edges are
    de-duplicated and sorted by ``(from, to, kind)``.
    """
    if manifest_paths is None:
        manifest_paths = discover_manifests(repo_root)

    texts: dict[str, str | None] = {}
    packages: list[dict] = []
    for record in manifest_paths:
        path = record["path"]
        kind = record["kind"]
        try:
            text = (repo_root / path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"package_facts: skipping unreadable manifest {path}: {exc}", file=sys.stderr)
            text = None

        package_id: str | None = None
        if text is not None:
            try:
                package_id = _package_id(path, kind, text)
            except _MANIFEST_PARSE_ERRORS as exc:
                # WR-03 (47-REVIEW.md): a malformed manifest degrades for THIS file only — the
                # package is still listed (directory-name fallback), the failure surfaces on
                # stderr, and the run continues rather than crashing whole-generator-wide.
                print(f"package_facts: failed to parse manifest {path}: {exc}", file=sys.stderr)
                package_id = None

        texts[path] = text
        packages.append(
            {
                "id": package_id if package_id is not None else _fallback_id(path),
                "manifest": path,
                "dir": str(PurePosixPath(path).parent),
                "language": _KIND_LANGUAGE[kind],
            }
        )
    packages.sort(key=lambda pkg: pkg["manifest"])

    manifest_by_path = {pkg["manifest"]: pkg for pkg in packages}
    id_by_manifest = {pkg["manifest"]: pkg["id"] for pkg in packages}
    manifest_by_id = {pkg["id"]: pkg["manifest"] for pkg in packages}
    kind_by_manifest = {record["path"]: record["kind"] for record in manifest_paths}
    # WR-02 (47-REVIEW.md): a PEP 503-normalized index, scoped to pyproject.toml packages only
    # (Python's own name-equivalence rule; other manifest kinds have their own conventions and
    # must not be folded together). Rendered ids stay each manifest's declared name — this index
    # is comparison-only, never surfaced.
    manifest_by_normalized_pyproject_id = {
        _normalize_pep503(pkg["id"]): pkg["manifest"]
        for pkg in packages
        if kind_by_manifest.get(pkg["manifest"]) == "pyproject.toml"
    }

    edges: set[tuple[str, str, str]] = set()
    for record in manifest_paths:
        path = record["path"]
        kind = record["kind"]
        text = texts[path]
        if text is None:
            continue  # unreadable manifest already reported above; no edges to/from it
        from_id = id_by_manifest[path]
        try:
            deps = detect.detect_dependencies(path, kind, text)
        except _MANIFEST_PARSE_ERRORS as exc:
            print(f"package_facts: failed to parse dependencies in {path}: {exc}", file=sys.stderr)
            continue
        for dep in deps:
            target_manifest: str | None = None
            if "path" in dep:
                own_dir = PurePosixPath(path).parent
                normalized = posixpath.normpath(str(own_dir / dep["path"]))
                if kind == "Cargo.toml":
                    normalized = posixpath.normpath(normalized + "/Cargo.toml")
                if normalized in manifest_by_path:
                    target_manifest = normalized
            else:
                target_id = dep["name"]
                if target_id in manifest_by_id:
                    target_manifest = manifest_by_id[target_id]
                elif kind == "pyproject.toml":
                    target_manifest = manifest_by_normalized_pyproject_id.get(
                        _normalize_pep503(target_id)
                    )

            if target_manifest is None:
                continue
            to_id = id_by_manifest[target_manifest]
            if to_id == from_id:
                continue
            edges.add((from_id, to_id, dep["kind"]))

    return {
        "packages": packages,
        "edges": [{"from": frm, "to": to, "kind": kind} for frm, to, kind in sorted(edges)],
    }


def _render_value(value: object) -> str:
    """Render a profile field for a markdown cell: ``None`` becomes the literal ``(none)``."""
    return "(none)" if value is None else str(value)


def render(facts: dict, cfg: dict | None = None) -> str:
    """Render ``facts`` into the deterministic DERIVED-marked markdown artifact.

    Three tables: ``## Packages`` (id/manifest/dir/language), ``## Dependency Edges``
    (from/to/kind), and a third convention-profiles section (MONO-05/MONO-06 —
    package/dir/language/test/format/bash_scope/agents_md/default, one row per package, computed
    entirely via :func:`tools.harness_config.conventions_for` — no command literal is ever
    restated here). No timestamp, no raw float. Trailing newline.

    ``cfg`` is an additive, optional parameter (defaults to ``None``, meaning "load the default
    ``harness/project.toml``") threaded straight through to ``conventions_for``; existing call
    sites (``write()``/``main()``) need no edit.
    """
    # Lazy in-function import — mirrors loader.py's own reverse-direction lazy import of
    # tools.memory_regen.package_facts inside effective_packages(); keeps the convention
    # consistent even though no import cycle exists in this direction.
    from tools.harness_config import conventions_for

    lines = [
        f"# {DERIVED_HEADER}",
        "",
        "Every package in this checkout with its manifest path, language and package id, plus "
        "intra-repo dependency edges parsed from the manifests themselves.",
        "",
        "## Packages",
        "",
        "| id | manifest | dir | language |",
        "| --- | --- | --- | --- |",
    ]
    for pkg in facts["packages"]:
        lines.append(f"| {pkg['id']} | {pkg['manifest']} | {pkg['dir']} | {pkg['language']} |")

    lines += [
        "",
        "## Dependency Edges",
        "",
        "| from | to | kind |",
        "| --- | --- | --- |",
    ]
    for edge in facts["edges"]:
        lines.append(f"| {edge['from']} | {edge['to']} | {edge['kind']} |")

    lines += [
        "",
        "## Convention Profiles",
        "",
        "| package | dir | language | test | format | bash_scope | agents_md | default |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for pkg in facts["packages"]:
        profile = conventions_for(pkg["dir"], cfg=cfg, facts=facts)
        lines.append(
            "| "
            + " | ".join(
                [
                    _render_value(profile["package"]),
                    _render_value(profile["dir"]),
                    _render_value(profile["language"]),
                    _render_value(profile["test"]),
                    _render_value(profile["format"]),
                    _render_value(profile["bash_scope"]),
                    _render_value(profile["agents_md"]),
                    "true" if profile["is_default"] else "false",
                ]
            )
            + " |"
        )

    return "\n".join(lines) + "\n"


def write(
    index_path: str | Path = PACKAGE_FACTS_PATH,
    manifest_paths: list[dict] | None = None,
    repo_root: Path = _REPO_ROOT,
) -> Path:
    """Regenerate the derived package-facts artifact and write it (mkdir parents)."""
    out = Path(index_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(build_facts(manifest_paths, repo_root)), encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    """CLI: regenerate ``.memory/derived/package-facts.md`` (`python -m ...package_facts`)."""
    argv = sys.argv[1:] if argv is None else argv  # noqa: F841 (reserved for future flags)
    out = write()
    facts = build_facts()
    print(
        f"wrote {out.relative_to(_REPO_ROOT)} "
        f"({len(facts['packages'])} package(s), {len(facts['edges'])} edge(s))"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
