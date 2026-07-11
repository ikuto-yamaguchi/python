# Phase 9b: hierarchical sparse event graphs

Phase 9a mapped each raw span to exactly one operation. That representation is
insufficient whenever one utterance contains an outer speech act and embedded
content, or when a condition, negation, quotation, temporal dependency, or
reference connects multiple events.

## Representation-collision trigger

If two histories map to the same active representation but require different
future actions, no policy over that representation can be optimal on both. The
Phase 9a report sentence created exactly this collision: it was both an `EMIT`
speech act and a statement that the tests `VERIFY` as passing.

Phase 9b replaces the single label with a graph containing:

- `EVENT` and `PROPOSITION` nodes;
- `NEXT` temporal edges;
- `CONDITION_TRUE` and `CONDITION_FALSE` edges;
- `CONTENT` edges between speech acts and propositions;
- `REFERS_TO` edges for local anaphora;
- polarity on event and proposition nodes.

The graph remains sparse. It does not allocate a dense tensor over all possible
relations.

## Memory separation

The active graph contains only decision-relevant structure. Raw utterances are
kept in a separate provenance ledger while audit, correction, or retraction is
possible. This prevents the active state from replaying full conversation text
without pretending that the original evidence can always be deleted.

## Representation-invention gate

A richer representation is not accepted merely because it can express more.
For a proposed representation change `r`, require:

```text
expected avoided decision loss
+ expected runtime saving
+ expected future induction saving
>
invention + schema + migration + verification + runtime cost
```

On the synthetic Phase 9b workload, the event graph breaks even after five
reuses under the explicit loss scale. That number is workload-specific; the
gate is the reusable principle.

## Current limitation

The connector inventory and some proposition extraction remain partly
hand-specified. Phase 9c must learn structural cues from interaction traces and
compare them with an exhaustive oracle on small grammars. The benchmark is not
evidence of open-domain language understanding or repository-scale coding.
