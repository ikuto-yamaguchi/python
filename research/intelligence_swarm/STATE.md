# Intelligence Swarm State

## Mission

長期目標は、1GB未満で弱いスマートフォンCPU上でも高速に動作し、日本語コミュニケーション・知識・推論を備える知能モデルである。R0では新規toy仮説や新機構族を作らず、公開baselineを固定契約で再現し、失敗原因を一つずつ除去する。

## Current stage

- Stage: **R0 Research Reconstruction — official SILG continuation blocked before replacement execution**
- Canonical branch: `research/intelligence-swarm-reconstruction-001`
- Canonical PR: **#409 open / draft / mergeable**
- A〜Dの新規toy仮説・別branch・新規機構族: **禁止**
- 既存stacked draft PR: **negative-results archive。新作業のbaseにしない**
- 外部baseline再現前の新規知能原理・能力進歩認定: **禁止**

## A–D responsibilities

- **A**: SILG/RTFM、J-CRe3等の公式再現とimmutable artifact保存。
- **B**: 実装・最適化・表現・探索/信号の失敗診断と、原因だけを変える最小run。
- **C**: 最新一次文献・公式codeとの重複監査とnovelty matrix。
- **D**: D015〜D035、matched controls、resource、leakage、RQ-001判定。

## Non-termination rule

「検証したが駄目だった」で終了しない。ただし、短期screeningを公式baseline再現と誤認して追加hyperparameter探索を続けることも禁止する。能力と無関係な監査・実行障害だけのために高コスト学習を重複しない。

## R0 status ledger

- immutable R0.1 short-horizon screening artifacts: **8件**
- official-contract infrastructure artifact: **1件**
- accepted exact one-step resume-equivalence artifact: **1件**
- official SILG RTFM 100M-frame reproduction: **0件**
- official seed-1 / entropy-0.05 first 1M chunk: **initial run failed before training; replacement result unconfirmed**
- 学習済み公開能力baseline再現: **0件**
- official-horizon matched controls: **0件**
- J-CRe3 numerical reproduction: **0件**
- R0.2正式再現: **0件**
- R0.3 hidden intervention-target ablation: **棄却維持**
- novelty matrix: **未完了**
- 中心命題の事前登録: **未完了**
- 広義RQ-001: **棄却**
- 狭義RQ-001: **未採用**
- 主分類: **`official_100m_replacement_execution_unconfirmed`**

## Official SILG reproduction contract

Pinned official SILG `launch.py --envs rtfm`は、`model=multi`、`stateful=false`、entropy grid `0.05/0.005`、train `silg:rtfm_train_s1-v0`、validation `silg:rtfm_test_s1-v0`を指定する。parser defaultsはtotal frames `100,000,000`、actors `30`、batch `24`、unroll `80`、threads `4`、learning rate `0.0005`、RMSprop、global gradient clip `40`である。

既存の`131,072`-frame runsは公式frame horizonの`0.131072%`にすぎない。すべてshort-horizon screening evidenceとして保持し、公式public baseline reproductionや公式baseline failureとは呼ばない。

## Accepted resume-equivalence evidence

- run `30300067389`
- job `90090542489`
- artifact `8666312079`
- artifact SHA-256 `34f02c802f6db15b55336a0547e3914846aad6d74783ebfc371d12ca6ac08115`
- frames `3840 -> 5760`

Exact consumed learner batch、initial recurrent state、learner model、optimizer、scheduler、gradient、Python/NumPy/Torch RNG、stats、frame incrementは一致した。これはcaptured official learner updateのexact replayだけを証明し、asynchronous queue continuation、100M horizon、benchmark competenceは証明しない。

## Active official continuation

最初のseed-1 / entropy-0.05 chunk run `30308447687`は、pinned SILGが`--seed` CLI argumentを持たないためtraining開始前に失敗した。

Immutable failure evidence:

- artifact `8669383695`
- SHA-256 `9a5518b1a5e5338886ed2d3f2429d0e0246f0ba9cd919de7627e6f01c74dccd4`

Commit `ce6909baf0e0879d1547c34beb457d59d2027b9e`はunsupported `--seed`を削除し、pinned `run_exp.py`へseedだけを固定する監査済みpatchを適用した。

- global Python / NumPy / Torch seed: `SILG_EXPERIMENT_SEED=1`
- actor seed: `experiment_seed * 1000003 + actor_index`
- patch前後sourceとSHA-256をartifact保存
- model、loss、optimizer、environment、action schema、sampling defaults、frame budgetは不変

現head `e168d58696eea3356adc971e7d2899f914b06b0d`に対する確認可能なPR-triggered workflow 12件はすべて`action_required`でjob未生成だった。これはmodel failureではなくworkflow execution approval/policy blockerである。replacement chunkのrun/job/artifact/qualificationを独立確認するまで開始・完了・能力進歩を認定せず、同一chunkを重複dispatchしない。

## Latest short-horizon negative evidence

Run `30240410850`, artifact `8644560521`:

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

## Official-contract resource anchor

Run `30258965674`, artifact `8650362356`:

- peak RSS `9,305,052 KiB`
- wall `631.66 s`
- throughput `63.83 frames/s`
- checkpoint frames `40,320`
- projected 100M wall `18.13 runner-days` per entropy/seed run

## Evaluation contract

D015〜D035を凍結する。能力runではrandom/language-blind/state-only/shuffle、model/checkpoint bytes、RSS、runtime、CPU latency、seed、split、actual frames、raw logs、checksums、leakageを保存する。infrastructure-only runでは能力対照をN/Aと明示し、能力進歩へ数えない。

Normalized-cell regression fixtureは明示holdout契約に合わせて修正済みであり、直前の実行可能headではevaluation-contract checksが通過した。現headの`action_required`は承認/policy層の実行ブロッカーであり、評価ロジックの回帰とは認定しない。Standalone canonical-instance-identity auditは、`validate_dataset()`と`score()`へのdirect fail-closed integration完了まで省略しない。

## Prior-art and RQ boundary

既存のscore-based CRL、finite-sample CRL、unknown multi-node intervention CRL、Multi-View CRL、LeGIT、GPI、ReCITE、C3、MCDRL、CmIR、CAIR、PCMCI、CausalLens、CTLD、DCAN、TRACE、Bayesian Ablation、CausalDisenSeg、MagicBench、CodeBind、NoisyCausal、CaST-Bench、CausalVerse、MTG-Causal-RL、Mind Dreamer、AER、COGS等の境界を維持する。

最新再監査では、2026年のfew-environment finite-sample CRLが少数のunknown multi-node interventionからlatent graph、mixing/representation、unknown intervention targetsを回復する保証を提示している。2024年のUMN-CRLにはauthor-official codeも存在する。ただし、本repositoryでexact commit、dependency、public numerical contractを固定したimmutable再現は未完了である。文献名だけを追加してnovelty matrixを水増ししない。

正式判断:

> **RQ-001: FURTHER NARROWED — NOT ADOPTED**

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

2026-07-28: **RESET-E082**。official first chunkの`--seed` CLI defectとimmutable failure artifact、seed-only patch、replacement execution未確認、現headのActions approval/policy blockerを統合した。外部baseline再現0件、能力進歩未認定、高校生級未達を維持する。
