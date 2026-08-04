"""test_fixtures.py — SC-3: 3 checked-in fixtures driving the REAL scan->plan->manifest->apply
pipeline end to end (never a mocked/stubbed subset of that chain).

Per 27-PATTERNS.md's file-by-file findings: ``polyglot-single`` is a NEW static tree (borrowing
``tmp_minirepo``'s hash-equal/hash-different collision-pair shape, never importing that fixture's
body); ``client-server`` extends the real, static ``tests/fixtures/workspace/{member-a,member-b}``
two-member layout; ``partial-collision-crlf`` is NEW and is the only fixture carrying the mandatory
CRLF/BOM input (the target's ``AGENTS.md``, which — being ``MARKER_CAPABLE`` — always routes
through ``tools.harness_emit.merge.splice_managed_block``, the ONE place ``apply.py`` calls
``_normalize`` on existing text; this is what makes the CRLF/BOM assertion meaningful rather than
invented).

Each fixture is copied into ``tmp_path`` before every pipeline run — the checked-in fixture trees
under ``tools/adoption_apply/tests/fixtures/`` are never mutated by a test (``apply_manifest``
writes into ``target_root`` directly).

``destinations.build_manifest``'s ``catalog``/``proposed_hashes`` parameters (already part of its
public signature, added for exactly this "decouple a fixed destination set from the live harness
checkout" purpose — see ``destinations.py``'s own docstring) are used to hand-pick the small,
domain-neutral destination set each fixture exercises, instead of the live
``destination_catalog()``/``harness_proposed_hashes()`` (which enumerate/hash THIS harness
checkout's real files — orthogonal to what a target-side fixture tree needs to prove).

Subprocess proof (T-27-05-01, ADOPT-07's "no arbitrary command execution"): ``subprocess.run`` is
spied (wrapping the real implementation, not stubbed — the pipeline's own git-based enumeration in
``scan.py`` must keep working) across the WHOLE cycle. Every recorded call is asserted to be one of
``scan.py``'s two fixed, target-scoped git invocations (``git -C <target> ls-files ...`` /
``git -C <target> rev-parse HEAD``) — never an argv containing any byte of manifest/draft/scanned
CONTENT. This is the meaningful form of the "no arbitrary command execution" proof: those two
git calls are pre-existing, already-audited, content-independent scan.py behavior (unchanged by
this plan); an argv built from scanned/manifest data would fail this assertion immediately.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

from tools.adoption_apply import apply
from tools.adoption_scan import destinations, plan, scan

_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

# The two, and only two, fixed argv shapes scan.py's own git usage may ever produce (git binary,
# `-C <target>`, then either `ls-files ...` or `rev-parse HEAD`) — never content-derived.
_ALLOWED_GIT_SUBCOMMANDS = ("ls-files", "rev-parse")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _copy_fixture(name: str, tmp_path: Path) -> Path:
    """Copy a checked-in fixture tree into ``tmp_path`` — the fixture on disk is never mutated."""
    source = _FIXTURES_DIR / name
    destination = tmp_path / name
    shutil.copytree(source, destination)
    return destination


def _snapshot(target: Path) -> dict[str, bytes]:
    """``{repo-relative path: bytes}`` over every managed-content file under ``target`` — used to
    prove idempotence (byte-identical second apply) and cross-member isolation.

    Excludes ``*.lock`` sidecar files: ``_apply_marker_merge``'s ``fcntl.flock``-guarded
    read-modify-write (WR-01, 27.1-01) persists a sidecar lock file next to its target, mirroring
    ``batch.py``'s own lock-file convention — this is expected operational state, not managed
    content, and its mere presence must not fail an idempotence/isolation comparison.
    """
    return {
        p.relative_to(target).as_posix(): p.read_bytes()
        for p in sorted(target.rglob("*"))
        if p.is_file() and not p.name.endswith(".lock")
    }


def _assert_only_fixed_git_calls(spy, target: Path) -> None:
    """Every recorded ``subprocess.run`` call is one of scan.py's two fixed, target-scoped git
    invocations — proves no arbitrary/content-derived command execution across the whole cycle."""
    target_resolved = str(target.resolve())
    for call in spy.call_args_list:
        argv = call.args[0]
        assert argv[0] == "git", f"unexpected non-git subprocess call: {argv!r}"
        assert argv[1] == "-C" and argv[2] == target_resolved, (
            f"git call not scoped to the fixture target: {argv!r}"
        )
        assert argv[3] in _ALLOWED_GIT_SUBCOMMANDS, f"unrecognized git subcommand: {argv!r}"


def _run_pipeline(
    target: Path,
    catalog: list[dict],
    proposed_hashes: dict[str, str],
    *,
    payloads: dict[str, bytes] | None = None,
    block_bodies: dict[str, str] | None = None,
) -> dict:
    """The shared scan -> plan -> manifest -> apply shape every fixture test drives — reused
    (never triplicated) per the plan's explicit instruction. Real function calls only; never a
    mocked/stubbed subset of ``tools.adoption_scan``/``tools.adoption_apply``."""
    inventory = scan.build_inventory(target)
    plan_doc = plan.build_plan(inventory)
    manifest = destinations.build_manifest(inventory, target, proposed_hashes, catalog=catalog)
    summary = apply.apply_manifest(
        manifest, target, payloads=payloads or {}, block_bodies=block_bodies or {}
    )
    return {"inventory": inventory, "plan": plan_doc, "manifest": manifest, "summary": summary}


def _disposition_map(manifest: dict) -> dict[str, str]:
    return {row["destination"]: row["disposition"] for row in manifest["dispositions"]}


# --------------------------------------------------------------------------------------------- #
# Fixture 1: polyglot-single (single-repo, create/preserve/conflict/marker-merge mix)
# --------------------------------------------------------------------------------------------- #


def test_polyglot_single_end_to_end(tmp_path):
    target = _copy_fixture("polyglot-single", tmp_path)

    widget_c_payload = b'def widget_c():\n    return "sink"\n'
    agents_block_body = "## Adoption\n\nManaged content for polyglot-single.\n"

    catalog = [
        {"destination": "pyproject.toml"},
        {"destination": "AGENTS.md"},
        {"destination": "widget_a.py"},
        {"destination": "widget_b.py"},
        {"destination": "widget_c.py"},
    ]
    proposed_hashes = {
        # pyproject.toml already matches the harness template byte-for-byte -> preserve.
        "pyproject.toml": _sha256((target / "pyproject.toml").read_bytes()),
        # widget_a.py's proposed content is the hash-equal companion -> preserve.
        "widget_a.py": _sha256((target / "widget_a_copy.py").read_bytes()),
        # widget_b.py's proposed content is the hash-DIFFERENT companion -> conflict.
        "widget_b.py": _sha256((target / "widget_b_modified.py").read_bytes()),
        # widget_c.py has no existing target file at all -> create; its proposed hash matches the
        # payload so a redraft after apply correctly resolves to preserve (idempotence, Pattern 2).
        "widget_c.py": _sha256(widget_c_payload),
        # AGENTS.md's disposition is MARKER_CAPABLE-forced (marker-merge always wins over any hash
        # comparison) — no proposed hash entry needed.
    }
    payloads = {"widget_c.py": widget_c_payload}
    block_bodies = {"AGENTS.md": agents_block_body}

    with patch("subprocess.run", wraps=subprocess.run) as spy:
        result = _run_pipeline(
            target, catalog, proposed_hashes, payloads=payloads, block_bodies=block_bodies
        )
    _assert_only_fixed_git_calls(spy, target)

    dispositions = _disposition_map(result["manifest"])
    assert dispositions["pyproject.toml"] == "preserve"
    assert dispositions["AGENTS.md"] == "marker-merge"
    assert dispositions["widget_a.py"] == "preserve"
    assert dispositions["widget_b.py"] == "conflict"
    assert dispositions["widget_c.py"] == "create"

    assert result["summary"]["applied"] == ["AGENTS.md", "widget_c.py"]
    assert result["summary"]["unchanged"] == ["pyproject.toml", "widget_a.py"]
    assert result["summary"]["conflicts"] == ["widget_b.py"]
    assert result["summary"]["refused"] == []

    assert (target / "widget_c.py").read_bytes() == widget_c_payload
    merged_agents = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Adoption" in merged_agents
    assert "target repository's own AGENTS.md" in merged_agents  # original prose preserved

    # Idempotence: re-running the identical cycle a second time is byte-identical.
    first_pass = _snapshot(target)
    with patch("subprocess.run", wraps=subprocess.run) as spy_2:
        _run_pipeline(
            target, catalog, proposed_hashes, payloads=payloads, block_bodies=block_bodies
        )
    _assert_only_fixed_git_calls(spy_2, target)
    second_pass = _snapshot(target)
    assert first_pass == second_pass


# --------------------------------------------------------------------------------------------- #
# Fixture 2: client-server (2-repo, extends tests/fixtures/workspace/{member-a,member-b})
# --------------------------------------------------------------------------------------------- #


def test_client_server_end_to_end(tmp_path):
    target = _copy_fixture("client-server", tmp_path)
    member_a = target / "member-a"
    member_b = target / "member-b"

    catalog = [
        {"destination": "AGENTS.md"},
        {"destination": "contracts/greeting.schema.json"},
    ]
    agents_block_body = "## Adoption\n\nManaged content for client-server.\n"

    # member-a already has an AGENTS.md -> marker-merge. contracts/ is constitution-plane ->
    # human-ratification-required regardless of any proposed hash -> refused by apply.py.
    member_a_pre = _snapshot(member_a)
    member_b_pre = _snapshot(member_b)

    with patch("subprocess.run", wraps=subprocess.run) as spy_a:
        result_a = _run_pipeline(
            member_a, catalog, proposed_hashes={}, block_bodies={"AGENTS.md": agents_block_body}
        )
    _assert_only_fixed_git_calls(spy_a, member_a)

    dispositions_a = _disposition_map(result_a["manifest"])
    assert dispositions_a["AGENTS.md"] == "marker-merge"
    assert dispositions_a["contracts/greeting.schema.json"] == "human-ratification-required"
    assert result_a["summary"]["applied"] == ["AGENTS.md"]
    assert result_a["summary"]["refused"] == ["contracts/greeting.schema.json"]

    # member-b is untouched by member-a's apply cycle — no cross-member write.
    assert _snapshot(member_b) == member_b_pre

    # member-b's own cycle: no AGENTS.md yet, but AGENTS.md is MARKER_CAPABLE so disposition()
    # resolves marker-merge regardless of existing-file state (step 4 wins before step 5's
    # existence check) -> _apply_marker_merge creates it from an empty existing_text. contracts/
    # is still refused. This proves a NORMAL single-repo apply cycle also runs correctly against
    # the second member.
    member_b_block_body = "## Adoption\n\nManaged content for client-server (member-b).\n"
    with patch("subprocess.run", wraps=subprocess.run) as spy_b:
        result_b = _run_pipeline(
            member_b, catalog, proposed_hashes={}, block_bodies={"AGENTS.md": member_b_block_body}
        )
    _assert_only_fixed_git_calls(spy_b, member_b)

    dispositions_b = _disposition_map(result_b["manifest"])
    assert dispositions_b["AGENTS.md"] == "marker-merge"
    assert dispositions_b["contracts/greeting.schema.json"] == "human-ratification-required"
    assert result_b["summary"]["applied"] == ["AGENTS.md"]
    assert result_b["summary"]["refused"] == ["contracts/greeting.schema.json"]
    assert "## Adoption" in (member_b / "AGENTS.md").read_text(encoding="utf-8")

    # member-a's tree is unaffected by member-b's apply cycle — the boundary holds both ways.
    assert _snapshot(member_a) == {
        **member_a_pre,
        "AGENTS.md": (member_a / "AGENTS.md").read_bytes(),
    }
    assert not (member_b / "contracts" / "new-widget.schema.json").exists()

    # Idempotence per member.
    member_a_first = _snapshot(member_a)
    with patch("subprocess.run", wraps=subprocess.run) as spy_a2:
        _run_pipeline(
            member_a, catalog, proposed_hashes={}, block_bodies={"AGENTS.md": agents_block_body}
        )
    _assert_only_fixed_git_calls(spy_a2, member_a)
    assert _snapshot(member_a) == member_a_first

    member_b_first = _snapshot(member_b)
    with patch("subprocess.run", wraps=subprocess.run) as spy_b2:
        _run_pipeline(
            member_b, catalog, proposed_hashes={}, block_bodies={"AGENTS.md": member_b_block_body}
        )
    _assert_only_fixed_git_calls(spy_b2, member_b)
    assert _snapshot(member_b) == member_b_first


# --------------------------------------------------------------------------------------------- #
# Fixture 3: partial-collision-crlf (partial-adoption/collision, mandatory CRLF/BOM input)
# --------------------------------------------------------------------------------------------- #


def test_partial_collision_crlf_end_to_end(tmp_path):
    target = _copy_fixture("partial-collision-crlf", tmp_path)

    original_agents_bytes = (target / "AGENTS.md").read_bytes()
    assert original_agents_bytes.startswith(b"\xef\xbb\xbf")  # genuine UTF-8 BOM
    assert b"\r\n" in original_agents_bytes  # genuine CRLF line endings

    widget_c_payload = b'def widget_c():\n    return "sink"\n'
    agents_block_body = "## Adoption\n\nManaged content for partial-collision-crlf.\n"

    catalog = [
        {"destination": "AGENTS.md"},
        {"destination": "widget_a.py"},
        {"destination": "widget_b.py"},
        {"destination": "widget_c.py"},
    ]
    proposed_hashes = {
        # widget_a.py already correctly adopted (hash-equal companion) -> preserve.
        "widget_a.py": _sha256((target / "widget_a_copy.py").read_bytes()),
        # widget_b.py's proposed content is the hash-DIFFERENT companion -> conflict.
        "widget_b.py": _sha256((target / "widget_a_modified.py").read_bytes()),
        "widget_c.py": _sha256(widget_c_payload),
    }
    payloads = {"widget_c.py": widget_c_payload}
    block_bodies = {"AGENTS.md": agents_block_body}

    with patch("subprocess.run", wraps=subprocess.run) as spy:
        result = _run_pipeline(
            target, catalog, proposed_hashes, payloads=payloads, block_bodies=block_bodies
        )
    _assert_only_fixed_git_calls(spy, target)

    dispositions = _disposition_map(result["manifest"])
    assert dispositions["AGENTS.md"] == "marker-merge"
    assert dispositions["widget_a.py"] == "preserve"
    assert dispositions["widget_b.py"] == "conflict"
    assert dispositions["widget_c.py"] == "create"

    assert result["summary"]["applied"] == ["AGENTS.md", "widget_c.py"]
    assert result["summary"]["unchanged"] == ["widget_a.py"]
    assert result["summary"]["conflicts"] == ["widget_b.py"]
    assert result["summary"]["refused"] == []

    # The CRLF/BOM input file's post-apply bytes match harness_emit.merge._normalize's own
    # documented transform (BOM stripped, LF-forced), never an ad hoc hand-computed expectation.
    from tools.harness_emit.merge import _normalize

    merged_text = (target / "AGENTS.md").read_text(encoding="utf-8")
    original_text = original_agents_bytes.decode("utf-8")
    expected_prefix = _normalize(original_text)
    assert merged_text.startswith(expected_prefix.rstrip("\n"))
    assert not merged_text.startswith("﻿")
    assert "\r\n" not in merged_text
    assert "## Adoption" in merged_text

    # Idempotence: re-running the identical cycle a second time is byte-identical.
    first_pass = _snapshot(target)
    with patch("subprocess.run", wraps=subprocess.run) as spy_2:
        _run_pipeline(
            target, catalog, proposed_hashes, payloads=payloads, block_bodies=block_bodies
        )
    _assert_only_fixed_git_calls(spy_2, target)
    second_pass = _snapshot(target)
    assert first_pass == second_pass
