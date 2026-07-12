"""Package entrypoint so ``python -m tools.harness_emit`` runs the emitter (EMIT-02)."""

from tools.harness_emit.generate import main

if __name__ == "__main__":
    raise SystemExit(main())
