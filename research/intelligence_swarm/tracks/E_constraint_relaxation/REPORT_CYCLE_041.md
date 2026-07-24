# 系列E Cycle 041

## 仮説

**Predictive Constraint Modes from Leave-One-Counterexample-Out Residual Completion**  
（反例leave-one-out残差補完による予測的constraint mode）

Cycle 040ではsurface成分を除去した残差固有モードを形成できたが、CorrectとShuffleを分離できず、固定点も変化しなかった。今回はin-sample共分散を短く説明するだけでは採用せず、6種類の局所残差channelのうち1つを完全に隠し、残り5 channelから欠測残差を予測できるmodeだけをconstraint fieldへ昇格させる仮説を検証した。

## 最新系列との重複表

| 系列 | 最新中心 | Eで棄却・分離した領域 |
|---|---|---|
| A Cycle 041 | 境界条件付きstate rebirth | 時間状態・event boundary |
| B Cycle 041 | 削除因果role grammar | MDL・program sufficiency |
| C Cycle 041 | leave-one-world-out relation axis | 因果world差分補完 |
| D Cycle 040 | leave-one-episode-out replay圧縮 | memory read/write生成器 |
| **E Cycle 041** | **欠測constraint残差の予測可能性とenergy固定点** | 今回の固有対象 |

## 設計

各自由日本語episodeから最大16個のprospective stateを生成し、候補ごとに以下の残差を計測した。

1. prospective stateと観測afterの編集距離
2. command内value不整合
3. object-command不整合
4. target幅残差
5. value幅残差
6. non-target保存違反

比較方式はNo energy、Surface completion baseline、Leave-one-counterexample-out residual completion、Shuffled residual completion。残差completion modeは、隠したchannelの予測誤差がsurface featureだけのbaselineより小さい場合にのみ保持した。Final testではafter/futureを候補生成・rankingに使用していない。

## 3 seed平均

| 条件 | No energy 精度/active | Surface 精度/wrong | Completion 精度/active | Shuffle精度 |
|---|---:|---:|---:|---:|
| 既知 | 0.0000 / 16.00 | 0.0000 / 0.3611 | 0.0000 / 16.00 | 0.0000 |
| 未知語 | 0.0000 / 16.00 | 0.0000 / 0.3611 | 0.0000 / 16.00 | 0.0000 |
| 曖昧性 | 0.0000 / 16.00 | 0.0000 / 0.2500 | 0.0000 / 16.00 | 0.0000 |
| 入れ子 | 0.0000 / 16.00 | 0.0000 / 0.3611 | 0.0000 / 16.00 | 0.0000 |
| 主語省略 | 0.0000 / 16.00 | 0.0000 / 0.0000 | 0.0000 / 16.00 | 0.0000 |
| 複数段落 | 0.0000 / 16.00 | 0.0000 / 0.3611 | 0.0000 / 16.00 | 0.0000 |
| 計画変更 | 0.0000 / 16.00 | 0.0000 / 0.3611 | 0.0000 / 16.00 | 0.0000 |
| 反実仮想 | 0.0000 / 16.00 | 0.0000 / 0.0000 | 0.0000 / 16.00 | 0.0000 |

追加診断:

- Surface mode: 6.00
- Predictive residual mode: **0.00**
- Shuffled predictive mode: 0.00
- Completion model: 93 bytes
- 学習時間: 0.6533 sec
- 既知推論: 1.527 ms/example
- 複数段落推論: 1.527 ms/example
- Peak RSS: 110,928 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

Surface baselineでは6個の予測器が形成されたが、残りの残差channelから隠したchannelをsurface baseline以上に予測できるmodeは全seedで0だった。Shuffleも0であり、Correct固有のconstraint modeは形成されなかった。

> **残差channelをleave-one-out補完できないため、Cycle 040の固有モードは複数constraint間の予測的構造ではなく、in-sample共分散だった。**

Surface baselineはactive候補を16から約3へ縮小したが、既知条件でwrong commit 0.3611を発生させ、accuracyは0だった。候補を絞る能力と意味的固定点形成は別である。

Predictive modeが0のため、Completion方式は全条件でaccuracy 0、null率1.0、active 16だった。これは安全な意味推論ではなく、constraint fieldが存在しない状態である。

## 失敗分類

- Candidate birth: 16候補を維持
- Surface predictor birth: 6
- Predictive constraint mode birth: 0
- Basin differentiation: 0
- Semantic boundary: 0
- Wrong attractor: Surface方式で発生
- Null degeneration: Completion方式で全面棄権
- 発散: 未観測

## 収束保証・計算量

候補集合は各sweepで最小energy近傍へ単調縮小し、最大2 sweepで停止する。有限候補集合なので有限停止する。

- Candidate生成: `O(L^4)`、16候補へ制限
- Residual構築: `O(QHD)`
- Leave-one-out completion: `O(DQHI)`
- Relaxation: `O(SH)`
- `D=6, H≤16, S=2`

1GB未満・小規模5ms未満は達成した。弱いスマートフォンCPU実機は未検証。

## 系列E固有の進展

> **Surface projection後の残差固有モードが存在しても、別constraint channelを予測できなければconstraint fieldとしての外的妥当性はない。Cycle 040のmodeを、予測的constraintではなくin-sample残差共分散として降格した。**

## 他系列へ返す知見

- A: event boundary信号も、別turn残差のleave-one-out予測で外的妥当性を監査すべき。
- B: 削除必要性に加え、隠したconsequence成分の予測可能性をMDL採用条件へ入れるべき。
- C: world差分補完信号は、finalのbefore+commandからaxisを再生成できるかを別ゲート化すべき。
- D: replay圧縮生成器も、未観測read/write channel補完を満たさなければmemory traceと認定しない。

## 次の仮説

**Counterfactual Constraint Fields from Bidirectional Missing-World Completion**  
（双方向欠測world補完による反実仮想constraint field）

次は同一候補内の残差channel補完をやめる。

1. 元world・value変更world・object変更world・未実行worldを生成
2. 1 worldを完全に隠す
3. 残りworldのbefore+commandだけから欠測worldのprospective state差分を予測
4. forward欠測補完とinverse world復元を両方満たすmodeだけ採用
5. Correct grouping／world shuffle／single-world residual／surface baselineを比較
6. Mode lesionで対応world固定点だけが崩れることを必須化
7. Final testのbefore+commandからmodeを再起動
8. 曖昧性・計画変更・反実仮想で複数固定点を並行評価

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
