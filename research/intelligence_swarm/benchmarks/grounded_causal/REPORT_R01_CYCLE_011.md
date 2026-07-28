# R0.1 Cycle 011 — corrected 32,768-frame SILG/RTFM matched reproduction

## Scope

This cycle used only the canonical branch and the pinned public SILG/RTFM recurrent baseline. No toy hypothesis, new architecture, pretrained language model, memory mechanism, or stacked branch was introduced.

## Public pins and schema

- SILG commit: `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM commit: `58f17955595b5a127c96d045d896fcbcc7d4b570`
- Train split: `silg:rtfm_train_s1-v0`
- Test split: `silg:rtfm_test_s1-v0`
- Seeds: `1, 7, 19`
- Model: official SILG `multi` recurrent, no pretrained language model
- Observation: 6x6 grid, wiki 80 tokens, task 40, inventory 8, valid-action mask 5, relative position 6x6x2
- Action space: 5; maximum episode length: 80

The corrected text ablation masks lexical token content but retains a one-token padded sequence length, satisfying the official packed-RNN input contract.

## Workflow and artifact

- Workflow run: `30120620610`
- Head commit: `cc2763a78e51c50fe6bb258e046fe33aa772ff4c`
- Conclusion: success
- Artifact ID: `8607725350`
- Artifact name: `r0-silg-rtfm-probe-30120620610`
- Artifact bytes: `73,259,322`
- Artifact digest: `sha256:662139632c73082f096154d819bef20f86f672d4e8f5b36f8667d754b6b751d2`

All installation, random probe, three-seed training, corrected matched evaluation, R0.2 export, eligibility audit, dependency freeze and artifact upload steps completed successfully.

## Training reproduction

Each seed requested 32,768 frames and produced a checkpoint at 32,800 frames.

| Seed | Wall time | Peak RSS | Trained model bytes |
|---:|---:|---:|---:|
| 1 | 341.906 s | 480,076 KiB | 19,693,911 |
| 7 | 346.898 s | 505,600 KiB | 19,693,911 |
| 19 | 341.882 s | 483,056 KiB | 19,693,990 |

Common audit:

- Parameters: `4,916,915`
- State-dict audit size: `19,694,385 bytes`
- CPU forward audit: `6.911 ms/step`
- Total three-seed training wall time: `1,033.885 s`
- Maximum training RSS: `505,600 KiB`

This remains a staged engineering budget, not the paper-scale public capability reproduction.

## Matched fixed-instance evaluation

Each method used 20 episodes per seed, for 60 episodes per method. All initial-instance fingerprint streams matched exactly across methods.

| Method | Win rate | Mean return | Mean episode length | CPU inference |
|---|---:|---:|---:|---:|
| Correct recurrent | 0.0167 | -1.8827 | 46.80 | 7.229 ms/step |
| Random valid action | **0.0667** | **-1.1513** | 15.23 | 0.0081 ms/step |
| Language-blind | 0.0167 | -2.0417 | 54.75 | 4.424 ms/step |
| State-only | 0.0167 | -2.1963 | 62.48 | 4.103 ms/step |
| Language-shuffle | 0.0167 | -1.9347 | 49.40 | 7.252 ms/step |

Correct minus controls:

- Correct - Random win rate: `-0.0500`
- Correct - Language-blind win rate: `0.0000`
- Correct - State-only win rate: `0.0000`
- Correct - Language-shuffle win rate: `0.0000`

The recurrent model won only 1 of 60 episodes. Random won 4 of 60. Language removal, state-only ablation and language shuffle all retained the same aggregate win rate as Correct.

## Leakage and provenance

- `answer_leakage: false`
- `pretrained_language_model: false`
- Full source pins, per-seed model hashes and raw training-log hashes are recorded in the artifact.
- Same-initial-instance matching passed.

The strict R0 contract is still incomplete because an immutable serialized public test dataset checksum, outcome/transition shuffle, and target-label-shuffle inapplicability record or non-oracle proxy are not yet joined into one complete evaluation manifest.

## Decision

Classification:

`matched_fixed_episode_32768_frame_staged_training_not_public_capability_reproduction`

The corrected 32,768-frame training and matched evaluation path is reproduced, but the learned public capability baseline is not reproduced. Correct remains below Random and does not separate from language controls in win rate. This is not evidence that language is unnecessary; policy competence is insufficient.

The next allowed change is limited to the official recurrent training budget or faithful reproduction condition. R0.2 tuning, new architectures and capability claims remain prohibited.

## Status

- Public training path: reproduced at 32,768-frame staged budget
- Corrected matched evaluation: reproduced for three seeds
- Learned public capability baseline: not reproduced
- New intelligence principle: not claimed
- Capability progress: not recognized
- High-school-level intelligence: not achieved
