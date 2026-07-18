"""Localhost-only HTTP dispatch shell for the memory web UI (Phase 16, MEM2-07, SC1, D-16-01).

A THIN ``BaseHTTPRequestHandler`` + ``ThreadingHTTPServer`` shell. It holds **no** business logic:
it parses the request (path / query / size-bounded JSON body) and delegates to the pure
:mod:`tools.memory_ui.routes` functions, writing back their ``(status, headers, body)``. All
edit/retire/save/validation logic — and every ``.memory/agreements`` write — lives in the tested
routes and the sanctioned :mod:`tools.agree.write`; the shell never authors a file itself.

Security boundary (T-16-05): the server binds ``127.0.0.1`` ONLY. The loopback bind IS the
access-control model for this single-user local tool — no auth, and by design no wildcard/routable
bind and no ``--host`` flag. :func:`make_server` hardcodes the loopback address;
:mod:`tools.memory_ui.__main__` exposes only ``--port``.

Freshness seam (D-16-03 / RESEARCH Q2, Pitfall 4): before a destructive retire the shell
INLINE-regenerates the derived pointer-index over the real repo roots (via
:func:`tools.memory_regen.pointer_index.write`) so the routes' orphan gate reads FRESH referrers.
Routes stay hermetic (they only read the injected ``derived_dir``); the server supplies freshness.

DoS bound (T-16-07): a POST body larger than :data:`MAX_BODY_BYTES` is refused with ``413`` before
any JSON parse.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from tools.memory_regen import pointer_index
from tools.memory_ui import routes
from tools.memory_ui.page import PAGE

# --- real plane dirs (tests monkeypatch these module globals; the handler reads them live) -----
_REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = _REPO_ROOT / ".memory" / "state"
AGREEMENTS_DIR = _REPO_ROOT / ".memory" / "agreements"
DERIVED_DIR = _REPO_ROOT / ".memory" / "derived"

# The loopback host is hardcoded — see module docstring (T-16-05). Never parameterise this.
_HOST = "127.0.0.1"
_DEFAULT_PORT = 8765

# Bound the POST body before parsing (T-16-07). 256 KiB is generous for an agreement/progress edit.
MAX_BODY_BYTES = 256 * 1024

_STATE_ITEMS = ("activeContext.md", "progress.md")
_HTML = {"Content-Type": "text/html; charset=utf-8"}
_JSON = {"Content-Type": "application/json; charset=utf-8"}


def _item_key(item: str) -> str:
    """Map a UI item id to its pointer-index key (state file or agreement path)."""
    if item in _STATE_ITEMS:
        return f".memory/state/{item}"
    return f".memory/agreements/{item}.md"


class MemoryUIHandler(BaseHTTPRequestHandler):
    """Thin request parser that dispatches to the pure ``routes.*`` functions (no logic here)."""

    server_version = "memory-ui/1"

    # -- helpers --------------------------------------------------------------------------------
    def _send(self, status: int, headers: dict, body: bytes) -> None:
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _read_json_body(self) -> dict | None:
        """Return the parsed JSON body, or ``None`` when absent/over-bound/malformed.

        Over-bound bodies are the ``413`` DoS guard (T-16-07): the caller maps ``None`` +
        over-length to ``413`` before ever touching a route.
        """
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        if length > MAX_BODY_BYTES:
            return None
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None

    def _json(self, status: int, payload: dict) -> None:
        self._send(status, dict(_JSON), json.dumps(payload, sort_keys=True).encode("utf-8"))

    # -- GET ------------------------------------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802 (stdlib handler naming)
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/":
            self._send(200, dict(_HTML), PAGE.encode("utf-8"))
            return

        if path == "/api/items":
            show_retired = (query.get("show_retired", ["0"])[0]) in ("1", "true")
            status, headers, body = routes.list_items(
                state_dir=STATE_DIR, agreements_dir=AGREEMENTS_DIR, show_retired=show_retired
            )
            self._send(status, headers, body)
            return

        if path == "/api/item":
            item = query.get("id", [""])[0]
            status, headers, body = routes.view_item(
                item, state_dir=STATE_DIR, agreements_dir=AGREEMENTS_DIR
            )
            self._send(status, headers, body)
            return

        if path == "/api/pointers":
            item = query.get("item", [""])[0]
            referrers = routes.pointer_lookup(
                _item_key(item),
                base_dir=_REPO_ROOT,
                scan_roots=pointer_index._default_scan_roots(),
            )
            self._json(200, {"item": item, "referrers": referrers})
            return

        self._json(404, {"error": f"no such route: {path}"})

    # -- POST -----------------------------------------------------------------------------------
    def do_POST(self) -> None:  # noqa: N802 (stdlib handler naming)
        path = urlparse(self.path).path
        payload = self._read_json_body()
        if payload is None:
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY_BYTES:
                self._json(413, {"error": "request body too large"})
            else:
                self._json(400, {"error": "malformed JSON body"})
            return

        if path == "/api/agreement/add":
            status, headers, body = routes.add_agreement(
                payload.get("slug", ""),
                payload.get("title", ""),
                payload.get("rule", ""),
                because=payload.get("because", ""),
                related=payload.get("related"),
                agreements_dir=AGREEMENTS_DIR,
                derived_dir=DERIVED_DIR,
            )
            self._send(status, headers, body)
            return

        if path == "/api/agreement/retire":
            slug = payload.get("slug", "")
            confirm = bool(payload.get("confirm", False))
            # Inline-regenerate the derived pointer-index over the real roots BEFORE the orphan
            # check so the routes' gate sees fresh referrers (D-16-03 / Pitfall 4). Writes only
            # under the gitignored derived plane; never touches .memory/agreements (T-16-10).
            self._refresh_pointer_index()
            status, headers, body = routes.retire_agreement(
                slug, agreements_dir=AGREEMENTS_DIR, derived_dir=DERIVED_DIR, confirm=confirm
            )
            self._send(status, headers, body)
            return

        if path == "/api/progress/save":
            status, headers, body = routes.save_progress(
                payload.get("item", ""), payload.get("body", ""), state_dir=STATE_DIR
            )
            self._send(status, headers, body)
            return

        self._json(404, {"error": f"no such route: {path}"})

    def _refresh_pointer_index(self) -> None:
        """Regenerate the derived pointer-index over the real repo roots (best-effort)."""
        try:
            pointer_index.write(
                json_path=DERIVED_DIR / "pointer-index.json",
                md_path=DERIVED_DIR / "pointer-index.md",
                base_dir=_REPO_ROOT,
                scan_roots=None,
            )
        except OSError:
            # A regen failure must not crash the retire path; the routes fall back to the
            # last-written index (or an empty referrer set), and the UI labels it "from last regen".
            pass

    def log_message(self, format: str, *args: object) -> None:
        """Silence the default stderr access log (single-user local tool)."""


def make_server(port: int = _DEFAULT_PORT) -> ThreadingHTTPServer:
    """Build a ThreadingHTTPServer bound to ``127.0.0.1`` ONLY (never a wildcard host, T-16-05).

    ``port=0`` binds an ephemeral port (read ``server.server_address[1]``) — used by smoke tests so
    they never fight over a fixed port.
    """
    return ThreadingHTTPServer((_HOST, port), MemoryUIHandler)


def serve(port: int = _DEFAULT_PORT) -> None:
    """Serve the memory UI on ``127.0.0.1:<port>`` until interrupted."""
    httpd = make_server(port)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
