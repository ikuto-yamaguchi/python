# CAP-GEN-002: first-principles ultra-light intelligence program

## Research question

Can a system with local-PC-scale lifetime resources acquire broad, human-level or
stronger intelligence by replacing dense, globally updated parameter tensors with a
minimal predictive state, sparse event-driven computation, an external memory, and a
self-compiled reusable operator library?

This is an open research question.  The program must neither assume that neural
networks are necessary nor assume that a symbolic machine is sufficient.

## What the human brain does and does not prove

The brain is evidence that physics permits highly capable intelligence at low operating
power.  It is not proof that a commodity CPU can reproduce that capability with the
same power or that the lifetime cost is only the adult brain's instantaneous power.
Evolution, development, embodiment, specialised in-memory hardware, massive
parallelism, sparse signalling, and continual adaptation are part of the biological
system.

The valid conclusion is narrower and important: today's dense accelerator workload is
not a known lower bound for intelligence.

## Assumptions explicitly rejected

The critical path must not assume any of the following without evidence:

- intelligence is best represented by one large dense parameter tensor;
- every input requires activating most of the model;
- learning requires global back-propagation through all parameters;
- knowledge, working state, episodic memory, and executable skill must share one store;
- architecture must remain fixed while knowledge grows;
- a model must repeatedly recompute facts that could be retrieved or execute skills
  that could be compiled;
- Transformer scaling laws are laws of intelligence rather than measurements of one
  architecture and training regime.

## Two targets that must not be conflated

1. **Local execution target**: a previously learned human-level system runs on a local
   PC within a strict RAM, energy, and latency envelope.
2. **Local acquisition target**: the same class of machine can acquire that capability
   from raw experience on a local PC without datacentre pretraining.

The second target is substantially stronger.  Results must always say which target is
being tested.

## Core hypothesis

The working hypothesis is that intelligence can be decomposed into four resource-aware
objects:

1. **Minimal predictive state**: retain only distinctions between histories that change
   future predictions or decisions.
2. **Sparse event-driven transition system**: update only state components causally
   touched by the new observation or action.
3. **External episodic and semantic memory**: store rare facts outside the executable
   core, with explicit retrieval cost and provenance.
4. **Self-compiled operator library**: when a recurring predictive computation appears,
   compile it into a reusable parameterised microprogram; delete it when lifetime
   resource savings disappear.

A neural component may be used for perception or approximation, but it is not privileged
as the universal substrate.  Finite automata, registers, stacks, graphs, arithmetic
operators, sparse associative memories, state-space maps, and small neural functions
compete under the same resource objective.

## Lower-bound-first methodology

For every controlled process, first estimate the minimum number of future-distinguishable
states.  For deterministic finite processes this is the observational quotient measured
by `cap_gen_002_predictive_state_lower_bound.py`.  The minimum persistent state naming
cost is at least `ceil(log2(q))` bits for `q` distinguishable quotient states.

This does not solve natural language.  It exposes whether a candidate spends 1 MB to
represent a process whose predictive state needs two bits.

When finite predictive state grows without bound, the learner must not merely allocate
more states.  It tests the next cheapest memory primitive in a hierarchy:

1. finite state;
2. bounded counters/registers;
3. stack or queue;
4. sparse graph/associative memory;
5. reusable recursive microprogram;
6. continuous approximator only where discrete structure is insufficient.

The hierarchy is selected by held-out predictive code plus complete lifetime resource
cost, not by task or benchmark identity.

## Lifetime resource objective

Every candidate reports the unweighted tuple:

- executable runtime and learned description bits;
- persistent predictive-state bits;
- external memory bits and retrieval indexes;
- training operations;
- inference operations per event;
- peak working memory;
- prediction or decision loss;
- energy when measurable.

A weighted scalar may guide search, but no result may hide a regression in one resource
inside an aggregate score.

## First architecture experiment

The first full experiment will learn one artifact from a single mixed, taskless stream.
The stream contains regular, counting, nested, relational, algorithmic, and noisy
segments without subject labels.  The learner may grow state and memory primitives only
when a cheaper class fails a prospective held-out prediction test.

The artifact is then frozen and evaluated on all CAP-GEN public axes.  No axis-specific
parser, solver, prompt template, or retraining is permitted.

The experiment must compare, under matched executable bits and operation budgets:

- byte n-gram/context tree;
- minimal finite predictive-state learner;
- register/stack extension;
- small recurrent or selective state-space baseline;
- self-compiled predictive machine;
- the current integrated worker.

## Breakthrough criterion

A synthetic score is not a breakthrough.  The direction becomes credible only when the
same learned artifact simultaneously:

- raises at least two previously zero public axes;
- does not add task-specific code;
- preserves previously solved axes within two points;
- uses materially fewer executable bits, inference operations, or peak memory than a
  matched neural baseline;
- demonstrates that learned state or operators are reused across domains;
- predicts a prospective unseen-domain gain before that domain is inspected.

## Persistence after failure

One failed implementation does not kill the hypothesis.  A direction is abandoned only
after separating at least these failure causes:

- representation class too weak;
- search or optimisation failed;
- data did not identify the latent structure;
- resource penalty was miscalibrated;
- compiler or memory hierarchy was inadequate;
- the theoretical advantage disappears under complete accounting.

At least three materially different optimisation/search strategies are tested when the
representation remains theoretically viable.  Repeating parameter tweaks does not count
as a different strategy.

## Anti-theatre rules

- No new phase or capability is created merely to report another controlled 100% score.
- No claim of novelty without a precise prior-art separation.
- No claim of generality without prospective cross-domain transfer.
- No claim of efficiency without complete runtime, memory, and learned-state accounting.
- Negative results, lower bounds, and architecture eliminations are retained.
- The central question is always whether broad capability per lifetime resource improves.

## Current claim boundary

This document defines a serious research program and a measurable hypothesis.  It does
not establish that local-PC human-level intelligence is achievable, does not prove that
neural networks are unnecessary, and does not claim a novel architecture yet.
