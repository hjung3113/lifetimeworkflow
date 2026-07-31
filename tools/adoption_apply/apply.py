"""apply.py — the ADOPT-05 atomic, collision-safe, idempotent manifest-apply writer.

RESEARCH's single highest-risk finding drives this module: ``tools/hooks/contract_guard.py`` is a
Claude Code ``PreToolUse`` hook — it fires ONLY on Claude's own Write/Edit tool calls, never on a
bare Python ``os.replace()``/``os.link()`` invocation. A caller that invokes this module directly
(bare CLI, CI, non-Claude-Code automation) has NO Claude hook anywhere in the loop. ``apply.py``
therefore duplicates the constitution-plane check as an explicit, structural, in-process
precondition — :func:`refuse_if_constitution`, reusing ``tools.hooks.contract_guard.
CONSTITUTION_GLOBS`` as DATA (never re-derived) — called at the START of :func:`apply_disposition`,
before any ``open()``/``os.link()``/``os.replace()`` call, for EVERY disposition branch, not cached
once per batch. A second, independent structural control, :func:`refuse_if_outside_root`, confines
discovery/draft-mode writes (ADOPT-05 clause 1) to a given task artifact root — the peer control
`/adopt draft` (Plan 27-06's ``cli.py``) calls before writing ``inventory.json``/``plan.json``/
``manifest.json``.

Two publish idioms, each a complete, self-contained, already-inlined implementation of the same
durable-write sequence (``tempfile.mkstemp`` in the target's own directory -> write/flush/fsync ->
publish -> directory fsync -> ``finally: os.unlink(tmp)``), per 27-RESEARCH's "Don't Hand-Roll"
guidance:

* :func:`atomic_create` — ``os.link``-based; raises ``FileExistsError`` -> :class:`CollisionError`
  on an existing target. Never silently overwrites. Used for the ``create`` disposition, where a
  target is NOT expected to exist yet.
* :func:`_atomic_replace` — ``os.replace``-based. Used ONLY by :func:`_apply_marker_merge`, where a
  marker-merge target already exists by definition (``AGENTS.md``/``CLAUDE.md``/
  ``.claude/settings.json`` always pre-exist in a real target tree).

Marker-merge for the 3 ``MARKER_CAPABLE`` destinations reuses ``tools.harness_emit.merge``'s
``splice_managed_block``/``merge_settings`` verbatim — no second fence/marker scheme.

:func:`apply_manifest` iterates ``manifest["dispositions"]`` ONLY (never ``excluded[]``, never a
destination absent from both) and is TOTAL over the 6-value ``DISPOSITION_ENUM`` — any other value
raises :class:`UnknownDispositionError` rather than silently defaulting to ``create``.

No arbitrary command execution: this module never builds a ``subprocess`` argv from manifest/draft
content — in fact it never calls ``subprocess`` at all.
"""

from __future__ import annotations

import fcntl
import json
import os
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from tools.adoption_scan.destinations import DISPOSITION_ENUM, MARKER_CAPABLE, _existing_hash
from tools.harness_emit.merge import merge_settings, splice_managed_block
from tools.harness_perms import resolve_path
from tools.hooks.contract_guard import CONSTITUTION_GLOBS


class ConstitutionRefusal(ValueError):
    """Raised when a destination resolves onto the CODEOWNERS-gated constitution plane."""


class PathEscapeError(ValueError):
    """Raised when a resolved path is not the given root or a descendant of it."""


class CollisionError(ValueError):
    """Raised when ``atomic_create`` hits an existing target (the ``os.link`` collision check)."""


class UnknownDispositionError(ValueError):
    """Raised when a disposition record's ``disposition`` is outside ``DISPOSITION_ENUM``."""


class ConcurrentDriftError(ValueError):
    """Raised when a ``create`` target now exists though the manifest recorded none at draft
    time."""


class SymlinkRefusal(ValueError):
    """Raised when ``_apply_marker_merge``'s read side would have to follow a symlink at the
    destination itself — refuses reading through it rather than silently splicing in whatever
    content the symlink points at (including constitution-plane content)."""


