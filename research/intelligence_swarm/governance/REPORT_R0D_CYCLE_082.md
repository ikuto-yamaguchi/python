# R0-D Cycle 082 — statistics recomputation fixture repair

## Scope

This cycle repairs an obsolete regression fixture only. It does not add memory, replay, fast weights, sleep, forgetting, or any new model mechanism.

## Failure found

The unified acceptance workflow executed `test_audit_statistics_recomputation_binding.py`. Its shuffle fixtures declared a valid donor permutation and donor fingerprint, but still emitted the target instance's own gold-derived values:

- `target_label_shuffle.pred_action` was not taken from the declared donor's `gold_action`.
- `outcome_shuffle.pred_state_after` was not taken from the declared donor's `gold_state_after`.

The core evaluation contract now correctly requires donor-value binding, so the obsolete fixture failed before statistics recomputation could be tested.

## Repair

The fixture now preserves the same within-cell bijection and derangement while binding:

- `target_label_shuffle.pred_action == donor.gold_action`
- `outcome_shuffle.pred_state_after == donor.gold_state_after`

No production acceptance condition was weakened. The recomputation tests continue to require exact equality between saved and freshly recomputed score artifacts, and continue to reject fabricated or non-finite statistics.

## Formal status

- canonical branch only: yes
- new PR chain: no
- production evaluation contract weakened: no
- real R0 bundle accepted: 0
- public baseline reproduction recognized: no
- classification until complete evidence exists: `initial_reproduction_failure`
