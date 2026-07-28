# R0-D Cycle 006 — Reproducibility, Statistics, and Leakage Audit

## Scope

This cycle does not add memory mechanisms or a new model. It hardens the shared evaluation contract before public SILG/RTFM measurements are accepted.

## Contract changes

`evaluation_contract.py` now directly accepts the trajectory schema emitted by `export_silg_trajectories.py`:

- `action` is adapted to `gold_action`
- `state_after` is adapted to `gold_state_after`
- holdout flags are converted to a canonical condition
- default policy inputs exclude current action, reward, done, and next state

The validator now audits:

1. exact normalized train/test utterance overlap
2. entity and dynamics holdout signature overlap
3. direct and nested gold-action / gold-after / completed-trajectory leakage
4. duplicate IDs and missing seed/split/domain cells
5. complete per-method prediction coverage on the same evaluation instances
6. presence of random, language-blind, state-only, target-label-shuffle, and outcome-shuffle controls

The scorer now stores:

- domain × seed × condition × method cells
- mean and approximate 95% cell confidence intervals
- Correct-control paired mean gap
- minimum and maximum cell gap
- positive-cell fraction
- exact or Monte Carlo paired randomization p-value
- explicit progress-contract flags

`audit-artifacts` additionally checks:

- model bytes
- peak RSS bytes
- training wall time
- CPU inference latency
- raw log, model, and data SHA-256
- code commit
- three seeds and required methods

Invalid or incomplete manifests are classified as `initial_reproduction_failure`.

## Regression tests

`test_evaluation_contract.py` exercises five cases:

- SILG export schema adaptation and valid scoring
- gold and completed-trajectory leakage rejection
- exact train/test utterance overlap rejection
- incomplete control prediction coverage rejection
- resource manifest and artifact checksum verification

Local result:

```text
Ran 5 tests in 0.057s
OK
```

## Current public reproduction status

SILG/RTFM remains blocked before source acquisition because the runtime cannot resolve `github.com`. No public benchmark model has been trained or evaluated.

The existing installation log is registered with SHA-256:

```text
ff8f9543963f5c79b58676526a5f7e9011a68f1de81b38774bdea9ab8b8984eb
```

Therefore the current classification remains:

`initial_public_environment_installation_failure / initial_reproduction_failure`

The following public measurements remain unavailable:

- task success
- next-state prediction
- action accuracy
- model bytes
- peak RSS
- training wall time
- CPU inference latency
- seed 1/7/19 results

## Decision

The evaluation harness is materially more reproducible, but no public baseline capability has been reproduced. No capability progress, novelty, memory result, or intelligence principle is claimed.

## Next executable step

Run `bootstrap_silg_rtfm_r01.sh` on an Ubuntu x86_64 host with outbound DNS, export the same RTFM S1 episode IDs for all required methods, then execute:

```bash
python evaluation_contract.py validate trajectories.jsonl
python evaluation_contract.py score trajectories.jsonl predictions.jsonl
python evaluation_contract.py audit-artifacts run_manifest.json --base-dir artifacts
python -m unittest test_evaluation_contract.py
```

Public reproduction is accepted only after all three commands pass for seeds 1, 7, and 19.

## Status

- Public baseline reproduction: not completed
- Reproducibility contract: expanded and regression-tested
- Capability progress: not recognized
- Novelty: not established
- High-school-level intelligence: not achieved
