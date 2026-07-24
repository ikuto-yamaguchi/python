# 系列B Operation/Goal Cycle 002

## 仮説

**Anonymous Four-Way Contrast Factorization for Executable Operation Birth**  
（四方向対照の匿名因子化による実行可能操作創発）

Cycle 001では、raw Japanese全文とbefore/after変換を一つの相関行列へ統合したが、identity・operation・goal・before/after方向が混在し、prospective、inverse、goal変更、failure repairがchance近傍だった。

今回は文字区間・grammar・operation IDを作らず、制御されたepisode pairの「どの要因が保存され、どの要因だけが変化したか」という弱い対照だけから、4つの匿名contrast channelを形成した。

1. 同じ対象で変換だけが異なる
2. 対象だけが異なり変換は同じ
3. 変換は同じで目的だけが異なる
4. 発話要素を保ったままbefore/after方向だけを反転

各channelは名称なしの疎text supportとして形成し、未知対象で同じ物理変換を説明できるchannelを、訓練episodeの外部transition予測力だけで選択した。テスト時は介入前の`raw Japanese + before state + hypothetical target/transition`のみを使用し、正解after、完成trajectory、scar、operation labelは使用していない。

## 現在stage・凍結族との整合

- Stage: S1 Semantic Identity Birth
- G1/G2: 未達
- HF-001/HF-002: surface span・MDLから意味を作る方式は凍結
- HF-006: post-treatment witnessをprospective identityへ流用する方式は凍結
- 本CycleはAF-004上で、介入前の四方向対照からidentity/operation/goal/directionを分離できるかを検証した。

## 先行研究整理

弱い対照や介入を使う表現学習では、どの生成要因が変化したかを完全にラベル付けしなくても、factor changeの共有構造から分離表現を学べる場合がある。一方、介入から潜在因子を同定できる理論結果は、介入環境・target・mixing assumptionsなどの条件を持つ。今回の課題は、その条件を大幅に弱め、生の日本語とpre-treatment worldだけから実行可能な操作を形成できるかである。

## 他系列との重複表

| 系列 | 最新中心 | Bで扱わない領域 |
|---|---|---|
| A Cycle 002 | pre-treatment relationからtarget×transition同時予測 | semantic identity unitのbirth |
| C Cycle 002 | post-treatment leakage監査 | causal identifiability監査 |
| D Cycle 002 | time-indexed memory eligibility | retention・consolidation |
| E GOV-003 | HF-006凍結、AF-004昇格 | 仮説族管理・stage判断 |
| **B Cycle 002** | **四方向対照から匿名operation方向を分離し実行へ再利用** | 今回の固有対象 |

## 最小実装

比較方式:

1. **Shared**: 4 contrast channelを混合
2. **Factorized**: cross-identity transition予測力が最大の匿名channelだけを使用
3. **Shuffle**: 選択channelを別contrast channelへ交換
4. **No-direction**: operation候補channelとbefore/after reversal channelを再混合

内部表現:

- Raw Japanese: 64次元の符号付きcodepoint sketch
- Pre-treatment world / hypothetical transition: 32次元sensor sketch
- Anonymous factor support: 各channel 16 feature
- Bilinear operation map: 64×32

固定語彙表、文字列検索、span、slot、ontology、RAG、外部LLMは使用していない。

## 3 seed平均

Joint target×moveは32択でchance **0.03125**、inverse operationは4択でchance **0.25**、goal-change move保持はchance **0.25**、failure repairは2択比較でchance **0.5**。

| 条件 | Factorized joint | Shuffle joint | 差 | Inverse | Goal変更 | Failure repair |
|---|---:|---:|---:|---:|---:|---:|
| Held | 0.0556 | 0.0000 | +0.0556 | 0.2500 | 0.2361 | 0.4167 |
| Rename | 0.0278 | 0.0417 | -0.0139 | 0.2500 | 0.2222 | 0.4167 |
| 未知語順 | 0.0417 | 0.0278 | +0.0139 | 0.1667 | 0.2639 | 0.5556 |
| 入れ子 | 0.0278 | 0.0278 | +0.0000 | 0.2361 | 0.3056 | 0.4444 |
| 複数段落 | 0.0139 | 0.0278 | -0.0139 | 0.1944 | 0.2361 | 0.5000 |
| 自由日本語 | 0.0000 | 0.0556 | -0.0556 | 0.1944 | 0.2361 | 0.5278 |
| 別領域 | 0.0278 | 0.0139 | +0.0139 | 0.3056 | 0.2917 | 0.6111 |

追加診断:

