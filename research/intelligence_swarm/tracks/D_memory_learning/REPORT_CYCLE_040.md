# 系列D Cycle 040

## 仮説

**Self-Predicting Memory Trace Birth from Leave-One-Episode-Out Replay Compression**  
（leave-one-episode-out replay圧縮からの自己予測memory trace創発）

Cycle 039では、候補traceをpaired replayへ転送して遅延再固定化を要求したが、fast/slow traceは0件だった。今回、境界traceを先に選別する方式をやめ、複数episodeのwrite変化とquery readを同時に短く説明する局所生成器を形成し、独立probeでwrite/read双方を予測できる生成器だけをmemory traceとみなせるか検証した。

## 重複表

| 系列 | 最新中心 | Dで棄却・分離した領域 |
|---|---|---|
| A Cycle 040 | microstate寿命とevent boundary | 時間予測状態・event開始終了 |
| B Cycle 040 | role-permutation quotient grammar | MDL・匿名production grammar |
| C Cycle 040 | state-difference tensor event | 因果event・低rankworld差分 |
| E Cycle 039 | constraint homotopy | energy basin・局所制約場 |
| **D Cycle 040** | **write/readを同時予測する圧縮生成器、削除必要性、fast/slow記憶** | 今回の固有対象 |

Bの圧縮・商化と重なるため、短い記述長や低rank性自体はDの進展としない。Dでは同じ生成器がprospective writeとquery readを閉じ、削除時に対応closed cycleだけが失われることを必須条件とした。

## 実装

- Modelは文字shape・局所context・相対境界から生成器候補を形成
- Literal / support圧縮 / 双方向probe接地 / shuffled probeを比較
- 独立probeでwrite成功2件以上・read成功2件以上・wrongより正支持が多い生成器だけをfast trace化
- Final testのafter/answerは生成器選択・rankingに不使用
- 各生成器を削除し、probe closed-cycleが選択的に低下するか監査
- 固定ontology、手書きslot、vector DB、RAG、外部LLMなし

## 3 seed平均

| 条件 | Literal closed/wrong | Compression closed/wrong | Bidirectional closed/wrong | Bidirectional null |
|---|---:|---:|---:|---:|
| 既知 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.1389 | 0.8611 |
| 未知語順 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.1944 | 0.8056 |
| Rename | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.1944 | 0.8056 |
| 別状態表現 | 0.4306 / 0.2917 | 0.1944 / 0.1667 | 0.0972 / 0.0000 | 0.9028 |
| 入れ子 | 0.0000 / 0.1250 | 0.0000 / 0.1250 | 0.0000 / 0.1806 | 0.8194 |
| 複数段落 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 1.0000 |
| 自由日本語 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 1.0000 |

追加診断:

- Literal generator: **32.67**
- Compression generator: **16.67**
- Bidirectional generator: **4.33**
- Shuffled generator: **2.67**
- Deletion-necessary generator: **0**
- Bidirectional model: **765 bytes**
- 学習時間: **0.422 sec**
- 推論: 既知 **2.575 ms/query**、複数段落 **5.871 ms/query**
- Peak RSS: **111628 KiB**（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### 圧縮生成器は形成された

Literal平均32.67件から、support圧縮で16.67件、双方向probe条件で4.33件まで削減できた。独立probe上でwrite/read双方に正支持を持つ小型生成器集合は形成された。

### 一般memory能力は形成されない

Bidirectional方式は別状態表現でclosed-cycle 0.0972を示したが、既知・未知語順・Rename・入れ子・複数段落・自由日本語ではclosed-cycle 0だった。既知ではwrong 0.1389、未知語順・Renameではwrong 0.1944が発生した。

別状態表現の信号もshuffleで0.0833残り、correct probe固有の差は極小である。局所context shapeと相対位置が一致したsurface再構成を完全には排除できない。

> **複数episodeを短く説明し、write/readを同時予測できることは、semantic memory traceであるための十分条件ではない。**

### 削除因果必要性は0

各生成器を削除しても、独立probeのclosed-cycle成功が選択的に低下する生成器は0件だった。形成された生成器は冗長なsurface候補か、そもそも正しいclosed cycleへ寄与しない候補である。

### One-shot・長期対話・干渉

今回の小型実装ではfinal条件のclosed cycleを中心に評価し、one-shot即時trace、長期干渉後保持、latest/obsolete競合の有効信号は形成されなかった。良い記憶が後から壊れたのではなく、semantic addressの初期形成が支配的失敗である。

## RAG・単純検索との差

保存文書やnearest-neighborを返していない。

1. 複数episodeから局所write/read生成器を形成
2. Prospective stateとquery answerを同じ生成器から生成
3. Leave-one-episode-out probeで再構成力を監査
4. 生成器削除のcounterfactualで必要性を測定
5. 必要かつ再現する生成器だけをfast/slow trace候補にする

という内部記憶統合を試した。ただしsemantic traceには未到達である。

## 先行研究整理

近年のcontinual learningでは、短期・長期memoryを分離するdual-memory設計、wake–sleep consolidation、疎なpattern separation、replay量を抑えるphasic consolidationが研究されている。しかし、これらはmemory slotや入力表現が既に存在する前提である。今回の未解決点は、その前段にある生の日本語からwrite/read共通traceを生成する問題である。

## 資源量・計算量

- Induction: `O(NL)`
- Probe grounding: `O(QGL²)`
- Inference: `O(GL²)`
- Deletion audit: `O(QG²L²)`
- Generator上限: 96

1GB未満は達成。既知は5ms未満だが複数段落は約5.87msであり、弱いスマートフォンCPUの長文条件と実機検証は未達。

## 系列D固有の進展

> **境界traceの後段選別から、write/read共同再構成を行う圧縮生成器へ研究順序を変更した。小型生成器集合は形成できたが、削除必要性0・広域転移0により、自己予測可能性もsurface圧縮からsemantic memoryを分離できないことを確認した。**

## 他系列へ返す知見

- A: event boundaryや寿命を圧縮できても、対応stateの削除必要性がなければsurface population boundaryの可能性が高い。
- B: MDL grammarは実行性能だけでなく、production削除時の選択的予測損失を採用条件へ含めるべき。
- C: 低rank差分componentは、対応eventを除去したときだけ特定world transitionが崩れるか監査すべき。
- E: constraint fieldの短い表現や反復収束ではなく、field除去による対応attractorの選択的崩壊が必要。

## 次の仮説

**Counterfactual-Deletion Memory Generators from Minimal Bidirectional Sufficiency Sets**  
（最小双方向十分集合からの削除因果memory生成器）

1. Generator単体ではなく小さなgenerator集合の組合せを探索
2. Writeとreadの双方を再構成する最小十分集合を求める
3. 集合内generator削除で対応episode群だけが崩れることを要求
4. 最も近いsurface generatorによる代替不能性を監査
5. Correct replay / shuffled replay / compression-only / deletionなしを比較
6. One-shotでは最小集合の局所fast weightだけ更新
7. Sleep phaseでは複数sessionの再構成bitを減らし、削除必要性も持つ集合だけslow統合
8. Latest/obsolete集合を同一潜在target上で競合

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
