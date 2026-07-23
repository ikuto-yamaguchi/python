# 系列D Cycle 035 研究報告

## 仮説

**Deletion-Causal Consolidation from Delayed Replay Necessity**  
（遅延replay上の削除因果必要性による記憶統合）

Cycle 034では`before・command・query`の三視点境界を一つのproposalへ共同格納したが、Factorized baselineに対するclosed read/write能力増分は0だった。

当初の次案であるobject/value swap共変生成器は、系列A Cycle 035のcross-turn contrastive swap、系列B Cycle 035のjoint-born swap grammar、系列C Cycle 035の介入交換子、系列E Cycle 034のcommand-state swap workと中心機構が重なるため棄却した。

今回は系列D固有の問いへ移した。

> **あるmemory addressをslow memoryへ統合してよいのは、そのaddressを削除したときに独立した遅延replay上のreadとwriteが選択的に崩れ、最も近いsurface addressへ置換しても回復しない場合ではないか。**

## 先行研究整理

- 2025年のdual-memory continual-learning研究は、短期memoryと長期memoryの容量比が安定性・可塑性へ影響することを示すが、保存単位と表現は既に与えられている。  
  https://openreview.net/forum?id=wgjVUIYyOD
- CleanEditは各editのcounterfactual harmを推定して有害entryをpruneし、bounded replayへ戻す。ただしkey-value edit memoryが前提である。  
  https://openreview.net/forum?id=pguFq8hyd4
- AISTATS 2026の理論研究は、full replayでも後続noiseが過去signalを上回ると忘却が起き得ることを示す。  
  https://openreview.net/forum?id=BPYDrYmGWs
- これらに対し、本Cycleは保存済みsampleや定義済みmemory slotではなく、生の日本語から生成したread/write address候補そのものの削除因果必要性を監査する。

## 最新系列との重複表

| 系列 | 最新中心 | Dで棄却・分離した領域 |
|---|---|---|
| A | cross-turn command-state swap cell | 時間予測状態・reactivation |
| B | joint-born variable production | MDL・swap grammar |
| C | intervention commutatorによる因果方向 | world transition・因果非対称性 |
| E | command-state coupled work | energy固定点・局所work |
| **D** | **memory address削除による遅延read/write必要性、fast/slow統合、干渉・latest保持** | 今回の固有対象 |

## 実装

1. `before→after`差分からwrite区間候補を生成
2. `command`固有区間からvalue候補を生成
3. `before・command・query`の最大共通区間からobject候補を生成
4. 相対境界bucketと文字shapeで最大96 addressを保持
5. Independent delayed replayでread/write closed cycleを監査
6. Addressを一件削除したcounterfactual lossを計測
7. 最も近いsurface addressへ置換したときの回復を監査
8. 複数sessionで、削除時のみclosed cycleが2件以上失われるaddressだけslow化
9. Final test outcomeはretrieval・rankingに不使用

固定ontology、手書きslot、vector DB、文字列検索による文書返却、RAG、外部LLMは使用していない。

## 3 seed平均

| 条件 | Episodic closed / wrong read / wrong write | Replay-support closed / null | Deletion-necessity closed / null |
|---|---:|---:|---:|
| 既知 | 0.0000 / 0.3194 / 0.3194 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 未学習言い換え | 0.0000 / 0.0417 / 0.0417 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| Rename | 0.0000 / 0.5694 / 0.5694 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 別状態表現 | 0.0000 / 0.2917 / 0.3333 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 主語省略 | 0.0000 / 0.0417 / 0.0417 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 複数段落 | 0.0000 / 0.0000 / 0.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 自由日本語 | 0.0000 / 0.0417 / 0.0417 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |

追加診断:

- Address候補: **96.00**
- Replay-support address: **0.00**
- Deletion-necessary slow address: **0.00**
- Delayed replay audit: **97.00**
- Deletion test: **96.00**
- Replacement test: **0.00**
- Unique closed-cycle witness: **0.00**
- One-shot closed cycle: **0.0000**
- 干渉前／後recall: **0.0000 / 0.0000**
- Latest-value recall: **0.0000**

## 判定

**中核仮説は強く反証された。**

### 削除因果必要性へ到達する前にaddress groundingが崩壊

96個のepisodic address候補は形成されたが、独立replayで正しいread/write closed cycleを作ったaddressは0件だった。

