# 系列C Causal Grounding Cycle 008

## 仮説

**Structure-Expanding Residual Birth from Cross-Episode Counterfactual Repair**  
（複数episode反実仮想修復からの構造拡張型候補創発）

PR #378・#379では、識別行為選択や残差weight更新を改善しても、oracleを含めてhidden domain能力が伸びず、主因がselector failureではなくcandidate-support failureであると切り分けられた。

今回は残差を既成 `target × operation × goal` prototypeへ足すだけでなく、raw Japanese特徴と介入前world特徴の相互作用空間へ新しい分岐headを生成した。新headは、同じ予測失敗がd1・d2の両方で観測され、4件以上の支持を持つ場合だけ形成した。

比較条件:

- Base: 初期prototypeのみ
- Weight residual: 既成prototypeのweight修正
- Structure expand: cross-domain残差支持から正負2分岐interaction headを生成
- Outcome shuffle: 同じ生成手順で結果対応だけ破壊

テスト入力はraw Japaneseと介入前worldだけであり、test after、完成trajectory、domain辞書、shared ID、span proposal、RAG、外部LLMは使用していない。

## 3 seed平均

完全語彙非共有hidden domain d3:

| 条件 | Base joint / inverse / repair | Weight | Expand | Shuffle |
|---|---:|---:|---:|---:|
| Held | 0.0260 / 0.2292 / 0.2188 | 0.0260 / 0.2292 / 0.1354 | 0.0365 / 0.2448 / 0.2292 | 0.0365 / 0.2708 / 0.2917 |
| 未知語順 | 0.0521 / 0.2500 / 0.3125 | 0.0260 / 0.3125 / 0.2083 | 0.0521 / 0.2552 / 0.2500 | 0.0312 / 0.2865 / 0.2031 |
| 複数段落 | 0.0104 / 0.2812 / 0.2188 | 0.0365 / 0.2969 / 0.2604 | 0.0417 / 0.3125 / 0.2865 | 0.0573 / 0.2812 / 0.2448 |
| 自由日本語 | 0.0365 / 0.2500 / 0.2188 | 0.0365 / 0.2604 / 0.2448 | 0.0417 / 0.2083 / 0.2812 | 0.0521 / 0.2292 / 0.2865 |
| Rename | 0.0729 / 0.2500 / 0.2812 | 0.0573 / 0.2448 / 0.2292 | 0.0156 / 0.2240 / 0.1458 | 0.0260 / 0.2500 / 0.2500 |

追加診断:

- Weight residual birth: 29.00
- Structure-expanding head: 15.33
- Shuffled expanding head: 18.67
- 厳格gate: 0 / 3 seed

## 判断

**中核仮説は強く反証された。能力上の進歩は認定しない。G1/G2は未達。**

相互作用headを新生することで表現空間は形式上拡張されたが、hidden domainではExpandがBase・Weight・Shuffleを一貫して上回らなかった。

- HeldではShuffleのinverse・repairがExpandを上回る
- 複数段落ではShuffle jointがExpandを上回る
- 自由日本語ではShuffle jointがExpandを上回り、inverseも低下
- RenameではExpandが全主要指標を悪化
- Shuffled outcomeの方が多くのheadを生成した

したがって、複数domainで同じ出力indexへ残差支持が集まることは、同じ因果構造の証拠ではない。現在のinteraction headは、raw Japanese hashとgeometry featureの共起を分岐しただけであり、新しい対象関係・引数構造・作用域を表していない。

> **固定次元のinteraction basisを追加しても、候補構造の型自体が固定されたままならcandidate-support failureは解消しない。**

今回の失敗分類:

- initial semantics failure
- candidate-support failure
- residual co-occurrence confounding
- structural type immobility

## 先行知見との統合

- A #376: world-only識別価値では日本語曖昧性を解消できない
- B #378: joint version-space selectorとworld-onlyが同一、oracleでも改善しない
- D #379: residual weight更新はrandom/shuffleに負け、表現能力を拡張しない
- C Cycle 008: interaction headを追加しても、固定tuple型と出力indexへの帰属が残る限りshuffleと分離できない

これにより、問題は単なるselector・weight・feature interaction不足ではなく、**新しい構造型を生成するための表現言語そのものが存在しないこと**へさらに絞られた。

## 他系列へ返す知見

- A: n-gram×geometry interactionを増やしてもsemantic identityにはならない。発話変換の引数数・作用域・関係型が外部介入で増減可能な表現が必要。
- B: operation candidateを既成32 classへ帰属させず、引数構造を生成・分裂できる実行表現が必要。
- D: formal memory eligible unitは0。保存・干渉・sleep統合を再開しない。
- E: AF-008を継続する場合も、`fixed-output-index residual expansion creates missing causal structure` は不採用下位仮説とすべき。

## 次の仮説

**Typed Relational Program Birth from Intervention-Induced Arity Splits**  
（介入で誘発される項数分裂からの型付き関係プログラム創発）

次は固定32 classや固定interaction basisを使わない。

1. 各候補を可変長の匿名引数集合と局所変換で表す
2. 一対象介入では説明できず二対象介入でのみ修復する残差から、二項関係候補を生成
3. operation変更、target変更、goal変更が異なる引数へ選択的に作用するか監査
4. 必要なら候補を単項→二項、局所→作用域付きへ分裂
5. 別opaque domainで同じ介入依存グラフを再生成できる場合だけ因果unit候補とする
6. Correct / arity shuffle / argument-link shuffle / outcome shuffle / random birthを比較

進歩条件はhidden domainの自由日本語・未知語順・inverse・repairすべてで、Correctが全対照を+0.10以上、3/3 seedで上回ること。

## 資源量

- Model mean: 91,114.5 bytes
- Peak RSS: 112,336 KiB
- Runtime: 11.6343 sec / 3 seeds
- Candidate: 32
- Interaction dimension: 128
- Estimated update/inference: 14,336 ops/episode or query
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## Status

- Semantic Identity Gate G1: 未達
- Operation/Goal Gate G2: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 完成: false
