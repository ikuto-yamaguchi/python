# Intelligence Swarm State

## Mission

1GB未満・弱いスマートフォンCPUで実行可能な知能モデルを長期目標とし、生の日本語と環境相互作用から対象・状態・操作・因果構造を獲得する原理を研究する。ただし現在は原理発明を停止し、公開研究の再現、評価資格、新規性境界を確立する。

## Current stage

- Stage: **R0 Research Reconstruction — public capability reproduction and benchmark qualification**
- Semantic Identity Gate G1: **未達**
- Operation/Goal Gate G2: **未達**
- Formal memory eligibility: **未達**
- 学術的新規性: **未確立**
- 査読可能な中心命題: **未確立**
- Active mechanism family: **なし**
- AF-001〜AF-014: **PAUSED**
- A〜Dの新規toy仮説、別branch、新規memory機構: **停止**
- 過去stacked draft PR: **negative-results archive**

## R0 status ledger

- 公開環境control再現: **1件**
- 公開学習経路再現: **1件**
- 固定初期instance matched評価経路: **1件（engineering smoke）**
- 学習済み公開能力baseline再現: **0件**
- R0.2正式再現: **0件**
- R0.3 empirical intervention-target ablation: **正式棄却**
- RQ-001-T1 theory-only candidate: **未採用**
- J-CRe3日本語外部監査: **未再現**

公開能力baselineとmatched controlsがevaluation contractを通るまで、新規機構族、知能原理、能力進歩を認定しない。

## Pinned SILG / RTFM reproduction

