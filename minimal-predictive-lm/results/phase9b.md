# Phase 9b results: hierarchical sparse event graphs

Single-label grounding is replaced by a sparse graph with event, proposition,
condition, content, temporal, and reference edges.

## Grounding

- benchmark cases: **5**
- single-label event recall: **3.3%**
- graph event recall: **100.0%**
- graph edge recall: **100.0%**
- unresolved clauses: **0**

## Memory accounting

- active graph: **3,388 bits**
- provenance ledger: **3,816 bits**
- graph + provenance: **7,204 bits**
- flat JSON hand-offs: **22,328 bits**
- flat / active graph: **6.59x**
- flat / graph+provenance: **3.10x**

## Conditional repair execution

- executed: `SET → VERIFY → RETRACT → SET → VERIFY → EMIT`
- skipped: `none`
- final expression: `x * x + 1`
- final test: **PASS**
- rollbacks / tests: **1 / 2**

## Representation-invention gate

- graph schema bits: **576**
- active instance bits: **3,388**
- break-even reuses: **5**

The graph is not adopted merely because it is more expressive. It is retained
only when avoided decision loss repays representation, parsing, migration,
verification, and runtime costs.

## Limitations

- the clause and connector inventory is still small and partly hand-specified
- raw grounding still depends on Phase 9a subword evidence
- world knowledge and open-ended reference resolution are not solved
- the benchmark is synthetic rather than an actual repository or open conversation
- global graph induction is not proven optimal outside the finite benchmark
