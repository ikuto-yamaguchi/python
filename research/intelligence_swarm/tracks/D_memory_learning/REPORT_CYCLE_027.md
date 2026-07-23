# 系列D Cycle 027 研究報告

## 仮説

**Shapley-Sparse Credit Sets with Redundancy-Aware Reconsolidation**  
（冗長性を考慮したShapley型疎credit集合による再固定化）

Cycle 026の単独memory要素除去では、代替可能なfactorと共同で有害なbindingを分離できなかった。今回は上位6候補に限定し、単独除去・pair除去のheld-out read損失差から疎なcoalition marginal creditを推定し、複数sessionで正のcreditを持つ要素だけslow化する仮説を検証した。

## 重複回避

| 系列 | 最新中心 | Dとの分離 |
|---|---|---|
| A | cross-encoded residual routing | 談話予測責任は扱わない |
| B | binding graph disagreement test | program選択・MDLは扱わない |
| C | outcome-blind source-only witness transport | 因果transitionは扱わない |
| E | predictor-independent residual hyperedge | energy・attractorは扱わない |
| **D** | **memory coalition除去のheld-out marginal credit** | 今回の固有対象 |

共通状態は高校生級・ネイティブ日本語コミュニケーション・弱いスマートフォン実機検証が未達。

## 実験

- seed: 1 / 7 / 19
- 学習event: 24 / 48 / 96
- 候補binding上限: 24
- coalition対象: top-k、k≤6
- 監査: singleton 6 + pair 15 = 最大21 coalition
- ablation: Support / Leave-one-out / Shapley-sparse
- 統合test: 既知、Rename、別状態表現、主語省略、複数段落、未知domain、one-shot、長期干渉、最新値保持

学習器はraw日本語から1〜6文字spanを生成し、固定value辞書・hidden object/relation/value labelを候補生成やrankingに使用しない。

## 最大96 event・3 seed平均

| 条件 | Support read / null | LOO read / null | Shapley read / null |
|---|---:|---:|---:|
| 既知 | 0 / 1 | 0 / 1 | 0 / 1 |
| Rename | 0 / 1 | 0 / 1 | 0 / 1 |
| 別状態表現 | 0 / 1 | 0 / 1 | 0 / 1 |
| 主語省略 | 0 / 1 | 0 / 1 | 0 / 1 |
| 複数段落 | 0 / 1 | 0 / 1 | 0 / 1 |
| 未知domain | 0 / 1 | 0 / 1 | 0 / 1 |

追加:

- Binding: 24
- Coalition audit: 21
- Slow binding: 0
- One-shot: 全方式0
- 干渉後recall: 全方式0
- 最新値recall: 全方式0

## 判定

**中核仮説は強く反証された。**

### Raw span候補形成が先に崩壊

固定value語彙を排除し、生の日本語から一般spanを生成すると、Support方式を含む全方式で正答readは0になった。

候補集合には状態説明の一般文字片が優先され、queryが要求するvalue endpointが安定して残らなかった。したがってcoalition credit以前に、memory element identityが未成立である。

### Shapley creditは全面0

Top-6の単独・pair除去を21通り監査したが、正答損失を安定して増やすcoalitionは形成されず、slow bindingは0件だった。

LOOとShapleyは全件棄権へ退化した。冗長性補正によって安全になったのではなく、credit対象が意味要素でないため全候補を拒否した。

### 以前の高いSupport値を降格

固定されたvalue inventoryを走査する旧プロトタイプではreadが高く見えたが、それは固定ontology禁止条件と両立しない。今回raw span形成へ置き換えると能力が消えたため、過去の一部read値は一般記憶能力ではなく、候補生成側の事前知識に依存していたと判断する。

### 破滅的忘却ではない

one-shot、干渉前、干渉後、最新値保持がすべて0であるため、良い記憶が後から壊れたのではない。支配的失敗は**記憶を書き込む前のendpoint候補形成**である。

## RAG・検索との差

保存文書や近傍vectorを返す方式ではない。候補memory要素を内部read状態へ注入し、coalitionを反実仮想的に除去してheld-out lossへの局所寄与を測る。ただし意味endpointが未形成なのでsemantic associative memoryには未到達。

## 資源量

- Shapley model: 3,340 bytes
- 学習: 約0.013秒
- 推論: 約0.0043 ms/query
- Peak RSS: 約111 MiB（Python runtime込み）
- Binding: 24
- Coalition: 21
- 計算量:
  - span候補 `O(NL²)`
  - sparse coalition `O(k²N)`、k≤6
  - read `O(BL)`

1GB未満・5ms未満は小規模条件で達成。弱いスマートフォン実機は未検証。

## 系列D固有の進展

> **Coalition creditは、意味を持つmemory elementが形成された後の冗長性監査には使える。しかしraw span候補がvalue endpointを保持できない段階では、Shapley近似は全面0-creditへ退化する。再固定化より先に、正解語彙なしのendpoint birthが必要である。**

## 他系列へ返す知見

- A: routing credit以前に、carry対象cellが正解語彙なしで形成されるか監査する。
- B: counterfactual test以前に、競合programの出力endpointが外部候補語彙に依存していないか確認する。
- C: source-only transportでもtarget endpoint候補が固定値集合由来ならopen-form witnessではない。
- E: predictor-independent residualでもcandidate nodeが固定語彙依存なら独立性は成立しない。

## 次の仮説

**Endpoint Birth by Cross-Temporal Predictive Necessity before Coalition Credit**  
（coalition credit前の時間横断予測必要性によるendpoint創発）

1. 固定value inventoryを使わず全局所spanを生成
2. Spanを一つ除去した際、次turn query応答・state変化・future再現の複数channelが同時に悪化するか測定
3. 同じspan文字列ではなく、除去応答signatureが再現する候補をendpoint class化
4. Object・relation・value候補を独立channelで形成
5. Endpoint成立後にだけcoalition creditを適用
6. one-shot、Rename、別状態表現、干渉前後latest-value recallを主評価化

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
