# Phase 19b: leave-one-domain-out transfer gate

Phase 19a showed that a byte dictionary plus a trigram predictor improves on file-disjoint held-out repository data as the mixed-domain training set grows. That is only a within-mixture scaling result.

Phase 19b removes one complete domain from every learning stage. For each of `code`, `prose`, and `structured`, the target domain is excluded from:

- merge/dictionary induction,
- n-gram parameter estimation,
- training-fraction selection,
- model comparison.

The learner trains only on the other two domains and predicts file-disjoint files from the unseen target domain. Training fractions are nested at 25%, 50%, and 100%.

## Required gates

- target-domain files never enter the source corpus,
- source and target paths are disjoint,
- each target has at least 4096 bytes,
- at least two of three domains improve as source data grows,
- at least two of three domains beat an equal-order raw-byte trigram,
- the byte-weighted aggregate beats the raw baseline,
- training records expose no task labels or answers.

## Interpretation

Passing is evidence of small cross-domain statistical transfer. It does not establish semantic representations, question answering, reasoning, free-form generation, LLM parity, or high-school intelligence.

A failure is kept as a failed gate rather than repaired with target-domain-specific rules.
