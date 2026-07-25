# Intelligence Swarm Backlog

## P0 — Complete one clean SILG recurrent reproduction

Accepted evidence remains the official SILG `multi` recurrent at 32,768 requested frames for seeds `1,7,19`, with matched fixed-instance controls:

- parameters: `4,916,915`
- state-dict audit bytes: `19,694,385`
- maximum RSS: `505,600 KiB`
- total three-seed training time: `1,033.885 s`
- CPU forward audit: `6.911 ms/step`
- Correct win rate: `0.0167`
- Random win rate: `0.0667`
- Language-blind、State-only、Language-shuffle: each `0.0167`

Classification: `matched_fixed_episode_32768_frame_staged_training_not_public_capability_reproduction`。

Current canonical headに131,072-frameの検証済み完了artifactはない。未完了・cancelled・duplicate runを証拠にしない。

Authorized actions:

1. stable workflow headからexactly one 131,072-frame runを起動・完了する。
2. seed `1,7,19`の3 checkpointとraw logsを検証する。
3. Correct、Random、Language-blind、State-only、within-environment language shuffleを同一immutable instanceで評価する。
4. source/model/data/raw-log/prediction SHA-256、full code commit、model bytes、RSS、training wall time、CPU latency、seed、splitを保存する。
5. policy competenceとaction collapseを監査する。
6. competence不成立なら、公式再現条件の検証済み不一致だけを最小修正するか、事前登録した上限でresource/budget insufficiencyと分類する。

Forbidden:

- failed-policy trajectoryでR0.2を調整する。
- architecture/mechanism familyを追加する。
- favorable seed/instanceを選ぶ。
- incompetent policyからlanguage irrelevanceを結論する。
- unfinished/cancelled/duplicate runを成果扱いする。

## P0 — Immutable R0.1 evaluation

R0.1完了条件は、competent learned public baselineとcontrolsが一つのfrozen serialized test instance bundleをseed `1,7,19`で消費すること。

Required controls:

- official recurrent Correct
- random valid action
- language-blind
- state-only
- environment-ID-only
- within-environment language shuffle
- transition/outcome shuffle
- target-label shuffleはnon-oracle labelが存在する場合のみ。存在しなければformal inapplicability record

Required outputs:

- per-instance prediction/fingerprint
- complete `method × seed × domain × split × condition` coverage
- win/return/episode length
- source/model/data/raw-log/prediction hashes
- model bytes/RSS/training time/CPU latency
- paired cell and episode statistics
- preregistered public-reference tolerance

## P0 — Evaluation, statistics, leakage and provenance

Implemented audits:

- D015: concrete SILG schema adaptation and core leakage checks
- D016: immutable prediction-to-dataset joins and exact instance coverage
- D017: exact seed coverage `1,7,19` for every domain/split/condition cell
- D018: target-label/outcome shuffle donor provenance、same-cell、bijection、derangement、semantic no-op rejection
- D019: entity/dynamics holdout leakage by condition and signature
- D020: episode-cluster hierarchical bootstrap、episode sign-flip、step/episode weighted gaps、minimum cell gap
- D021: prediction/data/raw-log/checkpoint/full commit/model bytes/RSS/training time/CPU latency cell binding
- D022: semantic model-input leakage aliases including `future_state`、`rollout_context`、`target_action`、`chosen_action`、`oracle_*`、reward/success/outcome aliases

D022 prospective input allowlist:

- `utterance`
- `state_before`
- `history`
- `valid_action_mask`

D022の4 testsはローカル成功。GitHub Actions完了は未確認。実R0 prediction/data/artifact bundleはD016〜D022を通過していないため、正式分類は **`initial_reproduction_failure`**。

Next evaluation action:

1. 新しい監査器を増やす前に、実R0 bundleを既存D016〜D022へ投入する。
2. failureが出た箇所だけを再現可能なlogとして固定する。
3. evaluatorの欠陥ではなくdata/run欠陥なら、実験側の最小修正だけを行う。

## P1 — R0.2 Environment-first faithful transfer

Primary reference:

