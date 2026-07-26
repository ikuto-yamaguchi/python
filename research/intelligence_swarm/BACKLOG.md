# Intelligence Swarm Backlog

## Operating rule

R0はcanonical branch `research/intelligence-swarm-reconstruction-001`だけで進める。A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。

外部baselineを再現するまで、新規機構族、新しい知能原理、能力進歩、高校生級到達を認定しない。単発失敗で終了せず、失敗分類、根拠、原因だけを変える最小修正、同一budget再run、採用・棄却・停止判定までを1サイクルとする。

## A–D allocation

- **A**: SILG/RTFM、J-CRe3、J-ORA、GPI、Multi-View CRL、ReCITEの公式code・dataset・command・dependency固定と無改変再現。
- **B**: 実装不一致、最適化不足、表現ボトルネック、探索・学習信号不足の診断と制約内最適化。
- **C**: 最新一次文献・公式codeとの重複監査、novelty matrix更新。
- **D**: D015〜D035、matched controls、resource provenance、leakage、RQ-001判定。

## P0 — Complete and qualify active SILG/RTFM R0.1 run

固定条件:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- official `multi` recurrent
- seeds `1,7,19`
- primary budget `131,072 requested frames`

現accepted evidenceは32,768 framesのみ。Correct `1/60`、Random `4/60`、Language-blind / State-only / Language-shuffle `1/60`であり、competent public baselineではない。

### Active run evidence

- run ID: `30203026269`
- run number: `285`
- workflow head: `5d9f137296a64fc401560356470ac27f520cbeff`
- job: `r01-public-reproduction`
- completed: source install、generator-signature test、random control、schema probe
- locator capture時点: official multi recurrent 131,072-frame training **in progress**
- artifact: **0件**

### Immediate execution contract

1. run `30203026269`のjob conclusionを取得する。
2. 成否にかかわらず、artifact ID、checkpoint、matched result、resource、raw log、dependency lock、checksum、qualification JSONを取得する。
3. artifactが0件のまま終了した場合は `implementation_or_artifact_failure` として、upload境界・`always()`条件・disk path・job cancellation/concurrencyを最初の単一原因候補にする。
4. artifactが存在する場合は `qualify_r01_source_policy.py` でsource pins、seeds、actual frames、checkpoint完成、same-instance controls、answer leakage、Correct対Randomをfail-closed確認する。
5. `Correct <= Random` またはCorrect success zeroの場合は、action histogram、valid-action率、entropy、episode length、reward到達率、mask前後logit、invalid-action mass、gradient norm、policy/value lossから最初のactionable failureを1件だけ選ぶ。
6. 不合格ならR0.2を開始しない。R0.2側でもdownloadしたqualification JSONを再検証する。
7. 不合格bundleにはfailure list、failure class、固定条件、診断項目、単一変更制約、matched再試験、停止条件を保存する。
8. 原因だけを変える最大6 screening runを同一frames・split・instances・model familyで実施する。
9. 有望候補だけseeds `1,7,19`へ昇格する。
10. 失敗runは次の単一原因候補とmatched rerunを発行するまで未完了とし、「検証したが駄目」で閉じない。
11. runの進捗はrun ID、job conclusion、artifact ID、qualification JSON、checksum manifestでのみ認定する。

最適化順は、公式差分除去、recurrent/optimizer修復、learning rate・entropy・unroll・gradient clipping、parameter数±2%以内の容量配分、fusion位置の順とする。

採用には同一frame・parameter budget、3-seed平均改善、最低seed非悪化、Correct>Random、language使用案ではlanguage-blind/state-only/shuffle超過を要求する。

## P0 — Evaluation contract freeze

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。

毎runで、matched random/language-blind/state-only/applicable shuffle、model/checkpoint bytes、peak RSS、training runtime、CPU latency、seed、split、actual frames、commit、dependency、raw logs、checksums、leakageを保存する。

監査codeの回帰成功は数値baseline再現には数えない。

## P1 — J-CRe3

一次論文はUeda et al., LREC-COLING 2024、公式repositoryは `riken-grp/J-CRe3`。

1. exact commit、dataset、license、容量、checksumを固定する。
2. official baseline、dependency、evaluation commandを無改変で実行する。
3. model bytes、RSS、runtime、seed、split、prediction、raw log、checksumを保存する。
4. random、text-only、vision-only、mention-shuffle、frame/object-shuffleを事前登録する。
5. 失敗分類と最小修正を行い、単発失敗で終了しない。

