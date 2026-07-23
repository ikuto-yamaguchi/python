# 系列E Cycle 027 研究報告

## 仮説

**Predictor-Independent Residual Nodes from Cross-View Leave-One-Channel-Out Error**  
（view除去予測誤差からの候補独立residual node）

Cycle 026ではobject・value・residualを同じafter/future文字列から生成したため、110件のtriadic hyperedgeがsurface leakageへ退化した。

今回はcandidate span生成器とresidual生成器を分離した。

- Candidate channel: raw `command` spanと`before / after / future`の包含関係
- After residual channel: `before`だけから`after`を予測する文字予測器
- Future residual channel: `command`だけから`future`を予測する別order予測器
- Residual node: leave-one-channel-out条件で高surprisalとなる局所区間の位置・幅・文字shape
- Prototype: object/valueの文字shapeとresidual応答signatureの局所energy credit

Residual nodeは具体的なafter/future substringをkeyにせず、channel・位置bucket・幅・shapeだけを保持した。

## 先行研究整理

- 2026年のEquilibrium PropagationによるPredictive Coding Network学習は、局所energy最小化とEPがImageNet規模へ拡張可能であることを示す。ただしnode・layer・prediction errorは定義済み。
- 2026年のAugmented Lagrangian Predictive Codingは、局所constraint errorをdual変数へ蓄積し、深い系でcredit propagationを改善する。ただしconstraint topologyは既知。
- 2025年のcombinatorial EBM研究は、大規模離散空間でもenergyとpartition functionを共同学習できることを示すが、candidate spaceは事前定義される。

今回の対象は、それらより上流にある、生の日本語からcandidateと独立なresidual node・constraint topology自体を生成できるかである。

## 最新系列との重複表

| 系列 | 最新中心 | 限定信号 | 支配的失敗 | Eとの分離 |
|---|---|---|---|---|
| A | Cross-encoded residual routing | 局所credit正値 | surface routing、能力増分0 | 談話commitmentは扱わない |
| B | Counterfactual test program | positive/wrong/noexec分離 | surface cutでtie未解消 | 実行program・MDLは扱わない |
| C | Outcome-blind source-only transport | alignment/fiber形成 | target outcome leakage | 因果transitionは扱わない |
| D | Cross-temporal endpoint birth | fixed value inventory依存を監査 | raw span endpoint崩壊 | 長期memoryは扱わない |
| **E** | **候補と別channelの予測誤差residualをenergy node化** | 今回検証 | residual identity・candidate collapse | 系列固有 |

Aの残差routing、Cのsource-only transport、Dの時間横断endpoint birthと中心機構が重なる案は棄却し、Eではresidualをenergy緩和の局所nodeとしてのみ使用した。

## 実験条件

- Seed: 1 / 7 / 19
- Train: seen 48 + unknown 48 / seed
- Test: 36例 / split / seed
- After predictor order: 3
- Future predictor order: 2
- Candidate cap: object 6 × value 6
- Residual cap: 10
- Active state cap: 36 → 12
- Relaxation max: 6 sweep
- Ablation:
  1. Base energy
  2. Predictor-independent residual credit
  3. Residual credit + Null

学習器はhidden object/value labelをproposal・energy・rankingへ使用していない。ラベルは評価だけに使用した。

## 3 seed平均

| 条件 | Base精度 | Residual精度 | Residual+Null率 | Pair recall |
|---|---:|---:|---:|---:|
| 既知 | 0.0833 | 0.0833 | 1.0000 | 0.6759 |
| 未知語 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 曖昧性 | 0.0926 | 0.0926 | 1.0000 | 0.9537 |
| 入れ子 | 0.0000 | 0.0000 | 1.0000 | 0.1111 |
| 主語省略 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 複数段落 | 0.0000 | 0.0000 | 1.0000 | 0.0093 |
| 計画変更 | 0.0000 | 0.1019 | 1.0000 | 0.1019 |
| 反実仮想 | 0.0000 | 0.0833 | 1.0000 | 0.0833 |

追加診断:

- Residual prototype: 82.67
- Model: 12499 bytes
- Training: 0.040646 sec
- Seen active state: 9.28 → 2.78
- Plan active state: 4.00 → 1.53
- Counterfactual active state: 6.49 → 3.43

## 判定

**一般仮説としては反証。計画変更・反実仮想の候補内選択に限定信号。**

### Candidate-independent residualでactive集合は縮小

Residual方式は、

- 既知: 9.28 → 2.78
- 計画変更: 4.00 → 1.53
- 反実仮想: 6.49 → 3.43

へactive状態を縮小した。

Cycle 026のexact span tripleとは異なり、具体的文字列をprototype keyにしていないため、局所energy creditがheld-out入力へ作用した。

