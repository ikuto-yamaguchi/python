# 系列A Cycle 018 研究報告

## 仮説

**Boundary-Action Co-Proposals from Prediction-Error Reduction under Reversible Split/Merge Moves**  
（可逆split/merge move下の予測誤差低減による境界・action共同提案）

Cycle 017では遅延予測誤差再発を状態同一性へ使ったが、既知を含む全splitでcandidate recallが0であり、主語省略では誤候補を強化した。本Cycleでは時間creditを後段へ移し、文字境界のsplit/mergeとcandidate actionを同時に提案し、即時after・future observation・non-target preservationを同時改善する局所moveだけを予測状態へ昇格させた。

## 他系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | A候補との区別 |
|---|---|---|---|---|
| B | 可逆境界・program共同帰納＋絶対MDL | 既知0.6944 | 未知形式0、モデル増大 | description length最適化は扱わない |
| C | latent state anchorとoperation transport | conditional評価漏れを除去 | transport coverage 0 | world operation fiberは扱わない |
| D | bridge episode alias transport | provenance保持 | slow link 0、干渉後recall 0 | 長期memory同値性は扱わない |
| E | frustration-driven candidate birth | null保持で誤確定抑制 | candidate recall 0 | energy relaxationは扱わない |
| **A** | **予測誤差で境界moveとactionを共同提案し、再帰状態へ昇格** | 今回検証 | boundary/action identifiability | 系列固有 |

## 先行研究との位置づけ

予測誤差をevent boundaryへ使う研究は、観測予測の急変がevent segmentationに有効であることを示す。active predictive codingは知覚と計画を階層状態で統合するが、既定の表現器・状態空間を前提とする。2026年のlatent-state研究でも、観測誤差最小化だけでは時間的に無秩序なlatent shortcutが生じ得るとされる。今回の課題は、固定表現器なしで生日本語の境界とactionを同時生成できるかにある。

## 実験条件

- seed: 1 / 7 / 19
- 学習: 24 episode
- test: 8例 / split / seed
- split: seen / held paraphrase / rename / alternate state / subject omission / paragraph / plan change
- ablation:
  1. Fixed exact boundary
  2. Reversible boundary-action co-proposal
  3. Co-proposal + delayed recurrence ranking
- candidate上限: 16
- move上限: 64
- learnerはraw before / command / after / futureと順序だけを使用。hidden object/valueは評価器専用。

## 3 seed平均

| 条件 | Fixed recall/accuracy | Co-proposal recall/accuracy/wrong | Recurrence recall/accuracy/wrong |
|---|---:|---:|---:|
| seen | 0.0000/0.0000 | 0.0000/0.0000/0.0833 | 0.0000/0.0000/0.0833 |
| held | 0.0000/0.0000 | 0.0000/0.0000/0.0000 | 0.0000/0.0000/0.0000 |
| rename | 0.0000/0.0000 | 0.0000/0.0000/0.0000 | 0.0000/0.0000/0.0000 |
| alternate | 0.0000/0.0000 | 0.0000/0.0000/0.0000 | 0.0000/0.0000/0.0000 |
| omitted | 0.0000/0.0000 | 0.0000/0.0000/0.0000 | 0.0000/0.0000/0.0000 |
| paragraph | 0.0000/0.0000 | 0.0000/0.0000/0.2500 | 0.0000/0.0000/0.2500 |
| plan | 0.0000/0.0000 | 0.0000/0.0000/0.1250 | 0.0000/0.0000/0.1250 |

## 判定

**中核仮説は強く反証。**

### 1. Candidate recallは全split 0

Co-proposalはseenで平均15.125候補、heldで12.708候補を生成したが、正しいobject/value組は一度も候補集合へ入らなかった。境界moveは候補数を増やしただけで、対象・値の束縛を生成していない。

### 2. 誤確定が増加

- seen wrong commit: 0.0833
- paragraph: 0.2500
- plan change: 0.1250

正答候補がない状態でafter/future類似を使うと、junk候補のうち予測誤差を偶然小さくするものを一意化した。

### 3. Delayed recurrenceの増分は0

Co-proposalとRecurrenceは全主要指標が完全に同一。時間的再発は既に即時/future gateを通ったsurface moveの順序を変えるだけで、候補classを追加分割しなかった。

### 4. 形成された状態は意味状態ではない

平均9.67 predictive stateは、候補長・context長・即時/future/non-target bitのbucketであり、object・relation・operation・goal・constraint・causeではない。

### 5. 計算量がスマートフォン目標を外れた

Co-proposal推論はseen 28.17ms、paragraph 33.84ms、plan 34.12ms。モデルは小さいが、`O(L²M)`の文字境界列挙が支配し、5ms目標を超えた。

## 資源量

- model: 6260 bytes
- moves: 64
- predictive states: 9.67
- training: 0.0695 sec
- inference: seen 28.17 ms/example
- Peak RSS: 111088 KiB（Python runtime込み）
- complexity: training `O(NL²M)`, inference `O(L²M+H)`, `M<=64`, `H<=16`
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 系列A固有の進展

> **予測誤差を境界探索へ直接戻すだけでは、正しい境界を生成せず「実行後の観測に偶然似る境界」を増殖させる。境界moveにはaction適用前に、対象候補と変化候補が異なる観測viewで独立に再現される識別条件が必要。**

## 他系列へ返す知見

- B: 絶対MDL利得だけでなく、object側・value側の独立view recallを先に測る。
- C: state anchorはafter再構成だけでなく、対象anchorと変化anchorを別transportで検証する。
- D: bridge episodeが同じtrajectoryを作っても、object/valueの誤束縛を独立反例で切る。
- E: frustration birth後にafter/future誤差だけで候補を昇格するとjunk attractorが生じる。

## 次の仮説

**Dual-View Boundary Birth from Independent Persistence and Change Predictions**  
（独立した持続予測・変化予測からの二視点境界生成）

次は単一のafter/future誤差でobject/valueペアを直接評価しない。

1. persistence view: before→futureで保存されるspan候補
2. change view: before→afterで置換されるspan候補
3. command view: persistence候補とchange候補を別々に説明する区間
4. 三viewの直積は全列挙せず、各viewでtop-kかつ独立反例を通った候補だけ結合
5. object候補recall・value候補recall・pair recallを分離計測
6. pair候補外ではunknownを保持し、active probeを実行しない

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
