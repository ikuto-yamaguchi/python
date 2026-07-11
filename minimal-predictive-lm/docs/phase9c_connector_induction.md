# Phase 9c: interaction effectからのconnector意味誘導

## 問題

Phase 9bは一文中の複数event、条件、内容、参照、順序を疎なevent graphへ分解できましたが、`なら`、`その後`、`その変更`などのconnector inventoryは一部手書きでした。このまま語彙だけを増やすと辞書化し、自由言語へスケールしません。

Phase 9cではconnector文字列にrelation labelを直接与えません。観測するのは、connectorを含むinteractionの前後で、

- propositionが真か偽か
- actionが実行されたか
- 直前eventを参照したか
- 発話内容を内包したか
- 時間的後続になったか

です。

## 候補と目的

有限検証段階では、候補roleを

```text
SEQUENCE
CONDITION_TRUE
CONDITION_FALSE
REFERENCE
CONTENT
```

とします。connector `c` のroleは、

\[
r^*(c)=\arg\min_r\{L(c)+L(r)+L(D_c\mid r)\}
\]

で選びます。

`L(D_c | r)` は各観測effectに対するBernoulli code lengthです。たとえば `CONDITION_TRUE` は propositionが真のときだけactionが実行されると予測し、`REFERENCE` は直前eventへの参照を予測します。

## 結果

- 基本connector 5種、10 interaction: role復元100%
- 新しいconnector 5種、10 interaction: role復元100%
- 新connectorの表面一致: 0%
- 誘導後のevent graph 6ケース: event recall 100%、edge recall 100%
- unresolved clause: 0
- connector 10種のlexicon: 1,144bit
- candidate評価: 50

重要なのは、新しいconnectorを既存文字列に似ているから分類したのではなく、そのconnectorが世界・会話状態へ与えたeffectから分類した点です。

## 限界

候補relationの種類自体はまだ与えています。また、interaction traceが実行、参照、内容、時間順序を観測可能にしています。次段階では、relation inventory自体を残差衝突からsplit/mergeし、長距離依存、入れ子条件、談話関係へ拡張します。
