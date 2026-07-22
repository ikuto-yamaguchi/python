# 系列E Cycle 013 研究報告

## 仮説

**Dual-Residual Null Attractors with Intervention-Calibrated Energy**  
（二重残差nullアトラクタと介入校正energy）

Cycle 012では絶対残差nullにより候補外誤確定率を0.9812から0.5062へ削減したが、依然として半数を誤確定し、適応factor取得との併用では0.8216へ再悪化した。

本Cycleでは残差を以下へ分離した。

1. 言語再構成残差
2. 介入・実行結果残差
3. 非対象保存残差
4. future recall残差
5. 複雑度

さらにnullを、

- `null_proposal`: 正答候補が候補集合にない
- `null_noise`: 観測自体が矛盾・汚染している

へ分離した。追加factorは候補classを分割するだけでなく、絶対介入残差を改善する場合だけ取得する方式を比較した。

## 先行研究整理

- Equilibrium Propagationの2025年拡張は、時間変化入力や有限nudgeでも局所credit assignmentを導ける可能性を示す。ただし、局所状態・energy derivativeが意味のある候補差を既に表現していることが前提。
- Energy-based OOD検出研究では、closed-set confidenceだけでは分布外検出が不十分であり、絶対energy・密度境界・回復可能性を別途学習する必要がある。
- Selective classificationでも、confidence校正の改善と基礎分類能力は切り離せず、棄権機構だけで誤った候補空間を救えない。

## 他系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | E候補との判定 |
|---|---|---|---|---|
| A | learned probe＋null predictive state | out-set誤確定0 | in-set 98.3%拒否、probe意味なし | 外部probe policyは重複のため棄却 |
| B | adversarial misapplication proxy | 候補削減・軽量性 | 上位program class不変、relation不在 | program生成は重複のため棄却 |
| C | object-swap surgery | 候補追加棄却 | object node不在、全精度ほぼ0 | object/causal node形成は重複のため棄却 |
| D | paraphrase write/read consolidation | 55KB→5KB圧縮 | write/read崩壊、address不在 | 長期memory統合は重複のため棄却 |
| **E** | **言語残差と介入残差を分離しnullへ収束** | 今回検証 | 候補生成・現実校正 | 系列固有 |

継承知見:

- A: nullを強めるだけでは全面拒否になる。
- B: 候補削減量と意味的精度は別。
- C: identity-bearing nodeがない介入factorは表面差に退化する。
- D: 圧縮・言い換え回数はsemantic equivalenceを保証しない。

## 実装

比較方式:

1. `single`
   - 言語再構成残差のみ
   - 単一null threshold
2. `dual`
   - 言語・介入・保存・future recall残差
   - proposal null / noise null
   - 候補classを分割するfactorを取得
3. `dual_calibrated`
   - 上記に加え、絶対介入残差を改善するfactorだけを許可

停止条件:

- 候補一意化
- proposal/noise null選択
- 分割利得0で平坦停止
- 最大4 sweep

反証状態:

- 局所最適: 誤候補へ一意収束
- 発散: 4 sweepで非安定
- 平坦化: 同率候補を分割できない
- 候補崩壊: 正答候補が集合外
- 全面拒否: in-setでもnullへ偏る

## 実験

- seed: 1 / 7 / 19
- 各条件: 120 / 360 / 1080
- 候補数: 10
- 最大factor: 5
- 最大sweep: 4
- 条件:
  - in-set
  - ambiguity
  - counterfactual
  - plan change
  - observation noise
  - proposal missing
  - 引用記号なし生日本語

## 最大1080例・3 seed平均

| 条件 | Single | Dual | Dual calibrated |
|---|---:|---:|---:|
| in-set accuracy | 0.0003 | **0.1688** | 0.0003 |
| ambiguity accuracy | 0.0000 | **0.1608** | 0.0000 |
| counterfactual accuracy | 0.0000 | **0.1648** | 0.0000 |
| plan-change accuracy | 0.0000 | **0.1043** | 0.0000 |
| noise wrong commit | 0.0000 | 0.3611 | **0.0000** |
| proposal-missing wrong commit | 0.0006 | 0.8361 | **0.0006** |
| proposal-missing null | 0.0000 | **0.1639** | 0.0528 |
| unmarked candidate recall/accuracy | 0 / 0 | 0 / 0 | 0 / 0 |

## 資源

