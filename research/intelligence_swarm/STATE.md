# Intelligence Swarm State

## Mission

長期目標は、1GB未満で弱いスマートフォンCPU上でも高速に動作し、日本語コミュニケーション・知識・推論を備える知能モデルである。ただし現在は新しい知能原理や機構族の発明を停止し、公開benchmark再現、評価資格、既存研究との境界、反証可能な中心命題の確立を優先する。

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
- R0.2 typed baseline/export/comparison/budget/holdout/manifest paths: **実装済み、qualified public dataで未実行**
- R0.3 empirical hidden intervention-target ablation: **正式棄却**
- RQ-001 broad/current formulation: **棄却**
- anchored joint language-equivalence / intervention-partition identification: **狭義化・未採用**
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

固定timeout、重複trigger、再起動問題は修正済みだが、current canonical headに検証済み完了artifactはない。未完了checkpoint、resource値、trajectory、能力値は採用しない。

次の唯一のR0.1作業は、stable workflow headからexactly one clean runを完了し、3 checkpoint、raw log、source/model/data/prediction hash、RSS、学習時間、CPU latency、同一instance controls、policy competence、action collapseを検証すること。

## R0.2 Environment-first status

Gaddy & Klein 2019と著者code commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f`を固定参照とする。

Canonical branchには、faithful typed baseline、typed SILG exporter、parameter-matched Environment-first / End-to-end / State-only comparison、matched-budget audit、holdout audit、immutable manifest joinがある。

Cycle 015で`build_r02_preregistered_holdout_manifest.py`を追加した。generator metadataと事前登録済みsignature集合だけからepisode-level manifestを構築し、action、reward、done、return、task success、prediction、action accuracy、next-state lossを入力として拒否する。seed `1/7/19`、一意episode key、非空signature、test metadata内の実在、3-seed coverage、train holdout禁止、metadata/spec/output SHA-256を必須化した。

ただしpinned RTFM generatorはまだ以下のsidecarを実出力していない。

- `entity_signature`
- `dynamics_signature`
- `language_form_signature`

したがってqualified three-seed source trajectory、実holdout、online task success、typed next-state prediction、action accuracy、matched comparisonは未実行。

Classification: **`preregistered_holdout_manifest_builder_implemented_generator_signature_sidecar_and_qualified_silg_execution_blocked`**。

## Evaluation contract status

- D015: 実SILG schemaへ適合。18件の回帰テスト。
- D016: immutable prediction-to-dataset join。
- D017: exact seed coverage `1,7,19`。
- D018: target-label/outcome shuffle donor provenance、same-cell、bijection、derangement、semantic no-op禁止。
- D019: entity/dynamics holdout leakageをcondition単位で監査。
- D020: episode-cluster hierarchical bootstrap、episode sign-flip、step/episode weighted gap、minimum cell gap。
- D021: prediction/data/raw-log/checkpoint/full commit/model bytes/RSS/training time/CPU latencyのcell binding。
- D022: `future_state`、`rollout_context`、`target_action`、`oracle_*`等のaliasによるsemantic model-input leakageをfail-closedで拒否。prospective allowlistは`utterance`、`state_before`、`history`、`valid_action_mask`。

D022の4テストはローカル成功したが、GitHub Actions完了は未確認。実R0 prediction/data/artifact bundleはD016〜D022を通過していないため、正式分類は **`initial_reproduction_failure`**。

## Prior-art and novelty boundary

既存境界にはunknown/uncoupled intervention CRL、general-environment CRL、subset-intervention causal abstraction、finite-sample CRL、trajectory-local parameter identifiability、auxiliary/temporal/multi-view/hidden-regime nonlinear ICA、grouping/weak supervision、mechanism sparsity、interactive grounding、environment-first、language-dynamics pretraining、WM3C、isolated causal effects of language、multimodal partial-sharing CRL、known observational grouping CRL、feature-conditioned generative intervention modelsを含む。

C018はknown observational groupingが言語なしのidentifiability routeであることを確認した。

C019はSchneider et al., ICML 2025のGenerative Intervention Modelsを監査した。観測されたperturbation featureから未知atomic intervention分布を学習し、未見perturbationの分布変化を予測する既存研究である。したがって、utterance embeddingをfeature-to-intervention modelへ渡すだけ、未知target確率を出すだけ、未見perturbationを予測するだけでは新規のlanguage-specific causal identificationにならない。

C019のcounterexampleは、language encoder、intervention generator、latent causal model、decoderを共同再符号化しても`p(X,Y,L)`を保存でき、完璧な予測でもlatent intervention-target partitionが一意とは限らないことを固定した。公式実装は一次記録と対象GitHub検索から特定できず、再現は開始していない。

## Research-question decision

- Gate L: **継続、未通過**
- Gate I empirical track / R0.3: **棄却**
- RQ-001-N5: **棄却**
- RQ-001 broad/current form: **棄却**
- unknown-target prediction、environment label recovery、parameter naming、non-zero language effect、partial shared-latent discovery、known groupingのlanguage再記述、feature-conditioned unknown-target predictionをlanguage-specific causal identificationとする案: **棄却**
- 唯一残る候補: feature-conditioned generative intervention modelsを含む既存identifiability route適用後に、externally fixed denotational anchorを持つpopulation language channelがraw utterance equivalenceと残存latent intervention-target partitionを共同同定できるか
- 上記候補: **未採用、preregistration候補のみ**

採用には、予測可能性とpartition identifiabilityの形式的分離、joint recoding後の残存同値類、outcome/target label/environment ID/completed trajectoryから独立なexternal anchor、一意性定理、anchor除去時のimpossibility theorem、GIM型baselineとの直接比較、unseen form/composition/target-combination/system split、dependency-pinned public baseline再現、exactly one preregistered claimが必要。

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

2026-07-25: **RESET-E026**。R0.2 Cycle 015のpreregistered manifest builder、C019のfeature-conditioned intervention boundary、D022のsemantic alias leakage auditを統合した。R0.1の能力証拠は増えておらず、公開能力baseline 0件、`initial_reproduction_failure`、段階遷移禁止、高校生級未達を維持する。