def refuse_if_constitution(destination: str) -> None:
    """Raise :class:`ConstitutionRefusal` iff ``destination`` is on the constitution plane.

    Pure, in-process, structural — independent of any Claude ``PreToolUse`` hook. Callable as a
    bare function with no Claude tool-call event object anywhere in the chain.
    """
    if resolve_path(CONSTITUTION_GLOBS, destination) == "deny":
        raise ConstitutionRefusal(
            f"'{destination}' is on the constitution plane (contracts/ · docs/adr/ · golden/); "
            "apply.py refuses this write structurally, independent of any Claude hook."
        )


def refuse_if_outside_root(path: str | Path, root: str | Path) -> None:
    """Raise :class:`PathEscapeError` iff ``path`` does not resolve to ``root`` or a descendant.

    Resolved-path-based (``Path.resolve()``), not a string-prefix check — refuses both a direct
    out-of-root destination and a ``..``-traversal escape attempt. ADOPT-05 clause 1's structural
    control for discovery/draft-mode writes.
    """
    resolved_root = Path(root).resolve()
    resolved_path = Path(path).resolve()
    if resolved_path != resolved_root and resolved_root not in resolved_path.parents:
        raise PathEscapeError(
            f"'{path}' resolves outside the confined root '{root}' — refusing the write."
        )


def refuse_unsafe_destination(destination: str, target_root: str | Path) -> Path:
    """Single choke point: resolve, confine, and classify ``destination`` before any write.

    Closes CR-01 (constitution-plane bypass via ``.``/``..``/case-variant spellings and symlinks)
    and CR-02 (absolute-path confinement bypass — ``Path(target_root) / destination`` silently
    discards ``target_root`` when ``destination`` is absolute) by funnelling every apply-mode
    destination through ONE function, rather than trusting every call site to remember both
    ``refuse_if_constitution`` and ``refuse_if_outside_root`` independently.

    Also closes WR-05 (a directory-shaped destination crashing the ``create`` branch with an
    unhandled ``IsADirectoryError`` instead of refusing cleanly) — in all three of its classes:
    a spelling that names a directory (``"a/"``, ``"a/b/."``), one that resolves to ``target_root``
    itself, and one that resolves to an existing directory — and WR-02 (a destination whose parent
    chain is an existing FILE, which crashed ``atomic_create``'s ``mkdir`` with a raw
    ``FileExistsError``).

    1. Structural pre-check, before any filesystem call: reject an absolute ``destination`` or one
       containing a literal ``..`` path segment (not a substring — ``foo/bar..json`` is fine), or
       one whose last raw segment is empty or ``.`` — i.e. a spelling that names a directory
       rather than a file (WR-05).
    2. Resolve ``target_root / destination`` (``strict=False`` — the target need not exist yet).
    3. Confine via the existing, unchanged ``refuse_if_outside_root``.
    4. Reject a destination that resolves to ``target_root`` itself, or to an existing directory
       (WR-05) — both before the ``relative_to`` classification below, whose ``"."`` result for a
       root-equal path matches no constitution glob and is exactly what let ``"."`` through. Note
       that after step 1 the root-equality arm is reachable only via a **symlink** resolving to the
       root; every plain spelling of the root is already stopped by step 1's last-segment check.
    5. Reject a destination whose parent chain runs through an existing NON-directory (WR-02) —
       ``AGENTS.md/evil.txt`` where ``AGENTS.md`` is a file passes every check above and would
       otherwise surface as a raw ``FileExistsError`` from ``atomic_create``'s ``mkdir``.
    6. Classify the resolved, target-root-relative path against ``CONSTITUTION_GLOBS`` — always
       case-insensitively (lowering the candidate only, never the globs; RESEARCH verified
       ``Path.resolve()`` does not itself canonicalize case) — by reusing the unchanged, thin
       ``refuse_if_constitution`` wrapper (D-01).

    Returns the resolved ``target_path`` so callers reuse it instead of recomputing
    ``Path(target_root) / destination`` (which is exactly the bug this function closes).
    """
    segments = destination.replace("\\", "/").split("/")
    if Path(destination).is_absolute() or any(segment == ".." for segment in segments):
        raise PathEscapeError(
            f"'{destination}' is absolute or contains a '..' path segment — refusing the write "
            "before any resolution or filesystem call."
        )
    # WR-05, structural: the ONLY check that sees the trailing-slash class. `"newdir/"` resolves to
    # `target_root/newdir` — neither root-equal nor an existing directory — so no resolve-based
    # check can catch it, and a manifest asking for a directory would silently create a FILE.
    if segments[-1] in ("", "."):
        raise PathEscapeError(
            f"'{destination}' names a directory, not a file (its last path segment is empty or "
            "'.') — refusing the write before any resolution or filesystem call."
        )

    target_path = (Path(target_root) / destination).resolve(strict=False)
    refuse_if_outside_root(target_path, target_root)
    resolved_root = Path(target_root).resolve()

    if target_path == resolved_root:
        raise PathEscapeError(
            f"'{destination}' resolves to the target root itself — a destination must be a proper "
            "descendant of it, not the root directory."
        )
    if target_path.is_dir():
        raise PathEscapeError(
            f"'{destination}' resolves to an existing directory — refusing the write."
        )

    # WR-02: a destination whose parent chain runs THROUGH an existing non-directory — e.g.
    # `AGENTS.md/evil.txt` where `AGENTS.md` is a file — is directory-shaped to none of the checks
    # above (relative, no `..`, last segment `evil.txt`, not root-equal, and `is_dir()` is False
    # precisely BECAUSE the parent is a file). It reached `atomic_create`, whose
    # `parent.mkdir(parents=True)` raised a bare `FileExistsError` (`NotADirectoryError` on some
    # platforms) that no caller named. Refuse it here instead, per D-01: unsafe destinations are
    # decided at the choke point, before any filesystem write. The walk stops at the target root,
    # which confinement has already established as an ancestor.
    for ancestor in target_path.parents:
        if ancestor == resolved_root:
            break
        if ancestor.exists() and not ancestor.is_dir():
            raise PathEscapeError(
                f"'{destination}' has an existing non-directory ancestor '{ancestor.name}' — "
                "refusing the write."
            )

    # The `\` fold matches step 1's, so the pre-check and the classification see ONE normalization
    # (IN-02). On POSIX `docs\glossary.md` is a single file whose NAME contains a backslash — a
    # different file, and harmless — but on Windows that spelling IS `docs/glossary.md`, a
    # constitution member, and a deny domain that depends on which OS reads the manifest is not a
    # deny domain.
    relative = target_path.relative_to(resolved_root).as_posix().replace("\\", "/")
    refuse_if_constitution(relative.lower())

    return target_path


