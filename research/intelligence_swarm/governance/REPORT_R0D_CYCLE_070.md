# R0-D Cycle 070 — normalized completed-trajectory leakage identities

`validate_dataset()` now canonicalizes `episode_id`, `episode_seed`, and `observation_fingerprint` before comparing train and evaluation splits. Unicode width/case differences, whitespace/control-format characters, numeric-vs-string aliases, and recursively structured identity aliases can no longer disguise completed-trajectory reuse.

The audit artifact records `normalized_trajectory_identity_required=true` and the normalization rule. Any normalized train/evaluation overlap is classified as `initial_reproduction_failure`. No memory, replay, fast-weights, sleep, or forgetting mechanism was added.
