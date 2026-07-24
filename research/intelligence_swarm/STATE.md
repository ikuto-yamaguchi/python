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
- R0.3 empirical intervention-target ablation: **未開始・SILGでは禁止**
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

32,768-frame公式recurrent学習はseed `1,7,19`すべてでcheckpoint作成まで完走した。最初のmatched evaluationは、言語ablationが公式packed RNNへ長さ0のsequenceを渡したため停止した。canonical branchはtoken内容をmaskしつつ1-token padding lengthを維持するよう修正済み。

- Workflow run: `30117375864`
- Status at E013 integration: **in progress**

補正workflowが完了するまで、32,768-frame能力値やtrajectory資格を確定しない。

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
- duplicate / missing prediction
- domain × seed × condition cell統計
- episode-level paired gap、Correct-only / control-only、exact McNemar検定
- hierarchical cluster-bootstrap 95% CI
- source/model/data/log SHA-256、code commit、model bytes、RSS、train time、CPU latency

strict controlsと完全prediction-to-artifact manifestが不足するため、現在の正式分類は **`initial_reproduction_failure`**。

## Prior-art and novelty boundary

未知介入下のnonparametric CRL、unknown multi-node intervention、score-based CRL、subset-intervention causal abstraction、finite-sample few-environment recovery、environment-first instruction following、language-dynamics pretraining、multimodal shared-latent recovery、perturbation-to-intervention modeling、causal sufficiency/necessityは単独では既存範囲である。

広い「言語とtrajectoryから未知因果変数を発見する」は中心命題として採用しない。

## Candidate research question status

SILG/RTFMはground-truth latent intervention family、target、mechanism pre/post operator、causal abstractionを定義しないため、Gate Iの直接benchmarkとして棄却した。

- **Gate L — 継続・未達:** competent public policyとmatched controlsで、raw languageがstate/action/history/environment identityを超える外部能力を持つか測る。
- **Gate I — empirical track blocked:** 監査したSILG/RTFM、J-CRe3、CausalTriplet、ACCESS、MIBは必要条件を同時に満たさない。

現在の候補は **RQ-001-N5 — narrowed, not adopted**:

> 独立にmechanism-changing variationを定義する公開benchmark上で、episode-aligned raw languageが完全な非言語trajectoryを条件とした後にもmechanism情報を持ち、trajectory-only CRLに残る同値類を厳密に細分化し、held-out mechanism能力を改善するか。

必要条件は `I(M; L | X) > 0`。`X`はstate、action、history、reward、time、policy phase、environment identityを含む。

適格benchmarkがnovelty audit完了までに見つからなければempirical Gate Iを閉じ、明示仮定を持つtheory-onlyの不可能性または十分条件へ限定する。

## Current maximum bottleneck

**補正済み32,768-frame matched-evaluation artifactを確定し、checkpoint、model、data、log provenance、policy competence、trajectory eligibilityを監査すること。合格するまでR0.2調整と新規architectureを禁止する。並行してGate-I適格公開benchmarkを最終監査し、見つからなければempirical RQを閉じる。**

## Stage-transition rule

次stageを提案できるのは全て満たした場合だけ。

1. 学習済み外部公開能力baselineを少なくとも1件再現
2. immutable公開instance上のrandom / language-blind / state-only / shuffle対照
3. canonical 3 seedと完全artifact/leakage contract
4. R0.2のonline task success、typed next-state、実holdout付き比較
5. R0.3を適格benchmarkで完了、またはundefined/unavailableとして正式棄却
6. 2026年までのnovelty matrix
7. 中心命題、主要指標、停止条件の事前登録

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

2026-07-25: **RESET-E013**。補正済み32,768-frame workflowは実行中のため未確定値を統合せず、R0.1〜R0.3、prior-art境界、evaluation contract、RQ-001-N5、段階遷移条件を一本化した。学習済み公開能力baselineは0件であり、R0継続・段階遷移禁止を維持した。
