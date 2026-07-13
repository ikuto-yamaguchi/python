# CAP-GEN-002 novelty and expressivity gate

## Decision on the first factor-graph proposal

The finite-domain factor-graph proposal is rejected as a core research contribution.
It remains useful only as an exact-inference baseline.

A Boolean factor of arity `k` needs `2^k` table entries.  A single unrestricted
`n`-ary factor can encode any Boolean function, but this merely moves the truth
table into the model and costs `Theta(2^n)` entries.  With bounded arity and bounded
induced treewidth `w`, exact elimination can be efficient (`O(n 2^w)`-scale time and
`O(2^w)`-scale working tables), but the representational efficiency comes from an
already supplied sparse factorization.  The proposal did not learn a deep nonlinear
representation or prove an asymptotic resource separation from existing graphical
models, circuits, or program interpreters.

Therefore a successful factor-graph experiment cannot count as progress toward
CAP-GEN-002 unless it predicts and produces improvement on the axis-blind public
reality gate without a task-specific compiler.

## Prior-art families that must not be rediscovered

Every candidate is compared against at least these families:

1. factor graphs and sum-product / variable-elimination inference;
2. sum-product networks and tractable probabilistic circuits;
3. deep arithmetic circuits and hierarchical tensor decompositions;
4. recurrent networks and repeated nonlinear maps;
5. neural programmer-interpreters and external program memories;
6. DreamCoder / Stitch-style library learning;
7. MDL-trained recurrent networks and description-length objectives;
8. ordinary low-rank adapters, sparse mixtures, and modular neural networks.

Recombining these names is not a contribution.  The candidate must identify a
property that the compared model classes do not obtain under matched resources.

## Formal resource model

For architecture class `A`, target function family `F_n`, and error tolerance
`epsilon`, report:

- `K_A(F_n, epsilon)`: minimum executable total description bits, including runtime,
  learned parameters, grammar, indexes, and persistent memories;
- `C_A(F_n, epsilon)`: induction and inference operations separately;
- `M_A(F_n, epsilon)`: peak working memory;
- `D_A(F_n, epsilon)`: data needed to identify the behavior under the frozen protocol.

A universal-approximation statement alone is insufficient.  Universality purchased by
an exponential table, unbounded precision, or unreported runtime fails the gate.

## Required research contribution

A CAP-GEN-002 architecture trial is promotable only if it supplies all four:

1. **Novelty statement** — a precise claim not reducible by reparameterization to the
   prior-art families above;
2. **Expressive-efficiency result** — a theorem, lower-bound separation, or rigorously
   delimited conjecture with falsifying cases, stated in `K/C/M/D` resources;
3. **Acquisition result** — the same learning rule learns from one mixed stream with no
   task, benchmark, subject, or solver identifier;
4. **Reality transfer** — one checkpoint improves several unrelated public axes and a
   prospectively frozen set, without adding an axis-specific parser or handler.

A negative theorem or failed experiment is a valid research result when it removes a
plausible architecture class.  A local synthetic success is not.

## Candidate hypothesis: resource-conditioned nonlinear generator grammar

The next candidate is intentionally a hypothesis, not a novelty claim.

Let a small shared state `z` be transformed by a library of quantized low-rank
piecewise-nonlinear generators:

```
g_j(z, m) = P_j z + U_j rho(V_j z + b_j) + R_j read(m, a_j(z))
```

A prefix-free learned grammar emits recursive compositions of these generators and
sparse memory operations.  The same generator library, state representation,
controller, and acquisition rule are used for every domain.  No task ID selects a
separate learner.

Learning minimizes a lifetime-resource code:

```
J = L(data | theta, grammar, memory)
    + B(theta, grammar, memory, runtime)
    + lambda_train * C_train
    + lambda_infer * C_infer
    + lambda_memory * M_peak
```

A new generator or macro is admitted only when it decreases held-out predictive code
length after paying for its executable bits and resource cost.  Removing a macro must
restore the predicted loss increase; otherwise the macro was decorative and is
rejected.

## What could be new, and what is already known

Already known and therefore not sufficient:

- nonlinear depth can yield exponential efficiency over shallower representations;
- repeated shared maps can create complex behavior;
- program libraries can compress repeated symbolic subprograms;
- MDL can favor compact recurrent solutions;
- low-rank residual maps reduce parameter count.

The unverified novelty hypothesis is narrower:

> Jointly invent quantized nonlinear generators, recursive composition grammar, and
> reusable approximate macros directly from an unlabeled mixed stream by minimizing
> complete lifetime resource code, with certified error propagation and immediate
> cross-domain transfer measurement.

This hypothesis is rejected if an existing method already provides the same formal
objective and guarantees, or if the construction is equivalent to a known method
under a simple reparameterization.

## First theorem targets

Before a large training run, the branch must establish or refute:

1. **Composition growth.**  State conditions under which `m` learned generators induce
   exponentially many distinguishable transformations with composition length while
   generator bits remain fixed.  This is a baseline result and not by itself novel.
2. **Robust macro-sharing bound.**  If a repeated subcomposition is replaced by a
   shared quantized macro with local error `delta` and surrounding Lipschitz constants
   `L_t`, bound final error and total saved bits/operations.  The novelty audit must
   determine whether the exact resource-coupled bound is prior art.
3. **Induction identifiability.**  Give sufficient conditions under which mixed
   observations identify generators or equivalence classes without task labels.
4. **Separation case.**  Exhibit a function family where the candidate has a strictly
   better `K/C/M` frontier than the factor-table baseline and a matched shallow model.
5. **Failure boundary.**  Construct families where generator discovery is
   non-identifiable or where grammar growth becomes linear in tasks.

## Experimental prohibition

Until the theorem targets have a concrete statement, the branch must not add separate
causal, reference, validity, adjective-order, or belief-propagation solvers.  Those five
zero-score axes are evaluation probes, not five development tasks.

The first empirical trial must train one artifact from a mixed stream and evaluate it
unchanged on all five probes plus untouched axes.  A gain confined to one probe is
recorded as specialization failure.
