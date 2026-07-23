# 系列A Cycle 026 研究報告

## 仮説

**Responsibility-Weighted Prospective Commitments by Counterfactual Prediction Removal**  
（反実仮想予測除去による責任重み付き前向きcommitment）

Cycle 025のevent gateは全条件でcarry率0へ退化し、誤carryと正しい継続を同時に消した。
今回は二値gateを廃止し、前turnのcommitment cellを1つずつ除去したとき、
現在turnの `before + command` 文字予測損失がどれだけ増えるかを、そのcell固有の予測責任として測定した。

現在turnのafter/futureは選択入力に使用していない。

## 先行研究整理

- Action-conditional self-predictive learningは、将来latent予測をaction条件付きの低rank dynamicsとして捉えるが、state/action表現は事前に与えられる。
  - https://proceedings.mlr.press/v258/khetarpal25a.html
- Active inferenceのlow-dimensional latent state planningは、情報利得とgoal-directed planningを統合するが、観測・action空間と生成modelを前提とする。
  - https://doi.org/10.3390/e27080846
- Counterfactual influenceは、単なる介入結果と観測個体に依存する反実仮想を区別する必要性を示す。
  - https://proceedings.mlr.press/v275/kazemi25a.html
- State-change counterfactual表現は手続き的event理解を改善するが、状態変化記述を学習信号として与える。
  - https://openaccess.thecvf.com/content/ICCV2025/html/Kung_What_Changed_and_What_Could_Have_Changed_State-Change_Counterfactuals_for_ICCV_2025_paper.html

本Cycleの課題は、それらより上流にある、生の日本語文字列から談話commitmentと責任範囲を形成できるかである。

## 他系列との重複表

| 系列 | 最新中心 | 限定信号 | 支配的失敗 | Aとの分離 |
|---|---|---|---|---|
| B | 実行可能binding graph | MDL短縮 | 実行accuracy 0 | 文法・圧縮は扱わない |
| C | Multi-witness state-variable fiber | Null偽統合の除去 | Identity class 0 | 因果transition identityは扱わない |
| D | Memory-element removal credit | Slow factor形成 | 誤factorのslow固定 | 長期memoryは扱わない |
| E | Residual-mediator hyperedge | 有限候補収束 | Constraint edge 0 | Energy graphは扱わない |
| **A** | **commitment除去による観測前予測責任** | 今回検証 | 談話継続責任 | 系列固有 |

重複候補として、Bのrole交換、Cのwitness-edge除去、Dのmemory element removal、Eのresidual mediatorを棄却した。
Aでは次turn予測に対する前向きcommitmentの責任だけを中心機構とする。

## 実験条件

- seed: 1 / 7 / 19
- train: 72 episode
- test: 36 episode / split / seed
- Transformer・attention・外部LLM・RAGなし
- hidden object/value labelは評価器のみ
- current-turn after/futureはcommitment選択に未使用
- 比較:
  1. No carry
  2. Unconditional carry
  3. Counterfactual-removal responsibility
  4. Responsibility + Null
- 統合条件:
  - 既知
  - 未学習言い換え
  - Rename
  - 別状態表現
  - 入れ子
  - 主語省略
  - 明示切替混在
  - 複数段落
  - 計画変更

## 3 seed平均

| 条件 | No carry pair / 精度 | 無条件carry pair / 精度 | Responsibility pair / 精度 |
|---|---:|---:|---:|
| 既知 | 0.2130 / 0.1944 | 0.0370 / 0.0185 | 0.2130 / 0.1944 |
| 未学習言い換え | 0.3148 / 0.2685 | 0.1204 / 0.0648 | 0.3148 / 0.2685 |
| Rename | 0.1574 / 0.1296 | 0.0556 / 0.0370 | 0.1574 / 0.1296 |
| 別状態表現 | 0.3704 / 0.0000 | 0.1389 / 0.0000 | 0.3704 / 0.0000 |
| 入れ子 | 0.0370 / 0.0370 | 0.0185 / 0.0093 | 0.0370 / 0.0370 |
| 主語省略 | 0.2870 / 0.0926 | 0.2963 / 0.0000 | 0.2870 / 0.0926 |
| 明示切替混在 | 0.3056 / 0.0556 | 0.4074 / 0.0093 | 0.3056 / 0.0556 |
| 複数段落 | 0.0093 / 0.0093 | 0.0000 / 0.0000 | 0.0093 / 0.0093 |
| 計画変更 | 0.0185 / 0.0185 | 0.0000 / 0.0000 | 0.0185 / 0.0185 |

責任診断:

- 主語省略 continuation recall: 0.0000
- 主語省略 carry率: 0.0000
- 主語省略平均除去責任: -0.0868
- 明示切替 wrong carry: 0.0000
- 既知 termination precision: 1.0000
- Responsibility+Null: 全split accuracy 0 / wrong 0 / null率1.0

