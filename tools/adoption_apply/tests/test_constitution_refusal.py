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
from tools.harness_emit import merge as merge_module
from tools.harness_emit.merge import merge_settings
from tools.harness_perms import load_matrix, resolve_path
from tools.hooks import ledger_guard
from tools.hooks._stdin import _REPO_ROOT as REPO_ROOT
from tools.hooks.contract_guard import CONSTITUTION_GLOBS
from tools.hooks.secret_scan import SECRET_PATH_GLOBS

# The ledger's repo-relative spelling — the path all three deny domains are probed against.
LEDGER_REL = "docs/.docs-review-ledger.toml"

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


# --- WR-02 (27.2 review) — a destination whose parent chain is an existing FILE ---------------
#
# `AGENTS.md/evil.txt` (with `AGENTS.md` an existing file) is not directory-shaped to ANY of the
# checks above: it is relative, has no `..`, its last segment is `evil.txt`, it does not resolve
# to the root, and `is_dir()` is False precisely because the parent is a file. It therefore passed
# the whole choke point and blew up downstream in `atomic_create`'s `mkdir` with a raw
# `FileExistsError` — not in the CLI's except tuple, so a traceback leaked.
NON_DIRECTORY_ANCESTOR_DESTINATIONS = [
    ("parent_is_file", "AGENTS.md/evil.txt"),
    ("grandparent_is_file", "AGENTS.md/nested/evil.txt"),
]


@pytest.mark.parametrize(
    ("case_name", "destination"),
    NON_DIRECTORY_ANCESTOR_DESTINATIONS,
    ids=[case_name for case_name, _ in NON_DIRECTORY_ANCESTOR_DESTINATIONS],
)
def test_refuse_unsafe_destination_rejects_non_directory_ancestor(tmp_path, case_name, destination):
    """WR-02: refuse at the choke point (D-01), before any filesystem write is attempted."""
    (tmp_path / "AGENTS.md").write_text("marker\n", encoding="utf-8")

    with pytest.raises(apply.PathEscapeError) as excinfo:
        apply.refuse_unsafe_destination(destination, tmp_path)

    message = str(excinfo.value)
    assert f"'{destination}'" in message, case_name
    assert "non-directory ancestor" in message, f"{case_name}: refused by the wrong guard"


def test_apply_disposition_refuses_non_directory_ancestor(tmp_path, monkeypatch):
    """End-to-end: `PathEscapeError`, never a raw `FileExistsError`, and zero writes — the
    existing marker file is left byte-identical."""
    (tmp_path / "AGENTS.md").write_text("marker\n", encoding="utf-8")
    open_spy = MagicMock(wraps=os.open)
    link_spy = MagicMock(wraps=os.link)
    replace_spy = MagicMock(wraps=os.replace)
    monkeypatch.setattr(os, "open", open_spy)
    monkeypatch.setattr(os, "link", link_spy)
    monkeypatch.setattr(os, "replace", replace_spy)

    record = {"destination": "AGENTS.md/evil.txt", "disposition": "create"}
    with pytest.raises(apply.PathEscapeError):
        apply.apply_disposition(record, tmp_path, payload=b"content")

    assert open_spy.call_count == 0
    assert link_spy.call_count == 0
    assert replace_spy.call_count == 0
    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == "marker\n"


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


# --- 28-09 — the human-review ledger is a THIRD path-deny domain -------------------------------
#
# `docs/.docs-review-ledger.toml` is the greenness authority for the docs plane: a disposition row
# in it is what makes a binding FRESH. Agents may PROPOSE registry rows
# (`docs/doc-dependencies.toml`, DOCSUP-07) but only a human may author a ledger disposition —
# otherwise an agent lands a new binding plus its own blessing and self-greens.
#
# Every row carries the spelling a single literal comparison would miss (27.1 CR-01's lesson:
# a refusal that a spelling bypasses is not a refusal). `expected` pins WHICH exception:
#   "ledger" — must raise `ReviewLedgerRefusal`, and must NOT be a `ConstitutionRefusal`.
#   "any"    — must be refused, but the row asserts nothing about which guard fires. The `..`
#              spelling is already stopped by the 27.1 structural pre-check; its purpose here is to
#              prove no spelling reaches the file, not to pin it to this plan's guard.
REVIEW_LEDGER_DESTINATIONS = [
    ("plain", "docs/.docs-review-ledger.toml", "ledger"),
    ("dot_slash_prefixed", "./docs/.docs-review-ledger.toml", "ledger"),
    ("interior_dot_segment", "docs/./.docs-review-ledger.toml", "ledger"),
    ("dotdot_resolving_onto_ledger", "docs/sub/../.docs-review-ledger.toml", "any"),
    ("upper_case", "DOCS/.DOCS-REVIEW-LEDGER.TOML", "ledger"),
    ("mixed_case", "docs/.Docs-Review-Ledger.toml", "ledger"),
]

