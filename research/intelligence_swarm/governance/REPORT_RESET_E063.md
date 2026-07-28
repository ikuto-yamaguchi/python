# RESET-E063 — R0 Research Reconstruction Integration

Date: 2026-07-26

Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope lock

A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。公開benchmark再現、prior-art audit、evaluation contract、hidden intervention-target ablationだけを同じcanonical branchへ累積する。既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。

外部baselineが再現されるまで、新規機構族、新しい知能原理、能力進歩、高校生級到達を認定しない。

## 1. Latest primary literature and official-code overlap audit

### Progressive Cross-Modal Causal Intervention, CVPR 2026

PCMCIは、optimal-transport-based causal intervention、action-relation-aware back-door blocking、deconfounded text embeddingをmediatorとするfront-door adjustmentを段階的に組み合わせ、長期行動認識におけるcross-modal spurious alignmentとvisual confoundingを抑える。

重複境界:

- cross-modal causal intervention
- text embeddingをmediatorとするfront-door adjustment
- action relationを使ったback-door blocking
- progressive visual deconfounding

これら単独ではRQ-001の新規性を認定しない。CVF一次論文は確認済みだが、author-official repository、exact commit、dependency、dataset command、公式数値再現は未解決である。

### CausalLens, CVPR 2026

CausalLensはtraining-free・single-passでLVLM decoder hidden stateへ介入し、visual/text/system prompt pathwaysを分解し、sensitivityでvisual-reliable attention headを選択してprojection-aligned correctionを行う。

重複境界:

- sensitivity-guided head selection
- training-free hidden-state intervention
- single-pass visual grounding correction
- low-overhead multimodal hallucination mitigation

これら単独でもRQ-001を採用しない。SILGのinteractive policy competence、hidden intervention-target recovery、J-CRe3の日本語実世界参照解決を直接再現するbaselineではない。

## 2. SILG / J-CRe3 reproduction progress

### SILG R0.1

閉じた原因:

- entropy reduction `0.05 → 0.005`: sufficient causeとして棄却
- evaluation protocol mismatch: main causeとして棄却

active single-factor screening:

- `stateful: false → true`

最新locator evidence:

- run `30221587227`, job `89844840438`: official multi stateful 3-seed training中
- run `30221650935`: pending

重複run契約:

- 最初のfactor-valid・artifact-valid bundleだけをprimary evidenceとする。
- 後続runはprimary execution/artifact failure時のfallbackに限定する。
- 同一条件の二runを独立な能力改善証拠として重複計上しない。
- 現在の二runが確定するまで同一screeningを追加dispatchしない。

### J-CRe3

公式repository `riken-grp/J-CRe3`のexact commit、dataset checksum、license、official command、model/RSS/runtime/seed/split、matched controlsを固定したnumerical reproductionは0件である。

## 3. Matched controls

SILG stateful screeningで必須:

- Correct
- Random
- Language-blind
- State-only
- Language-shuffle
- same-instance topology

J-CRe3で予定:

- Random
- Text-only
- Vision-only
- Mention-shuffle
- Frame/object-shuffle

controlが欠落したbundleは能力証拠に採用しない。

## 4. Model and resource provenance

各seedについて以下を必須保存する。

- exact model family and command
- `--stateful` factor routing
- checkpoint `core.*` LSTM weights
- recurrent-state diagnostics
- model/checkpoint bytes
- peak RSS
- training wall time
- CPU latency
- seed and split
- actual frames
- raw logs
- dependency lock
- SHA-256 manifest

## 5. Leakage and evaluation contract

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。

毎bundleで以下を確認する。

- utterance overlap
- entity/dynamics split leakage
- gold action / after-state / reward / outcome / completed-trajectory leakage
- semantic alias leakage
- prediction/resource/checksum provenance
- same-instance paired topology

PR headでunified acceptance gateとR0D core metric coverageに失敗があるが、これをstateful model performanceと混同しない。該当jobの最小root causeだけを切り分ける。

## 6. RQ-001 decision

Broad RQ-001: **rejected**

Narrow RQ-001: **not adopted**

Formal boundary:

> **FURTHER NARROWED BEYOND PROGRESSIVE CROSS-MODAL DECONFOUNDING AND SENSITIVITY-GUIDED HIDDEN-STATE INTERVENTION — NOT ADOPTED**

採用には、既存非言語baselineを差し引いた後にも残るlanguage固有追加情報、明示的countermodel pair、joint recodingを排除する外部denotation law、事前登録済みclaim/counterexample/stopping ruleが必要である。

## Non-termination decision

stateful screeningがnegativeでもiterationを閉じない。

- factor routingが無効: 配線修復して同一条件再run
- recurrent state有効かつcompetenceなし: stateful不足単独原因を棄却
- 次の単一要因: `unroll_length: 20 → 80`
- 高コストartifactが有効: auditor/qualification障害だけのために再学習しない

## Formal status

- immutable R0.1 artifacts: **4**
- competent external baseline reproduction: **0**
- active official-stateful screening: **1 training, 1 pending**
- J-CRe3 numerical reproduction: **0**
- qualified R0.2: **0**
- R0.3: **rejected and retained**
- novelty matrix: **incomplete**
- central claim preregistration: **incomplete**
- new mechanism family: **not recognized**
- new intelligence principle: **none**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next-stage proposal: **none**
