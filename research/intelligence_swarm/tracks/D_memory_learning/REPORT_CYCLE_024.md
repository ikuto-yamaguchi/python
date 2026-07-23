# 系列D Cycle 024 研究報告

## 仮説

**Endpoint Identity from Bidirectional Query–State Reconstruction before Slow Linking**  
（slow link前の双方向query–state再構成によるendpoint identity）

Cycle 023ではwrite-only classとread addressを分離してread全面崩壊を止めたが、wrong read 0.537、slow link 0だった。今回はslow化より先に、query→state value contextとstate→query contextの双方を再構成し、複数session支持・wrong 0を満たすendpointだけを安定endpointへ昇格した。

## 最新PR・失敗知見の集約

| 系列 | 最新中心 | 限定成功 | 支配的失敗 | Dとの分離 |
|---|---|---|---|---|
| A Cycle 024 | 観測前prospective commitment | 主語省略pair recall 0.1944→0.4167 | accuracy 0.0833、wrong carry 0.9167 | 予測談話stateは扱わない |
| B Cycle 024 | 三者導出交差binding seed | 明示surface anchor回収 | Rename・省略pair recall 0 | MDL・program帰納は扱わない |
| C Cycle 025 | 環境paired mechanism residual partition | 評価監査 | 64 eventが1 classへnull-collapse | 因果world modelは扱わない |
| E Cycle 023 | 環境不変energy response | 18.67 prototype | 能力増分0、surface symmetry | energy dynamicsは扱わない |
| **D** | **双方向query-state再構成によるread endpoint identity** | 今回検証 | slow前のendpoint形成 | 系列固有 |

## 実験

- seed: 1 / 7 / 19
- train: 24 / 48 / 72 event
- test: 各24例
- 条件: 既知、言い換え、Rename、別状態表現、複数段落
- Endpoint上限: 32
- Write trace上限: 32
- Slow link上限: 64
- ablation: Raw / Bidirectional / Slow
- 追加評価: 一回提示、96 distractor後latest-value recall

Hidden object・field・valueは評価器だけで使用した。

## 最大72 event・3 seed平均

| 条件 | Raw read / wrong | Bidirectional read / wrong | Slow read / wrong |
|---|---:|---:|---:|
| 既知 | 0.2500 / 0.6528 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 未学習言い換え | 0.2500 / 0.6528 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| Rename | 0.2222 / 0.6528 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 別状態表現 | 0.2222 / 0.6528 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 複数段落 | 0.2500 / 0.6528 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |

追加診断:
- Endpoint: 32
- Stable endpoint: 0
- Slow link: 0
- One-shot: Raw 1.0 / Bidirectional 0 / Slow 0
- 干渉後recall: Raw 0.4722 / Bidirectional 0 / Slow 0

## 判定

**中核仮説は強く反証された。**

最大72 event・全seedで、32 endpoint候補からstable endpointは0件だった。query→stateとstate→queryの双方で2回以上成功、複数session支持、wrong 0を要求すると全候補が棄却された。

Raw方式は既知read 0.2500、wrong read 0.6528だった。Bidirectional方式はread 0、wrong 0になった。これはendpoint identityを獲得したのではなく、すべてのendpointを棄却した安全停止である。

stable endpointがないためslow linkも0件。干渉後latest-value recallはRaw 0.4722からBidirectional/Slow 0へ低下した。

支配的失敗は破滅的忘却ではない。初期形成時点でstable endpointが0であり、queryとstateのsurface contextを跨いで同じobject/relation/value endpointを形成できないことが原因である。

## RAG・検索との差

文章を検索して返す方式ではなく、queryからstate内部のvalue addressへ到達し、逆にstate contextからquery familyを再構成し、双方向一致したendpointだけを推論状態へ注入する設計である。ただし実装は文字contextによる小規模episodic transducerで、semantic memoryではない。

## 資源量

- Model: 8,961 bytes
- Training: 0.000885 sec
- Inference: 0.00493 ms/query
- Peak RSS: 160,148 KiB（Python runtime込み）
- 計算量: endpoint抽出 `O(NL)`、双方向監査 `O(AN)`、slow linking `O(AWN)`、read `O(AL)`、`A,W≤32`

1GB未満・5ms未満は小規模制御条件で達成。弱いスマートフォン実機は未検証。

## 系列D固有の進展

> **双方向再構成を厳密gateにすると誤読は止まるが、surface contextが分裂したままではendpointを全棄却する。endpoint identityは再構成成功の完全一致ではなく、失敗原因を因子別に分離して段階的に統合する必要がある。**

## 他系列へ返す知見

- A: 前向きcommitmentを完全一致gateにすると全carry棄却へ退化する危険がある。
- B: forward/inverse導出の完全一致前に、object/value/relation失敗を分離する。
- C: 双方向replayのwrongをevent identity欠如と不可逆性へ分解する。
- E: 複数energy gateの完全交差は候補崩壊を起こし得る。

## 次の仮説

**Factorized Endpoint Evidence with Fast-to-Slow Reconsolidation Ladders**  
（因子別endpoint証拠とfast→slow再固定化ladder）

1. Query/stateのobject候補、relation候補、value候補を独立に保持
2. 各因子のforward/reverse再構成creditを別管理
3. 1回提示ではfast endpointを即時形成
4. wrong因子だけ局所減衰し、全endpointを削除しない
5. 複数sessionで三因子が揃った場合だけslow endpointへ昇格
6. Alias・別状態表現では因子別対応を許可
7. obsolete valueのみ選択的に忘却
8. 主評価: one-shot、wrong read、干渉前後recall、slow precision

## 最終状態

- 高校生級: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機: **未検証**
- 完成: **未達**
