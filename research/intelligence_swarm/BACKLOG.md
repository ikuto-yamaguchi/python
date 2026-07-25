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

Run `30158106220` completed install、schema/random probe、131,072 requested frames × seeds `1,7,19` training、and matched Correct/Random/Language-blind/State-only/Language-shuffle evaluation. It then failed during the R0.2 typed trajectory/baseline step before dependency freeze and artifact upload. Workflow artifacts are empty. None of the new checkpoint、performance、resource、or log values are accepted.

Required next actions:

1. Use only the canonical split-job workflow on `research/intelligence-swarm-reconstruction-001`.
2. Run `r01-public-reproduction` and verify immutable artifact upload immediately after matched R0.1 evaluation.
3. Retrieve and verify seed `1,7,19` checkpoints and actual frame counters before R0.2 consumes them.
4. Verify Correct、Random、Language-blind、State-only、Language-shuffle use identical initial instances.
5. Verify model bytes、peak RSS、training wall time、CPU latency、seed、split、raw logs、source/model/data/prediction checksums.
6. Feed the preserved R0.1 bundle through the unified evaluation contract and preserve the first failure.
7. Audit policy competence and action collapse before interpreting any ablation.
8. Do not place R0.2 inside the R0.1 preservation boundary.

Queue control:

- R0.1 workflow runs only on benchmark-code/run-request pushes or manual dispatch.
- Governance/prior-art commits must not enqueue another long reproduction.
- Existing pending/duplicate runs are not results.
- R0.2 may start only by downloading an uploaded immutable R0.1 artifact.

Forbidden:

- new toy mechanism or architecture family
- favorable seed/instance selection
- failed-policy trajectory tuning
- interpreting incompetent-policy ablations as language irrelevance
- counting workflow edits、queued/cancelled runs、documents、or unaudited step success as capability progress

## P0 — Evaluation, statistics, leakage and provenance

Implemented through D029:

- SILG real-schema adaptation
- train/test utterance overlap
- entity/dynamics split leakage
- gold action/after-state/completed-trajectory/post-treatment leakage
- semantic alias/value leakage
- exact global and per-cell seeds `1,7,19`
- domain/split/condition non-missing checks
- train and evaluation presence per seed
- immutable prediction/data/log/checkpoint/commit/resource joins
- random/language-blind/state-only/target-label shuffle/outcome shuffle same-instance coverage
- shuffle donor provenance、same-cell bijection、derangement、semantic no-op rejection
- observed sparse `domain × split × condition` topology shared by all methods/seeds
- mean gap、minimum cell gap、paired randomization、McNemar、episode-cluster bootstrap CI
- model bytes、RSS、training wall time、CPU latency、raw logs、checksums
- D027 exact six-method artifact coverage、one data path/hash per cell、one immutable code commit per bundle
- D028 exact prediction topology: only `correct/random/language_blind/state_only/target_label_shuffle/outcome_shuffle`; reject extras、global omissions、per-instance omissions、per-cell omissions、and evaluation-external predictions
- D029 core-contract enforcement: `evaluation_contract.py` itself rejects extra prediction/artifact methods、mixed full code commits、and different `data_path + data_sha256` identities within one `seed × domain × split × condition` cell

D028 short CI run `30165709843` passed. D029 reports a successful focused local regression, while the current head has no published combined-status checks. These validate code paths only; they do not establish a real benchmark result.

Remaining:

1. Do not add another auditor unless a preserved real bundle exposes a concrete false pass/failure.
2. Apply the unified contract to the next preserved R0.1 artifact.
3. Preserve the first failing condition and raw evidence.
4. If target-label is undefined in SILG, record formal inapplicability instead of inventing labels.
5. Require the core contract and companion auditors to agree on the same method registry、full code commit、and per-cell dataset identity.

Formal classification remains **`initial_reproduction_failure`** until a real bundle passes.

## P1 — R0.2 Environment-first faithful transfer