- Gaddy & Klein 2019
- `dgaddy/environment-learning`
- commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f`

Implemented paths:

1. `gaddy_klein_typed_baseline.py`
   - language-free transition pretraining
   - 20 categorical message variables × 30 symbols
   - straight-through Gumbel-Softmax
   - shared typed next-state/action decoder
   - LSTM language encoder
   - direct message matching weight `0.01`
   - decoder freezing
   - typed CE/BCE/MSE
   - canonical seeds、hash/resource reporting
2. `export_silg_typed_policy_trajectories.py`
   - typed before/after fields、schema/cardinality
   - episode/seed/split/fingerprint provenance
   - dataset/schema SHA-256
   - text/reward/done/outcome exclusion
3. `r02_typed_comparison.py`
   - Environment-first / parameter-matched End-to-end / State-only
   - equal data、seed、split、row exposure
   - online task successをoffline accuracyで代用しない
4. `audit_r02_matched_budget.py`
   - parameter bytes、row exposure、checkpoint/hash、RSS、time、CPU latency、metrics
5. `audit_r02_holdout_assignments.py`
   - entity/dynamics/language-form signature、3-seed coverage、train/test disjointness、placeholder rejection
6. `attach_r02_holdout_manifest.py`
   - immutable preregistered manifest join by `domain/split/seed/episode_seed`
7. `build_r02_preregistered_holdout_manifest.py`
   - generator metadataと事前登録済みsignature集合だけからmanifest生成
   - action/reward/done/return/task success/prediction/action accuracy/next-state lossを入力として拒否
   - seed `1/7/19`、unique episode keys、non-empty signatures、test metadata existence、3-seed coverage、train holdout禁止、SHA-256

Current blocker:

- pinned RTFM generatorから`entity_signature`、`dynamics_signature`、`language_form_signature`をepisode sidecarとしてまだ実出力していない
- qualified competent three-seed source trajectoriesがない
- online task success、typed next-state、action accuracy、real transfer metricsがない

Current classification:

`preregistered_holdout_manifest_builder_implemented_generator_signature_sidecar_and_qualified_silg_execution_blocked`

Minimal next correction:

1. pinned RTFM generator/configuration stateから、rollout outcomeを見る前に3 signatureをsidecar出力する。
2. versioned preregistration JSONを固定する。
3. manifestを生成・joinし、holdout auditを通す。
4. competent R0.1 trajectoriesが得られた後だけmatched comparisonを実行する。

Representation appearance、compression、clusteringは進歩に数えない。モデル調整は認可しない。

## Closed — Empirical Gate I / R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず、R0.3 hidden intervention-target ablationとRQ-001-N5は棄却維持。

## Closed — Broad RQ-001 formulation

Rejected:

- finite benchmark上でraw languageが全unrestricted finite auxiliary representationを超える
- grammar/mechanism restrictionなしでlanguage factorsとlatent target blocksを共同識別する
- unknown target recovery、environment label recovery、parameter namingをlanguage-specific causal identificationとする
- shuffle degradation、semantic naming、prediction improvement、non-zero language effectだけでidentifiabilityを主張する
- partial shared-latent discoveryを新規性とする
- known observational groupingのlanguage再記述をjoint identificationとする
- text embeddingをfeature-conditioned intervention modelへ渡すだけで新しいcausal identificationとする
- unseen perturbation predictionやtarget probabilityをpartition identifiabilityの証拠とする

## P2 — Only admissible RQ reformulation, not adopted

Preregistration candidate only:

> feature-conditioned generative intervention modelsを含む既存のintervention/general-environment/trajectory-local/multimodal/known-grouping identifiabilityを適用した後に、externally fixed denotational anchorを持つpopulation language channelが、raw utterance equivalenceと残存latent intervention-target partitionを共同同定できるか。

Before adoption:

1. predictive attributionとpartition identifiabilityの形式的分離
2. language encoder/intervention generator/latent model/decoderのjoint recoding後に残る同値類
3. outcome、target label、environment ID、completed trajectoryから生成されないexternal denotational anchor
4. target partitionの一意性定理
5. anchorまたはtarget separation除去時のimpossibility theorem
6. feature-conditioned GIM baselineとの直接比較
7. unseen utterance form/composition/target combination/system split
8. discrete/stochastic/non-injective population language channel
9. dependency-pinned public baseline reproduction
10. exactly one preregistered claim、counterexample、stopping rule

No implementation、synthetic benchmark、architecture is authorised.

## P1 — Prior-art and novelty matrix

Matrix must remain current through relevant 2026 primary work and official code where available.

Current included boundaries:

- unknown/uncoupled intervention CRL
- general-environment CRL
- subset-intervention causal abstraction
- finite-sample CRL
- trajectory-local parameter identifiability
- auxiliary/temporal/multi-view/hidden-regime nonlinear ICA
- grouping/weak supervision and known observational grouping
- mechanism sparsity and mechanistic independence
- interactive grounding
- environment-first representation learning
- language-dynamics pretraining
- WM3C and multimodal partial-sharing CRL
- isolated causal effects of language
- feature-conditioned generative intervention models

C018:

- Morioka and Hyvärinen, ICML 2024
- official `hmorioka/GCaRL` commit `0020bfce34736d61d70ab8175f061d02951a7ed4`
- known observational groupingを新規language contributionから除外

C019:

- Schneider et al., ICML 2025, Generative Intervention Models
- observed perturbation featureからunknown atomic intervention distributionを学習する既存領域を追加
- unseen perturbation predictionはtarget-partition identificationを保証しないcounterexampleを固定
- corresponding official implementation repositoryは一次記録と対象GitHub検索で未特定

Novelty matrixは拡張されたがstage-transition用にclosedとは認定しない。

## P2 — Japanese realism audit

Pinned candidate: official `riken-grp/J-CRe3`。commit、license、downloads、checksums、split/schemaを固定し、supported text/vision/combined baselinesを再現する。SILGへ平均せずGate Iにも使わない。

## Stage transition

次stageは以下すべての完了後だけ提案する。

1. learned external public capability baseline
2. immutable-instance controls
3. canonical 3-seed prediction/artifact/leakage contract
4. qualified R0.2 online comparison with typed metrics and real holdouts
5. formal R0.3 rejection
6. novelty matrix through 2026 closed for the successor claim
7. exactly one preregistered successor claim/theorem、counterexamples、stopping rule

## Frozen work

- new toy benchmarks/mechanisms
- memory/replay/fast weights/sleep/forgetting
- best-seed/average-only positives
- prospective leakage
- new stacked PR chains
- smoke/offline imitation as intelligence progress
- manual Gate-I ontology
- R0.2 tuning on failed demonstrations
- RQ implementation before formalization/preregistration
