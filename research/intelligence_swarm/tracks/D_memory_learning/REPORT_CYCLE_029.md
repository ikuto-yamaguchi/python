# 系列D Cycle 029 研究報告

## 仮説

**Functional Endpoint Birth from Cross-Channel Intervention Response Kernels**  
（channel横断介入応答kernelによる機能的endpoint創発）

Cycle 028ではraw span除去がquery・状態変化・futureの複数channelを同時に壊す場合だけendpoint候補化したが、read accuracyは0、wrong readは1.0だった。複数channel必要性が文字列再出現へ依存していたためである。

今回は具体的文字列をendpoint identity keyにせず、候補spanを一度除去した際の次の応答を量子化した。

- Query–state整合変化
- Command–state整合変化
- State–future整合変化
- Before–after保存整合変化
- 介入位置bucket
- span長・文字shape

学習後のmemoryはvalue内容を保持するが、検索addressは具体的value文字列ではなくquery kernelとstate kernelの応答類似度で形成する。複数sessionで再現したendpointだけをslow候補とした。

## 先行研究整理

- Semi-parametric Memory Consolidationはepisodic memoryとwake–sleep consolidationを統合するが、memory表現とencoderは既定である。  
  https://arxiv.org/abs/2504.14727
- HiCLはsparse pattern separation、autoassociative episodic memory、prioritized replayを組み合わせるが、grid/DG表現とtask routingを持つ。  
  https://arxiv.org/abs/2508.16651
- ESSENTIALは疎なepisodic featureとsemantic promptを統合するが、cross-attentionと事前表現を前提とする。  
  https://arxiv.org/abs/2508.10896
- 2025年のtransfer/interference研究は、共有表現による転移向上と干渉増加のtrade-offを示す。  
  https://doi.org/10.1038/s41562-025-02318-y
- 2026年のepisodic-to-semantic consolidationは、episodic memoryから別addressable semantic layerを決定論的に生成するが、事実fieldとidentity manifestは定義済みである。  
  https://arxiv.org/abs/2607.01988

今回の課題は、それらより上流にある、生の日本語からmemory endpointの機能的identity自体を形成する問題である。

## 他系列との重複表

| 系列 | 最新中心 | Dで棄却・分離した領域 |
|---|---|---|
| A | operator中心の反復prediction-error相殺 | 談話予測状態・carry |
| B | 独立probeによるprogram選択 | MDL・program grammar |
| C | target境界競合によるmechanism transport | 因果state transition |
| E | split–mergeによるenergy candidate birth | energy固定点・attractor |
| **D** | **query/state/future介入応答でaddressされるfast/slow associative endpoint** | 今回の固有対象 |

Aもresponse kernelを扱ったが、Aは前turn→現在turnの時間routeであり、Cycle 029ではroute prototype 0だった。Dでは長期記憶address、one-shot、干渉、latest-value保持へ限定した。

Bの独立probeは少数の既存program tieを解いたため、Dでも同一episode再構成だけをendpoint証拠とせず、独立test sessionを使用した。ただしprogram選択やMDLは扱わない。

## 実験条件

- seed: 1 / 7 / 19
- train: 既知36 + 未学習言い換え18 / seed
- test: 18例 / split / seed
- learner:
  - 固定value inventoryなし
  - 手書きslot・ontologyなし
  - RAG・vector DB・外部LLMなし
  - test answerをretrievalへ不使用
- ablation:
  - Surface
  - Functional kernel
  - Slow-only functional kernel
- 統合test:
  - 既知
  - 未学習言い換え
  - Rename
  - 別状態表現
  - 主語省略
  - 複数段落
  - 自由日本語query
- 追加:
  - 一回提示学習
  - 干渉系列
  - 最新値保持

## 3 seed平均

| 条件 | Surface read / wrong | Kernel read / wrong | Slow read / wrong |
|---|---:|---:|---:|
| 既知 | 0.0000 / 0.0000 | 0.0185 / 0.2407 | 0.0185 / 0.2407 |
| 未学習言い換え | 0.0000 / 0.0000 | 0.0185 / 0.2407 | 0.0185 / 0.2407 |
| Rename | 0.0000 / 0.0000 | 0.0000 / 0.3333 | 0.0000 / 0.3333 |
| 別状態表現 | 0.0000 / 0.0000 | 0.0185 / 0.0556 | 0.0370 / 0.2037 |
| 主語省略 | 0.0000 / 0.0000 | 0.0185 / 0.2407 | 0.0185 / 0.2407 |
| 複数段落 | 0.0000 / 0.0000 | 0.0185 / 0.2407 | 0.0185 / 0.2407 |
| 自由日本語 | 0.0000 / 0.0000 | 0.0185 / 0.2407 | 0.0185 / 0.2407 |

追加診断:

- Memory endpoint: 26.33
- Slow endpoint: 14.33
- 更新量: 162
- モデルサイズ: 3037 bytes
- 学習時間: 0.014117 sec
- 既知Kernel推論: 16.368 ms/query
- 既知Slow推論: 9.166 ms/query
- Peak RSS: 168160 KiB（Python runtime込み）
- One-shot: Surface 1.0000 / Kernel 1.0000 / Slow 0.0000
- 干渉後recall: Surface 0.0370 / Kernel 0.0741 / Slow 0.0741
- 最新値recall: Surface 0.0741 / Kernel 0.0370 / Slow 0.0370

## 判定

**中核仮説は強く反証された。機能応答kernelに極小信号はあるが、semantic endpoint・継続学習能力は成立しない。**

