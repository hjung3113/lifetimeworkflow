"""Package entrypoint so ``python -m tools.adoption_scan`` runs the CLI."""

from tools.adoption_scan.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
