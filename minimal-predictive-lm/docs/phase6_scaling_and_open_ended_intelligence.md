# Phase 6: Scaling toward open-ended minimum-cost intelligence

## Top-level goal

The project is not successful merely because a tiny machine solves toy tasks.

The target is a resource-parameterized family of machines that can scale from kilobytes to larger systems without changing its basic representation or introducing a fixed architectural ceiling:

```text
U(B_static, B_dynamic, R, W, O, T_search)
```

where:

- `B_static`: static program and compressed knowledge bits
- `B_dynamic`: active working-state bits
- `R`: bits read from memory and knowledge stores
- `W`: bits written
- `O`: primitive operations
- `T_search`: offline or online search effort

For every resource budget, choose the machine on the Pareto frontier of task quality versus lifetime cost. The goal is not a single fixed finite machine that is literally infinitely intelligent. A fixed finite state and finite runtime necessarily distinguish only finitely many situations. The goal is an extensible sequence of machines whose capability can continue to improve when useful knowledge, memory, and search budget are increased.

## What “beyond current LLMs” means

Do not define success by parameter count or benchmark imitation alone.

A system surpasses an LLM at a workload point when it Pareto-dominates it on the relevant distribution:

```text
quality >= baseline quality
static bits <= baseline static bits
working bits <= baseline working bits
bits read/written <= baseline
primitive operations <= baseline
latency/energy <= baseline
training cost amortized over deployment <= baseline
```

A stronger milestone is to obtain higher coding, writing, and agent success at the same full-lifetime resource budget.

The comparison must include:

- model weights or program bits
- static knowledge store
- dynamic memory and caches
- retrieved context
- tool calls
- verifier/test execution
- candidate search
- training and compilation amortized over expected usage

No hidden RAG corpus, teacher model, internet lookup, or offline compiler is free.

## Literal infinite intelligence is not a valid finite-system claim

Three distinctions are mandatory.

### 1. Fixed machine versus scalable family

A fixed finite machine cannot contain arbitrary future facts or solve every problem with finite fixed computation. Open-ended intelligence means that the architecture accepts additional exact knowledge, program fragments, memory, and search time without requiring a new incompatible architecture.

### 2. Universal expressiveness versus efficient execution

A tiny instruction set may be computationally universal while being disastrously inefficient. Universality is only a gate. The research must also measure compiler overhead, constant factors, memory traffic, and asymptotic behavior.

### 3. Theoretical optimum versus computable approximation

The ideal universally optimal predictor/agent is not expected to be directly computable. The practical target is an expanding computable DSL and compiler whose frontier approaches lower bounds on selected real-world task distributions.

## Scaling hypothesis

The central hypothesis is:

> Real coding, writing, and agent workloads contain reusable algorithmic structure. Their useful state can be factored into compact programs, exact sparse knowledge, and task-local working state. A compiler can specialize this structure into execution paths that use work proportional mainly to new information, proof length, changed code, and required actions rather than total model size or full context length.

This hypothesis explicitly does not claim that arbitrary worlds are compressible. An arbitrary mapping may require essentially a full table. Gains must come from exploitable regularity in the actual workload.

## Four forms of scaling

### Breadth scaling: knowledge

Knowledge must be expandable without retraining the whole machine.

```text
core program
+ compressed reusable concepts
+ exact domain facts
+ project-local state
```

A query should read only the knowledge needed for its proof or action plan. Total stored knowledge may grow while per-task reads remain sparse.

### Depth scaling: reasoning and search

Easy tasks should execute compiled direct paths. Difficult tasks may receive more proof, simulation, synthesis, or search steps.

Compute is adaptive and explicit:

```text
simple case -> direct compiled rewrite
novel case  -> local search
hard case   -> deeper proof/simulation with a stated budget
```

The machine must report the marginal quality gained per additional operation and stop when expected gain no longer pays for cost.

### Horizon scaling: persistent agency

The same canonical state must survive long episodes:

- requirements
- repo facts
- attempted patches
- tool observations
- unresolved goals
- evidence and provenance
- final report commitments

No periodic conversion of the whole history back into a dense prompt is allowed. Only changed facts and still-live obligations should remain active.

### Self-improvement scaling

Candidate changes may modify rules, indexes, compression, search policy, or compiler passes. A change is accepted only when one of the following is available:

- proof of improvement under explicit assumptions
- held-out reproducible evidence with complexity penalty
- verified dominance on a declared workload distribution

The search cost and new implementation bits are included in lifetime MDL. Self-modification is not accepted merely because it improves a training trace.

## One canonical substrate

Coding, writing, planning, memory, creativity, and tool use remain programs over one canonical state.

```text
symbol / variable / typed relation / value / provenance / validity interval
```

Core semantic effects remain conceptually small:

```text
MATCH
ADD
DELETE
EMIT
EFFECT
CHOOSE
```

Variables, recursion, arithmetic, stacks, maps, graph traversal, AST edits, and text realization first exist as macros. A macro becomes a native operation only when lifetime cost decreases after charging for:

- opcode bits
- compiler and serializer growth
- additional runtime state
- conversion boundaries
- verification burden
- workload frequency

The final compiled executable may be highly specialized. The canonical substrate is for learning, transfer, and deduplication; abstractions that are unnecessary at runtime should be removed by partial evaluation and state minimization.

## Lower-bound accounting

Optimization must separate several irreducible quantities.

### Predictive state lower bound

