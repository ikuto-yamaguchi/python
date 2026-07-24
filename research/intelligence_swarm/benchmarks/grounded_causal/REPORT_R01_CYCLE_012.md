# R0.1 SILG / RTFM public recurrent reproduction — cycle 012

## Scope

This cycle changes only the faithful public recurrent reproduction budget on the canonical branch. It does not introduce a toy hypothesis, new architecture, memory mechanism, pretrained language model, or stacked branch.

## Fixed public sources and environment

- SILG commit: `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM commit: `58f17955595b5a127c96d045d896fcbcc7d4b570`
- Train split: `silg:rtfm_train_s1-v0`
- Test split: `silg:rtfm_test_s1-v0`
- Canonical seeds: `1, 7, 19`
- Python: `3.8`
- Runner: `ubuntu-22.04`, CPU only
- Pretrained language model: `false`
- Official / faithful recurrent family: SILG `multi`

Pinned installation remains controlled by `install_silg_rtfm.sh`. Observation and action contracts remain unchanged:

- grid: `6 x 6`
- wiki: `80` tokens
- task: `40` tokens
- inventory: `8` tokens
- relative position: `6 x 6 x 2`
- valid-action mask: `5`
- action space: `5`
- maximum episode length: `80`

## Previous staged result

The completed 32,768-frame staged run produced checkpoints at 32,800 frames for all three seeds, but did not reproduce public capability:

- Correct recurrent win rate: `0.0167` (`1 / 60`)
- Random valid-action win rate: `0.0667` (`4 / 60`)
- Language-blind win rate: `0.0167`
- State-only win rate: `0.0167`
- Language-shuffle win rate: `0.0167`

Because Correct remained below Random, this result is classified as insufficient policy competence rather than evidence that language is unnecessary.

## Minimal reproduction change

The workflow training budget is increased from `32,768` to `131,072` requested frames per seed. No model, loss, optimizer, observation, action, split, seed, ablation, or evaluation logic is changed.

The workflow timeout is increased from `180` to `300` minutes to preserve all three seeds and artifact upload under the larger staged budget.

## Evaluation retained unchanged

Each checkpoint will be evaluated on the same fixed initial episode streams with:

- Correct recurrent
- Random valid action
- Language-blind
- State-only
- Language-shuffle

The run must continue to record:

- checkpoint/model bytes and SHA-256
- peak RSS
- training wall time
- CPU inference latency
- source commits and dependency freeze
- raw logs
- per-episode initial-instance fingerprints
- three canonical seeds

## Acceptance and stop interpretation

This remains a staged engineering reproduction, not a paper-scale reproduction. The result may only advance the public-capability status if Correct becomes meaningfully competent and separates from Random on the immutable matched protocol. Otherwise it remains a reproduction failure or insufficient-budget result, and no new intelligence principle, novelty, or capability progress is claimed.

Current classification before completion:

`131072_frame_staged_public_recurrent_reproduction_launched / result_pending`

- Public capability baseline: not reproduced
- New intelligence principle: not claimed
- Capability progress: not recognized
- High-school-level intelligence: not achieved
