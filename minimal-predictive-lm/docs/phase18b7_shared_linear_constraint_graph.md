# Phase 18b-7: shared linear-constraint graph

## Question

Can the separately implemented Phase 18b-3 through 18b-6 capabilities be represented by one compact mathematical substrate instead of four solver-specific execution paths?

## Representation

Every compiler emits a `ConstraintGraph` containing exact rational linear constraints:

- affine equation: one equality over one variable,
- simultaneous equations: equalities over two variables,
- inequalities: one-variable order constraints,
- unit-rate word problems: two equalities over two unknown counts.

The shared solver performs exact rational elimination or exact interval intersection. The shared verifier reconstructs the canonical solution from the graph and rejects altered answers or proofs.

## Gates

- 100% accuracy, coverage, and proof replay on a frozen 12-problem mixed-family suite.
- Constraint order must not affect the result.
- Variable renaming must not affect the result.
- Underdetermined, inconsistent, empty, and unsupported multi-variable inequality systems must abstain.
- No learned payload is claimed: the compilers and solver are fixed source code.

## Claim boundary

This phase is consolidation. It demonstrates a reusable exact linear core, but adds no new mathematics and does not solve schema induction, free Japanese parsing, nonlinear reasoning, or high-school intelligence.
