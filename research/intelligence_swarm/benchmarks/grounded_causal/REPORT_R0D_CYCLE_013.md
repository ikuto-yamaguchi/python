# R0-D Cycle 013 — shuffle provenance and assignment integrity

## Scope

This cycle changes only the R0 evaluation contract and its tests. It does not add a memory mechanism, replay, fast weights, sleep, forgetting, a toy hypothesis, a new architecture, a branch, or a PR chain.

## Problem found

The prior contract required `target_label_shuffle` and `outcome_shuffle` method names and complete prediction coverage, but it did not prove that either control was an actual shuffle. A payload could pass method/coverage checks while:

- using the same instance as its own donor;
- reusing one donor for multiple targets;
- crossing seed, domain, split, or condition cells;
- reporting a donor ID whose snapshot did not match the immutable evaluation dataset;
- supplying arbitrary predictions under a shuffle method label without preserving a permutation.

That hole weakens same-instance causal-control comparisons and can create artificial differences through domain or split changes rather than the intended ablation.

## Contract change

`evaluation_contract.py` now requires, for `target_label_shuffle` and `outcome_shuffle` prediction rows:

- `control_source_instance_id`;
- `control_source_fingerprint`.

The scorer verifies that:

1. the donor exists in the immutable evaluation set;
2. the donor is not the target instance;
3. the donor fingerprint matches the canonical donor snapshot;
4. donor and target share seed, domain, split, and condition;
5. every cell uses a bijective donor assignment;
6. every cell is a derangement, with no fixed points.

The result JSON now includes `shuffle_assignment_audit` with row counts and per-cell `bijective` and `deranged` status. The progress contract explicitly requires shuffle provenance and within-cell derangement.

## Regression tests

The standard-library fixture now has 13 tests. It covers the previous schema, leakage, coverage, statistics, artifact, checksum, resource, and seed checks, plus:

- missing shuffle provenance;
- self-shuffle;
- duplicate donor/non-bijective assignment;
- cross-cell donor;
- valid same-cell derangement.

The exact staged files passed locally:

```text
Ran 13 tests in 4.861s
OK
```

## Current reproduction classification

The public baseline remains:

`initial_reproduction_failure`

because the existing public evaluation payload still lacks:

- actual `target_label_shuffle` predictions;
- actual `outcome_shuffle` predictions;
- donor instance IDs and donor fingerprints for those controls;
- complete raw-log/model/immutable-data artifact joins;
- paper-scale public capability reproduction.

This cycle improves the trust boundary of future comparisons. It does not establish a benchmark improvement, novelty, an intelligence principle, or capability progress.

## Commits

- `064a2c6553e54620f1a6156f31648a24ffa04703` — contract implementation
- `ec7adfb9a68b3068e925535c44b6dedd9be34bfc` — regression tests
- `9316f1bb55d42b146c62697c0038d547d35af2bb` — machine-readable audit result

## Next minimum action

Export immutable target-label and outcome-shuffle assignments as same-cell derangements, include donor provenance in every prediction row, then run the full instance-level scorer and artifact audit. Until that payload exists, the failure classification must remain unchanged.
