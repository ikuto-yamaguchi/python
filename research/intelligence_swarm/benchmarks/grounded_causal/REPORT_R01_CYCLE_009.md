# R0.1 SILG/RTFM Reproduction Cycle 009

## Scope

This cycle advances the public SILG/RTFM reproduction path only. It adds no new architecture or toy mechanism and makes no novelty or capability-progress claim.

## Completed engineering reproduction

GitHub Actions run `30107848065` completed all of the following on the canonical reconstruction branch:

1. install the pinned public SILG and RTFM sources;
2. run the canonical random/schema probe;
3. train the official SILG `multi` recurrent learner for seeds `1,7,19`;
4. persist the official final checkpoints and extracted trained state dictionaries;
5. reload each trained state dictionary;
6. evaluate `correct`, `random`, `language_blind`, and `state_only` on independently seeded, identical RTFM test instances;
7. upload raw logs, checkpoints, installed versions and SHA-256 manifests.

Artifact:

- workflow run: `30107848065`
- artifact id: `8602443375`
- artifact digest: `sha256:408e95f8c0b682dab398dd52a5694e3bb57533453a33d775d9bd952f55b4ad50`
- artifact size: `72,612,064 bytes`

## Fixed public sources

- SILG: `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM: `58f17955595b5a127c96d045d896fcbcc7d4b570`
- train: `silg:rtfm_train_s1-v0`
- evaluation: `silg:rtfm_test_s1-v0`
- model: official SILG `multi` recurrent
- pretrained language model: none
- seeds: `1,7,19`

The only external-source patch makes actor and validation RNGs deterministic functions of the declared experiment seed. Model architecture, optimizer, V-trace loss, observation schema and environment dynamics are unchanged.

## Training smoke resources

Training budget is deliberately small: `2,048` requested frames, with official final checkpoints reporting `2,080` frames because updates proceed in fixed unroll batches.

| Seed | Wall time | Peak RSS | Extracted model bytes | Model SHA-256 |
|---:|---:|---:|---:|---|
| 1 | 26.560 s | 477,160 KiB | 19,693,911 | `1d5dfce4...f9052f1c2` |
| 7 | 26.592 s | 493,576 KiB | 19,693,911 | `67a9326d...987eac23` |
| 19 | 26.565 s | 454,260 KiB | 19,693,990 | `8672cbbd...216f2e1` |

- parameters: `4,916,915`
- maximum training RSS: `493,576 KiB`
- untrained-model CPU forward audit: `7.611 ms/environment step`
- 1GB resource ceiling: passed on the GitHub Actions host
- weak-smartphone hardware: not tested

## Matched evaluation protocol

Each method receives twenty independently created episodes per seed. Episode seed is:

`experiment_seed * 1,000,003 + episode_index`

A fresh environment is created for every method and episode, and the initial observation fingerprint is checked. All methods matched on all `60` initial instances.

Inference controls:

- `correct`: unmodified trained official recurrent policy;
- `random`: uniform choice among currently valid actions;
- `language_blind`: zero `wiki` and `task` fields;
- `state_only`: zero `wiki`, `task`, `inv`, and grid `name` fields.

No future state, reward, outcome, completed trajectory or gold action is exposed.

## Matched 3-seed result

| Method | Win rate | Mean return | Mean episode length | CPU inference |
|---|---:|---:|---:|---:|
| Correct | 0.0167 | -1.8820 | 46.77 | 8.124 ms/step |
| Random | **0.0667** | **-1.1513** | 15.23 | 0.0109 ms/step |
| Language-blind | 0.0167 | -1.9087 | 48.10 | 8.028 ms/step |
| State-only | 0.0000 | -2.1243 | 57.22 | 7.990 ms/step |

Evaluation peak RSS was `298,808 KiB`; total matched-evaluation wall time was `124.071 s`.

## Interpretation

The matched evaluation infrastructure is now operational, but the 2,048-frame model is not a reproduced capability baseline:

- `correct` is below random on win rate and return;
- removing `wiki` and `task` changes aggregate win rate by exactly zero and only minimally changes return;
- seed 7 and seed 19 produce identical correct/language-blind scores;
- the result is consistent with an undertrained recurrent policy, not evidence that language is unnecessary in the published task.

Classification:

`matched_fixed_episode_smoke_completed / public_capability_baseline_not_reproduced / insufficient_training_budget`

The result must not be used as evidence for or against a new intelligence principle.

## Remaining contract gaps

The current run still does not complete the full R0.1 capability contract:

1. paper-scale or convergence-checked training is absent;
2. official published-score tolerance comparison is absent;
3. language shuffle, target-label shuffle and outcome/transition shuffle are absent;
4. held-out entity/dynamics/language-form transfer is absent;
5. test trajectories and per-step predictions are not yet exported into `evaluation_contract.py`'s full paired-statistics schema.

## Next minimal work

Increase the official recurrent budget in staged, checkpointed increments and evaluate the same fixed episode seeds after each stage. Stop increasing the budget when either:

- the official policy clearly exceeds random and language-blind controls, enabling formal matched evaluation; or
- the published setup cannot be approached within declared compute limits, which must be recorded as a reproduction-resource limitation.

No R0.2 environment-first superiority claim or R0.3 causal-identification experiment is authorized from this smoke result.

## Status

- checkpoint persistence: completed
- matched fixed-instance evaluation path: completed
- official public capability baseline: not reproduced
- novelty: not established
- capability progress: not recognized
- high-school-level intelligence: not achieved
