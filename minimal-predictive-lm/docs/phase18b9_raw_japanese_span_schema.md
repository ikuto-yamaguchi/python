# Phase 18b-9: raw Japanese span and schema induction

## Removed shortcut

Phase 18b-8 explicitly marked targets, clue spans, and the question. Phase 18b-9 removes those wrappers. Inputs are ordinary short Japanese sentences separated by punctuation. Entity names are anchored by one of three fixed generic question forms, quantities are recognized by a fixed number-unit recognizer, and nonnumeric distractor sentences may appear anywhere.

The learner is not told which recurring raw relation span means:

- total count,
- an entity-specific rate,
- weighted total.

It also searches three count equations and four weighted-value equations. Across nine recurring relation spans, the exhaustive admissible space contains 217,800 role/equation programs. Demonstration answers must select a unique optimum.

## Frozen gates

- Unique zero-error schema with a positive margin over the second candidate.
- Six unseen domains and twelve held-out problems with changed sentence order, entity order, cue combination, values, units, and distractor text.
- Exact answer and independent proof replay at 100% coverage.
- Whole-text and domain memorizer coverage of zero.
- A paired number-bag control capped at 50%.
- Symmetric calibration, unknown relation spans, extra numeric facts, unit mismatch, unsupported question forms, schema intervention, and proof tampering must fail safely.

## Claim boundary

The explicit wrapper is gone, but this is not unrestricted Japanese parsing. Sentence splitting, unit recognition, three question forms, exactly two target entities, exactly four numeric facts, and the count-plus-weighted-total family remain fixed. Unseen paraphrases abstain and are reserved for the next phase.