- Unique closed-cycle witness: 0
- Replacement test: 0
- Slow address: 0

したがって「削除すると能力が落ちるか」を調べる以前に、削除対象となる有効memory addressが存在しなかった。

> **削除因果必要性は、既に機能するaddressの統合・剪定条件にはなり得る。しかしread/write addressのsemantic birth原理にはならない。**

### Episodic方式は誤commitを増やすだけ

全候補を保持するEpisodic方式は、正しいclosed cycleを一件も作らず、既知でwrong read/write 0.3194、Renameで0.5694へ達した。

これは表面位置・shapeが近い候補を記憶として再起動しただけであり、対象・変数・関係・操作の記憶ではない。

### Replay supportを要求すると全面棄権

正しいreplay supportが誤実行を上回る条件を課すと、active addressは0になった。Deletion necessity方式も全条件null率1.0である。

誤記憶を安全に除去できたのではなく、候補をすべて消して何も思い出せなくなった状態である。

### 破滅的忘却ではない

- One-shot: 0
- 干渉前recall: 0
- 干渉後recall: 0
- Latest recall: 0

良い記憶が後から壊れたのではない。初期address形成が失敗しており、破滅的忘却や選択的忘却を評価できる段階に達していない。

### Surface暗記との分離

Episodic方式はsurface類似だけで多数のwrong commitを返した。一方、独立replayと削除必要性を要求すると全消失した。

この差により、Cycle 034までの小さなread/write信号をsemantic memoryではなくsurface-local再適用としてさらに厳密に降格した。

## RAG・単純検索との差

文書やnearest neighborを返していない。候補addressを内部write/read operatorとして適用し、prospective stateとanswerを生成し、独立replay上の削除counterfactualでslow統合を判断した。

ただし現在のaddressは相対位置と文字shapeへ依存する離散prototypeであり、semantic associative memoryには未到達である。

## 資源量

- Necessity model: **9808 bytes**
- Peak RSS: **111812 KiB**（Python runtime込み）
- 学習時間: **0.051481 sec**
- 既知推論: **0.002683 ms/query**
- 複数段落推論: **0.002724 ms/query**
- 計算量:
  - Induction `O(NL²)`
  - Replay grounding `O(QPL)`
  - Deletion/replacement audit `O(QP²L)`
  - Inference `O(PL)`
  - `P≤96`

1GB未満・5ms未満は小規模条件で達成した。ただし高速なのは有効slow addressが0件になったことにも依存する。弱いスマートフォンCPU実機は未検証。

## 系列D固有の進展

> **記憶候補のsupportや再現回数だけでなく、削除時の選択的read/write損失とsurface代替不能性をslow統合条件へ導入した。しかし厳密監査に耐えるaddressは0件であり、過去の小さなmemory信号をsurface再適用として降格した。**

## 他系列へ返す知見

- A: transition cellを継続状態へ昇格する際も、cell除去で対応する時間予測だけが壊れるか監査すべき。
- B: 圧縮可能なproductionでも、除去して予測性能が落ちなければ意味symbolではない。
- C: 因果diagramはdiagram除去で対応介入だけが失われる選択的necessityを満たす必要がある。
- E: energy edgeがactive集合を変えるだけでなく、edge除去で正しい固定点だけが消えることを要求すべき。

## 次の仮説

**Loss-Born Memory Addresses from Bidirectional Replay Residual Transport**  
（双方向replay残差輸送によるloss-born memory address創発）

削除監査はaddress選別にしか使えず、birthには使えなかった。次は失敗したread/write残差からaddress境界を生成する。

1. Write成功・read失敗とread成功・write失敗を別channel化
2. Read residualをstate target境界へ逆輸送
3. Write residualをquery/object/value境界へ逆輸送
4. 双方向lossを同時に減らすboundary split・merge・shiftだけ新address化
5. Independent delayed replayで複数session再現を要求
6. Correct residual／shuffled residual／deletion-only／birthなしを比較
7. Address除去で対応closed cycleだけが崩れることを必須化
8. 一回提示ではresidual-born fast addressを即時利用
9. Sleep phaseでは必要性のあるaddressだけslow統合
10. Latest/obsolete addressを同一潜在target上で競合させる

- 高校生級: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機: **未検証**
- 完成: **未達**