Primary reference:

- Gaddy & Klein 2019
- `dgaddy/environment-learning`
- commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f`

Implemented:

- language-free transition pretraining followed by instruction following
- Environment-first / parameter-matched End-to-end / State-only
- typed before/after trajectory export without reward/outcome leakage
- generator-side entity/dynamics/language-form signatures
- immutable `(domain, split, seed, episode_seed)` join
- offline next-state/action comparison
- same-initial-instance online task evaluation
- checkpoint/model bytes、RSS、wall time、CPU latency、logs、hashes

RTFM S1 boundary:

- dynamics holdout: measurable
- entity holdout: formally inapplicable in S1
- language-form holdout: formally inapplicable in S1

Run `30158106220` produced no preserved R0.2 artifact and is classified as failed. No task success、next-state prediction、action accuracy、or transfer result is accepted.

Remaining:

1. Start only after an immutable R0.1 artifact exists and passes basic checkpoint/resource integrity.
2. Download that artifact in the separate R0.2 job.
3. Produce and audit the 3-seed signature-to-trajectory join artifact.
4. Pass the real dynamics holdout audit.
5. Measure and audit task success、next-state prediction、action accuracy and transfer for all three methods and seeds.
6. Confirm source-policy competence before attributing differences to representation learning.
7. Use another public benchmark such as J-CRe3 only after its official split/code/dependencies are reproduced; do not create synthetic entity/language-form holdouts.

Representation appearance、compression、clusteringは進歩に数えない。モデル調整は認可しない。

## Closed — R0.3 hidden intervention-target track

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず、R0.3 empirical trackを棄却維持する。

## P1 — Prior-art and novelty matrix

Integrated boundaries:

- C023: state-dependent local-dynamics identifiability
- C024: isolated causal effects of natural language
- C025: mechanistic independence

Previously retained boundaries include unknown-target CRL、finite-sample recovery、causal abstraction quotient/coarsening、grouped/multimodal CRL、interactive OpenLock transfer、concept/context-conditioned causal disentanglement、LLM-guided intervention selection、language-model graph priors。

No new branch evidence after C025 changes the adoption decision. The novelty matrix remains incomplete and must still be closed through relevant 2026 primary work and official code.

## P2 — Only admissible RQ reformulation, not adopted

Candidate only:

> 最強のnon-language estimator、mechanistic-independence criterion、完全なprospective interaction history、isolated-language-effect adjustmentを条件付けた後にも同一mechanistic component内に残るexplicit countermodel pairに対して、externally fixed・non-recodableなpopulation language contrastが不足するseparationを供給し、raw utterance equivalenceとresidual intervention-target partitionを有限標本またはconsistentに共同同定できるか。

Before adoption:

1. explicit residual countermodel pair inside one mechanistic component
2. positive-measure language-law separation
3. outcome/trajectory/environment identity/factor-effect supportから復元不能なexternal anchor
4. joint recodingを防ぐ条件
5. strict joint-identification theorem
6. anchor/residual-information除去時のimpossibility theorem
7. finite-sampleまたはconsistency保証
8. strongest non-language、mechanistic-independence、interactive-transfer、isolated-language-effect baselineとの比較
9. unseen form/composition/target/system split
10. dependency-pinned public baseline reproduction
11. exactly one preregistered claim、counterexample、stopping rule

No implementation、synthetic benchmark、new architecture is authorised.

## Stage transition

次stageは以下すべての完了後だけ提案する。

1. competent learned external public capability baseline
2. immutable matched controls
3. complete canonical three-seed prediction/artifact/leakage qualification
4. qualified R0.2 online comparison with real dynamics holdout and entity/language-form boundary
5. retained R0.3 rejection
6. novelty matrix closed through relevant 2026 primary work and official code
7. exactly one preregistered successor claim with theorem、counterexample、stopping rule

## Status

- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- 完成: **false**