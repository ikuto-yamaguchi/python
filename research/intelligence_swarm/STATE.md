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

- immutable R0.1 artifacts: **7件**
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

## Completed learning-rate screening

Primary evidence:

- run `30235108376`
- job `89881341003`
- artifact `8642403437`
- digest `sha256:882e92a17ba5da5836dcf78379a484cc7ed63827ed3bf0b18196c5b18c3d8917`
- execution commit `67556f067028edac502380c6d3de15575c996ffc`
- `--stateful`、`--unroll_length 80`、`--learning_rate 0.0001`、LSTM `core.*`: **passed**
- same-instance controls、official/fresh parity、artifact upload: **passed**
- answer leakage: **false**
- qualification: **rejected**

Matched aggregate:

- Correct `0/60`
- Random `4/60`
- Language-blind `0/60`
- State-only `1/60`
- Language-shuffle `0/60`
- Correct mean return `-2.1523326`
- Random mean return `-1.1513333`
- Correct−Random return `-1.0009993`

Resources:

- parameters `6,200,115`
- trained model-state `24,827,943 / 24,827,943 / 24,828,026 bytes`
- actual frames `131,200` per seed
- peak RSS `1,470,976 / 1,269,884 / 2,414,924 KiB`
- wall `1441.30 / 1404.99 / 1483.19 s`
- CPU forward `7.511 ms/step` model audit; matched inference approximately `8.5–8.7 ms/step`
- chosen-action valid fraction `1.0` for all seeds

Decision:

> **learning-rate不足を単独主因として棄却する。`0.0001`は全seedへ正しく到達したが、Correct successは0でRandomを下回り、language-blind/shuffleとの差も成立しなかった。**

## Active single-factor screening: gradient clipping

Official pinned SILG `run_exp.py`は`clip_grad_norm_(model.parameters(), 40.0)`をhard-codeしている。次はその閾値だけを`40.0 → 10.0`へ変更する。

Fixed:

- `stateful=true`
- `unroll_length=80`
- learning rate: **official default**
- entropy `0.05`
- actors `2`、threads `1`、batch `2`
- frames `131072`、seeds `1/7/19`
- model family、split、matched instances、全controls

Implementation:

- source patch: `patch_silg_gradient_clip_screening.py`
- workflow: `.github/workflows/r01_silg_gradient_clip_screening.yml`
- source-patch commit: `2c877197b275e9c11f018479909adfe8e2a82844`
- workflow commit: `3f0c62430a27116722c22f69525b54631d93032b`
- run / job / artifact / performance: **未確認・未認定**

Fail-closed evidence requires the pinned source to contain clip `10.0` and not `40.0`, all commands to keep stateful/unroll=80 without an explicit learning-rate override, complete LSTM checkpoints, matched controls, resource provenance, checksums, leakage=false, parity and unchanged qualification.

If valid gradient clip `10.0` remains at/below Random, reject clipping threshold as the sole cause and continue to optimizer/checkpoint restore integrity as the next single cause. Do not close on the negative result alone.

## Evaluation contract

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。毎runでrandom/language-blind/state-only/shuffle、model/checkpoint bytes、RSS、runtime、CPU latency、seed、split、actual frames、raw logs、checksums、leakageを保存する。

## Prior-art and RQ boundary

既存のscore-based CRL、finite-sample CRL、Multi-View CRL、LeGIT、GPI、ReCITE、C3、MCDRL、CmIR、CAIR、PCMCI、CausalLens、CTLD、DCAN、TRACE、Bayesian Ablation、CausalDisenSeg等の境界を維持する。

MagicBench（ACL 2026）は、対称prompt下でも視覚探索が言語triggerへ依存するvisual-agency lossを診断し、spatial promptingとsignal magnificationによる因果介入で内部推論が残ることを示す。したがって、language dominance、perceptual-access bottleneck、prompt介入によるvisual grounding回復だけではRQ-001の新規性を認定しない。公式code/dataset `Ink-Dawn/MagicBench`は公開されているが、exact commit、dependency、immutable numerical reproductionは未完了であり、SILG/J-CRe3の代替baselineにも数えない。

正式判断:

> **RQ-001: FURTHER NARROWED BEYOND CAUSAL DIAGNOSIS OF LANGUAGE-TRIGGERED VISUAL AGENCY LOSS — NOT ADOPTED**

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

2026-07-27: **RESET-E069**。learning-rate `0.0001` run `30235108376`をartifactまで精査し、Correct `0/60`、Random `4/60`、qualification rejectedを確認してlearning-rate単独原因を棄却した。次の一要因としてofficial hard-coded gradient clipを`40.0→10.0`に変更するsource patchとworkflowを同じcanonical branchへ追加した。MagicBenchをnovelty境界へ追加したが、外部baseline再現0、能力進歩未認定、高校生級未達を維持する。
