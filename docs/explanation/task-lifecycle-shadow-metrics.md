# Task lifecycle shadow metrics

These definitions are for future policy observation only. They are not production measurements, release evidence, or substitutes for deterministic gates.

| Metric | Definition | Collection boundary |
|---|---|---|
| `lane_override` | Count and direction of a recorded human lane override, keyed by task and policy hash. | Packet metadata; never infer from prose. |
| `ceremony_count` | Number of user-visible lifecycle checkpoints: intake, required review, verify, and explicit human gates. | Fixture/evaluation event list. |
| `gate_failure_reason` | Stable tool error category emitted by an existing gate. | Existing gate result; do not normalize away failures. |
| `evidence_completeness` | Required acceptance criteria and constraints with passing, hash-valid evidence divided by required total. | Evidence index at a fixed state revision. |
| `handoff_reconstruction_time` | Elapsed monotonic time from fresh-process orient start to successful snapshot reconstruction. | Eval harness only until a separately approved production collector exists. |

Any collection design needs a later contract and human approval. This document deliberately declares no threshold, target, rate, or claim of observed performance.
