# Intelligence Swarm State

## Mission

1GB未満・弱いスマートフォンCPUで実行可能な知能モデルを目標とし、生の日本語と環境相互作用から対象・状態・操作・因果構造を獲得する原理を研究する。

## Current stage

- Stage: **R0 Research Reconstruction — public capability reproduction and benchmark qualification**
- Semantic Identity Gate G1: **未達**
- Operation/Goal Gate G2: **未達**
- Formal memory eligibility: **未達**
- 学術的新規性: **未確立**
- 公開環境control再現: **1件**
- 公開学習経路再現: **1件**
- 固定初期instance matched評価経路: **1件（engineering smoke）**
- 学習済み公開能力baseline再現: **0件**
- R0.2公開trajectory offline診断: **1件（negative diagnostic、正式再現ではない）**
- 査読可能な中心命題: **未確立**
- Active mechanism family: **なし**
- AF-001〜AF-014: **PAUSED**
- A〜Dの新規toy仮説生成: **停止**
- Memory/consolidation最適化: **停止継続**

## Why the program was reset

過去サイクルは、合成opaque-token環境上で候補機構を変更し、Correctとshuffle/randomの差が出ないことを反復確認した。評価漏れや不可能条件の切り分けはあったが、公開benchmark上の既存baseline再現、同一benchmark・split・instanceでの累積比較、一次研究との新規性監査、反証可能な単一中心命題、一つのcanonical実装が欠けていた。したがって過去成果を新しい知能原理または基礎研究上の発見とは扱わない。

## R0 gates

1. **R0.1 SILG capability reproduction** — paper-scaleまたは収束確認済みrecurrent policyと全controlを固定公開test instanceで比較し、reference scoreとの許容差を宣言する。
2. **R0.2 Environment-first reproduction** — 既存environment-first / language-dynamics baselineとend-to-endを同一データ・parameter budgetで比較し、online task successと実holdout transferを測る。
3. **R0.3 Intervention-target ablation** — Gate L陽性かつ公開benchmarkが非自明な介入partitionを定義する場合だけ実行する。
4. **R0.4 Japanese realism audit** — J-CRe3を日本語参照接地の外部監査として使用し、SILG性能と混合しない。
5. **Resource / reproducibility gate** — model bytes、peak RSS、学習時間、CPU推論時間、raw logs、source/model/data checksumを全methodで記録する。

公開能力baselineとmatched controlsがevaluation contractを通るまで、新規原理・能力進歩を認定しない。

## Candidate research question status

旧RQ-001-N3を単一SILG benchmark上のGate L＋Gate I命題として扱うことは**棄却**した。

理由: RTFM/SILGはraw language、grid state、action、rewardを提供するが、ground-truth latent intervention family、intervention target、causal abstraction、utterance-to-intervention対応を定義しない。独自partitionを後付けすると手書きontologyになる。

現在は二つに分離する。

- **Gate L — 継続:** raw languageがstate/action/history/environment identityを超える外部予測・行為情報を持つか、matched public episodesで測定する。
- **Gate I — 保留:** explicit mechanism pre/post、ground-truth intervention familyまたは理論的に正当化されたcausal abstraction、held-out target/mechanism、permutation-aware評価を持つ公開benchmarkが見つかるまで開始しない。

Gate-I適格benchmarkが見つからなければ、共同同定の実証命題を棄却し、識別不能条件・必要条件の理論研究だけを残す。

## Pinned public reproduction

