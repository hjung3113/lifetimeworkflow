"""detect.py — language/manifest/documentation/CI/test-surface/candidate-process-boundary
detection feeding :func:`tools.adoption_scan.scan.build_inventory` (ADOPT-01).

Every detection rule is EXTENSION/FILENAME/STRUCTURE-based only — no tree-sitter, no symbol
parsing (26-RESEARCH.md: D-02's conservative bias makes symbol-level inference ``unknown`` anyway).
Operates purely on the ``included`` list already assembled by ``scan.py`` (each entry already
carries ``path``/``size``/``sha256``) — no filesystem access here, so detection can never diverge
from what was actually hashed as an evidence pointer.

D-02 evidence classification ladder, enforced structurally by every function below:
- ``observed`` — direct evidence only: a file/extension is literally present (languages,
  manifests, documentation/CI/test surfaces when the recognized path exists).
- ``inferred`` — strong *structural* signals only: a directory containing a recognized manifest is
  a candidate component root. ``candidate_process_boundaries`` is ALWAYS ``inferred`` — component
  existence is inherently inferred (never ``observed``), per D-02.

Ownership/authority classification (who OWNS a component, contract, or CODEOWNERS path) is out of
scope here — that evidence ladder step belongs to Plan 03's ``plan.py``.
"""

from __future__ import annotations

import fnmatch
import json
import re
import tomllib
import xml.etree.ElementTree as ET
from pathlib import PurePosixPath

# Extension -> language slug (observed on extension presence, D-02).
_LANGUAGE_BY_EXTENSION: dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".cs": "csharp",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".go": "go",
    ".rs": "rust",
    ".sh": "shell",
    ".rb": "ruby",
    ".java": "java",
}

# Manifest filename -> kind (observed on literal file existence, D-02).
#
# `pnpm-workspace.yaml` is deliberately NOT registered here. This table drives
# `detect_manifests` -> `detect_candidate_process_boundaries`, so registering it would emit a
# 6th manifest record and a duplicate root boundary, directly defeating RTA-02's "exactly the
# five members" (52-CONTEXT.md D-07's literal wording vs its intent — see PNPM_WORKSPACE_MANIFEST
# below, which teaches the workspace manifest as its own module-level constant + pure parser
# instead, scoping membership at the source without growing this kind table).
_MANIFEST_KIND_BY_NAME: dict[str, str] = {
    "pyproject.toml": "pyproject.toml",
    "package.json": "package.json",
    "go.mod": "go.mod",
    "Cargo.toml": "Cargo.toml",
}

# OBS-D-01 (51-BASELINE-EVIDENCE.md) — purpose 2: pnpm workspace member scoping.
PNPM_WORKSPACE_MANIFEST = "pnpm-workspace.yaml"


def _strip_matched_quotes(item: str) -> str:
    """Strip ONE pair of matched surrounding quotes, if present."""
    if len(item) >= 2 and item[0] == item[-1] and item[0] in "\"'":
        return item[1:-1]
    return item


def _parse_flow_sequence(remainder: str) -> list[str] | None:
    """Parse a single-line YAML flow sequence (``["apps/*", 'packages/*']``) into its items.

    Returns ``None`` when *remainder* is not a complete single-line flow sequence (so the caller
    can fall back to block-style handling); returns ``[]`` for a literally empty ``[]``.

    Scope note, deliberately narrow (same zero-new-external-deps reasoning as
    :func:`parse_pnpm_workspace_globs`): items are split on ``,``, so a glob containing a literal
    comma inside quotes would split wrongly. pnpm workspace globs are path patterns and do not
    contain commas; a multi-line flow sequence is likewise not handled and falls through to the
    "no globs parsed" degrade path rather than being half-parsed.
    """
    stripped = remainder.strip()
    if not (stripped.startswith("[") and stripped.endswith("]")):
        return None
    body = stripped[1:-1].strip()
    if not body:
        return []
    items: list[str] = []
    for raw_item in body.split(","):
        item = _strip_matched_quotes(raw_item.strip())
        if item:
            items.append(item)
    return items


