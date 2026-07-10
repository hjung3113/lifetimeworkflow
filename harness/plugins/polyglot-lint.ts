// harness/plugins/polyglot-lint.ts
//
// ┌───────────────────────────────────────────────────────────────────────────────────────────┐
// │ RESUME NOTE — AUTHORED-ONLY, EXECUTION DEFERRED (D-01, mirrors harness/plugins/session-inject.ts) │
// │                                                                                             │
// │ This opencode adapter is SOURCE-authored but NOT execution-validated: there is no opencode  │
// │ runtime in this container. Do NOT try to run, wire (into opencode.json), or test it here.   │
// │ EXECUTION validation resumes when the opencode surface lands (after an opencode install).   │
// │                                                                                             │
// │ It deliberately consumes the SAME single §4.3-4.6 rule engine as the LIVE Claude surfaces    │
// │ (D-01): `python -m tools.polyglot_lint.lint <path>` — the ONE POLY-01 linter that the        │
// │ on-write hook, the commit-gate, and the /lint command all call (one engine, three sites).    │
// │ The linter takes the TSV path as an ARGV argument (not stdin) and exits 1 on any violation.  │
// │ The ONLY difference here is the runtime envelope.                                            │
// │                                                                                             │
// │ Confidence (04-RESEARCH A1): opencode hook name `tool.execute.after` is MEDIUM — re-verify   │
// │ before wiring into opencode.json. This stub documents the contract; it does not run.        │
// └───────────────────────────────────────────────────────────────────────────────────────────┘

import { execFileSync } from "node:child_process";

// The single §4.3-4.6 rule engine — identical CLI to the /lint command and the commit-gate.
const LINT_ARGV = ["run", "python", "-m", "tools.polyglot_lint.lint"] as const;

type WriteArgs = { file_path?: string };

// Lint a single tracked boundary (*.tsv) file; return the linter's fail-loud stderr, or null when
// clean / not a TSV. Presence-safe: a non-.tsv target is a no-op (mirrors the /lint macro loop).
function lintTsv(cwd: string, filePath: string): string | null {
  if (!filePath.endsWith(".tsv")) return null;
  try {
    // argv form (execFileSync, path as a positional ARG, NOT a shell string) — T-04-19.
    execFileSync("uv", [...LINT_ARGV, filePath], { cwd, encoding: "utf8" });
    return null; // exit 0 -> no §4.3-4.6 violation.
  } catch (err) {
    // exit 1 -> the linter wrote `polyglot-lint: FAIL [Rx-...]` lines to stderr; surface them.
    const stderr = (err as { stderr?: Buffer | string })?.stderr;
    return stderr ? String(stderr).trim() : "polyglot-lint: §4.3-4.6 violation";
  }
}

// opencode plugin shape (authored/deferred). PluginInput provides `directory`.
export const PolyglotLintPlugin = async ({ directory }: { directory: string }) => {
  const cwd = directory;
  return {
    // tool.execute.after — a report gate: lint a written TSV boundary file and warn on a violation.
    "tool.execute.after": async (
      input: { tool: string },
      output: { args: WriteArgs },
    ) => {
      if (input.tool !== "write" && input.tool !== "edit") return;
      const filePath = output.args?.file_path;
      if (!filePath) return;
      const failure = lintTsv(cwd, filePath);
      if (failure) console.error(failure); // report; on-write byte hygiene stays format-on-write's job.
    },
  };
};

export default PolyglotLintPlugin;
