# Phase 18d-2: data-driven library growth

Phase 18d-1 can select and compose a fixed primitive DSL from task demonstrations. Phase 18d-2 asks whether repeated learned programs can themselves become reusable primitives without source edits.

## Protocol

Thirteen library-training tasks are solved with the frozen Phase 18d-1 learner. Every learned subtree of cost at least three is normalized across variable names and associative/commutative ordering. A candidate is promoted only when it appears in multiple independent tasks and its minimum-description-length compression gain is positive:

`support * (body_cost - call_cost) - body_cost > 0`.

The post-library tasks are excluded from macro induction. They are then supplied only as data and learned with the base DSL plus the induced macro library under the same maximum search cost of five.

## Required gates

- all source and post-library held-out examples are exact;
- every post-library solution causally uses an induced macro;
- at least four post-library tasks are outside the base learner's cost-five expressible set but become solvable with macros;
- exact motif reuse reduces program evaluations;
- singleton patterns are not promoted;
- post-task ids are absent from source dispatch;
- source changes per macro and per post task are zero.

## Boundary

The promoted macros are compositions of existing primitives. This is automatic concept/library formation and expands effective capability under a fixed search budget, but it is not invention of a genuinely new atomic operation. Task boundaries, structured values, the base DSL, type system, and MDL rule remain human-designed. Raw language pretraining, autonomous task discovery, world-model learning, and high-school intelligence remain unsolved.
