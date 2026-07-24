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
- 公開学習経路再現: **1件（32,768-frame staged budget、3 seed）**
- 固定初期instance matched評価経路: **1件**
- 131,072-frame staged run: **実行中・未統合**
- 学習済み公開能力baseline再現: **0件**
- R0.2正式再現: **0件**
- R0.3 empirical intervention-target ablation: **正式棄却**
- RQ-001-T1 theory-only candidate: **再狭義化・未採用**
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

補正済みworkflow run `30120620610`は全工程を完走した。公式SILG `multi` recurrentをseed `1,7,19`で各32,768 frames要求し、checkpointは各32,800 framesで保存された。pretrained language modelは使用していない。

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

各method・seedで20 episode、methodあたり60 episodeを評価し、全methodの初期instance fingerprint streamは一致した。

| Method | Win rate | Mean return | Mean episode length | CPU inference |
|---|---:|---:|---:|---:|
| Correct recurrent | `0.0167` | `-1.8827` | `46.80` | `7.229 ms/step` |
| Random valid action | `0.0667` | `-1.1513` | `15.23` | `0.0081 ms/step` |
| Language-blind | `0.0167` | `-2.0417` | `54.75` | `4.424 ms/step` |
| State-only | `0.0167` | `-2.1963` | `62.48` | `4.103 ms/step` |
| Language-shuffle | `0.0167` | `-1.9347` | `49.40` | `7.252 ms/step` |

Correctは1/60勝、Randomは4/60勝だった。これは言語不要の証拠ではなく、policy competence不足である。

Classification: **`matched_fixed_episode_32768_frame_staged_training_not_public_capability_reproduction`**。

### Current staged run

忠実な条件を維持したまま学習budgetだけを`131,072 frames/seed`へ増やしたworkflow run `30127967677`は、RESET-E016統合時点で **`in_progress`** である。未完了runの能力値、資源値、trajectory資格、R0.2結果はSTATEへ取り込まない。

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

現行実装はGaddy & Klein 2019の二段階順序を持つが、公式defaultのstructured discrete messageと直接message-alignment objectiveを持たないため、**`continuous_environment_first_adaptation_not_gaddy_klein_default_reproduction`** とする。flatten済みmixed-type stateへの一律MSEは正式next-state指標として無効である。

R0.2を再開する前に、各seedで次を満たす。

- majority-action share `<= 0.90`
- successful train episode `>= 5`
- 5%以上のsupportを持つaction `>= 2`

正式比較ではtyped observation-field transition loss、online task success、実entity/dynamics/language-form holdout、matched parameter/data budget、同一instance controlsを必須とする。source policyがこの資格を満たすまでEnvironment-firstを調整しない。

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
- top-level集計値とrun valuesの再計算一致
- independently readable raw-log、model、immutable-data files
- full 40-hex source/code pins
- full 64-hex checkpoint/model/data/log SHA-256
- reported `model_bytes`と実model file sizeの一致
- model bytes、RSS、training wall time、CPU latencyの有限・非負監査
- canonical seeds `1,7,19`
- `answer_leakage: false`、`pretrained_language_model: false`の明示

D013から`target_label_shuffle`と`outcome_shuffle`の各prediction rowに、donor `control_source_instance_id`と`control_source_fingerprint`を必須化した。donor存在、self-donor禁止、同一seed/domain/split/condition、fingerprint一致、cell内全単射、固定点なしderangement、donor不正再利用を自動検査し、`shuffle_assignment_audit`を保存する。

**13件の回帰テストは成功した。** 実target-label/outcome shuffle predictionとdonor provenance、target labelが非oracleで定義不能な場合の正式inapplicability記録、immutable serialized test dataset checksum、全cellのraw-log/model/data artifact joinが不足するため、現在の正式分類は **`initial_reproduction_failure`**。

## Prior-art and novelty boundary