# OBS-D-01 (51-BASELINE-EVIDENCE.md) — purpose 2: pnpm workspace member scoping.
def parse_pnpm_workspace_globs(text: str) -> list[str]:
    """Narrow line-based reader of a ``pnpm-workspace.yaml``'s top-level ``packages:`` value.

    Deliberately NOT a general YAML parser (52-RESEARCH.md § Don't Hand-Roll) — this repo's
    ``pyproject.toml`` carries a zero-new-external-deps invariant, so pulling in a full
    third-party YAML library for one four-line list-of-globs shape is out of proportion. Scope
    is exactly pnpm's ``packages:`` list-of-glob-strings, in BOTH of the shapes real pnpm
    manifests use:

    - block style — collect ``- glob`` / ``- "glob"`` / ``- 'glob'`` list items inside the block
      (surrounding matched quotes stripped, order preserved), skip ``#`` comment lines and blank
      lines, and stop the block at the next top-level key (a non-blank, non-comment,
      non-list-item line).
    - flow style — ``packages: ["apps/*", "packages/*"]`` on one line (CR-02, 52-REVIEW.md: valid
      YAML and a common pnpm manifest shape; before this it never entered the block at all and
      silently mis-scoped the whole target).

    No filesystem access — this function only ever sees text handed to it (module docstring
    invariant: detection can never diverge from what was hashed).

    Malformed / non-YAML / empty text degrades to ``[]`` rather than raising, mirroring
    ``package_facts.py:176-182``'s degrade-per-file posture (T-52-04). CR-02 (52-REVIEW.md):
    ``[]`` here means "no globs could be extracted", which the CALLER
    (``scan.build_inventory``) must read as "no workspace scoping — take the D-10 unchanged
    path", NEVER as "this workspace declares zero members". Returning ``[]`` is not itself the
    downgrade; the caller performs it.
    """
    try:
        globs: list[str] = []
        in_block = False
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if not in_block:
                if stripped == "packages:":
                    in_block = True
                elif stripped.startswith("packages:"):
                    flow = _parse_flow_sequence(stripped[len("packages:") :])
                    if flow is not None:
                        globs.extend(flow)
                continue
            if not stripped or stripped.startswith("#"):
                continue
            if not stripped.startswith("-"):
                # A non-blank, non-comment, non-list-item line is the next top-level key.
                in_block = False
                continue
            item = stripped[1:].strip()
            if not item or item.startswith("#"):
                continue
            if not item.startswith(('"', "'")):
                hash_idx = item.find("#")
                if hash_idx != -1:
                    item = item[:hash_idx].strip()
            item = _strip_matched_quotes(item)
            if item:
                globs.append(item)
        return globs
    # WR-09 (52-REVIEW.md): narrowed from a bare `except Exception`, which swallowed genuine
    # programming errors introduced later and discarded already-parsed globs. These are exactly
    # the input-SHAPE faults a non-str / undecodable `text` produces; anything else is a bug and
    # must surface.
    except (AttributeError, TypeError, UnicodeError):
        return []


def _segments_match(directory_parts: tuple[str, ...], glob_parts: tuple[str, ...]) -> bool:
    """Per-segment match of ``directory_parts`` against ``glob_parts``, honouring ``**``.

    WR-01 (52-REVIEW.md): a ``**`` segment matches ZERO OR MORE directory segments (standard
    globstar, which is what pnpm's own documented ``packages/**`` example means); every other
    segment matches EXACTLY one segment via :func:`fnmatch.fnmatchcase`. WR-02: ``fnmatchcase``,
    not ``fnmatch`` — ``fnmatch`` applies ``os.path.normcase`` to both operands, which makes
    membership case-insensitive on Windows and so makes ``inventory.json`` platform-dependent,
    breaking ``scan.py``'s byte-determinism invariant.
    """
    if not glob_parts:
        return not directory_parts
    head, rest = glob_parts[0], glob_parts[1:]
    if head == "**":
        return any(
            _segments_match(directory_parts[i:], rest) for i in range(len(directory_parts) + 1)
        )
    if not directory_parts:
        return False
    if not fnmatch.fnmatchcase(directory_parts[0], head):
        return False
    return _segments_match(directory_parts[1:], rest)


