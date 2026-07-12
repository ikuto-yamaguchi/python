# Phase 13a: frozen public multi-domain baseline

## Research question

Can the Phase 12 learner process genuinely public tasks outside its calibrated capability family without benchmark-specific code, primitives, or examples?

Phase 13a deliberately does **not** attempt to improve the model. It establishes a failure boundary before any adaptation.

## Public suite

The benchmark contains 200 raw prompts:

- 40 Google BIG-bench direct-arithmetic examples
- 40 BIG-Bench-Hard boolean-expression examples
- 40 BIG-Bench-Hard multistep-arithmetic examples
- 40 BIG-Bench-Hard object-counting examples
- 40 BIG-Bench-Hard word-sorting examples

Every source file is retrieved from a pinned public Git blob. The combined manifest is deterministic and checksum-addressed.

## Anti-specialization protocol

Before downloading the benchmark, the Phase 12 model is induced from its original forty interactions and serialized into a stable fingerprint.

The benchmark run requires:

1. zero exact calibration-prompt overlap;
2. zero benchmark examples used as calibration;
3. zero benchmark-specific handlers;
4. zero new primitives;
5. the same model fingerprint before and after evaluation;
6. raw prompts only—the model does not receive task names or axes.

Axis labels exist only in the scorer and failure report.

## Result

The model obtains 40/200 overall:

- direct arithmetic: 40/40;
- every other public axis: 0/40.

All 160 failures are explicit abstentions, not wrong answers. This means the existing routing/type system detects that no learned program applies. It does **not** mean the missing capabilities are solved.

## Interpretation

The baseline separates two properties that are often confused:

- **calibration**: do not invent an answer outside the known program family;
- **generality**: acquire and compose the missing program family from domain-neutral evidence.

Phase 13a demonstrates the first and fails the second.

The four missing public capabilities share more structure than four unrelated benchmark names suggest:

- boolean and multistep arithmetic both require recursive expression composition, operator semantics, and precedence;
- object counting and word sorting both require variable-length sequence extraction, element roles, and a query-dependent reduction;
- all four require a raw-text codec that creates typed atoms instead of only extracting numbers and `key=value` fields.

The next phase must therefore add a reusable sequence/expression representation and induce its operators from independent interactions. Adding four benchmark handlers would invalidate the research objective even if it produced 100% accuracy.

## Claim boundary

Phase 13a authorizes only the statement that a frozen, 892-byte Phase 12 payload achieves 20% on this public five-axis slice while abstaining on all unsupported axes.

It does not authorize public multi-domain parity, runtime Pareto, broad LLM comparison, or evidence of human-level reasoning.