J-CRe3は日本語multimodal reference resolution baselineであり、SILGのinteractive policy competenceを代替しない。

## P1 — ReCITE official-code reproduction

Saklad et al., ACL 2026のReCITEは、実世界textから因果関係を抽出・推論するbenchmarkであり、公式code/dataは `Ryan-Saklad/ReCITE` と報告されている。hidden intervention-target recoveryやinteractive policy competenceとは別列で扱う。

1. exact commit、dataset release、license、checksum、task schemaを固定する。
2. official evaluation commandとreported splitを無改変で再現する。
3. model、prompt、temperature、seed、split、runtime、peak RSS、raw predictions、score、checksumを保存する。
4. random label、entity/order shuffle、causal-marker masking、sentence shuffle、retrieval-only baselineを事前登録する。
5. 成功してもlanguage-only causal relation extractionをRQ-001のhidden-target grounding証拠へ流用しない。
6. 失敗時はdataset、model access、prompt/evaluation、parser、artifactのいずれかへ分類し、単一原因rerunへ接続する。

## P1 — Multi-View CRL official-code reproduction

Yao et al., ICLR 2024の公式repositoryは `CausalLearningAI/multiview-crl`。

1. exact commit、MIT license、`env.yaml`、tokenizer assets、numerical/multimodal commandを固定する。
2. numerical experimentを無改変でtrain/evaluateし、raw output、model bytes、peak RSS、runtime、seed、dependency、checksumを保存する。
3. Multimodal3DIdentのdataset version、download source、archive checksum、展開後manifestを固定する。
4. official three-view `(img0,img1,txt0)` experimentを無改変で実行する。
5. text-view removal、image-view removal、text shuffle、cross-instance view shuffle、random representationを事前登録する。
6. 失敗時はenvironment、dataset、training stability、evaluation、artifactのいずれかへ分類し、原因だけを変えるrerunへ接続する。

## P1 — GPI official-software reproduction

1. canonical repository、PyPI release、documentation versionを固定する。
2. exact commit、package version、license、dependency、example data、commandを保存する。
3. text-as-treatmentの最小公開exampleを無改変で再現する。
4. effect estimate、standard error、runtime、peak RSS、model、seed、split、raw output、checksumを保存する。
5. representationなし、random representation、shuffled representation、frozen alternative representationのmatched controlを追加する。
6. 失敗時はdependency/model access、representation extraction、overlap/propensity、estimator、artifactのいずれかへ分類し、単一原因rerunへ接続する。

## P1 — R0.2 Environment-first

immutable R0.1 competence bundleが `qualified_for_r02=true` を満たした後のみ開始する。Environment-first、parameter-matched End-to-end、State-onlyを比較し、source policy competence、3-seed平均改善、最低seed非悪化、next-state prediction、action accuracy、online task successを確認する。

## Closed — R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず棄却維持する。

## Prior-art and RQ-001

既存境界として、score-based CRL、有限標本CRL、Markham et al.、Baumgartner et al.、LeGIT、GPI、Multi-View CRLを維持する。

Mai & Han, ACL 2026のCmIRにより、multimodal invariant/spurious decomposition、環境横断の安定予測、mutual-information/reconstruction制約付き因果不変表現だけでは新規性を認定しない。author-official codeは未固定。

Saklad et al., ACL 2026のReCITEにより、language-only causal-relation extraction/inferenceをhidden intervention-target groundingと混同しない。公式repository exact commitと再現は未完了。

### Required prior-art actions

1. CmIRのauthor-official repository公開有無を監査する。
2. `Ryan-Saklad/ReCITE` のexact commit、dataset、command、reported metricsを固定して無改変再現する。
3. Markham、Baumgartner、LeGITのauthor-official repository公開有無を継続監査する。
4. GPIとMulti-View CRLの公式再現を進める。
5. 各論文上の性能値を本研究の能力証拠へ流用しない。
6. RQ-001採用候補は、既存のlanguage-only causal extraction、multimodal invariance、target selection、context composition、生成表現利用、multi-view recovery、trajectory identificationを差し引いた後に残るlanguage固有追加情報だけに限定する。

- 広義RQ-001: **棄却**
- 狭義RQ-001: **追加狭域化・未採用**

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Status

- 外部baseline再現: **0件**
- 新規機構族: **未認定**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- 完成: **false**