def _usable_glob_parts(glob: str) -> tuple[str, ...] | None:
    """Split *glob* into path segments, or ``None`` when the T-52-03 traversal guard rejects it.

    A glob that is absolute or contains a ``..`` segment contributes NO members: membership is
    computed on repo-relative POSIX directories only.
    """
    if glob.startswith("/") or PurePosixPath(glob).is_absolute():
        return None
    glob_parts = PurePosixPath(glob).parts
    if any(part == ".." for part in glob_parts):
        return None
    return glob_parts


# OBS-D-01 (51-BASELINE-EVIDENCE.md) — purpose 2: pnpm workspace member scoping.
def is_workspace_member(directory: str, globs: list[str]) -> bool:
    """True if ``directory`` (a repo-relative POSIX dir, ``"."`` for the workspace root)
    matches one of the pnpm workspace ``globs``.

    The workspace root (``"."``) is always a member, regardless of ``globs`` — pnpm's own
    implicit-root semantics. A glob that is absolute or contains a ``..`` segment contributes NO
    members (T-52-03 traversal guard), and the caller (``scan.py``) re-validates any glob-derived
    path with its own ``_confined`` idiom before ever treating it as a member.

    Matching is per-path-segment (:func:`_segments_match`): a bare ``*`` matches exactly one
    directory segment, so ``apps/*`` matches ``apps/widget-app`` but NOT
    ``apps/widget-app/nested``; a ``**`` segment matches any depth, so ``packages/**`` matches
    both ``packages/b`` and ``packages/b/deep`` (WR-01).

    WR-03: a ``!``-prefixed glob is a pnpm NEGATION, not a positive pattern. A directory is a
    member iff it matches at least one positive glob AND no negative glob — previously the ``!``
    was stored verbatim and never interpreted, so ``["packages/*", "!packages/legacy"]``
    reported ``packages/legacy`` as a member and the inventory over-included.
    """
    if directory == ".":
        return True
    directory_parts = PurePosixPath(directory).parts

    positive: list[tuple[str, ...]] = []
    negative: list[tuple[str, ...]] = []
    for glob in globs:
        bucket = negative if glob.startswith("!") else positive
        pattern = glob[1:] if glob.startswith("!") else glob
        if not pattern:
            continue
        parts = _usable_glob_parts(pattern)
        if parts is None:
            continue
        bucket.append(parts)

    if not any(_segments_match(directory_parts, parts) for parts in positive):
        return False
    return not any(_segments_match(directory_parts, parts) for parts in negative)


# WR-06 (26-REVIEW.md): all three GitHub-honored CODEOWNERS locations — a repo may place the
# file at the root, under .github/, or under docs/, and GitHub resolves whichever is present.
_CODEOWNERS_PATHS: frozenset[str] = frozenset(
    {"CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS"}
)


def _evidence(entries: list[dict]) -> list[dict]:
    """Build a sorted evidenceRef list from already-hashed ``included`` entries."""
    return [
        {"path": entry["path"], "sha256": entry["sha256"], "size": entry["size"]}
        for entry in sorted(entries, key=lambda item: item["path"])
    ]


def _surface(
    target: str, entries: list[dict], classification: str, rationale: str | None = None
) -> dict:
    record = {
        "target": target,
        "classification": classification,
        "evidence": _evidence(entries),
    }
    if rationale is not None:
        record["rationale"] = rationale
    return record


