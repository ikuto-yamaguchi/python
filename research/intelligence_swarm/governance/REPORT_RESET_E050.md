# RESET-E050 — R0 Research Reconstruction Integration

Date: 2026-07-26
Branch: `research/intelligence-swarm-reconstruction-001`

## Scope

A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。公開benchmark再現、prior-art audit、evaluation contract、hidden intervention-target ablationだけを同じcanonical branchへ累積する。既存stacked draft PRはnegative-results archiveであり、新作業のbaseにしない。

## Required six-point review

1. **最新一次文献と公式codeの重複監査**
   - J-CRe3、score-based CRL、有限標本CRL、CLeaR 2026、LeGITの境界を維持した。
   - Imai & NakamuraのGPI系研究と公開softwareを追加した。
   - 生成AI内部表現をtext/image/videoのtreatment・confounder表現として利用し、生成データ、overlap改善、double machine learningへ接続すること自体は新規性候補から除外した。
   - GPIはinteractive policy learningやhidden intervention-target recoveryを直接扱わないため、SILG/J-CRe3とは別列の再現対象とした。

2. **SILG/J-CRe3等の再現進捗**
   - immutable 131,072-frame R0.1 bundle: 0件。
   - 学習済み公開能力baseline再現: 0件。
   - J-CRe3 numerical reproduction: 0件。
   - GPI official-software reproduction: 0件。
   - R0.2正式再現: 0件。

3. **Controls**
   - SILG: random、language-blind、state-only、language-shuffleをsame-instanceで要求する。
   - J-CRe3: random、text-only、vision-only、mention-shuffle、frame/object-shuffleを要求する。
   - GPI: representationなし、random representation、shuffled representation、frozen alternative representationを要求する。

4. **Resources and provenance**
   - model/checkpoint bytes、peak RSS、training/evaluation runtime、CPU latency、seed、split、actual frames、commit、dependency、raw logs、checksumsを必須とする。
   - GPIはeffect estimate、standard error、package version、model、example dataも保存する。

5. **Leakage**
   - D015〜D035を凍結する。
   - 実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。
   - 監査codeの回帰成功は能力進歩に数えない。

6. **RQ-001 decision**
   - 広義RQ-001: 棄却。
   - 狭義RQ-001: 追加狭域化・未採用。
   - 判定: **NARROWED BEYOND LANGUAGE-GUIDED TARGET SELECTION, INTERVENTION-CONDITIONED COMPOSITION, AND GENERATIVE-REPRESENTATION CAUSAL INFERENCE — NOT ADOPTED**。

## Non-termination and performance-maximization contract

失敗runは「検証したが駄目」で終了しない。以下が揃うまで未完了とする。

- metric/log/code差分に基づくfailure class
- 固定条件と変更する単一原因
- 同一budget・split・instance・model familyでのmatched rerun
- 採用・棄却・停止条件
- 停止条件未達時の次screening contract

SILGのscreening順は、official差分、recurrent/optimizer、learning rate・entropy・unroll・gradient clipping、parameter数±2%以内の容量配分、fusion位置とする。最大6件のscreening runを許可し、有望案だけseeds `1/7/19`へ昇格する。

## GPI reproduction contract

GPIは新しい機構族ではなく、prior-art境界を閉じるための公式software再現である。

1. canonical repository、PyPI release、documentation versionを固定する。
2. exact commit、package version、license、dependency、example data、commandを保存する。
3. text-as-treatmentの最小公開exampleを無改変で再現する。
4. effect estimate、standard error、runtime、peak RSS、model、seed、split、raw output、checksumを保存する。
5. matched controlsを追加する。
6. 成功してもinteractive policy competenceやhidden intervention-target recoveryの証拠へ流用しない。

## Stage gate

次stageは、R0.1〜R0.3、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Formal status

- 新規機構族: 未認定
- 新規知能原理: 未発見
- 能力進歩: 未認定
- 高校生級知能: 未達
- 完成: false
