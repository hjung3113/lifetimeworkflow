"""Package entrypoint so ``python -m tools.strangler_guard`` runs the refusal gate.

CMD-06 macro target.
"""

from tools.strangler_guard.guard import main

if __name__ == "__main__":
    raise SystemExit(main())