## 判定

**中核仮説は強く反証された。**

### Counterfactual removal responsibilityは全体に負

各commitmentをprefixとして与えた場合より、与えない場合の方が現在turnの文字予測損失が低かった。

平均責任は、
- 既知: -0.0817
- 主語省略: -0.0868
- 明示切替混在: -0.0873

で全て負だった。

つまり形成したcommitment cellは次turn予測を担うlatent stateではなく、文字予測器にとって雑音になっている。

### 主語省略でも継続を一件も選ばない

主語省略のcontinuation recallとcarry率は0だった。

Cycle 025の二値gateと同じく、今回も責任方式は実質的にno-carryへ退化した。
無条件carryのpair recallは0.2963だが、Responsibility方式は0.2870まで低下した。

### 責任除去と意味的必要性が一致しない

Commitment文字列を予測prefixへ加える操作は、談話状態を内部遷移へ注入することではない。

文字n-gram文脈が変わるためNLLは変化するが、それは、
- object permanence
- relation binding
- goal continuation
- scope
- causal state
の責任を表さない。

> **入力文字列の除去影響は、内部予測状態の反実仮想除去ではない。**

### 候補選択能力も未成立

Responsibility方式は候補集合を平均29〜48 pair保持し、Nullなしではwrong commitが0.73〜1.0残った。

主語省略pair recall 0.2870に対しaccuracy 0.0926であり、候補包含を正答選択へ変換できていない。

### 計画変更は未成立

計画変更のpair recall / accuracyは0.0185 / 0.0185。
旧goal、最終goal、撤回、revision scopeを別の予測状態として保持できていない。

### Nullは全面棄権

Responsibility+Nullは全条件でwrong commitを0にしたが、null率1.0、accuracy 0。
安全停止であり能力増分ではない。

## 反証条件

仮説支持には以下が必要だった。

1. 主語省略で正の除去責任が複数seedで再現
2. continuation recallがNo-carryを上回る
3. 明示切替wrong carryを増やさずaccuracy改善
4. Responsibility方式がUnconditional方式より候補数を減らし精度を上げる
5. 計画変更で旧goal除去・新goal追加が分離
6. Nullなしでもjunk一意化を抑制

今回は全条件を満たさない。

## 資源量

- モデルサイズ: 9629 bytes
- Commitment prototype: 48.33
- 学習時間: 0.035621 sec
- 既知推論: 1.4135 ms/example
- 主語省略推論: 1.3868 ms/example
- Peak RSS: 160164 KiB（Python runtime込み）
- 推定計算量:
  - 文字予測 `O(NL)`
  - 区間生成 `O(L)`
  - commitment除去監査 `O(KL)`
  - sparse pairing `O(KoKv)`
  - `K≤6, Ko,Kv≤8`

1GB未満・5ms未満は小規模制御条件で達成した。
弱いスマートフォン実機は未検証。

## 系列A固有の進展

予測状態形成段階を更新する。

1. Prediction-error stream
2. Event cell
3. Predictive candidate
4. Prospective commitment
5. Event termination gate――反証
6. **Counterfactual-removal responsibility――今回反証**
7. State-transition-mediated responsibility
8. Sparse focus stack
9. Goal revision state
10. 自由日本語world state

核心的知見:

> **文字列commitmentを予測prefixとして除去するだけでは、latent stateの責任を測れない。責任はcommitmentが内部状態遷移のどの残差を説明したかに帰属させる必要がある。**

## 他系列へ返す知見

- B: binding nodeの除去効果は出力文字列ではなくstate-change endpoint再構成で測る。
- C: witness edge除去は複数transitionの局所残差へ帰属させる。
- D: memory element removalはquery全体lossではなく、該当endpointの未説明残差で評価する。
- E: residual mediatorは単なる入力prefix効果ではなく内部state updateを媒介する必要がある。

## 次の仮説

**Transition-Mediated Predictive Responsibility from Local Residual Routing**  
（局所残差routingを介した状態遷移型予測責任）

次はcommitment文字列を予測prefixへ直接入れない。

1. `before / command`から局所未説明残差cellを生成
2. 前turn commitmentごとに、どの残差cellへ接続できるか複数routing仮説を保持
3. Commitmentを除去したとき、そのrouting先残差だけが増えるか測定
4. 無関係な全体NLL変化はcreditに数えない
5. 主語省略ではobject residualを説明するcellだけcarry
6. 明示objectでは新cellが同じresidualを説明した場合に旧cellを終了
7. 計画変更ではgoal residualを旧案・最終案へ分離
8. Local residual reduction、continuation recall、wrong carry、観測前accuracyを独立評価

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
