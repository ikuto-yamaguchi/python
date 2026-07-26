# Intelligence Swarm Backlog

## Operating rule

R0はcanonical branch `research/intelligence-swarm-reconstruction-001`だけで進める。A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。

外部baselineを再現するまで、新規機構族、新しい知能原理、能力進歩、高校生級到達を認定しない。単発失敗で終了せず、失敗分類、根拠、原因だけを変える最小修正、同一budget再run、採用・棄却・停止判定までを1サイクルとする。

## A–D allocation

- **A**: SILG/RTFM、J-CRe3、J-ORAの公式code・dataset・command・dependency固定と無改変再現。
- **B**: 実装不一致、最適化不足、表現ボトルネック、探索・学習信号不足の診断と制約内最適化。
- **C**: 最新一次文献・公式codeとの重複監査、novelty matrix更新。
- **D**: D015〜D035、matched controls、resource provenance、leakage、RQ-001判定。

## P0 — SILG/RTFM competence recovery

固定条件:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- official `multi` recurrent
- seeds `1,7,19`
- primary budget `131,072 requested frames`

現accepted evidenceは32,768 framesのみ。Correct `1/60`、Random `4/60`、Language-blind / State-only / Language-shuffle `1/60`であり、competent public baselineではない。

### E045 next execution

1. canonical split-jobでR0.1だけを実行する。
2. R0.1終了直後にcheckpoint、prediction、resource、raw log、dependency lock、checksumを保存する。
3. requested framesとactual environment steps、seed、split、initial instance identityを検証する。
4. D015〜D035を保存済みbundleへ適用する。
5. seedごとにaction histogram、valid-action率、policy entropy、episode length、reward到達率、mask前後logit、invalid-action mass、gradient norm、policy/value lossを保存する。
6. recurrent reset/detach、optimizer restore、termination、frame counting、mask、checkpoint restoreを公式実装と比較する。
7. Correct / Random / Language-blind / State-only / Language-shuffleを同一instanceで評価する。
8. 失敗を `implementation_mismatch`、`optimization_failure`、`representation_bottleneck`、`exploration_or_signal_failure`、`artifact_failure` のいずれかへ分類する。
9. 原因だけを変える最大6件のscreening runを行い、有望案だけseeds `1,7,19`へ昇格する。

最適化順は、公式差分除去、recurrent/optimizer修復、learning rate・entropy・unroll・gradient clipping、parameter数±2%以内の容量配分、fusion位置の順とする。

採用には同一frame・parameter budget、3-seed平均改善、最低seed非悪化、Correct>Random、language使用案ではlanguage-blind/state-only/shuffle超過を要求する。

## P0 — Evaluation contract freeze

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。

毎runで、matched random/language-blind/state-only/applicable shuffle、model/checkpoint bytes、peak RSS、training runtime、CPU latency、seed、split、actual frames、commit、dependency、raw logs、checksums、leakageを保存する。

監査CI、文書更新、queued/cancelled runは能力進歩に数えない。

## P1 — J-CRe3

一次論文はUeda et al., LREC-COLING 2024、公式repositoryは `riken-grp/J-CRe3`。

1. exact commit、dataset、license、容量、checksumを固定する。
2. official baseline、dependency、evaluation commandを無改変で実行する。
3. model bytes、RSS、runtime、seed、split、prediction、raw log、checksumを保存する。
4. random、text-only、vision-only、mention-shuffle、frame/object-shuffleを事前登録する。
5. 失敗分類と最小修正を行い、単発失敗で終了しない。

J-CRe3は日本語multimodal reference resolution baselineであり、SILGのinteractive policy competenceを代替しない。

## P1 — R0.2 Environment-first

immutable R0.1 competence bundle通過後のみ開始する。Environment-first、parameter-matched End-to-end、State-onlyを比較し、source policy competence、3-seed平均改善、最低seed非悪化、next-state prediction、action accuracy、online task successを確認する。

## Closed — R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず棄却維持する。

## Prior-art and RQ-001

2025 score-based CRLに加え、2026年3月の有限標本CRLは、対数個の未知multi-node intervention環境からlatent graph、mixing matrix、representation、unknown intervention targetsを有限標本で回復できる条件を示す。unknown target、少数environment、finite-sample recoveryだけではRQ-001を採用しない。

- 広義RQ-001: **棄却**
- 狭義RQ-001: **未採用**

採用には、最強の非言語公式baseline再現後にも残るcountermodel pair、externally fixedでjoint recoding不能なdenotation law、language固有追加情報の直接証拠、事前登録済みclaim/counterexample/stopping ruleが必要。

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Status

- 外部baseline再現: **0件**
- 新規機構族: **未認定**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- 完成: **false**