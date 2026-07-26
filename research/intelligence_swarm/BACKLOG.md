# Intelligence Swarm Backlog

## Operating rule

R0はcanonical branch `research/intelligence-swarm-reconstruction-001`だけで進める。A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。

外部baselineを再現するまで、新規機構族、新しい知能原理、能力進歩、高校生級到達を認定しない。単発失敗で終了せず、失敗分類、根拠、原因だけを変える最小修正、同一budget再run、採用・棄却・停止判定までを1サイクルとする。

## A–D allocation

- **A**: SILG/RTFM、J-CRe3、J-ORAの公式code・dataset・command・dependency固定と無改変再現。
- **B**: 実装不一致、最適化不足、表現ボトルネック、探索・学習信号不足の診断と制約内最適化。
- **C**: 最新一次文献・公式codeとの重複監査、novelty matrix更新。
- **D**: D015〜D035、matched controls、resource provenance、leakage、RQ-001判定。

## P0 — Execute and qualify SILG/RTFM R0.1

固定条件:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- official `multi` recurrent
- seeds `1,7,19`
- primary budget `131,072 requested frames`

現accepted evidenceは32,768 framesのみ。Correct `1/60`、Random `4/60`、Language-blind / State-only / Language-shuffle `1/60`であり、competent public baselineではない。

### Immediate execution contract

1. canonical split-jobでR0.1を実行する。
2. 成否にかかわらずR0.1終了直後にcheckpoint、matched result、resource、raw log、dependency lock、checksum、qualification JSONを保存する。
3. `qualify_r01_source_policy.py`で以下をfail-closed確認する。
   - source pins
   - seeds `1/7/19`
   - requested framesとcheckpoint actual frames
   - 全seed checkpoint完成
   - Correct / Random / Language-blind / State-only / Language-shuffleの存在
   - same initial instance stream
   - answer leakageが明示的にfalse
   - Correctのwin rateとreturnがRandomを上回る
4. 不合格ならR0.2を開始しない。R0.2側でもdownloadしたqualification JSONを再検証する。
5. 不合格bundleにはfailure list、`implementation_or_artifact_failure` または `optimization_or_policy_competence_failure`、固定条件、診断項目、単一変更制約、matched再試験、停止条件を保存する。
6. action histogram、valid-action率、policy entropy、episode length、reward到達率、mask前後logit、invalid-action mass、gradient norm、policy/value lossをseed別に追加保存する。
7. official command/defaultsとdeterminism patch、recurrent reset/detach、optimizer、termination、frame counting、mask、checkpoint restoreの差を診断する。
8. 原因だけを変える最大6 screening runを実施する。各runは同一frames、seeds/split、instances、model familyを維持する。
9. 有望候補だけseeds `1,7,19`へ昇格する。
10. governanceや監査文書の更新だけでiterationを閉じない。次の数値run requestを同じ統合内で発行する。

最適化順は、公式差分除去、recurrent/optimizer修復、learning rate・entropy・unroll・gradient clipping、parameter数±2%以内の容量配分、fusion位置の順とする。

採用には同一frame・parameter budget、3-seed平均改善、最低seed非悪化、Correct>Random、language使用案ではlanguage-blind/state-only/shuffle超過を要求する。

## P0 — Evaluation contract freeze

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。

毎runで、matched random/language-blind/state-only/applicable shuffle、model/checkpoint bytes、peak RSS、training runtime、CPU latency、seed、split、actual frames、commit、dependency、raw logs、checksums、leakageを保存する。

監査CI、文書更新、queued/cancelled runは能力進歩に数えない。現headで確認できたworkflowはartifact-path、unified-acceptance、prediction-topologyの監査系successのみであり、R0.1数値再現とは扱わない。

## P1 — J-CRe3

一次論文はUeda et al., LREC-COLING 2024、公式repositoryは `riken-grp/J-CRe3`。

1. exact commit、dataset、license、容量、checksumを固定する。
2. official baseline、dependency、evaluation commandを無改変で実行する。
3. model bytes、RSS、runtime、seed、split、prediction、raw log、checksumを保存する。
4. random、text-only、vision-only、mention-shuffle、frame/object-shuffleを事前登録する。
5. 失敗分類と最小修正を行い、単発失敗で終了しない。

J-CRe3は日本語multimodal reference resolution baselineであり、SILGのinteractive policy competenceを代替しない。

## P1 — R0.2 Environment-first

immutable R0.1 competence bundleが `qualified_for_r02=true` を満たした後のみ開始する。Environment-first、parameter-matched End-to-end、State-onlyを比較し、source policy competence、3-seed平均改善、最低seed非悪化、next-state prediction、action accuracy、online task successを確認する。

## Closed — R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず棄却維持する。

## Prior-art and RQ-001

2025 score-based CRLと2026年3月有限標本CRLにより、unknown target、少数environment、finite-sample recoveryだけではRQ-001を採用しない。

LeGITは、自然言語のvariable meta-informationとLLM世界知識を使ってonline causal discovery初期のintervention targetを選び、数値的選択をwarm-startする。したがって以下を新規性候補から除外する。

- language descriptionから介入候補を選ぶこと
- low-data初期局面をLLMでwarm-startすること
- language/world knowledgeと数値的causal discoveryを組み合わせること
- target-selection改善だけをlanguage grounding原理とみなすこと

### LeGIT code-status correction

project pageには`Code`表記があるが、2026-07-26時点の監査では公開repository URLへ解決できず、OpenReviewにも公式code URLは提示されていない。したがって「公式コード確認済み」ではなく、**paper/project-page確認済み・official code unresolved**とする。exact commit、dependency、prompt、split、seed、raw output、checksumの固定は未着手であり、再現可能な外部baselineには数えない。

Required next prior-art action:

1. 著者またはproject pageが公開するcanonical repository URLを特定する。
2. URLが特定できなければcode-unavailableとしてnovelty matrixへ明記し、論文記載だけを境界監査へ用いる。
3. repositoryが得られた場合のみexact commit、dependency、prompt、benchmark split、seed、raw output、checksumを固定する。
4. Asia、Child、Insurance、Alarmの少なくとも1つでofficial target-selection baselineをimmutable再現する。
5. random、numerical-only、LLM-only、meta-information shuffleを同一budgetで比較する。
6. 再現前はLeGIT由来の能力差を本研究の証拠へ流用しない。

- 広義RQ-001: **棄却**
- 狭義RQ-001: **追加狭域化・未採用**

採用には、最強の非言語baselineとLeGIT型baselineの再現後にも残るcountermodel pair、externally fixedでjoint recoding不能なdenotation law、target selectionを超えるlanguage固有追加情報の直接証拠、事前登録済みclaim/counterexample/stopping ruleが必要。

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Status

- 外部baseline再現: **0件**
- 新規機構族: **未認定**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- 完成: **false**