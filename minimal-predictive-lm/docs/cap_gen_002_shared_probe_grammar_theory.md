# CAP-GEN-002-SPG-001: shared probe grammar theory

## Why this comes after EPQ-001

EPQ-001 showed that a wholly unseen surface cannot be assigned to a known predictive
role unless some observable probe, intervention, invariance, or auxiliary view separates
the roles. It also reduced exact probe selection to a minimum-test problem.

A naive next step would assign each candidate probe an independent cost and greedily add
the probe that separates the most unresolved class pairs per bit. That is incorrect when
probes share a runtime, parser, loop body, memory accessor, or other executable component.
The shared component must be paid once, not once per probe.

This document establishes the resource model and a negative theorem before implementing a
probe learner.

## Prior-art boundary

The following are already known and are not the contribution:

- adaptive distinguishing sequences and active automata learning;
- exact and interactive submodular set cover;
- adaptive submodularity for active learning;
- submodular-cost submodular-cover optimization;
- observational equivalence and active program synthesis.

Relevant primary sources include:

- Frohme, adaptive distinguishing sequences:
  https://arxiv.org/abs/1902.01139
- Vaandrager et al., apartness-based active automata learning:
  https://arxiv.org/abs/2107.05419
- Guillory and Bilmes, interactive submodular set cover:
  https://arxiv.org/abs/1002.3345
- Golovin and Krause, adaptive submodularity:
  https://arxiv.org/abs/1003.3967
- Crawford, Kuhnle, and Thai, submodular-cost submodular cover:
  https://arxiv.org/abs/1908.00653
- Barnaby et al., active learning for neurosymbolic program synthesis:
  https://arxiv.org/abs/2508.15750

Thus neither a greedy query policy nor a shared-library cost is a novelty claim.

## Executable component model

Let `C` be a finite set of executable components. Each component `c` has prefix-free code
length `k(c)`. A probe `q` consists of:

```text
components(q) subset C
wrapper_bits(q)
execution_operations(q)
peak_memory(q)
separated_pairs(q)
```

For a selected probe set `S`, executable code is

```text
K(S) = runtime_bits
     + sum(k(c) for c in union(components(q), q in S))
     + sum(wrapper_bits(q) for q in S).
```

The component union is essential: shared parsers, interpreters, memories, and macros are
charged once. Inference operations are charged per actual execution and are not hidden in
`K(S)`.

Let `U` be all unresolved unordered predictive-state pairs. The identification benefit is

```text
F(S) = size(union(separated_pairs(q), q in S)).
```

Exact identification requires `F(S) = size(U)` plus successor/update closure from EPQ-001.

## Proposition 1: shared executable code is monotone submodular

Ignoring the modular wrapper term, `K(S)` is a weighted coverage function over executable
components. Therefore it is monotone and has diminishing marginal cost:

```text
A subset B  =>  K(A union {q}) - K(A)
              >= K(B union {q}) - K(B).
```

The more of the grammar already exists, the cheaper a related probe becomes.

## Proposition 2: pair-separation benefit is monotone submodular

`F(S)` is also a coverage function, now over unresolved class pairs. Adding a probe never
removes a distinction, and its number of newly separated pairs can only decrease as the
selected set grows.

## Proposition 3: the exact objective is a known hard optimization family

Minimizing shared executable cost subject to complete pair separation is an instance of
submodular-cost submodular cover. Adding uncertain outcomes and adaptive probe choice
connects it to interactive/adaptive submodular cover and active automata learning.

This classification is useful because it prevents us from renaming a known optimization
problem as a new intelligence theory. It also means unrestricted exact search is not a
scalable acquisition mechanism.

## Proposition 4: independent per-probe accounting can reverse the optimum

Consider two required distinctions, each obtainable either through a shared grammar or a
direct standalone probe.

```text
shared core: 10 bits
shared leaf A: 1 bit
shared leaf B: 1 bit
direct A: 7 bits
direct B: 7 bits
```

The true cost of both shared probes is `10 + 1 + 1 = 12` bits, while both direct probes
cost `14` bits. Independent accounting charges the shared core twice and reports
`11 + 11 = 22`, incorrectly selecting the direct pair.

Therefore RII/EPQ resource accounting must operate on the executable union, not on a sum
of isolated model cards.

## Proposition 5: one-step marginal greedy can be arbitrarily bad

For `n` required distinctions, construct:

- one shared core of cost `B`;
- `n` shared leaves of cost `1`, one per distinction;
- `n` direct probes of cost `B-1`, one per distinction.

The shared bundle costs `B+n`. The direct bundle costs `n(B-1)`.

From the empty set, every shared probe has marginal cost `B+1`, while its corresponding
direct probe costs `B-1` for the same immediate benefit. A one-step marginal greedy rule
therefore chooses every direct probe, costing `n(B-1)`.

Choose `B=n^2`. The approximation ratio is

```text
n(B-1) / (B+n) -> n
```

as `n` grows. Hence no constant approximation guarantee is possible for that naive rule
on this family.

The failure is not a coding bug. Shared setup cost creates a bundle whose value is visible
only after several related probes are considered together.

## Proposition 6: observational probe quotienting is only conditionally safe

Two probes that produce identical responses on the current finite hypothesis set may be
collapsed for the current search. They can still differ on a prospectively unseen state.
Therefore observational quotienting is safe only relative to a declared frozen hypothesis
set or when a theorem proves equivalence for the entire admissible process family.

Pruning current duplicates and then claiming universal equivalence would repeat the same
identifiability mistake EPQ-001 rejected.

## Consequence for the architecture

A scalable probe learner cannot be:

```text
repeat:
    choose one probe with best immediate separated-pairs / isolated-cost ratio
```

It needs a mechanism that can propose and evaluate shared grammar bundles. Candidate
mechanisms include:

1. lower bounds plus branch-and-bound over component unions;
2. bounded bundle lookahead;
3. learned macro proposals from repeated executable prefixes;
4. column generation over component/probe incidence;
5. prospective validation before observationally equivalent probes are removed.

Items 1--4 are established optimization/program-synthesis ideas. Their use is engineering,
not the research contribution.

## Unverified novelty candidate

The remaining hypothesis is narrower:

> Acquire a shared executable probe grammar and an update-closed predictive quotient
> jointly from one raw mixed stream, charging each reusable component once, every probe
> execution each time it runs, and every identifying observation in support; require the
> same acquired grammar to refine several unrelated frozen behaviors.

The candidate contribution would need a theorem or resource separation that is not
already supplied by submodular cover, active automata learning, program-library learning,
or predictive-state theory.

## Immediate finite theory gate

The implementation must verify:

1. shared code and separation coverage are submodular on finite examples;
2. true shared accounting and isolated accounting choose different probe sets;
3. the parameterized greedy counterexample grows with `n`;
4. exact search recovers the shared bundle;
5. one-step marginal greedy takes the direct bundle;
6. observational duplicate pruning fails on an unseen row;
7. no benchmark, subject, task, or axis identifier enters the API.

## Research prohibition

Do not respond to this result by adding a new semantic probe for each failed public axis.
The next empirical learner must acquire generic executable components and probe bundles
from a mixed stream. A gain isolated to one benchmark family is specialization failure.