def detect_languages(included: list[dict]) -> list[dict]:
    """One ``languageRecord`` per distinct extension found among ``included`` entries.

    ``classification: "observed"`` — extension presence is direct evidence (D-02).
    """
    by_language: dict[str, list[dict]] = {}
    for entry in included:
        suffix = PurePosixPath(entry["path"]).suffix.lower()
        language = _LANGUAGE_BY_EXTENSION.get(suffix)
        if language is None:
            continue
        by_language.setdefault(language, []).append(entry)

    return [
        {
            "name": language,
            "classification": "observed",
            "evidence": _evidence(by_language[language]),
        }
        for language in sorted(by_language)
    ]


def detect_manifests(included: list[dict]) -> list[dict]:
    """One ``manifestRecord`` per recognized manifest file present in ``included``.

    ``classification: "observed"`` — literal file existence (D-02).
    """
    records: list[dict] = []
    for entry in sorted(included, key=lambda item: item["path"]):
        name = PurePosixPath(entry["path"]).name
        kind = _MANIFEST_KIND_BY_NAME.get(name)
        if kind is None and name.endswith(".csproj"):
            kind = "*.csproj"
        if kind is None:
            continue
        records.append(
            {
                "path": entry["path"],
                "kind": kind,
                "classification": "observed",
                "evidence": _evidence([entry]),
            }
        )
    return records


def detect_documentation_surfaces(included: list[dict]) -> list[dict]:
    """``surfaceRecord``s for recognized documentation surfaces (ADR / README / AGENTS.md).

    ``classification: "observed"`` when the recognized path exists (D-02).

    WR-01 (26-REVIEW.md): every distinct ``AGENTS.md`` path (root AND every nested one) gets its
    OWN ``surfaceRecord`` with ``target`` set to that file's actual path — never lumped into one
    fixed-literal-target record. Nearest-wins ``AGENTS.md`` semantics are inherently per-directory
    (a root ``AGENTS.md`` and e.g. ``libs/python/AGENTS.md`` are different boundaries with
    potentially different answers), so each needs its own proposal/question downstream in
    ``plan.py``. README stays coarse-grained (one record for all README/README.md files) — an
    intentional, narrower design choice noted in the review as acceptable.
    """
    records: list[dict] = []

    adr_entries = [
        entry for entry in included if PurePosixPath(entry["path"]).parts[:2] == ("docs", "adr")
    ]
    if adr_entries:
        records.append(_surface("docs/adr", adr_entries, "observed"))

    readme_entries = [
        entry for entry in included if PurePosixPath(entry["path"]).name in {"README", "README.md"}
    ]
    if readme_entries:
        records.append(_surface("README", readme_entries, "observed"))

    agents_entries = [
        entry for entry in included if PurePosixPath(entry["path"]).name == "AGENTS.md"
    ]
    for entry in sorted(agents_entries, key=lambda item: item["path"]):
        records.append(_surface(entry["path"], [entry], "observed"))

    return sorted(records, key=lambda record: record["target"])


def detect_ci_surfaces(included: list[dict]) -> list[dict]:
    """``surfaceRecord``s for CI surfaces (``.github/workflows/*.yml``).

    ``classification: "observed"`` when the recognized path exists (D-02).
    """
    ci_entries = [
        entry
        for entry in included
        if PurePosixPath(entry["path"]).parts[:2] == (".github", "workflows")
    ]
    if not ci_entries:
        return []
    return [_surface(".github/workflows", ci_entries, "observed")]


def detect_test_surfaces(included: list[dict]) -> list[dict]:
    """``surfaceRecord``s for test surfaces (a ``tests/`` dir containing ``test_*.py``).

    ``classification: "observed"`` when the recognized path exists (D-02).
    """
    test_entries = [
        entry
        for entry in included
        if PurePosixPath(entry["path"]).parts[:1] == ("tests",)
        and PurePosixPath(entry["path"]).name.startswith("test_")
    ]
    if not test_entries:
        return []
    return [_surface("tests", test_entries, "observed")]


