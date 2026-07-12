# Phase 16b: Minimality reset and theoretical status

## Executive verdict

The project has demonstrated several compact mechanisms, but the sequence from
Phase 13 to Phase 15 also exposed a serious failure mode: capability can rise by
adding benchmark-informed surface compilers while broad frozen transfer remains
near zero. Phase 16a's frozen third slice scored 0/200 with 0.5% coverage. This
means that the current system is not yet a compact general learner. It is a
small shared runtime plus a growing library of manually supplied codecs,
knowledge, and bounded procedures.

That is useful engineering evidence, but it is not evidence that repeatedly
adding parsers will converge to LLM-like general intelligence.

## A finite universal core does not imply finite universal competence

A finite interpreter can be computationally universal. This only means that it
can execute any computable program when the appropriate program, data, memory,
and time are supplied. It does not mean that the interpreter already contains
those programs, can discover them efficiently, or can solve every new task with
small resources.

The project must separate three quantities:

1. **core complexity**: the reusable interpreter, state substrate, learner, and
   search policy;
2. **acquired complexity**: learned programs, concepts, facts, indexes, and
   codecs;
3. **task execution cost**: active state, reads, writes, operations, search,
   verification, tool effects, and latency.

The core may remain finite and small. Acquired knowledge and useful programs
must remain extensible and can grow without a finite upper bound as the target
distribution expands. Generality therefore cannot be defined as "eventually no
more additions". It must be defined as "new competence is acquired through the
same learner and representation, with marginal cost proportional to genuinely
new information rather than a new human-written subsystem per benchmark".

## Theoretical ladder

The following claims must not be conflated.

### 1. Expressive universality

A universal instruction set or Turing-complete substrate can represent every
computable algorithm. This is an expressiveness result only. It gives no useful
bound on program discovery, data requirements, execution time, or transfer.

### 2. Minimal predictive state

For a fixed stochastic process and prediction target, causal-state methods can
define a minimal sufficient predictive statistic. This supports the project's
state-minimization direction, but only after the process distribution and
prediction equivalence are defined. It does not produce a single finite state
representation that is minimal for all future tasks.

### 3. Description-length induction

MDL and algorithmic probability formalize a preference for short explanations.
They justify charging model/program bits together with residual error. Exact
Kolmogorov complexity and Solomonoff induction are incomputable, so practical
systems can only optimize restricted, computable upper bounds inside a declared
language and search budget.

### 4. Universal rational agency

AIXI-style theory gives an ideal Bayesian decision agent over computable
environments, but the ideal is incomputable. Time/space-bounded variants move
cost into an enormous search over programs and proofs. They are existence and
comparison results, not a practical recipe proving that this repository's
architecture will acquire broad intelligence.

### 5. Distribution-relative generalization

PAC, PAC-Bayes, MDL, and related bounds can constrain held-out risk under stated
sampling, prior, hypothesis-class, and loss assumptions. They do not guarantee
open-ended competence under arbitrary distribution shift, unknown objectives,
or unrestricted environments.

## No absolute minimum-resource intelligent system

There is no architecture that is uniformly best over every possible task
mapping without assumptions about the task distribution. Any resource claim
must therefore be indexed by a workload distribution `D`, horizon `H`,
information interface `I`, and permitted failure level `epsilon`.

Use a Pareto cost vector rather than hiding trade-offs in one score:

```text
C(A; D,H,I) = (
    B_core,
    B_acquired,
    B_active,
    bits_read,
    bits_written,
    primitive_operations,
    search_operations,
    observations_and_effects,
    induction_cost / expected_reuses,
    verification_and_migration,
    latency,
    energy,
    expected_loss,
    shifted_distribution_regret
)
```

A component is justified only if the new system is non-dominated on a declared
workload or if its extra cost purchases a clearly separated new frontier point.

## Manual specialization debt