- SILG commit: `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM commit: `58f17955595b5a127c96d045d896fcbcc7d4b570`
- Train: `silg:rtfm_train_s1-v0`
- Test: `silg:rtfm_test_s1-v0`
- Seeds: `1,7,19`
- Python 3.8.18 / Ubuntu 22.04
- Core pins: `torch==1.13.1+cpu`, `torchvision==0.14.1+cpu`, `gym==0.21.0`, `numpy==1.24.4`, `transformers==4.30.2`, `expman==0.0.7`, `ujson==5.10.0`
- Observation: 6×6 grid, wiki 80 token, task 40 token, inventory 8 token, valid-action mask 5, relative position 6×6×2
- Action space: 5; maximum episode length: 80

## R0.1 public recurrent status

2,048-frame級の公式SILG `multi` recurrentについて、seed `1,7,19`の学習、checkpoint保存・再読込、固定初期instance上のCorrect / Random / Language-blind / State-only評価経路を再現した。

- Parameters: `4,916,915`
- Trained state dict: 約`19.694 MB`
- Training wall time: 約`26.6 s/seed`
- Maximum RSS: `493,576 KiB`
- CPU inference: 約`8.1 ms/step`
- Correct win rate: `0.0167`
- Random win rate: `0.0667`
- Language-blind win rate: `0.0167`
- State-only win rate: `0.0000`

Classification: **`matched_fixed_episode_smoke_completed / public_capability_baseline_not_reproduced / insufficient_training_budget`**。

32,768-frame公式recurrent学習はseed `1,7,19`すべてでcheckpoint作成まで完走した。最初のmatched evaluationは、言語ablationが公式packed RNNへ長さ0のsequenceを渡したため停止し、token内容をmaskしつつ1-token padding lengthを維持するよう修正済み。

- Current corrected workflow run: `30120620610`
- Status at RESET-E014 integration: **in progress**

補正workflowのartifact、完全checksum、matched fingerprint、policy competence、trajectory eligibilityが確定するまで、32,768-frame能力値を統合しない。

## R0.2 Environment-first status

旧公開trajectory上のoffline比較:

- Environment-first action accuracy: `0.6840`
- End-to-end: `0.6907`
- State-only: `0.7240`
- Environment-first language-blind: `0.6840`
- Environment-first language-shuffle: `0.6840`

しかし生成元policyは比較資格を満たさなかった。

- seed 1 train success: `0/40`
- seed 7 train success: `0/40`; majority action share `97.42%`
- seed 19 train success: `1/40`
- 全seed test success: `0/20`

Classification: **`ineligible_failed-policy-trajectory_negative_diagnostic / not_R0.2_reproduction`**。

R0.2を再開する前に、各seedで次を満たす。

- majority-action share `<= 0.90`
- successful train episode `>= 5`
- 5%以上のsupportを持つaction `>= 2`

正式比較ではtyped observation-field transition loss、online task success、実entity/dynamics/language-form holdout、matched parameter/data budget、同一instance controlsを必須とする。

## Evaluation contract status

`evaluation_contract.py`とSILG episode adapterは以下を監査する。

- train/test utterance overlap、entity/dynamics split overlap
- gold action、after state、reward、done、post-treatment state、completed trajectory leakage
- prediction側のimmutable `instance_fingerprint`
- method × seed × domain × split完全coverage
- duplicate / missing predictionとduplicate method-seed run
- domain × seed × condition cell統計
- episode-level paired gap、Correct-only / control-only、exact McNemar検定
- hierarchical cluster-bootstrap 95% CI
- run-level集計値とepisode recordsの再計算一致
- full 40-hex SILG/RTFM source pins
- full 64-hex checkpoint/model/data/log SHA-256
- model bytes、RSS、training wall time、CPU latencyの有限・正値監査
- `answer_leakage: false`、`pretrained_language_model: false`の明示

7件の回帰テストは成功した。Target-label shuffle、Outcome shuffle、immutable test dataset checksum、raw workflow log実体との独立joinが不足するため、現在の正式分類は **`initial_reproduction_failure`**。

## Prior-art and novelty boundary

未知介入下のnonparametric CRL、unknown multi-node intervention、score-based CRL、subset-intervention causal abstraction、finite-sample few-environment recovery、environment-first instruction following、language-dynamics pretraining、multimodal shared-latent recovery、perturbation-to-intervention modeling、causal sufficiency/necessity、causal-world-modelと言語interfaceは単独では既存範囲である。

広い「言語とtrajectoryから未知因果変数を発見する」は中心命題として採用しない。

## Research-question decision

SILG/RTFMはground-truth latent intervention family、target、mechanism pre/post operator、causal abstractionを定義しない。J-CRe3、CausalTriplet、ACCESS、MIB、CausalPhysを含む監査済み候補も、episode-aligned raw language、interactive trajectory、独立mechanism change、held-out mechanism ground truth、permutation-aware評価を同時に満たさない。

- **Gate L — 継続・未達:** competent public policyとmatched controlsで、raw languageがstate/action/history/environment identityを超える外部能力を持つか測る。
- **Gate I empirical track — 正式棄却:** 現在の公開benchmark制約下で共同同定実験を開始しない。研究者がtarget/mechanism ontologyを後付けすることも禁止する。
- **RQ-001-N5 — 棄却:** empirical joint-identification claimとして閉じる。
- **RQ-001-T1 — theory-only candidate, not adopted:** 明示した観測・介入仮定の下で、言語がtrajectory-only causal equivalence classを厳密に細分化できる条件と不可能条件を特徴づける。

必要条件 `I(M; L | X) > 0` は十分条件ではない。T1採用前にformal observation model、equivalence relation、既存multimodal ICA/CRLとの差、非自明なpositive/negative construction、事前登録が必要であり、R0.1完了前の新規architectureは禁止する。

## Current maximum bottleneck

**補正済み32,768-frame matched-evaluation artifactを確定し、checkpoint、model、data、raw-log provenance、policy competence、trajectory eligibilityを監査すること。合格するまでR0.2調整と新規architectureを禁止する。Empirical Gate Iは閉じ、理論候補T1も事前登録条件を満たすまで開始しない。**

## Stage-transition rule

次stageを提案できるのは全て満たした場合だけ。

1. 学習済み外部公開能力baselineを少なくとも1件再現
2. immutable公開instance上のrandom / language-blind / state-only / shuffle対照
3. canonical 3 seedと完全artifact/leakage contract
4. R0.2のonline task success、typed next-state、実holdout付き比較
5. R0.3 empirical trackの正式棄却をgovernanceへ統合
6. 2026年までのnovelty matrix
7. exactly one中心命題、主要指標、反例、停止条件の事前登録

## Canonical branch policy

今後の研究は`research/intelligence-swarm-reconstruction-001`だけへ累積する。過去のstacked draft PRを新実験のbaseにしない。

## Current status

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 完成: **false**

## Last integration

2026-07-25: **RESET-E014**。C007のempirical Gate-I棄却とtheory-only候補T1、D011のprovenance・集計再計算監査を統合した。補正済み32,768-frame workflow run `30120620610`は実行中のため未確定値を採用せず、学習済み公開能力baseline 0件、R0継続、段階遷移禁止を維持した。