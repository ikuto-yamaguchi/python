# 系列D Cycle 004 — Boundary-Uncertain Sleep Consolidation with Reversible Rejection

## 結論

未知表現を低速記憶へ統合する際、entity/value境界を一つへ早期確定せず、複数の可逆境界候補を暫定保持し、後続のcross-view証拠で矛盾したschemaを解除する仮説を検証した。

最大540例・3 seed平均で、単一境界へ早期確定する方式は新規view統合後の想起が0だった。一方、複数境界候補を保持して後続証拠で不適合候補を解除する方式は、統合後の新規view想起1.0、50件干渉後の最新値想起1.0を得た。query readsは3、モデル直列化サイズは14,817 bytes、推論は約0.00275 ms/queryだった。

したがって、**意味記憶への統合前に境界・束縛候補の不確実性を保持し、反例で統合を可逆に取り消す**更新原理は、制御日本語上の記憶機構として限定的に支持された。

ただし本実験は、同一episodeの既知viewと未知view、entity/valueの完全表面共参照、関係系列IDを実験器から与えている。自由日本語からepisode grouping、対象、値、関係、質問方向を自律生成しておらず、汎用知能経路としては反証である。

## 他4系列との重複表

| 系列 | 最新中心 | 継承した知見 | 本サイクルの非重複点 |
|---|---|---|---|
| A | 候補未来差分から確認発話を生成 | 競合仮説は追加観測で分離する | 外部質問生成ではなく、観測後に記憶schemaを固定・解除する条件 |
| B | 実行可能binding MDL | episode文を捨て、匿名binding/graphへ圧縮できる | 圧縮graph生成ではなく、境界候補の暫定保持と再固定化解除 |
| C | open-set対照集合誘導 | identity/valueを長期event骨格と分離する | 因果辺ではなく、事実記憶のwrite/read schema競合 |
| E | open-set factor graph緩和 | 境界差だけでは意味候補にならない | energy最小化でなく、後続cross-view反例によるschema撤回 |

A型の質問選択、B型のMDL商、C型の因果world branch、E型の反実仮想緩和は中心機構が重複するため採用しなかった。

## 仮説

未知viewについて次を行う。

1. episode-local entity/valueを既知viewから可逆に抽出する。
2. 未知view上で、正確境界に加えて助詞等を含み得る複数境界候補を生成する。
3. 異なるepisodeで再現した候補だけを睡眠時に低速schemaへ統合する。
4. 後続cross-view証拠と一致しない統合schemaを低速記憶から解除する。
5. entity/valueそのものは高速bindingに保持し、schemaには表面値を保存しない。

予測は、単一境界へ早期確定する方式より、新規view一回提示、干渉後上書き、誤統合解除が改善することである。

## 実装

`boundary_uncertain_sleep_consolidation.py`

- 既知viewからepisode-localな2値を抽出
- 未知viewに対してexact境界と1文字拡張境界を列挙
- 候補ごとに異なるepisode値組のsupportを保持
- sleep時にsupport 2以上の候補を統合
- 後続cross-view証拠で誤った値組を抽出するschemaを解除
- 高速bindingはtimestamp付きで最新値を優先
- queryは3本のquery patternだけを読む

使用していないもの:

- 回答ラベル・answer span
- entity/valueの有限一覧
- 形態素解析器
- Transformer・外部LLM
- RAG・ベクトルDB
- 問題別の回答コード

ただし関係系列ID、同一episodeのview pair、完全表面共参照は実験器から与えている。

## 実験

- 学習規模: 48 / 180 / 540
- seed: 1 / 7 / 19
- 比較:
  - `SingleBoundaryMemory`: 最初の広い境界候補へ早期確定
  - `UncertainSleepMemory`: 複数候補を保持し反例で解除
- 学習済みview一回提示
- 第3viewの反復cross-view統合
- 後続証拠による誤境界解除
- 50件の無関係記憶後の最新値上書き
- model bytes / Peak RSS / 学習・推論時間 / query reads / schema数 / binding数

再現:

```bash
python research/intelligence_swarm/tracks/D_memory_learning/boundary_uncertain_sleep_consolidation.py
```

## 最大540例・3 seed平均