# The narrowness control. Every row MUST stay writable; the first is the load-bearing one.
#   * `docs/doc-dependencies.toml` — THE REGISTRY. DOCSUP-07 requires `/adopt` to propose rows into
#     it, and the D-01 plane split exists precisely so that stays possible. A refusal that also
#     caught the registry would silently break Phase 29.
#   * the two prefix-adjacent names — what a sloppy `startswith`/`docs/.docs-review-ledger*` glob
#     would over-match.
LEDGER_ADJACENT_ALLOWED = [
    "docs/doc-dependencies.toml",
    "docs/how-to/task-lifecycle.md",
    "docs/.docs-review-ledger.toml.bak",
    "docs/.docs-review-ledger-notes.md",
    "docs/reference/doc-dependencies.md",
]


@pytest.mark.parametrize(
    ("case_name", "destination", "expected"),
    REVIEW_LEDGER_DESTINATIONS,
    ids=[case_name for case_name, _, _ in REVIEW_LEDGER_DESTINATIONS],
)
def test_review_ledger_destination_is_refused(tmp_path, case_name, destination, expected):
    """RED pre-fix: `apply.ReviewLedgerRefusal` does not exist, and no spelling of the ledger is
    refused today — the ledger is absent from `CONSTITUTION_GLOBS`, from `path_deny_globs`, and
    from CODEOWNERS.

    The distinct exception type is the point: conflating it with `ConstitutionRefusal` would teach
    an operator to reach for `GOLDEN_APPROVE_HUMAN`, which authorizes CONSTITUTION writes and must
    never be understood to authorize a ledger disposition.
    """
    if expected == "any":
        with pytest.raises(ValueError):
            apply.refuse_unsafe_destination(destination, tmp_path)
        return

    with pytest.raises(apply.ReviewLedgerRefusal) as excinfo:
        apply.refuse_unsafe_destination(destination, tmp_path)

    assert f"'{destination}'" in str(excinfo.value), case_name
    assert not isinstance(excinfo.value, apply.ConstitutionRefusal), case_name


@pytest.mark.parametrize(
    ("case_name", "destination", "expected"),
    REVIEW_LEDGER_DESTINATIONS,
    ids=[case_name for case_name, _, _ in REVIEW_LEDGER_DESTINATIONS],
)
def test_review_ledger_destination_is_refused_end_to_end(
    tmp_path, monkeypatch, case_name, destination, expected
):
    """End-to-end through `apply_disposition`, with a zero-call write spy: the ledger is refused
    before any `open()`/`os.link()`/`os.replace()`, for every spelling."""
    open_spy = MagicMock(wraps=os.open)
    link_spy = MagicMock(wraps=os.link)
    replace_spy = MagicMock(wraps=os.replace)
    monkeypatch.setattr(os, "open", open_spy)
    monkeypatch.setattr(os, "link", link_spy)
    monkeypatch.setattr(os, "replace", replace_spy)

    expected_exception = ValueError if expected == "any" else apply.ReviewLedgerRefusal
    record = {"destination": destination, "disposition": "create"}
    with pytest.raises(expected_exception):
        apply.apply_disposition(record, tmp_path, payload=b"content")

    assert open_spy.call_count == 0, case_name
    assert link_spy.call_count == 0, case_name
    assert replace_spy.call_count == 0, case_name


@pytest.mark.parametrize("destination", LEDGER_ADJACENT_ALLOWED)
def test_review_ledger_adjacent_destination_stays_allowed(tmp_path, destination):
    """Narrowness control — GREEN against unmodified code, and it must STAY green.

    `docs/doc-dependencies.toml` is the row that matters: the registry must remain agent-writable
    at the choke point or DOCSUP-07 becomes unimplementable.
    """
    result = apply.refuse_unsafe_destination(destination, tmp_path)
    assert Path(tmp_path).resolve() in result.parents, destination


def test_review_ledger_ordinary_tool_path_is_denied_by_a_real_hook(tmp_path):
    """CR-02: ADR-0010 clause 3b layer 1 must be an ENFORCER, not a data row.

    The `apply.py` choke point guards only the adoption-APPLY write path; a plain agent
    `Write`/`Edit` never reaches it. The previous version of this test asserted
    `resolve_path(load_matrix()["path_deny_globs"], "<the ledger>") == "deny"` — but at that time
    NO hook consumed `path_deny_globs`, and the emitter strips the key from `opencode.json` as
    resolver-only, so the assertion reduced to "the glob I just added matches the path I just
    added". It could not fail while the control was absent, which is the definition of vacuous
    coverage.

    This drives the hook's own `decide()` with an ABSOLUTE path, the shape the runtime actually
    passes, and asserts a deny decision. Delete the hook and this fails.
    """
    ledger = Path(REPO_ROOT) / "docs" / ".docs-review-ledger.toml"

    decision = ledger_guard.decide(str(ledger))

    assert decision is not None, "a plain agent Write to the review ledger was not denied"
    output = decision["hookSpecificOutput"]
    assert output["permissionDecision"] == "deny"
    reason = output["permissionDecisionReason"]
    assert "GOLDEN_APPROVE_HUMAN" in reason, (
        "the deny must say the constitution token does NOT apply"
    )
    assert "doc-dependencies.toml" in reason, "the deny must name the agent-writable alternative"


