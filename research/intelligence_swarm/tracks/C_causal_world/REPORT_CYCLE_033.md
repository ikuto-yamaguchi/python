# 系列C Cycle 033 研究報告

## 仮説

**Boundary-Faithful Mechanism Families from Minimal Intervention Supports**  
（最小介入supportによる境界忠実mechanism family）

Cycle 032では独立probe応答同値類から平均1 familyを形成し、局所transition exact-after accuracy 0.47を得たが、exact old/new target-boundary recallは0だった。今回は「同じafterを生成した」だけを成功条件とせず、probe上でoutcomeを維持する置換区間を左右から逐次contractし、最小介入supportが再現するsignatureだけをfamilyへ残した。

Final testのafter/futureはfamily形成・候補生成・rankingに使用していない。

## 重複表

| 系列 | 最新中心 | Cで棄却・分離した領域 |
|---|---|---|
| A | residual-born transition kernel | 談話予測状態・時間誤差輸送 |
| B | scope-compressed repair production | MDL・program symbol |
| D | read/write address topology rewiring | 長期memory・slow統合 |
| E | scope-gated repair attractor | energy固定点・局所force |
| **C** | **外部介入結果と最小置換supportが一致する因果mechanism family** | 今回の固有対象 |

## 3 seed平均

| 条件 | Surface | Minimal-support family | Exact境界 | Shuffle | Null率 |
|---|---:|---:|---:|---:|---:|
| 既知 | 0 | 0 | 0 | 0 | 1.0 |
| 未知語順 | 0 | 0 | 0 | 0 | 1.0 |
| 未知語彙 | 0 | 0 | 0 | 0 | 1.0 |
| Rename | 0 | 0 | 0 | 0 | 1.0 |
| 主語省略 | 0 | 0 | 0 | 0 | 1.0 |
| 複数段落 | 0 | 0 | 0 | 0 | 1.0 |
| 計画変更 | 0 | 0 | 0 | 0 | 1.0 |
| 反実仮想 | 0 | 0 | 0 | 0 | 1.0 |

追加診断:

- signature: 32
- minimal-support family: 1
- モデルサイズ: 1,212 bytes
- 学習時間: 0.445 sec
- 既知推論: 0.597 ms/example
- 複数段落推論: 1.401 ms/example
- Peak RSS: 111,044 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Cycle 032の0.47信号は消失

最小support忠実性を要求すると、全条件でaccuracy 0、exact boundary recall 0、null率1.0になった。Cycle 032の局所transition信号は、真のold/new状態区間より広い置換区間による文字列再構成へ依存していた可能性が高い。

### Familyは1件残るが因果機構ではない

平均1 familyは形成されたが、候補間tieを解けず、family除去時と同様に実行能力0だった。Family数やprobe応答同値性だけでは、状態変数・対象・関係・操作targetを表さない。

### 最小support contractが空になる理由

広い区間をnew valueで置換してafter全体を一致させる候補は、左右を1文字contractすると直ちにoutcomeを失う。つまり「結果を保つ最小区間」は真のold valueではなく、surface templateを含む広い不可分区間だった。

> **Outcome一致を保つ区間縮約だけでは、state-variable境界を発見できない。境界忠実性には、非対象部分の独立介入不変性と、同じ変数への複数値介入が必要である。**

### 計画変更・主語省略・反実仮想

全条件で全面null。旧goalと最終goal、継続object、実行worldと非実行worldを別状態として形成できていない。

## 相関暗記と因果理解の反証条件

支持には次が必要だった。

1. Correct probeでのみfamily形成
2. Exact target-boundary recall > 0
3. Family方式がSurfaceよりexecution accuracyを改善
4. Family除去で対応transitionだけが消失
5. Rename・未知語順でも同じ最小supportを維持
6. 計画変更・反実仮想で複数world stateを分離

1のみ部分達成、2〜6は未達。

## 資源量

- 1GB未満: 達成
- 推論5ms未満: 小規模条件で達成
- 弱いスマートフォンCPU実機: 未検証
- 推定計算量:
  - signature birth `O(NL)`
  - boundary candidate `O(SVL)`
  - support contraction `O(QSVL)`
  - inference `O(SVL)`
  - `S≤32`

## 系列C固有の進展

> **Cycle 032の高いexact-after信号を、内部境界忠実性の監査で降格できた。正しい出力生成と因果状態変数の形成を明確に分離したことが今回の主要進展である。**

## 他系列へ返す知見

- A: 正しいnext observationだけでoperator-stateを認定せず、最小状態介入supportを監査すべき。
- B: Repair後の文字列一致だけでsymbol productionを採用せず、非対象不変性と複数値介入を要求すべき。
- D: Read値一致だけでmemory addressを認定せず、write対象の最小supportと独立不変性を監査すべき。
- E: Energy低下や正答afterだけで境界attractorを認定すると広域置換へ退化する。

## 次の仮説

**Multi-Value Intervention Fibers from Non-Target Invariance Cross-Tests**  
（非対象不変性cross-testによる複数値介入fiber）

1. 同じtarget候補へ複数の異なるnew valueを介入
2. 変更区間外の全局所観測が値に依存せず保存されるか監査
3. 同じ境界で3値以上を可逆に置換できる候補だけfiber化
4. Probe間で同じnon-target invariance signatureを要求
5. Correct / shuffled / single-value / no-invariance ablation
6. Rename・別状態表現でexact boundary recallを主評価化
7. 計画変更では旧goal／最終goalを別fiberへ分離
8. 反実仮想では実行／非実行値を並列rollout

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
