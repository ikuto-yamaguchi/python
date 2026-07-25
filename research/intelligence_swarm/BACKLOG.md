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

Current canonical headに131,072-frameの検証済み完了artifactはない。workflow修正、trigger更新、run要求、監査文書は能力進捗に数えない。

Authorized actions:

1. stable workflow headからexactly one 131,072-frame runを完了する。
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
- complete `method × seed × domain × split × condition` coverage
- win/return/episode length
- source/model/data/raw-log/prediction hashes
- model bytes/RSS/training time/CPU latency
- paired cell and episode statistics
- preregistered public-reference tolerance

## P0 — Evaluation, statistics, leakage and provenance

Implemented through D024:

- concrete SILG schema adaptation
- immutable prediction-to-dataset joins
- exact seed coverage `1,7,19`
- target-label/outcome shuffle donor provenance・same-cell・bijection・derangement・semantic no-op rejection
- entity/dynamics holdout leakage audit
- episode-cluster hierarchical bootstrap・episode sign-flip・step/episode weighting・minimum cell gap
- prediction/data/raw-log/checkpoint/full commit/model bytes/RSS/time/CPU latency cell binding
- semantic aliases including `future_state`、completed `rollout_context`、`target_action`、`chosen_action`、`oracle_*`、reward/success/outcome aliases
- semantic auditorのcanonical CI必須接続
- immutable実bundle結合後にdataset契約、semantic leakage、shuffle provenance、prediction coverage、paired/cluster statisticsを一括実行するend-to-end bundle audit

Remaining:

1. 新しい監査器を増やさず、実R0 bundleをD016〜D024へ投入する。
2. failure箇所だけを再現可能なlogとして固定する。
3. evaluatorではなくdata/run欠陥なら実験側の最小修正だけを行う。
4. target-labelがSILG schemaで定義不能ならformal inapplicability recordを固定し、擬似labelを作らない。

Formal classification remains **`initial_reproduction_failure`**。

## P1 — R0.2 Environment-first faithful transfer

Primary reference:

- Gaddy & Klein 2019
- `dgaddy/environment-learning`
- commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f`

Implemented and connected paths:

1. `gaddy_klein_typed_baseline.py`
   - language-free transition pretraining
   - 20 categorical message variables × 30 symbols
   - straight-through Gumbel-Softmax
   - shared typed next-state/action decoder
   - LSTM language encoder
   - direct message matching weight `0.01`
   - decoder freezing
   - typed CE/BCE/MSE
2. `export_silg_typed_policy_trajectories.py`
   - typed before/after fields、schema/cardinality
   - episode/seed/split/fingerprint provenance
   - dataset/schema SHA-256
   - text/reward/done/outcome exclusion
3. `r02_typed_comparison.py`
   - Environment-first / parameter-matched End-to-end / State-only
   - equal episode exposure、seed、split、epoch budget
   - online task successをoffline accuracyで代用しない
4. matched-budget、holdout、immutable-manifest audits
5. canonical R0.1 workflowからtyped export・3-method comparison・holdout auditへ接続

Current blockers:

- pinned RTFM generatorから`entity_signature`、`dynamics_signature`、`language_form_signature`をepisode sidecarとしてまだ実出力していない
- competent qualified three-seed source policy trajectoriesがない
- online task success、typed next-state、action accuracy、real transfer metricsがない

Minimal next correction:

1. pinned generator/configuration stateから、rollout outcomeを見る前に3 signature sidecarを出力する。
2. versioned preregistration JSONを固定する。
3. manifestを生成・joinし、holdout auditを通す。
4. competent R0.1 trajectoryが得られた後だけmatched comparisonを正式実行する。

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
- intervention-induced quotientを言語で命名・予測することをstrict refinementとする

## P2 — Only admissible RQ reformulation, not adopted

Preregistration candidate only:

> 最強のnon-language intervention-induced quotientを先に構成した後、externally fixed denotational anchorを持つpopulation language channelが、残存quotient blockをstrict refinementし、raw utterance equivalenceとrefined intervention-target partitionを共同同定できるか。

Before adoption:

1. non-language quotient equivalence classの明示
2. residual-equivalent models間のpositive-measure language-law separation
3. outcome、target label、environment ID、completed trajectoryから独立なexternal anchor
4. joint recodingを防ぐanti-recoding condition
5. quotient block strict-refinement theorem
6. anchor/residual-information条件除去時のimpossibility theorem
7. non-language quotient、quotient-label language、genuinely residual languageの直接ablation
8. unseen utterance form/composition/target combination/system split
9. dependency-pinned public baseline reproduction
10. exactly one preregistered claim、counterexample、stopping rule

No implementation、synthetic benchmark、architecture is authorised.

## P1 — Prior-art and novelty matrix

Matrix must remain current through relevant 2026 primary work and official code where available.

Current accepted boundary:

- Li, Kaba, and Ravanbakhsh, AISTATS 2025, `On the Identifiability of Causal Abstractions`
- unknown subset interventionsから識別可能な最大因果抽象をintervention-induced quotientとして追加
- quotientを命名・予測するlanguageはlatent partitionをstrict refinementしないcounterexampleを固定
- official implementationは一次記録から未特定

## Stage transition

次stageは以下すべての完了後だけ提案する。

1. competent learned external public capability baseline 1件以上
2. immutable matched controls
3. complete canonical three-seed prediction/artifact/leakage qualification
4. qualified R0.2 online comparison with real entity/dynamics/language-form holdouts
5. retained R0.3 rejection
6. novelty matrix closed through relevant 2026 primary work and official code
7. exactly one preregistered successor claim with theorem、counterexample、stopping rule

## Status

- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- 完成: **false**
