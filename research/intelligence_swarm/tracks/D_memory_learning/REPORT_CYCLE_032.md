# 系列D Cycle 032 研究報告

## 仮説

**Probe-Plastic Read–Write Address Topology from Consequence-Preserving Boundary Rewiring**  
（結果保存型boundary rewiringによるprobe可塑的read–write address topology）

Cycle 031では可変境界operator familyを96件形成し、独立probeから正負creditとslow候補を得たが、Operator方式はSurface方式を改善せず、write accuracy・one-shot・干渉保持・latest-value recallは0だった。

今回はprobeをfamily scoreへの加点に留めず、write consequenceが等価なfamily間にmerge edge、競合するfamily間にinhibitory edgeを形成し、正しいprobe outcomeを保つ境界shiftだけを新nodeとして生成するaddress topology可塑性を検証した。

## 開始時監査・重複表

| 系列 | 最新中心 | Dで棄却・分離した領域 |
|---|---|---|
| A | probe局所誤差からのtransition-kernel birth | 時間方向予測状態・carry |
| B | repair applicability codeによるsymbol production | MDL・program symbol |
| C | multi-value intervention fiber | 因果state-variable・world model |
| E | scope-gated boundary repair attractor | energy固定点・局所force |
| **D** | **write→read閉路、fast/slow topology、旧値忘却、干渉耐性** | 今回の固有対象 |

単なる境界修復、operator family分類、probeによるcandidate selectionは他系列と重なるため、系列Dの進展とは数えない。記憶固有の評価は、同じaddress topologyがwrite結果をqueryからreadできるか、one-shotで即時利用できるか、長期更新後も保持されるか、obsolete valueだけを忘れられるかで判定する。

共有STATEの高校生級・ネイティブ日本語・弱いスマートフォン実機は未達のままである。

## 先行研究整理

- FAAST（arXiv:2605.04651）は教師例をclosed-form fast weightsへ一回のforward passでコンパイルし、一定時間推論と低い適応コストを示す。ただし事前学習表現と教師ラベルを前提とし、生の日本語からaddress topologyを生成する問題ではない。
- Sparse Memory Finetuning（arXiv:2510.15103）は高活性memory slotだけを疎更新してforgettingを抑える。ただしmemory slotとaddress表現は既に存在する。
- Semi-parametric Memory Consolidation（arXiv:2504.14727）はepisodic/semantic memoryとwake–sleep統合を組み合わせるが、入力表現とmemory substrateを前提とする。
- Experience Replay（arXiv:2503.20018）はloss of plasticityを改善するが、replay対象を正しく表現・addressできることが前提である。

したがって今回の上流課題は、**何を疎更新・統合・replayするかを生の日本語から形成すること**である。

## 最小実装

- 固定ontology、手書きslot、RAG、外部LLMなし
- raw日本語の局所差分から相対境界nodeを生成
- inductionとindependent probeを分離
- probe consequence signatureが近いnode間へmerge edge
- 競合signature間へinhibitory edge
- positive consequenceを保存する境界shiftだけをrewire候補化
- query shapeからnodeを逆起動しvalueをread状態へ注入
- 2 probe以上・複数session支持・negative以下のnodeだけslow化
- correct probe／shuffled probe／topologyなし／slow-onlyを比較

## 3 seed平均

| 条件 | Family read/write | Plastic read/write | Slow read/write | Shuffle read/write |
|---|---:|---:|---:|---:|
| 既知 | 0.0972 / 0.0556 | 0.0972 / 0.0556 | 0.0556 / 0.0556 | 0.0833 / 0.0417 |
| 未学習言い換え | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| Rename | 0.1389 / 0.0139 | 0.1389 / 0.0139 | 0.1389 / 0.0139 | 0.0833 / 0.0139 |
| 別状態表現 | 0.0278 / 0.0000 | 0.0278 / 0.0000 | 0.0139 / 0.0000 | 0.0278 / 0.0000 |
| 主語省略 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 複数段落 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 自由日本語 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |

追加診断:

- Family node: 96.00
- Plastic topology edge: 48.67
- Consequence-preserving rewire node: 0.00
- Slow node: 3.00
- Probe update: 141.00
- Positive / negative: 8.00 / 133.00
- One-shot: 0.0000
- 干渉前 / 干渉後: 0.0278 / 0.0278
- Latest-value recall: 0.0833
- Obsolete-value recall: 0.0000

## 判定

**中核仮説は強く反証された。**

### Topology edgeは形成されたが、能力増分は0

Correct probeから平均48.67本のmerge/inhibitory edgeが形成された。一方、Family方式とPlastic方式は全条件でread/write accuracyが完全に同一だった。

つまりprobeはaddress graphの見た目を変えたが、queryから起動される候補順位、write対象、read値を一件も変えていない。

> **Topologyが形成されることと、記憶推論へ因果的に作用することは別である。**

### Consequence-preserving boundary rewireは0

Positive probe consequenceを保ったまま境界をshiftできる新nodeは全seedで0件だった。

現在のnodeは相対位置・old/new shape・query shapeへ依存し、境界を1 bucket動かすとwrite結果が壊れる。したがって得られたedgeは既存surface node間の相関であり、新しいsemantic address topologyではない。

