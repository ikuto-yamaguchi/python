# 系列C Causal Grounding Cycle 005

## 仮説

**Bidirectional Lesion-Consensus Causal Units from Cross-Lexicon Response Conservation**  
（語彙横断の応答保存に基づく双方向lesion合意因果単位）

GOV-005 / AF-006およびA PR #367、B PR #368を踏まえ、結果側channelの一致だけではなく、各channelを除去したときにprospective target×transition、inverse query、言語―結果cycle closureが同時に低下するchannelだけを、完全語彙非共有domain D/E/Fで合意させた。

テスト時に使用するのはraw Japaneseと介入前worldのみで、正解after、完成trajectory、domain辞書、shared object ID、span proposal、固定ontology、RAG、外部LLMは使用しない。

## 重複回避

- A PR #367: factor-specific counterfactualで2 domainの弱いresponse/lesion同符号を形成。ただし自由日本語・全seed未達。
- B PR #368: 3 domainの結果channel合意を形成したが、結果側符号化に留まり双方向bindingなし。
- D PR #365: domain/seed依存でmemory eligibility未達。
- E PR #366: HF-008凍結、複数domain・全seed・双方向能力を必須化。
- 本Cycle: **同一channelの除去がforward、inverse、cycle closureを同時に崩すか**をC固有の因果必要性として監査。

## 設計

1. 完全語彙非共有domain D/E/Fを独立生成。
2. 各domainでraw Japanese全文と介入前worldから結果指紋への局所双方向写像を学習。
3. 16結果channelを1つずつlesionし、prospective joint、inverse、cycle cosineの低下を測定。
4. 3 domainすべてで3能力が同方向に低下するchannelだけをconsensus化。
5. Full / Bidirectional consensus / Shuffled-domain consensusを比較。
6. Held、Rename、未知語順、複数段落、自由日本語、goal変更、failure repairを3 seedで評価。

## 3 seed平均

- Consensus channel: **3.00 / 16**
- Strict progress gate: **0 / 3 seed**
- Model size: **7026 bytes/domain**
- Peak RSS: **112536 KiB**（Python runtime込み）
- 3 seed実行時間: **23.181秒**
- Candidate: **32**
- 推定更新量: **1536 ops/episode**
- 推定推論量: **11264 ops/query**

| Domain / 条件 | Correct joint | Shuffle joint | Correct inverse | Shuffle inverse | Cycle cosine |
|---|---:|---:|---:|---:|---:|
| D / held | 0.0000 | 0.1250 | 0.2083 | 0.2083 | 0.0870 |
| D / rename | 0.0417 | 0.0000 | 0.2500 | 0.1250 | 0.0684 |
| D / word_order | 0.0417 | 0.0000 | 0.0833 | 0.1250 | 0.0043 |
| D / paragraph | 0.0000 | 0.0000 | 0.2917 | 0.0000 | 0.1324 |
| D / free | 0.0833 | 0.0833 | 0.1667 | 0.0833 | 0.1388 |
| D / goal_change | 0.0417 | 0.0417 | 0.2917 | 0.3333 | 0.1469 |
| D / repair | 0.0000 | 0.0417 | 0.3333 | 0.0833 | 0.0904 |
| E / held | 0.0417 | 0.0000 | 0.0833 | 0.1667 | 0.0660 |
| E / rename | 0.0417 | 0.0000 | 0.1250 | 0.0833 | 0.0138 |
| E / word_order | 0.0417 | 0.0000 | 0.3750 | 0.2500 | 0.1311 |
| E / paragraph | 0.0000 | 0.0833 | 0.2500 | 0.0833 | 0.1020 |
| E / free | 0.0417 | 0.0417 | 0.2917 | 0.0417 | 0.0254 |
| E / goal_change | 0.0417 | 0.0000 | 0.2083 | 0.1250 | 0.0108 |
| E / repair | 0.0417 | 0.0000 | 0.1667 | 0.0833 | 0.0675 |
| F / held | 0.0000 | 0.0417 | 0.1667 | 0.2083 | 0.2164 |
| F / rename | 0.0417 | 0.0417 | 0.0833 | 0.1250 | 0.0803 |
| F / word_order | 0.0000 | 0.0417 | 0.0417 | 0.0417 | 0.0227 |
| F / paragraph | 0.0000 | 0.0000 | 0.1250 | 0.1250 | 0.0886 |
| F / free | 0.0833 | 0.0000 | 0.0833 | 0.0833 | 0.1418 |
| F / goal_change | 0.0833 | 0.0000 | 0.1250 | 0.1667 | 0.1276 |
| F / repair | 0.0417 | 0.0417 | 0.1250 | 0.0417 | 0.1395 |

## 判定

**中核仮説は反証。能力上の進歩は未認定。G1/G2未達。**

双方向lesion条件を満たすchannelは平均3個残ったが、外部能力の符号はdomain・条件ごとに安定しなかった。3 domain × free/goal-change/repair × forward/inverseの厳格gateは0/3 seedだった。

したがって、**同一channelのlesionがforward・inverse・cycleを同時に悪化させることも、再利用可能な因果単位の十分条件ではない。** 現在のchannelは、小標本で偶然同方向になった物理結果成分と、domain固有の文字特徴結合を混在させている。

これは低rank差分、欠測補完、relation axis、graph形成の再試行ではなく、外部能力に対する双方向の選択的必要性監査である。しかし結果は、結果指紋channelを先に固定した後段選別の限界を示した。

## 他系列へ返す知見

- A: 固定結果channelの共通性だけでsemantic unitへ昇格してはいけない。発話側にも独立に創発した変換単位が必要。
- B: 出力channel合意や転置近似だけではoperation primitiveにならない。発話counterfactualとworld interventionの最小可換図を入力側から同時生成する必要がある。
- D: eligible unitは0。保存・干渉・sleep consolidationは再開不可。
- E: AF-006は診断枠として継続できるが、「固定結果codebookの双方向lesion合意」下位仮説は不採用候補。

## 次の仮説

**Jointly Emergent Intervention Diagram from Language–World Commutator Residuals**  
（言語―世界交換子残差からの共同創発介入図式）

次は16次元の結果codebookを先に固定しない。identity・operation・goal・wordingの反実仮想について、言語側変換を先に行ってからworldへ介入した結果と、world側介入後に言語説明を変換した結果の不一致を直接最小化する。潜在単位はこの可換図式を複数domainで閉じる最小局所変換として同時生成する。

進歩条件は、完全語彙非共有3 domain、3/3 seedで、自由日本語・goal変更・repairのprospective jointとinverseのCorrect−shuffle/randomが各+0.10以上、post-treatment leakageなし。

- Semantic Identity Gate G1: 未達
- Operation/Goal Gate G2: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
