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

「検証したが駄目だった」で終了しない。失敗runは、失敗分類、metric/log/code差分に基づく原因、最小修正、同一budget・instance再run、採用・棄却・停止判定まで未完了とする。高コスト学習済みartifactが有効なら、監査・qualification障害のために再学習しない。

## R0 status ledger

- immutable R0.1 artifacts: **5件**
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

## Completed official-stateful screening

Primary evidence:

- run `30221587227`
- job `89844840438`
- artifact `8638198496`
- digest `sha256:ae28542e4bda4ca968de9d7ffc42b5ab4b4dadb518a26636a41d63b92131aa31`
- execution commit `4b1dff1cd6cd3f6a2dc360d5689cb9968c6a4998`
- `--stateful`, LSTM `core.*`, non-zero recurrent state: **passed**
- same-instance controls、official/fresh parity、artifact upload: **passed**
- answer leakage: **false**
- qualification: **rejected**

Matched aggregate:

- Correct `2/60`
- Random `4/60`
- Language-blind `2/60`
- State-only `1/60`
- Language-shuffle `2/60`
- Correct mean return `-1.8273327`
- Random mean return `-1.1513333`

Resources:

- parameters `6,200,115`
- trained model-state `24,827,943 bytes` per seed
- actual frames `131,080` per seed
- peak RSS `1,069,864 / 1,334,592 / 1,274,272 KiB`
- wall `1691.39 / 1569.14 / 1686.73 s`
- CPU forward `8.162 ms/step`

Decision:

> **official stateful core不足を単独主因として棄却する。statefulは正しく作動したが、CorrectはRandomを下回り、language-blind/shuffleと同率で、言語利用能力も成立していない。**

## Active single-factor screening: unroll length 20 → 80

変更要因は`unroll_length: 20 → 80`のみ。`stateful=true`、entropy `0.05`、actors `2`、threads `1`、batch `2`、frames `131072`、seeds `1/7/19`、split、matched instances、controlsを固定する。

Execution status:

- workflow: `.github/workflows/r01_silg_unroll80_screening.yml`
- request integration: `R01-SCREEN-004-E064`
- run `30226976064`
- job `89867137085`
- workflow head `344002bc8e5130cbb9a302fda1a2115baa8edb1c`
- status: **in_progress**
- completed: checkout、Python setup、provenance、pinned SILG/RTFM install、stateful patch、unroll-80 patch、generator schema、random/schema probe
- active step: **Train official stateful multi with unroll 80**
- artifacts: **0件（学習中）**
- performance result: **未認定**

既存push-run locatorがunroll-80を監視していなかったため、commit `746d527a0d760cc4e910e13d8913c040ee8afd5f`でmatrixとpath triggerへ追加した。locator run `30228319127`は成功した。run `30226976064`はjob生成済み・学習中へ進んだため、同一screeningを重複dispatchしない。

有効なunroll=80 runでもCorrectがRandomを上回らない場合、unroll不足単独原因を棄却する。ただしiterationは閉じず、次の単一原因をlearner optimization parity（learning rate、gradient clipping、optimizer/checkpoint restoreのうち証拠が最も強い一件）から選ぶ。

## Evaluation contract

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。毎runでrandom/language-blind/state-only/shuffle、model/checkpoint bytes、RSS、runtime、CPU latency、seed、split、actual frames、raw logs、checksums、leakageを保存する。

## Prior-art and RQ boundary

既存のscore-based CRL、finite-sample CRL、Multi-View CRL、LeGIT、GPI、ReCITE、C3、MCDRL、CmIR、CAIR、PCMCI、CausalLens、CTLD、DCAN等の境界を維持する。

ACL Findings 2026のTRACEは、multi-turn dialogueを通じたunderlying causal graphのonline reconstructionを定式化し、探索段階のcausal-graph reconstruction rewardと、介入段階のtargeted belief restructuring rewardを組み合わせる。したがって、言語対話から因果グラフを逐次探索すること、causal-graph-driven rewardで介入対象を深掘ること、探索と介入を二段階RLで接続することだけではRQ-001の新規性を認定しない。一次論文は確認済みだが、author-official repository、exact commit、dependency、dataset、公式commandのimmutable再現は未確認であり、SILG/J-CRe3の代替baselineにも数えない。

正式判断:

> **RQ-001: FURTHER NARROWED BEYOND DIALOGUE-DRIVEN CAUSAL-GRAPH EXPLORATION AND TARGETED INTERVENTION — NOT ADOPTED**

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

2026-07-27: **RESET-E066**。unroll-80 run `30226976064`はjob `89867137085`を生成し、固定条件の配線・schema/random probeを通過して3-seed学習中へ進んだ。重複dispatchせず完了artifactを待つ。TRACEのdialogue-driven causal-graph explorationとtargeted interventionをprior-art境界へ追加したが、official codeと数値再現は未確認であり、外部baseline再現0、能力進歩未認定、高校生級未達を維持する。