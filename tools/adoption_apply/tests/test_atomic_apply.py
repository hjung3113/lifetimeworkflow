"""test_atomic_apply.py — apply_manifest totality, drift refusal, idempotence, SC-2 integration.

Covers: idempotent re-apply, concurrent-drift refusal, marker-merge idempotence, no-arbitrary-
command-execution, draft-mode artifact-root confinement (ADOPT-05 clause 1), and the SC-2 full
apply-cycle integration proof (one of each of the 6 dispositions in a single manifest).
"""

from __future__ import annotations

import concurrent.futures
import fcntl
import os
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tools.adoption_apply import apply


def test_idempotent_reapply(tmp_path):
    manifest = {
        "target_ref": "unknown",
        "dispositions": [{"destination": "src/widget.py", "disposition": "create"}],
        "excluded": [],
    }
    payloads = {"src/widget.py": b"print('hi')\n"}

    summary = apply.apply_manifest(manifest, tmp_path, payloads=payloads)
    assert summary["applied"] == ["src/widget.py"]

    target = tmp_path / "src" / "widget.py"
    original_bytes = target.read_bytes()

    # A re-drafted manifest against the now-existing target correctly reports preserve — the
    # disposition chain never re-emits `create` for a target it already knows about.
    manifest_redraft = {
        "target_ref": "unknown",
        "dispositions": [{"destination": "src/widget.py", "disposition": "preserve"}],
        "excluded": [],
    }
    summary_2 = apply.apply_manifest(manifest_redraft, tmp_path, payloads=payloads)

    assert summary_2["skipped"] == ["src/widget.py"]
    assert target.read_bytes() == original_bytes


def test_concurrent_drift_refused(tmp_path):
    manifest = {
        "target_ref": "unknown",
        "dispositions": [{"destination": "src/widget.py", "disposition": "create"}],
        "excluded": [],
    }
    target = tmp_path / "src" / "widget.py"
    target.parent.mkdir(parents=True)
    out_of_band_bytes = b"human edited this after draft time\n"
    target.write_bytes(out_of_band_bytes)

    with pytest.raises(apply.ConcurrentDriftError):
        apply.apply_manifest(manifest, tmp_path, payloads={"src/widget.py": b"new content\n"})

    assert target.read_bytes() == out_of_band_bytes


def test_marker_merge_idempotent(tmp_path):
    target = tmp_path / "AGENTS.md"
    target.write_text("# Repo agents\n\nSome human prose.\n", encoding="utf-8")
    manifest = {
        "target_ref": "unknown",
        "dispositions": [{"destination": "AGENTS.md", "disposition": "marker-merge"}],
        "excluded": [],
    }
    block_bodies = {"AGENTS.md": "## Project\n\nManaged content.\n"}

    apply.apply_manifest(manifest, tmp_path, block_bodies=block_bodies)
    first_pass = target.read_text(encoding="utf-8")

    apply.apply_manifest(manifest, tmp_path, block_bodies=block_bodies)
    second_pass = target.read_text(encoding="utf-8")

    assert first_pass == second_pass
    assert "## Project" in first_pass
    assert "Some human prose." in first_pass


def test_no_arbitrary_command_execution(tmp_path, monkeypatch):
    run_spy = MagicMock()
    monkeypatch.setattr("subprocess.run", run_spy)

    settings_target = tmp_path / ".claude" / "settings.json"
    settings_target.parent.mkdir(parents=True)
    settings_target.write_text("{}\n", encoding="utf-8")

    manifest = {
        "target_ref": "unknown",
        "dispositions": [
            {"destination": "src/widget.py", "disposition": "create"},
            {"destination": ".claude/settings.json", "disposition": "marker-merge"},
            {"destination": "src/existing.py", "disposition": "preserve"},
            {"destination": "src/other.py", "disposition": "conflict"},
        ],
        "excluded": [],
    }
    apply.apply_manifest(manifest, tmp_path, payloads={"src/widget.py": b"x = 1\n"})

    assert run_spy.call_count == 0


def test_no_arbitrary_command_execution_structural():
    """Structural proof: apply.py's own source never calls subprocess.run at all."""
    source = Path(apply.__file__).read_text(encoding="utf-8")
    assert "subprocess.run(" not in source


