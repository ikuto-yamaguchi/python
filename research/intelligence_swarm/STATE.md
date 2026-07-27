# Intelligence Swarm State

## Mission

長期目標は、1GB未満で弱いスマートフォンCPU上でも高速に動作し、日本語コミュニケーション・知識・推論を備える知能モデルである。R0では新規toy仮説や新機構族を作らず、公開baselineを固定契約で再現し、失敗原因を一つずつ除去する。

## Current stage

- Stage: **R0 Research Reconstruction — resume-equivalence instrumentation**
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
- official SILG RTFM 100M-frame reproduction: **0件**
- 学習済み公開能力baseline再現: **0件**
- J-CRe3 numerical reproduction: **0件**
- R0.2正式再現: **0件**
- R0.3 hidden intervention-target ablation: **棄却維持**
- novelty matrix: **未完了**
- 中心命題の事前登録: **未完了**
- 広義RQ-001: **棄却**
- 狭義RQ-001: **未採用**
- 主分類: **`resume_equivalence_instrumentation_gap`**

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

次の単一修正対象はresume instrumentationのみ。

1. checkpoint境界のPython/NumPy/Torch RNG stateを保存する。
2. 次のlearner updateで消費するexact batchを保存または決定的fingerprint化する。
3. model、optimizer、scheduler、frame、RNGをrestoreする。
4. 同一batchでone-step updateを再実行する。
5. model tensors、optimizer slots、scheduler/frame、scalar lossesの完全一致を要求する。

model、source pins、optimizer、sampling defaults、split、能力評価は変更しない。この監査が通るまで100M-frame capability reproductionを開始しない。

## Evaluation contract

D015〜D035を凍結する。能力runではrandom/language-blind/state-only/shuffle、model/checkpoint bytes、RSS、runtime、CPU latency、seed、split、actual frames、raw logs、checksums、leakageを保存する。infrastructure-only runではrandomをplumbing probeとして保存し、他の能力対照はN/Aと明示する。

## Prior-art and RQ boundary

既存のscore-based CRL、finite-sample CRL、Multi-View CRL、LeGIT、GPI、ReCITE、C3、MCDRL、CmIR、CAIR、PCMCI、CausalLens、CTLD、DCAN、TRACE、Bayesian Ablation、CausalDisenSeg、MagicBench、CodeBind、NoisyCausal、CaST-Bench、CausalVerse、MTG-Causal-RL等の境界を維持する。

Mind Dreamer (ICML 2026)はlatent world-model manifoldへのactive causal intervention、adversarially generated intervention anchors、relay value/uncertainty propagationを扱う。これらだけではRQ-001の新規性にならず、SILG/J-CRe3の再現証拠も代替しない。

正式判断:

> **RQ-001: FURTHER NARROWED BEYOND ACTIVE CAUSAL INTERVENTION ON LATENT WORLD-MODEL MANIFOLDS — NOT ADOPTED**

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

2026-07-27: **RESET-E076**。official-contract infrastructure runを回収し、command/checkpoint/model/optimizer/frame/resource保存の成功と、RNG・learner-batch state不足によるresume-equivalence未達を分離した。次の単一修正をresume instrumentationだけに固定し、能力進歩未認定・高校生級未達を維持する。
