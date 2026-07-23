# 系列D Cycle 036

## 仮説

**Loss-Born Memory Addresses from Bidirectional Replay Residual Intersection**  
（双方向replay残差の交差によるloss-born memory address創発）

Cycle 035では、既存addressの削除因果必要性をslow統合条件にしたが、独立遅延replay上で正しいread/write closed cycleを作るaddressが0件だった。今回は既存候補の選別だけをやめ、write失敗のstate境界残差とread失敗のcommand-value境界残差が同一episodeで同時に存在する場合だけ、両境界を1 bucketずつ修復した新addressを生成した。

Final test outcomeはretrieval・rankingに使用していない。

## 他系列との重複表

| 系列 | 最新中心 | Dで棄却・分離した領域 |
|---|---|---|
| A | counterfactual sensor separation | 時間予測状態・多channel cell |
| B | residual-generating quotient production | MDL・program grammar・trace split |
| C | object-edge birth / paired worlds | 因果親・world transition |
| E | frustration residual node birth | energy hyperedge・attractor |
| **D** | **read/write残差の交差からmemory addressを新生し、fast/slow・干渉・latestを評価** | 今回の固有対象 |

単方向の境界残差輸送はA・B・Eで既に検証されているため、Dではreadとwriteの双方を同時に閉じる残差交差のみを採用した。

## 実装

- `before`内write境界、`command`内value/object境界、`query`内object境界を疎addressとして保持
- Independent delayed replayでread/write結果を監査
- Write残差からstate target境界、read残差からcommand value境界の修復方向を得る
- 双方が同時に存在する場合のみ1-step交差修復addressを生成
- 複数probeで2回以上成功し、失敗より成功が多いaddressのみ採用
- 複数session再現addressのみslow候補化
- Base / Residual birth / Slow / Shuffled residualを比較

固定ontology、手書きslot、vector DB、RAG、外部LLM、final-test正解利用はない。

## 3 seed平均

| 条件 | Base closed / wrong read / wrong write | Birth closed / wrong read / wrong write | Slow closed / null |
|---|---:|---:|---:|
| 既知 | 0.0000 / 0.3194 / 0.3056 | 0.0000 / 0.3194 / 0.3056 | 0.0000 / 1.0000 |
| 未学習言い換え | 0.0000 / 0.1944 / 0.2222 | 0.0000 / 0.1944 / 0.2222 | 0.0000 / 1.0000 |
| Rename | 0.0000 / 0.3194 / 0.3194 | 0.0000 / 0.3194 / 0.3194 | 0.0000 / 1.0000 |
| 別状態表現 | 0.0000 / 0.4444 / 0.4444 | 0.0000 / 0.4444 / 0.4444 | 0.0000 / 1.0000 |
| 主語省略 | 0.0000 / 0.2222 / 0.0417 | 0.0000 / 0.2222 / 0.0417 | 0.0000 / 1.0000 |
| 複数段落 | 0.0000 / 0.0000 / 0.0000 | 0.0000 / 0.0000 / 0.0000 | 0.0000 / 1.0000 |
| 自由日本語 | 0.0000 / 0.8056 / 0.6389 | 0.0000 / 0.8056 / 0.6389 | 0.0000 / 1.0000 |

追加診断：

- Base address：**64.00**
- Bidirectional residual intersection：**188.33**
- Residual-born address：**0.00**
- Shuffled residual intersection：**22.67**
- Shuffled residual-born address：**0.00**
- One-shot closed cycle：Base 0.0000 / Birth 0.0000
- 干渉前／後recall：Birth 0.0222 / 0.0222
- Latest-value recall：Birth 0.0222
- モデルサイズ：Birth **5597 bytes**
- 学習時間：Birth **0.033081 sec**
- 既知推論：Birth **0.1186 ms/query**
- 複数段落推論：Birth **0.1154 ms/query**
- Peak RSS：**111568 KiB**（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### 双方向残差交差は観測できた