### 計画変更・反実仮想に限定的な選択信号

- 計画変更: 0 → 0.1019
- 反実仮想: 0 → 0.0833

Pair recallと同じ上限までaccuracyが上昇した。正答pairが候補集合内にある場合、residual response signatureがjunk候補を落とす限定信号を示した。

ただし絶対値は低く、全体としてwrong commitは0.90前後である。一般的なscope・goal・counterfactual world理解とは認めない。

### 既知・曖昧性では能力増分0

既知は0.0833のまま、曖昧性は0.0926のままだった。Residual prototypeは候補集合を縮めても、object/value/scopeの意味identityを形成していない。

### 未知語・主語省略はcandidate collapse

- 未知語 pair recall: 0
- 主語省略 pair recall: 0

Residual energy以前に正答object/valueが候補集合外である。Residual nodeは存在しない候補をbirthできない。

### Residualはprospective stateではない

Residual生成時には評価episodeのobserved `after / future`を使用している。候補生成器とはchannelを分離したが、観測前の意味推論ではない。

したがって今回示したのは、**観測後のcross-view errorが候補内rankingへ使える**ことまでであり、自由日本語から目的・制約・因果を事前形成する能力ではない。

### Nullは全面棄権

Residual+Nullは全splitでwrong 0・null率1.0・accuracy 0だった。安全停止だけである。

## Hopfield記憶・既存NNとの差

固定patternを想起するのではなく、入力ごとにobject/value候補を生成し、別channel予測器の局所誤差nodeと候補pairのenergyを結合し、active集合を反復収縮する点は単純Hopfield記憶と異なる。

一方、文字予測器と手続き的energyからなる最小実装であり、学習された意味energy network、正式な平衡伝播、局所Hebbian weight dynamicsには未到達である。

## 収束保証・失敗分類

各sweepでactive集合を`best + 0.06`以内へ単調縮小し、最大12状態に制限する。有限候補上でactive集合不変または最大6 sweepで停止する。

- **候補崩壊**: 正答object/valueが候補外
- **Residual identity崩壊**: response signatureが意味roleを分けない
- **観測後依存**: after/future観測が必要
- **局所最適**: wrong pairへ安定収束
- **Null安全停止**: 全面棄権
- **発散**: 未観測

仮説支持には、未知語・主語省略を含む複数splitでBaseを上回り、wrong commitを増やさず、residual prototypeが観測前入力だけで作用する必要があった。未達である。

## 資源量

- Model: 12499 bytes
- Peak RSS: 111360 KiB（Python runtime込み）
- Training: 0.040646 sec
- Inference:
  - Seen 0.5017 ms/example
  - Paragraph 1.0064 ms/example
- Mean sweeps: 2.0
- Max sweeps: 2
- Convergence: 1.0
- 推定計算量:
  - Predictor学習 `O(NL)`
  - Residual生成 `O(L)`
  - Prototype監査 `O(NOVR)`
  - Relaxation `O(SH)`
  - `O,V≤6、R≤10、H≤36、S≤6`

1GB未満・5ms未満は小規模制御条件で達成した。弱いスマートフォンCPU実機は未検証。

## 系列E固有の進展

> **候補生成器から独立した予測誤差channelを使うと、exact span leakageなしでもenergy landscapeを縮小し、計画変更・反実仮想の候補内選択に限定信号が出る。しかしobserved outcome依存であり、候補birth・意味role・観測前推論には到達しない。**

## 他系列へ返す知見

- A: residualを別encoderで作るだけでなく、current outcome非依存にしないとprospective responsibilityにならない。
- B: counterfactual testは正答観測後の差ではなく、programごとの事前予測差で生成する必要がある。
- C: positive witnessはtarget outcomeを隠したsource-only予測でのみ昇格させる。
- D: endpoint necessityはfuture/query正解観測をcandidate birthへ漏らさず、次時点の予測誤差で評価する。

## 次の仮説

**Prospective Residual Fields from Self-Consistency Disagreement without Outcome Access**  
（正解観測なしの自己整合不一致からの前向きresidual field）

次はafter/futureの実観測をresidual生成から外す。

1. `before + command`から複数のafter予測を生成
2. After予測から複数future予測を生成
3. 予測器間で一致しない局所位置だけresidual field化
4. Object/value候補とresidual predictorは別seed・別context幅を使用
5. Candidate pairごとに予測after/futureをrollout
6. Pairがresidual disagreementを減らす場合だけenergy credit
7. 観測after/futureは最終評価と局所weight更新時だけ使用
8. 未知語・主語省略・計画変更・反実仮想でcandidate birth／selectionを分離測定
9. Free/nudged phaseの局所相関差によるprototype更新を追加

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