- SILG commit: `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM commit: `58f17955595b5a127c96d045d896fcbcc7d4b570`
- Train: `silg:rtfm_train_s1-v0`
- Test: `silg:rtfm_test_s1-v0`
- Seeds: `1,7,19`
- Python 3.8.18 / Ubuntu 22.04
- Core pins: `torch==1.13.1+cpu`, `torchvision==0.14.1+cpu`, `gym==0.21.0`, `numpy==1.24.4`, `transformers==4.30.2`, `expman==0.0.7`, `ujson==5.10.0`
- Observation: 6×6 grid, wiki 80 token, task 40 token, inventory 8 token, valid-action mask 5, relative position 6×6×2
- Action space: 5; maximum episode length: 80

## R0.1 matched recurrent smoke

GitHub Actions run `30107848065` trained and reloaded the official SILG `multi` recurrent model for seeds `1,7,19`, then evaluated Correct, Random, Language-blind and State-only from identical independently seeded initial RTFM test instances.

- Requested frames: `2,048`; final checkpoints: `2,080`
- Parameters: `4,916,915`
- Trained state dict: approximately `19.694 MB`
- Training wall time: `26.560 / 26.592 / 26.565 s`
- Maximum RSS: `493,576 KiB`
- CPU inference: approximately `8.1 ms/step`
- Artifact digest: `sha256:408e95f8c0b682dab398dd52a5694e3bb57533453a33d775d9bd952f55b4ad50`

Aggregate smoke result:

| Method | Win rate | Mean return |
|---|---:|---:|
| Correct recurrent | 0.0167 | -1.8820 |
| Random | 0.0667 | -1.1513 |
| Language-blind | 0.0167 | -1.9087 |
| State-only | 0.0000 | -2.1243 |

Classification: **`matched_fixed_episode_smoke_completed / public_capability_baseline_not_reproduced / insufficient_training_budget`**。

低予算policyはRandom未満であり、言語除去にもほぼ不変。これはundertrainingと評価経路の診断であって、言語不要・能力進歩の証拠ではない。

## R0.2 public trajectory offline diagnostic

GitHub Actions run `30108096366` exported pinned public recurrent trajectories and trained environment-first、parameter-matched end-to-end、state-only baselines for seeds `1,7,19`.

- Environment-first / end-to-end inference model: both `7,661,516 bytes`
- State-only model: `696,140 bytes`
- Mean offline action accuracy: environment-first `0.6840`; end-to-end `0.6907`; state-only `0.7240`
- Environment-first − end-to-end: `-0.0067`
- Environment-first − state-only: `-0.0401`
- Environment-first Correct / language-blind / language-shuffle: all `0.6840`
- Maximum RSS: `538,256 KiB`
- Environment-first CPU inference: approximately `0.493 ms/item`
- Online task success and real held-out entity/dynamics/language-form transfer: 未測定

Classification: **`public_trajectory_offline_negative_diagnostic_not_r02_reproduction`**。

現在のundertrained-policy trajectoryでは言語寄与が0でstate-onlyが最良。typed observation loss、成功demonstration、online success、real holdoutがないため正式なenvironment-first再現ではない。

## Evaluation-contract status

`evaluation_contract.py`は以下を監査する。

- train/test発話重複、entity/dynamics split重複
- gold action、after state、reward、done、completed trajectory、post-treatment入力漏洩
- domain/seed/split/method欠落
- immutable instance fingerprintとprediction coverage
- method × seed × domain × splitの完全coverage
- domain × seed × condition cell、平均差、最小cell差、95% CI、paired randomization test
- model/data/log checksum、code commit、model bytes、RSS、train time、CPU latency

回帰テストは6件成功。ただし最新R0.2 summaryはinstance-level prediction、全control、完全manifest、online/holdout指標を欠くためpreflight不合格。

Formal classification: **`initial_reproduction_failure`**。

## Prior-art boundary

単独では新規性にならない既存範囲:

- unknown intervention target / unknown multi-node intervention recovery
- nonparametric causal representation learning under general environments
- causal abstraction under limited intervention families
- language-conditioned dynamics pretraining
- environment-first instruction-following pretraining
- intervention-conditioned or causal response representation

2025〜2026の一次研究は未知介入、一般mixing、少数環境・有限標本、causally disentangled representationまで範囲を拡大している。残る候補差分は、公開interactive trajectory上の言語固有情報と、別のGate-I適格benchmark上のjoint-permutation-aware partition recoveryを厳密に分離した場合に限られる。

## Current maximum bottleneck

**paper-scaleまたは収束確認済みSILG recurrent policyを固定公開test setで全controlと比較し、evaluation contractを通すこと。その後、成功または十分なtask competenceを持つtrajectory上でR0.2をonline task success・typed next-state objective・実holdout付きで再現すること。Gate Iは適格公開benchmarkが見つかるまで禁止する。**

## Progress rule

進歩として認めるのは、公開baseline再現、同一benchmark・split・instance・seed上の外部能力差、既存理論との差分が明確な定理・反例・識別可能性条件、再現可能なデータ・コード・測定ログのみ。候補数、graph、tensor、圧縮、low-rank、version-space縮約、toy環境内の一意化は数えない。

## Canonical branch policy

今後の研究は`research/intelligence-swarm-reconstruction-001`だけへ累積する。過去のstacked draft PRはnegative-results archiveとして保持し、新しい実験のbaseには使用しない。

## Current status

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 新規知能原理: 未発見
- 完成: false

## Last integration

2026-07-25: **RESET-E011**。R0.1固定初期instance matched smoke、R0.2公開trajectory negative diagnostic、R0-D strict preflight、C004のSILG Gate-I benchmark棄却を統合。R0継続、次stage遷移なし。