# 系列A Cycle 024 研究報告

## 仮説

**Prospective Discourse State from Pre-Observation Prediction Commitments**  
（観測前予測commitmentからの前向き談話状態）

Cycle 023ではafter/futureへ露出したobject区間を過去側へ逆投影し、主語省略pair recallを0から0.2917へ回復した。しかしこれは現在turnの観測後にobjectを遡及説明したもので、command受理時点のobject permanenceではなかった。

今回は各turn終了時に、before・after・future1・future2で持続すると予測された上位4 cellを次turn向けにcommitした。主語省略turnでは、**現在turnのafter/futureを一切参照せず**、command・before・前turncommitだけからobject/value pairを生成した。

## 他系列との重複表

| 系列 | 最新中心 | 限定成功 | 主失敗 | Aとの分離 |
|---|---|---|---|---|
| B | 三者導出交差からの可逆binding seed | 既知局所script | grammar/binding seed未形成 | MDL・program帰納は扱わない |
| C | 対称情報付きevent replay | 評価非対称の除去 | event identity未形成 | 因果方向・world graphは扱わない |
| D | write-only classとquery-conditioned read address | read崩壊の防止 | slow link 0 | 長期memoryは扱わない |
| E | 環境分離介入に不変なenergy応答 | value候補限定信号 | object/pair binding崩壊 | energy dynamicsは扱わない |
| **A** | **次turn前の持続cell commitment** | 今回検証 | 前向き談話state | 系列固有 |

## 実験条件

- Seed: 1 / 7 / 19
- Train: 24 / 48 / 72 episode
- Test: 12例 / split / seed
- Commitment: 最大4 cell
- Object / value候補: 各最大8
- Pair: 最大48
- 比較: No carry / Retrospective / Prospective commitment / Commitment + Null
- 条件: 既知、言い換え、Rename、別状態表現、入れ子、主語省略、複数段落、計画変更

Hidden object/valueは評価器だけで使用した。Prospective方式は現在turnのafter/futureを候補生成・選択へ使用していない。

## 最大72例・3 seed平均

| 条件 | No carry pair recall | Retrospective | Commitment pair recall | Commitment accuracy |
|---|---:|---:|---:|---:|
| 既知 | 0.0556 | 0.3611 | 0.1111 | 0.0833 |
| 未学習言い換え | 0.2778 | 0.5556 | 0.1667 | 0.1389 |
| Rename | 0.2222 | 0.3611 | 0.0833 | 0.0556 |
| 別状態表現 | 0.3611 | 0.3611 | 0.3056 | 0.0278 |
| 入れ子 | 0.0556 | 0.0556 | 0.0556 | 0.0556 |
| 主語省略 | 0.1944 | 0.5833 | 0.4167 | 0.0833 |
| 複数段落 | 0.0278 | 0.0278 | 0.0278 | 0.0278 |
| 計画変更 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## 判定

**中核仮説は強く反証された。主語省略の候補recallに限定信号はあるが、前向き予測stateとしての選択能力は成立しなかった。**

### 主語省略pair recallは0.1944→0.4167

Prospective commitmentにより、主語省略のpair recallは0.1944から0.4167へ改善した。現在turnのafter/futureを見ずに、前turnの持続cellを候補集合へ運べた点はCycle 023の事後逆投影とは異なる。

### しかしaccuracyは0.0833

主語省略のcommitment accuracyは0.0833、wrong commitは0.9167だった。正しいpairを候補集合へ入れても、包含span・値候補・他の持続cellから選べていない。形成したのは安定したobject stateではなく、複数のsurface persistence候補である。

### 事後逆投影より弱い

主語省略のRetrospective方式はpair recall 0.5833、accuracy 0.4167だった。Prospective commitmentは観測漏洩を避ける代わりに精度が大きく低下した。Cycle 023の改善の多くが、現在turnのafter/futureにobject名が露出したことへ依存していたことを再確認する。

### 通常条件を悪化

言い換え・Renameではpair recallがNo carryより低下した。前turnのobject候補を無差別に持ち越すと、談話継続がないturnでもjunk候補を増やす。

### 計画変更は全面0

計画変更では全方式pair recall・accuracy 0。旧goal・新goal・revision scopeを別cellとして保持する時間的抽象化は未成立。

### Nullは安全だが全面棄権

Commitment+Nullは全splitでwrong commit 0だが、全件nullでaccuracy 0。安全停止であり能力ではない。

## 反証条件

1. 現在turn after/futureなしで主語省略object/pair recallを改善
2. AccuracyがNo carryを上回る
3. Wrong commitを増やさない
4. 非継続turnで過去objectを誤持続しない
5. 複数段落・計画変更でfocus/goal cellを分離

今回は1のみ限定達成、2〜5は未達。

## 資源量

- モデルサイズ: 11,907 bytes
- 学習時間: 0.005534 sec
- 推論時間: 8.757499 ms/example
- Peak RSS: 111,360 KiB（Python runtime込み）
- Predictive prototype: 64
- Commitment: 最大4
- Active pair: 主語省略平均46.83
- 計算量: character prediction `O(NL)`、interval proposal `O(L)`、commitment形成 `O(WL)`、sparse pairing `O(KoKv)`、`Ko,Kv≤8`

1GB未満は達成。主語省略の推論は5ms目標を超えており、弱いスマートフォン実機は未検証。

## 系列A固有の進展

> **観測前commitmentは主語省略の正答pairを候補集合へ運べるが、単純なsurface persistenceでは継続objectと無関係な持続spanを分離できない。前向きcandidate recallと前向きstate selectionは別問題である。**

## 他系列へ返す知見

- B: binding seedを持続させる際、次episodeでの再利用可能性だけでなく終了条件を符号化する。
- C: object permanence edgeには継続開始だけでなく、focus切替・終了eventが必要。
- D: memory endpointを再活性化する際、現在contextでの継続確率とforget gateを独立に持つ。
- E: attractorの持続性だけでobject identityを判断せず、basin終了条件を学習する。

## 次の仮説

**Event-Gated Prospective State with Learned Commitment Termination**  
（学習されたcommitment終了条件を持つevent-gated前向き状態）

次は全turnで上位cellを無条件carryしない。

1. 前turn終了時に持続候補と終了候補を同時生成
2. command開始時のsurprisal eventがfocus継続・切替のどちらを予測するか測定
3. 継続gate通過cellだけを主語省略候補へ注入
4. 新objectが明示されたturnでは旧commitmentを抑制
5. 複数object対話ではfocus stackを疎に保持
6. 計画変更では旧goal commitmentを終了し、新goalを別stateへ昇格
7. 観測前accuracy、wrong carry、termination precisionを主評価にする

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
