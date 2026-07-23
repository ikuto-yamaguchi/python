# 系列B Cycle 027 研究報告

## 仮説

**Contrastive Binding Graph Selection by Minimal Negative Witness Cuts**  
（最小negative witness cutによる対照的binding graph選択）

Cycle 026では、training witness上でforward after生成・inverse before復元・non-target保存を満たすbinding triangleが64件形成されたが、held-outでは複数triangleが同点で異なるafterを提案し、全面棄権した。

今回はtriangleを増やさず、各triangleについてpositive / wrong / noexec witnessを分離し、正例に頻出し誤例に少ない最小局所特徴集合をnegative witness cutとして付与した。推論時にはcut hit数で競合triangleを選別した。

## 先行研究整理

- CEGIS/STUNはcounterexampleを追加してcandidate programを反復的に絞り、部分解をunificationで統合する。ただしprogram spaceとunification operatorは事前定義される。
- Representative-example selectionは、program synthesisの制約集合から少数の識別的exampleを選ぶことで探索を安定化するが、入出力仕様とprogram候補は既知である。
- Negative sampleを使うcontrastive searchは不適合解を識別するのに有効だが、negativeの生成過程が意味概念と衝突すると誤ったcutを学ぶ。

今回の課題は、生の日本語からprogram候補・変数・negative test自体を生成するさらに上流の問題である。

## 他系列との重複表

| 系列 | 最新中心 | 限定信号 | 主な失敗 | Bとの分離 |
|---|---|---|---|---|
| A | Cross-encoded residual routing | 局所creditは正へ転化 | 能力増分0、surface routing | 予測状態は扱わない |
| C | Bidirectional local alignmentによるpositive witness birth | 必要性監査原理 | positive witness不足 | 因果state-variable identityは扱わない |
| D | Shapley-sparse memory coalition credit | leave-one-out正負credit | slow binding 0 | 長期memoryは扱わない |
| E | Predictor-independent residual hyperedge | triadic structure形成 | surface leakage、能力0 | energy dynamicsは扱わない |
| **B** | **negative witness cutによる実行graph選択とMDL** | 今回検証 | triangle競合選択 | 系列固有 |

## 実験条件

- seed: 1 / 7 / 19
- train: 48 / 144 / 288 episode
- test: 24例 / split / seed
- endpoint上限: 32
- triangle上限: 64
- cut上限: 4 / triangle
- ablation:
  1. Graph supportのみ
  2. Negative witness cut
  3. Cut + MDL
- split: 既知、未知語順、未知語彙、Rename、別状態表現、入れ子、主語省略、複数段落

学習器はraw `before / command / after / future`のみ使用し、hidden object・field・valueは評価器だけで使用した。

## 最大288例・3 seed平均

| 条件 | Graph accuracy / pair recall | Cut accuracy / pair recall | MDL accuracy / pair recall |
|---|---:|---:|---:|
| 既知 | 0.0000 / 0.0556 | 0.0000 / 0.0556 | 0.0000 / 0.0556 |
| 未知語順 | 0.0000 / 0.0139 | 0.0000 / 0.0139 | 0.0000 / 0.0139 |
| 未知語彙 | 0.0000 / 0.0417 | 0.0000 / 0.0417 | 0.0000 / 0.0417 |
| Rename | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 別状態表現 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 入れ子 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 主語省略 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 複数段落 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |

追加診断:

- Triangle: 64
- Cut候補総数: 393.33
- Raw候補: 1900
- Witness audit: 2472
- 既知平均生成候補: 9.56
- 既知commit率: 0.0000
- MDL description: 32256 bits

## 判定

**中核仮説は強く反証された。**

### 約393 cutを形成したがtieを一件も解消しない

64 triangleに対して平均393.33個の局所cut候補が形成された。しかしGraph / Cut / MDLは全splitでaccuracy・commit率・pair recallが同一だった。

既知条件でも平均9.56個の異なるafter候補が残り、score差0.5未満の競合として全面棄権した。

### Negative witnessがtriangle非依存のsurface feature

