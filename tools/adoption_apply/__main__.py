"""Package entrypoint so ``python -m tools.adoption_apply`` runs the CLI."""

from tools.adoption_apply.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
