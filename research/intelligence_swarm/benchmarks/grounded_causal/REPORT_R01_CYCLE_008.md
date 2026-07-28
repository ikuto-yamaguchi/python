# R0.1 SILG/RTFM Reproduction Cycle 008

## Scope

This cycle advances public benchmark reproduction only. It adds no new model,
no toy mechanism, and no capability claim.

## Official baseline audit

Pinned public SILG source:

- SILG commit: `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM commit: `58f17955595b5a127c96d045d896fcbcc7d4b570`
- train: `silg:rtfm_train_s1-v0`
- validation/test: `silg:rtfm_test_s1-v0`
- official model: `multi`
- pretrained LM: disabled
- official RTFM launch grid:
  - entropy cost: `0.05`, `0.005`
  - stateful: false
  - local convolution: false
  - field attention: false

The public training loop is actor-learner V-trace with a recurrent shared model.
The launch script defaults to four experiment indices but does not pass an
experiment seed into actors. In `run_exp.py`, each actor instead initializes
its RNG from `os.urandom()`. Therefore the public command does not by itself
provide deterministic trajectory-level reproduction for canonical seeds
1/7/19.

## Minimal reproducibility patch

`run_silg_recurrent_smoke.py` applies only the following runtime patch to the
pinned external source and records before/after SHA-256 values:

1. add `--seed` to the official argument parser;
2. replace actor seed generation with
   `experiment_seed * 1000003 + actor_index`.

The architecture, losses, optimizer, observations, actions and environment are
unchanged.

## Authorized smoke run

The GitHub Actions workflow now performs:

1. pinned SILG/RTFM installation;
2. random valid-action control on canonical seeds `1, 7, 19`;
3. official `multi` recurrent training smoke on the same seeds;
4. 2,048 frames per seed, CPU only;
5. parameter count and serialized state-dict bytes;
6. peak RSS, user/system time, wall time, raw logs and SHA-256 checksums.

Smoke settings reduce only resource scale:

- actors: 2
- learner threads: 1
- batch size: 2
- unroll length: 20
- checkpoint evaluation disabled

These settings verify that the official recurrent learner can initialize,
collect trajectories, update parameters and terminate reproducibly. They are
not the published full-budget result and cannot count as baseline reproduction
or capability progress.

## Current status

At commit `df609f21cfcb886d739896aee1214bd8b9300127`, the workflow definition and
runner are committed to the canonical reconstruction branch. Results must be
accepted only from the uploaded Actions artifact.

Pending measurements:

- recurrent smoke completion for all three seeds;
- model parameters and bytes;
- peak RSS;
- training wall time;
- CPU forward latency;
- canonical random control;
- subsequent matched language-blind and state-only controls.

## Decision

- public environment control: previously reproduced;
- official recurrent full baseline: not reproduced;
- deterministic official recurrent smoke: submitted for execution;
- matched controls: not completed;
- novelty: not established;
- capability progress: not claimed;
- high-school-level intelligence: not achieved.