def test_draft_confined_to_artifact_root(tmp_path):
    root = tmp_path / "artifacts" / "adoption" / "batch123"
    root.mkdir(parents=True)

    # A legitimate in-root draft write must not raise.
    apply.refuse_if_outside_root(root / "inventory.json", root)

    # A direct out-of-root write (one artifact-kind level up) is refused.
    with pytest.raises(apply.PathEscapeError):
        apply.refuse_if_outside_root(root.parent.parent / "escape.json", root)

    # A `..`-traversal escape attempt is refused — proves resolved-path, not string-prefix, logic.
    with pytest.raises(apply.PathEscapeError):
        apply.refuse_if_outside_root(root / ".." / ".." / ".." / "etc" / "passwd", root)


def test_sc2_full_apply_cycle(tmp_path):
    settings_target = tmp_path / ".claude" / "settings.json"
    settings_target.parent.mkdir(parents=True)
    settings_target.write_text("{}\n", encoding="utf-8")

    constitution_target = "contracts/new-widget.schema.json"

    manifest = {
        "target_ref": "unknown",
        "dispositions": [
            {"destination": "src/widget.py", "disposition": "create"},
            {"destination": ".claude/settings.json", "disposition": "marker-merge"},
            {"destination": "src/existing.py", "disposition": "preserve"},
            {"destination": "src/other.py", "disposition": "conflict"},
            {"destination": "docs/reference/index.md", "disposition": "derived-regenerate"},
            {"destination": constitution_target, "disposition": "human-ratification-required"},
        ],
        "excluded": [],
    }

    create_spy = MagicMock(wraps=apply.atomic_create)
    original_atomic_create = apply.atomic_create
    try:
        apply.atomic_create = create_spy
        summary = apply.apply_manifest(
            manifest, tmp_path, payloads={"src/widget.py": b"print(1)\n"}
        )
    finally:
        apply.atomic_create = original_atomic_create

    # Constitution-plane row refused before mutation — zero calls involving it.
    assert constitution_target in summary["refused"]
    assert constitution_target not in summary["applied"]
    assert not (tmp_path / constitution_target).exists()
    for call in create_spy.call_args_list:
        assert constitution_target not in str(call.args[0])

    # create row lands atomically.
    assert "src/widget.py" in summary["applied"]
    assert (tmp_path / "src" / "widget.py").read_bytes() == b"print(1)\n"

    # marker-merge row applied on the first pass.
    assert ".claude/settings.json" in summary["applied"]

    # preserve/conflict/derived-regenerate are all no-ops.
    for skipped_destination in ("src/existing.py", "src/other.py", "docs/reference/index.md"):
        assert skipped_destination in summary["skipped"]
        assert not (tmp_path / skipped_destination).exists()

    # marker-merge row is idempotent on a second pass — everything else re-drafted to preserve.
    first_settings_bytes = settings_target.read_bytes()
    manifest_pass_2 = {
        "target_ref": "unknown",
        "dispositions": [
            {"destination": "src/widget.py", "disposition": "preserve"},
            {"destination": ".claude/settings.json", "disposition": "marker-merge"},
            {"destination": "src/existing.py", "disposition": "preserve"},
            {"destination": "src/other.py", "disposition": "conflict"},
            {"destination": "docs/reference/index.md", "disposition": "derived-regenerate"},
            {"destination": constitution_target, "disposition": "human-ratification-required"},
        ],
        "excluded": [],
    }
    summary_2 = apply.apply_manifest(manifest_pass_2, tmp_path)
    assert settings_target.read_bytes() == first_settings_bytes
    assert constitution_target in summary_2["refused"]

    # summary dict correctly buckets all 6 rows in the first pass.
    assert sorted(summary["applied"] + summary["skipped"] + summary["refused"]) == sorted(
        record["destination"] for record in manifest["dispositions"]
    )


# --- CR-02 (27.1-01) — apply_manifest-level zero-write proof for escaped destinations ----------


def test_absolute_destination_refused_zero_writes(tmp_path, monkeypatch):
    """Proves the confinement guarantee through `apply_manifest` (not just `apply_disposition`).

    RED pre-fix reasoning: `Path(target_root) / destination` silently discards `target_root` when
    `destination` is absolute (pathlib's documented absolute-override join behavior); the synthetic
    destination is guaranteed not to already exist, so `atomic_create` really writes it — the spy
    `call_count > 0` assertion is what fails pre-fix, never the wrong exception type. Also asserts
    `PathEscapeError` propagates OUT of `apply_manifest` rather than being bucketed into
    `summary["refused"]` — a destination-shape integrity fault, not a routine per-record outcome.
    """
    open_spy = MagicMock(wraps=os.open)
    link_spy = MagicMock(wraps=os.link)
    replace_spy = MagicMock(wraps=os.replace)
    monkeypatch.setattr(os, "open", open_spy)
    monkeypatch.setattr(os, "link", link_spy)
    monkeypatch.setattr(os, "replace", replace_spy)

    escaped_destination = str(tmp_path / "outside-marker" / "widget.txt")
    manifest = {
        "target_ref": "unknown",
        "dispositions": [{"destination": escaped_destination, "disposition": "create"}],
        "excluded": [],
    }

    with pytest.raises(apply.PathEscapeError):
        apply.apply_manifest(manifest, tmp_path, payloads={escaped_destination: b"x = 1\n"})

    assert open_spy.call_count == 0
    assert link_spy.call_count == 0
    assert replace_spy.call_count == 0


