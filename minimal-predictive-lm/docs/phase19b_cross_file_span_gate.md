# Phase 19b: file-disjoint contextual span reconstruction reality gate

Phase 19a established only that a tiny byte dictionary plus an n-gram predictor compressed unseen repository files better as training data increased. Phase 19b asks a stricter question: can the frozen self-supervised learner use both left and right context to identify a missing span in a file it never trained on?

## Protocol

- Reuse the deterministic file-disjoint corpus split from Phase 19a.
- Build masked-span tasks only from held-out files.
- Hide an 8-byte span and provide 24 bytes of left and right context.
- Rank the true span against seven same-length, same-domain distractors taken from other held-out files.
- Train forward and backward fourth-order token n-grams over the automatically learned byte-pair dictionary.
- Compare 25%, 50%, and 100% nested training sets with a raw-byte bidirectional n-gram baseline.
- Report top-1 accuracy, mean reciprocal rank, domain-level MRR, and the exact chance levels.

The learner receives no task identifier, file label, answer annotation, or domain-specific parser. Domain metadata is used only for evaluator-side construction of equally typed distractors.

## Falsification gates

The phase fails when there are too few file-disjoint tasks, a domain disappears, the task is effectively binary, performance does not exceed chance, more data reverses the trend beyond tolerance, or the learned dictionary does not beat the raw-byte baseline in MRR.

## Claim boundary

This remains candidate ranking rather than free generation. Passing would show context-sensitive cross-file prediction on a small mixed repository, not semantic understanding, general LLM parity, or Japanese high-school intelligence.
