# Intelligence Swarm State

## Mission

1GB未満・弱いスマートフォンCPUで実行可能な知能モデルを長期目標とする。ただし現在は新原理の発明を停止し、公開benchmark再現、評価資格、既存研究との境界、反証可能な中心命題の確立を優先する。

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
- 131,072-frame staged reproduction: **current headで検証済み完了artifactなし**
- 学習済み公開能力baseline再現: **0件**
- R0.2正式再現: **0件**
- R0.2 typed full-method / typed exporter / matched comparison harness: **実装済み、qualified public dataで未実行**
- R0.3 empirical hidden intervention-target ablation: **正式棄却**
- RQ-001 broad/current formulation: **棄却**
- externally anchored residual-symmetry refinement: **狭義化・未採用**
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
- Observation: 6×6 grid, wiki 80 token, task 40 token, inventory 8 token, valid-action mask 5, relative position 6×6×2
- Action space: 5; maximum episode length: 80

## R0.1 public recurrent status

Completed workflow run `30120620610` reproduced the official SILG `multi` recurrent training path for seeds `1,7,19` at 32,768 requested frames and saved 32,800-frame checkpoints.

### Training and resources

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
- Artifact digest: `662139632c73082f096154d819bef20f86f672d4e8f5b36f8667d754b6b751d2`

### Matched fixed-instance evaluation

| Method | Win rate | Mean return | Mean episode length | CPU inference |
|---|---:|---:|---:|---:|
| Correct recurrent | `0.0167` | `-1.8827` | `46.80` | `7.229 ms/step` |
| Random valid action | `0.0667` | `-1.1513` | `15.23` | `0.0081 ms/step` |
| Language-blind | `0.0167` | `-2.0417` | `54.75` | `4.424 ms/step` |
| State-only | `0.0167` | `-2.1963` | `62.48` | `4.103 ms/step` |
| Language-shuffle | `0.0167` | `-1.9347` | `49.40` | `7.252 ms/step` |

Correctは1/60、Randomは4/60。これはpolicy competence不足であり、言語不要の証拠ではない。

Classification: **`matched_fixed_episode_32768_frame_staged_training_not_public_capability_reproduction`**。

### 131,072-frame status

固定timeout、重複trigger、再起動問題は修正済みだが、RESET-E022時点のcanonical head `5dfa423808c2348a774eae1d64ddd8186cecf9be`には関連workflow run、combined status、検証済み完了artifactがない。未完了checkpoint、resource値、trajectory、能力値は採用しない。

次の唯一のR0.1作業は、stable workflow headから1本だけ実行し、3 checkpoint、raw log、source/model/data/prediction hash、RSS、学習時間、CPU latency、同一instance controls、policy competence、action-collapseを検証すること。

## R0.2 Environment-first status

旧trajectory比較はnegative diagnosticのみ。source policyはseed 1でtrain success `0/40`、seed 7で`0/40`かつmajority action `97.42%`、seed 19で`1/40`、全test `0/20`で不適格。

