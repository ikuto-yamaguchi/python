# Intelligence Swarm State

## Mission

長期目標は、1GB未満で弱いスマートフォンCPU上でも高速に動作し、日本語コミュニケーション・知識・推論を備える知能モデルである。R0では新規toy仮説や新機構族を作らず、公開baselineを固定資源制約下で再現し、失敗原因を一つずつ除去して性能を最大化する。

## Current stage

- Stage: **R0 Research Reconstruction — constrained performance maximization**
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

「検証したが駄目だった」で終了しない。失敗runは、失敗分類、metric/log/code差分に基づく原因、最小修正、同一budget・instance再run、採用・棄却・停止判定まで未完了とする。高コスト学習済みartifactが有効なら、監査・qualification障害だけのために再学習しない。

## R0 status ledger

- immutable R0.1 artifacts: **8件**
- 学習済み公開能力baseline再現: **0件**
- J-CRe3 numerical reproduction: **0件**
- R0.2正式再現: **0件**
- R0.3 hidden intervention-target ablation: **棄却維持**
- 広義RQ-001: **棄却**
- 狭義RQ-001: **未採用**
- 評価分類: **`initial_reproduction_failure`**

## Closed causes

- `entropy_cost=0.005`単独原因: **棄却**
- evaluation protocol mismatch主因: **棄却**
- official stateful core不足単独原因: **棄却**
- `unroll_length=20`不足単独原因: **棄却**
- `learning_rate=0.0001`単独原因: **棄却**
- gradient clip norm `40.0`不足単独原因: **棄却**

## Latest qualified negative evidence

Gradient-clipping screening:

- run `30240410850`
- job `89896249118`
- artifact `8644560521`
- digest `sha256:987bc842229a8a9d03dcced3387c4c8a17a2049fdc2aadfad6c7560027e11e19`
- execution commit `3f0c62430a27116722c22f69525b54631d93032b`
- Correct `3/60`
- Random `4/60`
- Language-blind `0/60`
- State-only `0/60`
- Language-shuffle `3/60`
- Correct mean return `-1.7679994`
- Random mean return `-1.1513333`
- parameters `6,200,115`
- trained model-state `24,827,943 / 24,827,943 / 24,828,026 bytes`
- actual frames `131,200` per seed
- peak RSS `1,299,228 / 1,180,104 / 1,856,556 KiB`
- wall `1528.08 / 1559.30 / 1591.64 s`
- CPU forward `8.565 ms/step`
- chosen-action valid fraction `1.0` for all seeds
- answer leakage `false`
- qualification **rejected**

Decision:

> **gradient-clipping閾値40.0を単独主因として棄却する。CorrectはRandomを超えず、language-shuffleと同率で、言語依存能力は成立しなかった。**

## Active diagnosis: checkpoint evidence preservation

artifact `8644560521`を実際に展開してinventory監査した結果、seed `1/7/19`のstandalone trained model-stateは存在するが、必要な`SILG_RTFM_OFFICIAL_CHECKPOINT_SEED_<seed>.job.tar`は0件だった。

Evidence:

- inventory: `results_audits/SILG_RTFM_ARTIFACT_8644560521_INVENTORY.json`
- inventory commit: `fd7978701408592a3e5171e29641a7b47583eb88`
- classification: **`checkpoint_evidence_preservation_failure`**
- optimizer/checkpoint restore integrity: **判定不能**

この欠落からoptimizer stateの空/非空、parameter groups、frame counter、model tensor一致、resume-equivalenceを推測してはならない。optimizer/checkpoint restoreを採用・棄却しない。

次の既に正当化されたtraining runでは、評価前に全seedのofficial `job.tar`存在・bytes・SHA-256をfail-closed確認し、artifact upload後にもinventoryを検証する。古いartifactの証拠欠落だけを直すための重複3-seed再学習は禁止する。

## Evaluation contract

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規受入auditorを追加しない。checkpoint inventoryは能力受入条件の追加ではなく、事前指定済みoptimizer/restore原因を検証可能にするprovenance要件である。毎runでrandom/language-blind/state-only/shuffle、model/checkpoint bytes、RSS、runtime、CPU latency、seed、split、actual frames、raw logs、checksums、leakageを保存する。

## Prior-art and RQ boundary

既存のscore-based CRL、finite-sample CRL、Multi-View CRL、LeGIT、GPI、ReCITE、C3、MCDRL、CmIR、CAIR、PCMCI、CausalLens、CTLD、DCAN、TRACE、Bayesian Ablation、CausalDisenSeg、MagicBench、CodeBind、NoisyCausal等の境界を維持する。

CaST-Bench（CVPR 2026）は、動画中の複数の時空間証拠をbounding-box trackとtemporal segmentでgroundしたcausal chain reasoning benchmarkを提供する。したがって、視覚証拠へgroundされた因果chainの構築・局在化・回答評価だけではRQ-001の新規性を認定しない。これはhidden intervention-target identificationやSILGのinteractive policy competenceとは別能力であり、論文値を本研究の能力証拠へ流用しない。

正式判断:

> **RQ-001: FURTHER NARROWED BEYOND CAUSAL-CHAIN-GROUNDED SPATIO-TEMPORAL VIDEO REASONING — NOT ADOPTED**

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

2026-07-27: **RESET-E072**。gradient-clip artifact `8644560521`を実展開し、official `job.tar`が全seedで欠落していることを確認した。optimizer/checkpoint restore failureとは認定せず、`checkpoint_evidence_preservation_failure`としてinventoryを固定した。古いartifactの欠落だけを理由とする重複学習を禁止し、次の正当化済みrunでcheckpoint存在・digest・artifact inventoryをfail-closed化する。CaST-Benchをnovelty境界へ追加したが、外部baseline再現0、能力進歩未認定、高校生級未達を維持する。
