"""DOCSUP-02 deterministic digest over a registry binding's resolved source/target set (D-03).

Two functions, one algorithm:

``resolve(selectors, root)``
    Expand a binding's selectors against ``root``, drop directories, dedupe, resolve-then-confine
    (a path escaping ``root``, including via a symlink inside the tree, is REFUSED before any byte
    is read), and return the set sorted by POSIX path.

``compute(paths, root)``
    Hash that set. Deliberately NOT the raw-byte concatenation of
    ``tools/adoption_apply/approval.py:57-63`` — see the comment on the loop below.

**No §4.3-4.6 normalization runs before hashing, on purpose (D-03 tradeoff).** The digest is what a
human ratifies in the review ledger, so it must agree with what that human sees in ``git diff``.
``format-on-write`` + ``polyglot_lint`` already keep the tree LF / no-BOM, so a CRLF-only re-save is
a real, reviewable change and must not be silently absorbed; normalizing here would make the digest
disagree with the raw-byte model the ledger's reviewer actually used.

Determinism rules this module obeys: no wall-clock or calendar reading anywhere, no floating-point,
and no ``set`` iteration reaching output — every returned or hashed sequence is explicitly sorted.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path

# Characters that make a selector a glob rather than a literal path. A literal selector is returned
# even when it does not exist, so `compute` can refuse it and the guard can classify it BROKEN — a
# glob that matches nothing simply contributes nothing.
_GLOB_MAGIC = ("*", "?", "[")


class MissingSourceError(ValueError):
    """A resolved path does not exist.

    Raised instead of hashing ``b""``: an absent file that hashed as empty would make a BROKEN
    binding indistinguishable from a FRESH one (research Q3).
    """


def _confine(candidate: Path, root: Path, selector: str) -> Path:
    """Resolve ``candidate`` and refuse it if it lands outside ``root``.

    Fail-closed variant of the ``tools/contract_hash/hash.py:60-63`` symlink defense: that manifest
    builder may silently skip an escaping path, but a review-obligation digest that silently drops
    a binding's file would under-report staleness, so this raises instead.
    """
    resolved = candidate.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(
            f"selector {selector!r} resolves outside the root {root.as_posix()}: "
            f"{candidate.as_posix()} -> {resolved.as_posix()}"
        )
    return resolved


def resolve(selectors: Iterable[str], root: str | Path) -> list[Path]:
    """Return the sorted, deduped, root-confined absolute paths a binding's selectors expand to."""
    base = Path(root).resolve()
    found: set[Path] = set()
    for selector in selectors:
        if any(char in selector for char in _GLOB_MAGIC):
            # Path.glob order is not guaranteed — never let it reach the output unsorted.
            candidates = [p for p in base.glob(selector) if p.is_symlink() or p.is_file()]
        else:
            candidates = [base / selector]
        for candidate in candidates:
            found.add(_confine(candidate, base, selector))
    return sorted(found, key=lambda path: path.as_posix())


def compute(paths: Iterable[Path], root: str | Path | None = None) -> str:
    """Return the 64-hex digest of the resolved set.

    ``root``, when given, is what each path is labelled relative to. Pass it: an absolute label
    would make the digest depend on the checkout location, and the ledger's digests are committed
    and re-verified in CI under a different absolute path.

    Bytes are hashed AS THEY SIT ON DISK — no §4.3-4.6 normalization runs first (D-03). The digest
    is what a human ratifies in the review ledger, so it must agree with what that human sees in
    ``git diff``; ``format-on-write`` + ``polyglot_lint`` already hold the tree at LF / no-BOM, so a
    CRLF-only re-save is a real change and must not be silently absorbed. Normalizing here would
    make the digest disagree with the raw-byte model the reviewer actually used.

    Raises ``MissingSourceError`` for any path that does not exist.
    """
    base = Path(root).resolve() if root is not None else None
    digest = hashlib.sha256()
    # Re-sort defensively: the canonical order is a property of the algorithm, never something a
    # caller has to remember to supply.
    for path in sorted(paths, key=lambda p: p.as_posix()):
        if not path.is_file():
            raise MissingSourceError(
                f"resolved path does not exist, refusing to hash as empty: {_label(path, base)}"
            )
        # ── D-03: this DELIBERATELY diverges from tools/adoption_apply/approval.py:57-63 ──────
        # That precedent concatenates raw file bytes with no path and no separator. It is safe
        # THERE only because its input is the fixed 3-element `_DRAFT_FILES` tuple. Here the input
        # is a VARIABLE, selector-expanded set, where raw concatenation is ambiguous: moving a byte
        # from one file to the next, adding an empty file, renaming a file, or swapping payloads
        # between two files all leave the concatenation — and therefore the digest — unchanged.
        # Interleaving the POSIX path and that file's OWN hex digest, each `\n`-terminated, removes
        # all four ambiguities. `AMBIGUITY_CASES` in tests/test_digest.py is the proof, and it was
        # confirmed RED against the precedent algorithm before this landed.
        # Do NOT "simplify" this back toward the precedent.
        digest.update(_label(path, base).encode("utf-8"))
        digest.update(b"\n")
        digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _label(path: Path, base: Path | None) -> str:
    """The POSIX path string hashed for ``path`` — relative to ``base`` when one was given."""
    if base is None:
        return path.as_posix()
    resolved = path.resolve()
    if resolved == base or base in resolved.parents:
        return resolved.relative_to(base).as_posix()
    return resolved.as_posix()
