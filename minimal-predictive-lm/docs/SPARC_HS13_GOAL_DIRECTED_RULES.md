# SPARC-HS13: goal-directed sparse rule induction

HS13 lifts HS12 relation paths into reusable variable-binding rules with an explicit head predicate.

## Rule induction

For several demonstrations, HS13 finds:

1. a direct source-grounded conclusion edge from the question subject to the demonstrated answer;
2. an alternative local relation path reaching the same answer;
3. the shortest `(head predicate, body relation sequence)` shared across demonstrations.

This yields rules such as:

`body-temperature-property(x,z) <- classification(x,y), body-temperature(y,z)`

The entity names are discarded; only the variable-binding predicate structure is retained.

## Goal-directed execution

- a question surface activates one target predicate;
- direct evidence is checked first;
- if absent, only rules whose head matches the target are considered;
- body predicates are resolved locally and may themselves invoke another learned rule;
- recursion is bounded and repeated goals are suppressed;
- proof edges and all source IDs are returned.

## Resource contract

- no forward materialisation of every possible conclusion;
- no global entity, edge, rule or episode scan;
- bounded rule depth, body length and active frontier;
- query-local subject lookup depends on question length;
- no Transformer, softmax attention or growing KV cache.

## Claim boundary

HS13 induces chain-shaped Horn-style rules from redundant source-grounded conclusions. It does not yet learn arbitrary logical forms, quantifiers, negation-as-failure, theorem proofs or open-ended research strategies, and it is not Japanese high-school-level general intelligence.
