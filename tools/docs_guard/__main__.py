"""Package entrypoint so ``python -m tools.docs_guard`` runs the CLI.

``cli.py`` lands later in the phase, so the import is deferred INSIDE ``main()``: an eager
top-level import would make the whole package unimportable this wave. Until then
``python -m tools.docs_guard`` fails with a plain ``ModuleNotFoundError`` naming ``cli``.
"""

from __future__ import annotations


def main() -> int:
    from tools.docs_guard.cli import main as cli_main  # pyright: ignore[reportMissingImports]

    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
