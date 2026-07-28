# R0-D Cycle 014 — split / condition cell integrity

## Scope

This cycle changes only the R0 benchmark reproducibility, statistics, and leakage contract. It does not add memory, replay, fast weights, sleep, forgetting, a toy mechanism, or a new branch.

## Identified audit gap

The previous scorer grouped results by `method × seed × domain × condition` but omitted `split`. The artifact manifest indexed runs by `method × seed × domain × split` but omitted `condition`.

That allowed two invalid situations:

1. results from different evaluation splits could be pooled into one statistical cell;
2. an artifact manifest could appear complete while a held-out condition was absent for one method or seed.

This is especially unsafe for entity, dynamics, and language-form transfer because an in-distribution run can mask a missing holdout run.

## Contract change

`evaluation_contract.py` now:

- records score cells as `method × seed × domain × split × condition`;
- computes paired cell differences with the same split-aware key;
- clusters instance bootstrap samples by `seed × domain × split × condition`;
- requires every artifact run to declare a non-empty `condition`;
- requires complete Cartesian coverage over `method × seed × domain × split × condition`;
- reports the discovered condition set and `condition_index_required: true`;
- records `requires_split_condition_cells: true` in the progress contract.

No model, benchmark environment, training code, or prediction was changed.

## Regression tests

The standard-library fixture suite now contains 15 tests and completed successfully:

```text
Ran 15 tests in 2.776s
OK
```

New regression cases verify that:

- every score cell contains `split`;
- the progress contract declares split/condition cell integrity;
- artifact manifests without `condition` fail;
- omission of one method × seed × condition cell is detected as incomplete Cartesian coverage.

Existing tests continue to cover utterance overlap, entity/dynamics holdout leakage, forbidden gold/completed-trajectory inputs, prediction coverage, instance fingerprints, shuffle donor provenance, derangement, checksums, resource fields, and canonical seeds.

## Classification

The public baseline remains:

`initial_reproduction_failure`

The contract is stricter, but the real evaluation bundle still lacks:

- target-label shuffle predictions with donor provenance;
- outcome-shuffle predictions with donor provenance;
- complete raw-log/model/immutable-data joins for every required cell;
- paper-scale public capability reproduction.

This cycle provides no evidence of capability progress, novelty, a new intelligence principle, or high-school-level intelligence.
