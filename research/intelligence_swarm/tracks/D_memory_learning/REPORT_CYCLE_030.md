# 系列D Cycle 030 研究報告

## 仮説

**Operator-Centered Memory Endpoints from Bidirectional Read–Write Consequence Kernels**  
（双方向read–write結果kernelによるoperator中心memory endpoint）

Cycle 029ではraw spanへのcross-channel介入応答kernelで記憶addressを形成し、Surface全面棄権から極小のread信号は得た。しかしwrong readが高く、Rename転移は0、slow化も安定改善を生まなかった。

今回はspanそのものではなく、局所write operatorを先に生成し、次の条件を同時に満たすoperatorだけをmemory endpoint候補とした。

- `before → after` の局所write成功
- `after → before` のinverse restoration
- query側のread kernelとの整合
- non-target保存
- independent probe sessionでの再実行
- 複数session支持後のみslow化

## 先行研究整理

- SARLは疎表現とsemantic similarityで継続学習の干渉を抑えるが、意味表現とtask構造は既に与えられる。  
  https://openreview.net/forum?id=WwwJfkGq0G
- Autonomous Memory Rehearsalは局所可塑性と自己再生で連続的な記憶追加を可能にするが、保存patternとnetwork topologyは既定である。  
  https://openreview.net/forum?id=WHqX7nWyHX
- Semi-parametric Memory Consolidationはwake–sleep型のepisodic/semantic統合を行うが、encoderとmemory representationを前提とする。  
  https://arxiv.org/abs/2504.14727
- Sparse Memory Finetuningは活性化されたmemory slotだけを更新して忘却を抑えるが、slot addressとpretrained representationは既存である。  
  https://arxiv.org/abs/2510.15103
- 2025年末のdual-memory分析はshort-term/long-term memoryの役割分離を強調するが、memory itemの意味identity生成は扱わない。  
  https://openreview.net/forum?id=wgjVUIYyOD

今回の課題は、それらより上流にある、生の自由日本語から読み書き可能なmemory endpoint operator自体を形成する問題である。

## 他系列との重複表

| 系列 | 最新中心 | Dで棄却・分離した領域 |
|---|---|---|
| A | probe-grounded operator birth | 時間方向の予測状態・carry |
| B | probe条件付きsymbol birth | MDL・program grammar |
| C | target boundary competition | 因果transition・world model |
| E | probe-nudged boundary attractor | energy固定点・境界緩和 |
| **D** | **read/write双方向結果でaddressされるfast/slow operator endpoint** | 今回の固有対象 |

Aもoperator birthを扱うが、Aは次turn prediction errorを相殺する時間状態、Dはone-shot read/write・長期対話・干渉・再固定化を扱う。

Bの独立probeが既存program選択に限定効果を出したため、Dでもinductionとprobe sessionを分離した。ただしprogram selectionやMDLは中心機構にしない。

## 実装

- 固定value inventoryをlearnerに使用しない
- 手書きslot・固定ontology・RAG・vector DB・外部LLMなし
- 生の日本語から局所差分operatorを生成
- Operator identityは具体valueではなく、左右context shape・old/new shape・query/write/read consequence kernelで表現
- Induction 70% / independent probe 30%
- Probe結果はoperator生成後のpositive/negative creditにのみ使用
- Slow条件:
  - positive probe support 2以上
  - 複数session
  - negativeがpositive以下

## 3 seed平均

| 条件 | Surface read / wrong | Operator read / wrong | Slow read / wrong |
|---|---:|---:|---:|
| 既知 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 未学習言い換え | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| Rename | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 別状態表現 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 主語省略 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 複数段落 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 自由日本語 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |

追加診断:

- Operator memory: 17.00
- Slow endpoint: 0.00
- Independent probe update: 0.00
- Positive / negative probe credit: 0.00 / 0.00
- One-shot: 0.0000
- 長期対話: 0.0000
- 未知領域転移: 0.0000
- 干渉後latest recall: 0.0000

## 判定

**中核仮説は強く反証された。**

### Operator候補は形成されたがprobe結果へ接続できない

