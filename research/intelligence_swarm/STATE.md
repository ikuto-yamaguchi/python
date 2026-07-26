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

- immutable R0.1 artifacts: **4件**（baseline失敗2件、entropy=0.005 bundle 1件、requalification addendum 1件）
- 学習済み公開能力baseline再現: **0件**
- J-CRe3 numerical reproduction: **0件**
- R0.2正式再現: **0件**
- R0.3 hidden intervention-target ablation: **棄却維持**
- 広義RQ-001: **棄却**
- 狭義RQ-001: **未採用**
- 評価分類: **`initial_reproduction_failure`**

## Completed entropy screening and requalification

Source run `30215555334`、artifact `8636643017`では、`entropy_cost=0.005`がseed `1/7/19`すべてのcommandへ到達した。

- Correct `0/60`
- Random `4/60`
- Language-blind `2/60`
- State-only `0/60`
- Language-shuffle `0/60`
- Correct return `-2.1523326`
- Random return `-1.1513333`
- actual frames: 全seed `131080`
- parameters `4,916,915`
- CPU forward `7.564 ms/step`

Corrected artifact-only requalification:

- run `30219453396`
- job `89839257839`
- artifact `8636783476`
- digest `sha256:f752a62497362a38aeda76e3917210d1eb6eb31903743f7ee08232fc75104f12`
- source verification: passed
- pinned SILG/RTFM reinstall: passed
- corrected official-vs-matched parity audit: passed
- qualification: rejected

Official continuous streamは合計`1/60`、fresh seeded instancesは`0/60`であり、protocol差は小さくseed間で一貫しなかった。`entropy_cost=0.005`単独原因とevaluation protocol mismatch主因は正式棄却する。

## Newly identified training-fidelity defect

公式SILG `model.multi.Model`は、parser flag `--stateful`がtrueのときだけLSTM coreを生成する。公式parserのdefaultは`stateful=false`である。これまでのR0.1 training commandは`--stateful`を渡しておらず、policy diagnosticsでも全seedのrecurrent-state L2 normが常に`0.0`だった。

したがって、これまで「official multi recurrent」と記録していたbundleは、実際には**official multi non-stateful**である。この名称誤りを訂正し、次screeningは公式flag `stateful: false → true`だけを変更する。

追加済み:

- `patch_silg_stateful_screening.py`
- `.github/workflows/r01_silg_stateful_screening.yml`

次runでは、全seed commandの`--stateful`、checkpoint内`core.*` weights、診断時のnon-zero recurrent stateをfail-closed確認する。entropy `0.05`、actors `2`、batch `2`、unroll `20`、frames、seeds、split、matched instancesは固定する。

## Evaluation contract

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。毎runでrandom/language-blind/state-only/shuffle、model/checkpoint bytes、RSS、runtime、CPU latency、seed、split、actual frames、raw logs、checksums、leakageを保存する。

## Prior-art and RQ boundary

既存のscore-based CRL、finite-sample CRL、Multi-View CRL、LeGIT、GPI、ReCITE、C3、MCDRL、CmIR等の境界を維持する。2026年のCAIRはmultimodal emotion reasoningでrationaleをcausal mediatorとして扱い、interventional utilityをreward化するため、causal-mediator rewardやinformation-bottleneck adaptive optimizationだけではRQ-001の新規性を認定しない。SILGのhidden intervention-target groundingを直接再現するbaselineではなく、公式code・exact commitの固定は未完了である。

正式判断:

> **RQ-001: FURTHER NARROWED BEYOND CAUSAL-MEDIATOR REWARD OPTIMIZATION — NOT ADOPTED**

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

2026-07-26: **RESET-E062**。entropy低下とevaluation protocol mismatchを正式棄却した。さらに、従来runが`--stateful`を渡しておらずLSTM coreを持たないことを公式codeとartifact診断から特定した。公式stateful flagだけを変更する次screening workflowを追加し、外部baseline再現0、能力進歩未認定、高校生級未達を維持する。
