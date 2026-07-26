# Intelligence Swarm Backlog

## Operating rule

R0はcanonical branch `research/intelligence-swarm-reconstruction-001`だけで進める。A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。

外部baselineを再現するまで、新規機構族、新しい知能原理、能力進歩、高校生級到達を認定しない。単発失敗で終了せず、失敗分類、根拠、原因だけを変える最小修正、同一budget再run、採用・棄却・停止判定までを1サイクルとする。既に同一screeningが実行中の場合は重複dispatchせず、完了・artifact判定・次の単一原因決定まで追跡する。

## A–D allocation

- **A**: SILG/RTFM、J-CRe3、J-ORA、GPI、Multi-View CRL、ReCITEの公式code・dataset・command・dependency固定と無改変再現。
- **B**: 実装不一致、最適化不足、表現ボトルネック、探索・学習信号不足の診断と制約内最適化。
- **C**: 最新一次文献・公式codeとの重複監査、novelty matrix更新。
- **D**: D015〜D035、matched controls、resource provenance、leakage、RQ-001判定。

## P0 — SILG/RTFM R0.1 screening cycle

固定条件:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- official `multi` recurrent
- seeds `1,7,19`
- `131,072 requested frames`、actual baseline `131,080` frames
- train `silg:rtfm_train_s1-v0`
- test `silg:rtfm_test_s1-v0`

### Completed immutable failure: run 30203026269

- conclusion: qualification failure
- artifact ID: `8633105142`
- artifact digest: `sha256:43ab7f1df82e9eba98c132b2e84a9ec55dbfdd726795fb43f7608fe288e00eef`
- Correct `0/60`、return `-2.0749993`
- Random `4/60`、return `-1.1513333`
- Language-blind `1/60`
- State-only `0/60`
- Language-shuffle `0/60`
- answer leakage: `false`
- same-instance controls: 成立
- classification: `initial_reproduction_failure / optimization_or_policy_competence_failure`

このrunはimmutable evidence保存の前進だが、公開能力baseline再現ではない。

### Active next run: R01-SCREEN-002-E055

- execution request commit: `3648f10c44ceab68891a08d5cf9ca174d739dd74`
- workflow run ID: `30208660095`
- RESET-E056 audit時点: **in progress**
- completed steps: checkout、Python setup、host provenance、pinned source install、generator schema、canonical random/schema probe
- current step: official `multi` recurrent 131,072-frame training

変更する要因は1つだけ:

- `entropy_cost: 0.05 -> 0.005`

固定:

- architecture、source pins、dataset、frames、seeds、split、actors、batch、unroll、matched instances

必須出力:

1. Correct / Random / Language-blind / State-only / Language-shuffleのsame-instance結果。
2. checkpoint bytes・SHA-256・actual frames。
3. model parameters/state bytes、peak RSS、training wall、CPU latency。
4. seed、split、dependency lock、raw logs、artifact digest。
5. answer leakage、schema leakage、prediction provenance。
6. action histogram、valid-action率、policy entropy、episode length、reward到達率。
7. mask前後logit、invalid-action mass、gradient norm、policy/value loss。

採用条件:

- Correct success > 0
- Correct win rate > Random
- Correct return > Random
- 3-seed平均改善かつ最低seedを悪化させない
- language使用案ではLanguage-blind / State-only / Language-shuffleを上回る

棄却条件:

- 同一契約でCorrectがRandomを上回らない、またはCorrect successが0なら、`entropy_cost`単独原因を棄却する。

run完了後の必須処理:

1. job conclusion、artifact ID、artifact digestを取得する。
2. artifact内のqualification、matched predictions、policy diagnostics、resource logs、checksums、leakageを読む。
3. baseline run `30203026269`との差をseed別・平均・最低seedで比較する。
4. 採用条件を満たさなければentropy単独原因を棄却する。
5. 最初のactionable failureを1件だけ選び、次の単一原因screening contractを同じbranchへ発行する。
6. artifact欠損なら性能仮説へ進まず、upload path / `always()` / cancellation / retentionを単一原因として修復する。

次の原因順序:

1. official evaluation/default parity
2. recurrent reset/detach、optimizer/checkpoint restore
3. learning rate、gradient clipping、unroll
4. parameter数±2%以内の容量配分
5. language/state fusion位置

最大6 screening runまたは事前停止条件まで継続する。「検証したが駄目」でcycleを閉じない。

## P0 — Evaluation contract freeze

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。

毎runで、matched random/language-blind/state-only/applicable shuffle、model/checkpoint bytes、peak RSS、training runtime、CPU latency、seed、split、actual frames、commit、dependency、raw logs、checksums、leakageを保存する。監査codeの回帰成功は数値baseline再現には数えない。

## P1 — J-CRe3