### Surface全面棄権からは脱した

Surface ablationはtest state中に複数の既知value memoryが同時に存在するため全面tieとなり、全条件read 0・null 1.0だった。

Kernel方式は既知・言い換え・主語省略・複数段落・自由queryで0.0185の正答を返した。別状態表現のSlow方式では0.0370だった。

ただし正答率は極小で、wrong readは多くの条件で0.24〜0.33である。能力成立とは判断しない。

### Kernelは誤ったaddressも活性化

具体的文字列をidentity keyから外しても、量子化kernelは次に支配された。

- 文字shape
- state内の位置bucket
- 共通句読点構造
- query/stateの粗い文字集合重なり
- 値境界を含まない短いsegment

同じ応答kernelを持つ候補が同一relation・value endpointとは限らず、誤addressを活性化した。

> **局所span介入への同じcross-channel応答は、semantic endpoint identityの十分条件ではない。**

### Slow化の能力増分はほぼ0

平均14.33件のslow endpointが形成されたが、既知・言い換え・主語省略・複数段落・自由queryでKernelとSlowの能力は同一だった。

別状態表現のみ0.0185→0.0370へ増えたが、wrong readも0.0556→0.2037へ増加した。安全なsemantic consolidationではない。

### One-shotは同一episode再読

Surface/Kernelのone-shot 1.0は、一回提示直後に同一episodeを読む制御条件であり、未知surface転移や概念学習の証拠から除外する。Slowは複数session条件により0だった。

### 干渉・最新値

Kernelは干渉後recallを0.0370→0.0741へ増やしたが、絶対値は低い。最新値recallは0.0741→0.0370へ悪化した。

古いvalueと新しいvalueを同じaddressへ束縛する機構がなく、選択的忘却・再固定化は未成立である。

### 支配的失敗は破滅的忘却ではない

- 初期readが0.0185程度
- Renameは正答0
- wrong readが高い
- latest-value保持が悪化
- slow化が能力を増やさない

したがって良い記憶が後から壊れたのではなく、**query・relation・valueを同じ更新operatorへ結ぶendpoint identityの初期形成失敗**である。

## RAG・検索との差

保存文書や近傍vectorをそのまま返していない。

1. 生の日本語からsegment候補を生成
2. 各候補への局所介入が複数予測channelへ与える応答をkernel化
3. Query kernelとstate kernelの機能的一致でmemory内容を内部read状態へ注入
4. 複数session再現後だけslow候補化

ただしvalue内容はepisodic memoryとして保持しており、現段階は小型の疎association prototypeである。意味推論状態や一般的semantic memoryには未到達。

## 破滅的忘却と表面暗記の反証条件

Semantic memory支持には次を同時に満たす必要があった。

1. Rename・自由queryでSurfaceを上回る
2. Wrong readを増やさない
3. One-shot後の未知surface転移
4. 干渉後recallの大幅改善
5. 最新値を保持しobsolete valueだけ忘却
6. Slow endpointがfast endpointより高精度
7. 同一kernel class内で文字列・位置・shapeを変えても再現

今回はすべて未達または極小であり、表面暗記・粗い構造一致を棄却できない。

## 資源量・計算量

- モデル: 3037 bytes
- Peak RSS: 168160 KiB
- 学習: 0.014117 sec
- 推論:
  - Kernel 16.368 ms/query
  - Slow 9.166 ms/query
- Memory: 26.33
- Slow memory: 14.33
- 更新: 162
- 推定計算量:
  - Segment生成 `O(NL)`
  - Kernel監査 `O(NSC)`
  - Read `O(BCL)`
  - `B≤64`

1GB未満は達成したが、Kernel推論は弱いスマートフォン目標の5msを超えた。Slow方式も平均9ms前後であり、実機未検証。

## 系列D固有の進展

> **Cross-channel介入応答はsurface exact-matchより多くの候補を活性化できる。しかし、raw spanへの介入ではquery・relation・valueを結ぶ更新operatorが存在せず、粗い応答同値類が誤addressを増やす。Memory endpointはspanではなく、状態を読み書きする局所operatorを中心に形成する必要がある。**

## 他系列へ返す知見

- A: Cycle 029の結論を支持する。raw span response kernelより、実行可能operatorを先に形成し、その除去でprediction errorが再発するか測るべき。
- B: 独立probeの限定成功は有効。Dでもendpoint候補の独立session選択は必要だが、候補birthの代替にはならない。
- C: Target境界を複数source mechanismで競合させる際、境界spanの応答一致だけでなく読み書き結果を評価すべき。
- E: Boundary split–mergeで生まれたsegmentも、状態更新operatorとしてread/writeできることを別gateにする必要がある。

## 次の仮説

**Operator-Centered Memory Endpoints from Bidirectional Read–Write Consequence Kernels**  
（双方向read–write結果kernelによるoperator中心memory endpoint）

次はspan自体をendpoint class化しない。

1. `before + command`から局所write operator候補を生成
2. Operator適用後のstate変化・non-target保存・future予測をkernel化
3. Queryから候補operatorを逆起動し、対応state値をreadできるか監査
4. Write→readとread→writeの双方で同じ結果へ到達するoperatorだけfast endpoint化
5. Operator除去で対応read/write lossが再発することを必須化
6. 一回提示ではfast operatorを即時利用
7. 独立session・複数surface環境で再現した場合だけslow化
8. Old/new operatorを同一addressで競合させ、obsoleteだけ選択的に忘却
9. Top-k operator indexで推論を5ms未満へ削減

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機: **未検証**
- 完成: **未達**
