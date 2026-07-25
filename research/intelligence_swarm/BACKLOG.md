# Intelligence Swarm Backlog

## P0 — Complete one clean SILG recurrent reproduction

Accepted evidence remains the official SILG `multi` recurrent at 32,768 requested frames for seeds `1,7,19`.

- parameters: `4,916,915`
- state-dict audit bytes: `19,694,385`
- maximum RSS: `505,600 KiB`
- total three-seed training time: `1,033.885 s`
- CPU forward audit: `6.911 ms/step`
- Correct win rate: `0.0167`
- Random win rate: `0.0667`
- Language-blind / State-only / Language-shuffle: each `0.0167`

Classification: `matched_fixed_episode_32768_frame_staged_training_not_public_capability_reproduction`。

Verified pre-integration head `830b1d13b39f9ab450271a1cf286aeee7f38bf25`に131,072-frameの検証済み完了artifactやregistered combined statusはない。workflow修正、trigger更新、run要求、監査文書は能力進捗に数えない。

Authorized actions:

1. stable canonical headからexactly one 131,072-frame runを完了する。
2. seed `1,7,19`の3 checkpoint、raw log、source/model/data/prediction hashを検証する。
3. Correct、Random、Language-blind、State-only、within-environment language shuffleを同一immutable instanceで評価する。
4. model bytes、RSS、training wall time、CPU latency、seed、splitを保存する。
5. policy competenceとaction collapseを監査する。
6. competence不成立なら、公式条件との検証済み差分だけを最小修正するか、事前登録した上限でresource/budget insufficiencyと分類する。

Forbidden:

- failed-policy trajectoryでR0.2を調整する
- architecture/mechanism familyを追加する
- favorable seed/instanceを選ぶ
- incompetent policyからlanguage irrelevanceを結論する
- unfinished/cancelled/duplicate runを成果扱いする

## P0 — Immutable R0.1 evaluation

Required controls:

- official recurrent Correct
- random valid action
- language-blind
- state-only
- environment-ID-only
- within-environment language shuffle
- transition/outcome shuffle
- target-label shuffleはnon-oracle labelが存在する場合のみ。なければformal inapplicability record

Required outputs:

- per-instance prediction/fingerprint
- complete `method × seed × domain × split × condition` coverage over the preregistered observed topology
- win/return/episode length
- source/model/data/raw-log/prediction hashes
- model bytes/RSS/training time/CPU latency
- paired cell and episode statistics
- preregistered public-reference tolerance

## P0 — Evaluation, statistics, leakage and provenance

Implemented through D025:

- concrete SILG schema adaptation
- immutable prediction-to-dataset joins
- exact seed coverage `1,7,19`
- target-label/outcome shuffle donor provenance・same-cell・bijection・derangement・semantic no-op rejection
- entity/dynamics holdout leakage audit
- episode-cluster hierarchical bootstrap・episode sign-flip・step/episode weighting・minimum cell gap
- prediction/data/raw-log/checkpoint/full commit/model bytes/RSS/time/CPU latency cell binding
- semantic aliasesによるgold action/after-state/completed trajectory/post-treatment leakage拒否
- immutable実bundle結合後のdataset契約、semantic leakage、shuffle provenance、prediction coverage、paired/cluster statistics一括監査
- observed `domain × split × condition` sparse topologyを全method・seedで固定

Remaining:

1. 新しい監査器を増やさず、実R0 bundleをD016〜D025へ投入する。
2. failure箇所だけを再現可能なlogとして固定する。
3. evaluatorではなくdata/run欠陥なら実験側の最小修正だけを行う。
4. target-labelがSILG schemaで定義不能ならformal inapplicability recordを固定し、擬似labelを作らない。

Formal classification remains **`initial_reproduction_failure`**。

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
2. `export_silg_typed_policy_trajectories.py`
   - typed before/after fields、schema/cardinality
   - episode/seed/split/fingerprint provenance
   - dataset/schema SHA-256
   - text/reward/done/outcome exclusion
3. `r02_typed_comparison.py`
   - Environment-first / parameter-matched End-to-end / State-only
   - equal episode exposure、seed、split、epoch budget
   - offline typed next-state/action metrics
4. `export_rtfm_generator_signatures.py`
   - outcome非依存でpinned generator内部からentity/dynamics/language-form signatureを抽出
   - RTFM S1ではdynamics holdoutだけをreal holdoutとして認定
5. `evaluate_r02_online_silg.py`
   - 3手法を同じseed・同じinitial-instance streamでonline評価
   - task success、return、episode length、model/checkpoint bytes、RSS、wall time、CPU latency、paired gap
6. matched-budget、holdout、immutable-manifest audits

Current blockers:

