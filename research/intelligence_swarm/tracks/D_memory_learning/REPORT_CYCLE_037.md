# 系列D Cycle 037

## 仮説

**Replay-Response Equivalence Address Birth from Cross-Episode Residual Transport**  
（episode横断replay応答同値類によるmemory address創発）

Cycle 036では、read失敗とwrite失敗の位置残差交差がcorrect replayでshuffleより大幅に多かった一方、個別修復候補は別episodeへ再利用できず、residual-born addressは0件だった。

本Cycleでは位置・文字shapeそのものをaddress identityにせず、各基底addressと全1-step境界変異候補を48件の独立遅延replayへ転送し、各replayに対する以下の応答vectorで商化した。

- closed read/write成功
- 実行可能だが誤read/write
- 実行不能
- non-target damage

同一応答vectorを持つ候補が2件以上あり、closed成功が2件以上、wrongより多く、他familyが成功しないunique witnessを持つ場合のみfast address familyへ昇格する。複数sessionで再現したfamily memberだけslow候補とした。Final test outcomeはretrieval・rankingに使用していない。

## 先行研究整理

- Semantic-Aware Representation Learning（ICLR 2025）は疎活性とsemantic similarityを継続学習の表現再利用に用いるが、semantic representation自体は学習器へ与えられる。
- Rethinking Memory in Continual Learning（TMLR 2025）は短期・長期のdual-memory architectureを整理するが、保存単位とaddressは既知である。
- Semi-parametric Memory Consolidation（2025）はepisodic/semantic memoryとwake-sleep統合を組み合わせるが、入力表現とmemory substrateを前提とする。
- Replay4NCL（2025）は組込み向けreplayの計算・容量効率を改善するが、何を一つの意味記憶としてaddressするかは事前定義される。

今回の問題はこれらより上流であり、生の日本語から再利用可能なread/write address identityそのものを生成できるかを扱う。

## 他4系列との重複表

| 系列 | 最新中心 | Dで棄却・分離した領域 |
|---|---|---|
| A | counterfactual sensor分離とpredictive state cell | 時間予測・channel lesion |
| B | quotient productionとactive counterexample partition | MDL・program grammar |
| C | paired-world object edge / co-segmentation | 因果object-support edge |
| E | frustration residual node / sensor分離 | Energy固定点・constraint field |
| **D** | **遅延replayに対するread/write応答同値類、fast/slow統合、干渉・latest保持** | 今回の固有対象 |

単なる応答同値類形成はB/Cにも現れるため、新規性とはしない。Dでは同値類がqueryからread状態へ入り、同一addressでwriteし、one-shot・長期保持・latest選択へ寄与するかだけを中心評価とした。

## 3 seed平均

| 条件 | Base closed / wrong read / wrong write | Family closed / null | Slow closed / null | Shuffle closed |
|---|---:|---:|---:|---:|
| 既知 | 0 / 0.0972 / 0.0972 | 0 / 1.0000 | 0 / 1.0000 | 0 |
| 未知言い換え | 0 / 0.0833 / 0.0833 | 0 / 1.0000 | 0 / 1.0000 | 0 |
| Rename | 0 / 0.1111 / 0.1111 | 0 / 1.0000 | 0 / 1.0000 | 0 |
| 別状態表現 | 0 / 0 / 0 | 0 / 1.0000 | 0 / 1.0000 | 0 |
| 主語省略 | 0 / 0 / 0 | 0 / 1.0000 | 0 / 1.0000 | 0 |
| 複数段落 | 0 / 0 / 0 | 0 / 1.0000 | 0 / 1.0000 | 0 |
| 自由日本語 | 0 / 0 / 0 | 0 / 1.0000 | 0 / 1.0000 | 0 |

追加診断:

- Base address: 64
- 1-step mutation trial: 700
- Replay response audit: 32,416
- Correct response family: 0
- Family member: 0
- Unique closed-cycle witness: 0
- Shuffled response family: 0
- One-shot closed cycle: 0
- 干渉前 / 後 recall: 0.0222 / 0
- Latest-value recall: 0

## 判定

**中核仮説は強く反証された。**

