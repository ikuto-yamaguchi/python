# RESET-E045 — R0 Research Reconstruction

Date: 2026-07-25  
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope control

A〜Dは新しいtoy仮説、別branch、新規機構族を作成しない。公開benchmark再現、prior-art audit、frozen evaluation contract、hidden intervention-target ablationの判定だけを累積する。既存stacked draft PRはnegative-results archiveであり、新作業のbaseにしない。

## 1. Latest primary literature and official-code overlap audit

- SILG/RTFMは引き続きofficial public capability reproductionの基準である。
- J-CRe3はLREC-COLING 2024の日本語実世界multimodal reference-resolution datasetであり、公式repository `riken-grp/J-CRe3`を再現対象とする。
- 2025 score-based CRLはlinear/general transformations下でlatent variables、graph、unknown target correspondenceを言語なしで回復できる領域を示す。
- 2026年3月のfinite-sample CRLは、対数個の未知multi-node intervention環境からlatent graph、mixing matrix、representation、unknown intervention targetsを有限標本で回復できる条件を示す。

結論: unknown target、少数environment、finite-sample recovery自体をRQ-001の新規性として扱わない。

## 2. Reproduction progress

- immutable 131,072-frame SILG R0.1 bundle: **0**
- competent learned SILG baseline: **0**
- J-CRe3 numerical reproduction: **0**
- J-ORA numerical reproduction: **0**
- R0.2 qualified result: **0**

32,768-frame accepted evidenceはCorrect `1/60`、Random `4/60`、Language-blind / State-only / Language-shuffle `1/60`であり、policy competence不足である。131,072-frame runはartifactが保存されなかったため受理しない。

## 3. Required controls

次のR0.1 runではCorrect、Random、Language-blind、State-only、Language-shuffleをsame initial instancesで評価する。J-CRe3ではrandom、text-only、vision-only、mention-shuffle、frame/object-shuffleを事前登録する。

## 4. Resource and provenance

毎runでmodel/checkpoint bytes、peak RSS、training runtime、CPU latency、seed、split、actual frame count、commit、dependency lock、raw logs、predictions、checksumsを保存する。

## 5. Leakage

D015〜D035を凍結し、保存済み実bundleへ適用する。具体的なfalse pass/failureが発生しない限り、新しいauditorを追加しない。

## 6. RQ-001 decision

- Broad RQ-001: **rejected**
- Narrow RQ-001: **not adopted**

採用には、最強の非言語公式baseline再現後にも残るcountermodel pair、externally fixedでjoint recoding不能なdenotation law、language固有追加情報の直接証拠、事前登録済みclaim/counterexample/stopping ruleが必要。

## Failure continuation contract

「検証したが駄目だった」でiterationを終了しない。失敗は実装不一致、最適化失敗、表現ボトルネック、探索/学習信号不足、artifact失敗へ分類し、根拠、原因だけを変える最小修正、同一budget再run、採用・棄却・停止判定まで継続する。

次のSILG runではaction histogram、valid-action率、policy entropy、episode length、reward到達率、mask前後logit、invalid-action mass、gradient norm、policy/value loss、recurrent reset/detach、optimizer restoreを保存し、原因分類に基づく最大6 screening runを登録する。

## Stage decision

R0.1〜R0.3、novelty matrix、中心命題の事前登録が完了していないため、次stageを提案しない。

## Formal status

- 新規機構族: **未認定**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- Evaluation class: **`initial_reproduction_failure`**
- Completion: **false**