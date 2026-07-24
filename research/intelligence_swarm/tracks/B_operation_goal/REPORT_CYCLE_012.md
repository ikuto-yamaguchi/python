# 系列B Operation / Goal Cycle 012

## 仮説

**Latent Operation-Axis Birth from Anonymous Commutator Sparsity**  
（匿名交換子疎性からの潜在操作軸創発）

GOV-013 / AF-014とA PR #407を受け、既知のtarget/state/goal/operation軸ラベルを与えず、raw発話と複数の匿名介入応答からoperation transformation signatureを生成できるか検証した。

A PR #407では既知介入軸を与えた条件でprospective・未知語順・主語省略・自由日本語に正方向信号があった一方、RenameはRandom以下、inverse差は+0.0139、strict gateは0/3だった。したがって系列Bでは、既知軸上のsurface prototypeを再利用せず、介入応答vectorの集合とpairwise非可換性だけを使用した。

## 設計

- 2 opaque domain
- seed 1 / 7 / 19
- operation: set1 / set0 / toggle / copy
- target / source / goal / word-order / causal-directionを匿名介入として生成
- learnerには介入軸名を渡さず、応答vector集合とpairwise commutator距離のみを渡す
- raw Japaneseは全文character hashing（token境界・辞書・slotなし）
- Correct / surface-only / anonymous-axis shuffle
- 標準・未知語順・主語省略・複数段落・自由記述・Rename
- final afterは学習・rankingに不使用

固定ontology、手書きslot、RAG、外部LLM、有限program posterior intersection、same-delta / response equalityによるidentity確定は使用していない。

## 3 seed × 2 domain平均

| 条件 | Correct prospective | Surface-only | Axis shuffle | Correct inverse | Goal | Repair |
|---|---:|---:|---:|---:|---:|---:|
| 標準 | 0.7792 | 0.8042 | 0.7833 | 0.7042 | 0.7792 | 0.7792 |
| 未知語順 | 0.7833 | 0.7708 | 0.7958 | 0.6167 | 0.7833 | 0.7833 |
| 主語省略 | 0.7667 | 0.6458 | 0.7875 | 0.5333 | 0.7667 | 0.7667 |
| 複数段落 | 0.8292 | 0.7833 | 0.7292 | 0.6583 | 0.8292 | 0.8292 |
| 自由記述 | 0.7542 | 0.7458 | 0.8083 | 0.6250 | 0.7542 | 0.7542 |
| Rename | 0.5833 | 0.5583 | 0.6750 | 0.2750 | 0.5833 | 0.5833 |

追加資源:

- Correct model: 5081.0 bytes
- Correct training: 0.0163 sec
- Peak RSS: 167000 KiB
- 候補operation: 4
- 推定更新量: O(N·D)
- 推定推論量: O(K·D + A²·E)
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証
- answer leakage: なし

## 判断

**中核仮説は反証。能力上の進歩は未認定、G1/G2未達。**

匿名介入signatureを加えたCorrectは、主語省略でsurface-onlyを+0.1208、複数段落で+0.0458上回った。しかし次の決定的な反証がある。

1. 標準表現ではCorrect 0.7792 < surface-only 0.8042。
2. 未知語順ではAxis shuffle 0.7958 > Correct 0.7833。
3. 自由記述ではAxis shuffle 0.8083 > Correct 0.7542。
4. RenameではAxis shuffle 0.6750 > Correct 0.5833。
5. Rename inverseは0.2750に低下した。
6. 3 seedすべてでCorrectがsurface-onlyとaxis-shuffleを+0.10上回るstrict gateは0/3。

したがって、匿名介入応答集合とpairwise commutator sparsityは、一部surface条件でoperation分類を補助するが、正しい介入軸対応に依存した再利用可能operation unitを形成していない。特にaxis対応を破壊しても性能が維持または改善する条件が多く、operation identityではなく発話表面と粗いeffect priorで説明できる。

## 根本原因

軸名を隠しても、応答vector集合をsortして扱うと、どの変換がtarget/source/goal/directionに対応するかという**link identity**が消える。

その結果、set1/set0/toggle/copyを区別するうえで必要な、

- target交換に対する対応成分の置換
- source交換に対するbinary-only変化
- goal変更時のoperation保存
- direction反転時のinverse対応
- non-target保存

を同じraw roleへ結び付けられない。

これはresponse equalityの言い換えではないが、**unlabeled multiset of transformation responses**をoperation identityとして用いる下位仮説の反証である。

## 失敗分類

- anonymous-axis multiset loses intervention linkage
- commutator sparsity without role binding
- rename and inverse failure
- axis-shuffle invariance
- initial operation semantics failure

正式operation proposalは0件。

## 他系列へ返す条件

### A

identity proposalには、匿名変換応答の集合一致ではなく、各変換とraw表現成分のlinkが独立取得集合で再生成される必要がある。Rename時にlinkを再構築できない候補は棄却する。

### C

causal groundingではState-axis / Target-link / Argument-link / Direction / Goal shuffleを個別に行い、正しいlinkだけを壊した際に対応能力だけが崩れることを要求する。軸集合の統計だけでは不足する。

### D

取得時same-unique operation unitは0。memory eligible unitは0であり、保存・干渉・忘却研究は再開しない。

### E

AF-014は継続可能だが、`anonymous commutator multiset defines operation identity`は不採用下位仮説候補。oracle axisを外しただけでidentity birthと認定してはならない。

## 次の仮説

**Link-Preserving Latent Axis Birth from Cross-Expression Transformation Incidence**

次は介入応答をunordered multisetへ潰さない。

1. raw表現側の変化候補とworld側の変化候補を二部graphとして保持
2. target/source/goal/directionの名称は与えない
3. 独立表現family間で同じincidence patternへ一意再収束するlinkだけを保持
4. Target-link / Source-link / Goal-link / Direction-link shuffleを個別対照化
5. Rename・自由記述・inverseでCorrect−各shuffle +0.10を要求
6. 各独立取得集合単独でsame-unique link graphへ再収束した場合のみoperation proposal化

## 状態

- Stage: S1継続
- G1: 未達
- G2: 未達
- Formal operation proposal: 0
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