If `K` future-equivalence classes must remain distinguishable, exact execution needs at least:

```text
ceil(log2 K) active bits
```

unless the distinction is recoverable by reading external information, in which case the read cost must be charged.

### New information lower bound

A genuinely novel incompressible name, fact, code fragment, or user preference requires storage or later reacquisition. The architecture cannot erase its information content by renaming it an embedding.

### Observation/read lower bound

If the correct output depends on an unread independent bit, exact correctness is impossible. The project must measure which evidence bits were actually read, not only model FLOPs.

### Proof/work lower bound

Some answers require a chain of dependent transformations. The target is work proportional to the shortest available proof/program under the current representation, not a promise of constant-time reasoning.

### Program description lower bound

Flat tables can have minimal runtime state but catastrophic static size. State bits and transition-program bits are separate objectives.

### Irreversible information loss

Deletion, merging, and lossy compression are allowed only when discarded distinctions do not affect the declared future workload enough to justify their cost. Where energy is evaluated, logically irreversible erasure is accounted separately from reversible transformation.

## Scaling gates

The architecture may advance only if it passes all relevant gates.

### Gate A: expressiveness

The core plus macros must represent:

- exact symbolic storage
- variable binding
- iteration/recursion or an equivalent mechanism
- conditional effects
- external observations
- program and text emission

### Gate B: factorization

Structured task families must not require flat exponential tables when a short generative rule exists.

### Gate C: transfer

A learned rule or concept must reduce cost across more than one episode or task family. Otherwise it remains task-local data.

### Gate D: sparse execution

Per-task work should scale with changed information, relevant dependency subgraph, proof length, and action count—not total static knowledge or total historical context.

### Gate E: no architecture ceiling

Increasing knowledge, memory, or search budget must not require replacing fixed context windows, fixed state vocabularies, or fixed-depth networks. Performance curves should show where current compilers or representations become the bottleneck.

### Gate F: real-work validation

Results must progress from known-lower-bound synthetic tasks to:

1. held-out compositional micro-worlds
2. multi-step specification -> code -> test -> repair -> report episodes
3. real repositories with bounded tasks
4. long-form writing with factual and structural constraints
5. persistent tool-using agent tasks

## Phase 6 experimental program

### 6a. Scaling audit on known structures

Measure flat versus factorized representations for increasing problem size:

- chain navigation: flat ground rules versus counter/parameterized transition
- parity and checksum: truth table versus constant program plus minimal state
- key-value memory: flat causal-state table versus indexed sparse memory
- proof chains: on-demand traversal versus workload-specific memoization

Report state lower bound, static bits, reads, writes, operations, and crossover workload.

### 6b. Unified long-horizon episode

One episode must perform:

```text
read specification
-> extract constraints
-> inspect repository facts
-> propose patch
-> execute tests through EFFECT
-> ingest failures
-> revise plan
-> emit final patch and report
```

All information is stored once in canonical form. Compare against a deliberately duplicated pipeline to quantify representation-boundary waste.

### 6c. Variable and parameterized-rule compiler

The current Phase 5a ground-rule engine does not scale sufficiently. Add variables and repeated structure first as macros, then compile them to indexed specialized transitions. Compare:

- ground-rule count
- macro/program bits
- compiled bytes
- rule checks
- working-state bits

### 6d. Open-ended curriculum

Generate task families whose size and composition increase. The system may add reusable rules only when held-out lifetime MDL improves. Track whether performance gains come from:

- larger memorized tables
- genuinely reusable algorithms
- better indexes
- better search control
- better compression

The project should reject apparent intelligence gains caused solely by storing benchmark answers.

### 6e. Matched-budget LLM comparison

Compare against tiny RNN/Transformer and, where feasible, larger API/hosted baselines using complete cost accounting. The first target is not broad domination. It is identifying regions where the compiled machine has a steeper quality-per-resource curve.

## Intelligence-density metrics

No single score is sufficient. Report a frontier including:

```text
success / static bit
success / dynamic bit
success / bit read
success / bit written
success / primitive operation
success / joule
success / end-to-end second
quality gain / additional resource unit
```

For agents, also report:

- successful task horizon
- recovery after failed actions
- number of environment effects
- verifier/test cost
- stale or duplicated state bits

For coding:

- changed lines and files
- repository bytes inspected
- tests executed
- defects introduced
- reusable rule gain across repositories

For writing:

- constraint satisfaction
- factual consistency
- long-range structure
- novelty without incoherence
- knowledge bytes read

## Stop conditions and falsification

The project must be willing to reject the central approach if evidence shows that:

- canonical symbolic conversion costs dominate dense inference
- rule/program growth matches or exceeds neural weights at equal quality
- sparse search explodes on ordinary language and code tasks
- reusable structure fails to transfer
- compilation removes flexibility needed for novel situations
- the scaling curve plateaus below useful real-work capability

A negative result is valuable only if the lower-bound accounting reveals exactly where the irreducible cost appears.

## Current conclusion

The current system is not yet proven universal, open-ended, or capable of exceeding modern LLMs. Phase 5a only demonstrates a shared substrate on tiny tasks.

Phase 6 changes the acceptance criterion: every future feature must improve both capability scaling and the full resource frontier. The research target is an extensible, self-specializing work machine whose cost approaches the information and computation actually required by each task, while preserving a path from kilobyte prototypes to systems that can eventually compete with and exceed LLMs on coding, writing, and agent workloads.
