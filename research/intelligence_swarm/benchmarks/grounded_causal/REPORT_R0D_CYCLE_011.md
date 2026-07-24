# R0-D Cycle 011 — SILG episode provenance and aggregate consistency

## Scope

This cycle extends the matched-episode evaluation contract only. It does not add memory, replay, fast weights, sleep, forgetting, a new model, or a new research branch.

## Completed

`evaluation_contract_silg_episode.py` now rejects a matched-evaluation payload when any of the following is true:

- a method/seed run is duplicated;
- wall time or CPU inference latency is missing, negative, NaN, or infinite;
- run-level win rate, return mean, or episode-length mean cannot be reproduced from the episode records;
- top-level method aggregates cannot be reproduced from the run-level values;
- a canonical checkpoint has non-positive size or a malformed SHA-256;
- SILG or RTFM is not pinned by a full 40-hex commit;
- peak RSS or total wall time is missing or invalid;
- answer leakage or pretrained-language-model absence is not explicitly declared false.

The existing checks remain active:

- canonical seeds 1, 7 and 19;
- complete episode coverage;
- identical initial-instance fingerprints across methods;
- Correct, Random, Language-blind, State-only and Language-shuffle;
- paired seed and episode statistics;
- seed-cluster bootstrap confidence intervals;
- exact McNemar tests.

## Verification

```text
Ran 7 tests in 11.380s
OK
```

New regression cases reject:

1. a tampered run-level win rate;
2. a malformed checkpoint digest;
3. a missing run resource field.

## Classification

`initial_reproduction_failure`

The contract is stricter, but the public capability baseline is still incomplete because matched payloads do not yet contain Target-label shuffle or Outcome shuffle. Raw workflow logs and an immutable exported test-set checksum are also not independently joined and rehashed by this adapter.

## Claims

- Public capability reproduction: not completed
- Capability progress: not claimed
- Novel intelligence principle: not claimed
- High-school-level intelligence: not reached