平均17件のoperator memory候補は形成された。しかしindependent probe上で実行可能な境界候補が一件も生まれず、positive/negative credit・局所更新・slow endpointはすべて0だった。

Operator keyから具体文字列を外しshape化しても、target state内でどの左右境界へ適用すべきかを再構成できなかった。

### 全方式が全面棄権

Surface、Operator、Slowは、既知・言い換え・Rename・別状態表現・主語省略・複数段落・自由日本語でread accuracy 0、null率1.0だった。

> **双方向結果kernelは、実行可能operatorが別入力へ転送できた後のendpoint監査には使える。しかしoperatorの引数境界と適用位置を生む原理にはならない。**

### One-shotも0へ低下

Cycle 029のone-shot 1.0は、同一episode直後のsurface再読だった。今回はinduction/probe分離とoperator実行条件を厳しくした結果、one-shotも0になった。

これは性能低下ではあるが、表面再読をfew-shot learningと誤認しない評価健全化である。

### 長期対話・未知領域・干渉

- 長期対話 recall: 0
- 未知領域転移: 0
- 干渉後latest recall: 0

良い記憶が後から壊れたのではなく、書込みと読出しを結ぶoperator endpointが初期形成されていない。支配的失敗は破滅的忘却ではなく**operator-boundary birth collapse**である。

## RAG・検索との差

保存文章や近傍vectorを返す方式ではない。

1. raw日本語から局所write operatorを形成
2. operator適用後の状態変化kernelを保持
3. query kernelからoperatorを逆起動
4. independent probeでread/write consequenceを監査
5. 複数sessionで再現したoperatorだけslow化

ただし現状はoperatorを別入力で起動できないためsemantic associative memoryには未到達である。

## 反証条件

仮説支持には、最低限以下が必要だった。

1. independent probeでpositive operator creditが形成される
2. Operator方式がSurfaceよりread accuracyを改善する
3. wrong readを抑制する
4. one-shot・長期対話・未知領域・干渉後latestで非ゼロ
5. Slow方式がfast memoryよりprecisionか保持率を改善する

今回はすべて未達。

## 資源量

- モデルサイズ: 2910 bytes
- 学習時間: 0.008002 sec
- 既知推論: 0.379 ms/query
- 複数段落推論: 0.542 ms/query
- Peak RSS: 111496 KiB（Python runtime込み）
- 推定計算量:
  - operator induction `O(NL)`
  - independent probe audit `O(PBVL)`
  - read `O(BCL)`
  - `B≤64`

1GB未満・5ms未満は小規模条件で達成した。弱いスマートフォンCPU実機は未検証。

## 系列D固有の進展

> **Memory endpointをspanからoperatorへ移す順序は妥当だが、operator identityを結果kernelで表現するだけでは、別入力上の引数境界と適用位置を生成できない。Fast/slow creditより先に、probe-groundedなread/write operator birthが必要である。**

## 他系列へ返す知見

- A: operator-stateも具体contextから生成するとprobe transfer前にcollapseする。可変境界operator familyが必要。
- B: independent probeは選択には効くが、candidate birthを代替しないという限定がDでも再確認された。
- C: target boundary competitionはsource operatorがtargetで実行可能になるための境界birthを中心評価すべき。
- E: split–merge境界へ、forward/inverse read-write consequenceの独立probe creditを与える価値がある。

## 次の仮説

**Probe-Grounded Read–Write Operator Birth from Variable Boundary Families**  
（可変境界familyへの独立probe groundingによるread–write operator創発）

1. `before + command + query`を可変境界segmentへ分解
2. old/new/value境界未確定のoperator familyを生成
3. Inductionではforward候補を広く保持
4. Independent probeでwrite→read / read→writeを実行
5. 一方だけ正しい境界pairへlocal positive/negative credit
6. Exact contextではなくprobe consequence signatureでoperator class化
7. One-shot fast operatorを即時利用
8. 複数sessionで再現したclassだけslow化
9. Obsolete operatorだけを選択的に忘却
10. Correct probe / shuffled probe / no probeを比較

**高校生級知能: 未達**  
**ネイティブ日本語コミュニケーション: 未達**  
**弱いスマートフォン実機検証: 未達**  
**完成: 未達**
