"""Package entrypoint so ``python -m tools.ruff_baseline`` runs the ratchet.

The import stays deferred inside ``main()`` so merely importing the package costs nothing —
mirrors ``tools/docs_guard/__main__.py``.
"""

from __future__ import annotations


def main() -> int:
    from tools.ruff_baseline.ratchet import (
        main as ratchet_main,  # pyright: ignore[reportMissingImports]
    )

    return ratchet_main()


if __name__ == "__main__":
    raise SystemExit(main())
