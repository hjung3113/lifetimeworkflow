"""Regime B-json — signature-matched, order-preserving hook-group merge into .claude/settings.json.

This is the single highest-risk surface in Phase 7 (T-07-09 / T-07-11 / Pitfall 4). The Phase 2/4
harness hooks (``tools.hooks.format_on_write`` / ``contract_guard`` / ``secret_scan`` /
``commit_gate``) + the ``memory-inject.sh`` injector are ALREADY hand-wired into the LIVE
``.claude/settings.json`` and guarded by ``tools/memory_regen/tests/test_hook_wiring.py`` (exactly 4
SessionStart groups). The MVP contract (Open Q2 / A5) is IDEMPOTENT COEXISTENCE:

  (a) ``merge_settings`` fed the parsed LIVE settings, serialized, MUST equal the ACTUAL live bytes
      byte-for-byte — no 5th SessionStart group, no key-order flap, NO global key-sort (the live
      file is SessionStart-FIRST / insertion-ordered, not alphabetical; a sort_keys pass produces a
      ~274-line Day-1 false-positive drift — T-07-11).
  (b) SessionStart stays exactly 4 groups (3 GSD + memory-inject) — T-07-09 / Pitfall 4.
  (c) the 3 GSD hooks + memory-inject survive in their ORIGINAL order (T-07-02).
  (d) a synthetic DUPLICATE harness group in the input is de-duplicated (no double-wire).
  (e) a second merge is byte-identical (idempotent).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.harness_emit import merge

# tests -> harness_emit -> tools -> repo root (parents[3]; mirrors conftest.py).
REPO_ROOT = Path(__file__).resolve().parents[3]
SETTINGS_PATH = REPO_ROOT / ".claude" / "settings.json"

# The 3 GSD SessionStart hooks + the 4th-slot injector — the coexistence contract from
# tools/memory_regen/tests/test_hook_wiring.py that this merge MUST preserve.
GSD_SESSION_COMMANDS = [
    "gsd-check-update.js",
    "gsd-session-state.sh",
    "tools/bootstrap/install.sh",
    "memory-inject.sh",
]


def _serialize(settings: dict) -> str:
    """Regime B-json serialization — order-PRESERVING, NO sort_keys, single trailing LF."""
    return json.dumps(settings, indent=2, ensure_ascii=False) + "\n"


def _session_commands(settings: dict) -> list[str]:
    commands: list[str] = []
    for group in settings["hooks"]["SessionStart"]:
        for hook in group["hooks"]:
            commands.append(hook["command"])
    return commands


def test_merge_reproduces_live_settings_byte_for_byte() -> None:
    """(a) merge_settings(<parsed live>) serialized == the ACTUAL live settings.json bytes."""
    live_bytes = SETTINGS_PATH.read_text(encoding="utf-8")
    parsed = json.loads(live_bytes)
    merged = merge.merge_settings(parsed)
    assert _serialize(merged) == live_bytes, (
        "merge_settings did not reproduce the live settings.json byte-for-byte "
        "(a 5th group, a key-order flap, or a global sort would trip this)"
    )


def test_session_start_stays_exactly_four_groups() -> None:
    """(b) SessionStart keeps exactly 4 groups after merge (Pitfall 4 / T-07-09)."""
    parsed = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    merged = merge.merge_settings(parsed)
    assert len(merged["hooks"]["SessionStart"]) == 4


def test_gsd_hooks_and_injector_survive_in_order() -> None:
    """(c) the 3 GSD hooks + memory-inject survive in their original order (T-07-02)."""
    parsed = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    merged = merge.merge_settings(parsed)
    commands = _session_commands(merged)
    positions = [
        next(i for i, c in enumerate(commands) if needle in c) for needle in GSD_SESSION_COMMANDS
    ]
    assert positions == sorted(positions), "GSD SessionStart hooks were reordered"


def test_duplicate_harness_group_is_deduplicated() -> None:
    """(d) a synthetic duplicate harness group in the input is collapsed (no double-wire)."""
    parsed = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    injected = copy.deepcopy(parsed)
    # Duplicate the format_on_write harness group in PostToolUse (simulate a naive re-wire).
    dup = copy.deepcopy(
        next(
            g
            for g in injected["hooks"]["PostToolUse"]
            if any("tools.hooks.format_on_write" in h["command"] for h in g["hooks"])
        )
    )
    injected["hooks"]["PostToolUse"].append(dup)

    merged = merge.merge_settings(injected)

    fow_groups = [
        g
        for g in merged["hooks"]["PostToolUse"]
        if any("tools.hooks.format_on_write" in h["command"] for h in g["hooks"])
    ]
    assert len(fow_groups) == 1, "duplicate harness group was not de-duplicated"
    # De-dup must land back on the live bytes exactly.
    assert _serialize(merged) == SETTINGS_PATH.read_text(encoding="utf-8")


def test_merge_is_idempotent() -> None:
    """(e) a second merge over an already-merged settings is byte-identical."""
    parsed = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    once = merge.merge_settings(parsed)
    twice = merge.merge_settings(copy.deepcopy(once))
    assert _serialize(once) == _serialize(twice)


def _assert_retired_signature_is_dropped(signature: str) -> None:
    """Reconstruct a stale checkout's group for ``signature`` and assert the re-emit drops it."""
    parsed = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    stale = copy.deepcopy(parsed)
    stale["hooks"]["PreToolUse"].append(
        {
            "matcher": "Write|Edit|Bash",
            "hooks": [{"type": "command", "command": f"uv run python -m {signature}"}],
        }
    )
    before = len(stale["hooks"]["PreToolUse"])

    merged = merge.merge_settings(stale)

    assert signature not in json.dumps(merged), (
        f"{signature} is listed in RETIRED_SIGNATURES but survived a re-emit — a stale checkout "
        "would keep running a deleted module and deny every Write/Edit/Bash"
    )
    assert len(merged["hooks"]["PreToolUse"]) == before - 1
    # Dropping the orphan must land back on the live bytes exactly.
    assert _serialize(merged) == SETTINGS_PATH.read_text(encoding="utf-8")


