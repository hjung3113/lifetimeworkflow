"""Pure route functions for the local memory web UI (Phase 16, MEM2-07, SC1 + SC3).

Every route is a pure function over **injected** plane dirs (``state_dir`` / ``agreements_dir`` /
``derived_dir``) — mirroring :func:`tools.memory_regen.inject.assemble`'s dependency-injection idiom
— and returns ``(status: int, headers: dict, body: bytes)``. No route opens a socket, reads a
wall-clock in a read path, or authors ``.memory/agreements/*`` directly: the HTTP shell (16-05) is a
trivial dispatcher over these, and unit tests exercise them against a synthetic corpus (RESEARCH
Pitfall 2 — hermetic, no real ``.memory/`` writes).

Non-negotiables enforced here:
  * All agreement writes delegate to the sanctioned :mod:`tools.agree.write` (``add`` / ``retire``),
    called module-qualified so a spy patch is observed (RESEARCH Pattern 3). ``add`` refuses a blank
    ``because`` (anti-invent, T-16-02) — the UI passes the user's reason verbatim and NEVER
    fabricates one; :class:`~tools.agree.write.AgreementRefused` is surfaced verbatim as a non-200.
  * Path/slug params are confined via :func:`tools.agree.write._target_for` (V5 slug regex + no
    ``_``-prefix + ``resolve().relative_to``) and a local ``_confine`` for state files — traversal
    is rejected (T-16-03).
  * D-16-03 surface-and-confirm: :func:`retire_agreement` reads the item's referrers from the
    injected pointer-index and returns ``409 {"orphans": [...]}`` WITHOUT writing when referrers
    exist and ``confirm`` is false. It NEVER rewrites referrer files (T-16-04) — a confirmed retire
    only flips the agreement's own ``status`` in place via the sanctioned writer.
    :func:`pointer_lookup` exposes the inline pointer-index regeneration
    (:func:`tools.memory_regen.pointer_index.build_index`) the live server runs to refresh
    ``derived_dir`` immediately before a destructive action (Pitfall 4 — correctness over cached
    freshness).
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from tools.agree import write as agree_write
from tools.harness_lint import parse_frontmatter
from tools.harness_lint.agreements import iter_agreement_files, load_agreement
from tools.memory_regen.pointer_index import build_index
from tools.memory_ui import _stamp

# The two committed state-plane files the UI lists/edits (always exactly these two).
_STATE_ITEMS = ("activeContext.md", "progress.md")

_JSON = {"Content-Type": "application/json; charset=utf-8"}
_MD = {"Content-Type": "text/markdown; charset=utf-8"}


def _json_body(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True).encode("utf-8")


def _confine(name: str, base: Path) -> Path | None:
    """Resolve ``name`` under ``base``, returning ``None`` on any traversal escape (T-16-03)."""
    base = Path(base)
    try:
        resolved_base = base.resolve()
        target = (base / name).resolve()
        target.relative_to(resolved_base)
    except (OSError, ValueError):
        return None
    return target


def list_items(*, state_dir: Path, agreements_dir: Path, show_retired: bool = False) -> tuple:
    """List the two state files plus active agreements; append retired when ``show_retired``.

    Retired agreements are appended (never interleaved) so the UI renders them below a divider.
    ``_``-prefixed and ``README`` corpus entries are excluded by ``iter_agreement_files``.
    """
    state_dir = Path(state_dir)
    state = [name for name in _STATE_ITEMS if (state_dir / name).is_file()]

    active: list[dict] = []
    retired: list[dict] = []
    for path in iter_agreement_files(agreements_dir):
        loaded = load_agreement(path)
        if loaded is None:
            continue
        frontmatter, _body = loaded
        status = frontmatter.get("status")
        entry = {"slug": path.stem, "status": status}
        if status == "retired":
            retired.append(entry)
        else:
            active.append(entry)

    agreements = active + (retired if show_retired else [])
    return 200, dict(_JSON), _json_body({"state": state, "agreements": agreements})


def view_item(item_id: str, *, state_dir: Path, agreements_dir: Path) -> tuple:
    """Return ``200`` + the editable body of a state file (or the raw markdown of an agreement).

    For a state file the frontmatter fence is stripped via the shared
    :func:`tools.harness_lint.parse_frontmatter` splitter so the UI edits **body-only** — the
    ``updated:`` stamp and sibling frontmatter keys are owned exclusively by :mod:`._stamp` and
    must never round-trip through the edit textarea (CR-01 / WR-03). Agreements are read-only and
    returned verbatim. The param is confined either way (T-16-03).
    """
    if item_id in _STATE_ITEMS:
        target = _confine(item_id, Path(state_dir))
        if target is None or not target.is_file():
            return 404, dict(_JSON), _json_body({"error": f"not found: {item_id}"})
        _frontmatter, body = parse_frontmatter(target.read_text(encoding="utf-8"))
        return 200, dict(_MD), body.lstrip("\n").encode("utf-8")

    try:
        target = agree_write._target_for(item_id, agreements_dir)
    except agree_write.AgreementRefused as exc:
        return 400, dict(_JSON), _json_body({"error": str(exc)})
    if not target.is_file():
        return 404, dict(_JSON), _json_body({"error": f"not found: {item_id}"})
    return 200, dict(_MD), target.read_bytes()


def add_agreement(
    slug: str,
    title: str,
    rule: str,
    *,
    because: str,
    related: str | None = None,
    agreements_dir: Path,
    derived_dir: Path,
) -> tuple:
    """Add an agreement via the sanctioned writer; surface ``AgreementRefused`` verbatim as non-200.

    ``because`` is passed verbatim from the UI's required field — a blank/refused value raises
    :class:`~tools.agree.write.AgreementRefused` (anti-invent, T-16-02) and NOTHING is written. The
    ``added`` provenance date is the write-path wall-clock (mirrors the ``/agree`` CLI); no
    read-path clock is involved. ``derived_dir`` is threaded for signature symmetry with
    :func:`retire_agreement` (future slug-collision surfacing).
    """
    _ = derived_dir
    try:
        path = agree_write.add(
            slug,
            title,
            rule,
            because=because,
            added=date.today().isoformat(),
            related=related,
            agreements_dir=agreements_dir,
        )
    except agree_write.AgreementRefused as exc:
        return 400, dict(_JSON), str(exc).encode("utf-8")
    return 201, dict(_JSON), _json_body({"slug": slug, "path": path.name})


def pointer_lookup(item: str, *, base_dir: Path, scan_roots: list[Path]) -> list[dict]:
    """Inline-regenerate the pointer-index and return ``item``'s referrer list (Pitfall 4).

    This is the correctness-over-cached-freshness path the live server (16-05) runs to refresh the
    derived pointer-index immediately before a destructive action: it rebuilds the index over the
    scanned roots via :func:`tools.memory_regen.pointer_index.build_index` (never trusting a
    possibly stale on-disk file) and returns the referrers keyed under ``item``.
    """
    index = build_index(base_dir=base_dir, scan_roots=scan_roots)
    return index.get(item, [])


def _referrers_for(slug: str, derived_dir: Path) -> list[dict]:
    """Read the item's referrers from the injected ``derived_dir/pointer-index.json`` (or ``[]``).

    Unit routes stay hermetic by reading the pre-regenerated index the caller placed under
    ``derived_dir``; the live server refreshes that file via :func:`pointer_lookup` /
    ``pointer_index.write`` right before calling in (D-16-03 inline-regenerate at the server seam).
    """
    index_path = Path(derived_dir) / "pointer-index.json"
    if not index_path.is_file():
        return []
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    key = f".memory/agreements/{slug}.md"
    referrers = index.get(key, [])
    return referrers if isinstance(referrers, list) else []


def retire_agreement(
    slug: str,
    *,
    agreements_dir: Path,
    derived_dir: Path,
    confirm: bool = False,
) -> tuple:
    """Surface-and-confirm retire (D-16-03/SC3): 409 with orphans unless confirmed; flip in place.

    Looks up the item's referrers first. When referrers exist and ``confirm`` is false, returns
    ``409 {"orphans": [{"file","line","kind"}, ...]}`` and writes NOTHING. On ``confirm`` (or zero
    referrers) it delegates to :func:`tools.agree.write.retire` — which flips ``status: retired`` in
    place, never deletes. Referrer files are NEVER modified by this tool (T-16-04).
    """
    try:
        agree_write._target_for(slug, agreements_dir)
    except agree_write.AgreementRefused as exc:
        return 400, dict(_JSON), str(exc).encode("utf-8")

    orphans = _referrers_for(slug, derived_dir)
    if orphans and not confirm:
        return 409, dict(_JSON), _json_body({"orphans": orphans})

    try:
        path = agree_write.retire(slug, agreements_dir=agreements_dir)
    except agree_write.AgreementRefused as exc:
        return 400, dict(_JSON), str(exc).encode("utf-8")
    return 200, dict(_JSON), _json_body({"slug": slug, "status": "retired", "path": path.name})


def save_progress(item_id: str, body_text: str, *, state_dir: Path) -> tuple:
    """Save a state file's body + refresh its quoted ``updated:`` stamp; confine to ``state_dir``.

    Only the two committed state files are editable; any path outside ``.memory/state`` is refused.
    The date is the write-path wall-clock (``_stamp`` keeps it out of the read path).
    """
    if item_id not in _STATE_ITEMS:
        return 400, dict(_JSON), _json_body({"error": f"not an editable state file: {item_id}"})
    target = _confine(item_id, Path(state_dir))
    if target is None or not target.is_file():
        return 404, dict(_JSON), _json_body({"error": f"not found: {item_id}"})
    _stamp.stamp_progress(target, body_text, today=date.today().isoformat())
    return 200, dict(_JSON), _json_body({"item": item_id, "saved": True})
