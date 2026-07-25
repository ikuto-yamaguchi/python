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
- R0.2 typed full-method / typed exporter / matched comparison / matched-budget / holdout audit / immutable-manifest join: **実装済み、qualified public dataで未実行**
- R0.3 empirical hidden intervention-target ablation: **正式棄却**
- RQ-001 broad/current formulation: **棄却**
- joint grouping-and-partition identification beyond known observational grouping: **狭義化・未採用**
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

固定timeout、重複trigger、再起動問題は修正済みだが、current canonical headに検証済み完了artifactはない。pre-integration head `8325ff9f63e8d782209cccce232170adc95689bb`にはcombined CI statusが登録されていなかった。未完了checkpoint、resource値、trajectory、能力値は採用しない。

次の唯一のR0.1作業は、stable workflow headから1本だけ実行し、3 checkpoint、raw log、source/model/data/prediction hash、RSS、学習時間、CPU latency、同一instance controls、policy competence、action-collapseを検証すること。

## R0.2 Environment-first status

旧trajectory比較はnegative diagnosticのみ。source policyはseed 1でtrain success `0/40`、seed 7で`0/40`かつmajority action `97.42%`、seed 19で`1/40`、全test `0/20`で不適格。

Gaddy & Klein 2019と著者code commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f`を固定参照とする。

Canonical branchには以下がある。

- `gaddy_klein_typed_baseline.py`: language-free transition pretraining、20 categorical message variables × 30 symbols、straight-through Gumbel-Softmax、shared typed next-state/action decoder、LSTM language encoder、direct message matching `0.01`、decoder freezing、typed CE/BCE/MSE、resource/hash reporting。
- `export_silg_typed_policy_trajectories.py`: typed before/after fields、schema/cardinality、episode/seed/split/fingerprint provenance、dataset/schema SHA-256、unknown field fail-closed。
- `r02_typed_comparison.py`: Environment-first、parameter-matched End-to-end、State-onlyを同一typed dataset・seed・splitで比較。
- `audit_r02_matched_budget.py`: canonical seed、train/test、dataset hash、test prediction coverage、parameter bytes、transition-pretraining-only bytes、checkpoint hash、RSS、training time、CPU latency、action accuracy、typed next-state loss、equal row exposureをfail-closedで監査する。
- `audit_r02_holdout_assignments.py`: entity/dynamics/language-form holdoutの実在、seed `1,7,19`、condition-specific signature、train/test非重複、placeholder禁止をfail-closedで監査する。
- `attach_r02_holdout_manifest.py`: preregistered episode manifestを`domain/split/seed/episode_seed`でtyped trajectoryへ結合し、3 signature、Boolean holdout assignment、manifest/input/output SHA-256を保存する。duplicate/missing/extra/noncanonical/train-held-out entryを拒否する。

Cycle 012は、`N` train rows、environment epochs `E`、language epochs `L`に対し、Environment-firstを`N*E + N*L`、End-to-endとState-onlyを`N*(E+L)`として総row exposureを一致させる。Environment-firstとEnd-to-endのinference parameter bytesも完全一致させる。offline accuracyをonline task successの代用にしない。

Cycle 013は現exporterで`entity_holdout=false`、`dynamics_holdout=false`が全行に固定され、test全体が`language_holdout=true`であることを確認した。このdatasetではheld-out entity/dynamics/language-form transferを測定できない。

Cycle 014はimmutable holdout manifest joinを実装したが、pinned RTFM generator/configurationからprediction/outcome閲覧前に生成したvalid manifest自体は未作成である。qualified three-seed source trajectory、実holdout、online task success、typed next-state、action accuracy、matched comparisonは未実行。

Classification: **`immutable_holdout_join_implemented_manifest_generation_and_qualified_silg_execution_blocked`**。

## Evaluation contract status

- D015: 実SILG schemaへ適合。**18件の実行済み回帰テスト**。
- D016: 各`method × seed × domain × split × condition`のprediction-to-dataset immutable join。
- D017: 各`domain × split × condition` cellにseed `1,7,19`が正確に揃うこと。
- D018: target-label/outcome shuffleのdonor payloadと実適用payloadのhash一致、same-cell、bijection、derangement、self-shuffle禁止、semantic no-op禁止。
- D019: entity/dynamics holdoutを`domain × split × condition × kind`単位で監査し、同一domain train signatureとの重複、signature欠落、seed欠落/余分、train reference欠落を拒否する。in-distribution cellの期待されるtrain overlapはholdout leakageへ誤分類しない。
- D020: SILG stepを独立標本として扱わず、`episode_id`を必須化し、cellを再標本化した後にepisode全体を再標本化するhierarchical bootstrapとepisode-level sign-flip検定を保存する。step-weighted gap、episode-equal gap、minimum cell gap、paired episode/step countを併記する。
- D021: 各評価cellへprediction/data/raw-log/checkpointのpath/hash、full commit、model bytes、RSS、training time、CPU latencyを結合する。exact method/seed/cell coverage、shared dataset hash、stable checkpoint/commitを要求し、post-manifest mutation、condition間checkpoint差替え、method間resource/artifact tupleコピーを拒否する。

D018の4テストはローカル成功。D019/D020/D021のCI完了結果は未確認。実R0 prediction/data/artifact bundleはD016〜D021を通過していないため、正式分類は **`initial_reproduction_failure`**。

## Prior-art and novelty boundary

既存境界にはunknown/uncoupled intervention CRL、general-environment CRL、subset-intervention causal abstraction、finite-sample CRL、trajectory-local parameter identifiability、auxiliary/temporal/multi-view/hidden-regime nonlinear ICA、grouping/weak supervision、mechanism sparsity、mechanistic independence、interactive grounding、environment-first、language-dynamics pretraining、WM3C、isolated causal effects of language、multimodal partial-sharing CRL、known observational grouping CRLを含む。

C018はMorioka and Hyvärinen, ICML 2024と公式`hmorioka/GCaRL` commit `0020bfce34736d61d70ab8175f061d02951a7ed4`を監査した。既知の観測groupingは言語なしのidentifiability routeであり、言語がschema/sensor/object/time/field group metadataを予測・再記述するだけではgroupingとlatent intervention partitionの共同同定にならない。公式codeは存在するがexact dependency lockがなく、再現は主張しない。

## Research-question decision

- Gate L: **継続、未通過**。
- Gate I empirical track / R0.3: **棄却**。
- RQ-001-N5: **棄却**。
- RQ-001 broad/current form: **棄却**。
- Unknown target recovery、environment label recovery、parameter naming、non-zero language effect、partial shared-latent discovery、known groupingのlanguage再記述をlanguage-specific causal identificationとする案: **棄却**。
- 唯一残る候補: intervention/general-environment/trajectory-local/multimodal partial-sharing/known-grouping identifiability適用後に残るcausal abstractionについて、externally anchored population language channelが未知observational groupingと残存latent intervention-target partitionを共同同定できるか。
- 上記候補: **未採用、preregistration候補のみ**。

採用には、G-CaRL互換grouping適用後の残存同値類、言語情報がschema/state/historyから復元不能である証明、grouping/latentと共同再符号化不能なanchor、joint grouping-and-partition theorem、anchor除去時のimpossibility theorem、direct grouping metadata/G-CaRL比較、unseen-form/composition/system評価、dependency-pinned public baseline再現、事前登録が必要。

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

2026-07-25: **RESET-E025**。R0.2 Cycle 014のimmutable holdout manifest join、C018のknown observational grouping境界、D021のruntime/resource/artifact cell bindingを統合した。current headにR0.1完了artifactはなく、公開能力baseline 0件、`initial_reproduction_failure`、段階遷移禁止、高校生級未達を維持する。
