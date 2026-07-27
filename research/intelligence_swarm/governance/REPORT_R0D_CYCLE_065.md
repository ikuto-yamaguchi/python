# R0-D Cycle 065 — score/dataset contract binding

## Scope

This cycle continues R0 reproducibility, statistical validity, and leakage auditing only. It does not add memory, replay, fast weights, sleep, or forgetting mechanisms.

## Defect found

`evaluation_contract.score()` can be invoked directly without first enforcing `validate_dataset()`. A dataset can therefore fail the canonical dataset contract because of duplicate instance IDs, split leakage, seed/domain/condition topology failure, missing domains, or schema leakage, while the scorer still emits `cells`, `summary`, and `paired_gaps_vs_correct` from the surviving/overwritten rows.

A `valid=false` flag does not make those emitted statistics safe evidence. Downstream code can accidentally retain the numerical sections while dropping the error list.

## Added fail-closed audit

`audit_score_dataset_contract_binding.py` independently runs both core paths and requires the score artifact to:

- declare `dataset_contract_binding=true`;
- save `dataset_contract_valid` equal to `validate_dataset().valid`;
- classify an invalid dataset as `initial_reproduction_failure`;
- emit no `cells`, `summary`, or `paired_gaps_vs_correct` when the dataset contract is invalid.

Any violation is classified as `initial_reproduction_failure`.

## Regression coverage

Focused tests pin:

1. a valid, explicitly bound score artifact;
2. rejection when an invalid dataset still produces cells, summary, or paired gaps;
3. rejection when the binding declaration is absent;
4. rejection when the saved dataset-validity bit disagrees with `validate_dataset()`.

## Status

The focused auditor and CI workflow are present on the canonical reconstruction branch. Direct integration into `evaluation_contract.score()` remains required before a direct scorer invocation is considered non-bypassable.

- Accepted real R0 bundles: 0
- Public baseline reproduction: not accredited
- Resource/statistics bundles accepted: 0
- Current classification: `initial_reproduction_failure`
