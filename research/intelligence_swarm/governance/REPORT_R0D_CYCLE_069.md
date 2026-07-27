# R0-D Cycle 069 — domain-local train/evaluation coverage

`validate_dataset()` now requires every observed domain, for every canonical seed 1/7/19, to contain both a train split and at least one registered evaluation split. A dataset can no longer pass merely because one domain supplies all training rows while another supplies all evaluation rows.

The audit artifact records `domain_local_train_eval_coverage_required=true` and the per-domain/per-seed split coverage. Missing domain-local train or evaluation evidence is classified as `initial_reproduction_failure`. No memory, replay, fast-weights, sleep, or forgetting mechanism was added.
