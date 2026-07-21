"""D-03 digest — the adversarial ambiguity table plus the negative controls.

``AMBIGUITY_CASES`` is the load-bearing artifact: each row is a PAIR of file trees that the
precedent algorithm at ``tools/adoption_apply/approval.py:57-63`` (raw ``h.update(read_bytes())``
in a loop — no path, no separator) hashes IDENTICALLY, and that ``digest.compute`` must therefore
distinguish. The table was authored and confirmed RED against a precedent-shaped ``compute`` BEFORE
the real algorithm landed; the verbatim failure output is recorded in ``28-02-SUMMARY.md``.

The property tests are the other half and matter just as much: a digest that distinguishes
*everything* — including selector spelling and glob iteration order — is as useless as one that
distinguishes nothing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.docs_guard.digest import MissingSourceError, compute, resolve

# ── helpers ──────────────────────────────────────────────────────────────────────────────────


def _write_tree(root: Path, tree: dict[str, bytes]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for rel, payload in tree.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    return root


def _digest_of_tree(root: Path, tree: dict[str, bytes]) -> str:
    _write_tree(root, tree)
    return compute(resolve(["**/*.md"], root), root=root)


# ── the adversarial table: pairs raw concatenation cannot tell apart ──────────────────────────

AMBIGUITY_CASES: tuple[tuple[str, dict[str, bytes], dict[str, bytes]], ...] = (
    # A byte moves from one file to the next: concatenation is b"xyz" both times.
    ("byte_move", {"a.md": b"xy", "b.md": b"z"}, {"a.md": b"x", "b.md": b"yz"}),
    # An empty file appears: concatenation is b"x" both times.
    ("empty_file_added", {"a.md": b"x"}, {"a.md": b"x", "b.md": b""}),
    # A file is renamed, contents untouched: concatenation is b"x" both times.
    ("rename_only", {"a.md": b"x"}, {"b.md": b"x"}),
    # The whole payload swaps between two files: concatenation is b"xy" both times.
    ("split_across_files", {"a.md": b"", "b.md": b"xy"}, {"a.md": b"xy", "b.md": b""}),
)


@pytest.mark.parametrize(
    ("case", "tree_a", "tree_b"),
    AMBIGUITY_CASES,
    ids=[row[0] for row in AMBIGUITY_CASES],
)
def test_ambiguity_case_is_distinguished(
    tmp_path: Path, case: str, tree_a: dict[str, bytes], tree_b: dict[str, bytes]
) -> None:
    """Each row must produce two DIFFERENT digests (raw concatenation produces two equal ones)."""
    digest_a = _digest_of_tree(tmp_path / f"{case}_a", tree_a)
    digest_b = _digest_of_tree(tmp_path / f"{case}_b", tree_b)

    assert digest_a != digest_b, (
        f"{case}: digests are equal but must differ — raw-byte concatenation "
        f"(approval.py:57-63) cannot see this change on a variable selector-expanded set"
    )


# ── negative controls: what must NOT change the digest ────────────────────────────────────────


def test_digest_is_deterministic(tmp_path: Path) -> None:
    root = _write_tree(tmp_path / "repo", {"docs/a.md": b"alpha\n", "docs/b.md": b"bravo\n"})
    paths = resolve(["docs/**/*"], root)

    assert compute(paths, root=root) == compute(paths, root=root)


def test_digest_ignores_selector_spelling(tmp_path: Path) -> None:
    """Selector spelling, duplication and ordering must not move the digest — the RESOLVED SET is
    what is hashed, not the way it was requested."""
    root = _write_tree(tmp_path / "repo", {"docs/a.md": b"alpha\n", "docs/n/b.md": b"bravo\n"})

    plain = resolve(["docs/**/*"], root)
    redundant = resolve(["docs/a.md", "docs/**/*", "docs/a.md"], root)

    assert plain == redundant, "a redundant/duplicated selector must resolve to the same set"
    assert compute(plain, root=root) == compute(redundant, root=root)


def test_digest_ignores_glob_iteration_order(tmp_path: Path) -> None:
    """The sort lives INSIDE ``compute``, not in the caller: a shuffled input list must hash the
    same as the sorted one (``Path.glob`` order is not guaranteed)."""
    root = _write_tree(
        tmp_path / "repo", {"docs/a.md": b"a\n", "docs/b.md": b"b\n", "docs/c.md": b"c\n"}
    )
    ordered = resolve(["docs/**/*"], root)
    shuffled = list(reversed(ordered))

    assert shuffled != ordered, "fixture sanity: the shuffled list must actually differ in order"
    assert compute(shuffled, root=root) == compute(ordered, root=root)


# ── negative controls: what must change the digest ────────────────────────────────────────────


def test_digest_no_normalization_applied(tmp_path: Path) -> None:
    """D-03 tradeoff: NO §4.3-4.6 normalization runs before hashing, so a CRLF-only re-save is a
    real digest change. The digest must agree with what a human sees in ``git diff``."""
    lf = _digest_of_tree(tmp_path / "lf", {"a.md": b"one\ntwo\n"})
    crlf = _digest_of_tree(tmp_path / "crlf", {"a.md": b"one\r\ntwo\r\n"})

    assert lf != crlf, "a CRLF-only re-save must move the digest (no pre-hash normalization)"


# ── fail-closed: absent and escaping paths ────────────────────────────────────────────────────


def test_compute_raises_on_missing_path(tmp_path: Path) -> None:
    """A resolved path that does not exist is NEVER hashed as empty — that is what lets the guard
    classify BROKEN instead of silently reporting FRESH (research Q3)."""
    root = _write_tree(tmp_path / "repo", {"docs/a.md": b"alpha\n"})
    paths = resolve(["docs/a.md", "docs/gone.md"], root)

    with pytest.raises(MissingSourceError) as excinfo:
        compute(paths, root=root)

    assert "docs/gone.md" in str(excinfo.value), "the error must name the missing path"


def test_compute_missing_path_is_not_hashed_as_empty(tmp_path: Path) -> None:
    """The specific silent-failure shape: an absent file must NOT collide with a present empty
    one. (If it merely raised on some other ground this control would still hold.)"""
    root = _write_tree(tmp_path / "repo", {"docs/a.md": b"alpha\n"})
    present_empty = _write_tree(tmp_path / "empty", {"docs/a.md": b"alpha\n", "docs/gone.md": b""})

    with pytest.raises(MissingSourceError):
        compute(resolve(["docs/a.md", "docs/gone.md"], root), root=root)

    # The comparison tree hashes fine — proving the refusal above is about absence, not shape.
    assert compute(resolve(["docs/**/*"], present_empty), root=present_empty)


def test_resolve_refuses_escape(tmp_path: Path) -> None:
    """A selector resolving outside ``root`` is refused before any ``read_bytes()``."""
    root = _write_tree(tmp_path / "repo", {"docs/a.md": b"alpha\n"})
    (tmp_path / "outside.md").write_bytes(b"secret\n")

    with pytest.raises(ValueError) as excinfo:
        resolve(["../outside.md"], root)

    assert "outside" in str(excinfo.value)


def test_resolve_refuses_symlink_pointing_outside(tmp_path: Path) -> None:
    """A symlink INSIDE the tree pointing outside it is refused, not followed — mirroring the
    ``tools/contract_hash/hash.py:60-63`` symlink defense, but fail-closed (raise, not skip)."""
    root = _write_tree(tmp_path / "repo", {"docs/a.md": b"alpha\n"})
    secret = tmp_path / "outside.md"
    secret.write_bytes(b"secret\n")
    link = root / "docs" / "link.md"
    try:
        link.symlink_to(secret)
    except (OSError, NotImplementedError):  # pragma: no cover - platform without symlinks
        pytest.skip("symlink creation unsupported on this platform")

    with pytest.raises(ValueError) as excinfo:
        resolve(["docs/**/*"], root)

    assert "link.md" in str(excinfo.value) or "outside" in str(excinfo.value)
