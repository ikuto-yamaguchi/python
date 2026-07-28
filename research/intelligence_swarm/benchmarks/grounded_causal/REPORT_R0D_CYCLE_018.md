# R0-D Cycle 018 — semantic shuffle payload audit

## Scope

This cycle continues R0 benchmark reproducibility, statistics and leakage auditing on the single canonical reconstruction branch. It adds no memory, replay, fast weights, sleep, forgetting, toy mechanism, architecture family or branch chain.

## Defect found

The existing evaluation contract required target-label and outcome shuffle rows to name a donor instance, provide its immutable instance fingerprint, remain inside the same seed/domain/split/condition cell, and form a fixed-point-free bijection. That proves the donor assignment is structurally valid, but it does not prove that the value actually applied to the control came from the declared donor.

A producer could therefore emit a valid-looking donor permutation while leaving the target label/outcome unchanged, applying a value from another row, or executing a different transform. Such a control is a named shuffle rather than an audited shuffle.

## Added fail-closed audit

`audit_shuffle_payloads.py` independently audits the two required shuffle controls.

For `target_label_shuffle` it requires:

- transform `replace_gold_action_from_donor`;
- donor value from `gold_action`, `action`, or `target_label`;
- SHA-256 of the typed donor target-label payload;
- SHA-256 of the value actually applied by the control;
- equality of the donor and applied payload hashes.

For `outcome_shuffle` it requires:

- transform `replace_gold_state_after_from_donor`;
- donor value from `gold_state_after`, `state_after`, `outcome`, `episode_success`, or `task_success`;
- SHA-256 of the typed donor outcome payload;
- SHA-256 of the value actually applied by the control;
- equality of the donor and applied payload hashes.

Both methods additionally require:

- donor instance and fingerprint provenance;
- same seed/domain/split/condition cell;
- no self-shuffle;
- cell-wise bijection and derangement;
- at least one semantic value change in every cell.

The output records source fields, transform, cell size, unique donor count, bijection/derangement status, changed-value count and changed-value fraction. Any failure is classified as `initial_reproduction_failure`.

## Regression tests

`test_audit_shuffle_payloads.py` covers:

1. a valid three-seed semantic shuffle;
2. declared donor with a different applied payload;
3. wrong method-specific transform;
4. structurally deranged but semantically no-op cells.

The four tests passed locally with the Python standard library. The lightweight `r0_evaluation_contract_tests.yml` workflow now compiles and runs this audit without triggering the long SILG training workflow. A GitHub Actions result is not claimed until the run completes.

## Current classification

No real target-label/outcome shuffle prediction bundle currently contains the new value-level provenance fields and a complete immutable artifact join. The public learned baseline also remains unqualified.

Therefore the strict classification remains:

`initial_reproduction_failure`

No novelty, intelligence principle, capability progress, or high-school-level intelligence is recognized.
