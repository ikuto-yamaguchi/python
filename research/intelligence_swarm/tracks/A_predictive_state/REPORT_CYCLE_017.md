# 系列A Cycle 017 研究報告

## 仮説

**Delayed Prediction-Error Recurrence States with Horizon-Separated Credit**  
（時間幅を分離した遅延予測誤差再発状態）

Cycle 016の次案だったprobe outcome tensorのrank/null空間検定は、系列B Cycle 016のrank-increasing intervention basisと中心機構・反証条件が重なるため棄却した。

今回は、生の日本語候補を即時予測誤差だけで選ばず、同じ誤差訂正signatureが1〜12 episode後にも再発する場合にだけ潜在予測状態へ昇格する仮説を検証した。潜在状態は固定ontology名を持たず、`immediate after error / delayed future error / span-size signature / recurrence horizon`だけで形成する。

## 他系列との重複表

| 系列 | 最新中心 | 有効部分 | 失敗・未解決 | A候補との判定 |
|---|---|---|---|---|
| B | separable intervention subspace / program role | rankだけではroleにならない | 未知形式0、surface圧縮 | rank/null probe案を重複として棄却 |
| C | executable operation fiber | 実行可能条件を先に分ける必要 | cross-form実行候補0 | operation algebraは扱わない |
| D | provenance-gated alias memory | cross-form同値性にはprovenanceが必要 | write崩壊、rename過分裂 | 長期memory mergeは扱わない |
| E | span–residual共同創発 | candidate recall 0では下流緩和不能 | raw basisがjunk収束 | energy最小化は扱わない |
| **A** | **時間を隔てて再発する予測誤差訂正から状態境界を昇格** | 今回検証 | open-form候補生成 | 系列固有 |

## 先行研究との関係

- 世界と言語を将来予測で統一する研究は、言語を将来観測・世界挙動・報酬予測の信号として扱う。
- 予測誤差によるevent segmentation研究は、誤差上昇をevent boundary形成へ使う。
- 2025年のpredictive-coding meta-RL研究は、部分観測下でcompact belief stateとactive information seekingの改善を報告する。

ただし既存研究の多くはニューラルencoder、既定観測空間、状態機械、視覚特徴を前提にする。本Cycleはraw日本語substringから状態境界を作る上流問題を対象とした。

## 実装

- raw commandから最大24 spanを生成
- command/stateの再出現spanをtarget候補、state非出現spanをvalue候補として最大32 pairを形成
- candidateをraw stateへ局所実行
- immediate afterとfuture observationの予測誤差を計測
- 誤差signatureが1〜12 episode後に再発するhorizon数をcreditへ加算
- 最大12個の匿名predictive stateを保持

比較:
1. random recurrence state
2. immediate-error state
3. delayed-recurrence state

## 実験条件

- seed: 1 / 7 / 19
- train: 24 / 48 / 96 episode
- test: 24例/split/seed
- split: seen / held paraphrase / rename / nested / subject omission / paragraph / plan change
- hidden object/valueは評価器専用

## 最大96 episode・3 seed平均

| 条件 | Candidate recall | Immediate accuracy / wrong | Delayed accuracy / wrong |
|---|---:|---:|---:|
| seen | 0.0000 | 0.0000 / 0.0139 | 0.0000 / 0.0139 |
| held | 0.0000 | 0.0000 / 0.0139 | 0.0000 / 0.0139 |
| rename | 0.0000 | 0.0000 / 0.0278 | 0.0000 / 0.0278 |
| nested | 0.0000 | 0.0000 / 0.0278 | 0.0000 / 0.0278 |
| omitted | 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.2361 |
| paragraph | 0.0000 | 0.0000 / 0.0139 | 0.0000 / 0.0139 |
| plan | 0.0000 | 0.0000 / 0.0139 | 0.0000 / 0.0139 |

## 判定

**中核仮説は強く反証。**

### Candidate recallが全split 0

seenを含め正しいobject/value pairが候補集合へ入らなかった。遅延credit以前にraw span境界・束縛候補形成が失敗している。

### Delayed recurrenceの能力増分0

全splitでaccuracy 0。seen/heldではimmediateとdelayedのwrong commitも同じ0.0139で、遅延horizonは候補classを意味的に分割していない。

### 主語省略では遅延creditが悪化

omitted条件はimmediateが全面棄権した一方、delayedはcandidate recall 0のままwrong commit 0.2361。時間的再発がjunk候補の表面signatureを強化した。

### Predictive stateではなくerror bucket

形成された11状態は誤差丸め値とspan長bucketであり、object、relation、operation、goal、constraint、causal variableを表現していない。

### 相関再発と状態同一性を分離できない

同じ誤差signatureが時間を隔てて現れても、同じ潜在状態変数が原因とは限らない。recurrence horizonはsurface failureの反復も強化する。

## 資源量

- delayed model: 49,978 bytes
- predictive states: 11
- training: 0.0645 sec
- inference: 0.5744 ms/example
- Peak RSS: 111,620 KiB（Python runtime込み）
- complexity: proposal `O(L²)`, fit `O(NH + R²)`, inference `O(SH)`, `H<=32`, `S<=12`

1GB未満・5ms未満は小規模制御条件で満たした。弱いスマートフォン実機は未検証。

## 系列A固有の進展

> 予測誤差の時間的再発は、候補生成が成立した後の状態持続性信号にはなり得るが、raw日本語からobject/value境界を生成する信号にはならない。候補外の状態で遅延creditを与えると、junk error attractorを強化する。

## 他系列へ返す知見

- B: cross-episode再現性は意味roleではなくfailure bucketも安定化する。
- C: operation fiberのsupportには実行成功だけを使い、実行不能の時間的再発をsupportにしない。
- D: alias linkの時間supportはtarget recall成立後にのみ加算する。
- E: repeated residualをcause basisへ昇格する前にcandidate recall gateを置く。

## 次の仮説

**Boundary-Action Co-Proposals from Prediction-Error Reduction under Reversible Split/Merge Moves**

次はspanを先に固定せず、文字境界のsplit/mergeとcandidate actionを同時に提案する。

- 境界split/mergeを局所可逆moveとして生成
- move後のcandidate実行がimmediate/future双方の絶対誤差を減らすか測る
- delayed recurrenceはcandidate recallが確認された後だけcredit化
- non-target保存を悪化させるmoveを棄却
- unknown候補を明示保持し、候補外で一意化しない

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