- generator signature sidecarとtyped trajectoryのqualified immutable join artifactがない
- holdout auditorによるreal dynamics splitの正式通過がない
- online SILG evaluatorの3-seed artifactがない
- competent qualified three-seed source policy trajectoriesがない
- task success、typed next-state、action accuracy、real dynamics transferの3-seed結果がない
- RTFM S1はentity ontologyと言語生成familyをtrain/testで分離しないため、real entity/language-form holdoutはS1単独では測定不能

Minimal next correction:

1. generator signature sidecarを`(domain, split, seed, episode_seed)`でtyped trajectoryへimmutable joinする。
2. join後datasetをholdout auditへ入力し、real dynamics holdoutだけを認定する。
3. online evaluatorを3 seedで実行し、artifactを保存する。
4. RTFM S1のentity/language-form holdoutはformal inapplicabilityとして記録し、擬似holdoutを作らない。
5. competent R0.1 trajectoryが得られた後だけmatched comparisonを正式認定する。
6. entity/language-form transferには、公式にそのsplitを持つ別公開benchmark（候補J-CRe3を含む）の再現が必要。

Representation appearance、compression、clusteringは進歩に数えない。モデル調整は認可しない。

## Closed — Empirical Gate I / R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず、R0.3 hidden intervention-target ablationとRQ-001-N5は棄却維持。

## Closed — Broad RQ-001 formulation

Rejected:

- finite benchmark上でraw languageが全unrestricted finite auxiliary representationを超える
- grammar/mechanism restrictionなしでlanguage factorsとlatent target blocksを共同識別する
- unknown target recovery、environment label recovery、parameter namingをlanguage-specific causal identificationとする
- shuffle degradation、semantic naming、prediction improvement、non-zero language effectだけでidentifiabilityを主張する
- known grouping、feature-conditioned intervention prediction、intervention-induced quotient namingを新規性とする
- strongly separating environmentsで既に回復可能なunknown multi-node targetsを言語の新規貢献とする
- OpenLock型prospective transfer成功をraw-language equivalence/latent partitionの一意性証拠とする
- supplied concept/contextによるcausal disentanglement、context modules、OOD concept compositionを新規性とする

## P2 — Only admissible RQ reformulation, not adopted

Preregistration candidate only:

> 最強のnon-language estimatorと完全なprospective interaction historyを先に条件付け、その後にも残るequivalence classに対して、externally fixed・non-recodableなpopulation language contrastが不足するseparationを供給し、raw utterance equivalenceとresidual intervention-target partitionを有限標本またはconsistentに共同同定できるか。

Before adoption:

1. strongest applicable non-language method後にも残るexplicit countermodel
2. complete prospective interaction historyでも区別不能なmodel pair
3. residual-equivalent models間のpositive-measure language-law separation
4. environment identity、incidence、observation、action、outcome、completed trajectoryから復元不能なexternal anchor
5. joint recodingを防ぐanti-recoding condition
6. strict equivalence-class reduction theorem
7. anchor/residual-information条件除去時のimpossibility theorem
8. finite-sampleまたはconsistency保証を持つestimator
9. non-language separating/non-separating、behavioural interactive transfer、quotient-label languageとの直接比較
10. unseen utterance form/composition/target combination/system split
11. dependency-pinned public baseline reproduction
12. exactly one preregistered claim、counterexample、stopping rule

No implementation、synthetic benchmark、architecture is authorised.

## P1 — Prior-art and novelty matrix

Matrix must remain current through relevant 2026 primary work and official code where available.

Newly integrated boundary:

- Xiang et al. 2026, `Grounding Before Generalizing: How AI Differs from Humans in Causal Transfer`
  - OpenLock型interactive causal transferを評価するが、behavioural successはinternal partitionのjoint identifiabilityを保証しない
  - linked public code was unavailable at the audited link; no reproduction claimed
- Markham et al. 2026, `Intervening to learn and compose causally disentangled representations`
  - supplied concept/context informationを使うcausally disentangled representation、context module、OOD composition、identifiability result
  - raw utterance equivalenceとunknown latent target partitionのjoint identificationではない

Previously retained boundary includes unknown-target CRL、finite-sample recovery、causal abstraction quotient/coarsening、LLM-guided intervention selection、noisy language-model graph priors、multimodal/grouped CRL。

## Stage transition

次stageは以下すべての完了後だけ提案する。

1. competent learned external public capability baseline 1件以上
2. immutable matched controls
3. complete canonical three-seed prediction/artifact/leakage qualification
4. qualified R0.2 online comparison with real dynamics holdout、かつentity/language-form transferの別公開splitまたはformal inapplicability boundary
5. retained R0.3 rejection
6. novelty matrix closed through relevant 2026 primary work and official code
7. exactly one preregistered successor claim with theorem、counterexample、stopping rule

## Status

- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- 完成: **false**
