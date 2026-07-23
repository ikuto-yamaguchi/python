# 系列D Cycle 038

## 仮説

**Active Replay Query Synthesis for Disagreement-Seeking Memory Address Birth**  
（address候補間の不一致を最大化する能動replay query合成）

Cycle 037では約32,000件の受動replay応答を商化してもread/write closed cycleを持つaddress familyは0件だった。本Cycleでは既存replayを待たず、address候補対が異なるwrite/read結果を返すquery・command摂動をoutcome-blindに合成し、`候補対の分割数 / replay記述bit`を最大化するqueryを選択した。

## 重複回避

| 系列 | 最新中心 | Dで扱わない領域 |
|---|---|---|
| A | Active object-disagreement query | 時間予測状態・sensor cell |
| B | Paired disagreement co-segmentation | MDL・production grammar |
| C | Multi-world event co-segmentation | 因果event・world model |
| E | Intervention-orthogonal sensor birth | Energy・hyperedge・attractor |
| **D** | **read/write address候補の能動識別、fast/slow memory、one-shot・干渉・latest保持** | 今回の固有対象 |

能動query生成そのものはA/B/Eと近いため新規性には数えず、同じ内部addressでwriteとreadを閉じ、one-shot・継続学習へ寄与するかだけを中心評価とした。

## 先行研究整理

Active continual learningでは、将来の学習と過去知識保持の両方に有益なサンプル選択が必要とされる。近年は累積informativeness、短期・長期memory比率、低予算下のreplay選択、forward-only fast weightsが研究されている。ただし、それらは表現・ラベル・memory slot・pretrained substrateを前提とする。本Cycleはその上流にある、生の日本語からのmemory address候補を識別するreplay queryを扱う。

## 実装

- `before / command / query`から64個の相対境界address候補を生成
- 候補対のwrite/read出力不一致を測定
- Value swap、query prefix shift、object maskingをoutcome-blindに合成
- `期待候補分割数 / query記述bit`で24 queryを選択
- Query合成後のみclosed/wrong/noexecを監査
- Passive / Random / Active / Shuffled-activeを比較
- Final test outcomeはcandidate生成・rankingに不使用

## 3 seed平均

| 方式 | Query | Disagreement | Description bits | Family |
|---|---:|---:|---:|---:|
| Passive | 24 | 0.00 | 10,813 | 0 |
| Random | 24 | 3,447.67 | 10,408 | 0 |
| Active | 24 | 3,298.00 | 10,259 | 0 |
| Shuffled active | 24 | 2,945.33 | 10,293 | 0 |

全方式・全条件でclosed accuracy 0、null率1.0。

追加診断:

- Base address: 64
- One-shot closed cycle: 0
- 干渉前 / 後 recall: 0 / 0
- Latest-value recall: 0
- Model size: 2,292 bytes
- Training: 0.003330 sec
- Inference: 0.00008047 ms/query
- Peak RSS: 111,164 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### 能動queryは候補不一致を作った

受動replayのdisagreementは0だった一方、Activeは平均3,298件の候補対不一致を作った。既存replayでは見えなかったaddress間の行動差を露出できた。

### しかし正しいclosed-cycle witnessは0

Active、Random、Shuffled-activeのいずれでも、2件以上の正しいread/write closed cycleを持ち、wrongより正支持が多いfamilyは0件だった。

> **不一致を最大化するqueryは候補を区別できるが、候補集合にsemantic addressが存在しなければ正しいaddressを生成しない。**

### ActiveはRandomを上回らない

Active disagreementはRandomより少なく、説明bitもわずかに短いだけだった。現在の摂動は意味的介入ではなく、相対位置をずらしてsurface prototypeを分岐させている。

### 破滅的忘却ではない

One-shot、干渉前後、latest recallはすべて0。良い記憶が後から壊れたのではなく、read/writeを同じsemantic addressへ束縛する初期形成が失敗している。

## RAG・検索との差

保存文章やnearest-neighborを返さず、候補addressへ能動合成queryを実行し、同じaddressでprospective writeとquery readを閉じるfamilyだけを内部推論状態へ採用する。ただしfamily 0のためsemantic associative memoryには未到達。

## 資源量・計算量

- Induction `O(NL²)`
- Active replay search `O(BP²Q)`
- Response quotient `O(PQ log P)`
- Inference `O(FPL)`
- Address上限64、query budget 24

1GB未満・5ms未満は達成。ただし高速なのは有効familyが0件である影響が大きい。弱いスマートフォンCPU実機は未検証。

## 系列D固有の進展

> **受動replayでは見えなかったaddress候補間の不一致を、outcome-blindな能動queryで露出できた。しかし不一致はsemantic read/write witnessではなくsurface位置prototypeの分岐で、fast/slow memoryへ統合可能なaddressは形成されなかった。**

## 他系列へ返す知見

- A: disagreement query数だけでstate cell成立を判定せず、object選択的closed witnessを必須化する。
- B: class分割効率が高くても、正しいproductionが候補内になければMDL grammarは失敗を圧縮する。
- C: paired-world co-segmentationでも、read/write双方のunique witnessを追加反証に使える。
- E: sensor直交性は候補応答差だけでなく、正しい固定点への選択的因果寄与を要求すべき。

## 次の仮説

**Co-Segmented Memory Address Birth from Paired Replay Worlds**  
（paired replay worldの共同分節によるmemory address創発）

1. Active queryと元episodeをpaired worldとして同時分節
2. 変化したcommand区間、state support、query targetを一つのlatent address proposalから共同生成
3. Valueだけ変えたpairでは同じsupport、objectだけ変えたpairではsupportとquery targetが同時移動することを要求
4. Passive / Active-selection-only / Co-segmentation / Shuffled pairを比較
5. 同じproposalでwrite→readとread→writeを閉じるunique witnessを必須化
6. One-shotではpaired residualからfast addressを即時生成
7. 複数sessionで再現し削除必要性を持つproposalだけslow統合
8. Latest/obsolete proposalを同一潜在target上で競合

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
