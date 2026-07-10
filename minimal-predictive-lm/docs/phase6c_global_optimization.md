# Phase 6c: local optimization is not enough

## Decision

The machine must not optimize only the next action, the current episode, or the currently visible benchmark.
A representation change, compiled shortcut, memory write, cache, tool action, or new primitive is accepted only against a **lifetime constrained objective** evaluated across:

- the current task
- future tasks drawn from the expected workload
- held-out and shifted task families
- multiple relevant horizons
- migration and rollback cost
- information acquisition and search cost
- static and dynamic memory
- bits read and written
- primitive operations and external effects
- training, synthesis, compiler, and verification cost amortized over deployment

## Outer and inner optimization

The research separates two levels.

### Inner problem: solve a task under a fixed machine

For machine architecture and representation `A`, choose actions and computation adaptively:

```text
pi_A = argmin task loss + runtime state + reads + writes + operations + effects
```

This includes the value-of-computation decision from Phase 6b.

### Outer problem: choose the machine over its deployment lifetime

```text
A* = argmin_A E_{task stream, horizon, shift}[
       task loss
     + static program and knowledge bits
     + dynamic memory
     + reads and writes
     + operations and effects
     + adaptation and migration
     + synthesis/training/compiler/verification amortization
     + regret on held-out tasks
]
```

A locally cheap representation is rejected when it creates larger future storage, prevents sharing, increases migration cost, or fails to transfer.

## No single representation is globally best for every workload

Global optimization does not mean choosing one universal structure forever.
It means selecting the cheapest representation **conditional on the workload distribution and lifetime**.

Examples:

- a one-off arbitrary fact may be best stored exactly
- a repeated algebraic family may be best represented by one rule plus parameters
- mostly regular data with a few irregular cases may be best represented by a shared rule plus exact exceptions
- an unstable workload may favor reversible caches until evidence justifies compilation

The global machine is therefore a Pareto-selected mixture of exact data, reusable programs, and temporary computation—not a commitment to symbolic rules or caching alone.

## Anti-local-minimum mechanisms

Exact global optimization is generally impossible for open-ended environments, so the implementation must expose how far it is from a lower bound.

Use, where applicable:

1. exact oracle search on finite micro-worlds
2. admissible lower bounds and branch-and-bound
3. dynamic programming and state equivalence merging
4. multiple abstraction candidates kept on the Pareto frontier
5. held-out and adversarial task families
6. reversible early decisions and explicit rollback cost
7. periodic global recompilation, deduplication, merge, and deletion
8. ablation: remove each cache, rule, index, and primitive and remeasure lifetime cost
9. regret curves over multiple deployment horizons
10. no-regret online adaptation when the workload distribution is unknown

## Local compilation rule

A shortcut or specialized program may be compiled only when at least one condition holds:

- it is losslessly reversible at low cost
- it is optimal under all plausible workload models still under consideration
- its expected lifetime saving exceeds program bits, discovery cost, migration cost, and generalization loss
- it lies on the measured Pareto frontier and does not dominate a more reusable representation only on the training sample

## Phase 6c experiment

The deterministic workload contains 64 tasks:

- 56 share an affine rule and differ only in small parameters
- 8 are genuine exceptions that must be stored exactly
- each task is first observed through two examples and later queried repeatedly

Compared representations:

1. exact per-case cache
2. a duplicated affine program per task
3. one shared affine schema plus exact exceptions
4. local cache first, then later migration to the shared representation

The first two examples make exact caching locally cheapest. Over four or more queries per task, the shared schema becomes globally cheapest. At 16 queries:

- myopic committed cache: 16,384 cost units
- later reoptimization with migration: 7,152
- global lifetime selection from the start: 4,032

On 32 unseen affine tasks with 16 queries each:

- exact cache: 8,192 bits
- shared schema parameters: 320 bits

This experiment is deliberately small. Its purpose is to make local/global disagreement measurable before attempting repository-scale coding agents.

## Research requirement

Every future result must report at least:

```text
current-episode cost
lifetime cost at several horizons
held-out transfer cost
migration / rollback cost
lower bound or oracle gap where available
Pareto status against simpler representations
```

A method that wins only the immediate task is not accepted as progress toward the minimum machine.
