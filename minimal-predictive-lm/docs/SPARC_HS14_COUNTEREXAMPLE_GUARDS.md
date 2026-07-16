# SPARC-HS14: counterexample-guided sparse rule guards

HS14 adds falsification and scope correction to HS13's learned variable-binding rules.

## Validation mechanism

1. A learned rule predicts an endpoint from its body relations while the direct head conclusion is hidden from that prediction.
2. Source-grounded validation examples provide the observed head conclusion.
3. Matching predictions increase support; mismatches become explicit counterexamples.
4. HS14 compares direct local attributes of supported and refuting subjects.
5. A relation-value condition repeated across counterexamples but absent from supports becomes an exclusion guard on the rule.
6. The original rule is retained for ordinary cases, but subjects matching the learned guard are not assigned its conclusion.

Example:

`activity-state(x,z) <- classification(x,y), standard-activity(y,z)`

Counterexamples may induce:

`exclude when seasonal-state(x, hibernating)`

## Inference

- direct source-grounded head evidence always has priority;
- otherwise the question activates only rules for its target predicate;
- before rule execution, only the few learned guard relation slots are read;
- a matching guard returns calibrated uncertainty instead of a false universal conclusion;
- a non-matching subject continues through the original HS13 goal-directed proof.

## Resource contract

- no scan over validation examples at inference;
- at most four local guard conditions per rule;
- no forward materialisation of conclusions;
- no global entity, edge, rule, episode or exception scan;
- no Transformer, softmax attention or growing KV cache.

## Claim boundary

HS14 learns local exception guards for chain-shaped rules. It does not yet revise arbitrary logical theories, discover hidden causal variables, perform probabilistic science or reach Japanese high-school-level general intelligence.
