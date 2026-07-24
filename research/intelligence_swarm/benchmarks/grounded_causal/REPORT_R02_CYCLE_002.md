# R0.2 Environment-first Baseline — Cycle 002

## Scope

This cycle did not introduce a new architecture or toy hypothesis. It removed public-reproduction dependency mismatches, executed the official SILG `multi` recurrent training path on public RTFM S1, and recorded the model/resource baseline required before an environment-first comparison can be meaningful.

## Public-source dependency repair

Pinned SILG imports `SlurmJob` from `expman.job`, while the previously resolved `expman==0.0.5` did not provide that API. The compatible `expman==0.0.7` source archive contains the required module but omits the `requirements.txt` file read by its own `setup.py` and does not expose its `ujson` runtime dependency through a usable installation path.

The canonical installer now:

1. downloads the exact `expman-0.0.7.tar.gz` source distribution;
2. verifies SHA-256 `5b778d23d9efdb541d72783d1ecf1482451cc1a476eb7e16fb52d6b2ce1445c6`;
3. restores the missing empty packaging file;
4. pins `ujson==5.10.0`;
5. verifies `Experiment`, `JSONLogger`, and `SlurmJob` before training.

No SILG model, objective, environment transition, observation, or action semantics were altered.

## Successful public recurrent smoke

GitHub Actions run `30104299406` completed successfully.

- artifact: `r0-silg-rtfm-probe-30104299406`
- artifact digest: `sha256:51d8bfb3fe31f4a00d9b5f86f1bc2761da5f91c70067d222e8f376f334418070`
- SILG commit: `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM commit: `58f17955595b5a127c96d045d896fcbcc7d4b570`
- model: official SILG `multi` recurrent
- pretrained language model: none
- train environment: `silg:rtfm_train_s1-v0`
- validation environment configured: `silg:rtfm_test_s1-v0`
- seeds: `1, 7, 19`
- training budget: `2,048` frames per seed
- actor seed patch: `experiment_seed * 1,000,003 + actor_index`

| Seed | Completed | Wall time | Peak RSS |
|---:|:---:|---:|---:|
| 1 | yes | 26.547 s | 462,752 KiB |
| 7 | yes | 26.531 s | 516,792 KiB |
| 19 | yes | 31.536 s | 481,432 KiB |

Mean wall time was `28.205 s/seed`; maximum observed RSS was `516,792 KiB`, below 1 GiB.

## Model and CPU audit

The official untrained `multi` recurrent model was constructed against the real public RTFM observation schema.

- parameters: `4,916,915`
- trainable parameters: `4,916,915`
- serialized state dict: `19,694,385 bytes`
- state-dict SHA-256: `29b6865d2366e30a59ee82b8e098f806b7b26b2b2d67231e18fca2a167540b62`
- CPU forward latency: `7.490 ms/environment step`

The inference measurement is an engineering audit on the GitHub-hosted CPU, not a weak-smartphone result.

## Canonical random control

The same public workflow ran RTFM S1 random-valid-action control with seeds `1, 7, 19`, 20 episodes per seed.

| Seed | Win rate | Mean return | Mean episode length |
|---:|---:|---:|---:|
| 1 | 0.15 | -1.003 | 21.05 |
| 7 | 0.15 | -1.030 | 17.50 |
| 19 | 0.10 | -1.181 | 22.50 |

This is an environment control, not an identical-instance evaluation of the trained policy.

## Remaining gap before R0.2 comparison

The recurrent execution is a short training-path smoke test, not the official full-budget score reproduction. The following remain incomplete:

- deterministic checkpoint evaluation on captured identical RTFM instances;
- official full-budget recurrent score;
- language-blind and state-only trained controls;
- public-trajectory environment-first pretraining;
- matched model/data/optimization budgets;
- held-out entity, dynamics, and language-form transfer;
- next-state prediction, action accuracy, and task-success comparison;
- trained-checkpoint size and trained-policy CPU latency.

## Decision

- public recurrent training path: **reproduced at smoke budget**
- public model size/RSS/runtime/CPU audit: **completed**
- public full baseline score: **not reproduced**
- environment-first public comparison: **not started**
- capability progress: **not claimed**
- novelty or new intelligence principle: **not claimed**
- high-school-level intelligence: **not achieved**

The next productive step is deterministic trajectory/checkpoint evaluation followed by matched official recurrent, environment-first, end-to-end, language-blind, state-only, language-shuffle, and transition-shuffle comparisons on identical public instances.
