# R0-D Cycle 007 — Same-instance and artifact-completeness audit

## Scope

This cycle advances only reproducibility, statistics and leakage auditing. It does not add memory, replay, fast weights, sleep, forgetting or a new intelligence mechanism.

## Contract changes

`evaluation_contract.py` now fingerprints the immutable evaluation input of every instance from domain, seed, split, condition, utterance, pre-treatment state, history, valid-action mask and available entity/dynamics signatures.

Every prediction may carry this `instance_fingerprint`. A mismatch is fatal, and the report records whether every method used the same input snapshot. This closes a gap where methods could have equal instance IDs and equal prediction counts while actually receiving different episode states or language.

Artifact auditing now requires complete Cartesian coverage over:

`required method × seed × domain × split`

It is no longer sufficient for every method to appear once. Missing a single seed or split for one control is classified as `initial_reproduction_failure`.

The statistical report continues to save domain × seed × condition cells, mean gaps, minimum and maximum cell gaps, approximate 95% confidence intervals and a paired randomization p-value. It now explicitly records whether the confidence interval excludes zero separately from the minimum +0.10 effect-size rule.

## Regression validation

The revised contract and tests were executed locally with Python 3 standard library only.

```text
Ran 6 tests in 0.085s
OK
```

Covered cases:

1. SILG exporter schema adaptation and complete scoring
2. immutable instance-snapshot mismatch rejection
3. completed-trajectory leakage rejection
4. normalized train/test utterance overlap rejection
5. incomplete prediction coverage rejection
6. incomplete method × seed × domain × split artifact coverage rejection

## Audit of the current public SILG result

Source: `SILG_RTFM_RECURRENT_SMOKE_R02_002.json`.

Verified observations already present in the repository:

- official SILG `multi` recurrent training path completed for seeds 1, 7 and 19
- 2,048 frames per seed
- 4,916,915 parameters
- state dict: 19,694,385 bytes
- CPU forward latency: 7.49024244 ms per environment step
- peak RSS: 473,858,048 / 529,195,008 / 492,986,368 bytes
- training wall time: 26.547 / 26.531 / 31.536 seconds

The current result fails the completed-reproduction contract for four independent reasons:

1. The recurrent model has not produced predictions on a frozen `rtfm_test_s1-v0` instance set.
2. Random control was measured separately rather than by replaying identical instances.
3. Language-blind, state-only, target-label-shuffle and outcome-shuffle results are absent.
4. Per-run raw-log digests in the source summary are truncated strings, while data checksums and per-run code commits are not recorded.

Formal classification:

`initial_reproduction_failure`

This does not invalidate the successful training-path smoke test. It means that training-path execution and resource measurement are not yet a reproduced public capability baseline.

## Next minimum action

Export one deterministic `rtfm_test_s1-v0` evaluation set for seeds 1, 7 and 19. Persist its dataset SHA-256 and the `instance_fingerprint` of each episode step. Replay that exact snapshot through:

- correct recurrent policy
- random
- language-blind
- state-only
- target-label shuffle
- outcome shuffle

For every method × seed cell, save model bytes, peak RSS, training wall time, CPU inference latency, full raw-log/model/data SHA-256 values and the exact code commit. Only after all coverage and leakage checks pass should capability statistics be interpreted.

## Decision

- Public recurrent training path: reproduced as an engineering smoke test
- Public matched capability baseline: not reproduced
- Capability progress: not claimed
- Novelty: not claimed
- High-school-level intelligence: not achieved
