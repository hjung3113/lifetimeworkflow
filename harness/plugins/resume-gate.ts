// Shared resume-attestation gate for OpenCode's mechanically identifiable mutations.
import { execFileSync } from "node:child_process";

const GATE_ARGV = ["run", "python", "-m", "tools.hooks.resume_gate"] as const;
type ToolArgs = { file_path?: string; content?: string; command?: string };

function envelope(tool: string, args: ToolArgs, cwd: string): string {
  return JSON.stringify({ tool_name: tool, cwd, tool_input: args ?? {} });
}

function check(cwd: string, tool: string, args: ToolArgs): void {
  let stdout: string;
  try {
    stdout = execFileSync("uv", [...GATE_ARGV], { cwd, input: envelope(tool, args, cwd), encoding: "utf8" }).trim();
  } catch {
    // The gate itself is a required control: runtime failure must not turn into an allow.
    throw new Error("resume_gate: unavailable; protected mutation blocked");
  }
  if (!stdout) return;
  try {
    const reason = JSON.parse(stdout)?.hookSpecificOutput?.permissionDecisionReason;
    throw new Error(reason ?? "resume_gate: protected mutation blocked");
  } catch (error) {
    if (error instanceof Error && error.message !== "Unexpected end of JSON input") throw error;
    throw new Error("resume_gate: invalid gate response; protected mutation blocked");
  }
}

export const ResumeGatePlugin = async ({ directory }: { directory: string }) => ({
  "tool.execute.before": async (input: { tool: string }, output: { args: ToolArgs }) => {
    if (["write", "edit", "bash"].includes(input.tool)) check(directory, input.tool[0].toUpperCase() + input.tool.slice(1), output.args ?? {});
  },
});

export default ResumeGatePlugin;
