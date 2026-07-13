# Phase 18d-9: online program-library growth

## Motivation

Phase 18d-8 performed causal next-field prediction without task IDs, boundaries, future suffixes, or support episodes. However, all 130 candidate program states were available to the filter from the start. The appended MIN block therefore selected a previously available behavior rather than growing the active skill library from zero.

Phase 18d-9 separates a fixed generic search pool from the acquired active library. The active library begins empty. Recent observations define a version space, and a program enters the active library only when one candidate uniquely explains a noiseless recent window. Previously acquired programs remain stored, while a post-freeze stream can add a new program with no source change.

## Online procedure

For each record:

1. Predict the next field using the currently active program when one exists.
2. Otherwise, predict only when every candidate consistent with the recent window agrees on the same output.
3. Reveal the target.
4. If the active program fails, begin a new recent window at the conflicting record.
5. Remove the oldest observations when no candidate can explain the whole window.
6. Add a candidate to the active library only when it is unique and has at least two supporting observations.

No audit label, task name, task count, block boundary, or support episode is passed to this procedure.

## Gates

- The active library starts with zero programs.
- The initial stream must acquire exactly the seven behaviors present in its audit blocks.
- The appended stream must add exactly one behavior, `MIN2`, without changing source code.
- Every block must finish with its correct acquired program active.
- Covered accuracy must remain at least 95%, with coverage at least 45%.
- Prediction errors must be confined to startup or the first distinguishable record of an unannounced same-signature switch.
- Appending a future suffix cannot change earlier predictions or active-library states.
- Shuffling must degrade acquisition or prediction, demonstrating reliance on local persistence.
- Doubling stream length must keep measured work near linear.
- The online learner must not call exact-cover search or accept support episodes.

## Claim boundary

The active program library is learned from data, but the 130-state typed DSL search pool is still human-designed and pre-enumerated. Program activation assumes noiseless records and unique identification inside a recent locally stationary window. UTF-8 codec calibration, atom families, record structure, and primitive operations remain fixed. This phase does not invent operations outside the DSL, learn natural-language meaning, or perform LLM-like open-domain pretraining.
