# 系列C Cycle 006 — Context-Conditioned Counterfactual Event Algebra

## 仮説

Cycle 005 では、operation node と episode-local identity/value binding の分離により、既知命令について rename・逆操作・別 identity・二段合成が成立した。一方、状態文脈から action / no-op / blocked branch を選ぶ条件は誘導できなかった。

本サイクルでは、**操作結果が変化した episode と変化しなかった episode の文脈残差を、意味名を付けずに競合させれば、identity-factored event program を維持したまま branch gating を誘導できる**という仮説を検証した。

学習器へ「通常」「固定中」「blocked」等の mode label、entity/value 一覧、形態素解析、手書き slot、固定 ontology は与えていない。状態文・命令文・結果文の文字対応から event program と episode binding を誘導し、状態文に残った context residue を action/no-op 結果別に保存した。

## 他系列との重複表

| 系列 | 最新の中心機構 | 今回の系列Cとの違い |
|---|---|---|
| A | 候補エントロピーに応じた対話修復 | 外部質問ではなく、観測前の world-branch gating |
| B | role-factored MDL encoder | 未知 predicate encoderではなく、既知 event の文脈条件選択 |
| D | predictive retrieval gain による episode grouping | 長期記憶統合ではなく、介入実行前の状態条件 |
| E | role-structured conditional attractor graph | 候補energy緩和ではなく、branch条件候補そのものの最小誘導 |

系列Bの「role factoring は語順variantに部分的効果があるが未知lexemeには効かない」、系列Eの「同型候補へscalar penaltyを足しても選別できない」、系列Dの「異なる未来を生まない候補は別仮説として価値がない」を継承した。

## 実装

比較方式:

1. `event_only`
   - identity/valueを分離した event program
   - contextに関係なく常に action branch を適用

2. `context_algebra`
   - 上記 event program
   - action episode と no-op episode の context residue を匿名文字 n-gram 状態として保持
   - 入力文脈が action/no-op のどちらへ近いかを比較
   - marginが小さい場合は棄権

候補branchは `action / no-op / unknown` の3状態。正答ラベルではなく、介入前後が変化したかどうかという観測結果だけを使用した。

## 実験条件

- 学習量: 32 / 128 / 512 action episode
- no-op episode: 最大256
- seed: 1 / 7 / 19
- 通常の既知context
- entity/value全面rename
- 未学習命令構文
- 未学習context表現
- 命令・contextの両方未学習
- action-only
- blocked/no-op-only
- モデルサイズ、学習時間、推論時間、候補読出し、program数
- 自由日本語統合ゲート

## 512例・3 seed平均

| 指標 | event only | context algebra |
|---|---:|---:|
| 通常精度 | 0.4833 | **1.0000** |
| rename精度 | 0.5667 | **1.0000** |
| 未学習命令構文 | 0.0000 | **0.5417** |
| 未学習context | 0.0000 | 0.0000 |
| 命令・context両方未学習 | 0.0000 | 0.0125 |
| action branch | 1.0000 | 1.0000 |
| blocked/no-op branch | 0.0000 | **1.0000** |
| モデルサイズ | 8,400 B | 292,294 B |
| 学習時間 | 0.02150 s | 0.04304 s |
| 推論時間 | 0.0976 ms | 2.7938 ms |
| 候補読出し | 4 | 20 |
| event program数 | 24 | 24 |

Peak RSS: 299,568 KiB。Python runtime全体を含み、方式固有値でもスマートフォン実測値でもない。

## 支持された部分

既知contextの範囲では、action/no-op outcomeから誘導したcontext residueにより、

- 通常精度: 0.4833 → 1.0000
- rename: 0.5667 → 1.0000
- blocked/no-op: 0.0000 → 1.0000

となった。

したがって、次の限定原理は支持される。

> **operationとepisode bindingを分離した後、介入結果の有無で文脈残差を分けると、既知の文脈表現についてaction/no-op branchを観測前に選択できる。**

Cycle 005で未成立だった branch gating を、固定mode slotなしで局所的には実現した。

## 決定的な反証

中核のopen-set因果世界モデル仮説は反証である。

### 1. 未学習contextへ完全に転移しない

未学習context精度は0.0000、命令とcontextの両方未学習も0.0125だった。

「扉が閉じている」と「出入口を通れない」が同じblocked条件だとは理解していない。既知context residueの表面類似を再利用しただけである。

### 2. 未学習命令構文も0.5417に留まる

系列B Cycle 006のrole factoringと同様、既知predicate断片や既知command skeletonが残る場合だけ部分転移する。完全なopen-set operation encoderではない。

### 3. モデルサイズが経験数へほぼ線形増加

context prototypeをepisodeごとに保持したため、512規模で292,294 bytesとなり、event-onlyの8,400 bytesより約34.8倍大きい。1GB未満ではあるが、軽量な一般原理とはいえない。

### 4. branch条件が因果変数ではない

内部表現はcontext文字列のn-gram集合であり、

- 通過可能性
- 許可
- 障害物
- 安全制約

のような再利用可能な状態変数へ分解されていない。新しい表現、新しい関係、新しい阻害理由へ転移できない。

### 5. 自由日本語統合能力は0

主語省略、複数段落、自然な反実仮想、目的・制約の生成、自由対話、読解、計画変更、継続学習は未達である。

## 系列C固有の進展

因果eventの問題を三段階へ分解できた。

1. **identity-factored event algebra**
   - 別identity、逆操作、合成へ再実行
   - Cycle 005で限定成立

2. **context-dependent branch gating**
   - action/no-op/blockedの選択
   - 今回、既知context表現で限定成立

3. **open-set causal condition abstraction**
   - 異なる日本語表現・異なる阻害理由を同じ因果条件へ統合
   - 完全未成立

最大ボトルネックは、branch scoreではなく、**異なるsurface contextを同じ可介入状態変数へ統合するcondition encoder**である。

## 他系列へ返す知見

- **Aへ:** 確認質問で得るべき情報は表面値だけでなく、どのbranch条件が成立するかを分離するcontext変数である。
- **Bへ:** effect-conditioned primitive inductionはpredicateだけでなく、同じaction/no-op差を生むcontext residueも一primitiveへ統合する必要がある。
- **Dへ:** branch condition schemaは、異なる表現・異なるepisodeで再現するまで低速記憶へ固定すべきでない。
- **Eへ:** role-structured候補にはoperation roleだけでなく、異なるsurface表現を共有するcontext-condition nodeが必要である。

## 次の仮説

**Intervention-Equivalence Condition Quotient**

次はcontext prototype保存を廃止する。異なるcontext文が、同じoperationに対して同じaction/no-op差を繰り返し生む場合にのみ、共通の潜在condition nodeへ統合する。

候補conditionは次の証拠で競合させる。

1. 元文の可逆再構成
2. 同一operationでのaction/no-op効果同値
3. 別identityへの転移
4. 別operationでの再利用または選択的非再利用
5. 逆操作・二段合成時の一貫性
6. 新context表現へのone-shot bridging
7. prototype保存量の非線形化

必須成功条件は、今回0だった未学習contextを改善し、rename・blocked選択性を維持しながら、モデルサイズを大幅に削減することである。

## 最終判定

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: 未達
