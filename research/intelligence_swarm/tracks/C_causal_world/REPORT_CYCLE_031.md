# 系列C Cycle 031 研究報告

## 仮説

**Target-Boundary Competition from Source-Mechanism Predictive Cuts**  
（source mechanism予測cutによるtarget境界競合）

Cycle 030ではsource programの左右contextを削るadapterを探索したが、既知精度を0.2315から0.1620へ悪化させ、主要転移条件では全面棄権した。今回はsource context自体を編集せず、targetの`before / command`内に存在する全局所境界へ複数source mechanismをoutcome-blindに投票させ、境界候補を直接競合させた。

候補生成・rankingではtargetの`after / future`を使用しない。学習データをinduction 190例と独立probe 98例へ分離し、probe outcomeは候補生成後の境界pair creditにのみ使用した。final testは別seedである。

## 先行研究整理

2025年の因果抽象同定研究は、利用可能な介入集合によって回収できる因果表現の粒度が制限されることを示している。一般変換下のscore-based CRLでも、一般に複数の十分な介入環境が必要である。複数環境の不変性だけではデータ対称性へ整合する可能性もある。

これらはlatent variable・intervention target・encoderを持つ。本Cycleはさらに上流の、生の日本語から介入target境界を形成する問題を扱う。

## 他系列との重複表

| 系列 | 最新中心 | Cで棄却・分離した領域 |
|---|---|---|
| A | Probe-grounded operator birth | 談話予測状態・時間誤差相殺 |
| B | Probe条件付きsymbol birth | MDL・program同値類 |
| D | Operator中心read/write endpoint | 長期memory・再固定化 |
| E | Probe-nudged boundary attractor | Energy固定点・局所力学 |
| **C** | **複数source mechanismが共同支持するtarget state境界と因果遷移** | 今回の固有対象 |

Eも境界候補を扱うが、Eはenergy固定点とnudge、Cはsource intervention mechanismのtarget transition生成・non-target保存・inverse restorationを採否基準とする。

## 最小実装

- 固定ontology・手書きslot・辞書・RAG・外部LLMなし
- Source mechanism: `before→after`局所差分、state/command左右context shape、old/new shape
- Target境界: `before`内の全1〜10文字局所区間
- Value候補: `command`固有span
- Predictive cut: 複数source mechanismの共同支持、non-target保存、command value再現、inverse restoration
- 独立probe: induction後に生成済み候補だけを評価。一方だけ正しい境界pairへcredit
- Final test: target outcomeはrankingに不使用

## 3 seed平均

| 条件 | Surface精度 | Probe境界精度 | 平均候補 | Null率 |
|---|---:|---:|---:|---:|
| 既知 | 0 | 0 | 78.69 | 1.0000 |
| 未知語順 | 0 | 0 | 78.69 | 1.0000 |
| 未知語彙 | 0 | 0 | 78.69 | 1.0000 |
| Rename | 0 | 0 | 94.00 | 1.0000 |
| 別状態表現 | 0 | 0 | 0 | 1.0000 |
| 入れ子 | 0 | 0 | 78.69 | 1.0000 |
| 主語省略 | 0 | 0 | 77.04 | 1.0000 |
| 複数段落 | 0 | 0 | 79.80 | 1.0000 |
| 計画変更 | 0 | 0 | 81.06 | 1.0000 |
| 反実仮想 | 0 | 0 | 78.69 | 1.0000 |

追加診断:

- Source mechanism: 16.67
- Probe pair audit: 307,543
- Probe discrimination: 0
- Boundary credit: 0
- Exact target-value recall: 全条件0
- Wrong commit: 全条件0
- モデルサイズ: 約1,702 bytes
- 学習時間: 約0.759秒
- 既知推論: 約7.90 ms/example
- 複数段落推論: 約9.58 ms/example
- Peak RSS: 160,200 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Target境界候補は多数生成された

既知・語順・語彙・入れ子・計画変更・反実仮想では平均約79〜81候補、Renameでは94候補を生成した。Cycle 030のadapter全面nullとは異なり、target側の境界探索自体は非空になった。

