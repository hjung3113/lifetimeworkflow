// harness/plugins/session-inject.ts
//
// ┌───────────────────────────────────────────────────────────────────────────────────────────┐
// │ RESUME NOTE — AUTHORED-ONLY, EXECUTION DEFERRED (D-01, mirrors the .NET DOTNET-RESUME.md)   │
// │                                                                                             │
// │ This opencode adapter is SOURCE-authored but NOT execution-validated: there is no opencode  │
// │ runtime in this container. Do NOT try to run or test it here. EXECUTION validation resumes  │
// │ when the opencode surface lands (Phase 3 CONFIG / after an opencode install).               │
// │                                                                                             │
// │ It deliberately consumes the SAME single injection contract as the Claude hook (D-01):      │
// │   `python -m tools.memory_regen.inject`  →  the capped, directive-first, priority-truncated, │
// │   pointer-only payload from tools/memory_regen/inject.py::assemble(). Same payload, same     │
// │   ~1k-token cap, same data-provenance banner — the ONLY difference is the runtime envelope.  │
// │                                                                                             │
// │ Confidence (02-RESEARCH A2): opencode hook names (`event` session.created +                 │
// │ `chat.system.transform` vs `experimental.chat.system.transform`) are MEDIUM — re-verify at  │
// │ Phase 3 before wiring into opencode.json. This stub documents the contract, it does not run. │
// └───────────────────────────────────────────────────────────────────────────────────────────┘

import { execFileSync } from "node:child_process";

// The single injection contract — identical stdout to the Claude SessionStart hook.
const INJECT_ARGV = ["run", "python", "-m", "tools.memory_regen.inject"] as const;

function assemblePayload(cwd: string): string {
  try {
    // argv form (execFileSync, NOT a shell string) — command-injection defense mirrors T-02-04.
    return execFileSync("uv", [...INJECT_ARGV], { cwd, encoding: "utf8" }).trimEnd();
  } catch {
    return ""; // degrade gracefully — never break session start on a missing generator.
  }
}

function regenerateDerivedPlane(cwd: string): void {
  // Best-effort — a missing Wave-2 generator must never break session start (|| true parity).
  for (const mod of ["tools.memory_regen.repo_map", "tools.memory_regen.contracts_index", "tools.memory_regen.pointer_index"]) {
    try {
      execFileSync("uv", ["run", "python", "-m", mod], { cwd, stdio: "ignore" });
    } catch {
      /* ignore — assembler degrades when derived files are absent */
    }
  }
}

// opencode plugin shape (authored/deferred). PluginInput provides `directory` + `worktree`.
export const SessionInjectPlugin = async ({ directory }: { directory: string }) => {
  const cwd = directory;
  return {
    // (1) session.created → regenerate the derived plane once per session.
    event: async ({ event }: { event: { type: string } }) => {
      if (event.type === "session.created") {
        regenerateDerivedPlane(cwd);
      }
    },
    // (2) chat.system.transform → prepend the SAME assembler stdout to the system prompt.
    //     (hook name MEDIUM-confidence — re-verify `experimental.chat.system.transform` at Phase 3.)
    "chat.system.transform": async (
      _input: unknown,
      output: { parts: string[] },
    ) => {
      const payload = assemblePayload(cwd);
      if (payload) output.parts.unshift(payload);
      return output;
    },
  };
};

export default SessionInjectPlugin;
