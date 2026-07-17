# SPARC High-School General Intelligence Gate

This document defines the only main-line acceptance gate after PR #73.

## Final target

One shared, non-Transformer learner must acquire knowledge from ordinary Japanese prose and use the same learned representations for reading, quantitative reasoning, causal and counterfactual reasoning, planning, explanation, long dialogue, and continual learning. The target is not a collection of task-specific solvers.

## Immediate policy change

Local feature PRs are no longer main-line evidence. A change may merge into `research/minimal-compute-lm` only when it improves the integrated gate, improves the minimum axis, causes no axis regression, and has an acceptable capability/efficiency trade-off.

The model must not receive task names, domain labels, benchmark names, gold parser output, relation names, operation names, or a hand-selected specialist route.

## Integrated axes

1. Ordinary Japanese single-exposure learning
2. Japanese reading and multi-paragraph inference
3. Mathematics: calculation, variable binding, and verification
4. Science: mechanism, prediction, and causal intervention
5. Social studies: temporal and relational integration
6. Counterfactual and belief revision
7. Planning with constraints and self-checking
8. Source-grounded free-form explanation
9. Long dialogue state and correction
10. Continual cross-domain learning without forgetting
11. Unknown-expression selective response
12. Transfer to untouched names, wording, and domains

## Frozen acceptance conditions

- the same serialized model is evaluated on every axis;
- no task/domain identifier is exposed to the model;
- aggregate score must improve over the previous integrated baseline;
- the minimum axis must improve;
- no axis may regress by more than 2 percentage points;
- selective accuracy must remain at least 90% at at least 70% coverage;
- continual-learning regression must remain below 5%;
- at least one untouched domain and one untouched wording family must improve;
- free-form explanations must cite the supporting source IDs and preserve the proof structure;
- efficiency metrics are mandatory: serialized bytes, peak RSS, feature reads, candidates, estimated operations, training time, and inference latency;
- a capability gain may not be purchased by an unbounded scan, growing KV cache, dense global update, or task-specific branch.

## Failure rule

A locally successful feature that does not improve this integrated gate is archived, not merged. Failed designs must be replaced structurally rather than patched with example-specific words, suffixes, or benchmark branches.

## Current honest status

The current main line has compact sparse program, world, relation, provenance, discourse-focus, contradiction-guard, and continual-update mechanisms. It has not demonstrated unrestricted Japanese textbook learning, cross-curricular transfer, free-form reasoning, robust planning, or high-school-level conversation. Therefore high-school-level intelligence is **not reached**.
