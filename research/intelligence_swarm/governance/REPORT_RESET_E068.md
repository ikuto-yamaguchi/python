# RESET-E068 — active learning-rate screening and duplicate-run control

## Scope

Canonical branch `research/intelligence-swarm-reconstruction-001`のみを更新した。A〜Dに新規toy仮説、別branch、新規機構族を作らせず、公開benchmark再現、prior-art audit、evaluation contract、hidden intervention-target ablationだけを累積する。既存stacked draft PRはnegative-results archiveとして扱い、新作業のbaseにしない。

## R0.1 active execution

Learning-rate single-factor screeningのprimary runを確認した。

- run: `30235108376`
- job: `89881341003`
- execution commit: `67556f067028edac502380c6d3de15575c996ffc`
- changed factor: explicit `learning_rate=0.0001`
- fixed: `stateful=true`、`unroll_length=80`、entropy `0.05`、actors `2`、threads `1`、batch `2`、frames `131072`、seeds `1/7/19`、split、matched instances、all controls

確認時点で以下は成功した。

- pinned SILG / RTFM install
- stateful routing patch
- unroll-80 routing patch
- learning-rate routing patch
- generator schema
- canonical random control / schema probe

現在はthree-seed training中である。artifact、qualification、Correct/Random/control値、model/RSS/runtimeはまだ生成されていないため、外部baseline再現や能力進歩には数えない。

## Duplicate-run handling

後続runも存在する。

- run: `30236217754`
- execution commit: `b3f1c6775fb6be5376ff53359b6732dfb100f313`
- status: pending
- jobs: 0
- artifacts: 0

Primary runが有効artifactを保存した場合、後続runを追加seed、独立再現、性能改善証拠として二重計上しない。Primary runがexecution failureまたはartifact lossの場合だけfallback候補とする。同一条件の追加dispatchは禁止する。

## Decision contract

全seedの実commandへ`--learning_rate 0.0001`、`--stateful`、`--unroll_length 80`が到達し、LSTM checkpoint、frame budget、same-instance controls、leakage=false、resource provenance、official/fresh parityを満たした場合だけ性能を解釈する。

- CorrectがRandomをwin rateとreturnの両方で上回れば、learning-rate reductionを候補として保持する。
- routingが有効でもCorrectがRandom以下なら、learning-rate単独原因を棄却する。
- 棄却しても終了せず、保存logと公式code差分に基づき、gradient clippingまたはoptimizer/checkpoint restoreの一方だけを次要因にする。

## Prior-art audit

CausalDisenSeg（arXiv 2026）は、missing-modality brain-tumor segmentationで、CVAE+HSICによりanatomical causal factorとstyle bias factorを分離し、region causality moduleとcounterfactual dual-adversarial抑制でbiasのNatural Direct Effectを抑える。

したがって、以下だけではRQ-001の新規性を認定しない。

- missing-modality下のcausal/style disentanglement
- region-grounded causal representation
- counterfactual suppression of bias NDE
- causal disentanglementによるcross-dataset robustness

一次preprintは確認済みだが、author-official repository、exact commit、immutable numerical reproductionは未確認であり、SILG/J-CRe3の代替baselineには数えない。

RQ-001:

> **FURTHER NARROWED BEYOND COUNTERFACTUAL CAUSAL DISENTANGLEMENT UNDER MISSING MODALITIES — NOT ADOPTED**

## Formal status

- immutable R0.1 artifacts: **6**
- competent learned external baseline: **0**
- active learning-rate screening: **primary run training中**
- J-CRe3 numerical reproduction: **0**
- qualified R0.2: **0**
- R0.3 hidden intervention-target ablation: **rejected and retained**
- novelty matrix: **incomplete**
- central-claim preregistration: **incomplete**
- new mechanism family: **not recognized**
- new intelligence principle: **not discovered**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next stage: **not proposed**