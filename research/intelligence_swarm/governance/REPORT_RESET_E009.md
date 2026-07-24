# RESET-E009 — First public SILG/RTFM control execution

Date: 2026-07-24

## Decision

Continue **R0 Research Reconstruction**.

Do not promote a mechanism family, intelligence principle, or capability claim.

The previous source-acquisition blocker is resolved in GitHub Actions, and a pinned SILG/RTFM public environment plus random-valid-action control now execute successfully. However, the official shared recurrent baseline and matched language/state controls remain absent, so R0.1 is incomplete and the next stage is not authorized.

## Verified public run

- GitHub Actions workflow: `R0.1 SILG RTFM probe`
- Run ID: `30101406916`
- Conclusion: `success`
- Head SHA: `2d99b4bfbe5b8786df6063caa45cb6921e626b4a`
- Artifact ID: `8599758890`
- Artifact name: `r0-silg-rtfm-probe-30101406916`
- Artifact digest: `sha256:ed463e76d5c528b2cf25d740847c77978dbe66d0ed5455a57289519ba0455afd`
- Artifact retention expiry: 2026-08-23

## Pinned sources and runtime

- SILG SHA: `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM SHA: `58f17955595b5a127c96d045d896fcbcc7d4b570`
- OS: Ubuntu 22.04 GitHub-hosted runner
- Python: 3.8.18
- CPU: 4 vCPU, AMD EPYC 7763
- RAM: 15 GiB
- PyTorch: `1.13.1+cpu`
- Torchvision: `0.14.1+cpu`
- Gym: `0.21.0`
- NumPy: `1.24.4`
- Transformers: `4.30.2`

Raw install log, host record, resolved pip freeze, probe log and SHA-256 manifest were captured.

## Public environment schema

Environment: `silg:rtfm_train_s1-v0`

Observed keys:

- `name`, `name_len`
- `wiki`, `wiki_len`
- `task`, `task_len`
- `inv`, `inv_len`
- `valid`
- `rel_pos`
- `pos`

Observed shapes:

- name: `[6, 6, 1, 8]`
- inventory: `[8]`
- wiki: `[80]`
- task: `[40]`
- valid-action mask: `[5]`
- relative positions: `[6, 6, 2]`
- player position: `[2]`

Action count: 5.

## Random-valid-action result

Twenty episodes per seed, 60 episodes total.

| Seed | Wins | Win rate | Mean return | Mean episode length | Wall seconds |
|---:|---:|---:|---:|---:|---:|
| 0 | 1/20 | 0.05 | -1.210 | 16.50 | 0.982 |
| 1 | 5/20 | 0.25 | -0.707 | 11.35 | 0.688 |
| 2 | 2/20 | 0.10 | -1.154 | 18.70 | 1.095 |

Aggregate:

- wins: 8 / 60
- aggregate win rate: 0.1333
- mean seed win rate: 0.1333
- mean return: -1.0237
- mean episode length: 15.5167
- total environment wall time: 2.7652 seconds
- random action-selection latency: 7.324 microseconds/action

## Interpretation

This is the first measured value from the pinned public SILG/RTFM environment in the reconstruction program.

It is **not**:

- an official SILG recurrent baseline reproduction
- a learned-model result
- evidence for language grounding
- evidence for RQ-001-N2
- a capability improvement
- an intelligence principle

The run used seeds `0,1,2`, not the canonical research seeds `1,7,19`. It is therefore accepted as an engineering and public-control reproduction only.

## Leakage and comparability status

Passed for this random probe:

- no learned model
- no gold after state used for action selection
- no completed trajectory used
- valid-action mask only
- exact source SHAs and resolved dependencies recorded
- raw artifact checksums recorded

Not yet satisfied:

- identical episode instances across methods
- official train/test metric
- canonical seeds `1,7,19`
- language-blind control
- state-only control
- language shuffle
- model size and learned-model CPU latency
- training wall time and peak RSS for a learned baseline
- paper-metric tolerance comparison

## RQ-001-N2 status

**NARROWED, NOT ADOPTED.**

This control does not test whether raw language adds intervention-partition or causal-abstraction information beyond state/action/history-only inputs.

## Next authorized work

1. Capture deterministic RTFM S1 episode instances for replay across methods.
2. Switch to seeds `1,7,19`.
3. Run official or faithful shared recurrent baseline without a pretrained LM.
4. Run random, language-blind, state-only and language-shuffle on identical instances.
5. Evaluate `rtfm_test_s1-v0`.
6. Record learned model bytes, peak RSS, training time and CPU inference latency.
7. Only after R0.1, connect the environment-first and Language Dynamics Distillation baselines.

## Gate status

- R0.1: partial, not complete
- R0.2: public execution not complete
- R0.3: blocked by R0.1/R0.2
- novelty matrix: ongoing
- preregistered central claim: absent
- next-stage transition: rejected
- high-school-level intelligence: not achieved
