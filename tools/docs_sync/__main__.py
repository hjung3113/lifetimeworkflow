"""Package entrypoint so ``python -m tools.docs_sync`` runs the generator (CMD-08 macro target)."""

from tools.docs_sync.generate import main

if __name__ == "__main__":
    raise SystemExit(main())
