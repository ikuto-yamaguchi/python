# Intelligence Swarm Backlog

## P0 — R0.1 matched public capability baseline

Current status: **official SILG/RTFM recurrent training path reproduced; public capability baseline not reproduced**.

### Completed

- SILG commit `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM commit `58f17955595b5a127c96d045d896fcbcc7d4b570`
- Ubuntu 22.04 / Python 3.8.18 installation
- resolved dependency set including `expman==0.0.7` and `ujson==5.10.0`
- RTFM S1 schema probe and random-valid-action public control
- official SILG `multi` recurrent training smoke for seeds `1,7,19`
- 2,048 frames per seed
- parameters, model bytes, RSS, training time and CPU forward latency recorded
- raw workflow artifact and top-level artifact digest recorded
- evaluation contract adapted to SILG exporter schema
- six regression tests for leakage, snapshot identity and artifact coverage

### Reproduced engineering values

- parameters: `4,916,915`
- state dict: `19,694,385 bytes`
- CPU forward latency: `7.49024244 ms/environment step`
- training wall time: `26.547 / 26.531 / 31.536 s`
- maximum peak RSS: `516,792 KiB`
- artifact digest: `sha256:51d8bfb3fe31f4a00d9b5f86f1bc2761da5f91c70067d222e8f376f334418070`

These values prove the public training path and resource audit only. They are not a reproduced task score.

### Next authorized commits — strict order

1. Capture one deterministic `rtfm_test_s1-v0` evaluation set for seeds `1,7,19`.
2. Store dataset SHA-256 and every immutable `instance_fingerprint`.
3. Save and reload the official recurrent checkpoint for test inference.
4. Replay the identical snapshot through:
   - official recurrent
   - random
   - language-blind
   - state-only
   - environment-ID-only
   - language shuffle
   - target-label shuffle where a target proxy is operationally defined without gold leakage
   - outcome/transition shuffle
5. Save every method × seed × split prediction with complete coverage.
6. Record full raw-log/model/data SHA-256, exact code commit, model bytes, peak RSS, train time and CPU inference latency.
7. Run `evaluation_contract.py`; do not interpret scores before it passes.
8. Compare the official recurrent score with paper/code reference under a declared tolerance.

R0.1 completes only when a learned recurrent policy and all required controls are measured on identical public test instances and pass artifact/leakage audit.

## P0 — Benchmark contract

Use `benchmarks/grounded_causal/evaluation_contract.py` for every measured experiment.

Required checks:

- train/test normalized-utterance overlap
- entity and dynamics split overlap
- gold action, next state, reward, done, post-treatment state and completed trajectory leakage
- canonical seeds `1,7,19`
- at least two eligible domains for any research claim
- immutable instance fingerprint agreement across methods
- complete method × seed × domain × split coverage
- prediction coverage and abstention
- domain × seed × condition cells
- paired mean gap, minimum cell gap, approximate 95% CI and paired randomization test
- raw logs, package lock, source SHAs, dataset checksum, model checksum and artifact digest
- model bytes, peak RSS, training wall time and CPU inference latency

Current public result classification: **`initial_reproduction_failure`** because matched test predictions and complete controls/artifacts are absent.

## P1 — R0.2 Environment-first and language-dynamics baselines

Start public comparison only after R0.1 deterministic instance replay and recurrent checkpoint evaluation work.

Reproduce, do not invent:

- Gaddy & Klein 2019 environment-first transition pretraining or a faithful task-matched equivalent
- Zhong et al. 2022 Language Dynamics Distillation or a faithful next-state objective on the same SILG data
- matched end-to-end shared recurrent baseline

Compare on identical trajectories and matched parameter/data budgets:

- task success
- next-state prediction
- action accuracy
- held-out entity transfer
- held-out dynamics/mechanism transfer
- held-out language-form transfer
- model bytes
- peak RSS
- training wall time
- CPU inference latency

The synthetic fixture remains a pipeline smoke test only and must not enter the public score table.

A language contribution requires Full to exceed state/action/history-only, environment-ID-only, language shuffle and transition shuffle on held-out mechanisms. Wording-only transfer is insufficient.

## P1 — R0.3 Intervention-target / abstraction ablation

Run only after R0.1 and R0.2 produce valid public numbers and Gate L is operational.

Conditions on the same trajectory data:

1. intervention target known
2. candidate target set known
3. intervention target unknown
4. target-label shuffle
5. transition/outcome shuffle
6. environment-ID-only

Measure:

- Gate L: language-specific predictive information beyond state/action/history/reward/environment ID
- Gate I: utterance/intervention partition recovery up to shared permutation or the finest intervention-supported abstraction

Gate I is unauthorized until the selected benchmark exhibits enough intervention diversity to define a nontrivial evaluation-only partition without hand-written ontology.

## P1 — Prior-art and novelty matrix

Already established and not standalone contributions:

- unknown-intervention causal representation identifiability
- unknown multi-node intervention recovery
- unknown soft-intervention inference
- finite-sample recovery from few environments
- causal abstraction under subset interventions
- perturbation-target prediction
- multi-environment interactive language grounding
- language-conditioned dynamics pretraining
- environment-first instruction-following pretraining
- language-feature-conditioned intervention distribution modeling

Candidate question:

**RQ-001-N3**

> On a fixed public interactive benchmark, does raw language provide predictive information about held-out mechanism changes beyond state, action, history, reward and environment identity; and, conditional on that gain, can an utterance-conditioned intervention partition be recovered up to joint permutation or the finest intervention-supported causal abstraction without target labels, semantic parsers, object slots, pretrained language models or supplied perturbation semantics?

Status: **NARROWED, NOT ADOPTED**.

Reject or narrow again when:

1. a primary source solves the same joint problem under equal or weaker assumptions;
2. Full fails to exceed state/action/history-only and language shuffle on held-out mechanisms;
3. gains disappear under entity Rename, environment-ID control or transition shuffle;
4. the benchmark lacks intervention diversity and fixing it requires hand-written ontology;
5. target labels, completed trajectories or post-treatment features are required;
6. recovery is exact-name-only and vanishes under shared latent/language permutation;
7. the strongest result remains synthetic rather than public;
8. language gain exists but partition recovery is no better than state/action/history alone.

## P2 — Japanese realism audit

Pinned source: official `riken-grp/J-CRe3` repository.

Tasks:

- pin license, commit, download command, checksum, split and annotation schema
- reproduce public text-only, vision-only and combined reference baselines when supported
- separate direct reference, predicate-argument and bridging reference
- audit subject omission and demonstratives where annotations permit

J-CRe3 does not substitute for SILG R0.1 and must not be averaged into the same primary score.

## P2 — Theory before new mechanism

After valid R0 reproduction, preregister at most one central claim:

- impossibility theorem for joint language–causal alignment under a specified symmetry; or
- sufficient-condition theorem for shared-permutation/abstraction recovery under explicit trajectory and intervention diversity.

No new architecture is authorized before baseline reproduction, novelty comparison, primary metric and stopping rule are preregistered.

## Frozen work

- new opaque-token toy benchmarks
- renamed span/slot/graph/tensor/assembly/attractor mechanisms
- AF-014 derivatives before reproduction
- memory/replay/fast weights/sleep/forgetting optimization
- best-seed, domain-average-only or single-condition positives
- prospective evaluation using after-state or completed trajectory
- new stacked PR chains
- treating random-control or training-path reproduction as intelligence progress
- treating synthetic-fixture scores as public benchmark evidence
- implementing Gate I before Gate L and intervention-diversity validation

## R0 completion rule

R0 completes only when all are true:

- at least one learned external public capability baseline reproduced
- random/language-blind/state-only/shuffle controls measured on identical instances
- at least three canonical seed logs
- full artifact/leakage contract passes
- CPU/RSS/model-size measurements recorded
- R0.2 matched public comparison completed
- R0.3 ablation completed or formally rejected as undefined on the benchmark
- novelty matrix completed through relevant 2026 primary literature
- RQ-001-N3 adopted, further narrowed or rejected
- exactly one next-stage central claim preregistered
