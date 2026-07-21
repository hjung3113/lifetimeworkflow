"""``harness/skills/registry.lock`` — the DECLARED skill surface, and the recompute-vs-lock diff.

WHY THIS EXISTS ALONGSIDE ``emit-drift``.  The two gates answer different questions and neither
covers the other:

* ``emit-drift`` re-runs the emitter and diffs the result.  It asks *"is the emitted tree a faithful
  projection of the current source?"* — and it is blind, BY CONSTRUCTION, to a change in what the
  source declares, because it re-derives the expectation from that same source.
* this lock asks *"does the skill surface still match its DECLARATION?"*

Three concrete things escape ``emit-drift`` and are caught here:

1. **A description rewrite.**  A skill's ``description`` is its routing trigger — it decides which
   requests reach the skill at all.  Editing it re-emits cleanly to both runtimes and the drift gate
   stays green.
2. **A new ``references/`` file.**  The emitter discovers that subtree by glob, so a file added to
   it is emitted and manifested with no declaration moving.
3. **A half-emitted surface.**  A skill present in one runtime lane and absent from the other is
   still a self-consistent re-emit; only a declaration of the expected PAIR catches it.

``tools/harness_lint/caps.py`` ``EXPECTED_SKILLS`` catches an added or removed skill NAME, and
nothing else.  The lock closes the rest.

The emitted-path column is READ from the emitter's committed ownership manifest
(``tools.harness_emit.manifest.load_manifest``), never recomputed here — a second copy of the emit
layout would be exactly the parallel mechanism this milestone exists to stop shipping.
"""

from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path
from typing import Any

from tools.harness_emit.manifest import load_manifest
from tools.harness_lint import parse_frontmatter

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "harness" / "skills"
LOCK_PATH = SKILLS_DIR / "registry.lock"
EMIT_MANIFEST = REPO_ROOT / "tools" / "harness_emit" / "emit-manifest.json"
DECLARATIONS = REPO_ROOT / "harness" / "disciplines.toml"

LOCK_VERSION = 1
# The two emitted lanes a skill must appear in. Declaring the PAIR is what catches a half-emitted
# surface; a single-lane expectation would pass a skill that reached only one runtime.
# The lock itself lives at harness/skills/registry.lock — a declaration ABOUT the skill tree, beside
# it rather than inside any skill directory, so it never hashes itself into an unreachable fixed
# point.
_EMITTED_LANES = (".claude/skills/", ".opencode/skill/")


class SkillRegistryError(ValueError):
    """A malformed lock or an unreadable skill — never an ordinary drift result.

    Drift is an ordinary result (a non-empty ``diff_lock`` list), not an exception: it is the
    expected answer whenever a declaration and the tree have moved apart.
    """


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _description(skill_md: Path) -> str:
    try:
        frontmatter, _ = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SkillRegistryError(f"unreadable skill frontmatter: {skill_md.name} ({exc})") from exc
    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.strip():
        raise SkillRegistryError(f"skill {skill_md.parent.name} declares no description")
    return description


