# R0-D Cycle 068 — fail-closed invalid prediction statistics

`evaluation_contract.score()` now emits `cells`, `summary`, and `paired_gaps_vs_correct` only when the entire dataset and prediction contract is valid. Prediction coverage failures, forbidden gold/outcome fields, snapshot mismatches, invalid actions, optional-metric coverage failures, and invalid shuffle provenance therefore cannot leave quotable statistical evidence behind.

The score artifact records `invalid_score_statistics_forbidden=true` and `statistics_emitted=false` on failure. Classification remains `initial_reproduction_failure`. No memory, replay, fast-weights, sleep, or forgetting mechanism was added.
