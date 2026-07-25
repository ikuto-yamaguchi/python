# R0-D Cycle 017 — exact canonical-seed coverage per evaluation cell

## Scope

This cycle advances only R0 benchmark reproducibility and leakage/statistical qualification on the canonical reconstruction branch. It adds no memory, replay, fast weights, sleep, forgetting, toy mechanism, architecture family, or PR chain.

## Gap found

`evaluation_contract.py` already required complete prediction coverage and the artifact manifest required the exact canonical seed set `{1, 7, 19}`. The dataset validator, however, only rejected datasets with fewer than three distinct seeds globally.

That allowed two invalid cases to pass dataset qualification:

1. three non-canonical seeds such as `{2, 3, 5}`;
2. all three canonical seeds present somewhere in the dataset, while one `domain × split × condition` evaluation cell silently omitted one seed.

The second case can bias minimum-cell gaps, paired tests, and cluster bootstrap results because the missing condition is no longer compared under the preregistered three-seed design.

## Implementation

Added `audit_dataset_cell_coverage.py`.

The audit consumes the same canonical or SILG-export rows as `evaluation_contract.py` and fail-closes when:

- any row uses a seed outside `{1, 7, 19}`;
- no evaluation cell exists;
- any `domain × split × condition` evaluation cell does not contain exactly seeds `{1, 7, 19}`.

It records:

- each evaluation cell and observed seed set;
- missing and extra seeds;
- training-cell seed coverage as a warning-level diagnostic;
- adapted dataset SHA-256;
- classification `initial_reproduction_failure` on any violation.

Added four regression tests covering:

- complete canonical cells;
- one missing seed in one holdout condition;
- three wrong seeds that previously satisfied the global count;
- a second domain missing one canonical seed.

Added a lightweight isolated GitHub Actions workflow, `r0_evaluation_contract_tests.yml`, so evaluation-contract tests can run without restarting the long SILG training workflow.

## Verification status

The implementation and tests are committed. The new lightweight workflow has been configured, but no completed check result was available at the time of this report. Therefore this cycle does not claim a successful test count yet.

## Classification

The real public evaluation bundle still lacks complete six-method prediction artifacts and a competent public baseline. The formal classification remains:

`initial_reproduction_failure`

No capability progress, novelty, intelligence principle, or high-school-level intelligence is recognized.
