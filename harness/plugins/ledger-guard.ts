// harness/plugins/ledger-guard.ts
//
// ┌───────────────────────────────────────────────────────────────────────────────────────────┐
// │ RESUME NOTE — AUTHORED-ONLY, EXECUTION DEFERRED (D-01, mirrors harness/plugins/contract-guard.ts) │
// │                                                                                             │
// │ This opencode adapter is SOURCE-authored but NOT execution-validated: there is no opencode  │
// │ runtime in this container. Do NOT try to run or test it here. EXECUTION validation resumes  │
// │ when the opencode surface lands (after an opencode install).                                │
// │                                                                                             │
// │ It consumes the SAME single enforcement contract as the LIVE Claude PreToolUse hook:        │
// │ `uv run python -m tools.hooks.ledger_guard`, fed the Claude event envelope on stdin         │
// │ (`{tool_name, tool_input:{file_path}}`) and interpreting the module's deny JSON. Same rule  │
// │ engine — the ONLY difference is the runtime envelope.                                       │
// │                                                                                             │
// │ ADR-0010 clause 3b layer 1. There is NO approval token and NO dev bypass in this domain:    │
// │ GOLDEN_APPROVE_HUMAN authorizes CONSTITUTION writes, and no token legitimizes an            │
// │ agent-authored review disposition. A human edits the ledger outside an agent session.       │
// └───────────────────────────────────────────────────────────────────────────────────────────┘

import { execFileSync } from "node:child_process";

// The single enforcement contract — identical stdin/stdout to the live Claude PreToolUse hook.
const GUARD_ARGV = ["run", "python", "-m", "tools.hooks.ledger_guard"] as const;

type WriteArgs = { file_path?: string; content?: string };

// Build the Claude PreToolUse event envelope the python gate parses from stdin (parse_event).
function eventEnvelope(tool: string, args: WriteArgs): string {
  return JSON.stringify({
    tool_name: tool,
    tool_input: { file_path: args.file_path ?? "", content: args.content ?? "" },
  });
}

// Run the shared python gate; return its deny decision (stdout JSON) or null on allow.
function evaluate(cwd: string, tool: string, args: WriteArgs): { reason: string } | null {
  let stdout = "";
  try {
    // argv form (execFileSync, NOT a shell string) — command-injection defense (T-04-19).
    stdout = execFileSync("uv", [...GUARD_ARGV], {
      cwd,
      input: eventEnvelope(tool, args),
      encoding: "utf8",
    }).trim();
  } catch {
    return null; // a broken gate must not wedge the editor — the LIVE Claude hook is the backstop.
  }
  if (!stdout) return null; // no decision -> allow (the path is not the review ledger).
  try {
    const decision = JSON.parse(stdout);
    const out = decision?.hookSpecificOutput;
    if (out?.permissionDecision === "deny") {
      return { reason: out.permissionDecisionReason ?? "ledger-guard denied the write" };
    }
  } catch {
    /* non-JSON stdout -> treat as allow (fail-open here; Claude hook is authoritative) */
  }
  return null;
}

// opencode plugin shape (authored/deferred). PluginInput provides `directory`.
export const LedgerGuardPlugin = async ({ directory }: { directory: string }) => {
  const cwd = directory;
  return {
    // tool.execute.before — a deny gate: throw to BLOCK the Write/Edit before it lands.
    "tool.execute.before": async (
      input: { tool: string },
      output: { args: WriteArgs },
    ) => {
      if (input.tool !== "write" && input.tool !== "edit") return;
      const denied = evaluate(cwd, input.tool, output.args ?? {});
      if (denied) throw new Error(denied.reason);
    },
  };
};

export default LedgerGuardPlugin;
