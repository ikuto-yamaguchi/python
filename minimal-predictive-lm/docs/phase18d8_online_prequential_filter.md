# Phase 18d-8: causal online next-field filtering

## Motivation

Phase 18d-7 used an offline Viterbi path. Although its large-stage dynamic program was linear in stream length, backtracking could use future records to label earlier records. It also evaluated separate support episodes when routing queries.

Phase 18d-8 removes both conveniences. Each next field must be predicted from the prefix and past filter state before the true field is read. The observation is then used to update the state distribution. No task ID, task boundary, future suffix, or complete support episode is supplied.

## Causal protocol

For candidate state `z` at record `t`:

1. Propagate the previous costs with a fixed switch penalty.
2. Read only the current prefix.
3. Produce a prediction when all minimum-cost candidate states agree on the same value; otherwise abstain.
4. Reveal the actual next field.
5. Add zero emission cost for an exact prediction and a fixed error cost otherwise.
6. Normalize the costs and continue left to right.

The prediction and observation APIs are separate. Tests replace the current target counterfactually and verify that the prediction is unchanged. Appending a future suffix must not change any earlier prediction or posterior state.

## Why zero errors are impossible at some switches

Suppose the previous behavior is multiplication and the next behavior is minimum, while the current prefix has the same numeric type under both. Before the next target is revealed, these two worlds have identical histories and identical current prefixes:

- the multiplication block continues;
- an unannounced minimum block begins.

Any deterministic predictor must make the same decision in both worlds and therefore cannot be correct in both when the two programs produce different targets. Phase 18d-8 consequently measures finite change-point regret and adaptation latency instead of claiming impossible foresight.

## Gates

- Prediction is target-independent at the same position.
- A future suffix cannot rewrite prior predictions or posterior states.
- Covered prequential accuracy must remain at least 95%.
- Every locally stationary block must be identified by its final record.
- The post-freeze `MIN2` behavior must be discovered within two observed examples with no source change.
- Prediction errors must be confined to startup or unannounced same-signature task switches.
- Removing persistence or shuffling the stream must degrade online prediction.
- Doubling stream length must approximately double measured operations.
- The large-stage online filter must not use exact-cover search or support episodes.

## Claim boundary

The candidate state library is still enumerated from a human-designed typed DSL and is frozen before the online campaign. UTF-8 codec calibration, atom families, penalties, record structure, and complete-field updates remain fixed. The learner does not invent new primitives, predict every raw byte, learn natural-language semantics, or support arbitrary interleaving without contextual persistence. This is a controlled causal online-learning experiment, not LLM-like pretraining.
