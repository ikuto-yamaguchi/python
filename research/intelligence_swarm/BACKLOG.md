# Intelligence Swarm Backlog

## Operating rule

R0はcanonical branch `research/intelligence-swarm-reconstruction-001`だけで進める。A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。

外部baselineを再現するまで、新規機構族、新しい知能原理、能力進歩、高校生級到達を認定しない。単発失敗で終了せず、失敗分類、根拠、原因だけを変える最小修正、同一budget再run、採用・棄却・停止判定までを1サイクルとする。

## A–D allocation

- **A**: SILG/RTFM、J-CRe3、J-ORA、GPI、Multi-View CRLの公式code・dataset・command・dependency固定と無改変再現。
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
3. `qualify_r01_source_policy.py`でsource pins、seeds、actual frames、checkpoint完成、matched controls、answer leakage、Correct対Randomをfail-closed確認する。
4. 不合格ならR0.2を開始しない。R0.2側でもdownloadしたqualification JSONを再検証する。
5. 不合格bundleにはfailure list、failure class、固定条件、診断項目、単一変更制約、matched再試験、停止条件を保存する。
6. action histogram、valid-action率、policy entropy、episode length、reward到達率、mask前後logit、invalid-action mass、gradient norm、policy/value lossをseed別に保存する。
7. official command/defaults、recurrent reset/detach、optimizer、termination、frame counting、mask、checkpoint restoreの差を診断する。
8. 原因だけを変える最大6 screening runを同一frames・split・instances・model familyで実施する。
9. 有望候補だけseeds `1,7,19`へ昇格する。
10. 失敗runは次の単一原因候補とmatched rerunを発行するまで未完了とし、「検証したが駄目」で閉じない。
11. runの進捗はR0.1 run ID、job conclusion、artifact ID、qualification JSON、checksum manifestでのみ認定する。
12. artifactが存在すれば即座に取得し、最初のactionable failureへ次の単一原因screening contractを接続する。
13. RESET-E052のcanonical headからR0.1を再要求し、workflow実行結果が取れない限り開始・成功・改善を推定しない。

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

## P1 — Multi-View CRL official-code reproduction

Yao et al., ICLR 2024の公式repositoryは `CausalLearningAI/multiview-crl`。画像・テキストを含む複数viewとpartial observability下のshared causal-factor recoveryを扱うため、RQ-001のmultimodal/shared-latent境界として別列で再現する。

1. exact commit、MIT license、`env.yaml`、tokenizer assets、numerical/multimodal commandを固定する。
2. numerical experimentを無改変でtrain/evaluateし、raw output、model bytes、peak RSS、runtime、seed、dependency、checksumを保存する。
3. Multimodal3DIdentのdataset version、download source、archive checksum、展開後manifestを固定する。
4. official three-view `(img0,img1,txt0)` experimentを無改変で実行する。
5. matched controlsとしてtext-view removal、image-view removal、text shuffle、cross-instance view shuffle、random representationを事前登録する。
6. shared-factor recovery、view-specific recovery、OOD/held-out評価を公式metricで保存する。
7. 成功してもSILGのinteractive competenceやRQ-001のlanguage-specific causal contributionへ流用しない。
8. 失敗時はenvironment、dataset、training stability、evaluation、artifactのいずれかへ分類し、原因だけを変えるrerunへ接続する。

## P1 — GPI official-software reproduction

Imai & NakamuraのGPIは、生成AI内部表現を用いたtext/image/videoの因果・予測推定を公開softwareとして提供する。SILG/J-CRe3とは目的が異なるため別列で再現する。

1. canonical repository、PyPI release、documentation versionを固定する。
2. exact commit、package version、license、dependency、example data、commandを保存する。
3. text-as-treatmentの最小公開exampleを無改変で再現する。
4. effect estimate、standard error、runtime、peak RSS、model、seed、split、raw output、checksumを保存する。
5. representationなし、random representation、shuffled representation、frozen alternative representationのmatched controlを追加する。
6. GPIの成功をinteractive policy competenceやhidden intervention-target recoveryの証拠へ流用しない。
7. 失敗時はdependency/model access、representation extraction、overlap/propensity、estimator、artifactのいずれかへ分類し、単一原因rerunへ接続する。

## P1 — R0.2 Environment-first

immutable R0.1 competence bundleが `qualified_for_r02=true` を満たした後のみ開始する。Environment-first、parameter-matched End-to-end、State-onlyを比較し、source policy competence、3-seed平均改善、最低seed非悪化、next-state prediction、action accuracy、online task successを確認する。

## Closed — R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず棄却維持する。

## Prior-art and RQ-001

2025 score-based CRLと2026年3月有限標本CRLにより、unknown target、少数environment、finite-sample recoveryだけではRQ-001を採用しない。

Markham et al., CLeaR 2026により、intervention-conditioned context module、causal concept disentanglement、compositional reuse、OOD composition自体は新規性候補から除外する。公式repositoryは未解決。

Baumgartner et al., CLeaR 2026により、raw trajectory、state-dependent local causal structure、system-parameter disentanglement、permutation/diffeomorphismまでのidentifiability、それを実装するsparsity-regularised transformer自体は新規性候補から除外する。author-official repositoryは今回固定できていないため、再現対象へ昇格せずcode-unresolved列に置く。

LeGITにより、language-guided target selection、low-data warm-start、言語知識と数値因果探索の組合せ自体は新規性候補から除外する。公式codeは未解決。

Imai & NakamuraのGPI系研究と公開softwareにより、LLM等の生成AI内部表現をtext/image/videoのtreatmentまたはconfounder表現として利用し、生成データ、overlap改善、double machine learningへ接続すること自体は新規性候補から除外する。

Yao et al.のMulti-View CRL with Partial Observabilityと公式 `CausalLearningAI/multiview-crl` により、言語を含むmulti-view alignment、partial observability、shared causal-factor recovery、multimodal contrastive learningだけでは新規性を認定しない。

### Required prior-art actions

1. Markham et al. 2026、Baumgartner et al. 2026、LeGITのauthor-official repository公開有無を継続監査する。
2. GPIのcanonical repositoryとexact commitを固定し、text-as-treatment最小exampleを再現する。
3. `CausalLearningAI/multiview-crl` のexact commitを固定し、numericalとthree-view multimodal experimentを無改変再現する。
4. 最強の非言語CRL、LeGIT型target-selection、介入context-module型composition、GPI型生成表現因果推定、partial-observability multi-view CRL、local-structure dynamical-system identificationをnovelty matrixの別列へ置く。
5. これらの論文上の性能値を本研究の能力証拠へ流用しない。
6. RQ-001採用候補は、上記すべてを差し引いた後に残るlanguage固有追加情報だけに限定する。

- 広義RQ-001: **棄却**
- 狭義RQ-001: **追加狭域化・未採用**

採用には、上記baseline再現後にも残るcountermodel pair、externally fixedでjoint recoding不能なdenotation law、target selection・context composition・既成生成表現利用・multi-view shared-factor recovery・local-structure trajectory identificationを超えるlanguage固有追加情報、事前登録済みclaim/counterexample/stopping ruleが必要。

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Status

- 外部baseline再現: **0件**
- 新規機構族: **未認定**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- 完成: **false**
