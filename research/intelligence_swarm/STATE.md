# Intelligence Swarm State

## Mission

長期目標は、1GB未満で弱いスマートフォンCPU上でも高速に動作し、日本語コミュニケーション・知識・推論を備える知能モデルである。現在は新しい知能原理や機構族の発明を停止し、公開benchmark再現、評価資格、既存研究との境界、反証可能な中心命題の確立を優先する。

## Current stage

- Stage: **R0 Research Reconstruction — public capability reproduction and benchmark qualification**
- Semantic Identity Gate G1: **未達**
- Operation/Goal Gate G2: **未達**
- Formal memory eligibility: **未達**
- 学術的新規性: **未確立**
- 査読可能な中心命題: **未確立**
- Active mechanism family: **なし**
- A〜Dの新規toy仮説、別branch、新規memory/replay/fast-weights/sleep/forgetting: **停止**
- 過去stacked draft PR: **negative-results archive。新作業のbaseにしない**

## R0 status ledger

- 公開環境control再現: **1件**
- 公開学習経路再現: **1件（SILG/RTFM、32,768-frame staged budget、seed 1/7/19）**
- 固定初期instance matched評価経路: **1件**
- 131,072-frame staged reproduction: **検証済み完了artifactなし**
- 学習済み公開能力baseline再現: **0件**
- R0.2正式再現: **0件**
- R0.2 typed baseline/export/comparison/budget/holdout/manifest paths: **実装・workflow接続済み、qualified public dataで未実行**
- R0.3 empirical hidden intervention-target ablation: **正式棄却**
- RQ-001 broad/current formulation: **棄却**
- residual quotientをlanguageでstrict refinementする狭義候補: **未採用**
- J-CRe3日本語外部baseline: **未再現**

公開能力baselineとmatched controlsがevaluation contractを通るまで、新規機構族、知能原理、能力進歩を認定しない。

## Pinned SILG / RTFM reproduction

- SILG commit: `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM commit: `58f17955595b5a127c96d045d896fcbcc7d4b570`
- Train: `silg:rtfm_train_s1-v0`
- Test: `silg:rtfm_test_s1-v0`
- Seeds: `1,7,19`
- Model: official `multi` recurrent
- Pretrained language model: **なし**
- Python 3.8.18 / Ubuntu 22.04
- Core pins: `torch==1.13.1+cpu`, `torchvision==0.14.1+cpu`, `gym==0.21.0`, `numpy==1.24.4`, `transformers==4.30.2`, `expman==0.0.7`, `ujson==5.10.0`
- Observation: 6×6 grid、wiki 80 token、task 40 token、inventory 8 token、valid-action mask 5、relative position 6×6×2
- Action space: 5、maximum episode length: 80

## R0.1 public recurrent evidence

Accepted completed evidence remains the 32,768-requested-frame, 32,800-checkpoint run for seeds `1,7,19`.

| Seed | Training wall time | Peak RSS | Trained model bytes |
|---:|---:|---:|---:|
| 1 | 341.906 s | 480,076 KiB | 19,693,911 |
| 7 | 346.898 s | 505,600 KiB | 19,693,911 |
| 19 | 341.882 s | 483,056 KiB | 19,693,990 |

- Parameters: `4,916,915`
- State-dict audit size: `19,694,385 bytes`
- CPU forward audit: `6.911 ms/step`
- Total three-seed training wall time: `1,033.885 s`
- Maximum RSS: `505,600 KiB`

| Method | Win rate | Mean return | Mean episode length | CPU inference |
|---|---:|---:|---:|---:|
| Correct recurrent | `0.0167` | `-1.8827` | `46.80` | `7.229 ms/step` |
| Random valid action | `0.0667` | `-1.1513` | `15.23` | `0.0081 ms/step` |
| Language-blind | `0.0167` | `-2.0417` | `54.75` | `4.424 ms/step` |
| State-only | `0.0167` | `-2.1963` | `62.48` | `4.103 ms/step` |
| Language-shuffle | `0.0167` | `-1.9347` | `49.40` | `7.252 ms/step` |

Correctは1/60、Randomは4/60。policy competence不足であり、言語不要の証拠ではない。

Classification: **`matched_fixed_episode_32768_frame_staged_training_not_public_capability_reproduction`**。

131,072-frame workflowはtrigger対象とtyped R0.2接続が修正済みだが、完了run・artifact・checkpoint・新しい能力値は確認されていない。workflow編集や起動操作は能力進捗に数えない。

## R0.2 Environment-first status

Gaddy & Klein 2019と著者code commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f`を固定参照とする。