- model:
  - single: 180 bytes
  - dual: 197 bytes
  - dual calibrated: 189 bytes
- dual inference: 0.0454 ms/example
- calibrated inference: 0.0321 ms/example
- active candidates: 7.03
- sweeps: 2.00
- Peak RSS: 160292 KiB（Python runtime込み）
- 推定計算量: proposal `O(L²)`、relaxation `O(SHF)`、`H<=10`, `F<=5`, `S<=4`

## 判定

**中核仮説は強く反証。**

### 1. Dual residualは平坦化を解除したが、誤候補を一意化した

in-setではsingleがほぼ全面平坦停止だったのに対し、dualは一意候補へ収束した。しかし精度は0.1688、誤確定率は0.8312である。

介入・保存・future recall残差を追加しても、正答edgeへcreditが帰属したのではなく、ランダムに近い候補差を強調した。

### 2. 絶対残差改善を要求するとfactor取得が完全停止

dual calibratedは全主要in-set条件でaccuracyほぼ0、flat rateほぼ1となった。

候補を分割するfactorは存在したが、絶対介入残差を単調に改善するfactorが存在しなかった。これはfactor空間そのものが意味的に不十分であることを示す。

### 3. Proposal nullとnoise nullの分離は不十分

dual方式のproposal-missing null率は0.1639に留まり、誤確定率は0.8361。

calibrated方式は誤確定をほぼ0にしたが、flat停止へ逃げただけで、proposal failureをnullとして同定していない。

### 4. Noise検出とin-set能力が両立しない

calibrated方式はnoise wrong commitを0へ抑えた一方、in-setでも全面平坦化した。安全性ではなく能力喪失である。

### 5. 生の自由日本語candidate proposalは0

引用記号なし条件では、低頻度spanは生成できても、それを実行可能graphへ束縛できずcandidate recall 0。対象・変数・relation・operation・goal・constraint・causal edgeは創発していない。

### 6. 平衡伝播・局所学習は未成立

残差factor選択を実装しただけで、free phase / nudged phaseの局所相関差によるweight更新は行っていない。

## 単なるHopfield記憶との差

保存patternへ最近傍回復するHopfield型記憶ではなく、候補graphごとに複数の絶対残差を評価し、null・平坦化・候補外を分ける制約緩和probeである。

ただし、意味状態の生成・局所weight学習・新規アトラクタ形成を実現していないため、新しい知能原理として成立したとはいえない。

## 系列E固有の進展

必要条件を次の8段階へ更新した。

1. Candidate recall
2. Outcome non-isomorphism
3. Local factor separability
4. Factor minimality
5. Reality calibration / null
6. Adaptive factor中の絶対残差校正
7. **Residual identifiability: どの残差がどの候補edgeを反証するか**
8. Attractor relaxation / local learning

本Cycleでは、残差を分離するだけでは第7段階を満たさず、相対差強調か全面平坦化の二択になることを示した。

## 他系列へ返す新知見

- A: survival-calibrated probeも、観測がどの候補edgeを反証したか識別できなければ全面拒否か誤確信になる。
- B: misapplication outcomeはprogram全体scoreではなく、どのrelation bindingを壊したかへ局所帰属する必要がある。
- C: object persistence signatureは、identity node候補ごとの予測残差へ分解しなければ表面fingerprintになる。
- D: cross-query write/read vectorは、address edgeごとの反証残差に分解しないと過剰統合か全面拒否になる。

## 次の仮説

**Residual-Cause Bipartite Attractors with Edge-Wise Contradiction Routing**  
（残差原因二部アトラクタとedge別矛盾routing）

次は候補graphと残差channelを直接合算しない。

- candidate edge node
- observation/residual cause node

の二部graphを作り、各残差が反証可能なedgeへだけ負energyを送る。

例:

- non-target preservation残差 → target binding edge
- inverse失敗 → operation direction edge
- future recall失敗 → memory address edge
- correction failure → revision/scope edge
- language reconstruction残差 → span boundary edge

未知の残差原因はnull-cause nodeへ保持し、既存候補を無理に一意化しない。

最低成功条件:

- in-set accuracy 0.1688を改善
- out-set wrong commit 0.8361を0.20未満
- in-set flat rateを0.30未満
- unmarked candidate recallを0から改善
- candidates 16以下、sweep 4以下、32KB以下、5ms/query以下
- 複数seed
- 自由日本語統合ゲートを独立維持

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
