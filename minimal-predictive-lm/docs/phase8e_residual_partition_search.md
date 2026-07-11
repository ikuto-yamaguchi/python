# Phase 8e: residual-driven partition search

## 問題

Phase 8dでは、relation channelを与えずにsurface templateの集合を潜在relationへ分割できた。ただし全set partitionを列挙したため、候補数はBell numberで増加する。

```text
B4  = 15
B8  = 4,140
B12 = 4,213,597
B32 = 128,064,670,049,908,713,818,925,644
```

これは小世界のoracleとしては有用だが、汎用learnerにはならない。

## 仮説

現在のclusterが誤っている場合、同じ内部relationとして扱われたsurface templateの間に、観測effectの衝突が残る。全partitionを列挙せず、その衝突から必要なsplitだけを提案できる。

各templateについて、entity-localな匿名cell名そのものではなく、次の最小署名を計算する。

```text
shared lag
+ each entityで最も支持されたlocal cell rank
```

候補splitは次の3種類に限定する。

```text
lagだけで分割
cell-rank構造だけで分割
lagとcell-rankの両方で分割
```

さらに、現在clusterで実際に誤りを残すtemplateの少数isolationを提案する。過分割を不可逆にしないため、cluster mergeも同じ探索空間へ入れる。

## 局所最適を避ける

最初の改善だけをcommitするgreedy searchにはしない。

- bounded beamで複数partitionを保持
- split後もmergeを許可
- objectiveが一時的に悪い候補もbeam内なら保持
- 4〜8 templateの小世界では全探索oracleと比較
- oracle gapをCIへ固定

ただし、beam searchは一般の大域最適を保証しない。oracle-sized worldでgapを測定し、分布を拡張するたびに反例を追加する。

## 目的と会計

partition modelの選択目的はPhase 8dと同じである。

```text
training error
+ held-out transfer error
+ relation program bits
+ template-to-relation assignment bits
+ entity-local cell calibration bits
```

加えてPhase 8eでは、inductionを無料扱いしない。

- evaluated partition数
- proposed partition数
- fit中のeffect-candidate比較回数
- search round数
- beam幅

を保存する。探索はcompile時に一度だけ行うため、1回・100回・10,000回利用時のamortized check数も報告する。

## 計算量

beam幅を `W`、round数を `R`、template数を `T` とする。signature splitはblockごとに定数種類、residual isolationはblock当たり上限付き、mergeはcluster数 `K` に対して `O(K^2)` である。

固定 `W, R` なら、生成するpartition候補はBell numberではなく、概ね

```text
O(W R (T + K^2))
```

へ制限される。ただし各partitionのfit自体には、trace、entity、cell、lagに比例する計算が必要である。また固定beamが正解候補を落とす反例は存在し得る。

## 実験

4種類の規模を使う。

| templates | hidden relations | exhaustive oracle |
|---:|---:|---|
| 4 | 2 | 実行する |
| 8 | 3 | 実行する |
| 12 | 3 | 実行しない |
| 32 | 4 | 実行しない |

各entityではrelationとsensor cellの対応を入れ替える。1本のtraceには、早い時刻に同じvalueを示す誤cellも混ぜる。held-out entityではrelationごとに1 templateだけ校正し、同relationの未観測paraphraseへ転移できるか測る。

## 成功条件

- 4・8 templateでexhaustive oracleとのobjective gap 0
- 全規模でhidden partitionを完全復元
- held-out entity/paraphrase 100%
- 8 templateで4,140候補を列挙せず50未満のfit
- 12 templateで100未満、32 templateで200未満のfit
- induction check数を結果に残す

## 限界

- 匿名cell timelineという制限されたsensor interface
- deterministic relation
- relationごとに固定lag
- action valueがsensor streamに直接現れる
- fixed beam / round budget
- surface template抽象化は既知のentity/value spanに依存

次段階では、確率的effect、欠測、contradiction、長い遅延、hidden intermediary stateを入れ、残差署名が不安定な場合に必要な追加観測のValue of Informationを選択させる。
