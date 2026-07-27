# Intelligence Swarm State

## Mission

長期目標は、1GB未満で弱いスマートフォンCPU上でも高速に動作し、日本語コミュニケーション・知識・推論を備える知能モデルである。R0では新規toy仮説や新機構族を作らず、公開baselineを固定資源制約下で再現し、失敗原因を一つずつ除去して性能を最大化する。

## Current stage

- Stage: **R0 Research Reconstruction — public reproduction contract repair**
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

「検証したが駄目だった」で終了しない。ただし、短期screeningを公式baseline再現と誤認して追加hyperparameter探索を続けることも禁止する。高コスト学習済みartifactが有効なら、監査・qualification障害だけのために再学習しない。

## R0 status ledger

- immutable R0.1 screening artifacts: **8件**
- official SILG RTFM 100M-frame reproduction: **0件**
- 学習済み公開能力baseline再現: **0件**
- J-CRe3 numerical reproduction: **0件**
- R0.2正式再現: **0件**
- R0.3 hidden intervention-target ablation: **棄却維持**
- novelty matrix: **未完了**
- 中心命題の事前登録: **未完了**
- 広義RQ-001: **棄却**
- 狭義RQ-001: **未採用**
- 主分類: **`public_reproduction_contract_mismatch`**

## Official SILG reproduction contract

Pinned official SILG `launch.py --envs rtfm`は、`model=multi`、`stateful=false`、entropy grid `0.05/0.005`、train `silg:rtfm_train_s1-v0`、validation `silg:rtfm_test_s1-v0`を指定する。parser defaultsはtotal frames `100,000,000`、actors `30`、batch `24`、unroll `80`、threads `4`、learning rate `0.0005`、RMSprop、global gradient clip `40`である。

既存の`131,072`-frame runsは公式frame horizonの`0.131072%`、推定learner update数でも公式契約の約`1/63.58`にすぎない。したがって、すべて**短期screening evidence**としてのみ保持し、公式public baseline reproductionや公式baseline failureとは呼ばない。

Immutable audit:

- `benchmarks/grounded_causal/R01_OFFICIAL_TRAINING_HORIZON_AUDIT.json`
- audit commit `4ccb3963a35d76cc8b28234f1280e7164e94df5e`

## Closed short-horizon screening causes

以下は各縮小契約内の単独原因としてのみ棄却した。公式100M-frame baselineの原因判定へ外挿しない。

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

この結果は縮小契約で言語依存能力が成立しなかったnegative evidenceであり、公式baseline失敗の証拠ではない。

## Active diagnosis: infrastructure qualification and checkpoint evidence

artifact `8644560521`にはstandalone trained model-stateは存在するが、official `job.tar`が全seedで欠落している。optimizer state、parameter groups、frame counter、model tensor一致、resume-equivalenceは判定不能である。

Evidence:

- checkpoint inventory: `results_audits/SILG_RTFM_ARTIFACT_8644560521_INVENTORY.json`
- learner variance audit: `results_audits/R0_SILG_ARTIFACT_8644560521_LEARNER_VARIANCE.json`

learner logではtotal/PG lossに大きな分散と多数の符号反転があるが、checkpoint欠落のためoptimizer/restore failureとは認定しない。

次の実行は能力screeningではなく**official-contract infrastructure qualification**とする。100M-frame本実行前に、公式model/stateful/default sampling contractのまま短いqualification segmentで、checkpoint保存、model/optimizer/scheduler/frame counter、one-step resume equivalence、RSS/runtime extrapolation、artifact post-upload inventoryをfail-closed確認する。qualification結果を能力進歩へ数えない。

runnerがactors `30`、batch `24`、threads `4`を実行できない場合は、resource-blocker logをimmutable保存し、縮小契約を公式再現と呼ばない。sampling-scaleの追加単一要因screeningは停止する。

## Evaluation contract

D015〜D035を凍結する。毎runでrandom/language-blind/state-only/shuffle、model/checkpoint bytes、RSS、runtime、CPU latency、seed、split、actual frames、raw logs、checksums、leakageを保存する。公式再現ではさらにofficial command parity、100M frame horizon、checkpoint/resume integrityを必須とする。

## Prior-art and RQ boundary

既存のscore-based CRL、finite-sample CRL、Multi-View CRL、LeGIT、GPI、ReCITE、C3、MCDRL、CmIR、CAIR、PCMCI、CausalLens、CTLD、DCAN、TRACE、Bayesian Ablation、CausalDisenSeg、MagicBench、CodeBind、NoisyCausal、CaST-Bench等の境界を維持する。

CausalVerseは、静止画、動的物理、ロボット操作、交通場面の24 sub-scenesで、ground-truth causal mechanisms、variables、interventions、temporal dependenciesを構成可能にした公開CRL benchmarkと公式repositoryを提供する。設定可能な高忠実度simulation、既知の介入target、時間依存を用いたCRL stress test自体はRQ-001の新規性にならない。exact commit、dataset checksum、公式baseline数値のimmutable再現は未完了であり、SILG/J-CRe3の能力証拠を代替しない。

正式判断:

> **RQ-001: FURTHER NARROWED BEYOND CONFIGURABLE GROUND-TRUTH INTERVENTION BENCHMARKING — NOT ADOPTED**

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

2026-07-27: **RESET-E074**。公式SILG launch contractを再監査し、既存13万frame試験を公式再現ではなく短期screeningへ明確に再分類した。次のsampling-scale hyperparameter screeningは停止し、100M-frame公式契約の前段としてcheckpoint/resume integrityとresource feasibilityだけを確認するinfrastructure qualificationへ切り替えた。artifact `8644560521`のlearner variance diagnosticとCausalVerse novelty境界は維持するが、外部baseline再現0、能力進歩未認定、高校生級未達を維持する。
