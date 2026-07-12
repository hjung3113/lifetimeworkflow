"""EMIT-02 determinism — two emits produce byte-identical output (the drift gate depends on it).

Mirrors the tools/docs_sync determinism idiom (Pitfall P12): emit into two independent tmp trees
and assert the per-file sha256 is identical. No ``datetime.now()``/timestamps/floats and a fixed
ordered frontmatter template make re-emit reproducible byte-for-byte, which is exactly what the
CI ``emit-drift`` gate (`git diff --exit-code`) relies on.

RED at Task 1: ``tools.harness_emit.generate`` does not exist yet — import fails.
GREEN at Task 2 once the emit spine lands.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from tools.harness_emit import generate as harness_emit


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _emit_into(base: Path) -> list[Path]:
    """Emit the real harness/ agents into an isolated tmp tree (own manifest — no real writes)."""
    return harness_emit.emit(
        opencode_dir=base / ".opencode",
        claude_dir=base / ".claude",
        manifest_path=base / "emit-manifest.json",
        root=base,
    )


def test_emit_twice_byte_identical(tmp_path: Path) -> None:
    """Two emits into separate tmp trees produce identical sha256 per relative file path."""
    first = _emit_into(tmp_path / "a")
    second = _emit_into(tmp_path / "b")

    assert first, "emit wrote nothing"
    digest_1 = {p.relative_to(tmp_path / "a").as_posix(): _sha256(p) for p in first}
    digest_2 = {p.relative_to(tmp_path / "b").as_posix(): _sha256(p) for p in second}

    assert digest_1 == digest_2