def detect_schema_surfaces(included: list[dict]) -> list[dict]:
    """``surfaceRecord``s for schema surfaces (``contracts/**/*.schema.json`` ONLY).

    ``classification: "observed"`` when a matching path exists (D-02). Deliberately scoped to
    files whose first path segment is ``contracts`` AND whose name ends ``.schema.json`` — NOT
    every ``*.schema.json`` anywhere in the tree, since this repo alone has schema-named files
    under ``harness/``, ``tools/``, the domain-instance directory, ``.claude/skills/``, and
    ``tests/fixtures/`` that must never match.
    """
    schema_entries = [
        entry
        for entry in included
        if PurePosixPath(entry["path"]).parts[:1] == ("contracts",)
        and PurePosixPath(entry["path"]).name.endswith(".schema.json")
    ]
    if not schema_entries:
        return []
    return [_surface("contracts/**/*.schema.json", schema_entries, "observed")]


def detect_codeowners_surfaces(included: list[dict]) -> list[dict]:
    """``surfaceRecord``s for a CODEOWNERS surface, recognizing all three GitHub-honored
    locations: ``CODEOWNERS`` (root), ``.github/CODEOWNERS``, and ``docs/CODEOWNERS``.

    ``classification: "observed"`` when a literal path exists (D-02) — only the file's
    EXISTENCE and path are recorded, never its ownership-mapping content interpreted as
    authority, at any of the three locations. One ``surfaceRecord`` PER distinct CODEOWNERS
    path found (mirrors :func:`detect_documentation_surfaces`'s per-nested-AGENTS.md
    precedent) — never lumped into a single fixed-literal-target record.
    """
    matches: dict[str, dict] = {}
    for entry in included:
        path = entry["path"]
        if path in _CODEOWNERS_PATHS:
            matches[path] = entry

    records = [_surface(path, [entry], "observed") for path, entry in matches.items()]
    return sorted(records, key=lambda record: record["target"])


def detect_candidate_process_boundaries(included: list[dict]) -> list[dict]:
    """``surfaceRecord``s for candidate component/process boundaries.

    A directory containing a recognized manifest is a candidate component root.
    ``classification: "inferred"`` ALWAYS — component/member existence is inherently inferred
    (D-02); never ``observed`` for a candidate process boundary.
    """
    manifests = detect_manifests(included)
    records: list[dict] = []
    for manifest in sorted(manifests, key=lambda item: item["path"]):
        directory = str(PurePosixPath(manifest["path"]).parent)
        records.append(
            {
                "target": directory,
                "classification": "inferred",
                "evidence": manifest["evidence"],
                "rationale": "manifest-directory",
            }
        )
    return records


def _dependency_bare_name(dep: str) -> str:
    """Split a version specifier / marker off a PEP 508-ish dependency string."""
    return re.split(r"[<>=!~\[; ]", dep, maxsplit=1)[0].strip()


def _dependencies_from_pyproject(text: str) -> list[dict]:
    """Parse ``[project].dependencies`` (runtime) and PEP 735 ``[dependency-groups].dev`` (dev)."""
    data = tomllib.loads(text)
    entries: list[dict] = []
    for dep in data.get("project", {}).get("dependencies", []):
        entries.append({"name": _dependency_bare_name(dep), "kind": "runtime"})
    for dep in data.get("dependency-groups", {}).get("dev", []):
        entries.append({"name": _dependency_bare_name(dep), "kind": "dev"})
    return entries


def _dependencies_from_package_json(text: str) -> list[dict]:
    """Parse ``dependencies`` (runtime) and ``devDependencies`` (dev) keys; version values
    ignored."""
    data = json.loads(text)
    entries: list[dict] = []
    # IN-02 (47-REVIEW.md): `.get(..., {})`'s default only applies when the key is absent, not
    # when it is present-but-null (`"dependencies": null` is valid JSON) — `or {}` covers both.
    for name in data.get("dependencies") or {}:
        entries.append({"name": name, "kind": "runtime"})
    for name in data.get("devDependencies") or {}:
        entries.append({"name": name, "kind": "dev"})
    return entries


