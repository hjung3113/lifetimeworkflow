"""RED tests for the localhost-only HTTP dispatch shell (Phase 16, MEM2-07, SC1, D-16-01).

These pin the ``tools.memory_ui.server`` shell BEFORE it exists (16-05 implements it): the
loopback-ONLY bind (the security boundary, T-16-05), the thin dispatch to the pure ``routes.*``
functions, ``GET /`` serving the inlined page, and the bounded POST body (T-16-07).

No test binds a fixed port — every live-socket smoke test binds ``127.0.0.1:0`` (ephemeral) and
reads ``server.server_address[1]`` (16-RESEARCH Pitfall 2), then shuts the server down. Dispatch is
exercised against tmp plane dirs monkeypatched onto the server module, so no test writes a real
agreement or touches the real ``.memory/`` planes.
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path


def _state_dir(tmp_path: Path) -> Path:
    state = tmp_path / "state"
    state.mkdir()
    (state / "activeContext.md").write_text(
        '---\nupdated: "2026-07-16"\n---\n\n# Active context\n\nSession log.\n',
        encoding="utf-8",
    )
    (state / "progress.md").write_text(
        '---\nupdated: "2026-07-16"\n---\n\n# Progress\n\ntiny.\n',
        encoding="utf-8",
    )
    return state


@contextmanager
def _running(server):
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[0], server.server_address[1]
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_make_server_binds_loopback_only() -> None:
    """The server binds 127.0.0.1 — the loopback bind IS the access-control boundary (T-16-05)."""
    from tools.memory_ui import server

    with server.make_server(0) as httpd:
        assert httpd.server_address[0] == "127.0.0.1"  # never 0.0.0.0 / "" / a routable address


def test_get_root_serves_inlined_page(tmp_path: Path) -> None:
    """GET / returns 200 and the self-contained inlined page (no external assets)."""
    from tools.memory_ui import page, server

    with server.make_server(0) as httpd, _running(httpd) as base:
        with urllib.request.urlopen(base + "/") as resp:
            assert resp.status == 200
            body = resp.read().decode("utf-8")
    assert "<title>Memory</title>" in body
    assert body == page.PAGE


def test_get_items_dispatches_to_routes(tmp_path, tmp_agreements_tree, monkeypatch) -> None:
    """GET /api/items delegates to routes.list_items over the (monkeypatched) tmp plane dirs."""
    from tools.memory_ui import server

    monkeypatch.setattr(server, "STATE_DIR", _state_dir(tmp_path))
    monkeypatch.setattr(server, "AGREEMENTS_DIR", tmp_agreements_tree)

    with server.make_server(0) as httpd, _running(httpd) as base:
        with urllib.request.urlopen(base + "/api/items") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
    assert "activeContext.md" in data["state"] and "progress.md" in data["state"]
    slugs = {a["slug"] for a in data["agreements"]}
    assert "alpha-ground" in slugs and "zeta-proceed" in slugs


def test_post_body_is_size_bounded(tmp_path, tmp_agreements_tree, monkeypatch) -> None:
    """An over-large POST body is rejected before parsing (T-16-07 DoS bound)."""
    from tools.memory_ui import server

    monkeypatch.setattr(server, "AGREEMENTS_DIR", tmp_agreements_tree)
    monkeypatch.setattr(server, "DERIVED_DIR", tmp_path / "derived")
    oversized = b"x" * (server.MAX_BODY_BYTES + 1)

    with server.make_server(0) as httpd, _running(httpd) as base:
        req = urllib.request.Request(
            base + "/api/agreement/add",
            data=oversized,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
        except urllib.error.HTTPError as exc:
            status = exc.code
    assert status == 413  # Payload Too Large — refused before JSON parse


def test_serve_module_has_no_wildcard_or_host_flag() -> None:
    """Static guard: the shell source never binds 0.0.0.0/"" and exposes no --host flag."""
    from tools.memory_ui import server

    src = Path(server.__file__).read_text(encoding="utf-8")
    assert "127.0.0.1" in src
    assert "0.0.0.0" not in src
    assert '"", ' not in src  # no wildcard bind via empty host