Cutはcommand/before/futureの先頭末尾、span長、文字shape、包含フラグから生成した。同じinput上で競合するtriangleはこれらのfeatureをほぼ共有するため、正しいtriangleだけを識別できなかった。

> **競合programが同じ表面観測を共有する場合、その表面から作ったnegative witnessはprogram間の差を説明しない。**

### Pair recallは極小でexecution 0

- 既知 pair recall: 0.0556
- 未知語順: 0.0139
- 未知語彙: 0.0417
- Rename / 別状態表現 / 入れ子 / 主語省略 / 複数段落: 0
- 全split execution accuracy: 0

Cycle 026より候補包含は若干増えたが、正しいafter生成・選択には結びつかなかった。

### MDLは短縮するが能力0

MDL descriptionは32,256 bitsまで短縮したが、能力値はCut方式と完全同一である。今回も短く保存できる失敗libraryを選択しただけで、意味一般化は形成されなかった。

## 反証条件

仮説を支持するには最低でも以下が必要だった。

1. Cut方式がGraph方式よりcommit coverageを増やす
2. Wrong commitを増やさずaccuracyを改善する
3. 未知語順・未知語彙・Renameのpair recallを増やす
4. 同じinput上の競合triangleを異なるnegative consequenceで分離する
5. MDL短縮と能力改善を同時達成する

今回はすべて未達。

## 探索爆発抑制

- object/value候補を各4件へ制限
- endpoint 32、triangle 64
- Cutはtriangleあたり最大4
- Cut採用条件: positive 60%以上、wrong 20%以下
- 推論時に同一afterを集約
- score差0.5未満はunknownとして棄権

計算量:

- 候補生成 `O(NL²)`
- Witness audit `O(NKₒKᵥ)`
- Cut誘導 `O(TF)`
- 推論 `O(TL²)`
- `T≤64`

## 資源量

- モデルサイズ: 8083 bytes
- 学習時間: 0.108408 sec
- 既知推論: 4.439 ms/example
- 入れ子推論: 7.853 ms/example
- 複数段落推論: 16.933 ms/example
- Peak RSS: 114256 KiB（Python runtime込み）

1GB未満は達成。既知推論は5ms級だが、入れ子・複数段落と弱いスマートフォン実機検証は未達。

## 系列B固有の進展

> **Positive/wrong/noexec witnessを分離するだけでは不十分で、negative witnessは競合programごとに異なる予測consequenceを発生させる必要がある。同一入力surfaceの局所特徴はcutにならない。**

研究段階:

1. Surface candidate
2. Reversible anchor
3. Role-exchange seed
4. Executable binding triangle
5. **Surface negative witness cut――今回反証**
6. Counterfactual consequence test generation
7. Relation/scope-conditioned executable grammar
8. MDL consolidation

## 他系列へ返す知見

- A: 同じ入力surfaceから作るresidual routeでは競合commitmentを分離できない。各commitment固有の予測差が必要。
- C: positive witness alignment後も、競合fiberが異なるcounterfactual outcomeを出すtestが必要。
- D: memory coalitionのnegative creditは共通query featureではなく、coalition固有のread/write consequenceで測る。
- E: predictor-independent residualでも、複数hyperedgeが同じresidualを共有するならedge固有のcounterfactual perturbationが必要。

## 次の仮説

**Counterfactual Test Programs from Competing Binding-Graph Output Disagreements**  
（競合binding graphの出力不一致からの反実仮想test program）

次は入力surfaceをcutにしない。

1. 同一入力で異なるafterを生成するtriangle pairを抽出
2. 両afterの最小差分区間をtest target化
3. Future・non-target・inverse reconstructionの各予測をtriangle別に生成
4. 観測可能な予測が異なる場合だけtest program化
5. Held-out training witnessで正triangleのtest outcomeが再現するか監査
6. 最小test集合でtriangleを選択
7. 観測不能・同値の場合はunknownを保持
8. Execution accuracy、commit coverage、wrong binding、test数、MDLを同時評価

- 高校生級: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機: **未検証**
- 完成: **未達**
