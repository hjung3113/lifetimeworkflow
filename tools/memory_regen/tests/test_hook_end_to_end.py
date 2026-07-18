"""End-to-end regression for the live SessionStart hook (MEM2-02, Phase 13-04, D-20).

`13-04-PLAN.md`'s acceptance criteria required running
``bash .claude/hooks/memory-inject.sh | node -e '...'`` and inspecting the emitted
``additionalContext`` — proof the kill switch (`.memory/.inject-disabled`) is gone and the hook
actually emits a non-empty, reframed, data-scoped payload rather than the empty string the
`|| echo ''` swallow would produce on failure (T-13-05). That command was run manually during plan
execution but never landed as a standing pytest test, so nothing in the regression suite would
catch a reintroduced kill switch or a broken hook silently degrading to an empty payload. This
file closes that gap by invoking the real hook script as a subprocess (no mocking of the
shell/node envelope) and parsing its actual stdout.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _run_hook(repo_root: Path) -> dict:
    proc = subprocess.run(
        ["bash", str(repo_root / ".claude" / "hooks" / "memory-inject.sh")],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return json.loads(proc.stdout)


def test_kill_switch_file_is_absent(repo_root: Path) -> None:
    """The `.memory/.inject-disabled` flag must not exist — its presence would silently empty
    every session's injected payload (D-20)."""
    assert not (repo_root / ".memory" / ".inject-disabled").exists()


def test_hook_emits_non_empty_data_scoped_payload(repo_root: Path) -> None:
    """Running the real hook end-to-end must yield a non-trivial, data-scoped payload — not the
    empty string the `|| echo ''` swallow (memory-inject.sh:40) would emit on a broken assembler."""
    payload = _run_hook(repo_root)
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert len(context) > 1000
    assert "DATA" in context


def test_hook_payload_carries_no_retired_provisional_wording(repo_root: Path) -> None:
    """D-06: the reframe retired the provisional/banner-first framing — the live end-to-end
    payload must not resurrect it."""
    payload = _run_hook(repo_root)
    context = payload["hookSpecificOutput"]["additionalContext"].lower()
    assert "provisional" not in context
    assert "hint, not truth" not in context
    assert "confirm before trusting" not in context
