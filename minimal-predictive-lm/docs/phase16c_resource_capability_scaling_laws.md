# Phase 16c: Resource-capability scaling laws

## Motivation

The project must stop treating a chronological sequence of hand-added mechanisms as
if it were a model-size scaling experiment. The Phase 12--16 systems differ in
architecture, supervision, external knowledge, surface adaptation, and benchmark
exposure. Their byte counts therefore cannot answer the question:

> For a fixed learning architecture, how much broadly transferable capability is
> obtained at a given persistent-size, training-information, induction-compute,
> and inference-compute budget?

Phase 16c creates a controlled family of machines analogous to an LLM scaling
suite. All sizes in one campaign are trained from scratch by the same learner,
with the same representation language, data stream, optimizer/search policy, and
evaluation protocol. Only declared resource budgets vary.

## Resource axes

A single parameter count is not sufficient for this architecture. Report the
following independently:

- `B_core`: executable interpreter, learner, codecs, and fixed runtime bits;
- `B_acquired`: induced programs, concepts, routing/index structures, and learned
  codecs;
- `B_knowledge`: retained factual information and provenance;
- `B_active`: peak task-local working-state bits;
- `D_train`: training evidence bits actually read;
- `C_induce`: candidate generation, fitting, proof, and verification operations;
- `C_test`: inference-time proof, search, simulation, and verification operations;
- `R/W`: persistent and working-memory bits read and written;
- `N_deploy`: expected deployment queries over which training and compilation are
  amortized.

For deployment distribution `D`, define the attainable quality frontier

```text
Q*(budget; D) = sup expected quality
```

where the supremum ranges over systems satisfying all declared resource limits.
The research target is an empirical approximation to this frontier, not a claim
of one universally optimal architecture.

## Size-capability theory

### Task-complexity distribution

For a task instance or family `x`, define representation-relative quantities:

- `K(x)`: shortest reusable program/representation description length available
  in the frozen language;
- `I(x)`: irreducible factual information that must be stored or observed;
- `S(x)`: induction/search work needed to discover the program from the training
  evidence;
- `T(x)`: inference/proof work needed after the program is available.

A hard-threshold idealization is

```text
solvable(x; B, C_induce, C_test)
  only if K(x) + I(x) <= B,
          S(x) <= C_induce,
          T(x) <= C_test.
```

For a task distribution, capability breadth is therefore related to the joint
CDF of task complexities:

```text
G(B, C_induce, C_test)
  = P[K + I <= B, S <= C_induce, T <= C_test].
```

Individual capabilities may appear step-like when their shortest useful mechanism
first fits in the budget. Aggregate breadth can remain smooth when task
complexities are distributed over many thresholds.

### Rate-distortion view

For task distribution `D` and loss `L`, define a resource-constrained analogue of
a rate-distortion function:

```text
R_D(epsilon; C_induce, C_test)
  = minimum persistent bits required to reach expected loss <= epsilon
    under the declared training and inference budgets.
```

The inverse curve gives the best attainable loss at each model size. This is the
central mathematical object for the project. It is distribution-, interface-,
and representation-relative; there is no absolute size-to-intelligence law over
all possible tasks.

### Empirical scaling surface

Do not assume a power law before measurement. Fit and compare at least:

```text
loss = L_inf + a B^-alpha + b D_train^-beta
loss = L_inf + a B^-alpha + b C_induce^-gamma + c C_test^-delta
loss = L_inf + f(log B, log D_train, log C_induce, log C_test)
```

where `f` is a monotone low-capacity spline or Gaussian-process baseline. For each
capability axis `j`, map a continuous latent loss or margin to success probability:

```text
p_j = sigmoid((threshold_j - latent_loss_j) / temperature_j).
```

Exact-match accuracy alone is forbidden for fitting emergence because discrete
metrics can turn smooth progress into an artificial cliff. Also record partial
constraint satisfaction, calibrated probability, proof progress, and edit
distance where meaningful.

## Compute-optimal training and deployment

For an expected deployment horizon `N_deploy`, optimize

```text
C_lifetime = C_train + N_deploy * C_inference
```

subject to a quality target, or maximize quality under a fixed lifetime budget.
A small heavily trained machine, a larger lightly trained machine, and a small
machine with more test-time search must be compared at matched lifetime cost.
The optimal allocation can change with deployment volume and task difficulty.

## Controlled scaling campaign

### Frozen campaign contract

Within one campaign, freeze:

1. interpreter and primitive set;
2. representation and serialization language;
3. candidate generator and search policy;
4. raw training mixture and ordering policy;
5. evaluation suites and metrics;
6. knowledge interface and tool permissions.

No benchmark-specific parser, primitive, document, routing cue, or exception may
be added between budget points. Architecture changes start a new named campaign;
they never overwrite an old scaling curve.

### Budget ladder

Use geometric budgets so exponents and thresholds can be estimated:

```text
B_acquired: 1, 4, 16, 64, 256 KiB, 1, 4, 16 MiB
D_train:    2^6, 2^8, 2^10, 2^12, 2^14 interactions or matched evidence bits
C_induce:   10^3, 10^4, 10^5, 10^6, 10^7 candidate/proof operations
C_test:     10^2, 10^3, 10^4, 10^5 operations per item
```

The initial CPU pilot may use a smaller subset of this grid. Every point requires
multiple seeds. Models are rebuilt from scratch; a larger point may not inherit a
human-selected module from a smaller point.

### Evaluation profile

Report a vector rather than one hidden intelligence score:

- raw-language grounding and shifted paraphrase transfer;
- arithmetic and formal reasoning;
- state, temporal, and causal reasoning;
- factual acquisition, provenance, contradiction, and abstention;
- reference and discourse resolution;
- long-horizon memory and sparse retrieval;
- code localization, patching, test repair, and rollback;
- constrained writing and planning;
- unseen-family transfer after training on the same mixture.

A predeclared aggregate may be reported, but all axes and coverage remain visible.

### Forecast validation

Fit laws on the smaller budget points and reserve at least two larger budgets as
forecast targets. A valid scaling claim requires:

- confidence intervals across seeds;
- successful prediction of held-out budget points;
- successful prediction on at least one shifted evaluation mixture;
- comparison against constant, linear-in-log-budget, power-law, and sigmoid
  baselines;
- residual checks for architecture thresholds and saturation;
- no post-hoc deletion of failed tasks.

## First implementation milestone

The first pilot modifies the mixed-task induction pipeline to accept explicit:

- maximum serialized acquired bits;
- maximum candidate evaluations;
- maximum calibration evidence bits;
- maximum inference operations.

Candidate rules are selected by held-out marginal loss reduction per complete
lifetime bit/operation cost, rather than requiring perfect reproduction of all
calibration rows. The pilot uses independent generated families for training and
blind families for evaluation. Existing Phase 13--16 public benchmarks are used
only after the scaling law is frozen.

## Interpretation and claim boundary

A fitted curve can support statements such as:

> Under frozen campaign C1 and task distribution D1, a 64 KiB acquired model
> trained with 10^6 induction operations reaches the estimated median transfer
> level X, while 1 MiB is forecast to reach Y.

It cannot support:

> Any 1 MiB machine is generally intelligent, or this law holds for arbitrary
> future tasks.

The theory supplies a distribution-relative frontier and falsifiable forecasts.
It does not prove that the current representation has LLM-like scaling. A central
research outcome may be that the curve saturates early, search cost grows too
quickly, or a learned neural codec is required. Those are decisive results, not
reasons to attach more manual solvers.