### Correct probeとshuffleの差は小さく、構造支持にならない

Correct probeはpositive 8、shuffleはpositive 0となり、slow nodeもcorrectで3、shuffleで0だった。しかしseen readは0.0972対0.0833、writeは0.0556対0.0417に留まり、Plastic方式はFamily baselineを上回らない。

独立probeに依存する極小信号はあるが、topology plasticityの能力証拠ではない。

### Read/write閉路は未成立

既知ではread 0.0972、write 0.0556となりCycle 031より数値上は増えた。しかし同じepisodeについてreadとwriteが同時成功するone-shotは0である。

Renameではread 0.1389に対しwrite 0.0139、wrong write 0.125。これは同じsemantic addressから読み書きした結果ではなく、query形式と相対位置の別々のsurface一致である。

### Slow統合

Slow-onlyは既知write wrongを0へ減らしたが、read 0.0556・write 0.0556に留まる。未学習言い換えではread/writeとも正答0、wrong 0.0972である。

安全なsemantic consolidationではなく、少数surface familyへの強い選別である。

### 継続学習・選択的忘却

- One-shot: 0
- 干渉前 recall: 0.0278
- 干渉後 recall: 0.0278
- Latest-value recall: 0.0833
- Obsolete-value recall: 0

Obsolete recall 0だけを見ると忘却に成功したように見えるが、旧値も新値もほぼ読めていないため、選択的忘却の証拠ではない。

支配的失敗は破滅的忘却ではなく、**write consequenceとquery readを同じaddressへ結ぶ初期topologyの欠如**である。

## RAG・検索との差

保存文書や近傍vectorを返していない。

1. 生の日本語からwrite nodeを形成
2. 独立probeのwrite consequenceでnode間edgeを局所更新
3. Queryからgraphを逆起動
4. 値を内部read状態へ注入
5. 複数sessionで再現するsubgraphだけslow化

という内部状態統合を試した。ただし現在はsurface-localな相対位置graphであり、semantic associative memoryには未到達。

## 反証条件

仮説支持には最低限、以下が必要だった。

1. Correct probeでshuffleと異なるtopologyが形成される: **部分達成**
2. Consequence-preserving rewire nodeが複数seedで形成: **未達**
3. PlasticがFamilyよりread/write双方を改善: **未達**
4. One-shot write→read閉路が成立: **未達**
5. 干渉後recallとlatest recallが改善: **未達**
6. Rename・別状態表現・自由日本語へ転移: **未達**
7. Obsoleteだけを忘れ、latestを保持: **未達**

## 資源量・計算量

- Plastic model: 12714 bytes
- Slow model: 12706 bytes
- Peak RSS: 160348 KiB（Python runtime込み）
- Training: 0.033677 sec
- Inference:
  - seen Plastic 1.429 ms/query
  - paragraph Plastic 4.012 ms/query
  - paragraph Slow 0.203 ms/query
- Capacity:
  - node ≤ 96
  - edge ≤ 256
  - slow node平均 3.00
- Update量: 141.00 probe executions
- 推定計算量:
  - induction `O(NL)`
  - probe grounding `O(QFBV)`
  - topology comparison `O(F²)`
  - read/write `O(FBL)`

1GB未満・5ms未満は小規模条件で達成した。弱いスマートフォンCPU実機は未検証。

## 系列D固有の進展

> **独立probe consequenceから疎なaddress edgeを形成できても、そのedgeがquery→readとcommand→writeの共通経路に参加しなければ能力は変わらない。次に必要なのはnode間類似edgeではなく、write成功とread成功を同時に閉じるcycle edgeの局所生成である。**

## 他系列へ返す知見

- A: topology edge数ではなく、edge除去で対応する時間予測だけが崩れるかを必須監査にする。
- B: symbol/repair graphの圧縮前に、そのedgeが候補entropyとexecutionを実際に変えるか測る。
- C: intervention familyは結果一致だけでなく、write/readに相当する双方向閉路とfamily除去の局所効果を確認する。
- E: repair attractorのedge形成数ではなく、correct固定点へのbasin変更をshuffle・edge removalで検証する。

## 次の仮説

**Cycle-Closing Memory Addresses from Joint Write–Read Counterexample Transport**  
（write–read共同反例輸送による閉路型memory address創発）

1. Probe上でwrite成功・read失敗、read成功・write失敗を別残差channel化
2. Write境界残差をquery segmentへ、read残差をstate boundaryへ逆輸送
3. 両残差を同時に減らすwrite-node→value-node→query-nodeの三部cycleだけ生成
4. Correct probeでのみcycle topologyが生まれることを必須化
5. Shuffled outcome、edgeなし、片方向のみ、cycle removalを比較
6. One-shotでは1回のepisodeからfast cycleを即時利用
7. 複数sessionで再現するcycleだけsleep型slow統合
8. Old/new cycleを同一address内で競合させ、latest edgeだけを保持
9. Cycle除去で対応read/writeのみが崩れることを反証条件化
10. Top-k cycle indexで長文5ms未満を維持

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