def test_review_ledger_hook_honours_no_token_and_no_dev_bypass(monkeypatch):
    """No token legitimizes an agent-authored disposition, so neither opt-out may open this gate.

    `GOLDEN_APPROVE_HUMAN` authorizes CONSTITUTION writes and `HARNESS_DEV_BYPASS` is the ADR-0007
    local-dev opt-out for that same plane. The ledger is a DIFFERENT domain — the docs plane's
    greenness authority — so both must be inert here (ADR-0010 clause 3b).
    """
    monkeypatch.setenv("GOLDEN_APPROVE_HUMAN", "yes-i-am-a-human")
    monkeypatch.setenv("HARNESS_DEV_BYPASS", "1")

    ledger = Path(REPO_ROOT) / "docs" / ".docs-review-ledger.toml"

    assert ledger_guard.decide(str(ledger)) is not None


def test_review_ledger_hook_leaves_the_registry_and_neighbours_writable():
    """Narrowness control — DENY must not spill onto the agent-writable registry (DOCSUP-07)."""
    for destination in LEDGER_ADJACENT_ALLOWED:
        assert ledger_guard.decide(str(Path(REPO_ROOT) / destination)) is None, destination


def test_review_ledger_hook_is_a_disjoint_third_domain():
    """`contract_guard.py:16-20`'s provably-disjoint-domain invariant must survive a third domain.

    Pairwise disjointness is asserted on the GLOBS, not on prose: the ledger domain may not overlap
    the constitution plane (which honours `GOLDEN_APPROVE_HUMAN`) or the secret plane.
    """
    assert resolve_path(CONSTITUTION_GLOBS, LEDGER_REL) != "deny"
    assert resolve_path(SECRET_PATH_GLOBS, LEDGER_REL) != "deny"
    assert resolve_path(ledger_guard.REVIEW_LEDGER_GLOBS, LEDGER_REL) == "deny"
    for glob_list, name in ((CONSTITUTION_GLOBS, "constitution"), (SECRET_PATH_GLOBS, "secret")):
        for probe in (
            "contracts/w.schema.json",
            "docs/adr/0099-x.md",
            "golden/b.verified",
            "a.env",
        ):
            if resolve_path(glob_list, probe) == "deny":
                assert resolve_path(ledger_guard.REVIEW_LEDGER_GLOBS, probe) != "deny", (
                    f"the ledger domain overlaps the {name} domain at {probe}"
                )


def test_review_ledger_hook_is_wired_into_the_emitted_pretooluse_set():
    """The wiring, not just the module. A gate nobody invokes is the CR-02 defect in a new place.

    Asserted through `merge_settings` — the function the emitter actually runs to produce
    `.claude/settings.json` — so deleting the hook group from `HARNESS_HOOK_GROUPS` fails this,
    and so does dropping its signature (which would make the group unowned and unplaced).
    """
    merged = merge_settings({"hooks": {}})

    commands = [
        hook["command"] for group in merged["hooks"]["PreToolUse"] for hook in group["hooks"]
    ]
    assert any("tools.hooks.ledger_guard" in command for command in commands), (
        "ledger_guard is not wired into the emitted PreToolUse set — ADR-0010's layer 1 is inert"
    )
    matchers = [
        group["matcher"]
        for group in merged["hooks"]["PreToolUse"]
        if any("tools.hooks.ledger_guard" in hook["command"] for hook in group["hooks"])
    ]
    assert matchers == ["Write|Edit"], "layer 1 covers the ordinary Write/Edit tool path"
    assert "tools.hooks.ledger_guard" in merge_module.HARNESS_SIGNATURES


def test_review_ledger_permission_matrix_still_carries_the_glob():
    """The matrix row remains, and it must AGREE with the hook that now enforces it.

    Kept as a consistency check between the two, never as the proof of enforcement — that is
    `test_review_ledger_ordinary_tool_path_is_denied_by_a_real_hook`.
    """
    deny_globs = load_matrix()["path_deny_globs"]
    assert resolve_path(deny_globs, LEDGER_REL) == "deny"
    assert set(ledger_guard.REVIEW_LEDGER_GLOBS) <= set(deny_globs), (
        "the hook denies a path the authored matrix does not — the two have drifted"
    )


def test_review_ledger_permission_matrix_keeps_registry_writable():
    """DENY must not spill onto the registry, nor onto the prefix-adjacent names."""
    deny_globs = load_matrix()["path_deny_globs"]
    for path in LEDGER_ADJACENT_ALLOWED:
        assert resolve_path(deny_globs, path) != "deny", path


@pytest.mark.parametrize(
    "path",
    [
        "contracts/widget.schema.json",
        "docs/adr/0099-example.md",
        "golden/y/baseline.verified.tsv",
        "secrets.env",
        "nested/dir/secrets.env",
    ],
)
def test_review_ledger_matrix_edit_left_existing_denies_intact(path):
    """The matrix edit added ONE glob and changed nothing else."""
    deny_globs = load_matrix()["path_deny_globs"]
    assert resolve_path(deny_globs, path) == "deny"
