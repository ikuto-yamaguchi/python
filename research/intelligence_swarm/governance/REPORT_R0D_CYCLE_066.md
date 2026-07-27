# R0-D Cycle 066 — score/dataset contract core binding

`evaluation_contract.score()` now executes `validate_dataset()` on the same submitted dataset, records the dataset audit in the score artifact, propagates dataset-contract errors, and emits no `cells`, `summary`, or `paired_gaps_vs_correct` when the dataset contract is invalid.

Acceptance remains fail-closed as `initial_reproduction_failure`. No memory, replay, fast-weights, sleep, or forgetting mechanism was added.
