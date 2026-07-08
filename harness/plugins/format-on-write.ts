// harness/plugins/format-on-write.ts
//
// ┌───────────────────────────────────────────────────────────────────────────────────────────┐
// │ RESUME NOTE — AUTHORED-ONLY, EXECUTION DEFERRED (D-01, mirrors harness/plugins/session-inject.ts) │
// │                                                                                             │
// │ This opencode adapter is SOURCE-authored but NOT execution-validated: there is no opencode  │
// │ runtime in this container. Do NOT try to run, wire (into opencode.json), or test it here.   │
// │ EXECUTION validation resumes when the opencode surface lands (after an opencode install).   │
// │                                                                                             │
// │ It deliberately consumes the SAME single enforcement contract as the LIVE Claude PostToolUse │
// │ hook (D-01): `uv run python -m tools.hooks.format_on_write`, fed the Claude event envelope on │
// │ stdin (`{tool_name, tool_input:{file_path}}`). Same byte hygiene (strip BOM / fold CRLF->LF, │
// │ §4.3-4.6 R1+R2 via normalize.core) + `ruff format` / dotnet-gated `dotnet format` — the ONLY │
// │ difference is the runtime envelope. PostToolUse NEVER blocks (advisory/mutating only).       │
// │                                                                                             │
// │ Confidence (04-RESEARCH A1): opencode hook name `tool.execute.after` is MEDIUM — re-verify   │
// │ before wiring into opencode.json. This stub documents the contract; it does not run.        │
// └───────────────────────────────────────────────────────────────────────────────────────────┘

import { execFileSync } from "node:child_process";

// The single enforcement contract — identical stdin behavior to the live Claude PostToolUse hook.
const FORMAT_ARGV = ["run", "python", "-m", "tools.hooks.format_on_write"] as const;

type WriteArgs = { file_path?: string };

// Build the Claude PostToolUse event envelope the python fixer parses from stdin (parse_event).
function eventEnvelope(tool: string, args: WriteArgs): string {
  return JSON.stringify({
    tool_name: tool,
    tool_input: { file_path: args.file_path ?? "" },
  });
}

// Run the shared python fixer (best-effort). It byte-fixes + formats on the FILE SYSTEM (no
// re-entry via a Write tool), so a re-run is a guaranteed no-op — mirrors the live hook.
function reformat(cwd: string, tool: string, args: WriteArgs): void {
  try {
    // argv form (execFileSync, NOT a shell string) — command-injection defense (T-04-19).
    execFileSync("uv", [...FORMAT_ARGV], {
      cwd,
      input: eventEnvelope(tool, args),
      stdio: ["pipe", "ignore", "ignore"],
    });
  } catch {
    /* PostToolUse never fails an edit — an env limitation (e.g. dotnet absent) is a logged SKIP */
  }
}

// opencode plugin shape (authored/deferred). PluginInput provides `directory`.
export const FormatOnWritePlugin = async ({ directory }: { directory: string }) => {
  const cwd = directory;
  return {
    // tool.execute.after — a mutating/report gate: canonicalize bytes + format after the write.
    "tool.execute.after": async (
      input: { tool: string },
      output: { args: WriteArgs },
    ) => {
      if (input.tool !== "write" && input.tool !== "edit") return;
      reformat(cwd, input.tool, output.args ?? {});
    },
  };
};

export default FormatOnWritePlugin;
