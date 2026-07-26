# RESET-E049 — R0 Research Reconstruction Governance

## Scope

Canonical branch `research/intelligence-swarm-reconstruction-001`のみを更新する。A〜Dは新しいtoy仮説、別branch、新規機構族を作らず、公開benchmark再現、prior-art audit、evaluation contract、hidden intervention-target ablationだけを累積する。既存stacked draft PRはnegative-results archiveであり、新作業のbaseにしない。

## Evidence inspected

- PR #409はopen、draft、mergeable。
- inspected head: `dba26a23a67f05712ae83143d99107f9effd5702`。
- このheadに紐づく取得可能なpull-request-triggered workflowは以下の3本で、すべてsuccess。
  - R0 prediction method topology tests: `30192898489`
  - R0 unified acceptance gate tests: `30192898458`
  - R0 artifact path containment tests: `30192898479`
- このAPI結果はpull-request-triggered runに限定されるため、push型R0.1 workflowが存在しない証拠にはしない。
- 受理可能な131,072-frame R0.1 artifact、qualification JSON、J-CRe3 numerical result、qualified R0.2 resultは確認できていない。

## Execution decision

RESET-E049 headから `R01_RUN_REQUEST.json` を再発行する。R0.1の開始・完了・成功は、run ID、job conclusion、artifact ID、qualification JSONを確認した場合だけ認定する。

失敗bundleでも以下を保存する。

1. source/model/data commit
2. seeds `1/7/19`、split、actual frames
3. Correct / Random / Language-blind / State-only / Language-shuffleのsame-instance結果
4. model/checkpoint bytes、peak RSS、training runtime、CPU latency
5. raw logs、dependency lock、SHA-256 manifest
6. leakage判定
7. action histogram、valid-action率、entropy、episode長、reward到達率
8. mask前後logit、invalid-action mass、gradient norm、policy/value loss
9. failure classificationとevidence
10. 次に変更する単一原因、固定変数、matched rerun、停止条件

「検証したが駄目だった」でcycleを閉じることは禁止する。停止条件を満たさない限り、最大6件のscreening orderを継続する。

## Prior-art audit

- Markham et al., CLeaR 2026のPMLR正式掲載を確認した。介入型context moduleによりblack-box generative modelで因果的disentanglementとOOD compositionを扱うため、context-conditioned intervention、causal concept disentanglement、compositional reuse自体はRQ-001の新規性候補から除外する。
- PMLR掲載ページでは公式repositoryを確認できなかった。状態は `paper/PMLR verified; official code unresolved`。
- J-CRe3はLREC-COLING 2024の日本語実世界reference-resolution benchmarkであり、SILG interactive policy competenceの代替にはしない。
- 2025 score-based CRLおよび2026 finite-sample CRLにより、unknown intervention target、少数environment、finite-sample recoveryだけではRQ-001を採用しない。

## RQ-001 decision

> **NARROWED BEYOND LANGUAGE-GUIDED TARGET SELECTION AND INTERVENTION-CONDITIONED COMPOSITION — NOT ADOPTED**

採用には、最強の非言語baseline、language-guided target-selection baseline、intervention-context composition baselineの再現後にも残るcountermodel pair、externally fixedでjoint recoding不能なdenotation law、language固有の追加情報、事前登録済みclaim/counterexample/stopping ruleが必要。

## Formal status

- immutable R0.1 competence bundle: **0**
- learned external baseline reproduction: **0**
- J-CRe3 numerical reproduction: **0**
- qualified R0.2: **0**
- R0.3 hidden intervention-target ablation: **rejected**
- broad RQ-001: **rejected**
- narrowed RQ-001: **not adopted**
- novelty matrix: **incomplete**
- central claim preregistration: **incomplete**
- new mechanism family: **not recognized**
- new intelligence principle: **none**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next-stage proposal: **none**