# Phase 9c results: connector semantics induced from interaction effects

Connector strings are not assigned hand-written relation labels. Their roles are
selected by minimum description length from observed execution, reference, content,
and temporal effects.

## Connector-role induction

- base connectors / observations: **5 / 10**
- base mapping accuracy: **100.0%**
- shifted exact-surface accuracy: **0.0%**
- shifted interaction-induced accuracy: **100.0%**
- shifted observations: **10**

## Event-graph transfer

- cases: **6**
- event recall: **100.0%**
- edge recall: **100.0%**
- unresolved clauses: **0**

## Limitations

- candidate relation types are still supplied even though connector-to-role mappings are induced
- interaction traces expose execution, reference, content, and temporal effects
- the connector benchmark is synthetic and Japanese-only
- open-ended syntax and long-distance discourse relations are not solved
