# Intelligence Swarm Backlog

## P0 — Preserve one clean SILG recurrent reproduction bundle

Accepted evidence remains the official SILG `multi` recurrent at 32,768 requested frames、seeds `1,7,19`:

- parameters `4,916,915`
- state-dict audit `19,694,385 bytes`
- maximum RSS `505,600 KiB`
- total training time `1,033.885 s`
- CPU forward `6.911 ms/step`
- Correct `1/60`
- Random `4/60`
- Language-blind / State-only / Language-shuffle `1/60` each

Classification: `matched_fixed_episode_32768_frame_staged_training_not_public_capability_reproduction`。

Run `30158106220` completed install、schema/random probe、131,072 requested frames × seeds `1,7,19` training、and matched Correct/Random/Language-blind/State-only/Language-shuffle evaluation. It then failed during R0.2 before dependency freeze and artifact upload. Workflow artifacts are empty. None of the new checkpoint、performance、resource、or log values are accepted.

Required next actions:

1. Use only the canonical split-job workflow on `research/intelligence-swarm-reconstruction-001`.
2. Run `r01-public-reproduction` and upload the immutable artifact immediately after matched R0.1 evaluation.
3. Verify seed `1,7,19` checkpoints and actual frame counters before R0.2 consumes them.
4. Verify all controls use identical initial instances.
5. Verify model bytes、peak RSS、training wall time、CPU latency、seed、split、raw logs、source/model/data/prediction/statistics checksums.
6. Feed the preserved R0.1 bundle through `audit_r0_acceptance_bundle.py`.
7. Preserve every failed component and the first minimal actionable root cause.
8. Audit source-policy competence and action collapse before interpreting any ablation.
9. Do not place R0.2 inside the R0.1 preservation boundary.

Queue control:

- R0.1 runs only on benchmark-code/run-request pushes or manual dispatch.
- Governance/prior-art commits must not enqueue a long reproduction.
- Pending/duplicate runs are not results.
- R0.2 may start only from an uploaded immutable R0.1 artifact.

Forbidden:

- new toy mechanism or architecture family
- favorable seed/instance selection
- failed-policy trajectory tuning
- interpreting incompetent-policy ablations as language irrelevance
- counting workflow edits、queued/cancelled runs、documents、or unaudited step success as capability progress

## P0 — Evaluation, statistics, leakage and provenance

Implemented through D033:

- SILG real-schema adaptation
- train/test utterance overlap
- entity/dynamics split leakage
- gold action/after-state/completed-trajectory/post-treatment leakage
- semantic alias/value leakage
- exact global and per-cell seeds `1,7,19`
- domain/split/condition non-missing checks
- immutable prediction/data/log/checkpoint/commit/resource joins
- six-method same-instance coverage: Correct、Random、Language-blind、State-only、Target-label shuffle、Outcome shuffle
- shuffle donor provenance、same-cell bijection、derangement、semantic no-op rejection
- observed sparse `domain × split × condition` topology shared by all methods/seeds
- mean gap、minimum cell gap、paired randomization、McNemar、episode-cluster bootstrap CI
- model bytes、RSS、training wall time、CPU latency、raw logs、checksums
- exact six-method artifact and prediction topology
- single full code commit and one data path/hash per cell
- checksummed prediction JSONL and derived statistics artifacts
- unified fail-closed acceptance command
- D033 core scorer validation for leaked gold/after-state/reward/terminal/return/success/future-state/rollout/completed-trajectory fields, unregistered fields, non-finite values, and invalid actions

Current focused CI:

- unified acceptance gate run `30175635819`: success
- prediction method topology run `30175635818`: success

These runs validate audit code only. No real R0 bundle has passed.

Remaining:

1. Do not add another auditor unless a preserved real bundle exposes a concrete false pass/failure.
2. Apply the unified D015–D033 gate to the next preserved R0.1 artifact.
3. Preserve all component errors and the first actionable root cause.
4. If target-label is undefined in SILG, record formal inapplicability instead of inventing labels.
5. Require core contract and companion auditors to agree on method registry、code commit、per-cell dataset identity、prediction payload、prediction/statistics checksums、and resource provenance.

Formal classification remains **`initial_reproduction_failure`** until a real bundle passes.

## P1 — R0.2 Environment-first faithful transfer

Primary reference:

- Gaddy & Klein 2019
- public repository `kristyelee/environment-learning`
- historical reference `dgaddy/environment-learning`
- pinned commit `98c0dc68926ee9535f15019922d2ca871b0ac0b5`
- inspected Git blob SHAs fixed in `GADDY_KLEIN_PUBLIC_REFERENCE_MANIFEST.json`

Implemented:

- language-free transition pretraining followed by instruction following
- Environment-first / parameter-matched End-to-end / State-only
- typed before/after trajectory export without reward/outcome leakage
- generator-side entity/dynamics/language-form signatures
- immutable `(domain, split, seed, episode_seed)` join
- offline next-state/action comparison
- same-initial-instance online task evaluation
- checkpoint/model bytes、RSS、wall time、CPU latency、logs、hashes
- machine-audited author-code → SILG component mapping

RTFM S1 boundary:

- dynamics holdout: measurable
- entity holdout: formally inapplicable in S1
- language-form holdout: formally inapplicable in S1

Remaining blockers:

1. Keep the claim as task adaptation; do not compare RTFM numbers to ACL 2019 native-task numbers.
2. Save the component-mapping validator output with every R0.2 artifact.
3. Execute the authors' code on a native public task.
4. Reproduce the language-data-efficiency curve only after the single-budget three-seed transfer succeeds.
5. Start R0.2 only after an immutable R0.1 artifact passes checkpoint/resource integrity.
6. Produce and audit the three-seed signature-to-trajectory join.
7. Pass the real dynamics holdout audit.
8. Measure task success、next-state prediction、action accuracy and transfer for all methods/seeds.
9. Confirm source-policy competence before attributing differences to representation learning.

Run `30158106220` produced no preserved R0.2 artifact. No R0.2 metric is accepted. Representation appearance、compression、clusteringは進歩に数えない。モデル調整は認可しない。

## Closed — R0.3 hidden intervention-target track

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず、R0.3 empirical trackを棄却維持する。

## P1 — Prior-art and novelty matrix

Integrated boundaries:

- C023: state-dependent local-dynamics identifiability
- C024: isolated causal effects of natural language
- C025: mechanistic independence
- C029: general-environment nonparametric CRL
- C030: lossy projected causal abstraction
- C031: unknown-target JCI / test-time causal discovery
- C032: intervention-induced causal abstraction identifiability

C032 adds that unknown perfect subset interventions can identify a maximal quotient causal abstraction from paired pre/post observations under explicit assumptions. Therefore non-atomic unknown interventions、failure of individual latent recovery、or discovery/naming of quotient blocks do not establish language-specific joint identification.

The novelty matrix must now separate:

1. general-environment CRL;
2. projected high-level causal-query identification;
3. unknown-target graph/context/target recovery under JCI/TICL assumptions;
4. maximal quotient abstraction induced by the actual intervention family;
5. residual within-block partition recovery after all applicable non-language sufficient statistics;
6. language-supplied information beyond observations、actions、outcomes、interaction history、environment/context signatures、detected targets、and quotient signatures;
7. joint raw-utterance / residual-target identification under an external anti-recoding law.

A paper-specific immutable official repository for C032 was not verified. Public baseline reproduction remains required when official code becomes available.

## P2 — Only admissible RQ reformulation, not adopted

Candidate only:

> benchmarkのunknown intervention familyから最大non-language quotient abstractionを計算した後にも残るwithin-block countermodel pairに対して、externally fixed・non-recodableなpopulation language contrastが不足するseparationを供給し、raw utterance equivalenceとresidual intervention-target partitionを有限標本またはconsistentに共同同定できるか。

Necessary but insufficient condition:

`I(P_residual ; L | S_abs) > 0`

Before adoption:

1. construct intervention-family non-descendant signatures for the benchmark;
2. compute the maximal quotient partition and quotient graph identifiable without language;
3. exhibit a within-block countermodel pair;
4. prove the language contrast is unavailable from observations、actions、outcomes、environment identity、and completed trajectories;
5. fix an external denotational anchor before fitting;
6. prove the within-block target/utterance/denotation/encoder joint automorphism group becomes trivial;
7. give an impossibility theorem when language only names or paraphrases a quotient block;
8. use direct recovery metrics for utterance classes and residual target blocks;
9. reproduce an applicable public non-language baseline;
10. preregister exactly one claim、counterexample、and stopping rule;
11. require model bytes、RSS、wall time、CPU latency、raw logs、checksums、seeds `1/7/19` once experiments begin.

No implementation、synthetic benchmark、new architecture is authorised.

## Stage transition

次stageは以下すべての完了後だけ提案する。

1. competent learned external public capability baseline
2. immutable matched controls
3. complete canonical three-seed prediction/artifact/leakage qualification
4. qualified R0.2 online comparison with real dynamics holdout and entity/language-form boundary
5. retained R0.3 rejection
6. novelty matrix closed through relevant primary work and official code
7. exactly one preregistered successor claim with theorem、counterexample、stopping rule

## Status

- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- 完成: **false**
