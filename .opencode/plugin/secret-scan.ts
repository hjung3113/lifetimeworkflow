// harness/plugins/secret-scan.ts
//
// ┌───────────────────────────────────────────────────────────────────────────────────────────┐
// │ RESUME NOTE — AUTHORED-ONLY, EXECUTION DEFERRED (D-01, mirrors harness/plugins/session-inject.ts) │
// │                                                                                             │
// │ This opencode adapter is SOURCE-authored but NOT execution-validated: there is no opencode  │
// │ runtime in this container. Do NOT try to run, wire (into opencode.json), or test it here.   │
// │ EXECUTION validation resumes when the opencode surface lands (after an opencode install).   │
// │                                                                                             │
// │ It deliberately consumes the SAME single enforcement contract as the LIVE Claude PreToolUse │
// │ hook (D-01): `uv run python -m tools.hooks.secret_scan`, fed the Claude event envelope on    │
// │ stdin (`{tool_name, tool_input:{file_path, content}}`) and interpreting the module's deny    │
// │ JSON. Same two deny paths (secret *.env path + shape-anchored content secret), same          │
// │ fixture allow-list — the ONLY difference is the runtime envelope.                            │
// │                                                                                             │
// │ Confidence (04-RESEARCH A1): opencode hook name `tool.execute.before` is MEDIUM — re-verify  │
// │ before wiring into opencode.json. This stub documents the contract; it does not run.        │
// └───────────────────────────────────────────────────────────────────────────────────────────┘

import { execFileSync } from "node:child_process";

// The single enforcement contract — identical stdin/stdout to the live Claude PreToolUse hook.
const SCAN_ARGV = ["run", "python", "-m", "tools.hooks.secret_scan"] as const;

type IoArgs = { file_path?: string; content?: string };

// Build the Claude PreToolUse event envelope the python gate parses from stdin (parse_event).
function eventEnvelope(tool: string, args: IoArgs): string {
  return JSON.stringify({
    tool_name: tool,
    tool_input: { file_path: args.file_path ?? "", content: args.content ?? "" },
  });
}

// Run the shared python gate; return its deny decision (stdout JSON) or null on allow.
function evaluate(cwd: string, tool: string, args: IoArgs): { reason: string } | null {
  let stdout = "";
  try {
    // argv form (execFileSync, NOT a shell string) — command-injection defense (T-04-19).
    stdout = execFileSync("uv", [...SCAN_ARGV], {
      cwd,
      input: eventEnvelope(tool, args),
      encoding: "utf8",
    }).trim();
  } catch {
    return null; // a broken gate must not wedge the editor — the LIVE Claude hook is the backstop.
  }
  if (!stdout) return null; // no decision -> allow (no secret path, no secret-shaped content).
  try {
    const decision = JSON.parse(stdout);
    const out = decision?.hookSpecificOutput;
    if (out?.permissionDecision === "deny") {
      return { reason: out.permissionDecisionReason ?? "secret_scan denied the operation" };
    }
  } catch {
    /* non-JSON stdout -> treat as allow (fail-open here; Claude hook is authoritative) */
  }
  return null;
}

// opencode plugin shape (authored/deferred). PluginInput provides `directory`.
export const SecretScanPlugin = async ({ directory }: { directory: string }) => {
  const cwd = directory;
  return {
    // tool.execute.before — a deny gate: throw to BLOCK a Read/Write/Edit of secret material.
    "tool.execute.before": async (
      input: { tool: string },
      output: { args: IoArgs },
    ) => {
      if (input.tool !== "read" && input.tool !== "write" && input.tool !== "edit") return;
      const denied = evaluate(cwd, input.tool, output.args ?? {});
      if (denied) throw new Error(denied.reason);
    },
  };
};

export default SecretScanPlugin;
