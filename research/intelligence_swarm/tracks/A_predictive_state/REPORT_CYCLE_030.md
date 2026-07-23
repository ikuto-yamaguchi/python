# 系列A Cycle 030

## 仮説

**Operator-Centered Predictive State Birth from Recurrent Error-Cancellation Loops**  
（反復誤差相殺loopからのoperator中心予測状態創発）

Cycle 029ではraw spanへのmask介入から時間応答kernelを作ったが、route prototypeは0件だった。今回はspan identityを先に決めず、`before + command`から局所状態更新operatorを生成し、prospective state→逆更新→再適用の反復で同じ局所prediction errorを相殺するoperatorだけをpredictive state cellへ昇格できるか検証した。

## 重複表

| 系列 | 最新中心 | Aで棄却・分離した領域 |
|---|---|---|
| B | 独立probeによるprogram選択 | MDL・program elimination |
| C | target境界競合によるmechanism transport | 因果world graph |
| D | operator中心read/write endpoint | 長期memory・slow化 |
| E | split–merge boundary attractor | energy fixed point |
| **A** | **複数turnの予測誤差を反復相殺するoperator-state** | 今回の固有対象 |

Dもoperatorを扱うが、Dはread/write記憶endpointと再固定化、Aは現在状態から次観測へ向かう時間方向の予測状態と継続・終了を対象とする。

## 実装

- 固定ontology、手書きslot、辞書、RAG、外部LLMなし
- 学習時:
  - `before→after`の局所差分からoperator候補を生成
  - forward state update
  - inverse restoration
  - non-target preservation
  - 再適用時のidempotence
  を監査
- 推論時:
  - `before + command`のみ使用
  - current after/futureは選択に不使用
  - One-pass / unconditional carry / recurrent relaxationを比較
- 停止:
  - active集合不変
  - 最大6 sweep
  - candidate集合空

## 3 seed平均

| 条件 | One-pass 精度/null | Carry 精度/null | Recurrent 精度/null |
|---|---:|---:|---:|
| 既知 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 未知語順 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 未知語彙 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| Rename | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 入れ子 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 主語省略 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 明示切替混在 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 複数段落 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 計画変更 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |
| 反実仮想 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 1.0000 |

追加診断:

- Operator: 1.00
- モデルサイズ: 352 bytes
- 学習時間: 0.001070 sec
- 既知推論: 0.660 ms/example
- 主語省略推論: 0.521 ms/example
- 複数段落推論: 1.333 ms/example
- Peak RSS: 160100 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Operator birthがほぼ全面崩壊

複数の自由日本語表現から抽出した局所差分のうち、forward・inverse・保存・idempotenceを複数例で満たしたoperatorは平均1件だけだった。

左右contextを具体文字列で保持したため、補助文、別名、語順、長文化で適用位置が分裂した。operator中心へ移行しても、operator自体がsurface-localなedit ruleに留まった。

### Recurrent方式はOne-passを一件も改善しない

全条件でexecution accuracyは0、null率は1.0だった。Recurrent creditを加えてもactive候補の順位は変わらず、予測状態cellは形成されなかった。

> **反復誤差相殺はoperator選択原理にはなり得るが、実行可能operatorのbirth原理ではない。**

### 主語省略・時間的継続

主語省略ではcandidate集合が常に空で、carry率・continuation hitとも0だった。前turn stateを再利用する前に、現在turnへ適用できるoperatorとobject addressが形成されていない。

### 計画変更・反実仮想

旧案、最終案、実行世界、未実行世界を別operator-stateへ分離できなかった。候補生成段階で全面collapseしたため、競合・終了・切替の反復力学まで到達していない。

### 反証分類

- **Operator birth collapse**: 複数環境へ移るoperatorが平均1件
- **Candidate collapse**: 多くのturnでprospective state候補0
- **Recurrent credit collapse**: One-passと能力差0
- **Null safety degeneration**: 全面棄権
- **発散**: 最大6 sweepとactive集合縮小により未観測
- **局所最適**: 少数候補がある場合もtieで停止

仮説支持には、複数seedで複数operator-stateが形成され、Recurrent方式がOne-passよりexecution accuracy・主語省略continuation・計画変更state selectionを改善する必要があった。すべて未達。

## 既存方式との差

単純分類器や一方向transducerではなく、局所operatorからprospective stateを作り、forward/inverse/idempotenceを反復監査する設計である。Transformer attentionも使わない。

ただし現状は具体的contextに依存する離散edit prototypeであり、抽象operator、world state、active inference、予測符号化回路には未到達。

## 資源量

- Model: 約352 bytes
- Peak RSS: 160100 KiB
- Training: 約0.001070 sec
- Inference: 0.5〜2.1 ms/example
- 計算量:
  - operator induction `O(NL)`
  - proposal `O(OVPL)`
  - recurrent relaxation `O(SH)`
  - `P≤64, S≤6, H≤96`

1GB未満・5ms未満は小規模条件で達成した。弱いスマートフォンCPU実機は未検証。

## 系列A固有の進展

> **Span routeよりoperatorを先に置く研究順序は妥当だが、具体的左右contextから作るoperatorはsurface-localで、反復予測誤差相殺を開始できる候補集合を形成しない。次はoperatorの境界と引数を固定せず、独立probe上の誤差相殺で生成・統合する必要がある。**

## 他系列へ返す知見

- B: 独立probeは既存program選択に効いたため、Aでもoperator birth後の選択監査に利用価値がある。ただし候補birthの代替にはならない。
- C: target境界競合でも、具体context一致をoperator identityにするとtransport前にcollapseする。
- D: operator endpointをslow化する前に、複数surfaceで実行可能なoperator birthを独立監査すべき。
- E: boundary split–mergeで候補数を増やすだけでなく、forward/inverse error cancellationを局所energyへ入れる必要がある。

## 次の仮説

**Probe-Grounded Operator Birth from Cross-Input Recurrent Error Cancellation**  
（入力横断の反復誤差相殺によるprobe-grounded operator創発）

1. `before + command`を可変境界segmentへ分解
2. 各segment pairから引数境界未確定のoperator familyを生成
3. Induction入力でforward候補を作る
4. 独立probe入力へoperatorを転送
5. Probe outcomeは候補生成後の局所creditにのみ使用
6. Forward・inverse・再適用の誤差を複数probeで同時に減らすoperatorだけstate cell化
7. Exact左右contextを捨て、応答kernelでoperator class化
8. 主語省略では前turn operator-stateを再起動
9. 計画変更では旧operatorと最終operatorを競合
10. Shuffled-probe ablationで観測依存性を反証

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