def _source_digests(skill_dir: Path) -> dict[str, str]:
    """Every regular file in the skill directory → the SHA-256 of its raw bytes.

    Symlinks are skipped and escapes are dropped, mirroring
    ``harness_emit.project_skill.iter_reference_files``: a link pointing outside the subtree must
    never contribute a digest for a file the emitter would not copy.
    """
    digests: dict[str, str] = {}
    root = skill_dir.resolve()
    for path in sorted(skill_dir.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        if path.resolve().parent != root and root not in path.resolve().parents:
            continue
        digests[path.relative_to(skill_dir).as_posix()] = _sha256(path.read_bytes())
    return digests


def _emitted_paths(manifest: list[str], name: str) -> list[str]:
    prefixes = tuple(f"{lane}{name}/" for lane in _EMITTED_LANES)
    return sorted(
        entry
        for entry in (item.replace("\\", "/") for item in manifest)
        if entry.startswith(prefixes)
    )


def _disciplines_by_skill(path: Path = DECLARATIONS) -> dict[str, list[str]]:
    """Which declared lane disciplines name each skill.

    Locking this mapping is the point phase 36 deferred here: a discipline whose skill is silently
    repointed is a lane requirement that now routes to a different procedure.
    """
    try:
        with Path(path).open("rb") as handle:
            raw = tomllib.load(handle)
    except (FileNotFoundError, tomllib.TOMLDecodeError) as exc:
        raise SkillRegistryError(f"unreadable discipline declarations: {exc}") from exc
    mapping: dict[str, list[str]] = {}
    table = raw.get("discipline")
    if isinstance(table, dict):
        for identifier, body in table.items():
            if isinstance(body, dict) and isinstance(body.get("skill"), str):
                mapping.setdefault(body["skill"], []).append(identifier)
    return {skill: sorted(ids) for skill, ids in mapping.items()}


def build_registry(
    skills_dir: str | Path = SKILLS_DIR,
    *,
    manifest_path: str | Path = EMIT_MANIFEST,
    declarations_path: str | Path = DECLARATIONS,
) -> dict[str, Any]:
    """Recompute the declared skill surface from the tree."""
    root = Path(skills_dir)
    if not root.is_dir():
        raise SkillRegistryError(f"no skills directory: {root}")
    manifest = load_manifest(manifest_path)
    owed = _disciplines_by_skill(Path(declarations_path))
    skills: dict[str, Any] = {}
    for skill_dir in sorted(p for p in root.iterdir() if p.is_dir() and not p.is_symlink()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            raise SkillRegistryError(f"skill directory with no SKILL.md: {skill_dir.name}")
        name = skill_dir.name
        skills[name] = {
            "description_sha256": _sha256(_description(skill_md).encode("utf-8")),
            "sources": _source_digests(skill_dir),
            "emitted": _emitted_paths(manifest, name),
            "disciplines": owed.get(name, []),
        }
    return {"tool": "tools.skill_registry", "version": LOCK_VERSION, "skills": skills}


def dumps(registry: dict[str, Any]) -> str:
    """Deterministic serialization — the ``manifest.prune_then_write`` contract, so a rewrite is
    byte-identical whenever nothing moved."""
    return json.dumps(registry, sort_keys=True, indent=2) + "\n"


def load_lock(path: str | Path = LOCK_PATH) -> dict[str, Any]:
    lock_path = Path(path)
    try:
        value = json.loads(lock_path.read_bytes().removeprefix(b"\xef\xbb\xbf"))
    except FileNotFoundError as exc:
        raise SkillRegistryError(f"no registry lock at {lock_path}") from exc
    except json.JSONDecodeError as exc:
        raise SkillRegistryError(f"invalid registry lock: {exc.msg}") from exc
    if not isinstance(value, dict) or value.get("version") != LOCK_VERSION:
        raise SkillRegistryError(f"registry lock version must be {LOCK_VERSION}")
    if not isinstance(value.get("skills"), dict):
        raise SkillRegistryError("registry lock has no skills table")
    return value


def diff_lock(locked: dict[str, Any], recomputed: dict[str, Any]) -> list[str]:
    """Every way the tree and the lock disagree, named specifically.

    A bare "the files differ" is not actionable and would make the gate one nobody acts on, so each
    line says WHICH skill and WHICH facet moved.
    """
    left = locked.get("skills", {})
    right = recomputed.get("skills", {})
    differences: list[str] = []
    for name in sorted(set(right) - set(left)):
        differences.append(f"{name}: present in the tree, absent from the lock")
    for name in sorted(set(left) - set(right)):
        differences.append(f"{name}: locked but no longer in the tree")
    for name in sorted(set(left) & set(right)):
        before, after = left[name], right[name]
        if before.get("description_sha256") != after.get("description_sha256"):
            differences.append(f"{name}: description changed (it is the skill's routing trigger)")
        old_sources = before.get("sources", {})
        new_sources = after.get("sources", {})
        for path in sorted(set(new_sources) - set(old_sources)):
            differences.append(f"{name}: source file added: {path}")
        for path in sorted(set(old_sources) - set(new_sources)):
            differences.append(f"{name}: source file removed: {path}")
        for path in sorted(set(old_sources) & set(new_sources)):
            if old_sources[path] != new_sources[path]:
                differences.append(f"{name}: source file changed: {path}")
        if sorted(before.get("emitted", [])) != sorted(after.get("emitted", [])):
            differences.append(
                f"{name}: emitted path set changed — locked "
                f"{sorted(before.get('emitted', []))}, found {sorted(after.get('emitted', []))}"
            )
        if sorted(before.get("disciplines", [])) != sorted(after.get("disciplines", [])):
            differences.append(
                f"{name}: the disciplines naming this skill changed — locked "
                f"{sorted(before.get('disciplines', []))}, found "
                f"{sorted(after.get('disciplines', []))}"
            )
    return differences


def write_lock(registry: dict[str, Any], path: str | Path = LOCK_PATH) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(dumps(registry), encoding="utf-8")
    return out
