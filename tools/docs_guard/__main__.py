"""Package entrypoint so ``python -m tools.docs_guard`` runs the CLI.

The import stays deferred INSIDE ``main()``. It was originally deferred because ``cli.py`` had not
landed yet (an eager top-level import would have made the whole package unimportable that wave);
it stays deferred now because ``cli`` pulls in the classifier, the registry/ledger loaders, and the
contract graph, and nothing that merely imports this package should pay for that.
"""

from __future__ import annotations


def main() -> int:
    from tools.docs_guard.cli import main as cli_main  # pyright: ignore[reportMissingImports]

    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