def atomic_create(path: Path, payload: bytes) -> None:
    """Create ``path`` exactly once via durable temp + hard-link publication.

    Writes ``payload`` (raw ``bytes``) to a same-directory temp file, flushes and fsyncs it, then
    publishes via ``os.link`` -> fsyncs the containing directory -> unlinks the temp file in a
    ``finally``. ``os.link`` raises ``FileExistsError`` on an existing target ->
    :class:`CollisionError`; ``os.replace`` (which silently overwrites) is never used here.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise CollisionError(f"target already exists: {path}") from exc
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _atomic_replace(path: Path, payload: bytes) -> None:
    """Durably replace ``path`` with a same-directory temporary file.

    Writes ``payload`` (raw ``bytes``) to a same-directory temp file, flushes and fsyncs it, then
    publishes via ``os.replace`` -> fsyncs the containing directory, unlinking the temp file on any
    exception. Only used by :func:`_apply_marker_merge`, where the target already exists by
    definition.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _read_target_no_symlink(path: Path) -> str | None:
    """Read ``path`` as UTF-8 text, refusing to follow a symlink at the destination itself.

    Returns ``None`` when ``path`` does not exist yet (same semantics as the previous
    ``target_path.is_file()`` guard). Raises :class:`SymlinkRefusal` when the final path component
    is a symlink (``os.O_NOFOLLOW`` -> ``OSError`` — verified live in RESEARCH to raise
    ``errno 62``/"Too many levels of symbolic links" on this platform) — defense in depth against
    constitution-plane (or any other) content being silently read through a symlinked
    marker-capable target and spliced into a foreign file.
    """
    try:
        descriptor = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise SymlinkRefusal(
            f"refusing to read through a symlink at marker-merge destination '{path}'"
        ) from exc
    with os.fdopen(descriptor, "rb") as handle:
        return handle.read().decode("utf-8")


