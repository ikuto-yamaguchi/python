# SPARC-HS16: public proposition-state integration

CAP-GEN-001 froze the older Phase15d worker and measured 398/600 (66.33%) across fifteen public axes. Later research already produced one induced signed-proposition compiler that solved both belief propagation and formal validity, but the integrated public gate still invoked the older worker. HS16 measures the actual integrated checkpoint rather than leaving that capability stranded in an isolated phase.

## Protocol

- Reuse the exact CAP-GEN-001 scoring manifest and its SHA-256.
- Hide every axis name from the worker.
- Use one frozen `phase16f_worker` for all 600 prompts.
- Use no public target as training or calibration data.
- Require every other axis to retain at least its CAP-GEN-001 correct count.
- Require belief propagation and formal validity to reach 40/40 together through the same induced clause compiler and signed-claim graph.

## Why this is not an axis-specific patch

The worker never receives task names. Base propositions, attributed propositions, queries, and controlled formal clauses are compiled into one signed proposition representation. The same queue-based propagation runtime answers both belief chains and formal-validity programs. Unknown surfaces abstain instead of selecting a task handler.

## Claim boundary

Even a successful run is expected to leave reference resolution, causal judgement, and adjective order unresolved. It is a large integrated gain, not Japanese high-school-level general intelligence. HS17 must connect natural-language reference and causal structure to the shared event-state representation and rerun the same frozen gate.