| 指標 | 単一境界 | 境界不確実性保持 |
|---|---:|---:|
| 学習済みview | 1.0000 | 1.0000 |
| 統合後の新規view | 0.0000 | **1.0000** |
| 50件干渉後の最新値 | 1.0000 | 1.0000 |
| 可逆拒否テスト | 1.0000 | 1.0000 |
| 統合候補数 | 3 | 10 |
| 解除候補数 | 3 | 7 |
| 最終schema数 | 6 | 9 |
| binding数 | 170 | 260 |
| model bytes | 9,793 | 14,817 |
| 学習時間 | 0.01395秒 | 0.01501秒 |
| 推論 | 0.00284 ms | 0.00275 ms |
| query reads | 3 | 3 |
| Peak RSS | 287,388 KiB | 287,388 KiB |

Peak RSSはPython runtime込みであり、方式固有値でも弱いスマートフォン実測でもない。

## 支持された部分

1. 境界を一つへ早期確定すると、後続証拠で候補が誤りと判明した際に新規view能力が完全消失した。
2. 複数境界候補を保持すると、不適合候補を7件解除した後も、正しい候補が残り新規view想起1.0を維持した。
3. 低速schemaの解除後も高速bindingの最新値上書きは維持された。
4. query readsは記憶量に依存せず3本で固定された。
5. モデルサイズは約14.8KB、推論約0.00275msで、局所機構は1GB未満・CPU向けの範囲にある。

## 構造的反証

現在の仮説を自由日本語の汎用記憶原理としては棄却する。

1. entity/value境界候補は、既知viewから正しいepisode-local値を抽出できることを前提としている。
2. 未知viewと既知viewが同一episodeであるというgroupingを実験器が与える。
3. entity/valueが同じ表面文字列として両viewへ出現する必要がある。代名詞、表記揺れ、同義語、暗示的照応は扱えない。
4. 関係系列IDを与えており、どの記憶schema候補同士を競合させるかを自律発見していない。
5. 境界候補はexactまたは1文字拡張という狭い列挙で、任意の日本語構造候補生成ではない。
6. 可逆拒否テストは後続cross-view正解値を利用する監査であり、生の観測だけから反例を発見していない。
7. 記憶値の参照・上書き以外の推論、因果、計画、反実仮想、自由生成、対話へ統合していない。
8. 長期容量制御、重要度に基づく選択的忘却、schema間の意味競合は未実装。

## 系列D固有の進展

記憶統合を次の4状態へ拡張できた。

1. 高速episode binding
2. 複数の暫定境界・束縛仮説
3. 反復証拠による低速schema統合
4. 後続反例による低速schema解除

重要な知見は、**統合を可逆にしない限り、初期の境界誤りが長期記憶の能力を不可逆に破壊する**ことである。

一方、次の最大ボトルネックは境界候補の数ではなく、同一episode、同一対象、同一関係を表面一致なしで発見することに移った。

## 他系列へ返す知見

- A: 確認応答を一度受けただけで状態へ固定せず、後続対話と矛盾した場合に状態統合を解除可能にする。
- B: latent operation/view decoderを低速記憶へ統合する際、単一parseを固定せず、複数可逆parseと撤回履歴を保持する。
- C: 因果event schemaは反復対照だけでなく、後続の逆操作・別対象観測で矛盾したときに長期記憶から降格できる必要がある。
- E: 候補緩和の出力を確定記憶へ直結せず、低margin候補を暫定状態へ残し、反例でattractor自体を解除する。

## 次の仮説

**Self-Grouped Episodic Identity Consolidation**

次は実験器が与えるepisode groupingを廃止する。

生の時系列日本語から、複数文が同じepisode/対象/値を指す候補を、以下の証拠で生成・競合させる。

1. 可逆再構成
2. 時間的近接性
3. 後続質問への予測改善
4. 操作前後identity保持
5. 他episodeとの干渉の少なさ
6. 後続反例によるgrouping解除

表面文字列が完全一致しない代名詞・省略・表記揺れを最低限の反証条件とする。成功条件は、grouping教師なしで未知view統合を維持し、誤groupingを可逆に解除しながら、自由日本語統合ゲートを0から改善することである。

- highschool_level_passed=false
- native_japanese_communication_passed=false
- weak_smartphone_verified=false
- completion=false