未知介入下のnonparametric CRL、unknown multi-node intervention、score-based CRL、subset-intervention causal abstraction、finite-sample few-environment recovery、environment-first instruction following、language-dynamics pretraining、multimodal shared-latent recovery、perturbation-to-intervention modeling、causal sufficiency/necessity、causal-world-modelと言語interfaceは単独では既存範囲である。

さらに、raw languageをauxiliary variableとして用いる識別、正しいtrajectory-language pairとshuffle pairの対比、完全historyを使うtemporal nonlinear ICA、multimodal partial-sharing identifiability、generic symmetry/invariance breaking、multi-view nonlinear ICA、hidden-regime nonlinear ICA、mechanistic-independence、heterogeneous measurement-model identifiabilityも既存境界として除外する。

広い「言語とtrajectoryから未知因果変数を発見する」「言語が補助変数として識別性を与える」「言語とtrajectoryを複数viewとして共有latentを回復する」は中心命題として採用しない。

## Research-question decision

SILG/RTFMはground-truth latent intervention family、target、mechanism pre/post operator、causal abstractionを定義しない。J-CRe3、CausalTriplet、ACCESS、MIB、CausalPhysを含む監査済み候補も、episode-aligned raw language、interactive trajectory、独立mechanism change、held-out mechanism ground truth、permutation-aware評価を同時に満たさない。

- **Gate L — 継続・未達:** competent public policyとmatched controlsで、raw languageがstate/action/history/environment identityを超える外部能力を持つか測る。
- **Gate I empirical track — 正式棄却:** 現在の公開benchmark制約下で共同同定実験を開始しない。研究者がtarget/mechanism ontologyを後付けすることも禁止する。
- **RQ-001-N5 — 棄却:** empirical joint-identification claimとして閉じる。
- **RQ-001-T1 — 再狭義化、未採用:** 完全な非言語trajectoryを条件とし、言語を単なるauxiliary/environment/intervention indexとして使う全説明を同値類として除外した後でも、raw utterance間の構成的関係がtrajectory-only causal equivalence classを厳密に細分化できるかを問う。

C009ではnegative constructionが成立した。可逆変換で結ばれた二つの潜在表現が同一の完全pre/post trajectoryを生成しながら、異なる介入partitionとtarget cardinalityを持てる。言語が環境・介入indexの関数なら追加情報を与えず、この同値性を破れない。

T1採用に残る必須条件:

1. formal observation modelとtrajectory-only equivalence relation
2. auxiliary/environment/intervention-index情報によるquotient
3. domain labelへ還元不能なcompositional language relation
4. correct languageのみでのstrict refinement
5. 独立介入効果による意味裏付け
6. 既存ICA/CRL/measurement-identifiabilityと異なる保証
7. **nontrivial positive construction**
8. sufficient-condition theorem
9. exactly one中心命題の事前登録と停止条件

negative constructionは存在するが、positive constructionと定理は存在しない。

## Current maximum bottleneck

**workflow run `30127967677`の131,072-frame公式SILG recurrentを完了・完全検証し、同じimmutable matched protocolでpolicy competenceが成立するか確認する。成立するまでR0.2調整、新規architecture、T1実装を禁止する。**

## Stage-transition rule

次stageを提案できるのは全て満たした場合だけ。

1. 学習済み外部公開能力baselineを少なくとも1件再現
2. immutable公開instance上のrandom / language-blind / state-only / shuffle対照
3. canonical 3 seedと完全artifact/leakage contract
4. R0.2のonline task success、typed next-state、実holdout付き比較
5. R0.3 empirical trackの正式棄却をgovernanceへ統合
6. 2026年までのnovelty matrix
7. exactly one中心命題、主要指標または定理、反例、停止条件の事前登録

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

2026-07-25: **RESET-E016**。C009の非識別反例、D013のshuffle donor provenance contract、131,072-frame staged workflowの実行中状態を統合した。未完了runの値は採用せず、最新の完了済み能力証拠は32,768-frame結果のままである。公開能力baselineは0件、R0継続、段階遷移禁止を維持した。