一次論文はUeda et al., LREC-COLING 2024、公式repositoryは `riken-grp/J-CRe3`。

1. exact commit、dataset、license、容量、checksumを固定する。
2. official baseline、dependency、evaluation commandを無改変で実行する。
3. model bytes、RSS、runtime、seed、split、prediction、raw log、checksumを保存する。
4. random、text-only、vision-only、mention-shuffle、frame/object-shuffleを事前登録する。
5. 失敗分類と最小修正を行い、単発失敗で終了しない。

J-CRe3は日本語multimodal reference resolution baselineであり、SILGのinteractive policy competenceを代替しない。

## P1 — ReCITE official-code reproduction

Saklad et al., ACL 2026のReCITEは実世界textから因果関係を抽出・推論するbenchmarkであり、hidden intervention-target recoveryやinteractive policy competenceとは別列で扱う。

1. exact commit、dataset release、license、checksum、task schemaを固定する。
2. official evaluation commandとreported splitを無改変で再現する。
3. model、prompt、temperature、seed、runtime、peak RSS、raw predictions、scoreを保存する。
4. random label、entity/order shuffle、causal-marker masking、sentence shuffle、retrieval-onlyを事前登録する。
5. 失敗時は単一原因rerunへ接続する。

## P1 — Multi-View CRL official-code reproduction

Yao et al., ICLR 2024の公式repository `CausalLearningAI/multiview-crl` を対象とする。exact commit・environment・dataset checksumを固定し、official three-view実験とtext/image removal、text/cross-instance shuffle、random representationを比較する。

## P1 — GPI official-software reproduction

canonical repository、PyPI、documentation version、exact commitを固定し、text-as-treatment公開exampleを無改変再現する。representationなし、random、shuffle、alternative frozen representationをmatched比較する。

## P1 — C3 Regularization official-code audit

Wang et al., ICML 2025 **Towards the Causal Complete Cause of Multi-Modal Representation Learning** と公式code link `WangJingyao07/Multi-Modal-Base` をC035として扱う。

1. exact commit、license、dependency、dataset、pretrained weightsの有無を固定する。
2. paperの主表に対応するofficial commandを特定する。
3. causal sufficiency、causal necessity、C3 risk、最終task metricを保存する。
4. no-C3、randomized counterfactual branch、instrument-shuffle、modality-shuffleをmatched比較する。
5. model bytes、RSS、runtime、seed、split、raw output、checksumを保存する。
6. 数値再現までは、C3を本研究の能力証拠に数えない。

## P1 — MCDRL official-code audit

Liang et al., CVPR 2026 **Multimodal Causality-Driven Representation Learning for Generalizable Medical Image Segmentation** をC036として扱う。

1. CVPR版論文、supplement、project page、author repositoryを突合する。
2. official codeが確認できた場合だけexact commit、license、dependency、dataset、pretrained weights、主表commandを固定する。
3. text-defined confounder dictionary、causal intervention network、domain-generalization metricを記録する。
4. no-text-confounder、dictionary shuffle、intervention-off、image-only、prompt shuffleをmatched controls候補として事前登録する。
5. model bytes、RSS、runtime、seed、split、raw output、checksumを保存する。
6. 医用segmentation domain generalizationをhidden intervention-target groundingやinteractive policy competenceの証拠として流用しない。

## P1 — R0.2 Environment-first

immutable R0.1 competence bundleが `qualified_for_r02=true` を満たした後のみ開始する。Environment-first、parameter-matched End-to-end、State-onlyを比較し、source policy competence、3-seed平均改善、最低seed非悪化、next-state prediction、action accuracy、online task successを確認する。

## Closed — R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず棄却維持する。

## Prior-art and RQ-001

既存境界として、score-based CRL、有限標本CRL、Markham et al.、Baumgartner et al.、LeGIT、GPI、Multi-View CRL、CmIR、ReCITE、C3 Regularization、MCDRLを維持する。

C3 Regularizationにより、multimodal representationの因果的十分性・必要性、instrumental variableを用いたC3 risk、counterfactual twin branch、plug-and-play regularizationは既存境界へ含める。MCDRLにより、text-defined confounder dictionary、multimodal causal intervention、domain-confounder removal、OOD segmentation generalizationも既存境界へ含める。これらだけではRQ-001を採用しない。

- 広義RQ-001: **棄却**
- 狭義RQ-001: **追加狭域化・未採用**

採用には、既存baselineを差し引いた後にも残るlanguage固有追加情報、countermodel pair、joint recoding不能な外部denotation law、事前登録済みclaim/counterexample/stopping ruleが必要。

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Status

- immutable R0.1 bundle: **1件・不合格**
- 外部baseline再現: **0件**
- 新規機構族: **未認定**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- 完成: **false**