Correct replayでは平均188.33件のepisode-address組で、write境界とread/value境界の修復要求が同時に発生した。Shuffled replayでは22.67件まで減少したため、残差交差数は正しいreplay対応へ依存する。

### 新addressは一件も採用条件を通らない

しかし複数probeで再現し、成功が失敗を上回るresidual-born addressは全seedで0件だった。Birth方式のaddress集合と能力はBase方式から変化していない。

> **Read残差とwrite残差が同じepisodeで交差することは、修復候補の生成トリガにはなるが、別episodeへ転送可能なsemantic address identityにはならない。**

残差修復は相対位置bucketを1段動かすだけであり、対象・変数・関係・operation・scopeを共同生成しない。異なる文面では同じ修復が再現しなかった。

### Closed cycle・one-shot・継続学習は未成立

既知条件でもclosed cycleは0。Base/Birthともreadとwriteの単独小信号に対して誤commitが大きい。One-shotは0、干渉前後とlatest-value recallはいずれも0.0222に留まる。

したがって支配的失敗は破滅的忘却ではなく、**semantic addressの初期形成失敗**である。良い記憶が後から壊れたのではない。

### Slow方式は全面棄権

Slow addressは0件で、全条件null率1.0。安全な統合ではなく、厳密条件で全候補が消失した結果である。

## RAG・単純検索との差

保存文書やnearest-neighborを返していない。生の日本語からwrite/value/object/query境界を生成し、prospective writeとread answerを内部状態として実行し、独立replayの双方向lossからaddressを局所生成する方式である。

ただし現状はsurface-localな離散境界prototypeであり、semantic associative memoryには未到達である。

## 先行研究との関係

近年のcontinual learningでは、短期・長期memoryを分離するdual-memory architecture、wake-sleep consolidation、疎memory、局所rehearsalが研究されている。これらは記憶保持・統合に有効だが、保存単位・表現・addressが既に与えられる。今回の失敗は、その前段である生の日本語からのaddress birthが未解決であることを示す。

## 資源量・計算量

- Induction：`O(NL²)`
- Delayed replay：`O(QPL)`
- Residual intersection birth：`O(QP)`
- Inference：`O(PL)`
- Address上限：128

1GB未満・5ms未満は小規模条件で達成。弱いスマートフォンCPU実機は未検証。

## 系列D固有の進展

> **削除必要性による選別から、双方向lossそのものをaddress birthへ戻した。Correct replayではread/write残差交差がshuffleより大幅に多いことを確認したが、再利用可能なaddressへ昇格する候補は0だった。残差位置ではなく、複数episodeをまたぐ機能的同一性が必要である。**

## 他系列へ返す知見

- A：複数sensor errorが同時発生しても、境界操作の再利用性がなければstate cellは生まれない。
- B：counterexample trace splitは新候補を生めても、複数episodeで同じ実行結果を持つproduction identityが必要。
- C：object edge birthでは位置残差だけでなく、object交換時にtargetだけが共変する外部選択性を必須にすべき。
- E：frustration gradientからnodeを生んでも、correct/shuffle差と機能的再現性を別ゲートにすべき。

## 次の仮説

**Replay-Response Equivalence Address Birth from Cross-Episode Residual Transport**  
（episode横断replay応答同値類によるmemory address創発）

1. 個別episodeの位置残差を直接address化しない
2. 各境界修復候補を複数の独立replayへ転送
3. Read成功・write成功・noexec・non-target damageを応答vector化
4. 具体位置やshapeではなく応答同値類でaddress familyを形成
5. Correct replayでのみ形成され、shuffleで消えるfamilyを要求
6. Family内の一候補削除で他候補が代替できる場合は統合せず冗長class化
7. Write/read双方のunique witnessを持つfamilyだけfast address化
8. 複数sessionで再現し、削除必要性も持つfamilyだけslow統合
9. One-shot・干渉・latest/obsolete競合を再評価

- 高校生級：未達
- ネイティブ日本語コミュニケーション：未達
- 弱いスマートフォン実機：未検証
- 完成：未達
