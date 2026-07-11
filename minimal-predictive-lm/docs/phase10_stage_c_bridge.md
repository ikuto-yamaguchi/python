# Phase 10: Stage-C比較へ進むための証拠階層

## Stage Cの定義

Stage Cは、会話、知識、数学、コード、長文理解、創作の6軸すべてで、公開されたopen-domain入力を同じ条件で処理し、対象open modelと品質・資源を比較できる段階です。

各軸の証拠levelを次のように固定します。

| level | 証拠 |
|---:|---|
| 0 | 未測定または能力なし |
| 1 | closed-world synthetic |
| 2 | held-out shiftまたはinteraction適応 |
| 3 | 公開open-domain benchmark |
| 4 | 同一入力・同一tool・同一metricで対象open model以上 |

総合点は24点ですが、平均点だけではStage Cと判定しません。全軸がlevel 4で、公開benchmark・matched input・実測resourceを満たした場合のみ比較claimを許可します。

## 資源会計

品質だけでなく、少なくとも次を同条件で測ります。

- serialized model/program/knowledge bytes
- peak RSS
- active state / KV相当のbytes
- CPU instructionsまたはFLOPs
- wall-clock latency
- energy
- external retrieval bytes
- tool calls
- learning/compilation/verification amortization

小さなsynthetic taskで100%を取っても、open model相当とは数えません。

## Phase 10a snapshot

Phase 9cまでの結果を入れた初期scorecardは5/24でした。

- conversation: level 2。ただし遠い語彙転換6.25%
- knowledge: level 1。closed-world indexed fact lookup
- mathematics: level 0
- code: level 1。synthetic one-function repair
- long context: level 1。synthetic state retention
- creative writing: level 0

このscorecardは、限定タスクでの効率的成功を総合LM性能と混同しないためのanti-overclaim gateです。

## Phase 10b後

自然言語算術programを追加し、数学をlevel 2へ上げました。総合点は7/24です。ただし公開数学benchmarkではなく、一段の生成問題なのでlevel 3には上げません。

## 比較実験へ向かう順序

1. exact math substrateを複数step・方程式・公開benchmarkへ拡張
2. 外部文書retrievalにprovenance・矛盾検出・abstentionを追加
3. synthetic code repairを小さな実repositoryへ移行
4. 長文をtoken列ではなくdecision-sufficient graphへ圧縮し、公開long-context taskで評価
5. 創作をconstraint satisfactionとblind preferenceで評価
6. SmolLM級135Mと0.5〜0.6B級open modelを同じCPU/GPU・入力・tool条件で比較

Stage Cへ到達するまで、モデル相当性能の主張は行いません。