平均64個のbase addressから約700個の1-step境界変異を作り、32,416件の独立replay応答を監査した。しかし、複数candidateが同じ応答vectorを持ち、2件以上の正しいclosed cycleとunique witnessを同時に持つfamilyは全seedで0件だった。Correct replayとshuffleの双方が空family集合へ収束した。

> **位置残差候補を複数replayへ転送し、外部応答で商化しても、元候補に正しいread/write閉路が含まれなければsemantic address familyは形成されない。**

Base方式は既知条件でwrong read/write 0.0972 / 0.0972を生じ、closed cycleは0だった。相対位置・文字shapeでsurface候補を起動しただけである。Family/Slow方式は全条件でnull率1.0となり、誤記憶を安全に選別したのではなく、厳密条件に耐えるaddressが一件もなく全面棄権した。

One-shot closed cycleは0。干渉前recall 0.0222、干渉後0、latest recall 0である。良い記憶が後から壊れたのではない。支配的失敗は、対象・変数・関係・操作を結ぶsemantic addressが初期形成されていないことにある。

## RAG・単純検索との差

保存文書やnearest-neighborを返す方式ではない。

1. before / command / queryから局所read/write候補を生成
2. 候補を複数の独立遅延replayへ実行
3. closed / wrong / noexec / damage応答vectorへ変換
4. 応答同値類をfast address候補化
5. 複数session再現候補だけslow統合
6. query起動valueを内部推論状態へ注入し、同じaddressでprospective writeを実行

ただしfamilyが0件のため、semantic associative memoryには未到達である。

## 反証条件

仮説支持には最低限、以下が必要だった。

1. Correct replayでのみresponse family形成
2. FamilyがBaseよりclosed-cycle accuracyを改善
3. Family除去で対応read/writeだけが崩壊
4. One-shotで新addressを即時利用
5. 干渉後も旧memoryを保持
6. Latestを保持しobsoleteだけを抑制
7. 未知表現・主語省略・長文へ転移

全条件が未達。

## 資源量

- Family model: 168 bytes
- Base model: 6,089 bytes
- Peak RSS: 112,156 KiB（Python runtime込み）
- Family training: 0.100722 sec
- Family inference seen: 0.000445 ms/query
- 計算量:
  - induction `O(NL²)`
  - mutation `O(P)`
  - replay response `O(QP)`
  - quotient `O(PQ log P)`
  - inference `O(PL)`

1GB未満・5ms未満は小規模条件で達成した。ただし小型・高速なのは有効familyが0件になった影響が大きい。弱いスマートフォンCPU実機は未検証。

## 系列D固有の進展

> **個別残差位置をaddress化する失敗から、複数replay上の外部read/write応答をidentityとする厳密監査へ進めた。その結果、過去のsurface-local候補群には再利用可能なclosed-cycle同値類が一つもないことを確定した。**

## 他系列へ返す知見

- A: sensor response classを作る前に、正しいobject-selective witnessが候補集合へ存在する必要がある。
- B: quotient圧縮はclass内部に正しい実行候補がなければbirth情報を生まない。
- C: paired-world response equivalenceだけでobject-support edgeは形成されない。
- E: response/frustration同値類をenergy化しても、正しいcandidate topologyがなければ空またはsurface attractorになる。

## 次の仮説

**Active Replay Query Synthesis for Disagreement-Seeking Memory Address Birth**  
（address候補間の不一致を最大化する能動replay query合成）

既存replayで正しいfamilyが自然に現れるのを待たず、候補address対が異なるread/write結果を返す最小query・command摂動を生成する。

1. Base/mutant address対の予測結果差を列挙
2. 値区間・query対象区間・state supportの最小摂動を合成
3. 期待address entropy減少 / replay記述bitを最大化
4. 外部outcomeは合成後の監査にのみ使用
5. Correct active replay / shuffled outcome / passive replay / random replayを比較
6. 識別された候補から新しい境界split・mergeを生成
7. Unique closed-cycle witnessを持つfamilyだけfast address化
8. 一回提示、長期干渉、latest/obsolete競合を再評価

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
