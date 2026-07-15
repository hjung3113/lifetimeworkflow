"""EMIT-02 Regime B-md — managed-block splice into shared human/GSD Markdown files.

``splice_managed_block`` owns ONLY the content between the HARNESS-MANAGED HTML-comment fence and
must preserve everything OUTSIDE it byte-for-byte. These tests pin the four load-bearing truths:

  * (preserve-outside) human/GSD content BEFORE and AFTER the block survives verbatim;
  * (replace-inside) content between the markers is replaced by the new block body;
  * (idempotent) a second splice of the same body reproduces the file byte-for-byte;
  * (append-once) a file with NO markers gets the block appended exactly once, idempotent after;
  * (drift-catch) a hand-edit INSIDE the block is overwritten while an edit OUTSIDE is preserved.

If these ever regress the emitter could clobber the GSD `## Project` block / nearest-wins rules —
the whole reason the merge is a marker splice and never a full-write (threat T-07-02).
"""

from __future__ import annotations

from tools.harness_emit import merge

_BEGIN = merge.BEGIN_MARKER
_END = merge.END_MARKER

_HUMAN_BEFORE = "# Root Rules\n\n> Human + GSD prose that MUST survive.\n\n## Non-negotiables\n\n- contract-first\n"
_HUMAN_AFTER = "## Developer Profile\n\n> profile block — must survive verbatim.\n"

_OLD_BODY = "## Old Managed\n\nstale generated pointer index\n"
_NEW_BODY = "## Harness-Emitted Runtime Surface\n\n- Agents: a, b, c\n"


def _with_block(before: str, body: str, after: str) -> str:
    return f"{before}\n{_BEGIN}\n{body}\n{_END}\n\n{after}"


def test_preserves_outside_and_replaces_inside() -> None:
    """Content before/after the fence is byte-preserved; content between the markers is replaced."""
    existing = _with_block(_HUMAN_BEFORE, _OLD_BODY, _HUMAN_AFTER)
    result = merge.splice_managed_block(existing, _NEW_BODY)

    # human prose outside the block survives verbatim
    assert result.startswith(_HUMAN_BEFORE)
    assert _HUMAN_AFTER.rstrip("\n") in result
    # the stale body is gone, the new body is spliced in between the (still-present) markers
    assert "stale generated pointer index" not in result
    assert _NEW_BODY.strip("\n") in result
    assert result.count(_BEGIN) == 1
    assert result.count(_END) == 1


def test_second_run_is_byte_identical() -> None:
    """Re-splicing the same body reproduces the file byte-for-byte (drift gate depends on it)."""
    existing = _with_block(_HUMAN_BEFORE, _OLD_BODY, _HUMAN_AFTER)
    once = merge.splice_managed_block(existing, _NEW_BODY)
    twice = merge.splice_managed_block(once, _NEW_BODY)
    assert once == twice


def test_appends_block_exactly_once_when_markers_absent() -> None:
    """A markers-absent file gets the block appended once; a second splice is byte-identical."""
    plain = "# CLAUDE.md\n\n## Project\n\nGSD-managed identity block.\n"
    first = merge.splice_managed_block(plain, _NEW_BODY)

    assert first.count(_BEGIN) == 1
    assert first.count(_END) == 1
    # original content preserved ahead of the appended block
    assert first.startswith("# CLAUDE.md\n\n## Project\n\nGSD-managed identity block.\n")
    assert _NEW_BODY.strip("\n") in first

    second = merge.splice_managed_block(first, _NEW_BODY)
    assert first == second  # idempotent — appended exactly once, never duplicated


def test_edit_inside_block_overwritten_edit_outside_preserved() -> None:
    """A human edit INSIDE the block is overwritten on re-emit; an edit OUTSIDE is preserved."""
    existing = _with_block(_HUMAN_BEFORE, _NEW_BODY, _HUMAN_AFTER)
    clean = merge.splice_managed_block(existing, _NEW_BODY)

    # human tampers: edits inside the managed block AND appends a note outside it
    tampered = clean.replace("- Agents: a, b, c", "- Agents: HAND-EDITED")
    tampered = tampered.rstrip("\n") + "\n\n## Human Addendum\n\nkeep me\n"

    result = merge.splice_managed_block(tampered, _NEW_BODY)

    # inside-block edit is reverted to the emitted body
    assert "HAND-EDITED" not in result
    assert "- Agents: a, b, c" in result
    # outside-block edit survives
    assert "## Human Addendum" in result
    assert "keep me" in result


def test_output_is_lf_no_bom_single_trailing_newline() -> None:
    """Output normalizes to LF, strips a BOM, and ends with exactly one trailing newline."""
    crlf_bom = (
        "﻿# Title\r\n\r\n"
        + _BEGIN
        + "\r\n"
        + _OLD_BODY.replace("\n", "\r\n")
        + _END
        + "\r\n\r\n\r\n"
    )
    result = merge.splice_managed_block(crlf_bom, _NEW_BODY)

    assert not result.startswith("﻿")
    assert "\r" not in result
    assert result.endswith("\n")
    assert not result.endswith("\n\n")


def test_malformed_single_marker_raises() -> None:
    """A file with exactly one marker is ambiguous and must fail loud rather than corrupt it."""
    only_begin = f"# Title\n\n{_BEGIN}\nno end marker here\n"
    try:
        merge.splice_managed_block(only_begin, _NEW_BODY)
    except ValueError:
        return
    raise AssertionError("expected ValueError on a single-marker (malformed) managed block")
