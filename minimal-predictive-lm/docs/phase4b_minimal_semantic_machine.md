# Phase 4b: Minimal Semantic Machine (no neural runtime)

## Decision

The final deployed machine must not delegate semantic understanding, memory, question answering, or reasoning to a dense neural residual model.

Neural networks may be used only as an optional offline search heuristic or teacher. Any behavior retained in the deployed model must be compiled into an explicit predictive program with measurable state bits, program bits, memory traffic, and operation count. If a neural component cannot be compiled away, it is not part of the minimum-machine research path.

Phase 4a remains useful as a surface-form compressor and local byte predictor. It is not the semantic core.

## Lifetime objective

For an expected deployment workload of N interactions, minimize:

```text
static program bits
+ static knowledge bits
+ expected dynamic memory bits
+ lambda_read  * expected bits read
+ lambda_write * expected bits written
+ lambda_ops   * expected primitive operations
+ lambda_train * training/search cost / N
+ prediction and answer loss
```

This prevents an expensive compiler or hidden external knowledge base from being treated as free.

## Proposed machine

```text
UTF-8 bytes
  -> deterministic surface transducer
  -> canonical semantic events / queries
  -> sparse entity and relation store
  -> query-directed rule execution
  -> proof trace
  -> deterministic language realizer
```

The machine is factorized into independently measurable components:

1. `surface transducer`
   - morphology, aliases, word order, particles, paraphrase rewrites
   - compiled trie / finite-state transducer / small pushdown rules
2. `symbol table`
   - exact storage of novel entity names
   - aliases map to canonical entity IDs
3. `world state`
   - typed sparse relations and timestamped events
   - overwrite, append, contradiction, and retraction operations
4. `reasoner`
   - Datalog-style rules, term rewriting, graph traversal, counters, stacks
   - only rules reachable from the query are executed
5. `answer realizer`
   - proof result to minimal Japanese output grammar

## Why each capability does not require a neural runtime

- Meaning understanding: compile utterances into typed executable predicates.
- Long-term consistency: preserve exact event and relation state with explicit constraints.
- Proper nouns: store unknown strings verbatim once, reference them by compact IDs afterward.
- Question answering: compile the question into a query and execute it over the sparse state.
- Logical reasoning: run only the proof rules and graph edges relevant to the query.

## Information-theoretic limits

The research must not claim impossible compression:

- A genuinely new name or fact contains new information and must consume storage.
- Open-domain knowledge must exist either in model bits, an external knowledge store, or the input.
- Some proofs inherently require many steps; the goal is to remove unrelated work, not make every proof constant-time.
- There is no computable universally shortest program for arbitrary data, so the practical target is a measured Pareto frontier within an expanding DSL.

## Phase 4b experiment

Create a deterministic Japanese micro-world with train/test separation across both wording and entity names.

Capabilities:

- unseen proper names
- aliases and pronouns
- location and ownership relations
- temporal updates: `Aは東京にいる` then `Aは大阪へ移動した`
- contradictions and retractions
- one-hop and multi-hop questions
- counting, comparison, and simple transitive rules
- nested clauses requiring a small stack

Candidate primitives are not fixed as a single architecture. The search may propose:

- exact symbol table
- last-write register
- sparse relation map
- append-only event log
- counter
- stack
- union-find
- graph edge and traversal
- Horn/Datalog rule
- string rewrite / finite-state transducer rule

## Residual-driven primitive proposal

1. Train the current shortest predictive program.
2. Collect histories or questions with different correct answers that collapse to the same state.
3. Find the smallest observable feature that separates those cases.
4. Instantiate candidate primitives capable of preserving that feature.
5. Recompile and retain a primitive only when held-out answer gain exceeds:
   - its program description bits
   - added runtime state bits
   - expected read/write bits
   - expected operation cost
6. Merge or delete primitives whose removal does not increase held-out loss enough to pay for them.

## Success criteria

The first Phase 4b milestone requires all of the following:

- no dense matrix multiplication at inference
- no neural component in the serialized runtime model
- exact retention of unseen names
- exact temporal consistency on held-out episodes
- exact answers for held-out compositional queries
- model and dynamic-memory bytes reported separately
- operations proportional to parsed input plus proof length, not corpus or context length
- every answer accompanied internally by an executable proof trace

## Baselines

Transformer/RNN models are comparison baselines only. They are not components of the proposed machine.

Compare:

- fixed n-gram / Phase 4a byte machine
- flat finite-state table
- hand-written symbolic oracle
- automatically synthesized minimal semantic machine
- tiny GRU/Transformer with matched serialized bytes

Report a Pareto frontier over answer accuracy, static bytes, dynamic bits per fact, bytes read/written, primitive operations, and training cost amortized over N interactions.
