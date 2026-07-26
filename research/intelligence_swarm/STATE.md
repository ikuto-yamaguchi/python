# Intelligence Swarm State

## Mission

長期目標は、1GB未満で弱いスマートフォンCPU上でも高速に動作し、日本語コミュニケーション・知識・推論を備える知能モデルである。現在のR0では新しい機構族を作らず、公開baselineを固定資源制約下で再現し、失敗原因を潰して性能を最大化する。

## Current stage

- Stage: **R0 Research Reconstruction — constrained performance maximization**
- Canonical branch: `research/intelligence-swarm-reconstruction-001`
- A〜Dの新規toy仮説・別branch・新規機構族: **禁止**
- 既存stacked draft PR: **negative-results archive。新作業のbaseにしない**
- 外部baseline再現前の新規知能原理・能力進歩認定: **禁止**

## A–D responsibilities

- **A**: SILG/RTFM、J-CRe3/J-ORAの公式再現とimmutable artifact保存。
- **B**: 実装・最適化・表現・探索/信号の失敗診断と、原因だけを変える最小run。
- **C**: 最新一次文献・公式codeとの重複監査、novelty matrix。
- **D**: frozen D015〜D035、matched controls、resource、leakage、RQ-001判定。

## Non-termination rule

「検証したが駄目だった」で終了しない。失敗runは、失敗分類、metric/log/code差分に基づく原因、最小修正、同一budget・instance再run、採用・棄却・停止判定まで未完了とする。

## R0 status ledger

- 公開環境control再現: **1件**
- immutable 131,072-frame R0.1 bundle: **0件**
- 学習済み公開能力baseline再現: **0件**
- J-CRe3 numerical reproduction: **0件**
- J-ORA numerical reproduction: **0件**
- R0.2正式再現: **0件**
- 実R0 bundleのevaluation contract通過: **0件**
- R0.3 hidden intervention-target ablation: **棄却**
- 広義RQ-001: **棄却**
- 狭義RQ-001: **未採用**
- 評価分類: **`initial_reproduction_failure`**

## R0.1 SILG / RTFM

固定条件:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- official `multi` recurrent
- seeds `1,7,19`
- primary budget `131,072 requested frames`

accepted evidenceは32,768 frames runのみ:

- parameters `4,916,915`
- state-dict `19,694,385 bytes`
- maximum RSS `505,600 KiB`
- total three-seed training wall time `1,033.885 s`
- CPU forward `6.911 ms/step`
- Correct `1/60`
- Random `4/60`
- Language-blind / State-only / Language-shuffle `1/60`

これはpolicy competence不足であり、公開能力baseline再現ではない。131,072-frame runはR0.2中のfailureでartifactが失われたため受理しない。

## E045 active execution

1. R0.1をR0.2から分離したjobで実行し、終了直後にcheckpoint、prediction、resource、raw logs、dependency lock、checksumsを保存する。
2. requested framesとactual environment steps、seed、split、same initial instancesを確認する。
3. D015〜D035を保存済みbundleへ適用する。
4. action histogram、valid-action率、entropy、episode length、reward到達率、mask前後logit、invalid-action mass、gradient norm、policy/value lossをseed別に保存する。
5. recurrent reset/detach、optimizer restore、termination、frame counting、mask、checkpoint restoreを公式実装と照合する。
6. Correct / Random / Language-blind / State-only / Language-shuffleをsame-instanceで評価する。
7. 失敗を実装不一致、最適化失敗、表現ボトルネック、探索/信号不足、artifact失敗へ分類し、原因だけを変える最大6 screening runを登録する。
8. 有望案だけseeds `1,7,19`へ昇格し、同一frame・parameter budgetで確認する。
9. SILG competence成立後のみR0.2を開始する。

## Evaluation contract

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。

毎runでrandom/language-blind/state-only/applicable shuffle、model/checkpoint bytes、peak RSS、runtime、CPU latency、seed、split、actual frames、commit、dependency、raw logs、checksums、leakageを保存する。

## Prior-art and RQ boundary

J-CRe3はLREC-COLING 2024の日本語実世界multimodal reference-resolution datasetであり、日本語groundingの外部baselineとして扱うが、SILG/RTFMのinteractive policy competenceを代替しない。

2025 score-based CRLに加え、2026年3月の有限標本CRLは、対数個の未知multi-node intervention環境からlatent graph、mixing matrix、representation、unknown intervention targetsを有限標本で回復できる条件を示す。unknown target、少数environment、finite-sample recoveryはRQ-001の新規性根拠から除外する。

正式判断:

> **RQ-001: NARROWED — NOT ADOPTED**

採用には、最強の非言語公式baseline再現後にも残るcountermodel pair、外部固定でjoint recoding不能なdenotation law、language固有追加情報の直接証拠、事前登録済みclaim/counterexample/stopping ruleが必要。

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

2026-07-25: **RESET-E045**。最新一次文献と公式benchmark境界を再監査し、2026年3月有限標本CRLをRQ-001境界へ統合した。SILG/J-CRe3の新しい保存済みartifactや数値再現は確認できないため、外部baseline再現0件、能力進歩未認定、高校生級未達を維持する。次のR0.1 runに診断・対照・資源・leakage・失敗分類と次run登録を一体化した。