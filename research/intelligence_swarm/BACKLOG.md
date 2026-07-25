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
10. Treat `R01_RUN_REQUEST.json` changes only as execution requests, never as evidence.

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

Implemented through D035:

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
- D033 core scorer validation for leaked gold/after-state/reward/terminal/return/success/future-state/rollout/completed-trajectory fields、unregistered fields、non-finite values、and invalid actions
- D034 alias-normalized recursive schema audit for camelCase、kebab-case、spaces、punctuation variants in `model_input_fields`、nested `model_input`、and prediction keys
- D035 mandatory invocation of the alias-normalized auditor inside `audit_r0_acceptance_bundle.py`, together with core contract、prediction payload、paired statistics、resource provenance、and prediction/statistics checksum audits

Current focused CI:

- unified acceptance gate run `30179464716`: success
- prediction method topology run `30179464653`: success

These runs validate audit code only. No real R0 bundle has passed.

Remaining:

1. Apply the unified D015–D035 gate to the next preserved R0.1 artifact.
2. Preserve all component errors and the first actionable root cause.
3. If target-label is undefined in SILG, record formal inapplicability instead of inventing labels.
4. Require core contract and companion auditors to agree on method registry、code commit、per-cell dataset identity、prediction payload、prediction/statistics checksums、resource provenance、and alias-normalized schema findings.
5. Do not add another auditor unless a preserved real bundle exposes a concrete false pass/failure not covered by D035.

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
- holdout-manifest validation for duplicate/missing rows and domain/split/seed/episode_seed mismatch
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
- C033: partially shared multimodal causal representation identifiability
- C034: score-based causal representation learning under linear/general transformations

C034 adds that under explicit intervention-diversity、smoothness、invertibility、score-estimation、and discrepancy assumptions, latent variables、DAG、and unknown intervention-target correspondence are identifiable and constructively recoverable without language. The official consolidated repository `acarturk-e/score-based-crl` is verified, but an exact commit and immutable native reproduction remain outstanding.

The novelty matrix must now separate:

1. general-environment CRL;
2. projected high-level causal-query identification;
3. unknown-target graph/context/target recovery under JCI/TICL assumptions;
4. maximal quotient abstraction induced by the actual intervention family;
5. partial-sharing multimodal component identification;
6. score-based latent/graph/target recovery under the strongest applicable linear or diffeomorphic theorem;
7. residual partition recovery after all applicable non-language sufficient statistics;
8. language-supplied information beyond observations、actions、outcomes、interaction history、environment/context signatures、score differences、detected targets、quotient signatures、and multimodal incidence;
9. joint raw-utterance / residual-target identification under an external anti-recoding law.

Required score-based prior-art work:

1. map SILG episodes to observational/interventional environments;
2. audit hard/soft、single-node/multi-node、score-estimation、smoothness、invertibility、and intervention-diversity assumptions;
3. pin an exact commit of `acarturk-e/score-based-crl`;
4. preserve the selected environment specification、subdirectory、command、raw outputs、and checksums;
5. reproduce the strongest applicable LSCALE-I、GSCALE-I、or UMNI-CRL baseline before any language-specific superiority claim.

## P2 — Only admissible RQ reformulation, not adopted

Candidate only:

> 最強の適用可能なscore-based CRLと他の非言語causal abstractionを適用した後、その許容変換でquotientしても残るcountermodel pairに対して、externally fixed・non-recodableなpopulation language contrastが不足するseparationを供給し、raw utterance equivalenceとresidual intervention-target partitionを有限標本またはconsistentに共同同定できるか。

Necessary but insufficient condition:

`I(P_residual ; L | S_SCRL) > 0`

Before adoption:

1. map SILG observations、instructions、actions、outcomes to observational/interventional environments and modalities;
2. audit the strongest applicable score-based and non-score identifiability assumptions;
3. compute the maximal non-language quotient、graph、target incidence、and score-based representation;
4. exhibit an identical-observable-law countermodel pair after score-based recovery;
5. prove the language contrast is unavailable from observations、actions、outcomes、environment identity、scores、detected targets、and completed trajectories;
6. fix an external denotational anchor before fitting;
7. prove the target/utterance/denotation/encoder-decoder joint automorphism group becomes trivial;
8. give an impossibility theorem when language only names or paraphrases a recovered node、environment、or component;
9. use direct recovery metrics for utterance classes and residual target blocks;
10. reproduce the strongest applicable official score-based baseline;
11. preregister exactly one claim、counterexample、and stopping rule;
12. require model bytes、RSS、wall time、CPU latency、raw logs、checksums、seeds `1/7/19` once experiments begin.

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