def test_traversal_destination_refused_zero_writes(tmp_path, monkeypatch):
    """Traversal-escape twin of the absolute case above, same zero-write-spy proof."""
    open_spy = MagicMock(wraps=os.open)
    link_spy = MagicMock(wraps=os.link)
    replace_spy = MagicMock(wraps=os.replace)
    monkeypatch.setattr(os, "open", open_spy)
    monkeypatch.setattr(os, "link", link_spy)
    monkeypatch.setattr(os, "replace", replace_spy)

    escaped_destination = "../outside-marker/widget.txt"
    manifest = {
        "target_ref": "unknown",
        "dispositions": [{"destination": escaped_destination, "disposition": "create"}],
        "excluded": [],
    }

    with pytest.raises(apply.PathEscapeError):
        apply.apply_manifest(manifest, tmp_path, payloads={escaped_destination: b"x = 1\n"})

    assert open_spy.call_count == 0
    assert link_spy.call_count == 0
    assert replace_spy.call_count == 0


# --- WR-01 (27.1-01) / WR-07 (27.2-02) — locked _apply_marker_merge read-modify-write -----------

# NEVER assert the existence of the `.lock` sidecar here. That was the WR-07 defect: it is created
# by `lock_path.open("a+b")` alone, so the assertion held even with the `fcntl.flock` line deleted —
# a control tested only by an input the control already handles. The observed-mutual-exclusion
# helpers below replace it, and `test_concurrency_control_removal_is_detected` proves they go red.

_DWELL_SECONDS = 0.2
_BARRIER_TIMEOUT_SECONDS = 5.0


def _observe_marker_merge_concurrency(tmp_path, monkeypatch, *, barrier=None):
    """Run two racing `_apply_marker_merge` calls with the critical section instrumented.

    `apply.splice_managed_block` is called INSIDE the flock-held critical section, between the read
    and the atomic write, so wrapping it makes any overlap of the two racers directly observable.
    The wrapper delegates to the real function, so the merge semantics under test are unchanged.

    Returns `(max_concurrent, events, final_text)`.
    """
    target = tmp_path / "AGENTS.md"
    target.write_text("# Repo agents\n\nSome human prose.\n", encoding="utf-8")

    real_splice = apply.splice_managed_block
    counter_lock = threading.Lock()
    state = {"inside": 0, "max_concurrent": 0}
    events: list[tuple[str, str]] = []

    def _instrumented(existing_text, block_body):
        tag = block_body.strip().splitlines()[0]
        if barrier is not None:
            # Force — not merely encourage — the overlap the negative control needs to observe.
            barrier.wait(timeout=_BARRIER_TIMEOUT_SECONDS)
        with counter_lock:
            state["inside"] += 1
            state["max_concurrent"] = max(state["max_concurrent"], state["inside"])
            events.append(("enter", tag))
        time.sleep(_DWELL_SECONDS)
        with counter_lock:
            events.append(("exit", tag))
            state["inside"] -= 1
        return real_splice(existing_text, block_body)

    monkeypatch.setattr(apply, "splice_managed_block", _instrumented)

    def _merge(block_body):
        apply._apply_marker_merge("AGENTS.md", target, block_body=block_body)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(_merge, "## Block A\n\nContent A.\n"),
            pool.submit(_merge, "## Block B\n\nContent B.\n"),
        ]
        for future in futures:
            future.result()

    return state["max_concurrent"], events, target.read_text(encoding="utf-8")


def _assert_mutual_exclusion(max_concurrent, events):
    """The one pass/fail judgement for WR-01, shared by the positive test AND the negative control.

    Keeping it in one helper is what makes "the negative control proves the positive test goes red"
    literally true rather than merely analogous — both call THESE assertions.
    """
    assert max_concurrent == 1, (
        f"marker-merge critical section was entered concurrently: max_concurrent="
        f"{max_concurrent} (expected 1); events={events}"
    )
    expected = "enter"
    for kind, tag in events:
        assert kind == expected, (
            f"marker-merge enter/exit events interleaved: got {kind!r} for {tag!r} where "
            f"{expected!r} was expected; events={events}"
        )
        expected = "exit" if kind == "enter" else "enter"
    assert expected == "enter", f"unterminated critical section; events={events}"


