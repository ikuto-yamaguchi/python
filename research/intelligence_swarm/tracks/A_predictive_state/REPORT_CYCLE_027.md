# 系列A Cycle 027 研究報告

## 仮説

**Transition-Mediated Predictive Responsibility from Local Residual Routing**  
（局所残差routingを介した状態遷移型予測責任）

Cycle 026ではraw commitment文字列を現在turnの文字予測prefixへ直接加え、除去時の全体NLL差を責任とした。しかし全主要条件で責任が負となり、主語省略のcontinuation recallは0だった。

今回は現在turnの`before + command`だけから高surprisal局所残差を生成し、前turn commitmentと残差の対応候補を保持した。現在turnのafter/futureはcommitment選択へ使用していない。

責任creditは全体NLLではなく、commitmentと現在before/commandの局所整合、学習時に再発したcommitment–residual route、routeを外したときの局所未説明残差に限定した。

## 他系列との重複表

| 系列 | 最新中心 | 支配的失敗 | Aとの分離 |
|---|---|---|---|
| B | Minimal negative witness cutによるbinding graph選択 | held-out全面tie | 文法・MDL・negative cutは扱わない |
| C | 双方向local alignmentによるpositive witness birth | event当たりwitness 1.21 | 因果transition alignmentは扱わない |
| D | Shapley-sparse memory coalition credit | slow binding 0 | 長期記憶再固定化は扱わない |
| E | Predictor-independent residual hyperedge | 同一channel leakage | energy hyperedgeは扱わない |
| **A** | **前turn commitment→現在turn局所予測残差routing** | 談話継続責任 | 系列固有 |

E系列と近いresidual第三nodeは、Aではenergy hyperedgeではなく、観測前の談話commitmentを次turn予測へ接続する時間方向付きroutingとして限定した。

## 実験条件

- seed: 1 / 7 / 19
- train: 48 episode
- test: 18 episode / split / seed
- commitment prototype上限: 64
- route prototype上限: 32
- residual候補: 最大6 / input
- active pair: 最大48
- ablation: No carry / Unconditional carry / Local residual routing / Routing + Null
- 自由日本語条件: 既知、言い換え、Rename、別状態表現、入れ子、主語省略、明示切替混在、複数段落、計画変更

## 3 seed平均

| 条件 | No carry pair / 精度 | 無条件carry pair / 精度 | Residual routing pair / 精度 |
|---|---:|---:|---:|
| 既知 | 0.1852 / 0.1481 | 0.1852 / 0.0926 | 0.1852 / 0.1481 |
| 未学習言い換え | 0.1667 / 0.1481 | 0.1852 / 0.0926 | 0.1667 / 0.1481 |
| Rename | 0.0741 / 0.0556 | 0.0556 / 0.0185 | 0.0741 / 0.0556 |
| 別状態表現 | 0.4815 / 0 | 0.3148 / 0 | 0.4815 / 0 |
| 入れ子 | 0.0370 / 0.0370 | 0.0556 / 0.0556 | 0.0370 / 0.0370 |
| 主語省略 | 0.0926 / 0.0185 | 0.1852 / 0 | 0.0926 / 0.0185 |
| 明示切替混在 | 0.1111 / 0.0370 | 0.2963 / 0.0185 | 0.1111 / 0.0370 |
| 複数段落 | 0.0370 / 0.0370 | 0.0370 / 0.0185 | 0.0370 / 0.0370 |
| 計画変更 | 0.0741 / 0.0741 | 0.0185 / 0.0185 | 0.0741 / 0.0741 |

追加診断:

- 主語省略 routed carry率: 0.9259
- 主語省略 continuation recall: 0.5000
- 主語省略 local residual reduction: 0.1173
- 明示切替 wrong carry: 0.2407
- route prototype: 32

## 判定

**中核仮説は強く反証された。局所残差routing信号は形成されたが、能力増分は0。**

### Routing creditは正になった

Cycle 026では平均除去責任が負だった。今回は局所残差へ限定したcreditが全条件で正となり、主語省略では平均0.1173を記録した。全体文字NLLより局所未説明区間へcreditを限定する方が、評価原理としては健全である。

