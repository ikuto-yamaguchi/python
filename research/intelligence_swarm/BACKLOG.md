# Intelligence Swarm Backlog

## Operating rule

R0は、固定資源制約下で公開baselineを再現し、失敗原因を一つずつ潰して性能を最大化する。

- canonical branchは`research/intelligence-swarm-reconstruction-001`のみ。
- A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。
- 既存stacked draft PRはnegative-results archiveであり、新作業のbaseにしない。
- 単発失敗で終了しない。原因分類、最小修正、同一budget再run、停止判定までを1サイクルとする。
- 外部baseline再現までは新しい機構族、知能原理、能力進歩、高校生級到達を認定しない。

## A–D allocation

- **A**: SILG/RTFM、J-CRe3、J-ORAの公式code・dataset・command・dependency固定と無改変再現。
- **B**: 実装不一致、最適化不足、表現ボトルネック、探索/学習信号不足の診断と、原因だけを変える最小run。
- **C**: 最新一次文献・公式codeの重複監査とnovelty matrix更新。文献追加だけでは完了しない。
- **D**: D015〜D035、matched controls、resource provenance、leakage、RQ-001判定。

## P0 — SILG/RTFM competence recovery

固定条件:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- official `multi` recurrent
- seeds `1,7,19`
- primary budget `131,072 requested frames`

現accepted evidenceは32,768 requested framesのみ。Correct `1/60`、Random `4/60`であり、公開能力baseline未達。

次の実行順:

1. canonical split-jobでR0.1を実行する。
2. R0.1直後にcheckpoint、prediction、resource、raw log、checksumをfreeze/uploadする。
3. actual frame、seed、split、initial instance identityを検証する。
4. preserved bundleへD015〜D035を適用する。
5. CorrectがRandomを下回る原因をaction histogram、valid-action率、entropy、episode長、reward到達率、mask前後logit、recurrent reset/detachで分類する。
6. 診断結果からofficial family内で最大6 screening runを行う。
7. 有望案だけseeds `1,7,19`へ昇格する。

最適化順:

1. config、dependency、frame counting、mask、termination、checkpoint restore差分。
2. recurrent reset/detach、optimizer restore。
3. learning rate、entropy coefficient、unroll、gradient clipping。
4. parameter数±2%以内のstate/language/recurrent/fusion容量配分。
5. early/recurrent-input/late fusion。

採用条件:

- 同一frame・parameter budget。
- 3-seed平均改善。
- 最低seed非悪化。
- CorrectがRandomを上回る。
- language使用案はlanguage-blind/state-only/shuffleを上回る。

失敗runは、次runの変更変数、固定変数、反証条件、停止条件を記録するまで未完了。

## P0 — Evaluation contract freeze

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。

毎runで保存する:

- random/language-blind/state-only/applicable shuffle controls
- identical initial instances
- model/checkpoint bytes
- peak RSS
- training wall time and CPU latency
- seed/split/actual frame count
- exact config/commit/dependency
- raw logs/checksums
- leakage findings

## P1 — J-CRe3

- 一次論文: Ueda et al., LREC-COLING 2024
- 公式repository: `riken-grp/J-CRe3`

次の実行順:

1. exact commit固定。
2. dataset、license、容量、checksum記録。
3. official baselineとevaluation command確認。
4. 無改変数値再現。
5. model/RSS/runtime/seed/split/prediction/log/checksum保存。
6. random、text-only、vision-only、mention-shuffle、frame/object-shuffleを事前登録。
7. 失敗を実装、最適化、表現、データへ分類し、原因だけを変えて再run。

J-CRe3はSILGのinteractive policy competenceを代替しない。

## P1 — J-ORA adjacent audit

J-ORAは日本語ロボット知覚のobject identification、reference resolution、next-action predictionを扱う隣接benchmarkである。

1. peer-reviewed statusと最新版を確認。
2. official project、code、dataset、license、split、evaluation commandを固定。
3. J-CRe3とのtask・annotation・model overlap matrixを作る。
4. attribute情報あり/なしの改善をprior-art境界へ反映する。
5. official artifactが再現可能な場合だけnumerical reproductionへ追加する。

## P1 — R0.2 Environment-first

immutable R0.1 competence bundle通過後のみ開始する。

比較:

- Environment-first
- parameter-matched End-to-end
- State-only

採用条件はsource policy competence、3-seed平均改善、最低seed非悪化、next-state prediction・action accuracy・online task successのうち2指標以上の整合。

## Closed — R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず棄却維持する。

## Prior-art and RQ-001

各回、最新一次文献と公式code、再現進捗、matched controls、model/RSS/runtime/seed/split、leakage、RQ-001条件を確認する。

2026 finite-sample CRLにより、少数の未知multi-node interventionからlatent graph、mixing、representation、unknown targetを有限標本で回復できる領域が示された。unknown target、少数environment、finite-sample recoveryだけではRQ-001を採用しない。

- 広義RQ-001: **棄却**
- 狭義RQ-001: **未採用**

採用には、最強の非言語baseline再現、residual countermodel pair、externally fixed anti-recoding law、language固有の追加情報の直接証拠、事前登録済みclaim/counterexample/stopping ruleが必要。

## Stage transition

次stageは以下すべての完了後だけ提案する。

1. competent external public baseline
2. immutable matched controls
3. canonical three-seed qualification
4. qualified R0.2 comparison
5. R0.3 rejection維持
6. novelty matrix完了
7. 中心命題の事前登録完了

## Status

- 新規機構族: **未認定**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- 完成: **false**
