# R0.2 Environment-first Baseline — Cycle 002

## Scope

This cycle did not introduce a new architecture or toy hypothesis. It removed a public-reproduction dependency mismatch, executed the official SILG `multi` recurrent training path on public RTFM S1, and stored the measurements required before an environment-first comparison can be considered meaningful.

## Public-source dependency repair

Pinned SILG imports `SlurmJob` from `expman.job`. The previously resolved `expman==0.0.5` package did not provide that API. PyPI release `expman==0.0.7`, published on 2021-10-08, contains the required module but its source archive omits the `requirements.txt` file read by `setup.py`.

The canonical installer now:

1. downloads the exact `expman-0.0.7.tar.gz` source distribution;
2. verifies SHA-256 `5b778d23d9efdb541d72783d1ecf1482451cc1a476eb7e16fb52d6b2ce1445c6`;
3. restores the missing empty `requirements.txt` packaging file;
4. installs its required `ujson==5.10.0` runtime dependency;
5. verifies imports for `Experiment`, `JSONLogger`, and `SlurmJob` before training.

No SILG model, loss, environment transition, observation, or action semantics were altered.

## Successful public recurrent smoke

GitHub Actions run `30103957538` completed successfully.

- artifact: `r0-silg-rtfm-probe-30103957538`
- artifact digest: `sha256:87076f69f2916b1e92fdfa4c11d1620225660ef7c6d1ab04662d964b967b9c58`
- SILG commit: `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM commit: `58f17955595b5a127c96d045d896fcbcc7d4b570`
- model: official SILG `multi` recurrent
- pretrained language model: none
- train environment: `silg:rtfm_train_s1-v0`
- validation environment configured: `silg:rtfm_test_s1-v0`
- seeds: `1, 7, 19`
- training budget: `2,048` frames per seed
- actor seed patch: `experiment_seed * 1,000,003 + actor_index`

| Seed | Completed | Wall time | Peak RSS | User CPU | System CPU |
|---:|:---:|---:|---:|---:|---:|
| 1 | yes | 26.609 s | 470,236 KiB | 67.74 s | 2.87 s |
| 7 | yes | 26.566 s | 457,640 KiB | 68.27 s | 2.82 s |
| 19 | yes | 26.548 s | 474,548 KiB | 67.38 s | 3.03 s |

Mean wall time was `26.575 s/seed`; maximum observed RSS was `474,548 KiB`, below 1 GiB.

## Canonical random control

The same workflow re-ran public RTFM S1 random-valid-action control with seeds `1, 7, 19`, 20 episodes per seed.

| Seed | Win rate | Mean return | Mean episode length |
|---:|---:|---:|---:|
| 1 | 0.15 | -1.003 | 21.05 |
| 7 | 0.15 | -1.030 | 17.50 |
| 19 | 0.10 | -1.181 | 22.50 |

This is an environment control, not a matched evaluation of the trained policy.

## Remaining gap before R0.2 comparison

The recurrent run is a short training-path smoke test, not the official full-budget score reproduction. It did not yet complete:

- deterministic checkpoint evaluation on captured identical RTFM instances;
- official full-budget recurrent baseline;
- language-blind and state-only trained controls;
- public-trajectory environment-first pretraining;
- matched parameter budget and data budget;
- held-out entity, dynamics, and language-form transfer;
- next-state prediction and task-success comparison;
- trained checkpoint size and CPU policy latency.

The model-audit helper initially failed because it did not import SILG environment registration before directly constructing `Model`. That inspection-only issue is now fixed, and the next workflow run will record parameter count, state-dict bytes, and CPU forward latency.

## Decision

- public recurrent training path: **reproduced at smoke budget**
- public full baseline score: **not reproduced**
- environment-first public comparison: **not started**
- capability progress: **not claimed**
- novelty or new intelligence principle: **not claimed**
- high-school-level intelligence: **not achieved**

The next productive step is to capture deterministic train/test trajectories or checkpoints and compare the official recurrent, environment-first, end-to-end, language-blind, state-only, language-shuffle, and transition-shuffle conditions on identical instances.