From this phase onward, every human-designed surface compiler, task recognizer,
ontology patch, primitive, and exception is recorded as **manual specialization
debt**.

A manual addition is not accepted as evidence of general learning merely because
it raises one public benchmark. It must satisfy all of the following:

1. its complete static, induction, migration, and verification cost is charged;
2. the mechanism is evaluated on at least two held-out task families not used to
   choose its surface form;
3. an ablation demonstrates that the gain comes from the proposed shared
   mechanism rather than answer leakage or routing;
4. the same capability can be induced from interactions or raw evidence without
   editing the runtime;
5. obsolete or dominated compilers are pruned after consolidation.

A benchmark-specific compiler may remain as an engineering adapter, but it does
not count toward the general-intelligence claim.

## Phase 16b experimental reset

Phase 16b must not begin by adding five new task solvers. It proceeds in four
stages.

### 16b-1: cost and mechanism ledger

Inventory every active component with:

- source bytes and compiled description bits;
- external knowledge bytes;
- human-designed compiler count;
- task families that selected the component;
- independently held-out families helped by it;
- per-query reads, writes, operations, and peak active state;
- induction and verification cost;
- predecessor ablation.

Report both the whole Python implementation and the serialized predictive
payload. Reporting only the compact payload while ignoring the human-authored
compiler is forbidden.

### 16b-2: frozen architecture test

Freeze all current handlers and evaluate further public families before
adaptation. This estimates the natural-transfer matrix and exposes whether the
current canonical substrate actually composes.

### 16b-3: one shared induced mechanism

Permit at most one representation/learner change. The candidate mechanism must
be induced from independent synthetic or interaction evidence and must target a
semantic invariant rather than a benchmark name. A candidate example is a
shared proposition-constraint graph supporting negation, equivalence,
implication, contradiction, quotation, and uncertainty.

### 16b-4: transfer, ablation, and pruning

Evaluate the unchanged new mechanism on multiple public families, shifted
surface forms, adversarial contradictions, and a non-benchmark micro-world.
Then remove redundant older rules and report net—not gross—resource change.

## Acceptance metrics

The next phase reports at least:

```text
new correct held-out examples / added static bit
new correct held-out task families / added manual compiler
quality gain / added operation
quality gain / added byte read
net serialized bytes after pruning
natural-transfer matrix before and after the mechanism
induction candidate evaluations
human engineering interventions
```

A useful consolidation target is:

```text
held-out families helped >= 2
benchmark task-name branches == 0
manual surface compilers added == 0 for the capability claim
net reusable representation growth < sum of replaced specialized growth
frozen predecessor retained for comparison
```

These are research gates, not mathematical guarantees.

## Falsification conditions

Pause or abandon the current symbolic-compiler path if any of the following
persist across several blind slices:

- frozen transfer remains near zero;
- each new public family requires a new human parser;
- compiler/source-code growth tracks benchmark breadth approximately linearly;
- candidate search becomes larger than dense-model inference at equal quality;
- raw-language grounding dominates all other costs;
- shared representations fail to reduce the number of mechanisms after pruning;
- real repository, long-context, dialogue, and writing performance stays far
  below small LLMs even when the full lifetime budget is matched.

In that case, the correct result is not to keep attaching modules. The project
should adopt a hybrid learned codec/candidate generator or revise the substrate.

## Current claim boundary

There is a mathematical motivation for minimum predictive states, MDL-biased
program induction, and resource-rational search. There is no theorem proving
that the current implementation—or any practical finite learner with fixed
resources—will acquire LLM-like general intelligence.

The strongest defensible hypothesis is conditional:

> If the target workload contains reusable computable structure, if the learner's
> representation language can express that structure compactly, and if the
> search/grounding procedure can discover it within the available budget, then a
> compiled sparse machine may approach the workload's information and proof
> lower bounds and may Pareto-dominate dense inference on parts of that workload.

Phase 16b exists to test those conditions rather than assume them.
