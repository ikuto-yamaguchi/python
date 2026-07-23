# 系列D Cycle 034

## 仮説

**Shared-Generator Memory Cycles from Tri-View Boundary Co-Induction**  
（三視点境界共同誘導による共有生成器memory cycle）

Cycle 033ではwrite境界・value・query nodeを別々に生成してから三部cycleへ接続したが、closed read/write能力はfactorized baselineを改善しなかった。今回は一つのlatent proposalから、次の4区間を同時に生成した。

- `before`内のwrite target
- `command`内のvalue
- `command`内のobject
- `query`内のobject

独立probeでwriteとreadが同時成功したproposalのみ正creditを受け、境界修復も4視点を同方向へ一括移動する共同rewiringに限定した。Final testのoutcomeは候補生成・rankingに使用していない。

## 重複表

| 系列 | 最新中心 | Dで扱わない領域 |
|---|---|---|
| A | Command-state共同創発transition cell | 時間予測・turn再起動 |
| B | Joint-born variable production grammar | MDL・program grammar |
| C | Command-coupled intervention fiber | 因果world transition |
| E | Command-state coupled energy fiber | Energy固定点 |
| **D** | **write/value/queryを共同生成するfast/slow memory address** | 今回の固有対象 |

共同生成という操作は他系列にも現れるため、それ自体を新規性としない。Dではone-shot write→read閉路、長期保持、干渉耐性、latest値選択を中心評価とした。

## 3 seed平均

| 条件 | Factorized closed | Joint closed | Slow closed | Shuffle closed |
|---|---:|---:|---:|---:|
| 既知 | 0.1250 | 0.1250 | 0.0417 | 0.1111 |
| 未学習言い換え | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Rename | 0.0278 | 0.0278 | 0.0139 | 0.0278 |
| 別状態表現 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 複数段落 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 自由日本語 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

追加診断:

- Factorized proposal: 35.67
- Joint proposal: 41.67
- Correct probe固有joint birth: 6.00
- Slow proposal: 1.33
- Probe audit: 23.33
- One-shot closed cycle: 0.3333
- 干渉前／後recall: 0.1389 / 0.1389
- Latest-value recall: 0.1667
- モデルサイズ: 3513 bytes
- 学習時間: 0.003644 sec
- 既知推論: 0.0833 ms/query
- 複数段落推論: 0.0867 ms/query
- Peak RSS: 159872 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Correct probe固有の共同境界birthは形成

Correct probeでは平均6件の共同rewiring proposalと1.33件のslow proposalが形成された。Shuffleではbirth 0・slow 0だったため、構造生成が独立probeの正しいwrite/read対応に依存することは確認できた。

### Joint方式はFactorizedを改善しない

既知closed cycleはFactorized 0.1250、Joint 0.1250で同一だった。未学習言い換え・Rename・別状態表現・主語省略・複数段落でも能力増分は0である。

共同rewiringで増えたproposalは、最終的なread値・write状態を一件も正しく追加選択しなかった。

> **複数視点の境界を同時に動かすことと、それらが一つの意味変数から生成されることは同じではない。**

### One-shot 0.333は新原理の成果ではない

One-shot closed cycleはFactorized・Joint・Shuffleで全て0.333だった。新episodeから形成したproposalではなく、既存surface proposalが同一形式へ適用された結果である。未知表現への一回提示転移ではないため、fast learningの証拠から除外する。

### 誤commit

Joint方式は既知でwrong read 0.1528、wrong write 0.1667、Renameで双方0.3056だった。Shuffleより既知の正答closed cycleは0.0139増えたが、誤commitも増えており、安全なmemory integrationではない。

### Slow化

Slow方式は既知closed cycleを0.0417へ下げ、ほぼ全面棄権した。複数session支持を要求するだけでは意味記憶統合にならない。

### 破滅的忘却ではない

干渉前後recallはともに0.1389で変化せず、latest recallは0.1667に留まった。良い記憶が後から壊れたのではなく、semantic addressが最初から成立していない。

## RAG・検索との差

保存文書や近傍vectorを返す方式ではない。

1. before・command・queryから共同latent boundary proposalを形成
2. Proposalでprospective writeを実行
3. 同じproposalからquery readを起動
4. 独立probeでwrite/read閉路を監査
5. 複数sessionで再現したproposalだけslow化

ただし現在のproposalは相対位置・文字shape・surface object一致に依存し、semantic associative memoryには未到達である。

## 資源量

- Model: 約3513 bytes
- Peak RSS: 159872 KiB
- Training: 0.003644 sec
- Inference: 0.08 ms/query前後
- Proposal上限: 128
- 計算量:
  - induction `O(NL)`
  - probe grounding `O(QPL)`
  - inference `O(PL)`

1GB未満・5ms未満は小規模条件で達成した。弱いスマートフォンCPU実機は未検証。

## 系列D固有の進展

> **後付けcycle接続から共同境界生成へ進めても、共有されるのが位置・shapeだけならsemantic addressにならない。共同生成器には、値交換とobject交換に対する三視点の共変化を学習する必要がある。**

## 他系列へ返す知見

- A: State・command区間を同時生成するだけでは時間state identityにならず、cross-value/object swapによる共変化が必要。
- B: Joint-born productionも共同位置codeだけではsemantic variableにならず、swap後の実行結果をMDL対象へ含める必要。
- C: Command-state fiberではobject交換時にtarget supportだけが切り替わることを必須化すべき。
- E: Coupled energy edgeも位置共起だけで形成するとsurface attractorへ退化する。

## 次の仮説

**Swap-Covariant Memory Generators from Joint Object–Value Intervention Cycles**  
（object・value共同介入cycleからのswap共変memory生成器）

1. 一つのproposalからwrite・value・command object・query object区間を共同生成
2. Command valueを別値へswapし、write結果とread回答が同じ値へ共変することを要求
3. Objectを別対象へswapし、state targetとquery targetだけが同時に切り替わることを要求
4. Value swapとobject swapの双方を満たすproposalだけfast address化
5. Correct swap／shuffled swap／value-only／object-only／no-swapを比較
6. 一回提示ではswap-consistent proposalだけ即時更新
7. 複数sessionで再現するproposalだけsleep型slow統合
8. Old/new proposalを同じaddress内で競合させlatestを保持
9. Address除去で対応read/writeだけが崩れることを必須化

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