def test_concurrent_marker_merge_does_not_lose_writes(tmp_path, monkeypatch):
    """Two racing `_apply_marker_merge` calls against the same target must not interleave.

    Asserts OBSERVED mutual exclusion of the critical section — never the existence of the `.lock`
    sidecar, which plain `open()` creates independently of `fcntl.flock` (WR-07). The second racer
    is blocked on the lock for the whole dwell, so `max_concurrent` stays 1 and the enter/exit
    event stream strictly alternates. No barrier here — a barrier would deadlock against the very
    lock under test.
    """
    max_concurrent, events, final_text = _observe_marker_merge_concurrency(tmp_path, monkeypatch)

    _assert_mutual_exclusion(max_concurrent, events)

    assert "Some human prose." in final_text
    # Exactly one of the two racers' content survives (last-writer-wins under the lock) — the
    # important property is that the file is NOT corrupted/interleaved/truncated.
    assert final_text.count("## Block A") <= 1
    assert final_text.count("## Block B") <= 1
    assert final_text.count("## Block A") + final_text.count("## Block B") >= 1


def test_concurrency_control_removal_is_detected(tmp_path, monkeypatch, capsys):
    """Negative control: with `fcntl.flock` neutered, the POSITIVE test's own assertion goes red.

    This is the executable form of "would this test still pass if the fix were reverted?" —
    deleting the real `fcntl.flock` line to prove a test is a one-off local mutation that does not
    repeat in CI, which is exactly why WR-07 survived review. Here the control is removed by
    patching the module attribute, the same observer runs, and `_assert_mutual_exclusion` — the
    very helper the positive test calls — is required to raise. Observing `max_concurrent == 2`
    alone would prove only that the instrumentation can see overlap, not that the guarding
    assertion fails; the `pytest.raises(AssertionError)` below is the load-bearing assertion.
    """
    monkeypatch.setattr(apply.fcntl, "flock", lambda *args, **kwargs: None)

    max_concurrent, events, _ = _observe_marker_merge_concurrency(
        tmp_path, monkeypatch, barrier=threading.Barrier(2)
    )

    with pytest.raises(AssertionError) as excinfo:
        _assert_mutual_exclusion(max_concurrent, events)

    # Recorded for the plan SUMMARY's RED evidence (SC-4) — this text IS the failure the positive
    # test would emit if someone deleted the `fcntl.flock` call from `_apply_marker_merge`.
    print(f"WR-07 negative control observed max_concurrent={max_concurrent}")
    print(f"WR-07 negative control AssertionError: {excinfo.value}")


def test_marker_merge_acquires_exclusive_flock(tmp_path, monkeypatch):
    """Structural spy: the `fcntl.flock(..., LOCK_EX)` call site still exists, whatever the timing.

    Closes the "the flock line was silently deleted" gap directly — the timing-based tests above
    could in principle be satisfied by an unrelated serialization, this cannot.
    """
    target = tmp_path / "AGENTS.md"
    target.write_text("# Repo agents\n\nSome human prose.\n", encoding="utf-8")

    real_flock = fcntl.flock
    flock_spy = MagicMock(wraps=real_flock)
    monkeypatch.setattr(apply.fcntl, "flock", flock_spy)

    apply._apply_marker_merge("AGENTS.md", target, block_body="## Block A\n\nContent A.\n")

    assert flock_spy.call_count >= 1
    assert any(call.args[1] == fcntl.LOCK_EX for call in flock_spy.call_args_list)


def test_marker_merge_refuses_symlink_read(tmp_path):
    """`_apply_marker_merge`'s read side must not follow a symlink into arbitrary content.

    RED pre-fix via a real read-through: today's `target_path.read_text()` follows the symlink and
    silently splices `victim.txt`'s content into the merge — this test proves that no longer
    happens and that the secret content never leaks into any raised exception's string form.
    """
    victim = tmp_path / "victim.txt"
    victim.write_text("SECRET-ORIGINAL\n", encoding="utf-8")

    agents_md = tmp_path / "AGENTS.md"
    agents_md.symlink_to(victim)

    with pytest.raises(apply.SymlinkRefusal) as excinfo:
        apply._apply_marker_merge("AGENTS.md", agents_md, block_body="## New\n")

    assert "SECRET-ORIGINAL" not in str(excinfo.value)
