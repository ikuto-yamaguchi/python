# 系列B Cycle 041

## 仮説

**Deletion-Causal Role Grammar from Minimal Predictive Sufficiency Sets**  
（最小予測十分集合による削除因果型role grammar）

Cycle 040ではmulti-world role permutationとMDLにより候補entropyをCycle 039比で大幅に削減したが、execution、exact state boundary、value bindingは全条件0だった。

今回は、短く圧縮できるroleをそのまま採用せず、匿名role `r0/r1/r2` を一つずつ削除した際に、対応する外部予測成分だけが選択的に崩れるかを監査した。

- `r0`削除: object変更worldにおけるtarget選択応答
- `r1`削除: value変更worldにおけるpayload共変応答
- `r2`削除: before→after rollout応答
- 2-role同時削除による代替経路監査
- Grammar bits + lesion residual + candidate entropy proxyの共同MDL
- Final testのafter/futureは候補生成・rankingに不使用

role名はモデル内部の匿名介入応答indexであり、固定ontology・手書きslotではない。意味上のobject/value/stateという名称は評価と報告にのみ用いた。

## 先行研究整理

2024年のLearning to Intervene on Concept Bottlenecksは、既成concept bottleneckに対する介入を記憶し、未知状況へ再適用する。しかしconcept層は既に定義されている。2025年のEditable Concept Bottleneck Modelsもconcept/data削除の影響を効率的に近似するが、削除対象conceptは既知である。Counterfactual Concept Bottleneck Modelsもconcept介入の因果効果を高めるが、concept集合と予測taskが与えられる。

今回の課題は、その前段で、生の自由日本語から形成した匿名roleが本当に予測上必要な変数・操作roleかを、削除による選択的損失で判定できるかである。

## 重複表

| 系列 | 最新中心 | Bで扱わない領域 |
|---|---|---|
| A | Boundary-conditioned state rebirth | 時間状態・event境界後の再起動 |
| C | Cross-object difference tensor | 因果event・world transition |
| D | Leave-one-episode-out replay compression | 長期memory・read/write閉路 |
| E | Residual eigenmode constraint field | Energy固定点・局所緩和 |
| **B** | **匿名role削除の選択的予測損失とMDL採否** | 今回の固有対象 |

A/C/D/Eでもlesionや削除監査を用いるが、系列Bでは削除因果性そのものではなく、削除で必要性が確認されたrole集合だけを再利用可能grammarへ圧縮し、記述長と候補entropyと実行性能を同時改善できるかを成果条件とした。

## 最小実装

比較方式:

1. **Quotient**: multi-world role quotientを全保持
2. **Deletion**: 1-role lesionで一つ以上の選択的損失があるgrammar
3. **Minimal sufficiency**: 2つ以上のroleが各々異なる予測成分へ必要なgrammar
4. **MDL**: grammar bits + lesion residual + entropy proxyで採用
5. **Shuffle**: object/value world対応を交換した対照

## 3 seed平均

| 条件 | Quotient候補 | Minimal候補 | MDL候補 | MDL entropy bits | MDL精度 |
|---|---:|---:|---:|---:|---:|
| 既知 | 4632.2 | 1847.4 | 1611.0 | 10.64 | 0.0000 |
| 未知語順 | 3652.3 | 1823.1 | 1072.2 | 10.06 | 0.0000 |
| 未知語彙 | 4818.9 | 1716.8 | 1574.8 | 10.62 | 0.0000 |
| Rename | 5534.1 | 1992.0 | 1731.1 | 10.75 | 0.0000 |
| 別状態表現 | 733.5 | 538.4 | 465.5 | 8.84 | 0.0000 |
| 入れ子 | 2224.9 | 1508.6 | 1131.0 | 10.14 | 0.0000 |
| 主語省略 | 2446.8 | 0.0 | 0.0 | 0.00 | 0.0000 |
| 複数段落 | 6067.7 | 2539.3 | 2256.2 | 11.14 | 0.0000 |

追加診断:

- Quotient grammar: 28.67
- Deletion grammar: 28.67
- Minimal sufficiency grammar: **17.00**
- MDL grammar: **10.33**
- Quotient selective role count: 62.67
- Minimal selective role count: 51.00
- MDL selective role count: 31.00
- MDL description: 1269.9 bits
- MDL model: 471 bytes
- Training: 0.003845 sec
- Inference: 既知 2.552 ms / 複数段落 5.241 ms
- Peak RSS: 113012 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### 選択的lesion profileは形成された