Canonical workflowはtyped SILG trajectoryをseed `1/7/19`でexportし、Environment-first、parameter-matched End-to-end、State-onlyを同一episode exposure・epoch budgetで実行する経路へ接続されている。typed next-state/action metrics、checkpoint、model bytes、RSS、training time、CPU latencyを保存する設計である。

ただしpinned RTFM generatorは、事前登録された`entity_signature`、`dynamics_signature`、`language_form_signature` sidecarをまだ実出力していない。competentなR0.1 policy trajectoryもないため、online task success、typed next-state prediction、action accuracy、real transferは未認定・未測定である。

Classification: **`typed_execution_path_connected_but_generator_signatures_and_qualified_source_policy_absent`**。

## Evaluation contract status

- D015: 実SILG schema適合とcore leakage checks
- D016: immutable prediction-to-dataset join
- D017: exact seed coverage `1,7,19`
- D018: target-label/outcome shuffle provenance・bijection・derangement・no-op rejection
- D019: entity/dynamics holdout leakage
- D020: episode-cluster bootstrap・sign-flip・minimum cell gap
- D021: prediction/data/log/checkpoint/commit/model bytes/RSS/time/latency cell binding
- D022: semantic aliasesによるgold/post-treatment leakageをfail-closed拒否
- D023: semantic leakage auditorをcanonical CIのwatch・compile・testへ必須接続
- D024: immutable実bundleの結合後に`validate_dataset()`、semantic alias/value leakage、shuffle provenance、prediction coverage、paired/cluster statisticsを一括実行するend-to-end bundle auditへ統合

D024によりartifact integrityと評価統計を別々に通過させる経路は閉じた。ただし実R0 prediction/data/resource bundleはD016〜D024をまだ通過していない。

Formal classification: **`initial_reproduction_failure`**。

## Prior-art and RQ boundary

C020はLi, Kaba, and Ravanbakhsh, AISTATS 2025を監査し、未知subset intervention下で非言語データから識別可能な最大因果抽象がintervention-induced quotientとして既に特徴付けられることを確認した。

言語がそのquotientを命名・予測・再構成するだけではlatent intervention partitionをstrict refinementしない。shuffle gap、next-state prediction、task successもidentifiabilityの証拠ではない。

唯一残る候補は、最強のnon-language quotient適用後も残るblockを、externally fixed denotational anchor付きpopulation language channelがstrict refinementし、raw utterance equivalenceとrefined intervention-target partitionを共同同定できるか、である。

この候補は**未採用**。採用には、residual-equivalent models間のpositive-measure language-law separation、anti-recoding anchor、strict-refinement theorem、anchor/information条件除去時のimpossibility theorem、quotient-label ablation、unseen form/composition/target/system split、公開baseline再現、exactly one preregistered claimが必要。

新規architecture実験は認可しない。

## Current maximum bottleneck

**一つのcleanな131,072-frame公式recurrent runを完了・監査し、competentな外部公開baselineを得ること。**

それまではR0.2 tuning、RQ-001 implementation、新規architectureを禁止する。

## Stage-transition rule

次stageは以下すべての完了後だけ提案できる。

1. 学習済み外部公開能力baseline 1件以上
2. immutable-instance random/language-blind/state-only/shuffle controls
3. canonical 3-seed prediction/artifact/leakage contract
4. R0.2 online task success、typed next-state、実holdout
5. R0.3 formal rejection
6. 2026年一次文献まで閉じたnovelty matrix
7. exactly one preregistered successor claim/theorem、counterexample、停止条件

## Canonical branch policy

全作業は`research/intelligence-swarm-reconstruction-001`だけへ累積する。既存stacked draftsはnegative-results archiveであり、実験baseにしない。

## Current status

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 完成: **false**

## Last integration

2026-07-25: **RESET-E028**。D024 end-to-end bundle auditを統合した。R0.1の完了artifact・能力証拠は増えておらず、公開能力baseline 0件、R0.2正式再現 0件、C020狭義RQ未採用、`initial_reproduction_failure`、段階遷移禁止、高校生級未達を維持する。
