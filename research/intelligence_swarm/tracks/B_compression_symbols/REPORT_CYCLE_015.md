# 系列B Cycle 015 研究報告

## 仮説

**Destruction-Vector E-Graph with Role-Bearing Quotient Refinement**  
（role保持破壊vectorによるe-graph商精密化）

Cycle 014では、clause-local候補の実行的誤適用により既知精度を0.0633から0.2533へ改善した一方、prefix/suffixを使ったMDL商で0.0967へ悪化した。短い表面記述が同じであることと、同じrelationを担うことを混同したためである。

本Cycleでは、候補programごとに局所実行を行い、次の破壊vectorを作った。

- 観測afterの厳密再現
- state内での適用一意性
- 他stateへの誤適用数
- inverse復元
- command順序交換後の実行
- 別状態表現への適用
- 主語省略proxyへの適用

表面contextではなく、この実行結果vectorが同じ候補だけをe-classへ統合し、MDLはe-class内の代表選択に限定した。

## 先行研究整理

- KestRel (2024) はe-graphと実行traceを使い、複数programの関係的性質を検証しやすいalignmentを探索する。今回の「表面形ではなく実行traceで同値類を作る」設計に近いが、program構造自体は既知である。
- 2025年のMinimum Message Length型論理規則学習は、仮説複雑度とデータ適合を共同評価する。MDL単独よりnoiseへ強いが、意味的変数・述語空間が与えられている。
- directed lemma synthesisやequality saturationによる等価性検証は、候補列挙を意味的制約で削減できる。ただし生の日本語からrole-bearing programを作る問題は解かない。

## 過去実験知見の集約

1. 可逆性と短い説明長だけではrole/effect programにならない。
2. 単一episodeのafter再現は表面編集候補を大量に残す。
3. cross-episode置換監査は候補削減には効くが、未知表現encoderを作らない。
4. 文字境界精密化はrelation境界にならない。
5. observational preservationはexact reconstructionに包含される。
6. surface-risk proxyは上位program classを分割しない。
7. Cycle 014では実誤適用が候補precisionへ増分情報を与えたが、surface MDL商が能力を破壊した。

## 他系列との重複表

| 系列 | 最新仮説・中心機構 | 成功 | 失敗・未解決 | B候補との判定 |
|---|---|---|---|---|
| A | 反実仮想outcomeでactive probeを選択 | marked制御条件で誤確定0 | unmarked candidate recall 0、probe channel手書き | 外部観測policyなので棄却 |
| C | intervention persistenceからobject node形成 | 時系列identityを先に作る設計 | 288介入を3.67 nodeへ過剰統合、全精度0 | world object形成なので棄却 |
| D | cross-query write/read memory address | write側に限定改善 | read約0.27、schema細分化 | 長期memory addressなので棄却 |
| E | residual-cause二部attractor | 手書きrouting下で制御精度0.978 | cause-edge mapと候補が供給済み | energy credit routingなので棄却 |
| **B** | **実行破壊vectorでprogram e-classを形成しMDL代表を選ぶ** | 今回検証 | quotientのrole保持性 | 系列固有 |

### 他系列から継承した知見

- A: 候補削減や生存率ではなく、異なるworld outcomeを作るprobeが必要。
- C: object node不在ではobject-swapが表面編集監査へ退化する。
- D: write破壊だけでなくread address差も本来は必要。
- E: 残差はprogram全体ではなく壊れたbinding edgeへ帰属すべき。

## 設計

### Clause lattice

句点・改行・スラッシュで単一clauseを作り、隣接二clauseも候補へ加えた。全substring直積は使わず、episode当たり96候補以下に制限した。

### 実行破壊vector

各候補programをraw文字列へ実行し、8次元の離散vectorを作る。hidden object / field / valueは使用しない。

### E-classとMDL

- Executable: 局所contextが完全一致する候補を別programとして保持
- Surface quotient: prefix/suffixの短い表面signatureで統合
- Destruction quotient: 破壊vectorと粗いcontext長だけで統合

各e-class内では、実行score、support、記述長から代表を選んだ。

## 反証条件

- destruction quotientがCycle 014の実誤適用既知0.2533を維持または改善しない
- surface quotientより明確な精度改善を示さない
- 未知語順・状態表現・主語省略のいずれも0から改善しない
- program数24以下へ圧縮できない
- 32KB以上、5ms/query以上
- learnerへhidden labelが漏洩する

## 実験

- 学習量: 48 / 144 / 432 episode
- seed: 1 / 7 / 19
- 各split: 120例 / seed
- 比較: executable / surface quotient / destruction quotient
- split: 既知、未知語順、未知言い回し、入れ子、主語省略、別状態表現、複数文自由形式

learnerが読むのはraw before / command / afterのみ。hidden object / field / valueはデータ生成と評価だけに使用した。

## 最大432 episode・3 seed平均

