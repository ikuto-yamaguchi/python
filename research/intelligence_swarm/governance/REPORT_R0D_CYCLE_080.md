# R0-D Cycle 080 — repair stale optional-metric regression fixture

The Cycle 055 optional inverse-metric coverage regression fixture predated the later shuffle donor-value binding contract. It declared valid target-label and outcome shuffle provenance, but left the reportable prediction values copied from the target instance rather than the declared donor. The focused workflow therefore failed even though the core inverse-coverage contract was already present.

This cycle updates only the regression fixture:

- `target_label_shuffle.pred_action` is copied from the declared donor's `gold_action`.
- `outcome_shuffle.pred_state_after` is copied from the declared donor's `gold_state_after`.
- donor IDs, donor fingerprints, within-cell bijection, derangement, prediction coverage, and optional inverse coverage remain unchanged.

No memory, replay, fast weights, sleep, forgetting, or new mechanism was added. This is an R0 reproducibility/statistics/leakage test repair only. A failing or incomplete benchmark bundle remains classified as `initial_reproduction_failure`; this change does not establish a successful public baseline reproduction.