def test_retired_signature_group_is_dropped_from_a_stale_checkout() -> None:
    """A retired harness hook is removed from a tree that still carries its group.

    The emitting repo cannot observe this: once its own re-emit has landed, its settings.json no
    longer holds the group, so the merge is idempotent and ``emit-drift`` stays green whether or not
    ``RETIRED_SIGNATURES`` still lists the signature. Every OTHER checkout can — an adopted target,
    a stale clone, a long-lived branch. There the group matches no current signature, falls through
    as GSD/human-owned, and is kept verbatim pointing at a deleted module; the guard then exits
    non-zero and PreToolUse denies every Write/Edit/Bash.

    Phase 43 shipped with the tuple emptied and this branch uncovered, so a full green suite proved
    nothing about it. The assertion reconstructs the stale group from the retired signature itself,
    so it keeps biting for whatever signature is retired next.
    """
    assert merge.RETIRED_SIGNATURES, "no retired signature to exercise"
    for signature in merge.RETIRED_SIGNATURES:
        _assert_retired_signature_is_dropped(signature)


def test_retired_signatures_are_permanent_tombstones() -> None:
    """Every tombstone ever added stays listed — the tuple is append-only, never cleared.

    The loop above only exercises what the tuple happens to list, so it stays GREEN when an entry is
    deleted (mutation-proved). These membership pins are the assertions that red on the Phase-43
    "clear the tuple after the re-emit" move (REVIEW.md CR-01) — the move that strands every OTHER
    checkout while the emitting repo stays green.
    """
    # Phase 43 / CER-07 — the resume_gate lifecycle plane removal.
    assert "tools.hooks.resume_gate" in merge.RETIRED_SIGNATURES, (
        "tools.hooks.resume_gate was dropped from RETIRED_SIGNATURES — tombstones are permanent; "
        "a checkout still carrying the pre-43 settings.json would invoke a deleted module"
    )


def test_gsd_group_never_removed_even_when_sharing_event() -> None:
    """A GSD group is never removed even though harness groups share PostToolUse/PreToolUse."""
    parsed = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    merged = merge.merge_settings(parsed)
    pre_commands = [h["command"] for g in merged["hooks"]["PreToolUse"] for h in g["hooks"]]
    assert any("gsd-validate-commit.sh" in c for c in pre_commands), (
        "a GSD PreToolUse hook was dropped while harness groups share the event"
    )
