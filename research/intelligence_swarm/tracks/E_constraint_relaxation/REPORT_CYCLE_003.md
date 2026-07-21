# 系列E Cycle 003: Open-Set Factor Graph Proposal and Contrastive Relaxation

## 結論

入力ごとに境界・束縛方向が異なる候補factor graphを生成し、可逆再構成・identity保持・対照証拠で緩和する仮説を検証した。候補グラフの構造分岐自体は実装できたが、意味的に正しい候補を生成できず、通常・未知構文とも正答率0だった。対照factorを追加しても `relax_no_contrast` と `open_factor_relax` の能力が同一であり、中核仮説は反証された。

## 他系列との重複表

| 系列 | 最新中心機構 | 今回の非重複点 | 継承知見 |
|---|---|---|---|
| A | 予測不一致から確認を選択 | 外部確認をせず、内部候補graph生成と緩和を検証 | 同型候補を保持するだけでは不十分 |
| B | cross-view MDL商 | 記述長でなく構造の異なるfactor graph間の整合性 | 表面prototype保存は意味graphではない |
| C | 操作/無操作の対照必要性 | 因果辺ではなく、対照factorが候補構造を選別できるか | 無介入対照を独立枝にする必要 |
| D | 未知viewの睡眠統合 | 長期記憶でなく、その場の境界・束縛仮説の競合 | 境界不確実性を早期確定しない |

## 仮説

生の文字列からentity境界、old/new value境界、entity-first/value-firstの束縛方向、操作後の置換候補が異なるgraphをopen-setに列挙する。可逆再構成、identity保存、commandとの共有区間、無介入対照をfactorとして疎な候補集合を反復緩和すれば、表面最近傍より未知構文へ転移するはずだと予測した。

## 実装

`open_set_factor_graph.py` は形態素辞書、意味slot名、固定ontology、外部LLM、RAG、回答ラベルを使用しない。文字列対応から境界のtrim variantを含む候補を列挙し、候補ごとに異なるfactor graphを作る。

比較:

1. `greedy`: 最良表面候補1件
2. `relax_no_contrast`: 複数候補を可逆性・identityで緩和
3. `open_factor_relax`: 無介入対照factorも追加

停止条件は、1 sweepで最良候補が変化しない、または最大8 sweep。実測では平均2反復で停止した。

## 実験条件

- seeds: 1 / 7 / 19
- 学習: seedあたり12 episode
- 評価: seen / 完全未見命令構文 / no-op混在confound
- 人工データ生成器のentity/value一覧は評価用であり、学習器には渡していない
- 小規模probeであり、結果の統計精度は低い

## 3 seed平均

| 指標 | greedy | relax_no_contrast | open_factor_relax |
|---|---:|---:|---:|
| seen accuracy | 0.0000 | 0.0000 | 0.0000 |
| unseen syntax accuracy | 0.0000 | 0.0000 | 0.0000 |
| confound accuracy | 0.0417 | 0.0417 | 0.0417 |
| confound abstention | 0.1667 | 1.0000 | 1.0000 |
| model bytes | 835 | 4,561.7 | 4,569 |
| training seconds | 0.00468 | 0.00492 | 0.00465 |
| unseen inference ms/query | 7.32 | 20.54 | 20.52 |
| mean iterations | 1 | 2 | 2 |
| active candidates | 19.25 | 19.25 | 19.25 |
| prototypes | 6.67 | 36.67 | 36.67 |

Peak RSSは281,440 KiB。Python runtime込みで方式固有値ではない。

## 反証

### 正しい意味候補が候補集合へ入らない

境界・束縛方向を分岐させても、候補生成は文字列共通区間と差分に依存する。助詞・述語・値境界が混ざり、正しい置換プログラムが安定して含まれなかった。energy最小化以前のcandidate recallが最大ボトルネックである。

### 対照factorが順位を変えない

`relax_no_contrast` と `open_factor_relax` は全能力指標が同じだった。無介入証拠をスカラー重みとして追加しても、候補graphに操作世界と無操作世界の構造的な別枝がないため、同型候補へ同じ信号を与えるだけだった。

### 棄権100%は理解ではない

緩和方式のconfound abstentionは1.0だが、通常入力でも正答0である。margin collapseによる全面拒否であり、矛盾の選択的検出ではない。

### 計算コスト悪化

候補を約19件保持すると、推論はgreedyの約7.3 msから約20.5 msへ悪化した。能力向上がないため、この動的計算深度は正当化できない。

## 系列E固有の知見

> factor graph候補の個数や境界の違いだけでは構造多様性にならない。候補間で反実仮想的な実行結果が異なり、操作世界・無操作世界・逆操作世界を別々に生成できなければ、対照energyは候補を選別できない。

次のボトルネックは重み・緩和法ではなく、候補graphに実行可能な世界分岐を生成することである。

## 他系列へ返す知見

- A: 予測不一致から質問を作る前に、候補世界が異なる未来を実際に生成できる必要がある。
- B: MDL parseは境界差だけでなく、実行結果が異なるprogram graphを生成しなければならない。
- C: 無介入対照はスカラーfactorではなく、操作あり/なしの別world branchとして表現すべき。
- D: 境界候補を暫定保持する際、後続観測に対する異なる予測を生成できない候補は統合対象にしない。

## 次仮説

**Counterfactual World-Branch Proposal with Executable Relaxation**

次は文字置換候補の順位付けをやめ、各候補graphから操作実行世界、無操作世界、逆操作世界、別対象操作世界、二段合成世界を実行生成する。各世界の可逆再構成、identity保存、観測一致、逆操作復元、別対象非干渉によって緩和する。

成功条件は通常精度と未知構文精度を0から改善し、通常入力を保ったままconfoundだけを選択的に棄権すること。

- highschool_level_passed=false
- native_japanese_communication_passed=false
- weak_smartphone_verified=false
- completion=false
