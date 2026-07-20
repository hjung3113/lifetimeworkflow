"""test_constitution_refusal.py — proves apply.py's constitution-plane refusal is structural.

RESEARCH's Pitfall 1: a test suite that only exercises ``apply.py`` via a simulated Claude
``PreToolUse`` tool-call event never proves the refusal is independent of that hook. Every test
here calls ``apply`` functions as bare Python — no Claude event object anywhere in the chain.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tools.adoption_apply import apply

# CR-01 adversarial destinations: all four resolve onto the constitution plane
# (contracts/) but only the first was caught by the raw-string, case-sensitive,
# non-``..``-collapsing `refuse_if_constitution` that shipped in Phase 27.
HOSTILE_DESTINATIONS = [
    "contracts/widget.schema.json",
    "./contracts/widget.schema.json",
    "a/../contracts/widget.schema.json",
    "CONTRACTS/widget.schema.json",
]


@pytest.mark.parametrize(
    "destination",
    [
        "contracts/widget.schema.json",
        "docs/adr/0099-example.md",
        "golden/y/baseline.verified.tsv",
    ],
)
def test_refuses_before_mutation(tmp_path, monkeypatch, destination):
    """Zero-call spy proof: refused BEFORE any open()/os.link()/os.replace() call."""
    open_spy = MagicMock(wraps=os.open)
    link_spy = MagicMock(wraps=os.link)
    replace_spy = MagicMock(wraps=os.replace)
    monkeypatch.setattr(os, "open", open_spy)
    monkeypatch.setattr(os, "link", link_spy)
    monkeypatch.setattr(os, "replace", replace_spy)

    record = {"destination": destination, "disposition": "create"}

    with pytest.raises(apply.ConstitutionRefusal):
        apply.apply_disposition(record, tmp_path, payload=b"content")

    assert open_spy.call_count == 0
    assert link_spy.call_count == 0
    assert replace_spy.call_count == 0
    # The refused destination must never land on disk under target_root either.
    assert not (tmp_path / destination).exists()


def test_refuses_bare_cli_invocation():
    """Bare function call, no Claude tool-call event object anywhere in the chain."""
    with pytest.raises(apply.ConstitutionRefusal):
        apply.refuse_if_constitution("contracts/example.schema.json")


def test_non_constitution_destination_allowed():
    apply.refuse_if_constitution("src/widget.py")  # must not raise


def test_atomic_create_collision(tmp_path):
    target = tmp_path / "src" / "widget.py"
    apply.atomic_create(target, b"first\n")
    with pytest.raises(apply.CollisionError):
        apply.atomic_create(target, b"second\n")
    assert target.read_bytes() == b"first\n"


def test_refuse_if_outside_root_allows_in_root(tmp_path):
    root = tmp_path / "artifacts" / "adoption" / "batch1"
    root.mkdir(parents=True)
    apply.refuse_if_outside_root(root / "inventory.json", root)  # must not raise


# --- CR-01/CR-02 (27.1-01) — refuse_unsafe_destination choke point -----------------------------
#
# PATH_ESCAPE_DESTINATIONS are built PER-TEST from `tmp_path`, never as literal real-world paths
# (e.g. `/etc/passwd`), so a pre-fix RED failure can never be a coincidence of what already exists
# on the host filesystem (27.1-RESEARCH.md, Pitfall re: ConcurrentDriftError short-circuiting).
# `_ESCAPE_ABSOLUTE`/`_ESCAPE_TRAVERSAL` are sentinel kinds resolved against `tmp_path` inside each
# test via `_resolve_destination_kind`.
_ESCAPE_ABSOLUTE = "__escape_absolute__"
_ESCAPE_TRAVERSAL = "__escape_traversal__"
PATH_ESCAPE_KINDS = [_ESCAPE_ABSOLUTE, _ESCAPE_TRAVERSAL]


def _resolve_destination_kind(tmp_path, kind):
    """Resolve a HOSTILE_DESTINATIONS literal or a PATH_ESCAPE_KINDS sentinel to a real string."""
    if kind == _ESCAPE_ABSOLUTE:
        # Absolute, guaranteed-nonexistent — never a real system path.
        return str(tmp_path / "outside-marker" / "widget.txt")
    if kind == _ESCAPE_TRAVERSAL:
        # Escapes one level above target_root, guaranteed-nonexistent.
        return "../outside-marker/widget.txt"
    return kind


@pytest.mark.parametrize("kind", HOSTILE_DESTINATIONS + PATH_ESCAPE_KINDS)
def test_refuse_unsafe_destination_rejects_hostile_input(tmp_path, kind):
    """RED pre-fix via AttributeError: `apply.refuse_unsafe_destination` does not exist yet.

    Post-fix: every hostile/escape destination is refused by the new choke point directly, with
    no dependency on `apply_disposition`'s dispatch — proves the primitive itself is correct in
    isolation, independent of any call site remembering to invoke it.
    """
    destination = _resolve_destination_kind(tmp_path, kind)
    with pytest.raises((apply.ConstitutionRefusal, apply.PathEscapeError)):
        apply.refuse_unsafe_destination(destination, tmp_path)


def test_refuse_unsafe_destination_allows_legitimate_input(tmp_path):
    """Negative control: a genuinely non-constitution, in-root destination must not be refused."""
    result = apply.refuse_unsafe_destination("src/widget.py", tmp_path)
    assert Path(tmp_path).resolve() in result.parents or result == Path(tmp_path).resolve()


@pytest.mark.parametrize("destination", HOSTILE_DESTINATIONS)
def test_apply_disposition_refuses_hostile_destinations_end_to_end(
    tmp_path, monkeypatch, destination
):
    """RED pre-fix via a REAL write: `apply_disposition` only calls the raw-string, case-sensitive,
    non-``..``-collapsing `refuse_if_constitution` today, so `a/../contracts/...` and
    `CONTRACTS/...` are NOT refused — the zero-write spy's `call_count > 0` is the pre-fix failure,
    proving CR-01 (not an AttributeError, since `apply_disposition` itself already exists).
    """
    open_spy = MagicMock(wraps=os.open)
    link_spy = MagicMock(wraps=os.link)
    replace_spy = MagicMock(wraps=os.replace)
    monkeypatch.setattr(os, "open", open_spy)
    monkeypatch.setattr(os, "link", link_spy)
    monkeypatch.setattr(os, "replace", replace_spy)

    record = {"destination": destination, "disposition": "create"}
    with pytest.raises((apply.ConstitutionRefusal, apply.PathEscapeError)):
        apply.apply_disposition(record, tmp_path, payload=b"content")

    assert open_spy.call_count == 0
    assert link_spy.call_count == 0
    assert replace_spy.call_count == 0


@pytest.mark.parametrize("kind", PATH_ESCAPE_KINDS)
def test_apply_disposition_refuses_path_escape_destinations_end_to_end(tmp_path, monkeypatch, kind):
    """RED pre-fix via a REAL unconfined write (CR-02), not via the wrong exception type.

    `Path(target_root) / destination` with an absolute `destination` silently discards
    `target_root` (pathlib's documented absolute-override join behavior); since the synthetic
    destination is guaranteed not to already exist, `target_path.exists()` is False, so
    `atomic_create` actually writes the file outside `target_root` pre-fix — the spy
    `call_count > 0` assertion is what fails, never a coincidental `/etc/passwd` short-circuit.
    """
    destination = _resolve_destination_kind(tmp_path, kind)
    open_spy = MagicMock(wraps=os.open)
    link_spy = MagicMock(wraps=os.link)
    replace_spy = MagicMock(wraps=os.replace)
    monkeypatch.setattr(os, "open", open_spy)
    monkeypatch.setattr(os, "link", link_spy)
    monkeypatch.setattr(os, "replace", replace_spy)

    record = {"destination": destination, "disposition": "create"}
    with pytest.raises(apply.PathEscapeError):
        apply.apply_disposition(record, tmp_path, payload=b"content")

    assert open_spy.call_count == 0
    assert link_spy.call_count == 0
    assert replace_spy.call_count == 0


# --- WR-05 (27.2-01) — directory-shaped destinations refuse, never IsADirectoryError -----------
#
# Each row carries the fragment identifying WHICH guard must fire, so a row cannot drift onto a
# different check and still pass (WR-01: the three `(a)` rows below were all being intercepted by
# the structural pre-check, leaving the root-equality branch with no test of its own).
#   (a) structural pre-check on the raw spelling — the last segment is empty or `.`. This is the
#       ONLY check that sees the trailing-slash class: `(root / "newdir/").resolve()` is
#       `root/newdir`, neither root-equal nor an existing directory, so a manifest asking for a
#       directory would otherwise silently create a FILE named `newdir`.
#   (b) resolves to target_root itself — reachable ONLY via a symlink pointing at the root; every
#       plain spelling of "the root" (`.`, `./`, ``) is stopped by (a) two checks earlier.
#   (c) an existing directory — the `is_dir()` check.
# `src/` and `selflink` are created by the test itself; `a/`, `b/`, `newdir/` deliberately never
# exist.
DIRECTORY_SHAPED_DESTINATIONS = [
    # (a) structural: last raw segment is empty or `.`
    ("root_dot", ".", "names a directory"),
    ("root_dot_slash", "./", "names a directory"),
    ("root_empty", "", "names a directory"),
    ("trailing_slash_nonexistent", "a/", "names a directory"),
    ("trailing_slash_newdir", "newdir/", "names a directory"),
    ("trailing_dot_nonexistent", "a/b/.", "names a directory"),
    ("existing_dir_trailing_slash", "src/", "names a directory"),
    # (b) resolves to the target root itself
    ("symlink_to_root", "selflink", "target root itself"),
    # (c) an existing directory
    ("existing_dir", "src", "existing directory"),
    ("existing_dir_dot_prefixed", "./src", "existing directory"),
]


def _seed_directory_shaped_fixtures(tmp_path):
    """Create the on-disk shapes the `(b)` and `(c)` rows need."""
    (tmp_path / "src").mkdir(exist_ok=True)
    selflink = tmp_path / "selflink"
    if not selflink.exists():
        os.symlink(str(tmp_path), str(selflink))


@pytest.mark.parametrize(
    ("case_name", "destination", "expected_guard"),
    DIRECTORY_SHAPED_DESTINATIONS,
    ids=[case_name for case_name, _, _ in DIRECTORY_SHAPED_DESTINATIONS],
)
def test_refuse_unsafe_destination_rejects_directory_shaped(
    tmp_path, case_name, destination, expected_guard
):
    """WR-05: a destination that names a directory is refused at the choke point (D-02:
    `PathEscapeError`, the existing refusal exception — not a new one).

    WR-01: `expected_guard` pins each row to the specific check that must reject it, so deleting
    any one guard turns its own rows red instead of letting an earlier check absorb them.
    """
    _seed_directory_shaped_fixtures(tmp_path)

    with pytest.raises(apply.PathEscapeError) as excinfo:
        apply.refuse_unsafe_destination(destination, tmp_path)

    message = str(excinfo.value)
    assert f"'{destination}'" in message, case_name
    assert expected_guard in message, f"{case_name}: refused by the wrong guard — {message}"


def test_refuse_unsafe_destination_still_allows_file_destinations(tmp_path):
    """D-03 negative control: the WR-05 guard must not over-refuse. A file inside an existing
    directory, a file whose parent chain does not exist yet, and a root-level file all stay
    allowed."""
    (tmp_path / "src").mkdir(exist_ok=True)
    root = Path(tmp_path).resolve()

    for destination in ("src/widget.py", "a/b/c.txt", "AGENTS.md"):
        result = apply.refuse_unsafe_destination(destination, tmp_path)
        assert root in result.parents, destination


@pytest.mark.parametrize("destination", [".", "newdir/"], ids=["root_dot", "trailing_slash_newdir"])
def test_apply_disposition_refuses_directory_shaped_destination(tmp_path, monkeypatch, destination):
    """End-to-end: `PathEscapeError`, never `IsADirectoryError`, and zero writes.

    The `"newdir/"` row matters most — pre-fix it is not directory-shaped to any resolve-based
    check, so `apply_disposition` silently creates a FILE named `newdir`.
    """
    open_spy = MagicMock(wraps=os.open)
    link_spy = MagicMock(wraps=os.link)
    replace_spy = MagicMock(wraps=os.replace)
    monkeypatch.setattr(os, "open", open_spy)
    monkeypatch.setattr(os, "link", link_spy)
    monkeypatch.setattr(os, "replace", replace_spy)

    record = {"destination": destination, "disposition": "create"}
    with pytest.raises(apply.PathEscapeError):
        apply.apply_disposition(record, tmp_path, payload=b"x")

    assert open_spy.call_count == 0
    assert link_spy.call_count == 0
    assert replace_spy.call_count == 0
    assert not (tmp_path / "newdir").exists()


def test_symlink_into_contracts_is_refused(tmp_path, monkeypatch):
    """SC-1 symlink case: a symlink whose RESOLVED target lands inside `contracts/` is refused,
    proving the classification runs against the resolved path, not the raw destination string.

    RED pre-fix via a REAL write: today's `refuse_if_constitution(destination)` sees only the raw
    string `"innocuous/alias.json"`, which does not match any constitution glob, so the write
    proceeds — the spy `call_count > 0` assertion is what fails pre-fix.
    """
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir()
    innocuous_dir = tmp_path / "innocuous"
    innocuous_dir.mkdir()
    symlink_path = innocuous_dir / "alias.json"
    symlink_path.symlink_to(contracts_dir / "victim.json")

    open_spy = MagicMock(wraps=os.open)
    link_spy = MagicMock(wraps=os.link)
    replace_spy = MagicMock(wraps=os.replace)
    monkeypatch.setattr(os, "open", open_spy)
    monkeypatch.setattr(os, "link", link_spy)
    monkeypatch.setattr(os, "replace", replace_spy)

    record = {"destination": "innocuous/alias.json", "disposition": "create"}
    with pytest.raises((apply.ConstitutionRefusal, apply.PathEscapeError)):
        apply.apply_disposition(record, tmp_path, payload=b"content")

    assert open_spy.call_count == 0
    assert link_spy.call_count == 0
    assert replace_spy.call_count == 0