# IN-01 (47-REVIEW.md): legacy (pre-SDK-style) .csproj files declare this default xmlns on the
# <Project> root, which puts every child element into that namespace; an unqualified `findall`
# then silently matches nothing.
_LEGACY_MSBUILD_NAMESPACE = "http://schemas.microsoft.com/developer/msbuild/2003"


def _dependencies_from_csproj(text: str) -> list[dict]:
    """Parse ``<ProjectReference Include="...">`` elements; each is a path-based reference."""
    root = ET.fromstring(text)
    matches = root.findall(".//ProjectReference")
    if not matches:
        # Fallback for legacy-style project files that declare the default MSBuild 2003
        # namespace on <Project> (IN-01, 47-REVIEW.md).
        matches = root.findall(f".//{{{_LEGACY_MSBUILD_NAMESPACE}}}ProjectReference")
    entries: list[dict] = []
    for element in matches:
        include = element.get("Include")
        if include is None:
            continue
        # WR-01 (47-REVIEW.md): MSBuild accepts backslash separators on any OS, and
        # Visual-Studio-authored .csproj files commonly emit them; git-tracked paths are always
        # forward-slash, so normalize before this reference is used as a lookup key.
        include_posix = include.replace("\\", "/")
        entries.append({"name": include_posix, "kind": "runtime", "path": include_posix})
    return entries


def _dependencies_from_go_mod(text: str) -> list[dict]:
    """Line-based parse of a ``require (...)`` block and single-line ``require`` statements."""
    entries: list[dict] = []
    in_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if not in_block and stripped.startswith("require") and stripped.endswith("("):
            in_block = True
            continue
        if in_block:
            if stripped == ")":
                in_block = False
                continue
            if not stripped or stripped.startswith("//"):
                continue
            parts = stripped.split()
            if parts:
                entries.append({"name": parts[0], "kind": "runtime"})
            continue
        if stripped.startswith("require ") and not stripped.startswith("require("):
            parts = stripped[len("require ") :].split()
            if parts:
                entries.append({"name": parts[0], "kind": "runtime"})
    return entries


def _dependencies_from_cargo_toml(text: str) -> list[dict]:
    """Parse path-only ``[dependencies]``/``[dev-dependencies]`` entries; registry deps dropped."""
    data = tomllib.loads(text)
    entries: list[dict] = []
    for section, kind in (("dependencies", "runtime"), ("dev-dependencies", "dev")):
        for name, value in data.get(section, {}).items():
            if isinstance(value, dict) and "path" in value:
                entries.append({"name": name, "kind": kind, "path": value["path"]})
    return entries


_DEPENDENCY_PARSER_BY_KIND = {
    "pyproject.toml": _dependencies_from_pyproject,
    "package.json": _dependencies_from_package_json,
    "*.csproj": _dependencies_from_csproj,
    "go.mod": _dependencies_from_go_mod,
    "Cargo.toml": _dependencies_from_cargo_toml,
}


def detect_dependencies(path: str, kind: str, text: str) -> list[dict]:
    """Parse declared dependency names + kind ("runtime"|"dev") from one manifest's raw text.

    Pure: given identical (path, kind, text) always returns identical output. Performs NO
    filesystem access itself — the caller (the generator) already reads `text` off disk to
    render the artifact, so this function never diverges from that read. An unrecognized `kind`
    returns `[]` rather than raising.
    """
    del path  # unused: kept for signature symmetry with detect_manifests' path-first shape
    parser = _DEPENDENCY_PARSER_BY_KIND.get(kind)
    if parser is None:
        return []
    return parser(text)
