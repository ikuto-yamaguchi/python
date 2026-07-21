# 系列C Cycle 004: Open-Set Contrast Set Induction

## 目的

Cycle 003 の `Contrastive Intervention Necessity Graph` は、操作あり／なしの対照を入れると高精度になった一方、有限の `VALUES` 集合と固定状態表現へ依存していたため、open-set 日本語因果誘導の証拠として棄却した。

本サイクルでは、対象名・状態値の既知集合をモデルへ与えず、操作、無操作、逆操作、別対象操作の **対照集合そのもの** から、episode identity と状態変化の候補を誘導できるかを検証する。

## 他系列との重複表

| 系列 | 最新中心機構 | 成功・失敗 | 本サイクルとの差 |
|---|---|---|---|
| A | 予測不一致から確認発話を生成 | literal 二択は生成できるが自由回答解釈0 | 外部確認ではなく、対照経験集合の自己誘導 |
| B | cross-view MDL program quotient | 同義動詞は改善、語順・圧縮・confoundは失敗 | 記述長ではなく操作／無操作／逆操作の必要性 |
| D | 未知viewの睡眠型統合 | 反復viewは追加可能、完全新構文0 | 記憶固定化ではなく因果event昇格前の対照監査 |
| E | open-set factor graph relaxation | candidate recall 0、全面棄権 | energy緩和ではなく、実行可能な対照bundleの抽出 |

## 既存研究との対応

未知介入targetを含む causal representation learning でも、単一観測だけではなく複数intervention environmentの多様性がidentifiabilityに重要である。本実験はそのニューラル表現部分を再現するものではなく、「文字列から抽出した候補が、対照環境を追加するだけで因果的構造へ昇格するか」という最小反証プローブである。

参考:

- Nonparametric Identifiability of Causal Representations from Unknown Interventions, NeurIPS 2023
- General Identifiability and Achievability for Causal Representation Learning, AISTATS 2024
- Identifying Linearly-Mixed Causal Representations from Multi-Node Interventions, CLeaR 2024

## 仮説

`Open-Set Contrast Set Induction`:

1. 介入前後の共通部分から episode identity 候補を生成する。
2. 前後差分と命令内の新規共有区間から状態値候補を生成する。
3. 操作時に変化し、無操作時に保持され、逆操作で復元され、別対象操作で非干渉ならイベント規則へ昇格する。
4. 対象名・状態値の有限語彙はモデルへ与えない。

比較:

- `action_only`: 操作による変化と無操作保持だけを要求。
- `full_contrast`: さらに逆操作復元と別対象非干渉を要求。

## 実装

- 文字列の共通substringとprefix/suffix差分だけから identity / old / new 候補を抽出。
- 抽出した表面値は長期規則へ保存せず、`<ID>`, `<OLD>`, `<NEW>` へ匿名化。
- 推論時に入力から匿名値を再束縛してafter stateを生成。
- 固定entity/value ontology、形態素解析、回答ラベル、RAG、外部LLMは不使用。

自己テスト:

```bash
python research/intelligence_swarm/tracks/C_causal_world/open_set_contrast_induction.py --self-test
```

実験:

```bash
python research/intelligence_swarm/tracks/C_causal_world/open_set_contrast_induction.py
```

## 実測

学習量 32 / 128 / 512 bundle、seed 1 / 7 / 19。

### 512 bundle・3 seed平均

| 指標 | action-only | full-contrast |
|---|---:|---:|
| 通常精度 | 0.6556 | 0.6556 |
| entity/value全面rename | 0.6806 | 0.6806 |
| 完全未見命令構文 | 0.0000 | 0.0000 |
| confound拒否率 | 1.0000 | 1.0000 |
| 直列化モデル | 2,211 B | 2,211 B |
| 学習時間 | 0.0353 s | 0.0351 s |
| 推論時間 | 0.0113 ms | 0.0111 ms |
| 誘導規則数 | 21 | 21 |
| 規則読み出し | 21 | 21 |
| 棄却bundle | 64 | 64 |

Peak RSS は Python runtime 込みで 292,588 KiB。スマートフォン固有実測ではない。

## 支持された部分

有限のentity/value一覧をモデルへ渡さなくても、介入前後・命令間の表面共通性から匿名binding規則を作り、未知名称へのrenameで約0.68を得られた。モデルサイズも2.2KB、推論約0.011msであり、局所機構は軽量である。

## 明確な反証

### 1. full contrast が action-only と完全に同一

逆操作・別対象操作を追加しても、規則数、精度、拒否率、モデルサイズがすべて同じだった。

原因は、候補規則が「一つの文字列編集」でしかなく、操作世界、無操作世界、逆操作世界、別対象操作世界を **別branchとして内部表現していない** ためである。追加対照は候補採否のbooleanを増やしただけで、イベント構造を変えなかった。

したがって、対照データを追加するだけでは因果候補は豊かにならない。

### 2. 未見構文は完全に0

対象・値renameには部分転移したが、完全未見の命令構文は全seed・全規模で0だった。

匿名化したのは表面値だけであり、命令構造は既知literal skeletonへ依存している。これはopen-set構造誘導ではない。

### 3. confound拒否1.0は選択的因果理解ではない

confoundはafter stateがbeforeと同じため、学習規則と出力が一致せず拒否される。これは観測後の不一致検出であり、命令実行前に因果必然性を理解した結果ではない。

### 4. 通常精度が0.66で頭打ち

32から512へデータを16倍にしても、128以降は改善しない。候補境界の誤抽出とliteral skeleton不一致が構造的上限になっている。

## 系列C固有の発見

> 対照集合は候補の採否条件ではなく、各仮説が異なる世界を実行生成する構造として内部化されなければならない。

操作あり／なし／逆操作／別対象操作をboolean監査へ追加しても、単一編集programの意味は変わらない。因果候補には、少なくとも各world branchで異なる予測を生成し、そのcross-world不変量と変化量を比較できる表現が必要である。

## 他系列へ返す知見

- A: 候補世界が本当にbranchしていなければ、予測不一致から意味ある確認を生成できない。
- B: 対照viewを共同圧縮する際、表面prototype群ではなくworld branch間の共有programと差分を符号化する必要がある。
- D: 反復対照が得られても、単一編集schemaへ睡眠統合すると因果構造を失う。
- E: full contrastがaction-onlyと同一だったことは、対照factorを重みとして足すだけでは無効というCycle 003の反証を再確認する。

## 次の仮説

`Executable Counterfactual Branch Induction`:

- 一つの編集規則を採点する方式を廃止。
- 入力ごとに、操作・無操作・逆操作・別対象操作・二段合成の世界branchを生成。
- branch間で、identity保存、変更relation、非対象への非干渉、逆操作復元を別々に表現。
- 同じ表面命令でもbranch予測が異なる複数hypothesisを保持。
- 観測された一部branchから未観測branchを予測し、そこを反証する。

成功条件は、固定ontologyなしで未見構文精度を0から改善し、通常精度を維持しつつ、観測前confound予測、逆操作、別対象非干渉、二段計画を同時改善すること。

## 完成判定

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: false
