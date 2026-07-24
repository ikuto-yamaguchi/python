# 系列A Semantic Identity Cycle 007

## 仮説

**Intervention-Born Semantic Identity from Minimal Discriminating Action Sets**  
（最小識別行為集合からの介入起点semantic identity）

直近A/B/Cでは、global低rank軸、単一domainの局所surprise cluster、domain横断の失敗類似対応がいずれも外部能力を閉じなかった。共通原因は、外部行為で候補を識別する前に類似度・誤差形状で候補同士を同一視したことである。

今回は候補を事前にfamily化しない。各episodeについて32個の target × operation × goal 候補が予測する外部結果を保持し、候補間の結果距離が大きいepisodeを観測対象として選ぶ。実際の外部結果で一意に生存した完全tupleだけを局所prototypeへ更新する。

比較:

- Active: 最小識別行為集合の分離余裕が大きい観測を優先
- Random: 同数の無作為観測
- Shuffle: Active観測だが外部結果との対応を破壊

固定ontology、手書きslot、span proposal、文字列検索、RAG、外部LLM、test時afterは使用していない。

## 3 seed平均

Joint chanceは1/32=0.03125、inverse chanceは1/4=0.25。

| 条件 | Active joint / inverse | Random joint / inverse | Shuffle joint / inverse |
|---|---:|---:|---:|
| d1_held | 0.0278 / 0.1667 | 0.0278 / 0.2083 | 0.0347 / 0.2292 |
| d1_free | 0.0278 / 0.2292 | 0.0486 / 0.3056 | 0.0000 / 0.2569 |
| d2_held | 0.0625 / 0.3056 | 0.0625 / 0.3264 | 0.0417 / 0.2778 |
| d2_free | 0.0764 / 0.2500 | 0.0347 / 0.2431 | 0.0347 / 0.2361 |
| d3_held | 0.0694 / 0.3125 | 0.0417 / 0.2500 | 0.0208 / 0.2222 |
| d3_word_order | 0.0694 / 0.3125 | 0.0764 / 0.2639 | 0.0417 / 0.2917 |
| d3_paragraph | 0.0625 / 0.2361 | 0.0764 / 0.2639 | 0.0347 / 0.2292 |
| d3_free | 0.1181 / 0.3333 | 0.0486 / 0.2778 | 0.0139 / 0.2431 |
| d3_rename | 0.0417 / 0.2847 | 0.0556 / 0.2708 | 0.0417 / 0.2431 |

Strict gate: `[false, false, false]`（0/3 seed）

## 判定

**中核仮説は反証。能力上の進歩は未認定。G1/G2未達。**

hidden d3自由日本語ではActive joint 0.1181、Random 0.0486、Shuffle 0.0139となり局所的な正方向信号が出た。一方、hidden d3未知語順ではActive 0.0694、Random 0.0764でRandomを上回らず、paragraphでもRandomが優位だった。d1ではheld/freeともActiveがRandomを上回らない。

したがって、候補結果の分離余裕が大きい観測を選ぶだけでは、意味的に重要な識別行為を選んだことにならない。現在の分離余裕はworld geometryが候補結果をどれだけ離すかを測っており、日本語表現の曖昧性、対象同一性、操作同一性のどれを解消するかを測っていない。

> 外部結果で候補を生存・破壊する順序は正しい方向だが、識別行為の価値をworld側だけで定義するとlanguage uncertaintyへ接続しない。

## 他系列へ返す知見

- B: action setはworld結果の分離だけでなく、operation/goalの言語候補を選択的に破壊する必要がある。
- C: generic outcome separabilityではなく、language候補対とworld候補対の両方を一意に分離するinterventionを探索する必要がある。
- D: hidden freeの平均陽性はあるが0/3 strict gateのためmemory eligible unitはない。
- E: AF-007は継続可能だが、`world-only discriminating action value` は不採用下位仮説候補。

## 資源

- Model: **98,781 bytes**
- Peak RSS: **112,536 KiB**
- Runtime: **2.0886 sec / 3 seeds**
- Observation budget: **24/domain**
- Candidate: **32**
- Estimated update: **12,288 ops/episode**
- Estimated inference: **12,288 ops/query**
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 次の仮説

**Language-Conditioned Discriminating Intervention Birth from Joint Version-Space Collapse**

言語側とworld側に独立な候補version spaceを維持し、介入後に両方の候補集合を同時に最も縮小するactionだけを選ぶ。world結果だけでなく、raw Japaneseの言い換え・対象変更・操作変更候補のどれが破壊されるかを価値関数へ含める。hidden opaque domainでActiveがRandom/Shuffleを自由日本語・未知語順・inverseの全てで+0.10以上、3/3 seed満たすことを進歩条件とする。

- Semantic Identity Gate G1: 未達
- Operation/Goal Gate G2: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
