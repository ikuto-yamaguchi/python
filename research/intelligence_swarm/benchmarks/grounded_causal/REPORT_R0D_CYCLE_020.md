# R0-D Cycle 020 — Episode-clustered paired statistics

## Scope

This cycle changes no model, memory mechanism, replay, fast weights, sleep, forgetting, architecture family, or branch topology. It extends the canonical R0 evaluation audit only.

## Defect found

The existing paired statistics include cell-level differences and an instance bootstrap. SILG trajectory rows are sequential steps, however, and steps from the same episode are not independent observations. Treating those steps as independently resampled instances can make confidence intervals too narrow and paired significance too optimistic.

## Added audit

`audit_episode_cluster_statistics.py` requires every evaluation row to carry an `episode_id`, requires complete same-instance predictions for `correct`, `random`, `language_blind`, `state_only`, `target_label_shuffle`, and `outcome_shuffle`, and checks instance fingerprints.

For each control and metric (`action`, `prospective`) it saves:

- domain × seed × split × condition cell count;
- paired episode count and paired step count;
- step-weighted mean gap;
- episode-equal-weight mean gap;
- minimum cell gap;
- hierarchical bootstrap CI resampling cells and then whole episodes;
- two-sided episode-level sign-flip test;
- a fail-closed CI-excludes-zero flag.

Missing episode IDs, incomplete control coverage, duplicate predictions, or fingerprint mismatch classify the bundle as `initial_reproduction_failure`.

## Regression coverage

`test_audit_episode_cluster_statistics.py` fixes three cases:

1. a complete three-seed bundle produces six episode clusters and eighteen steps;
2. missing `episode_id` fails closed;
3. one missing state-only prediction fails complete-coverage enforcement.

The lightweight `r0_evaluation_contract_tests.yml` workflow now compiles and runs this audit without starting the long SILG training workflow.

## Current decision

No real immutable R0 dataset/prediction bundle has yet passed this episode-cluster audit. Therefore the formal classification remains:

`initial_reproduction_failure`

No public capability progress, novelty, or intelligence principle is recognized.