- Held target accuracy: 0.1528
- Domain target accuracy: 0.1111
- Active text features: 16
- Model size: 8660 bytes
- Training: 0.024404 sec
- Inference: Held 0.927 ms/query
- Peak RSS: 168104 KiB（Python runtime込み）
- Candidate count: 32
- Update estimate: 2048 multiply-add / episode
- Inference estimate: 65536 multiply-add / query

## 判定

**中核仮説は反証。能力上の進歩は認定しない。G2未達。**

### Held条件には小さな局所信号

Held joint accuracyはFactorized 0.0556、Shuffle 0.0000で、32択chance 0.03125をわずかに上回った。したがって、四方向contrastから選んだ匿名channelに、既知domain内のoperation方向を分離する弱い信号は存在する。

### 未知条件へ安定して転移しない

- Rename: Factorized 0.0278 / Shuffle 0.0417
- 未知語順: 0.0417 / 0.0278
- 自由日本語: 0.0000 / 0.0556
- 別領域: 0.0278 / 0.0139

符号も条件ごとに反転し、別領域ではchance未満である。Correctがshuffleを複数未知条件で一貫して上回る進歩条件を満たさない。

### Inverse・goal・repairはchance近傍

Factorizedの主要条件で、

- Inverse: 約0.17〜0.31（chance 0.25）
- Goal変更: 約0.22〜0.29（chance 0.25）
- Failure repair: 約0.42〜0.61（chance 0.5）

であり、Correct固有の改善はない。No-direction ablationとの差も一貫しないため、before/after方向とoperationが分離された証拠はない。

### 原因

匿名contrast channelは「どのepisode pairで発話featureが変わったか」を分離したが、各episodeのraw Japaneseには対象名・操作表現・目的表現が同時に含まれる。Pairingだけでは、同一操作が異なる語彙・domainで同じ変換を表すことを十分に拘束できない。

つまり、

> **四方向対照は混線を診断できるが、対照pairだけでは新しい語彙domainへ再生成可能なoperation primitiveを同定しない。**

## 反証条件

| 条件 | 結果 |
|---|---|
| HeldでFactorized > Shuffle | 小さく達成 |
| Rename・未知語順・自由日本語で一貫して上回る | 未達 |
| 別領域で実質差 > 0.10 | 未達 |
| Prospective jointとinverseを同じchannelで改善 | 未達 |
| Goal変更でもoperationを維持 | 未達 |
| Direction lesionで性能が選択的に崩れる | 未達 |
| Post-treatment leakageなし | 達成 |

## 資源量

- Model: 約8.7 KiB
- Peak RSS: 約164 MiB（Python + NumPy runtime込み）
- Training: 約0.025 sec
- Inference: 約0.93 ms/query
- Candidate: 32
- Update: O(TR) = 2,048 multiply-add/episode
- Inference: O(KTR) ≈ 65,536 multiply-add/query

1GB未満・5ms未満はこの環境で達成した。弱いスマートフォンCPU実機は未検証。NumPy runtime込みRSSが大きいため、実装時はint8疎行列へ置換する必要がある。

## 系列B固有の知見

> **Same/differentの四方向contrastを導入するとheld domain内のoperation方向を弱く分離できるが、pair relationだけでは語彙・domainを越えるoperation identityを同定できない。Operationを成立させるには、発話変換とworld transitionが複数座標系・複数対象で可換することを直接要求する必要がある。**

## 他系列へ返す知見

- A: identityとoperationを分離するにはsame/different pairだけでなく、座標変換後も同じoperation作用が可換するequivariance witnessが必要。
- C: operation proposalの資格に、translation/rotation/object permutation後のcommuting rolloutを追加すべき。
- D: 現在のanonymous operation channelは未知domainで取得資格を満たさず、memory保存対象にしない。
- E: AF-004を継続。ただし「四方向contrastだけでoperation factorが同定できる」という下位仮説は未支持。

## 次仮説

**Transformation-Commuting Operation Birth from Paired Coordinate Worlds**

次はepisode pairのsame/different分類だけを使わない。

1. 同じcommand/worldを平行移動・回転・object permutationしたpaired coordinate worldを生成
2. 発話側の変換とworld transition側の変換が可換する匿名operatorを形成
3. Operationを絶対方向ではなく座標変換に対する作用として同定
4. Correct transform / transform shuffle / four-way-only / no-directionを比較
5. Held、Rename、未知語順、自由日本語、別domainでprospectiveとinverseを同時評価
6. Goal変更ではoperatorを維持し、failure repairでは逆作用を識別
7. 別domainでCorrect-shuffle差0.10以上を進歩条件とする

- Stage: S1継続
- G1: 未達
- G2: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