def lock_sidecar_for(destination: str) -> str:
    """Return the ``.lock`` sidecar path ``_apply_marker_merge`` would create for ``destination``.

    Pure, POSIX-relative, no filesystem access — reproduces ``_apply_marker_merge``'s
    ``target_path.with_name(f".{target_path.name}.lock")`` rule for a repo-relative destination
    string rather than an already-resolved ``Path``, so it is checkable both against the naming
    RULE and (in tests) against what the writer actually creates on disk.
    """
    posix_destination = PurePosixPath(destination)
    return str(posix_destination.with_name(f".{posix_destination.name}.lock"))


def expected_lock_sidecars(destinations: Iterable[str]) -> set[str]:
    """The set of ``.lock`` sidecars marker-merge creates for the ``MARKER_CAPABLE`` members of
    ``destinations``.

    A destination outside ``MARKER_CAPABLE`` (imported from ``destinations.py``, never retyped)
    contributes no sidecar — only the 3 marker-merge destinations ever acquire one.
    """
    return {
        lock_sidecar_for(destination)
        for destination in destinations
        if destination in MARKER_CAPABLE
    }


# OBS-D-04 (51-BASELINE-EVIDENCE.md) — purpose 4: sidecars are DECLARED, never unlinked (D-15);
# comparison scope is phase-local (D-21). Plan 05's apply comparison imports this frozenset as its
# allowlist for the matches/unexpected_paths computation rather than recomputing the naming rule.
HARNESS_MANAGED_LOCK_SIDECARS: frozenset[str] = frozenset(expected_lock_sidecars(MARKER_CAPABLE))


