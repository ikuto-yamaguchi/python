# RESET-E051 — R0 Research Reconstruction

Date: 2026-07-26
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope lock

- A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。
- 公開benchmark再現、prior-art audit、frozen evaluation contract、hidden intervention-target ablationだけを累積する。
- 既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。
- 外部baseline再現前に新しい機構族、知能原理、能力進歩を認定しない。
- 「検証したが駄目だった」でcycleを閉じない。停止条件未達なら、根拠付き失敗分類から単一原因matched rerunへ接続する。

## 1. Latest primary literature and official-code overlap audit

今回の追加境界はYao et al., ICLR 2024, *Multi-View Causal Representation Learning with Partial Observability* である。公式repository `CausalLearningAI/multiview-crl` はMIT licenseで、numerical experimentとMultimodal3DIdentを用いた三view `(img0,img1,txt0)` experimentのtrain/evaluate commandを公開している。

このため、次のみではRQ-001の新規性を認定しない。

- 言語を含むmulti-view alignment
- partial observability下のshared causal-factor recovery
- multimodal contrastive learning
- view-specific informationとshared informationの分離
- text viewを追加した因果表現学習

公式codeは確認したが、exact commit、environment、dataset checksum、数値結果、model/RSS/runtime/seed/split、raw output、checksumを固定した再現は0件である。

既存境界も維持する。

- score-based CRL: latent variables、graph、unknown intervention-target correspondenceの識別・構成可能領域
- finite-sample CRL: 少数のunknown multi-node intervention環境からの有限標本回復
- CLeaR 2026: intervention-conditioned context、causal concept disentanglement、composition
- LeGIT: language-guided intervention target selectionとlow-data warm-start
- GPI: generative representationを用いたtext/image/video causal inference

## 2. SILG / J-CRe3 reproduction progress

- SILG/RTFM immutable 131,072-frame competence bundle: 0
- accepted learned public capability baseline: 0
- accepted evidence: 32,768-frame runのみ
- Correct: 1/60
- Random: 4/60
- Language-blind / State-only / Language-shuffle: 1/60
- J-CRe3 official numerical reproduction: 0
- J-ORA official numerical reproduction: 0
- GPI official-software reproduction: 0
- Multi-View CRL official-code reproduction: 0
- qualified R0.2: 0

RESET-E051では `R01_RUN_REQUEST.json` をcanonical headから再発行した。これは数値run要求であり、run ID、job conclusion、artifact ID、qualification JSON、checksum manifestが揃うまでは開始・成功・能力進歩として認定しない。

## 3. Matched controls

R0.1で必須:

- Random
- Language-blind
- State-only
- Language-shuffle
- same initial instance stream

J-CRe3で事前登録:

- Random
- Text-only
- Vision-only
- Mention-shuffle
- Frame/object-shuffle

Multi-View CRLで事前登録:

- Text-view removal
- Image-view removal
- Text shuffle
- Cross-instance view shuffle
- Random representation

## 4. Resources and reproducibility

各runで必須:

- model/checkpoint bytes
- peak RSS
- training runtime
- CPU inference latency
- seed
- split
- actual frames
- source and execution commit
- dependency lock
- raw logs
- SHA-256 manifests

SILGでは追加でaction histogram、valid-action率、policy entropy、episode length、reward到達率、mask前後logit、invalid-action mass、gradient norm、policy/value loss、recurrent reset/detach、optimizer/checkpoint restore、termination/frame countingをseed別に保存する。

## 5. Leakage

D015〜D035は凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。

- answer/gold action
- after-state/future-state
- reward/return/success/terminal
- completed trajectory/rollout
- entity/dynamics split
- utterance overlap
- semantic alias
- cross-instance shuffle provenance

のfail-closed判定を維持する。監査codeのCI成功は能力進歩に数えない。

## 6. RQ-001 decision

Broad RQ-001: **REJECTED**

Narrow RQ-001:

> **NARROWED BEYOND LANGUAGE-GUIDED TARGET SELECTION, INTERVENTION-CONDITIONED COMPOSITION, GENERATIVE-REPRESENTATION CAUSAL INFERENCE, AND PARTIALLY OBSERVED MULTI-VIEW CRL — NOT ADOPTED**

採用条件:

1. competent external baseline再現
2. strongest applicable non-language CRL再現
3. LeGIT型target-selection再現
4. intervention-context composition再現
5. GPI型生成表現因果推定再現
6. Multi-View CRL再現
7. 上記後にも残るidentical-observable-law countermodel pair
8. externally fixedでjoint recoding不能なdenotation law
9. language固有追加情報のdirect recovery evidence
10. claim、counterexample、stopping ruleの事前登録

## Stage and capability decision

- R0.1: incomplete
- R0.2: blocked by unqualified R0.1
- R0.3: rejected and closed
- novelty matrix: incomplete
- central preregistration: incomplete
- next stage: not proposed
- new mechanism family: not recognized
- new intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
- completion: false
