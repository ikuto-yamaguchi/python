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
- narrowed population-grammar reformulation: **未採用**
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

At RESET-E019, workflow run `30136732061` has completed source installation and random/schema probing and remains in the official recurrent 131,072-frame training step. No unfinished capability, resource, checkpoint, trajectory, or R0.2 value is incorporated.

## R0.2 Environment-first status

The old public-trajectory offline comparison is a negative diagnostic only:

- Environment-first action accuracy: `0.6840`
- End-to-end: `0.6907`
- State-only: `0.7240`
- Environment-first language-blind: `0.6840`
- Environment-first language-shuffle: `0.6840`

The source policy was ineligible: seed 1 train success `0/40`; seed 7 `0/40` with `97.42%` majority action; seed 19 `1/40`; all test sets `0/20`.

Classification: **`ineligible_failed-policy-trajectory_negative_diagnostic / not_R0.2_reproduction`**.

Gaddy & Klein 2019 and authors' code commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f` are now the fixed method reference. The official full method uses language-free `E(s,s')->m`, reused `D(s,m)->s'`, a structured discrete message, direct environment/language message matching, an LSTM language module, and a pretrained decoder frozen by default.

The current SILG adaptation remains non-faithful: continuous width-48 message, no direct matching loss, GRU, flat MSE over mixed typed fields, no online task success, and no verified entity/dynamics/language-form holdouts.

`audit_r02_gaddy_klein_fidelity.py` fails closed unless canonical seeds, disjoint episodes, typed schema/losses, real holdouts, non-collapsed successful source trajectories, official method-contract fields, matched inference topology, complete resource reporting, and `pretrained_language_model:false` are present.

R0.2 classification: **`official_method_transfer_audited_current_dataset_blocked`**. No tuning is authorized until R0.1 source-policy competence passes.

## Evaluation contract status

D015 adapts the contract directly to the concrete SILG exporter schema:

- `text_tokens -> utterance`;
- `action -> gold_action`;
- `state_after -> gold_state_after`;
- prospective-only default `model_input`;
- reward, done, outcome, action label and after-state excluded from model input;
- shared train/test `episode_id`, `episode_seed`, or `observation_fingerprint` rejected;
- wholly missing required methods reported in coverage.

The contract also audits:

- train/test utterance and entity/dynamics overlap;
- gold action, after-state, reward, done, post-treatment and completed-trajectory leakage;
- immutable prediction-side `instance_fingerprint`;
- complete `method × seed × domain × split × condition` prediction and artifact coverage;
- domain × seed × split × condition cells, paired gaps, exact McNemar and hierarchical bootstrap 95% CI;
- readable raw-log, model and immutable-data artifacts;
- full source/code pins and SHA-256 values;
- exact model bytes, finite RSS, wall time and CPU latency;
- canonical seeds `1,7,19`, `answer_leakage:false`, `pretrained_language_model:false`;
- shuffle donor existence, same-cell bijection, fixed-point-free derangement and no reuse.

D015 has **18 passing regression tests**. Missing real target-label/outcome shuffle predictions or formal target-label inapplicability, immutable serialized test checksum, complete artifact joins, and a competent public baseline remain. Formal classification remains **`initial_reproduction_failure`**.

## Prior-art and novelty boundary

Unknown-target and multi-node intervention recovery, score/general-environment CRL, subset-intervention causal abstraction, finite-sample recovery, environment-first instruction following, language-dynamics pretraining, auxiliary-variable/temporal/multi-view/hidden-regime nonlinear ICA, grouping-based and weakly supervised CRL, mechanism sparsity, mechanistic independence, multimodal shared-latent recovery, and WM3C language-controlled block identification are existing boundaries.

WM3C already covers composable language-conditioned latent dynamics and block-wise identifiability when language components and target blocks are supplied. These broad claims are not novel.

## Research-question decision

- **Gate L — continued, not passed:** test whether raw language adds external capability beyond state/action/history/environment identity after a competent public policy exists.
- **Gate I empirical track — rejected:** no joint-identification experiment and no researcher-authored target ontology on SILG.
- **RQ-001-N5 — rejected.**
- **RQ-001-T1 current form — rejected by finite-index collapse.**
- **C012 re-encoding result:** without an explicit population grammar and restricted language-to-dynamics mechanisms, hidden language factors can be bijectively merged or reversibly split while preserving the observable distribution; even the number and size of target blocks are not jointly identifiable.
- **Only admissible narrowed question — not adopted:** under a specified population grammar and a restricted non-lookup language-to-dynamics class, determine whether raw utterances jointly identify a nontrivial utterance factorization and a refinement of a known intervention-induced causal abstraction when neither language components nor target blocks are supplied.

Preregistration must rule out utterance-ID lookup and arbitrary splitting/merging, define the residual abstraction, supply positive and impossibility results, include unseen-form/tuple/target splits, and compare directly with WM3C and auxiliary/multi-view CRL. No implementation is authorized before public baseline reproduction and preregistration.

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

2026-07-25: **RESET-E019**。C012でWM3C重複境界とraw-language factor再符号化による共同識別不能性を統合した。R0.2はGaddy & Klein公式full methodとの差をfail-closed監査へ固定した。D015で実SILG exporter schema、episode/seed/observation identity leakage、18 regression testsを統合した。workflow run `30136732061`は131,072-frame公式recurrent学習中であり未完了値を採用しない。公開能力baseline 0件、段階遷移禁止、高校生級未達を維持する。
