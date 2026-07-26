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

「検証したが駄目だった」で終了しない。失敗runは、失敗分類、metric/log/code差分に基づく原因、最小修正、同一budget・instance再run、採用・棄却・停止判定まで未完了とする。文書・監査更新だけでiterationを閉じず、数値run requestまで同じ統合内で発行する。

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

## Active execution

1. `qualify_r01_source_policy.py`をR0.1とR0.2の間に置く。
2. R0.1は終了直後にcheckpoint、matched predictions、resource、raw logs、dependency lock、checksums、qualification結果を、成功・失敗にかかわらず保存する。
3. qualificationはsource pin、seeds `1/7/19`、actual checkpoint frames、全checkpoint完了、same-instance control、answer-leakage false、Correct/Randomのwin・returnをfail-closedで確認する。
4. `Correct <= Random`、Correct success zero、frame未達、seed/method/instance不整合、artifact欠落のいずれかならR0.2を開始しない。
5. 不合格時は `implementation_or_artifact_failure` または `optimization_or_policy_competence_failure` に分類し、固定条件、診断項目、変更可能な単一原因、matched再試験、停止条件を `next_run_contract` として保存する。
6. R0.2 jobはdownload後にもqualification artifactの `qualified_for_r02=true` を再確認する。
7. 次runではaction histogram、valid-action率、entropy、episode length、reward到達率、mask前後logit、invalid-action mass、gradient norm、policy/value lossをseed別に保存し、公式実装との差、recurrent reset/detach、optimizer、termination、frame counting、mask、checkpoint restoreを診断する。
8. 原因だけを変える最大6 screening runを行い、有望案だけseeds `1,7,19`へ昇格する。
9. 今回の文書更新後のcanonical headからR0.1 run requestを更新し、数値実験を再要求する。

このゲートは新しいモデルやtoy仮説ではなく、無能力なsource policyからR0.2の見かけ上の差を作ることを防ぎ、失敗から次の性能改善runへ接続する実行制御である。

## Evaluation contract

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。

毎runでrandom/language-blind/state-only/applicable shuffle、model/checkpoint bytes、peak RSS、runtime、CPU latency、seed、split、actual frames、commit、dependency、raw logs、checksums、leakageを保存する。

現headで確認できたworkflow successはartifact-path containment、unified acceptance gate、prediction-method topologyの監査系のみであり、R0.1数値再現や能力進歩には数えない。

## Prior-art and RQ boundary

J-CRe3はLREC-COLING 2024の日本語実世界multimodal reference-resolution datasetであり、日本語groundingの外部baselineとして扱うが、SILG/RTFMのinteractive policy competenceを代替しない。

2025 score-based CRLと2026年3月の有限標本CRLにより、unknown target、少数environment、finite-sample recoveryはRQ-001の新規性根拠から除外済みである。

LeGITは、システム変数の自然言語meta-informationとLLMの世界知識を使って初期のintervention targetを選択し、数値的online causal discoveryをwarm-startする。したがって、自然言語記述を使った介入候補選択、低データ初期局面でのLLM warm-start、言語知識と数値因果探索の組合せ自体はRQ-001の新規性候補から除外する。

LeGITのproject pageには`Code`表記があるが、2026-07-26時点の監査では公開repository URLへ解決できず、OpenReviewにも公式code URLは提示されていない。したがって状態を **paper/project-page確認済み・official code unresolved** に訂正する。exact commit、dependency、prompt、split、seed、raw output、checksumを固定した再現は未実施であり、性能証拠として認定しない。

正式判断:

> **RQ-001: NARROWED BEYOND LANGUAGE-GUIDED INTERVENTION SELECTION — NOT ADOPTED**

採用には、最強の非言語baselineとLeGIT型language-guided target-selection baselineの再現後にも残るcountermodel pair、外部固定でjoint recoding不能なdenotation law、target selectionを超えるlanguage固有追加情報の直接証拠、事前登録済みclaim/counterexample/stopping ruleが必要。

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

2026-07-26: **RESET-E047**。監査文書だけでiterationを閉じない規則を明文化し、現headのsuccessが監査系CIだけであることを記録した。LeGITのcode状態をofficial-code確認済みからofficial-code unresolvedへ訂正した。外部baseline、J-CRe3、R0.2の新しい数値再現は0件のままであり、能力進歩未認定、高校生級未達を維持する。