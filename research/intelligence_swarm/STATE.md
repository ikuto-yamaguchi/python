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
- R0.2 typed baseline/export/comparison/budget/holdout/manifest paths: **実装済み**
- RTFM generator-side signature export: **実装・workflow接続済み**
- R0.2 online SILG evaluator: **実装済み、workflow未接続・未実行**
- R0.3 empirical hidden intervention-target ablation: **正式棄却**
- RQ-001 broad/current formulation: **棄却**
- language-supplied missing separation beyond finite-sample unknown-target CRL: **未採用**
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

Current canonical headに131,072-frameの検証済み完了run、artifact、checkpoint、能力値はない。workflow編集、trigger更新、run request、監査文書は能力進捗に数えない。headのcombined statusも未登録であり、実行開始・完了を推測しない。

## R0.2 Environment-first status

Gaddy & Klein 2019と著者code commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f`を固定参照とする。

実装済み経路:

- `gaddy_klein_typed_baseline.py`: language-free transition pretraining後にinstruction followingへ接続
- `r02_typed_comparison.py`: Environment-first / parameter-matched End-to-end / State-only
- `export_rtfm_generator_signatures.py`: rollout outcomeを参照せずgenerator内部からepisode signatureを出力
- `evaluate_r02_online_silg.py`: 同一seed・同一初期instance stream上で3手法のonline task successを測定
- model/checkpoint bytes、RSS、training time、CPU inference、raw log、checksum保存経路

RTFM S1で公式に分割されるのはgenerator assignmentに基づく**dynamics**である。entity ontologyとlanguage generation familyはtrain/testで分離されないため、S1単独ではreal entity holdoutとlanguage-form holdoutを認定しない。

未完了点:

1. generator signature sidecarはworkflowで出力されるが、typed trajectoryへimmutable joinされていない。
2. holdout auditorは現在raw typed trajectoryを読むため、sidecar由来のreal dynamics holdoutをまだ正式評価できない。
3. online evaluatorは実装済みだがcanonical workflowから呼ばれていない。
4. competentなR0.1 source policy trajectoryがない。
5. task success、typed next-state、action accuracy、real dynamics transferの3-seed結果がない。

Classification: **`generator_signature_and_online_evaluator_implemented_but_join_execution_and_qualified_source_policy_absent`**。

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
- D024: immutable実bundle結合後にdataset contract、semantic leakage、shuffle provenance、prediction coverage、paired/cluster statisticsを一括実行
- D025: `domain × split × condition`の**観測済み疎topology**を固定し、存在しない直積cellを要求せず、全method・seedで同じtopologyを必須化

D025は正当な疎い評価設計のfalse failureを除去するが、methodまたはseedだけのcell欠落は引き続き拒否する。実R0 prediction/data/resource bundleはD016〜D025をまだ通過していない。

Formal classification: **`initial_reproduction_failure`**。

## Prior-art and RQ boundary

C021はLee, Jin, and Aragam 2026 `Beyond identifiability: Learning causal representations with few environments and finite samples`を監査した。未知full-rank linear decoder、未知linear SEM、未知multi-node targetsの下で、strongly separating intervention familyによりgraph、representation、decoder、targetを有限標本で回復し、必要環境数はlatent次元に対して対数オーダーである。

したがって、未知multi-node target回復、少数環境、target namingを言語固有の新規性とする案は棄却する。言語が既に回復可能なincidence signatureの関数なら、interactive responseやparaphraseを加えても因果同値類を縮小しない。

2026年の隣接一次研究も境界確認した。

- LeGIT: LLM priorでonline causal discoveryの介入target選択を支援する。latent representationとraw-language equivalenceのjoint identificationではない。
- Sequential Causal Discovery with Noisy Language Model Priors: noisy LM expert knowledgeをPAG学習へ統合する。latent intervention partitionの同定定理ではない。
- Coarsening Causal DAG Models: unknown-target interventional dataからpartition-refinement lattice上でcausal abstractionを学ぶ。languageなしで得られるcoarsening/refinement境界を先に適用すべき追加prior artである。

唯一残る候補は、最強のnon-language estimatorが明示的に残すequivalence classに対して、environment identity、incidence、observation、action、outcome、completed trajectoryから復元不能なexternally anchored language contrastが不足するseparationを供給し、raw utterance equivalenceとrefined intervention-target partitionを有限標本で共同同定できるか、である。

この候補は**未採用**。採用には、残存countermodel、positive-measure language-law separation、anti-recoding anchor、strict equivalence-class reduction theorem、anchor除去時のimpossibility theorem、finite-sample estimator、non-language separating/non-separating比較、unseen form/composition/target/system split、公開baseline再現、exactly one preregistered claimが必要。

新規architecture実験は認可しない。

## Current maximum bottleneck

**一つのcleanな131,072-frame公式recurrent runを完了・監査し、competentな外部公開baselineを得ること。**

それまではR0.2 tuning、RQ-001 implementation、新規architectureを禁止する。

## Stage-transition rule

次stageは以下すべての完了後だけ提案できる。

1. 学習済み外部公開能力baseline 1件以上
2. immutable-instance random/language-blind/state-only/shuffle controls
3. canonical 3-seed prediction/artifact/leakage contract
4. R0.2 online task success、typed next-state、実dynamics holdout、およびentity/language-form transferを測れる別の公開splitまたはformal inapplicability boundary
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

2026-07-25: **RESET-E029**。R0.1能力証拠は増加なし。R0.2 generator-side dynamics signatureとonline evaluatorの実装を統合したが、immutable join・workflow実行・competent source policyは未完。D025 sparse-topology correction、C021 finite-sample unknown-target境界、2026年隣接prior artを反映した。公開能力baseline 0件、R0.2正式再現 0件、RQ未採用、`initial_reproduction_failure`、段階遷移禁止、高校生級未達を維持する。