### Residual routingはNo-carryと完全同値

全splitでResidual routingのpair recall・accuracyはNo-carryと完全に同一だった。

主語省略ではcarry率0.9259、continuation recall 0.5000まで上がったにもかかわらず、pair recall 0.0926、accuracy 0.0185のままである。Routeは多数のcommitmentを責任ありと判定したが、正しいobject cellを候補集合へ追加できていない。

### 責任routingがsurface overlapへ退化

Route prototypeはcommitment文字列とcurrent before/command residual文字列の局所overlapから形成される。したがって正のcreditは、内部状態遷移の説明ではなく文字区間の類似性を再検出した可能性が高い。

> **局所creditを測る場所を正しくしても、routing edge自体がsurface spanならlatent state responsibilityにはならない。**

### 無条件carryより安全だが、継続選択ではない

無条件carryは主語省略pair recallを0.1852まで増やしたがaccuracy 0だった。Residual routingはNo-carry精度を維持したが、正しい継続objectの選択能力を増やしていない。

明示切替混在ではwrong carryが0.2407残り、focus切替・終了も未成立である。

### 計画変更は未成立

計画変更のpair recall / accuracyは0.0741 / 0.0741で、旧goal・最終goal・撤回scopeを分離していない。

### Nullは全面棄権

Routed+Nullはwrong commitを止めるが、全条件null率1.0となり能力向上ではない。

## 反証条件

仮説支持には、主語省略でNo-carryより観測前pair recallまたはaccuracyが上昇し、明示切替でwrong carryが増えず、route除去時にrouting先局所残差だけが増加し、Rename・言い換えでも同じ責任cellへ転移し、計画変更で旧goalと最終goalを分離する必要があった。今回は局所creditの正値以外を満たさない。

## 資源量

- モデルサイズ: 10,050 bytes
- 学習時間: 0.094秒
- 既知推論: 4.52 ms/example
- 主語省略推論: 4.47 ms/example
- Peak RSS: 約111 MiB（Python runtime込み）
- Commitment prototype: 39.67
- Route prototype: 32
- 推定計算量:
  - 文字予測 `O(NL)`
  - 残差区間生成 `O(L)`
  - Route照合 `O(KRW)`
  - 疎pairing `O(KoKv)`

1GB未満・5ms未満は小規模制御条件で達成した。弱いスマートフォン実機は未検証。

## 系列A固有の進展

1. Prediction-error stream
2. Event cell
3. Prospective commitment
4. Global removal responsibility――反証
5. **Local residual routing responsibility――credit信号のみ、能力仮説は反証**
6. Representation-independent route identity
7. Sparse focus stack
8. Goal revision state
9. 自由日本語world state

核心的知見:

> **全体NLLではなく局所未説明残差へcreditを帰属させると正の責任信号は得られる。しかし、commitmentとresidualが同じsurface表現に依存する限り、routingは談話状態遷移にならない。**

## 他系列へ返す知見

- B: negative witnessは競合programと同じsurface区間ではなく、独立した出力残差へ接続する必要がある。
- C: positive witness alignmentはsource/target spanの類似ではなく、対応除去で局所transition residualが増えることを要求する。
- D: memory coalition creditはquery全体lossではなく、独立生成した局所read/write residualへ帰属させる。
- E: residual node独立性だけでなく、候補表現とresidual表現の共通情報を明示的に差し引く必要がある。

## 次の仮説

**Cross-Encoded Residual Routing by Predictive Information Exclusion**  
（予測情報除外によるcross-encoded residual routing）

次はcommitmentとresidualを同じ文字表現で照合しない。

1. Commitmentは前turnのafter/future持続signatureから符号化
2. Residualはcurrent `before + command`を別seed・別context幅の予測器で生成
3. Commitment文字列との直接overlapをroute scoreから除外
4. Commitmentを除いたときだけ増えるresidual response patternをroute identity化
5. 複数surface環境で同じresponse patternが再現したrouteだけ保持
6. 主語省略ではobject residualへのrouteだけcarry
7. 明示objectが同じresidualを説明すれば旧routeを終了
8. 計画変更では旧goal residualと最終goal residualを別channel化

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
