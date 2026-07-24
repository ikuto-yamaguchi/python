# 系列D Memory Eligibility Cycle 008

## 仮説

**Independent Minimal-Witness Consensus before Memory Eligibility**  
（記憶資格判定前の独立最小witness集合合意）

C Cycle 009では、oracle token境界・対象/操作factorization・unary arityを与えた上限条件で、3個の独立witnessにより576個の対象×操作worldを一意化できた。

系列Dでは、この一度の一意化をそのまま記憶資格とみなさない。次の2条件を追加した。

1. 最初の3 witnessと重複しない第二の3 witness集合でも、同じlatent worldへ独立に一意収束すること
2. 第一集合の1 witnessが矛盾した場合、第二集合のidentityを上書きせず、取得競合として検出すること

semantic identity未成立のため、fast weights、replay、sleep consolidation、選択的忘却、容量最適化は実装していない。

## 実験

- opaque target token: 4
- opaque operation token: 4
- target permutation: 24
- operation permutation: 24
- initial causal worlds: 576
- first minimal witness set: 3 queries
- disjoint second witness set: 3 queries
- corrupted acquisition: first setの2番目のoutcomeを別outcomeへ置換
- seed: 1 / 7 / 19
- final query outcomeはwitness選択・rankingに不使用

## 3 seed平均

| 指標 | 結果 |
|---|---:|
| 第一集合の残存world | 1.0000 |
| 第二集合の残存world | 1.0000 |
| 両集合統合後の残存world | 1.0000 |
| 独立集合合意 | 1.0000 |
| 使用witness総数 | 6.0000 |
| 矛盾第一集合の残存world | 0.6667 |
| 矛盾集合+正常第二集合の残存world | 0.0000 |
| 取得競合検出 | 1.0000 |
| 正常第二集合からのprospective | 1.0000 |
| 正常第二集合からのinverse | 1.0000 |
| closed-loop | 1.0000 |

## 判断

**上限監査仮説は支持された。ただし正式な能力進歩・G1/G2・memory eligibilityは未達。**

3個の最小witness集合は単独でもlatent mappingを一意化し、重複しない第二集合も全seedで同じmappingへ収束した。第一集合を1件だけ破壊すると、正常第二集合との統合version spaceは全seedで空になり、矛盾を検出できた。

この結果から、記憶資格の上限条件として次が妥当である。

> 一度の一意化ではなく、独立したwitness集合が同じunitを再同定し、矛盾witnessを既存identityへの上書きではなく取得競合として隔離できること。

一方、今回の成功はoracle条件に依存する。

- token境界が既知
- targetとoperationへのfactorizationが既知
- arity=1が既知
- 仮説空間が有限permutation world

したがって、生の自由日本語からsemantic unitが創発した証拠ではなく、正式なmemory eligible unitとは認定しない。

## 取得失敗と保持失敗の分離

今回の矛盾条件では、正常identityを一度取得した後に忘却したのではない。矛盾witness集合と正常集合が同時に成立不能であることを検出した。

- 正常取得上限: 成立
- 独立再同定上限: 成立
- 矛盾取得の隔離: 成立
- 生の日本語semantic acquisition: 未成立
- 長期保持: 評価対象外
- catastrophic forgetting: 未観測

失敗分類は **oracle-to-raw grounding gap** である。

## 他系列へ返す知見

- A: unit候補は単一接地集合だけでなく、重複しない第二witness集合でも同一化される必要がある
- B: operation proposalは別action witness集合から同じtransition mappingを再生成できることを要求する
- C: 次のsegmentation/arity共同同定では、単一version-space collapseに加えてleave-one-witness-set-out再同定を測るべき
- E: G1/G2未達を維持しつつ、正式memory eligibilityへ independent witness consensus と conflict quarantine を追加可能

## 次の仮説

**Segmentation–Arity Uncertainty under Independent Witness-Set Memory Eligibility**

次はoracle token境界・固定factorization・固定arityを外すCの次段階と接続し、異なるwitness集合が、

- 同じsegmentation
- 同じarity
- 同じtarget/operation mapping

へ独立収束する場合だけmemory eligible候補とする。単一集合だけで一意化する偶発的分節は拒否する。

## 資源量

- Model upper bound: 9,216 bytes
- Peak RSS: 109,988 KiB
- Runtime: 0.02237 sec / 3 seeds
- Initial worlds: 576
- Estimated probe simulations max: 55,296
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

- Semantic Identity Gate G1: 未達
- Operation/Goal Gate G2: 未達
- Formal memory eligibility: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 完成: false
