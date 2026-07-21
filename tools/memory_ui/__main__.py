"""Entrypoint: ``python -m tools.memory_ui`` — serve the local memory web UI (MEM2-07, SC1).

Exposes ONLY ``--port`` (default 8765). There is deliberately no flag to change the bind address:
the server binds ``127.0.0.1`` unconditionally, and that loopback bind IS the tool's access-control
boundary (D-16-01 / T-16-05). Allowing a routable bind would expose the tool beyond the local
machine.
"""

from __future__ import annotations

import argparse

from tools.memory_ui.server import serve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.memory_ui",
        description="Serve the local memory web UI on 127.0.0.1 (loopback only).",
    )
    parser.add_argument("--port", type=int, default=8765, help="loopback port (default: 8765)")
    args = parser.parse_args(argv)

    # Loopback URL only — never a routable address (T-16-05).
    print(f"memory UI serving on 127.0.0.1 port {args.port}  (Ctrl-C to stop)")
    try:
        serve(args.port)
    except KeyboardInterrupt:
        print("\nstopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
