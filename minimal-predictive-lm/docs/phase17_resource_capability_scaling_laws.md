# Phase 17: Resource-capability scaling laws

## Goal

The chronological Phase 12--16 sequence is not a valid model-size scaling experiment because architecture, supervision, external knowledge, surface adaptation, and benchmark exposure all changed between phases.

Phase 17 instead trains a controlled family from scratch with one frozen learner and varies only declared resource budgets. The question is:

> For a fixed learning architecture and workload distribution, how much transferable capability is obtained at each persistent-size, training-information, induction-compute, and inference-compute budget?

## Resource axes

Report these quantities independently:

- `B_core`: interpreter, learner, fixed codecs, and runtime bits;
- `B_acquired`: induced programs, concepts, routing/index structures, and learned codecs;
- `B_knowledge`: retained facts and provenance;
- `B_active`: peak task-local state bits;
- `D_train`: training evidence bits actually read;
- `C_induce`: candidate generation, fitting, proof, and verification operations;
- `C_test`: inference-time proof, search, simulation, and verification operations;
- `R/W`: memory bits read and written;
- `N_deploy`: expected deployment queries used to amortize induction and compilation.

For deployment distribution `D`, define the attainable frontier

```text
Q*(budget; D) = sup expected quality
```

where the supremum ranges over systems satisfying every declared limit.

## Size-capability theory

For task instance or family `x`, define representation-relative quantities:

- `K(x)`: shortest reusable program or representation available in the frozen language;
- `I(x)`: irreducible factual information that must be stored or observed;
- `S(x)`: induction/search work needed to discover that program from evidence;
- `T(x)`: inference/proof work needed after the program is available.

A hard-threshold idealization is

```text
solvable(x; B, C_induce, C_test)
  only if K(x) + I(x) <= B,
          S(x) <= C_induce,
          T(x) <= C_test.
```

Capability breadth is then related to the joint task-complexity distribution:

```text
G(B, C_induce, C_test)
  = P[K + I <= B, S <= C_induce, T <= C_test].
```

Individual abilities may appear step-like when their shortest useful mechanism first fits. Aggregate breadth may look smooth when task thresholds are distributed broadly.

## Rate-distortion view

For task distribution `D` and loss `L`, define

```text
R_D(epsilon; C_induce, C_test)
  = minimum persistent bits required for expected loss <= epsilon
    under the declared induction and inference budgets.
```

Its inverse is the central empirical size-to-capability curve. It is relative to the workload, interface, representation language, and search policy. There is no absolute byte-to-intelligence law over arbitrary tasks.

## Candidate empirical laws

Do not assume a power law before measurement. Compare at least:

```text
loss = L_inf + a B^-alpha + b D_train^-beta
loss = L_inf + a B^-alpha + b C_induce^-gamma + c C_test^-delta
loss = L_inf + f(log B, log D_train, log C_induce, log C_test)
```

where `f` is a monotone low-capacity model. Exact-match alone is not enough because it can turn smooth progress into an artificial emergence cliff. Also record partial constraint satisfaction, proof progress, edit distance, confidence calibration, and correct abstention.

## Lifetime compute allocation

For expected deployment horizon `N_deploy`, optimize

```text
C_lifetime = C_train + N_deploy * C_inference
```

A small heavily trained model, a larger lightly trained model, and a small model with deeper test-time search must be compared at matched lifetime cost.

## Frozen campaign contract

Within one named campaign, freeze:

1. interpreter and primitive set;
2. representation and serialization language;
3. candidate generator and search policy;
4. raw training mixture and ordering policy;
5. evaluation suites and metrics;
6. knowledge interface and tool permissions.

No benchmark-specific parser, primitive, document, routing cue, or exception may be added between budget points. An architecture change starts a new campaign and never overwrites an old curve.

## Full budget ladder

```text
B_acquired: 1, 4, 16, 64, 256 KiB, 1, 4, 16 MiB
D_train:    2^6, 2^8, 2^10, 2^12, 2^14 interactions or matched evidence bits
C_induce:   10^3, 10^4, 10^5, 10^6, 10^7 candidate/proof operations
C_test:     10^2, 10^3, 10^4, 10^5 operations per item
```

The CPU pilot may use a smaller geometric ladder. Every point uses multiple seeds and is rebuilt from scratch.

## Evaluation vector

- raw-language grounding and shifted paraphrase transfer;
- arithmetic and formal reasoning;
- state, temporal, and causal reasoning;
- factual acquisition, provenance, contradiction, and abstention;
- reference and discourse resolution;
- long-horizon memory and sparse retrieval;
- code localization, patching, test repair, and rollback;
- constrained writing and planning;
- unseen-family transfer.

## Forecast validation

Fit only smaller budget points and reserve at least two larger points as forecast targets. A scaling claim requires:

- confidence intervals across seeds;
- successful prediction of held-out budget points;
- successful prediction on a shifted evaluation mixture;
- comparison with constant, linear-in-log-budget, power-law, and sigmoid baselines;
- residual checks for thresholds and saturation;
- no post-hoc removal of failed task families.

## Phase 17a CPU pilot

The first implementation adds explicit limits for:

- serialized acquired bits;
- calibration evidence bits;
- candidate search per fitting attempt, with total evaluations reported;
- inference operations per item.

Candidate rules are consolidated under the acquired-bit budget by held-out marginal correctness gain per added bit. Training/selection examples are generated independently from the final blind suite. Existing public Phase 13--16 benchmarks remain untouched until the campaign contract and curve-fitting procedure are frozen.

The first version is deliberately labelled a pilot because the current mixed learner exposes a per-fit candidate cap rather than a strict global induction-operation interrupt. Total induction operations are measured, and a strict global limiter is a required follow-up before extrapolating.

## Claim boundary

A valid curve may support a statement such as:

> Under frozen campaign C1 and workload D1, a 64 KiB acquired model trained with 10^6 induction operations reaches transfer level X, and a held-out 1 MiB point is predicted at Y.

It cannot support:

> Any 1 MiB machine is generally intelligent.

The curve may saturate early, candidate search may grow too quickly, or raw-language grounding may require a learned neural codec. Those are decisive outcomes rather than reasons to attach manual solvers.
