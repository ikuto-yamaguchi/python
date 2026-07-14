# CAP-GEN-002-EPQ-001: executable predictive quotient

## Purpose

The research goal is not to accumulate synthetic solvers. It is to find a mathematically
new route to general learning with minimum executable bits, induction compute, inference
compute, and peak memory. RII-001--003 removed several supplied structures, but RII-003
still cannot map a wholly unseen surface context into an existing role unless that surface
participates in an observable relation.

This document starts from theory. No benchmark handler or subject-specific parser is
permitted until the propositions below survive the prior-art and falsification gates.

## What is already known and is not the contribution

The central idea "two histories are the same state when all relevant futures are the
same" is old and deep:

- causal states / epsilon-machines are minimal sufficient predictive states;
- predictive state representations encode state using predictions of observable tests;
- epsilon-transducers extend causal-state ideas to input-output mappings;
- bisimulation and Myhill--Nerode quotients merge behaviorally indistinguishable states;
- causal rate-distortion and information bottleneck methods trade representation rate
  against predictive distortion;
- time-bounded Kolmogorov complexity and speed priors combine program length and runtime;
- enumerative program synthesis uses observational equivalence to quotient programs.

Therefore, merely clustering contexts by future behavior, adding an MDL term, or pruning
observationally equivalent programs is not a new theory.

Primary starting points for the audit:

- Shalizi and Crutchfield, causal states and minimal optimal prediction:
  https://arxiv.org/abs/cond-mat/9907176
- Singh, James, and Rudary, predictive state representations:
  https://arxiv.org/abs/1207.4167
- Barnett and Crutchfield, epsilon-transducers:
  https://arxiv.org/abs/1412.2690
- Ferns, Panangaden, and Precup, bisimulation metrics:
  https://arxiv.org/abs/1207.4114
- Marzen and Crutchfield, causal rate-distortion:
  https://arxiv.org/abs/1412.2859
- Lu and Oliveira, time-bounded / probabilistic Kolmogorov complexity survey:
  https://arxiv.org/abs/2205.14718
- Feser, Dillig, and Solar-Lezama, observational similarity in synthesis:
  https://arxiv.org/abs/2206.06164

The exact novelty of the construction below is **unverified**. The current audit has not
yet found a framework that jointly charges executable code for the predictive state,
probe language, updater, and decoder together with induction/inference operations and
peak memory, while learning the probe set itself from one raw mixed stream. Absence from
this initial audit is not evidence of novelty.

## Finite deterministic foundation

Let an experience system be

```text
E = (H, Q, Y, response, successor).
```

- `H` is a finite set of observable histories or raw contexts.
- `Q` is a finite prefix-free set of executable probes.
- `Y` is the observable response set.
- `response(h, q)` is the response when probe `q` is applied after history `h`.
- `successor(h, q)` is the resulting history state after the response.

Every probe has a declared resource vector

```text
r(q) = (executable_bits, operations, peak_memory).
```

For a budget `b`, let `Q_b` contain exactly the probes whose resources fit `b`.

### Definition 1: budgeted executable predictive congruence

`h ~=_b h'` is the greatest relation satisfying, for every `q in Q_b`,

```text
response(h, q) = response(h', q)
successor(h, q) ~=_b successor(h', q).
```

This is a resource-indexed behavioral quotient. The quotient itself is a bounded
bisimulation / Nerode-style object and is not claimed as novel.

### Definition 2: executable predictive machine

An executable predictive machine is

```text
M = (Z, encode, emit, update, probe_library, runtime).
```

It is exact on `Q_b` when for every reachable history and admissible probe:

```text
emit(encode(h), q) = response(h, q)
update(encode(h), q, response(h, q)) = encode(successor(h, q)).
```

Its complete lifetime resource vector is

```text
R(M) = (
    K_exec,
    C_induce,
    C_infer,
    M_peak,
    D_support
).
```

`K_exec` includes the executable state encoder, selected probes, update program, decoder,
runtime, persistent indexes, and parameters. Training and inference operations are never
combined. A model is Pareto-dominated when another exact model is no worse in every
coordinate and strictly better in at least one.

### Definition 3: resource-canonical representative

For a fixed observable behavior, budget, candidate machine language, and deterministic
coding convention, the resource-canonical set is the Pareto frontier of exact machines
after quotienting state names and observationally equivalent executable programs.

A single representative may be selected only after declaring scalar weights or a strict
lexicographic policy. It is not meaningful to call an unweighted representative the true
latent model.

## Proposition 1: exact predictors cannot merge distinguishable histories

If `h` and `h'` are not equivalent under `~=_b`, every exact executable predictive
machine must encode them into different predictive states.

### Proof sketch

By non-equivalence, a finite admissible probe continuation exists whose first differing
response occurs at some depth. If both histories share one machine state, deterministic
`emit` and `update` produce the same response and same next machine state at every prior
step, including the differing step, contradicting exactness.

### Consequence

Every exact machine needs at least as many reachable machine states as the number of
`~=_b` equivalence classes. With fixed-length state identifiers, it needs at least
`ceil(log2 N_b)` state bits for `N_b` classes, before charging transition/update code.

## Proposition 2: the quotient is sufficient under update closure

If `~=_b` has finite index and is closed under every successor induced by `Q_b`, then the
quotient classes themselves form an exact predictive machine on `Q_b`.