### 正しいstate-variable境界は一件も選べない

全splitでexecution accuracy、exact target-value recallは0だった。平均80前後の候補はold valueの部分span、object名の部分span、助詞を含む境界、command-onlyの長い複合span、同じ文字shapeを持つ無関係な状態区間に支配された。

> **複数source mechanismの投票数は、target境界の意味的同一性を保証しない。Source mechanism自身がsurface shapeに依存している場合、共同支持は相関票の集積になる。**

### 独立probeも識別情報を生成しない

307,543件の候補pairを監査したが、一方だけがprobe outcomeを再構成するdiscriminationは0件だった。全候補が誤るか、同じsurface-localな変換結果を共有した。

系列Bで独立probeが局所program選択へ効いたのは、少数ながら正しいprogram候補が存在したためである。系列Cでは正しいtarget境界が候補集合にないため、probe選択以前に崩壊した。

### 別状態表現は候補0

状態表現を完全に変えるとsource mechanismの左右shapeが一致せず、候補生成が0になった。機構identityではなく表記context identityであることを示す。

### 主語省略・計画変更・反実仮想

- 主語省略: 候補77件だが正答0。object permanenceなし
- 計画変更: 候補81件だが正答0。旧goal/最終goal分離なし
- 反実仮想: 候補79件だが正答0。実行/未実行world分離なし

## 相関暗記と因果理解の反証条件

仮説支持には、target outcome非参照、複数source mechanismの共同支持、independent probeでのwrong境界識別、held/Rename/alternateでのbaseline超過、non-target保存・inverse restoration、主語省略でobject permanence、計画変更・反実仮想での世界状態分離が必要だった。

Outcome非参照と共同支持、wrong commit 0は満たしたが、能力条件はすべて未達。

## 資源量・疎表現

- Mechanism上限: 64
- Target候補上限: 96
- Model: 約1.7KB
- Peak RSS: 約156.4MiB（Python runtime込み）
- 計算量:
  - mechanism extraction `O(NL)`
  - target boundary generation `O(L²)`
  - mechanism voting `O(BVPL)`
  - independent probe audit `O(QH²)`
  - inference `O(BVPL)`

1GB未満は達成。既知・長文とも5msを超え、弱いスマートフォンCPU高速条件と実機検証は未達。

## 系列C固有の進展

> **Source mechanismをtarget内の全境界へ直接競合させれば候補集合は形成できる。しかしsource mechanismが具体的surface contextから作られている限り、複数機構の共同支持も独立probeも正しいstate-variable境界を作れない。**

## 他系列へ返す知見

- A: Probeは実行可能operator候補が存在して初めて選択情報になる。
- B: Probe応答同値類をsymbol化する際、全候補が誤る同値類を意味記号へ昇格しない。
- D: Read/write operatorの共同支持も、具体context由来なら誤addressの多数決になる。
- E: Boundary候補をnudgeする前に、probe内に少なくとも一つ正しい境界operatorが必要。

## 次の仮説

**Mechanism-Family Birth from Cross-Input Intervention Equivalence Classes**  
（入力横断介入同値類からのmechanism family創発）

1. Induction episodeごとに複数の局所介入operator候補を生成
2. 独立probeへoperatorを転送
3. Forward結果、inverse restoration、non-target damageの応答vectorを作る
4. 具体文字列やshapeではなく、probe応答同値類でmechanism family化
5. 全候補が誤る同値類を棄却
6. 複数surface環境で正の外部outcome差を持つfamilyだけ保持
7. Familyが支持するtarget境界を新生
8. Held・Rename・alternateでoutcome-blind executionを評価
9. Family成立後にobject permanence、因果方向、反実仮想rolloutへ進む
10. Shuffled probeで独立観測依存性を反証

**高校生級知能：未達**  
**ネイティブ日本語コミュニケーション：未達**  
**弱いスマートフォン実機検証：未達**  
**完成：未達**
