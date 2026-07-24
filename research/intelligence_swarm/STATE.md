# Intelligence Swarm State

## Mission

1GB未満・弱いスマートフォンCPUで実行可能な知能モデルを長期目標とし、生の日本語と環境相互作用から対象・状態・操作・因果構造を獲得する原理を研究する。ただし現在は原理発明を停止し、公開研究の再現・評価資格・新規性境界を確立する。

## Current stage

- Stage: **R0 Research Reconstruction — public capability reproduction and benchmark qualification**
- Semantic Identity Gate G1: **未達**
- Operation/Goal Gate G2: **未達**
- Formal memory eligibility: **未達**
- 学術的新規性: **未確立**
- 査読可能な中心命題: **未確立**
- Active mechanism family: **なし**
- AF-001〜AF-014: **PAUSED**
- A〜Dの新規toy仮説・別branch生成: **停止**
- 過去stacked draft PR: **negative-results archive**

## R0 status ledger

- 公開環境control再現: **1件**
- 公開学習経路再現: **1件**
- 固定初期instance matched評価経路: **1件（engineering smoke）**
- 学習済み公開能力baseline再現: **0件**
- R0.2公開trajectory offline診断: **1件（比較不適格）**
- R0.3 intervention-target ablation: **未開始・SILGでは実施禁止**
- J-CRe3日本語外部監査: **未再現**

公開能力baselineとmatched controlsがevaluation contractを通るまで、新規機構族・知能原理・能力進歩を認定しない。

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

2,048-frame級の公式SILG `multi` recurrentについて、seed `1,7,19`の学習、checkpoint保存・再読込、固定初期instance上のCorrect / Random / Language-blind / State-only評価経路を再現した。

- Parameters: `4,916,915`
- Trained state dict: 約`19.694 MB`
- Training wall time: 約`26.6 s/seed`
- Maximum RSS: `493,576 KiB`
- CPU inference: 約`8.1 ms/step`
- Correct win rate: `0.0167`
- Random win rate: `0.0667`
- Language-blind win rate: `0.0167`
- State-only win rate: `0.0000`

Classification: **`matched_fixed_episode_smoke_completed / public_capability_baseline_not_reproduced / insufficient_training_budget`**。

32,768 frames/seedへの段階的拡張、Language-shuffle、episode-level paired exportは実装・投入済みだが、完了artifactは本統合時点で未確定。結果がない状態で進歩判定しない。

## R0.2 environment-first status

公開trajectory上の旧offline比較:

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

Representation modelを調整する前に、32,768-frame以上のsource policy trajectoryが次のanti-collapse条件を通る必要がある。

- majority-action share `<= 0.90`
- 各seedでsuccessful train episode `>= 5`
- 5%以上のsupportを持つaction `>= 2`

## Evaluation contract status

`evaluation_contract.py`は以下を監査する。

- train/test utterance overlap、entity/dynamics split overlap
- gold action、after state、reward、done、post-treatment state、completed trajectory leakage
- immutable `instance_fingerprint`のprediction側必須化
- method × seed × domain × splitの完全coverage
- duplicate / missing predictionとcoverage
- domain × seed × condition cell統計
- episode-level paired gap、Correct-only / control-only、exact McNemar検定
- hierarchical cluster-bootstrap 95% CI
- source/model/data/log SHA-256、code commit、model bytes、RSS、train time、CPU latency

回帰テストは**7件成功**。ただし全methodの固定test prediction JSONLと完全artifact manifestが未提出のため、現在の正式分類は **`initial_reproduction_failure`**。

## Candidate research question status

SILG/RTFMはground-truth latent intervention family、target、mechanism pre/post operator、causal abstractionを定義しないため、Gate Iの直接benchmarkとしては棄却した。

- **Gate L — 継続・未達:** raw languageがstate/action/history/environment identityを超える外部能力を持つか、competent public policyとmatched controlsで測る。
- **Gate I — audited public benchmarkでは利用不能:** SILG/RTFM、J-CRe3、CausalTriplet、ACCESS、MIBのいずれも、episode-aligned raw language、interactive trajectory、独立に定義されたmechanism variation、正当化されたtarget/abstraction、held-out mechanism splitを同時に持たない。

現在の候補は **RQ-001-N5 — narrowed, not adopted; empirical track blocked**:

> 独立にmechanism-changing variationを定義する公開benchmark上で、episode-aligned raw languageが完全な非言語trajectoryを条件とした後にもmechanism情報を持ち、trajectory-only CRLに残る同値類を厳密に細分化し、held-out mechanism能力を改善するか。

必要条件は `I(M; L | X) > 0`。ここで`X`はstate、action、history、reward、time、policy phase、environment identityを含む。`M ⟂ L | X`なら`p(M|X,L)=p(M|X)`であり、architectureに関係なく言語はtrajectory-only同値類を細分化できない。

未知介入target回復、unknown multi-node intervention、general-environment nonparametric CRL、subset-intervention causal abstraction、temporal partition＋causal graph、multimodal partial-sharing identifiability、perturbation-feature-to-intervention modeling、causal sufficiency/necessity、language-dynamics pretraining、environment-first instruction followingは単独では既存範囲であり、新規性にならない。

適格benchmarkがnovelty audit完了までに見つからなければ、empirical Gate Iを正式に閉じ、明示的な観測・介入仮定を持つtheory-onlyの不可能性または十分条件へ限定する。

## Current maximum bottleneck

**R0.1では32,768-frame段階実験のartifactを確定し、competenceとtrajectory eligibilityを監査する。因果研究Cでは、researcher-authored target slotなしにGate Iを評価できる公開mechanism-change benchmarkが存在するかを最終監査する。見つからなければempirical Gate Iを閉じ、中心命題をtheory-onlyへ事前登録する。**

## Stage-transition rule

次stageを提案できるのは全て満たした場合だけ。

1. 学習済み外部公開能力baselineを少なくとも1件再現
2. 固定公開instance上のrandom / language-blind / state-only / shuffle対照
3. canonical 3 seedと完全artifact/leakage contract
4. R0.2のonline task success・typed next-state・実holdout付き比較
5. R0.3を適格benchmarkで完了、またはundefined/unavailableとして正式棄却
6. 2026年までのnovelty matrix
7. 中心命題・主要指標・停止条件の事前登録

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

2026-07-25: **C006**。Gate-Iの必要条件を`I(M;L|X)>0`として明文化し、SILG/RTFM、J-CRe3、CausalTriplet、ACCESS、MIBを公開benchmark資格監査した。適格benchmarkは0件。RQ-001-N5へ狭義化し、empirical Gate Iをbenchmark unavailableとして保留、研究者手書きtargetの追加を禁止した。
