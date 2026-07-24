# 系列B Cycle 042

## 仮説

**Cross-Form Deletion-Stable Grammar from Predictive Role Equivalence**  
（表現横断削除安定性による予測role同値grammar）

Cycle 041では同一surface family内で匿名roleを削除すると選択的なconsequence lossが得られ、candidate entropyも低下した。しかし全条件でexecution・exact boundary・value bindingは0であり、surface-local roleにも選択的lesion profileが成立することが分かった。

今回は同じ潜在変更を canonical / 語順変更 / 言い換え / 別状態表現 / 入れ子 / 複数段落の6表現で生成し、1表現を完全に隠したleave-one-form-out条件で、残り5表現からrole削除loss vectorを予測できる候補だけを同値grammarへ昇格した。

- state / command-object / command-value境界は各表現で独立生成
- grammar identityから文字列identityを除外
- Cross-form方式では削除loss vector・role順序・可換性のみ使用
- MDL方式ではgrammar bits・held-form residual・候補entropy proxyを共同評価
- Final testのafter/futureはcandidate生成・rankingに不使用

## 先行研究と位置づけ

2025年のcompositional generalization理論は、因子化表現があってもdataset統計やshortcutにより合成的一般化が生じない条件を示している。またinteraction asymmetryは、異なる概念間より同一概念内の相互作用が複雑という構造から教師なしdisentanglementを識別する原理を提案している。これらは表現の一般化条件を扱うが、自然日本語から匿名role境界自体を生成する今回の問題より下流である。

## 他系列との重複表

| 系列 | 最新中心 | Bで扱わない領域 |
|---|---|---|
| A | Post-event残差からのstate rebirth | 時間状態・event順序 |
| C | Leave-one-world-out relation axis completion | 因果world・relation axis |
| D | Interference-graph memory assembly | 長期memory・read/write閉路 |
| E | Leave-one-counterexample-out constraint completion | Energy固定点・constraint field |
| **B** | **表現横断で予測可能なrole削除profileの匿名grammar化とMDL** | 今回の固有対象 |

## 3 seed平均

| 条件 | Within-form候補 | Cross-form候補 | MDL候補 | Shuffle候補 | MDL精度 |
|---|---:|---:|---:|---:|---:|
| 既知 | 0.0 | 1695.8 | 1695.8 | 2129.7 | 0.0000 |
| 未知語順 | 17.5 | 0.0 | 0.0 | 2299.3 | 0.0000 |
| 未知語彙 | 4.0 | 1697.4 | 1697.4 | 2131.2 | 0.0000 |
| Rename | 2.6 | 1849.1 | 1849.1 | 2135.5 | 0.0000 |
| 別状態表現 | 9.3 | 1629.1 | 1629.1 | 1975.3 | 0.0000 |
| 入れ子 | 22.7 | 1245.6 | 1245.6 | 2140.5 | 0.0000 |
| 主語省略 | 10.7 | 2297.3 | 2297.3 | 2297.3 | 0.0000 |
| 複数段落 | 18.7 | 1346.1 | 1346.1 | 2190.1 | 0.0000 |

追加診断:

- Within-form grammar: 43.67
- Cross-form grammar: 2.00
- MDL grammar: 2.00
- Shuffle grammar: 4.00
- MDL description: 360.7 bits
- MDL model: 100 bytes
- 学習時間: 0.000384 sec
- 推論: 既知 2.502 ms / 複数段落 2.746 ms
- Peak RSS: 112736 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### 表現横断profileは形成

Cross-form方式では平均2個のgrammarがleave-one-form-out条件を通過した。Shuffleでは平均4個となり、正しい対応の方がgrammar数は少なかった。

### しかし候補entropyは依然大きい

既知条件ではCross-form / MDLとも平均1695.8候補、entropy 10.73 bitsだった。Within-form方式は厳しすぎて候補0となり、Cross-form方式は緩すぎて約1700候補を残した。

### 実行・境界・値束縛は全面0

全方式・全8条件で以下が0だった。

- Execution accuracy
- Exact state boundary recall
- Value recall
- Rename転移
- 別状態表現転移
- 主語省略role再起動

> **表現横断で削除loss vectorを予測できることは、semantic variable・operation・scopeの十分条件ではない。**

削除channel自体が各表現のsurface置換可能性から作られているため、異なる表現間でも「削除すると同じ種類の表面再構成が崩れる」profileが共有される。これは意味roleの同一性ではなく、同じsynthetic生成過程の再構成同値性である。

### Correctとshuffleの差も能力へ接続しない

Correct alignmentはshuffleよりgrammarを少なくできたが、どちらもaccuracy 0だった。正しい表現対応に依存する圧縮信号と、意味programの形成は別である。

## 反証条件

| 条件 | 結果 |
|---|---|
| Leave-one-form-outで削除profileを予測 | 部分達成 |
| Correct alignmentがshuffleより小さいgrammar | 達成 |
| Candidate entropyを実用域へ削減 | 未達 |
| Exact state/value boundary recall > 0 | 未達 |
| Execution accuracy > 0 | 未達 |
| Rename・別状態表現へ転移 | 未達 |
| 主語省略で前turn role再起動 | 未達 |

## 資源量

- Role proposal: `O(NL)`
- Leave-one-form-out profile: `O(FP)`
- 推論: `O(GL²V)`
- Grammar上限: 48
- Local span上限: 12

1GB未満と小規模5ms未満は達成した。弱いスマートフォンCPU実機は未検証である。

## 系列B固有の進展

> **同一surface内の選択的lesionから、表現横断で予測可能なlesion profileへ条件を厳格化しても、semantic bindingは成立しなかった。表現横断安定性だけでは、共通の生成templateを共有するsurface roleを排除できない。**

## 他系列へ返す知見

- A: 時系列順序を越えて再現するresponsibility traceでも、評価channelがsurface再構成なら意味stateにならない。
- C: Leave-one-world-out completionはafter差分ではなく、入力から再生成できるsupportとlesion必要性を同時に要求すべき。
- D: Cross-form assemblyはedge sign patternの予測だけでなく、write/read閉路の選択的改善を必須化すべき。
- E: Missing-world completionは残差予測だけでなく、対応constraint除去で特定固定点だけが崩れることを要求すべき。

## 次の仮説

**Interaction-Asymmetric Role Birth from Cross-Form Counterfactual Coupling**  
（表現横断反実仮想couplingの相互作用非対称性によるrole創発）

1. Role単体の削除lossではなくrole pairのjoint lesionを測る
2. 同じ潜在role内のjoint lossがrole間の加算値を超えるsuperadditivityを要求
3. 異なるrole間では相互作用が弱いことを要求
4. Leave-one-form-outでinteraction matrixを予測
5. Correct form alignment / shuffled alignment / additive lesion / MDL-onlyを比較
6. Interaction graphの最小cutからrole boundaryを再生成
7. Exact boundary・execution・candidate entropyを同時評価
8. Rename・別状態表現・主語省略への転移を必須化

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