def _apply_marker_merge(destination: str, target_path: Path, block_body: str = "") -> None:
    """Merge the harness-managed content into ``target_path`` and publish it atomically.

    ``.json`` destinations (``.claude/settings.json``) go through ``merge_settings``; every other
    marker-capable destination (``AGENTS.md``/``CLAUDE.md``) goes through ``splice_managed_block``
    with ``block_body`` as the fenced content. Both merge functions are already documented
    idempotent — a second call with the same input reproduces the same output byte-for-byte.

    The entire read-merge-write sequence is guarded by an ``fcntl.flock``-held sidecar lock
    (mirroring ``batch.py::update_status``'s exact idiom) so two concurrent ``apply`` invocations
    against the same target never interleave (WR-01). The read itself refuses to follow a symlink
    at the destination (``_read_target_no_symlink``).

    # OBS-D-04 / D-16 (52-CONTEXT.md): a visible signal beats a quiet resume. Scope note: with
    # D-15's no-unlink rule this predicate cannot distinguish a normal re-run from a
    # crash-interrupted one — it reports PROVENANCE, not staleness. A real staleness probe
    # (recorded owner pid + liveness, or mtime vs run start) is unbuilt on purpose (NG-01, no
    # observation behind it).
    """
    target_path = Path(target_path)
    lock_path = target_path.with_name(f".{target_path.name}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    pre_existed = lock_path.exists()
    with lock_path.open("a+b") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            if pre_existed:
                print(
                    f"apply: lock sidecar from a prior run at {lock_path} — acquired, not "
                    "silently reused (sidecars are never unlinked, D-15)",
                    file=sys.stderr,
                )
        except (BlockingIOError, OSError):
            # A genuinely held lock (another holder currently inside the critical section) —
            # wait for it, exactly as before. No prior-run report here: this branch means the
            # lock is CURRENTLY held, not merely that a sidecar was left over from a prior run.
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        if destination.endswith(".json"):
            existing_text = _read_target_no_symlink(target_path)
            existing: dict[str, Any] = (
                json.loads(existing_text) if existing_text is not None else {}
            )
            merged = merge_settings(existing)
            payload = (json.dumps(merged, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        else:
            existing_text = _read_target_no_symlink(target_path)
            merged_text = splice_managed_block(existing_text or "", block_body)
            payload = merged_text.encode("utf-8")
        _atomic_replace(target_path, payload)


def apply_disposition(
    record: dict[str, Any],
    target_root: str | Path,
    *,
    payload: bytes = b"",
    block_body: str = "",
) -> dict[str, str]:
    """Dispatch a single ``dispositionRecord`` to the correct writer, or refuse the write.

    ``refuse_unsafe_destination(destination, target_root)`` is called FIRST — before any branch,
    before any ``open()``/``os.link()``/``os.replace()`` call — so a destination that is absolute,
    ``..``-escaping, or resolves onto the constitution plane (including via a symlink or a
    case-variant spelling) is refused regardless of its disposition value (CR-01/CR-02). The
    returned, already-resolved ``target_path`` is reused by every branch below instead of being
    recomputed. Returns ``{"destination", "disposition", "status"}`` where ``status`` is
    ``"applied"`` or ``"skipped"``. Raises on any refusal/error rather than returning a refused
    status — the caller (``apply_manifest``) decides which exceptions to bucket vs. propagate.
    """
    destination = record["destination"]
    disposition_value = record["disposition"]
    target_path = refuse_unsafe_destination(destination, target_root)

    if disposition_value not in DISPOSITION_ENUM:
        raise UnknownDispositionError(
            f"unknown disposition {disposition_value!r} for destination {destination!r}"
        )

    if disposition_value == "create":
        if target_path.exists():
            current_hash = _existing_hash(target_path)
            raise ConcurrentDriftError(
                f"concurrent target drift: '{destination}' now exists (sha256={current_hash}) but "
                "the manifest recorded no existing target for a 'create' disposition at draft time"
            )
        atomic_create(target_path, payload)
        return {"destination": destination, "disposition": disposition_value, "status": "applied"}

    if disposition_value == "marker-merge":
        if destination not in MARKER_CAPABLE:
            raise ValueError(
                f"'{destination}' is not marker-capable; the disposition manifest is malformed"
            )
        _apply_marker_merge(destination, target_path, block_body)
        return {"destination": destination, "disposition": disposition_value, "status": "applied"}

    # preserve / conflict / derived-regenerate / human-ratification-required: never written by
    # apply.py. human-ratification-required destinations are expected to already be refused above
    # (they live on the constitution plane by construction); this is a belt-and-suspenders no-op
    # for the case where one somehow is not.
    return {"destination": destination, "disposition": disposition_value, "status": "skipped"}


def apply_manifest(
    manifest: dict[str, Any],
    target_root: str | Path,
    *,
    payloads: dict[str, bytes] | None = None,
    block_bodies: dict[str, str] | None = None,
) -> dict[str, list[str]]:
    """Apply every record in ``manifest["dispositions"]`` (never ``excluded[]``) against
    ``target_root``.

    Iterates ``dispositions[]`` ONLY, sorted by destination for deterministic output ordering.
    ``ConstitutionRefusal`` is caught per-record and bucketed into ``"refused"`` — a refusal, not a
    fault, so a single refused destination does not abort the rest of the apply cycle. Every other
    exception
    (``ConcurrentDriftError``, ``UnknownDispositionError``, ``CollisionError``,
    ``PathEscapeError``, a malformed marker-capable destination) propagates immediately.

    **Partial application is therefore reachable** (AD-05): a record that raises after earlier
    records have been written leaves those earlier writes committed. Because records are applied in
    sorted-destination order the surviving state is deterministic, but it is not a transaction —
    the caller re-runs the batch after fixing the manifest, relying on ``atomic_create``'s
    collision check rather than on rollback. WR-05 widened what raises ``PathEscapeError`` from
    "hostile spelling" to "a plausible manifest row asking for a directory", so this is now
    reachable from an honest mistake, not only from an attack.

    Note (AD-04): the CLI maps ``CollisionError`` and ``ConcurrentDriftError`` to the same exit 1
    as a routine path refusal, so the integrity-fault-vs-refusal distinction drawn here is NOT
    preserved in the process exit code — only in the exception type seen by an in-process caller.

    Returns ``{"applied": [...], "skipped": [...], "refused": [...]}`` — destinations only.
    """
    target_root = Path(target_root)
    payloads = payloads or {}
    block_bodies = block_bodies or {}
    summary: dict[str, list[str]] = {"applied": [], "skipped": [], "refused": []}

    for record in sorted(manifest["dispositions"], key=lambda r: r["destination"]):
        destination = record["destination"]
        try:
            result = apply_disposition(
                record,
                target_root,
                payload=payloads.get(destination, b""),
                block_body=block_bodies.get(destination, ""),
            )
        except ConstitutionRefusal:
            summary["refused"].append(destination)
            continue
        summary["applied" if result["status"] == "applied" else "skipped"].append(destination)

    return summary
