# 系列B Cycle 014 研究報告

## 仮説

**Clause-Lattice Misapplication Execution with Relation Quotient Induction**  
（clause格子上の実行的誤適用とrelation商誘導）

Cycle 013では、anchor長・singleton alias・old/new多様性による誤適用risk proxyが候補を追加棄却しても、全能力が変化しなかった。今回は状態全文のsingle diffを廃止し、句読点・改行・隣接clauseから小さな格子を生成した。各候補を実際にbefore stateへ適用し、観測afterを再現できる候補だけを保持する。さらに同じwrite programを別clauseへ誤適用し、異なるworld破壊を生む候補を排除した後、観測同値な候補をMDLでrelation quotientへ統合した。

## 先行研究整理

- Hocquette & Cropper, *Relational Decomposition for Program Synthesis* (IJCAI 2025): 入出力全体をfact集合へ分解し、fact間relationを学習する表現が標準表現を上回り得る。今回のclause分解の直接的な先行根拠。ただしfact境界は与えられており、生日本語からの自律境界形成は未解決。
  - https://www.ijcai.org/proceedings/2025/504
- Frankel et al., *Syntax-guided synthesis with counterexample-guided E-graphs* (SMT 2025): 観測同値をe-graphへ持ち上げて探索爆発を抑える方向を示す。今回のrelation quotientに対応するが、誤った観測同値を圧縮すると正候補まで潰す危険がある。
  - https://www.research.ed.ac.uk/en/publications/syntax-guided-synthesis-with-counterexample-guided-e-graphs-a-wor/
- *Symbolic metaprogram search improves learning efficiency and explains rule learning in humans* (Nature Communications, 2024): AntiUnifyをmetaprimitiveとして使うと、構造を利用して変数導入探索を削減できる。ただし入力構造が意味的roleへ整列していることが前提。
  - https://www.nature.com/articles/s41467-024-50966-x
- Relational synthesis・CEGISは関係仕様や反例によって候補空間を絞るが、適切なDSL・変数・仕様が存在することを前提とする。今回の課題は、その仕様自体を生日本語から創発する上流問題である。

## 過去実験知見の集約

1. Cycle 008: 可逆性とMDL短縮は実行可能role/effect programを保証しない。
2. Cycle 009: 単一episodeのafter再現はprogram groundingとして弱すぎる。
3. Cycle 010: cross-episode置換監査は既知性能を維持してprogram数・モデル・読出しを約半減した。
4. Cycle 011: 文字境界を精密化してもrole境界にならず、推論時bindingが再爆発した。
5. Cycle 012: observational preservationはexact reconstructionに包含され、増分情報0だった。
6. Cycle 013: surface-risk proxyは上位program classを一つも分割せず、既知精度0.0306だった。

## 他系列との重複表

| 系列 | 最新仮説・中心機構 | 成功 | 失敗・未解決 | B候補との判定 |
|---|---|---|---|---|
| A | Causal-survival probe program | 一部未知条件で誤確定削減 | candidate recall低、probeは文字fingerprint | 外部観測policyなので棄却 |
| C | intervention persistenceによるobject node | 次はidentity nodeを先に形成 | Cycle 013のclause swapはobject surgeryにならず | object/world node形成なので棄却 |
| D | cross-query write/read address | 次はtarget/unrelated query不変性 | paraphrase統合が過圧縮、干渉後0 | 長期memory addressなので棄却 |
| E | residual-cause bipartite attractor | 複数残差で平坦化解除 | 誤候補一意化または全面平坦化 | energy・credit routingなので棄却 |
| **B** | **clause格子でprogram候補を生成し、実誤適用後にMDL商を作る** | 今回検証 | relation quotientの意味同値性 | 系列固有 |

### 他系列から継承した知見

- A: 候補削減量・生存率だけでは意味的妥当性を示さない。実行outcomeが必要。
- C: identity nodeなしのclause交換はobject surgeryではない。
- D: 圧縮率だけでschemaを統合するとwrite/read能力が壊れる。
- E: 候補classを実際に分割しないfactor・反例は増分情報0である。

## 設計

### Clause lattice

固定ontologyやfield辞書を使わず、次から候補nodeを作る。

- 句点・読点・セミコロン・改行による単一clause
- 隣接する二clauseの結合
- before/afterで異なるclause pair
- commandに出現するnew substringを含む局所変換

全substring直積は使わず、候補をepisode当たり96以下へ制限した。

### 実行的誤適用

候補programをbefore stateの全clauseへ再適用し、次を測る。

- 観測afterを厳密再現するか
- 同一programが複数clauseへ適用可能で曖昧にならないか
- 別clauseへ適用した際に異なる破壊worldを生成するか

### Relation quotient / MDL

具体old/new値を除外した局所context signatureで候補を商空間化し、次のscoreで保存する。

- cross-episode support
- cross-form support
- 記述長
- 誤適用破壊risk

## 反証条件

中核仮説は以下のいずれかで反証とした。

- 実誤適用ablationが既知・未知表現を改善しない
- quotient圧縮が精度を維持せず、単なる表面同値圧縮になる
- 未知語順・主語省略・別状態表現のいずれも0から改善しない
- 実行候補が100/queryを超える
- モデル1GB以上、推論5ms/query以上
- 評価用object/field/valueをlearnerへ漏洩する

## 実験

