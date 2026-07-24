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
- RQ-001-T1 current formulation: **棄却**
- population-level restricted-auxiliary reformulation: **事前登録候補のみ・未採用**
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

Completed workflow run `30120620610` reproduced the official SILG `multi` recurrent training path for seeds `1,7,19` at 32,768 requested frames and saved 32,800-frame checkpoints. No pretrained language model was used.

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

Each method used 20 episodes per seed, 60 episodes total, with identical initial-instance fingerprint streams.

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

The first 131,072-frame attempt stopped because of a fixed 1,200-second reconstruction-harness subprocess timeout, not an official learner exception. The timeout now scales with requested frames and timeout failures preserve raw logs and hashes. The official model, loss, optimizer, seed, split and schema were unchanged.

At RESET-E018, head workflow run `30133481693` is still in the official recurrent training step. No unfinished capability, resource, trajectory or R0.2 value is incorporated. Repeated governance-only updates are not treated as new evidence; the latest completed capability evidence remains the 32,768-frame result.

## R0.2 Environment-first status

The old public-trajectory offline comparison is a negative diagnostic only:

- Environment-first action accuracy: `0.6840`
- End-to-end: `0.6907`
- State-only: `0.7240`
- Environment-first language-blind: `0.6840`
- Environment-first language-shuffle: `0.6840`

The source policy was ineligible: seed 1 train success `0/40`; seed 7 `0/40` with `97.42%` majority action; seed 19 `1/40`; all test sets `0/20`.

Classification: **`ineligible_failed-policy-trajectory_negative_diagnostic / not_R0.2_reproduction`**.

The current implementation is a continuous environment-first adaptation, not the official Gaddy & Klein default structured discrete-message and direct message-alignment baseline. Flat MSE over mixed typed state is not a valid formal next-state metric.

R0.2 remains blocked until every source-policy seed has majority-action share `<=0.90`, successful train episodes `>=5`, and at least two actions with `>=5%` support. Formal comparison requires typed transition loss, online task success, real entity/dynamics/language-form holdouts, matched parameter/data budget and identical-instance controls.

## Evaluation contract status

`evaluation_contract.py` and the SILG adapter audit:

- train/test utterance and entity/dynamics overlap;
- gold action, after-state, reward, done, post-treatment and completed-trajectory leakage;
- immutable prediction-side `instance_fingerprint`;
- complete `method × seed × domain × split × condition` prediction and artifact coverage;
- duplicate/missing predictions and duplicate method-seed runs;
- domain × seed × split × condition cells, paired gaps, exact McNemar and hierarchical bootstrap 95% CI;
- run and top-level aggregate recomputation;
- readable raw-log, model and immutable-data artifacts;
- full source/code pins and SHA-256 values;
- reported model bytes versus actual artifact size;
- finite model bytes, RSS, training wall time and CPU latency;
- canonical seeds `1,7,19`, `answer_leakage:false`, `pretrained_language_model:false`.

`target_label_shuffle` and `outcome_shuffle` require donor IDs/fingerprints, same-cell assignment, bijection, fixed-point-free derangement and no donor reuse. D014 has 15 passing regression tests.

Missing real target-label/outcome shuffle predictions or formal target-label inapplicability, immutable serialized test checksum and complete artifact joins. Formal classification remains **`initial_reproduction_failure`**.

## Prior-art and novelty boundary

Unknown-target and multi-node intervention recovery, score/general-environment CRL, subset-intervention causal abstraction, finite-sample recovery, environment-first instruction following, language-dynamics pretraining, auxiliary-variable/temporal/multi-view/hidden-regime nonlinear ICA, grouping-based and weakly supervised CRL, mechanism sparsity, mechanistic independence and multimodal shared-latent recovery are existing boundaries.

Broad claims that language is an auxiliary identifiability signal, shuffled language supplies contrastive negatives, unknown targets can be recovered, language and trajectory are two views of a shared latent, or utterance pair/group labels identify intervention semantics are not adopted as novelty.

## Research-question decision

SILG/RTFM does not define ground-truth latent intervention families, targets, mechanism operators or causal abstractions. Audited alternatives including J-CRe3, CausalTriplet, ACCESS, MIB and CausalPhys do not jointly provide episode-aligned raw language, interactive trajectories, independent mechanism changes, held-out mechanism ground truth and permutation-aware evaluation.

- **Gate L — continued, not passed:** test whether raw language adds external capability beyond state/action/history/environment identity after a competent public policy exists.
- **Gate I empirical track — rejected:** no joint-identification experiment and no researcher-authored target ontology on SILG.
- **RQ-001-N5 — rejected.**
- **RQ-001-T1 current form — rejected by C011.** On finite benchmark support, every observed utterance and every deterministic relation derived from it can be losslessly represented by a finite auxiliary index such as `U=index(L)`. Therefore “raw language exceeds every finite auxiliary representation” is not empirically demonstrable.
- **Only admissible reformulation — not adopted:** under an explicit population grammar and a restricted auxiliary class that cannot copy utterance identity, test whether compositional relations over unseen utterance forms refine a known intervention-induced causal abstraction beyond complete non-language trajectories.

Before that reformulation can be preregistered it requires a formal population language generator, explicit admissible auxiliary class, exact causal-model equivalence relation, a known residual abstraction, unseen-form positive and negative constructions, a proof sketch, falsification rule and lookup-preventing split. No architecture or synthetic benchmark is authorized before preregistration and public baseline reproduction.

## Current maximum bottleneck

**Complete and fully verify the active 131,072-frame official SILG recurrent run under the immutable matched protocol. Until policy competence exists, R0.2 tuning, new architecture and any RQ-001 implementation remain forbidden.**

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

2026-07-25: **RESET-E018**。C011のfinite-index collapseによりRQ-001-T1現行形式を棄却し、population grammarとrestricted auxiliary classを明示する再定式化だけを未採用の事前登録候補として残した。D014の厳格評価contractを維持し、head workflow run `30133481693`は131,072-frame公式recurrent学習中のため未完了値を採用しない。公開能力baseline 0件、R0継続、段階遷移禁止、高校生級未達を維持する。
