# Phase 18d-10: residual-driven primitive invention

## Motivation

Phase 18d-9 can grow an active program library from zero, but every active program must still be expressible in the frozen typed DSL. Phase 18d-10 studies the next failure mode: several locally stable residual tasks remain unexplained by that DSL.

The learner receives grouped residual episodes produced after base-DSL synthesis fails. It does not receive the target primitive name or parameters.

## Generic invention meta-grammar

The candidate space contains:

- a lookup-table control;
- length-preserving affine index transducers

\[
y_i = x_{(a i+b) \bmod |x|}
\]

for bounded integer \(a,b\).

This meta-grammar is human-designed and narrow. The target parameter values are selected from data and are not stored in the task file.

A primitive is accepted only when it:

1. fits all induction examples;
2. fits held-out examples from at least two residual episodes;
3. transfers across both strings and number lists;
4. has a single probe-distinct behavior;
5. has positive MDL gain over a literal residual table.

## Post-freeze reuse

After primitive selection, the learner source and primitive library are frozen. Five new task episodes are supplied only as data. They require the invented primitive composed with existing operations:

- case conversion;
- sorting;
- repeated application;
- concatenation;
- list reversal.

The frozen DSL without the primitive and the extended DSL are evaluated separately.

## Controls

- one value type only is insufficient;
- inconsistent residual transformations are rejected;
- identity transformations already expressible by the base DSL are not treated as residual invention;
- a metamorphic campaign with a different hidden index parameter must recover that different parameter.

## Claim boundary

This is controlled primitive invention, not unrestricted operation discovery. Residual episodes are pre-grouped, the affine-index meta-grammar is hand-designed, and invention is batch rather than online at raw-byte scale. No natural-language semantics, arbitrary computation, LLM parity, or high-school intelligence is claimed.