- 学習量: 48 / 144 / 432 episode
- seed: 1 / 7 / 19
- 各split: 100例 / seed
- 比較:
  1. clause supportのみ
  2. clause + executable misapplication
  3. executable misapplication + relation quotient MDL
- split:
  - 既知表現
  - 未知語順
  - 未知言い回し
  - 入れ子
  - 主語省略
  - 別状態表現
  - 複数文自由形式

learnerが読むのはraw before / command / afterのみ。hidden object / field / valueはデータ生成と評価だけに使用した。

## 最大432 episode・3 seed平均

| 条件 | Clause | Misapplication execution | Quotient MDL |
|---|---:|---:|---:|
| 既知 | 0.0633 | **0.2533** | 0.0967 |
| 未知語順 | 0.0000 | 0.0000 | 0.0000 |
| 未知言い回し | 0.0267 | 0.1800 | **0.2133** |
| 入れ子 | 0.0633 | **0.2533** | 0.0967 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 |
| 別状態表現 | 0.0000 | 0.0000 | 0.0000 |
| 複数文自由形式 | 0.0000 | 0.0000 | 0.0000 |

## 資源測定

| 指標 | Clause | Misapplication | Quotient |
|---|---:|---:|---:|
| モデルサイズ | 4717 B | 5751 B | 4574 B |
| 保存program | 32.0 | 32.0 | 23.3 |
| raw候補 | 4378 | 4378 | 4378 |
| 棄却候補 | 143.3 | 3891.3 | 3891.3 |
| 学習時間 | 0.2044s | 0.2269s | 0.2280s |
| 推論時間 | 0.0093ms | 0.0075ms | 0.0043ms |
| 読出し候補 | 0.207 | 0.420 | 0.150 |

- Peak RSS: 298488 KiB（Python runtime込み）
- 推定計算量:
  - clause proposal `O(N C²)`
  - program execution `O(P C)`
  - clause lattice `O(L)`
  - `P <= 32`, episode候補 `<= 96`
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 判定

### 限定的に支持された部分

実誤適用方式はclause support方式に対して、

- 既知: 0.0633 → **0.2533**
- 未知言い回し: 0.0267 → **0.1800**
- 入れ子: 0.0633 → **0.2533**

へ改善した。

また、約4378 raw候補のうち約3891を実行不一致・誤適用曖昧性で棄却した。Cycle 013のsurface-risk proxyとは異なり、候補を実際にworld文字列へ適用した結果が上位program classを変えた。

したがって、次の部品原理は限定的に残せる。

> **状態全文diffではなくclause-local候補を生成し、観測after再現と別clause誤適用を実行してから統合することは、候補precisionに増分情報を持つ。**

### 中核仮説の反証

1. **Relation quotientが能力を維持しない**
   - 実誤適用の既知0.2533をquotientは0.0967へ悪化させた。
   - program数は32から23.33へ減ったが、意味同値でなく局所prefix/suffix同値を統合している。

2. **未知語順・主語省略・別状態表現・自由形式は0**
   - command contextが既知順序と一致しないとnew valueを束縛できない。
   - 主語省略には談話focus/object permanenceが必要で、clause latticeだけでは候補生成不能。

3. **既知精度も0.2533止まり**
   - clause-local化しても、どのclauseがobject、relation、valueを担うかを意味的に識別していない。

4. **MDLは誤った商を好む**
   - 短い局所contextと多数supportを持つsurface familyが、異なるrelationを混ぜても高scoreになる。

5. **自由日本語統合ゲートは未成立**
   - 自由対話、指示遂行、読解、推論、計画、因果、反実仮想、自由記述、長期対話、継続学習を同一原理で処理できない。

## 系列B固有の進展

program inductionを次の6段階へ更新した。

1. Clause-lattice proposal
2. Local executable reconstruction
3. Executable misapplication precision
4. **Relation-bearing quotient signature**
5. Open-form binding / discourse focus
6. MDL library consolidation

今回、1～3には限定的な信号があった。4をsurface contextで近似したため、圧縮で能力が壊れた。5は未成立。

> **実誤適用はsurface proxyより有効だが、誤適用結果をrelation-bearing signatureへ変換できなければ、MDL商は意味構造を潰す。**

## 他系列へ返す新知見

- A: active probe候補は、実際のworld変換で候補classを分割した場合だけ有効とみなす。
- C: object node形成前でもclause-local executionは候補precisionを改善するが、identity/relation quotientにはならない。
- D: write/read schema統合時に、別clause誤適用の破壊vectorを保存しないと過剰圧縮する。
- E: residual-cause edgeは、実誤適用で生じた具体的な破壊clauseへroutingする必要がある。

## 次の仮説

**Destruction-Vector E-Graph with Role-Bearing Quotient Refinement**  
（role保持破壊vectorによるe-graph商精密化）

次はprefix/suffixだけでrelation quotientを作らない。各programについて、

- target clause変更
- 同一objectの別clause破壊
- 別object clause破壊
- inverse復元
- command語順交換
- 別状態表現
- 主語省略focus

の実行結果vectorを保持する。同じ破壊vectorを持つ候補だけをe-classへ統合し、異なるvectorの候補はMDLが短くても統合しない。

最低成功条件:

- 実誤適用既知0.2533を維持または改善
- quotient既知0.0967を0.2533以上へ回復
- 未知語順・別状態表現・主語省略の最低1つを0から改善
- program 24以下
- 実行候補50/query未満
- 32KB未満
- 5ms/query未満

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
