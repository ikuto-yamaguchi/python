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
- 131,072-frame staged reproduction: **完了artifact未取得**
- 学習済み公開能力baseline再現: **0件**
- R0.2正式再現: **0件**
- R0.2 typed full-method path: **実装済み**
- R0.2 typed SILG exporter path: **実装済み・未実行**
- R0.3 empirical intervention-target ablation: **正式棄却**
- RQ-001 broad/current formulation: **棄却**
- language-added residual-abstraction refinement: **狭義化・未採用**
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

### 131,072-frame status

The initial attempt stopped because of a fixed reconstruction-harness timeout. Timeout handling was corrected. Subsequent long runs were repeatedly restarted by branch/PR triggers; workflow concurrency and trigger scope were corrected so unrelated commits no longer restart the expensive job.

At RESET-E021, no completed 131,072-frame artifact is verified at the current canonical head. No unfinished checkpoint, resource value, trajectory or capability result is incorporated. The next authorized action is one clean manual or path-triggered run followed by artifact verification.

## R0.2 Environment-first status

The old public-trajectory offline comparison is a negative diagnostic only:

- Environment-first action accuracy: `0.6840`
- End-to-end: `0.6907`
- State-only: `0.7240`
- Environment-first language-blind: `0.6840`
- Environment-first language-shuffle: `0.6840`

The source policy was ineligible: seed 1 train success `0/40`; seed 7 `0/40` with `97.42%` majority action; seed 19 `1/40`; all test sets `0/20`.

Gaddy & Klein 2019 and authors' code commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f` remain the fixed method reference.

The faithful path now contains:

- `gaddy_klein_typed_baseline.py`: language-free transition pretraining, 20 categorical message variables × 30 symbols, straight-through Gumbel-Softmax, shared typed next-state/action decoder, LSTM language encoder, direct message matching (`0.01`), decoder freezing, typed losses and resource/hash reporting;
- `export_silg_typed_policy_trajectories.py`: preserves `state_before_fields`, `state_after_fields`, `state_schema`, categorical cardinalities, episode/seed/split/fingerprint provenance, dataset SHA-256 and schema SHA-256.

Typed export rules currently classify `name` and `inv` as categorical, `name_len` and `inv_len` as bounded categorical, `valid` as binary, and `rel_pos`/`pos` as continuous. Text fields, reward, done and post-treatment outcomes are excluded from environment state. Unknown fields/cardinalities fail closed.

Neither path has a qualified three-seed execution because no competent source-policy artifact exists. R0.2 classification remains **`typed_discrete_message_and_typed_export_paths_implemented_execution_blocked`**.

No R0.2 result is accepted until competent non-collapsed source trajectories, typed export, parameter/topology-matched End-to-end and State-only controls, equal data/steps/splits, real entity/dynamics/language-form holdouts, online task success, action accuracy, typed next-state metrics, CPU latency and complete artifacts exist.

## Evaluation contract status

D015 directly adapts concrete SILG exporter rows and has **18 executed passing regression tests**.

D016 adds an immutable prediction-to-dataset join for every `method × seed × domain × split × condition` run: prediction path/hash, readable JSONL, method identity, unique instance IDs, exact dataset/prediction instance-set equality, fingerprint agreement, shared dataset hash and stable model/code identity.

D017 adds fail-closed dataset cell coverage. Every `domain × split × condition` evaluation cell must contain exactly canonical seeds `1,7,19`; missing, extra or noncanonical seeds are rejected and recorded with the dataset SHA-256. A separate lightweight evaluation-contract workflow was added so these tests do not restart the long SILG training job.

D016/D017 completion results are not yet verified at the canonical head, so the confirmed passing-test count remains 18. Existing evidence lacks a complete immutable six-method prediction artifact join.

Formal classification remains **`initial_reproduction_failure`**.

## Prior-art and novelty boundary

Existing boundaries include unknown/uncoupled multi-node intervention recovery, score/general-environment CRL, subset-intervention causal abstraction, finite-sample CRL, environment-first instruction following, language-dynamics pretraining, auxiliary/temporal/multi-view/hidden-regime nonlinear ICA, grouping and weak supervision, mechanism sparsity, mechanistic independence, multimodal shared-latent recovery and WM3C language-controlled block identification.

C013 excludes unknown-target recovery as a language novelty claim under strongly separating intervention designs.

C014 further excludes the claim that language is required merely because targets are unknown, environment labels are incomplete, dynamics are nonlinear or observation mixing is nonparametric. General-environment CRL already supplies identifiability under sufficient mechanism changes, while subset-intervention work characterizes the residual causal abstraction when interventions are insufficient.

If `L ⟂ M | X,E`, equivalently `I(M;L | X,E)=0`, language cannot refine the causal-model equivalence class left by non-language observations. Language-shuffle degradation, environment classification, semantic naming or finite-sample prediction gains alone do not establish identifiability.

## Research-question decision

- **Gate L — continued, not passed:** evaluate whether raw language adds external capability only after a competent public policy exists.
- **Gate I empirical track / R0.3 — rejected:** no joint-identification experiment and no researcher-authored target ontology on SILG.
- **RQ-001-N5 — rejected.**
- **RQ-001 broad/current form — rejected.**
- **Unknown-target recovery as language contribution — rejected.**
- **Only admissible narrowed question — not adopted:** after exhausting general-environment non-language statistics, determine whether raw language supplies an independent separating relation that strictly refines a formally specified residual causal abstraction on unseen utterance forms and intervention compositions.

Adoption requires a deficient intervention design and exact residual equivalence class, proof that general-environment sufficient-change conditions fail, `I(M;L|X,E)>0`, anti-lookup grammar, restrictions against arbitrary factor re-encoding, a positive refinement theorem, matched impossibility theorem without language separation, unseen-form/tuple/target tests, finite-sample or consistent estimation and direct prior-art comparisons.

No implementation is authorized before public baseline reproduction and preregistration.

## Current maximum bottleneck

**Produce one clean, completed 131,072-frame official recurrent run at the stable workflow head, verify its artifacts under the immutable matched protocol, and test policy competence. Until then, R0.2 tuning, new architecture and RQ-001 implementation remain forbidden.**

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

2026-07-25: **RESET-E021**。R0.2 Cycle 010のtyped SILG exporter、C014のgeneral-environment conditional-sufficiency境界、D017の`domain × split × condition`別canonical three-seed監査を統合した。131,072-frameについてcurrent headで検証済み完了artifactはなく、古い実行中表記を撤回した。公開能力baseline 0件、`initial_reproduction_failure`、段階遷移禁止、高校生級未達を維持する。
