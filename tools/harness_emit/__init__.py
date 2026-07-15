"""harness_emit — the EMIT-01/02 single-source dual-runtime emitter.

Invoked as ``python -m tools.harness_emit``. A virtual uv-workspace member (sibling of docs_sync/,
contract_hash/, golden_runner/, memory_regen/). It reads the runtime-neutral authored source under
``harness/`` and writes the two runtime-native artifact trees — ``.opencode/`` (primary) and the
harness slice of ``.claude/`` (secondary) — so both runtimes stay byte-faithful to ONE source and
nothing is silently truncated or drifts.

Phase-7 Wave-1 (D-05 agent-first walking skeleton) drives the 4 harness agents end-to-end through
EVERY mechanic — frontmatter projection → per-runtime shape → loud-fail validators → ownership
manifest → committed output → CI re-emit-diff drift gate — before widening to commands/skills/
plugins/config in later waves.

Determinism discipline is cloned from ``tools/docs_sync/generate.py`` (fixed ordered frontmatter
template per target, a DERIVED "do not hand-edit" marker, LF/no-BOM, no ``datetime.now()``/floats,
byte-identical delete+regenerate). The public API lives in :mod:`tools.harness_emit.generate`
(``emit`` / ``main``), :mod:`tools.harness_emit.project_agent`, :mod:`tools.harness_emit.validate`,
and :mod:`tools.harness_emit.manifest`; this package stays import-light so the test conftest can
wire ``sys.path`` first.
"""