Gaddy & Klein 2019と著者code commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f`を固定参照とする。

Canonical branchには以下がある。

- `gaddy_klein_typed_baseline.py`: language-free transition pretraining、20 categorical message variables × 30 symbols、straight-through Gumbel-Softmax、shared typed next-state/action decoder、LSTM language encoder、direct message matching `0.01`、decoder freezing、typed CE/BCE/MSE、resource/hash reporting。
- `export_silg_typed_policy_trajectories.py`: typed before/after fields、schema/cardinality、episode/seed/split/fingerprint provenance、dataset/schema SHA-256、unknown field fail-closed。
- `r02_typed_comparison.py`: Environment-first、parameter-matched End-to-end、State-onlyを同一typed dataset・seed・splitで比較。Environment-firstとEnd-to-endのinference parameter bytes不一致は拒否する。

Cycle 011 harnessはaction accuracy、typed next-state loss、entity/dynamics/language-form holdout、独立online fieldがある場合だけtask success、CPU latency、training wall time、peak RSS、checkpoint bytes/hash、dataset hashを保存する。offline accuracyをtask successの代用にしない。

Qualifiedな3-seed public trajectoryがないため未実行。Classification: **`matched_typed_offline_comparison_harness_implemented_execution_on_qualified_silg_data_blocked`**。

## Evaluation contract status

D015は実SILG schemaへ適合し、**18件の実行済み回帰テスト**を持つ。

D016は各`method × seed × domain × split × condition`についてprediction-to-dataset immutable joinを要求する。

D017は各`domain × split × condition` cellにseed `1,7,19`が正確に揃うことを要求する。

D018はshuffleのdonor割当だけでなく、実際に適用されたpayloadを値レベルで監査する。

- `target_label_shuffle`: `replace_gold_action_from_donor`、donor target hashとapplied payload hashの一致。
- `outcome_shuffle`: `replace_gold_state_after_from_donor`、donor outcome hashとapplied payload hashの一致。
- 同一cell、bijection、derangement、self-shuffle禁止に加え、各cellで最低1件のsemantic value changeを要求する。

D018の4テストはローカル成功。current headのGitHub Actions完了結果は未確認なので、CI成功数としては計上しない。実shuffle prediction bundle、immutable test serialization、完全artifact join、competent baselineがないため、正式分類は **`initial_reproduction_failure`**。

## Prior-art and novelty boundary

既存境界にはunknown/uncoupled intervention CRL、general-environment CRL、subset-intervention causal abstraction、finite-sample CRL、trajectory-local parameter identifiability、auxiliary/temporal/multi-view/hidden-regime nonlinear ICA、grouping/weak supervision、mechanism sparsity、mechanistic independence、interactive grounding、environment-first、language-dynamics pretraining、WM3Cを含む。

C015は、明示的target labelがないことだけをlanguage necessityの根拠にする主張を追加で棄却した。Baumgartner et al. 2026は、trajectory間で変化するsystem parameterを、local transition graph、mechanism sparsity、Jacobian variation、graphical separationの条件下で、言語なしにpermutationとelement-wise diffeomorphismまで識別する。

trajectory-onlyで残る対称性が`theta'_i = h_i(theta_(pi(i)))`なら、language generatorも`g'(theta',X,E,epsilon)=g(H^-1(theta'),X,E,epsilon)`と再定義でき、`p(X,E,L)`は不変である。したがってparameter naming、language-conditioned prediction、shuffle gap、fluent/compositional descriptionsだけではsymmetry breakingを証明しない。

## Research-question decision

- Gate L: **継続、未通過**。
- Gate I empirical track / R0.3: **棄却**。
- RQ-001-N5: **棄却**。
- RQ-001 broad/current form: **棄却**。
- Unknown target recovery、environment label recovery、parameter namingをlanguage-specific causal identificationとする案: **棄却**。
- 唯一残る候補: general-environment、intervention-abstraction、trajectory-local parameter criteriaを使い切った後に残る明示的symmetryを、latentと共同再符号化できないexternally anchored language channelが未知utterance form/composition/systemでも厳密に除去できるか。
- 上記候補: **未採用、preregistration候補のみ**。

採用には、残存同値類、非言語criterionの失敗、外部anchor、positive refinement theorem、anchor除去時のimpossibility、anti-lookup population grammar、unseen-form/composition/system評価、consistent estimatorまたはpopulation-only宣言、公開baseline再現、事前登録が必要。

新規architecture実験は認可しない。

## Current maximum bottleneck

**一つのcleanな131,072-frame公式recurrent runを完了・監査し、competentな外部公開baselineを得ること。** それまではR0.2 tuning、RQ-001 implementation、新規architectureを禁止する。

## Stage-transition rule

次stageは以下すべての完了後だけ提案できる。

1. 学習済み外部公開能力baseline 1件以上。
2. immutable-instance random/language-blind/state-only/shuffle controls。
3. canonical 3-seed prediction/artifact/leakage contract。
4. R0.2 online task success、typed next-state、実holdout。
5. R0.3 formal rejection。
6. 2026年一次文献まで閉じたnovelty matrix。
7. exactly one preregistered successor claim/theorem、counterexample、停止条件。

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

2026-07-25: **RESET-E022**。R0.2 Cycle 011のmatched typed comparison harness、C015のtrajectory-local parameter identifiabilityとexternally anchored symmetry-breaking境界、D018のsemantic shuffle payload監査を統合した。current headにR0.1完了run/artifactはなく、公開能力baseline 0件、`initial_reproduction_failure`、段階遷移禁止、高校生級未達を維持する。
