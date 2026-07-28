# R0-D Cycle 089 — canonical split integration repair

## Scope

R0 benchmark reproducibility, leakage and statistics auditing only. No memory, replay, fast weights, sleep or forgetting mechanisms were added.

## Finding

`evaluation_contract.py` still used raw `str(split).lower()` identities in dataset cells, fingerprints and holdout checks. The existing Cycle 087 patch and regression existed, but its workflow committed the core update only for `workflow_dispatch`. Pull-request runs therefore validated a temporary workspace and discarded the actual core change.

## Change

The existing canonical-split workflow now commits an idempotent core update on the canonical branch after the patch, compile and focused regression succeed. It uses the existing branch directly and does not create another branch or PR chain.

The intended fail-closed core contract remains:

- Unicode NFKC and case folding for split identity;
- whitespace, control and format character removal for alias detection;
- exact canonical raw spelling required for evidence rows;
- shared split identity across dataset topology, utterance overlap, entity/dynamics holdout, completed-trajectory isolation, prediction coverage, resource manifests and raw-log binding;
- invalid split evidence classified as `initial_reproduction_failure`;
- invalid dataset/prediction statistics suppressed.

## Status

- workflow integration defect: repaired;
- core commit: pending successful workflow execution;
- accepted real R0 bundle: 0;
- public baseline reproduction: not recognized;
- classification: `initial_reproduction_failure`.
