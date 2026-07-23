# 系列D Cycle 022 研究報告

## 仮説

**Value-Change Equivalence Classes from Cross-Surface Write Consequences**  
（surface横断write consequenceからのvalue-change同値類）

Cycle 021ではobject・relation・value endpointを独立化すると誤読は減ったが、value endpointがsurface contextごとに分裂し、slow bindingは0件だった。

今回は三因子全体を同時に固定せず、command内value候補とbefore→after変化区間を局所write consequenceで比較した。異なるsurfaceでも、old/new局所shape、write成功、wrong write不在、non-target保存、inverse read support、複数session supportが一致する候補をvalue-change classへまとめ、fast trace / value class / slow value classを比較した。

## 他系列との重複表

| 系列 | 最新中心 | 限定成功 | 主な未解決 | Dとの分離 |
|---|---|---|---|---|
| A | 残差逆投影と談話carry | 候補内test識別 | open-set birth 0 | active queryは扱わない |
| B | edit graph反単一化 | filler再利用 | context transport 0 | grammar/MDLは扱わない |
| C | 対称情報event direction | 評価漏れ除去 | causal direction未成立 | world modelは扱わない |
| E | 制約別basin分岐交差 | null安全停止 | value birth消失 | energy dynamicsは扱わない |
| **D** | **value change consequenceのfast/slow記憶統合** | 今回検証 | semantic value class | 系列固有 |

## 最大144 event・3 seed平均

| 条件 | Trace write/read | Value class write/read | Slow class write/read |
|---|---:|---:|---:|
| 既知 | 0.2407 / 0.2037 | 0.2407 / 0.0000 | 0.2407 / 0.0000 |
| 未学習言い換え | 0.2407 / 0.2037 | 0.2407 / 0.0000 | 0.2407 / 0.0000 |
| Rename | 0.1852 / 0.2037 | 0.1852 / 0.0000 | 0.1852 / 0.0000 |
| 別状態表現 | 0.0000 / 0.1481 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 主語省略 | 0.0000 / 0.2037 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 複数段落 | 0.2407 / 0.2037 | 0.2407 / 0.0000 | 0.2407 / 0.0000 |
| 未知domain | 0.2407 / 0.2037 | 0.2407 / 0.0000 | 0.2407 / 0.0000 |

追加評価:

- one-shot: Trace / Class / Slow = 1.0000 / 1.0000 / 1.0000
- 干渉後latest-value recall: 0.0556 / 0.0000 / 0.0000
- value class: 12.00
- slow value class: 10.67

## 判定

**中核仮説は強く反証された。**

Value classを12個、slow classを平均10.67個形成しても、write能力増分は0だった。既知readはTrace 0.2037からClass/Slow 0へ低下し、wrong readは0.7963から1.0へ増えた。同じ局所write consequenceを持つことは、同じquery-conditioned value identityを意味しない。

Cycle 021ではslow binding 0だったが、今回は平均10.67 slow value classが形成された。しかし干渉後recallはTrace 0.0556からClass/Slow 0へ悪化した。複数session・write成功・damage 0というgateだけではsemantic reconsolidationにならない。

One-shot 1.0は同じepisode直後の局所template再実行であり、未知surfaceへの一般化や長期保持の証拠ではない。支配的失敗は破滅的忘却ではなく、**write consequenceの同型性をvalue identityへ早まって商形成した誤統合**である。

## RAG・検索との差

保存文を返すのではなく、局所traceを別surfaceへ適用して内部stateを書き換え、value classをread/write推論状態へ注入する。しかし現在は文字context依存のepisodic transducerであり、semantic memoryには未達。

## 資源量

- Slow model: 16,964 bytes
- Training: 0.003577 sec
- Inference: 0.345744 ms/read-or-write
- Peak RSS: 160,136 KiB（Python runtime込み）
- Trace: 96
- Value class: 12.00
- Slow class: 10.67
- 推定計算量: trace抽出 `O(NL)`、consequence grouping `O(T)`、read/write `O(TL)`、`T ≤ 96`

1GB未満・5ms未満は制御条件で達成。弱いスマートフォン実機では未検証。

## 系列D固有の進展

> **同じwrite consequenceを持つvalue mentionは、write template共有には使えてもread identity共有には使えない。write-only equivalenceとquery-conditioned read addressを同じslow classへ統合すると誤読と干渉を悪化させる。**

## 他系列へ返す新知見

- A: 候補が同じfuture outcomeを持っても、同じ逆引きaddressとは限らない。
- B: derivation equivalenceを生成方向とinverse retrieval方向で別々に符号化する。
- C: forward transition同型性だけでevent/state identityを統合しない。
- E: 同じenergy consequenceを持つfactorでもread endpointは別反証が必要。

## 次の仮説

**Dual-Channel Value Memory with Write-Only Equivalence and Query-Conditioned Read Addresses**

write consequence classはstate更新だけに利用し、read側はquery/object/relation endpointから独立にvalueへ到達させる。両経路が同じvalueへ到達した場合だけslow cross-linkを形成し、干渉後latest-value recallとwrong readを主評価にする。

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