Quotient grammar 28.67件に対し、Minimal sufficiency条件を満たすgrammarは17件、MDLでは10.33件まで減った。匿名role削除によって異なるobservable consequence channelが低下するprofile自体は形成された。

### 候補entropyは削減

既知候補はQuotient 4632.2件からMinimal 1847.4件、MDL 1611.0件へ減少した。既知entropyも12.18 bitsから10.64 bitsへ低下した。

削除必要性は単なる可換性より強い候補空間制約として働いた。

### しかしexecution・境界・値bindingは0

全方式・全8条件でexecution accuracyは0、MDL方式のnull率は1.0だった。Exact state boundaryとvalue recallも全条件0である。

> **匿名roleを削除したとき異なるsurface consequenceが崩れることは、semantic roleの十分条件ではない。**

現在のconsequence channel自体が、相対位置、区間幅、語順、同一template内の文字列保存から構成されるため、surface roleにも選択的lesion profileが成立する。

### Correctとshuffleの分離も不十分

Correct alignmentはMDL候補を既知1611件まで削減したが、shuffleでも2681.5件残った。両者ともaccuracy 0である。Correct対応に依存する圧縮差があっても意味programの証拠にはならない。

### 主語省略と表現転移

主語省略では全方式で候補0、Rename・別状態表現でもexecution 0だった。前turn focus、object identity、relation、operation、scope、goal、constraintは形成されていない。

## 反証条件

| 条件 | 結果 |
|---|---|
| Role削除で予測成分が選択的に崩れる | 表面上達成 |
| Minimal sufficiencyが候補entropyを削減 | 達成 |
| Correct deletionがshuffleより短い/疎 | 部分達成 |
| Exact state/value boundary recall > 0 | 未達 |
| Execution accuracy > 0 | 未達 |
| Rename・別状態表現へ転移 | 未達 |
| 主語省略でrole再起動 | 未達 |
| Grammar追加costを予測利得で回収 | 未達 |

## 既存方式との差

既成conceptやDSL primitiveを削除したのではない。Multi-world介入応答から匿名role候補を生成し、各roleのlesion effectから最小十分集合を選んだ。

ただし予測成分の定義がまだsurface consequenceであり、現実・言語上の意味的妥当性を保証しない。これは共通Backlogの「内部整合性と意味的妥当性を区別する」課題を再確認する結果である。

## 資源量・探索爆発抑制

- Multi-world共同分節: `O(NL)`
- Role lesion監査: `O(P 2^R)`、`R=3`
- Quotient/MDL: `O(P log P)`
- 推論: `O(GL²V)`
- Grammar上限: 48
- Span長上限: 12

1GB未満を達成した。MDL推論は既知約2.55msで5ms未満、複数段落は約5.24msで5msをわずかに超えた。弱いスマートフォンCPU実機は未検証である。

## 系列B固有の進展

> **Role permutationに削除必要性を追加するとcandidate entropyをさらに減らせる。しかしlesion対象の予測成分がsurface-localなら、選択的削除効果もsemantic variable・operationの証拠にならない。**

## 他系列へ返す知見

- A: Boundary gateやstate rebirthは、対応stateを削除したとき境界後の特定予測だけが崩れることに加え、shuffleより強い意味転移を要求すべき。
- C: Difference tensor componentは、component削除で特定object/world transitionだけが崩れ、別表現でも同じaxisが再生成されることを必須化すべき。
- D: Replay generator削除はclosed-cycle全体ではなく、対応episode/addressだけを選択的に崩す必要がある。
- E: Constraint mode削除でactive集合が変わるだけでは不十分。正しいboundary/executionのみの選択的損失を要求すべき。

## 次の仮説

**Cross-Form Deletion-Stable Grammar from Predictive Role Equivalence**  
（表現横断削除安定性による予測role同値grammar）

次は同一surface family内の選択的lesionを証拠にしない。

1. 同じ潜在変更を異なる状態表現・語順・言い換えで生成
2. 各表現で匿名roleを独立生成
3. Role削除によるprediction-loss vectorが表現横断で一致する候補だけ同値化
4. 文字幅・相対位置・語順をgrammar identityから完全除外
5. Leave-one-form-outで削除profileを予測
6. Cross-form deletion／within-form deletion／shuffle／MDL-onlyを比較
7. Exact boundary・execution・candidate entropyを同時評価
8. 主語省略では前turn deletion-stable roleを再起動

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
