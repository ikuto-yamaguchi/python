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
- R0.2 typed full-method path: **実装済み・dataset/online評価でblocked**
- R0.3 empirical intervention-target ablation: **正式棄却**
- RQ-001 broad/current formulation: **棄却**
- residual-abstraction refinement reformulation: **未採用**
- J-CRe3日本語外部監査: **未再現**

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

Correct was 1/60 and Random was 4/60. This demonstrates insufficient policy competence, not that language is unnecessary.

Classification: **`matched_fixed_episode_32768_frame_staged_training_not_public_capability_reproduction`**.

### Current staged run

The first 131,072-frame attempt stopped because of a fixed reconstruction-harness timeout, not an official learner exception. Timeout handling now scales with frames and preserves logs and hashes.

At RESET-E020, workflow run `30138560445` has completed checkout, Python setup, host recording, pinned-source installation and canonical random/schema probing, and remains in the official recurrent 131,072-frame training step. No unfinished capability, resource, checkpoint, trajectory or R0.2 value is incorporated.

## R0.2 Environment-first status

The old public-trajectory offline comparison is a negative diagnostic only:

- Environment-first action accuracy: `0.6840`
- End-to-end: `0.6907`
- State-only: `0.7240`
- Environment-first language-blind: `0.6840`
- Environment-first language-shuffle: `0.6840`

The source policy was ineligible: seed 1 train success `0/40`; seed 7 `0/40` with `97.42%` majority action; seed 19 `1/40`; all test sets `0/20`.

Gaddy & Klein 2019 and authors' code commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f` remain the fixed method reference.

Cycle 009 adds `gaddy_klein_typed_baseline.py` with:

- language-free transition pretraining;
- 20 categorical message variables × 30 symbols;
- straight-through Gumbel-Softmax;
- shared typed next-state/action decoder;
- LSTM language encoder;
- direct environment/language message matching, weight `0.01`;
- pretrained decoder frozen during language training by default;
- categorical CE, binary BCE and continuous MSE;
- seed `1,7,19`, episode-disjointness, dataset hash, parameter bytes, wall time and RSS reporting.

The entry point rejects flattened `state_before/state_after` rows and requires `state_before_fields`, `state_after_fields` and `state_schema`. It has not been executed because the active R0.1 run is unfinished and the current exporter does not preserve typed field boundaries.

R0.2 classification: **`typed_discrete_message_method_path_implemented_dataset_and_online_evaluation_blocked`**.

No R0.2 result is accepted until competent non-collapsed source trajectories, typed export, parameter/topology-matched end-to-end and state-only controls, real entity/dynamics/language-form holdouts, online task success, action accuracy, typed next-state metrics, CPU latency and complete artifacts exist.

## Evaluation contract status

D015 directly adapts concrete SILG exporter rows and has **18 executed passing regression tests**. It audits prospective-only input construction, utterance/entity/dynamics overlap, gold/post-treatment/completed-trajectory leakage, immutable fingerprints, full `method × seed × domain × split × condition` coverage, paired statistics, McNemar, hierarchical bootstrap CI, readable artifacts, full hashes, resources and canonical seeds.

D016 adds `audit_evaluation_bundle.py`, requiring for every run:

- `prediction_path` and full `prediction_sha256`;
- readable prediction JSONL;
- manifest/prediction method agreement;
- unique prediction instance IDs;
- exact prediction/dataset instance-set equality;
- per-row fingerprint agreement;
- one dataset hash shared across all methods in a cell;
- stable model SHA and code commit for a method/seed across split and condition cells.

D016 regression tests are committed but not yet executed by GitHub Actions, so no new passing-test count is claimed. Existing SILG evidence lacks a complete immutable six-method prediction artifact join.

Formal classification remains **`initial_reproduction_failure`**.

## Prior-art and novelty boundary

Existing boundaries include unknown/uncoupled multi-node intervention recovery, score/general-environment CRL, subset-intervention causal abstraction, finite-sample CRL, environment-first instruction following, language-dynamics pretraining, auxiliary/temporal/multi-view/hidden-regime nonlinear ICA, grouping and weak supervision, mechanism sparsity, mechanistic independence, multimodal shared-latent recovery and WM3C language-controlled block identification.

C013 adds Lee, Jin and Aragam 2026. Under a strongly separating intervention design in their linear setting, unknown multi-node targets, latent graph, representation and decoder are recoverable from non-language data with `O(log d)` environments and finite-sample guarantees. Therefore unknown-target recovery is not an admissible language novelty claim.

## Research-question decision

- **Gate L — continued, not passed:** evaluate whether raw language adds external capability only after a competent public policy exists.
- **Gate I empirical track / R0.3 — rejected:** no joint-identification experiment and no researcher-authored target ontology on SILG.
- **RQ-001-N5 — rejected.**
- **RQ-001 broad/current form — rejected.**
- **Unknown-target recovery as language contribution — rejected.**
- **Only admissible narrowed question — not adopted:** under a specified population grammar, restricted non-lookup language-to-dynamics class and a known non-strongly-separating intervention family, determine whether raw utterances supply missing separating relations that strictly refine its residual causal abstraction on unseen forms and intervention compositions.

Adoption requires an explicit deficient intervention design and residual abstraction, anti-lookup grammar, restrictions against arbitrary factor merging/splitting, a positive refinement theorem, matched impossibility result, unseen-form/tuple/target tests, finite-sample or consistent estimation, and comparison with logarithmic-environment unknown-target CRL, causal-abstraction, WM3C and auxiliary/multi-view baselines.

No implementation is authorized before public baseline reproduction and preregistration.

## Current maximum bottleneck

**Complete and fully verify workflow run `30138560445` under the immutable matched protocol. Until policy competence exists, R0.2 tuning, new architecture and any RQ-001 implementation remain forbidden.**

## Stage-transition rule

A next stage may be proposed only after all are complete:

1. at least one learned external public capability baseline;
2. immutable-instance random/language-blind/state-only/shuffle controls;
3. canonical three-seed artifact and leakage contract;
4. R0.2 online task success, typed next-state and real holdouts;
5. formal R0.3 empirical rejection in governance;
6. novelty matrix through relevant 2026 primary work;
7. exactly one preregistered claim/theorem, counterexamples and stopping conditions.

## Canonical branch policy

All work accumulates only on `research/intelligence-swarm-reconstruction-001`. Existing stacked drafts remain negative-results archives and are not experiment bases.

## Current status

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 完成: **false**

## Last integration

2026-07-25: **RESET-E020**。C013で有限標本・少数環境のunknown-target CRLを統合し、unknown-target回復を言語の新規貢献候補から除外した。R0.2 Cycle 009でtyped structured-message full-method pathを実装したが、typed datasetとonline評価がなく未実行・未認定。D016でprediction artifactとimmutable datasetの厳密joinを追加したが、新テストは未実行のためD015の18件を最新の確認済み件数とする。workflow run `30138560445`は131,072-frame公式recurrent学習中であり未完了値を採用しない。公開能力baseline 0件、段階遷移禁止、高校生級未達を維持する。
