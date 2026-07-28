# R0.1 entropy=0.005 competence failure audit — run 30203026273

## Scope

This audit records a completed one-factor public-baseline screening run. It does not introduce a new mechanism, architecture, operation hypothesis, or goal hypothesis.

- Repository: `ikuto-yamaguchi/python`
- Canonical branch: `research/intelligence-swarm-reconstruction-001`
- GitHub Actions run: `30203026273`
- Artifact ID: `8633701993`
- Artifact name: `r01-silg-rtfm-entropy-0005-30203026273`
- Artifact digest: `sha256:004e5b3f180a27e2baa48b11fe7cf432b6da03a9038a3be737aafd35871dfc14`
- Artifact size: `72,686,668` bytes

## Fixed public sources and protocol

- SILG commit: `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM commit: `58f17955595b5a127c96d045d896fcbcc7d4b570`
- Environment: `silg:rtfm_train_s1-v0`
- Validation environment: `silg:rtfm_test_s1-v0`
- Model: official SILG `multi` recurrent
- Pretrained language model: none
- Seeds: `1, 7, 19`
- Requested frames per seed: `131072`
- Actual checkpoint frames per seed: `131080`, the first complete learner-update boundary
- Episodes per method per seed: `20`
- Matched controls: Correct, Random, Language-blind, State-only, Language-shuffle
- Same initial instances: yes
- Single changed factor relative to the preceding screen: `entropy_cost=0.005`

## Resource audit

- Parameters: `4,916,915`
- State-dict bytes: `19,694,385`
- CPU forward latency: `7.46144204 ms/step`
- Seed 1 training wall time: `1488.3666 s`
- Seed 7 training wall time: `1441.0211 s`
- Seed 19 training wall time: `1409.1277 s`
- Seed 1 peak RSS: `1,296,464 KiB`
- Seed 7 peak RSS: `1,298,784 KiB`
- Seed 19 peak RSS: `1,065,708 KiB`

All three training commands exited successfully and produced checksummed official checkpoints and extracted model-state files.

## Matched-control result

| Metric | Correct | Random | Correct − Random |
|---|---:|---:|---:|
| Win rate | 0.033333 | 0.066667 | -0.033333 |
| Mean return | -1.979666 | -1.151333 | -0.828333 |

Control win rates:

- Language-blind: `0.000000`
- State-only: `0.000000`
- Language-shuffle: `0.033333`
- Random: `0.066667`

The learned Correct policy did not outperform the matched Random valid-action policy on either required competence metric.

## Formal classification

- Qualification status: `rejected`
- Qualified for R0.2: `false`
- Classification: `optimization_or_policy_competence_failure`
- Failures:
  - `correct_not_above_random_win_rate`
  - `correct_not_above_random_return`

This is not an installation, dependency, schema, checkpoint, frame-accounting, resource-evidence, or checksum failure.

## Interpretation boundary

Lowering the official entropy coefficient to `0.005` did not restore public-baseline competence at the fixed 131,072-frame screening budget. Internal representation appearance, compression, next-state fit, or checkpoint completion cannot be counted as capability progress.

R0.2 Environment-first comparison remains blocked by the unchanged qualification gate. No novelty, intelligence principle, or capability progress is recognized.

## Next minimal action

A later run with the same fixed sources, model family, frames, seeds, split, and matched instances is collecting action histogram, valid-action counts, masked policy entropy, recurrent-state norms, episode lengths, termination rewards, and CPU latency. Only an observed harness or policy-dynamics defect may justify one minimal correction. Otherwise this entropy setting remains a negative result.