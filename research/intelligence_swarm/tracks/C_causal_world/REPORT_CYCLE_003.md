# 系列C Cycle 003: Contrastive Intervention Necessity Graph

## 仮説
観測された状態変化をそのまま因果辺へ昇格させず、同一初期状態近傍における操作あり・操作なしの対照を要求すれば、相関変化と操作必要性を分離できる。

## 他系列との重複回避
- A: 確認発話生成ではなく、介入必要性の判定。
- B: MDL境界生成ではなく、候補イベントの因果昇格条件。
- D: 記憶固定化ではなく、保存前の因果監査。
- E: factor graph緩和ではなく、対照系列からの辺採否。

継承知見: Aのidentity保護、Bの残差は候補に過ぎないという反証、Dの抽象schemaとepisode値の分離、Eの同型候補へ重みを付けても識別不能という反証。

## 実験
32/128/512 episode、seed 1/7/19。表面相関検索と、操作・無操作対照を要求する必要性グラフを比較。通常、未知identity rename、言い換え、無変化confound、逆操作、二段合成を測定。

## 512例・3 seed平均
| 指標 | 相関検索 | 対照必要性 |
|---|---:|---:|
| 通常 | 0.3111 | 1.0000 |
| rename | 0.0000 | 1.0000 |
| 言い換え | 0.3111 | 1.0000 |
| 観測後confound拒否 | 0.0000 | 1.0000 |
| 逆操作 | 0.3444 | 1.0000 |
| 二段合成 | 0.3333 | 0.6722 |
| model bytes | 148,212 | 14,044 |
| inference | 5.128 ms | 2.646 ms |
| reads | 1,024 | 3 |

Peak RSSは394,208 KiBでPython実行環境込み。

## 厳格監査と判定
正の結果はそのまま採用できない。target value抽出に有限の`VALUES`集合、状態表現に3個の固定surface patternを使用している。これは固定ontology依存であり、ユーザー条件を満たさない。したがって本実装は汎用因果原理として棄却する。

それでも限定的に残る知見は、**操作あり／なしの対照は、観測後に因果予測を監査する信号として有効**という点である。未解決なのは、生の日本語から対象・値・操作境界と対照集合をopen-setに生成する部分。

## 次仮説
`Open-Set Contrast Set Induction`。Bの複数可逆parse、Dのcross-view binding、Eの異構造factor候補を使い、固定値集合なしで操作・無操作・逆操作・別対象操作の対照集合そのものを誘導する。成功条件は、未知構文と言い換えでconfound拒否と通常精度を同時改善し、有限ontology監査を通過すること。

- highschool_level_passed=false
- native_japanese_communication_passed=false
- weak_smartphone_verified=false
- completion=false