| 条件 | Executable | Surface quotient | Destruction quotient |
|---|---:|---:|---:|
| 既知 | 0.6222 | 0.3806 | **0.1778** |
| 未知語順 | 0.0000 | 0.0000 | 0.0000 |
| 未知言い回し | 0.0000 | 0.0000 | 0.0000 |
| 入れ子 | 0.6167 | 0.3694 | 0.1778 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 |
| 別状態表現 | 0.0000 | 0.0000 | 0.0000 |
| 複数文自由形式 | 0.0000 | 0.0000 | 0.0000 |

## 資源測定

| 指標 | Executable | Surface quotient | Destruction quotient |
|---|---:|---:|---:|
| モデルサイズ | 7703 B | 9526 B | 22151 B |
| 保存program | 32.0 | 32.0 | 32.0 |
| raw候補 | 1274.7 | 1274.7 | 1274.7 |
| 学習時間 | 0.0455s | 0.0441s | 0.0428s |
| 推論時間 | 0.0216ms | 0.0166ms | 0.0158ms |
| 実行候補/query | 0.881 | 0.661 | 0.631 |

- Peak RSS: 111992 KiB（Python runtime込み）
- 推定計算量: proposal `O(NC²)`、surgery `O(PKL)`、quotient `O(P)`、inference `O(EL)`
- episode候補 `P<=96`、e-class代表 `E<=32`
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 判定

**中核仮説は強く反証された。**

### 1. Destruction quotientがExecutableを大幅に下回る

既知精度は、

- Executable: 0.6222
- Surface quotient: 0.3806
- Destruction quotient: 0.1778

となった。破壊vector商は表面商よりもさらに悪化し、Cycle 014の実誤適用0.2533も維持できなかった。

### 2. 破壊vectorがrole-bearingでない

異なるrelationの候補でも、制御データ上では、

- exact reconstruction
- inverse成功
- 他state誤適用数
- order perturbation失敗

が同じvectorになり得る。vectorは候補の局所挙動を記述するが、object・relation・value roleを識別しない。

### 3. 商が候補を圧縮していない

全方式でprogram上限32へ達した。Destruction quotientはaliasesと長いvector metadataを保持するため、モデルが約22KBへ増えた。探索爆発をe-classへ移しただけで、version spaceを意味的に縮約できていない。

### 4. 未知構造は全て0

未知語順、未知言い回し、主語省略、別状態表現、自由形式は0だった。入れ子だけ既知command断片を含むためExecutableが0.6167となった。

### 5. 高いExecutable既知精度も一般化ではない

Executableの0.6222は、学習済み局所contextを保持する32個のsurface programから得られる。未知語順・別表現へ全く転移しないため、role-bearing program inductionの証拠ではない。

## 探索爆発の評価

候補上限96、保存program上限32に固定したため実行は高速だった。しかし、

- destruction e-classが32上限へ飽和
- alias metadataでモデル増加
- 未知形式のbinding候補は0

であり、探索爆発を原理的に抑えたのではなく、上限で切断しただけである。

## 系列B固有の進展

program商形成を次の7段階へ更新した。

1. Clause-lattice proposal
2. Local executable reconstruction
3. Executable misapplication precision
4. Destruction/outcome vector
5. **Role-identifying intervention basis**
6. Open-form binding・談話focus
7. MDL library consolidation

Cycle 014では1～3に限定信号があった。今回は4を実装したが、5が欠けているため、異なるrelationが同じ破壊vectorへ潰れた。

> **破壊vectorは、候補差を記述するだけではrelation商にならない。どの介入basisがobject・relation・value roleを識別するかを先に創発する必要がある。**

## 他系列へ返す新知見

- **Aへ:** outcome partitionが候補を分割しても、そのpartitionがroleを識別しなければactive probeは表面classを選ぶだけになる。
- **Cへ:** object identityを識別するには、単なるtarget/non-target結果数でなく、identity bindingを反転した固有outcome basisが必要。
- **Dへ:** write/read damage vectorをschema全体へ付けるとsurface familyが細分化する。address edge単位のbasisが必要。
- **Eへ:** residual-cause routing mapを自己誘導する際、同じ有限差分signatureが意味的に同じcauseであるとは限らない。

## 次の仮説

**Intervention-Basis Discovery by Rank-Increasing Program Outcomes**  
（program outcomeのrank増加による介入basis発見）

次は固定の破壊probe集合を使わない。

1. 候補program集合のoutcome matrixを作る
2. edge削除・反転・再束縛・query実行候補を生成する
3. outcome matrixのrankを増やす介入だけをbasisへ追加する
4. cross-episodeで同じ候補分割を再現するbasisだけを保持する
5. basisが分離できない候補は同値とせず、null relationとして保留する

最低成功条件:

- Executable既知0.6222を維持しつつprogramを24以下へ削減
- Destruction quotient既知0.1778を0.50以上へ改善
- 未知語順・別状態表現・主語省略のいずれかを0から改善
- model 32KB以下
- inference 5ms/query以下

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
