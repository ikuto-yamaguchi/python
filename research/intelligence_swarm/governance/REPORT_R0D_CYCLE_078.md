# R0-D Cycle 078 — shuffle donor value binding

## Finding

The core previously verified shuffle provenance, same-cell assignment, bijection, derangement, and donor fingerprints, but did not verify that the submitted shuffled prediction actually used the donor value. A valid donor permutation could therefore accompany arbitrary predictions.

## Fail-closed rule

- `target_label_shuffle.pred_action` must equal the selected donor instance's `gold_action`.
- `outcome_shuffle.pred_state_after` must equal the selected donor instance's `gold_state_after`.
- Provenance-only assignments are rejected.
- Any mismatch suppresses all score statistics and is classified as `initial_reproduction_failure`.

No memory, replay, fast weights, sleep, or forgetting mechanism was added.