### Proof sketch

Define `emit([h], q) = response(h, q)` and
`update([h], q, y) = [successor(h, q)]`. Congruence guarantees that neither definition
depends on the chosen representative. Therefore the quotient is exact.

This is a standard automata/bisimulation-style result. It is included as a correctness
boundary, not as the research contribution.

## Proposition 3: unseen-surface no-free-lunch

Suppose a surface context `u` never appears in training and no observed or admissible
probe connects `u` to a trained context. Then no learner can guarantee assigning `u` to
the correct latent role, even with perfect training accuracy.

### Counterexample

Construct two worlds that are identical on all training observations and probes. In world
A, `u` has role 0; in world B, `u` has role 1. Swap only the unobserved responses of `u`.
The learner receives identical data in both worlds and therefore returns the same answer,
which must be wrong in one world.

### Consequence for RII-003

A wholly unseen context spelling cannot be classified from surface novelty alone. The next
system needs at least one of:

- a separating observable continuation;
- an intervention or substitution connecting it to known roles;
- a learned generative nuisance action whose invariance is itself observable;
- an auxiliary view whose relation to behavior is independently identified.

Inventing a similarity metric without one of these assumptions does not solve the
identifiability problem.

## Proposition 4: finite separating probes identify the quotient up to permutation

Let the true quotient contain `N` classes. If a finite probe subset `S` has a distinct
response signature for every pair of quotient classes and the observed successor table is
closed on those classes, then the quotient machine is identifiable from the complete
`S` response/update table up to a permutation of state names.

Removing the separation condition restores Proposition 3 ambiguity. Removing update
closure allows histories with identical immediate signatures but different deeper futures
to collapse incorrectly.

## Proposition 5: minimum-cost probe discovery is a minimum-test problem

For every unordered pair of candidate classes, define it as "covered" by probe `q` when
that probe gives different responses for the pair. Selecting a minimum-cost separating
probe set is exactly a weighted cover problem over class pairs.

Consequences:

- exhaustive optimal probe selection is combinatorial in the worst case;
- a greedy rule that maximizes newly separated class-pairs per resource cost is a
  principled approximation baseline;
- a new probe must pay for its executable bits, execution cost, and persistent support;
- brute-force expansion of the probe language cannot be presented as a scalable theory.

This reduction is related to the established minimum test set / distinguishing test
literature and is not itself a novelty claim.

## Proposition 6: no resource-independent single optimum exists

There are exact predictors `A` and `B` for the same quotient such that:

```text
K_exec(A) < K_exec(B)
C_infer(A) > C_infer(B).
```

For example, `A` can store a short algorithm and recompute a response, while `B` stores a
larger lookup table and answers in constant time. Neither dominates the other.

Therefore "smallest model" is undefined unless the complete resource vector or scalar
policy is declared. Minimum state count, minimum parameter count, minimum codelength, and
minimum runtime are different optimization problems.

## Proposition 7: finite resource-canonical sets exist, uniqueness generally does not

For a finite machine language, finite resource limits, and finite exact behavior table,
there are finitely many candidate machines. Hence a nonempty Pareto frontier exists.

The frontier can contain several observationally equivalent machines. A unique code can
be forced by deterministic tie-breaking, but this creates a canonical *encoding*, not a
uniquely true internal semantics. A strict resource gap is required before claiming
stability of the chosen representative.

## Candidate research contribution

The quotient theory above is mostly established mathematics. The unverified research
hypothesis is the following joint construction:

> Learn, from one raw mixed stream, an executable probe language and an update-closed
> predictive quotient while minimizing the Pareto vector of complete executable bits,
> induction operations, inference operations, peak memory, and identifying support;
> canonicalize only within observable-equivalence classes and require immediate transfer
> to several unrelated frozen evaluations.

What may distinguish this from causal states, PSRs, epsilon-transducers, causal
rate-distortion, and time-bounded description complexity is not any component alone, but
the joint charging and acquisition of:

1. the probes used to define the state;
2. the state encoder and update closure;
3. the response decoder;
4. the induction algorithm and its search work;
5. the inference runtime and peak memory;
6. the data/support needed to identify every quotient refinement.

This hypothesis is rejected if a prior method already supplies the same formal object and
resource guarantees, or if the joint objective reduces to an existing framework under a
simple reparameterization.

## Immediate theory experiment

The first implementation is limited to finite exact tables and must verify:

1. quotient necessity and sufficiency;
2. the unseen-surface counterexample;
3. exact and greedy separating-probe selection;
4. Pareto non-collapse of code bits versus inference operations;
5. canonical tie handling and abstention when the resource gap is zero;
6. observational program quotienting only as a known search optimization.

It must not train on causal judgement, reference resolution, formal validity, adjective
order, belief propagation, or any other public axis. Those remain frozen evaluation
probes.

## Promotion gate

EPQ-001 is theory groundwork, not CAP-GEN-002 promotion. A later learner is promotable
only when one frozen artifact:

- acquires its probe/state/update language from one mixed raw stream;
- maps prospectively unseen surfaces using genuinely separating evidence;
- improves several unrelated public axes without axis-specific code;
- reports `K/C/M/D` and beats matched baselines on a Pareto frontier;
- preserves the previously solved axes;
- survives a broader prior-art audit and an explicit novelty challenge.
