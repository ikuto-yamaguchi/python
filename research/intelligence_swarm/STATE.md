# Intelligence Swarm State

## Mission

長期目標は、1GB未満で弱いスマートフォンCPU上でも高速に動作し、日本語コミュニケーション・知識・推論を備える知能モデルである。R0では新規toy仮説や新機構族を作らず、公開baselineを固定契約で再現し、失敗原因を一つずつ除去する。

## Current stage

- Stage: **R0 Research Reconstruction — resume-equivalence execution blocked before job creation**
- Canonical branch: `research/intelligence-swarm-reconstruction-001`
- A〜Dの新規toy仮説・別branch・新規機構族: **禁止**
- 既存stacked draft PR: **negative-results archive。新作業のbaseにしない**
- 外部baseline再現前の新規知能原理・能力進歩認定: **禁止**

## A–D responsibilities

- **A**: SILG/RTFM、J-CRe3等の公式再現とimmutable artifact保存。
- **B**: 実装・最適化・表現・探索/信号の失敗診断と、原因だけを変える最小run。
- **C**: 最新一次文献・公式codeとの重複監査とnovelty matrix。
- **D**: D015〜D035、matched controls、resource、leakage、RQ-001判定。

## Non-termination rule

「検証したが駄目だった」で終了しない。ただし、短期screeningを公式baseline再現と誤認して追加hyperparameter探索を続けることも禁止する。能力と無関係な監査障害だけのために高コスト学習を重複しない。

## R0 status ledger

- immutable R0.1 short-horizon screening artifacts: **8件**
- official-contract infrastructure artifacts: **1件・resume evidence不足で不合格**
- one-step resume-equivalence artifact: **0件**
- one-step resume-equivalence execution: **PR headのActionsが`action_required`でjob未生成**
- official SILG RTFM 100M-frame reproduction: **0件**
- 学習済み公開能力baseline再現: **0件**
- J-CRe3 numerical reproduction: **0件**
- R0.2正式再現: **0件**
- R0.3 hidden intervention-target ablation: **棄却維持**
- novelty matrix: **未完了**
- 中心命題の事前登録: **未完了**
- 広義RQ-001: **棄却**
- 狭義RQ-001: **未採用**
- 主分類: **`workflow_execution_approval_blocker`**

## Official SILG reproduction contract

Pinned official SILG `launch.py --envs rtfm`は、`model=multi`、`stateful=false`、entropy grid `0.05/0.005`、train `silg:rtfm_train_s1-v0`、validation `silg:rtfm_test_s1-v0`を指定する。parser defaultsはtotal frames `100,000,000`、actors `30`、batch `24`、unroll `80`、threads `4`、learning rate `0.0005`、RMSprop、global gradient clip `40`である。

既存の`131,072`-frame runsは公式frame horizonの`0.131072%`にすぎない。すべて短期screening evidenceとして保持し、公式public baseline reproductionや公式baseline failureとは呼ばない。

## Closed short-horizon screening causes

以下は縮小契約内の単独原因としてのみ棄却した。公式100M-frame baselineへ外挿しない。

- `entropy_cost=0.005`
- evaluation protocol mismatch
- `stateful=true`追加
- `unroll_length=20→80`
- `learning_rate=0.0001`
- gradient clip norm `40→10`

## Latest short-horizon negative evidence

Gradient-clipping screening run `30240410850`, artifact `8644560521`:

- Correct `3/60`
- Random `4/60`
- Language-blind `0/60`
- State-only `0/60`
- Language-shuffle `3/60`
- Correct mean return `-1.7679994`
- Random mean return `-1.1513333`
- parameters `6,200,115`
- actual frames `131,200` per seed
- peak RSS `1,299,228 / 1,180,104 / 1,856,556 KiB`
- wall `1528.08 / 1559.30 / 1591.64 s`
- CPU forward `8.565 ms/step`
- answer leakage `false`
- qualification **rejected**

これは縮小契約で言語依存能力が成立しなかったnegative evidenceであり、公式baseline失敗の証拠ではない。

## Official-contract infrastructure result

Run `30258965674`, job `89954109262`, artifact `8650362356`:

- artifact digest `sha256:975d5c6223637f48c3e358d51ead0470e3f97b01826e2cd6e216fd484b8f8750`
- artifact size `61,174,640 bytes`
- official command parity: **pass**
- exact `job.tar` preservation: **pass**
- checkpoint/model tensor equality: **pass**
- optimizer state: **73 entries / 1 parameter group**
- scheduler and frame counter: **present**
- checkpoint frames: `40,320`
- checkpoint bytes: `39,266,613`
- checkpoint SHA-256: `1ce3a0590611d8d26ef06330e7f5eca43e9c13deafb8d41bf3570eadaa754675`
- peak RSS: `9,305,052 KiB`
- wall: `631.66 s`
- throughput: `63.83 frames/s`
- projected 100M-frame wall: `18.13 runner-days` per entropy/seed run

不合格理由は次の2件だけである。

- `missing_rng_state_for_one_step_resume_equivalence`
- `missing_batch_state_for_one_step_resume_equivalence`

よってoptimizer failure、public-baseline failure、能力failureとは認定しない。immutable resultは`benchmarks/grounded_causal/results_audits/SILG_RTFM_OFFICIAL_INFRA_RUN_30258965674.json`へ保存した。

## Active execution

resume instrumentationだけを追加した。pinned SILGのlearner updateを一度だけ包み、Python/NumPy/Torch RNG、exact learner batch、initial agent state、model、actor model、optimizer、schedulerを保存し、uninterrupted one-stepとreload-resumed one-stepを比較する契約は維持する。

受理条件はmodel/optimizer/schedulerのbitwise equality、lossesとgradient normのexact equality、exact batch payloadのbytes・SHA-256保存である。model、source pins、optimizer、sampling defaults、split、能力評価は変更していない。

ただし、PR head `4376e9ab931fb663214404b2b4ef0c4ec84432a1`に紐づく確認可能な11件のPR workflowはすべて`completed/action_required`で、jobが生成されていない。resume-equivalenceのrun ID、job ID、artifact ID、qualificationは0件である。これはモデル・optimizer・resume-equivalenceの失敗ではなく、実行前のapproval/policy blockerとして扱う。同条件を重複dispatchせず、Actions承認またはpolicy解除後に同じworkflowを実行する。

## Evaluation contract

D015〜D035を凍結する。能力runではrandom/language-blind/state-only/shuffle、model/checkpoint bytes、RSS、runtime、CPU latency、seed、split、actual frames、raw logs、checksums、leakageを保存する。infrastructure-only runでは能力対照をN/Aと明示し、能力進歩へ数えない。

## Prior-art and RQ boundary

既存のscore-based CRL、finite-sample CRL、Multi-View CRL、LeGIT、GPI、ReCITE、C3、MCDRL、CmIR、CAIR、PCMCI、CausalLens、CTLD、DCAN、TRACE、Bayesian Ablation、CausalDisenSeg、MagicBench、CodeBind、NoisyCausal、CaST-Bench、CausalVerse、MTG-Causal-RL、Mind Dreamer、AER等の境界を維持する。

AAAI 2026のCOGSは、構造事前分布を用いたlatent causal graph学習、causal/non-causal変数の分離、domain-invariant time-series representation、domain label不在時のprototype-based unsupervised domain discoveryを既存化している。したがって、時系列でのlatent causal/non-causal disentanglement、unsupervised environment discovery、因果表現によるOOD generalizationだけではRQ-001の新規性を認定しない。一次論文は確認済みだが、author-official repository、exact commit、公式commandを固定できていないため再現済みbaselineには数えない。

正式判断:

> **RQ-001: FURTHER NARROWED BEYOND UNSUPERVISED-DOMAIN CAUSAL REPRESENTATION LEARNING FOR TIME-SERIES OOD GENERALIZATION — NOT ADOPTED**

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Current status

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 完成: **false**

## Last integration

2026-07-28: **RESET-E078**。resume-equivalence workflowのコード契約は維持したまま、確認可能なPR Actionsが全件`action_required`でjob未生成であることをexecution blockerとして固定した。COGSをtime-series OOD causal representationの既存境界へ追加し、外部baseline再現0件、能力進歩未認定、高校生級未達を維持する。
