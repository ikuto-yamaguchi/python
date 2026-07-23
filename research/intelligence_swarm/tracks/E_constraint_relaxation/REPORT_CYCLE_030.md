# 系列E Cycle 030 研究報告

## 仮説

**Probe-Nudged Boundary Attractors from Independent Cross-Input Constraint Violations**  
（独立入力の制約違反でnudgeされる境界アトラクタ）

Cycle 029では境界split/merge/shiftにより候補集合を非空にできたが、正しいobject/value/target境界は上位候補へ残らず、free/nudged差分による局所更新は0だった。

今回は候補生成と評価を分離し、inductionとは独立したprobe episodeで、各境界候補が生成するafterの制約違反を監査した。片方だけ正しい候補pairがある場合、その境界signatureへ正の局所force、誤境界へ負のforceを与え、final testではprobeから得た局所weightだけでenergy relaxationを行った。

- 推論時: `before + command`のみ使用
- Probe outcome: 候補生成後の局所nudgeにのみ使用
- Final test outcome: rankingへ不使用
- Ablation: no probe / correct probe / shuffled probe
- 固定ontology、手書きslot、辞書、分類器、RAG、外部LLMなし

## 先行研究整理

Equilibrium Propagationはfree phaseとnudged phaseの固定点差から局所学習信号を得るが、状態変数・結合・energy topologyは既に定義されている。2025–2026年のLagrangian・dissipative dynamicsへの拡張も、時間軌道と境界条件を明示した系を前提とする。

今回の課題は、正解境界が定義されていない生の日本語から、probe制約違反を使って境界node自体を形成できるかである。

## 他系列との重複表

| 系列 | 最新中心 | Eで棄却・分離した領域 |
|---|---|---|
| A | Probe-grounded operator birth | 談話予測状態・時間誤差相殺 |
| B | Probe条件付きsymbol birth | MDL・program同値類 |
| C | Intervention-equivalence mechanism family | 因果transition・world graph |
| D | Probe-grounded read/write operator birth | 長期memory・再固定化 |
| **E** | **独立probe違反による境界energyの局所nudgeと固定点** | 今回の固有対象 |

Bでは独立probeが既存surface-local programの選択に限定信号を出した。C・Dでは正しいoperator候補が存在せずprobe監査が空になった。Eでは、境界candidate birth後にprobeが局所energyを更新できるかだけを中心機構とした。

## 実験条件

- seed: 1 / 7 / 19
- induction: 72例 / seed
- independent probe: 36例 / seed
- final test: 24例 / split / seed、別seed
- 候補上限: 96
- active上限: 24
- relaxation上限: 6 sweep
- test: 既知、未知語、曖昧性、入れ子、主語省略、複数段落、計画変更、反実仮想

## 3 seed平均

| 条件 | No probe 精度/pair | Probe 精度/pair | Shuffle精度 | Probe候補数 |
|---|---:|---:|---:|---:|
| 既知 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 96.00 |
| 未知語 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 96.00 |
| 曖昧性 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 96.00 |
| 入れ子 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 96.00 |
| 主語省略 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 96.00 |
| 複数段落 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 96.00 |
| 計画変更 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 96.00 |
| 反実仮想 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 | 96.00 |

追加診断:

- Probe audit: **3456 / seed**
- 有効discrimination: **0**
- Boundary weight: **0**
- Local update: **0**
- モデルサイズ: **276374 bytes**
- 学習時間: **0.291 sec**
- 既知推論: **5.371 ms/example**
- 複数段落推論: **5.822 ms/example**
- 平均反復: **2.0**
- 最大反復: **2**
- 平均active状態: **24.0**
- 収束率: **1.0000**
- Peak RSS: **121564 KiB**（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Probe違反監査は3,456件だが正のnudgeは0

各seedで3,456候補を独立probe上で監査したが、probe outcomeを正しく再構成する境界候補が一件もなかった。したがって、正候補と誤候補を分離するdiscrimination、boundary weight、局所updateはすべて0だった。

> **独立probeは正候補と誤候補が候補集合に共存するときだけ選択情報になる。正候補が存在しなければnudged phaseは空である。**

### Candidate birthは維持されたが意味境界は0

全主要条件で96候補を生成でき、Cycle 028以前の空集合collapseは再発しなかった。しかしexact object-value pair recallは全条件0だった。

候補は長いcommand固有span、object/valueの部分文字列、助詞を含む区間、状態文の無関係な短区間に支配された。

### Correct probeとshuffleが同一

Correct probe方式とshuffled probe方式は全指標でno-probeと同一だった。これはprobe信号がノイズだったのではなく、正誤を比較できる候補pairが一件も形成されなかったためである。

### Junk attractorを安全棄権へ変えただけ

全条件でnull率1.0となった。候補は多数あるがenergy gapがほぼ0で、誤った安定点を選ばず棄権した。wrong commit 0は能力ではなく安全停止である。

## 収束・失敗分類

active集合を各sweepで`最小energy + 0.08`以内へ単調縮小し、最大6 sweepとした。実測は平均・最大とも2 sweepで有限停止し、発散は観測されなかった。

- **Boundary birth collapse**: 候補数96でも正しいtarget/value境界が0
- **Probe discrimination collapse**: 正候補がなく片側だけ成功する候補pair 0
- **Nudged phase collapse**: boundary weight / update 0
- **Flat landscape**: mean energy gapがほぼ0
- **Null safety degeneration**: 全面棄権
- **局所最適**: 確定前にtie停止
- **発散**: 未観測

仮説支持には、correct probeでのみ正の境界weightが形成され、no-probe/shuffleよりpair recallまたはexecution accuracyが改善する必要があった。すべて未達。

## Hopfield記憶・既存NNとの差

固定patternの保存・想起ではなく、入力ごとに境界候補を生成し、別入力の制約違反から局所energyをnudgeし、反復緩和で固定点を探索する点は単純Hopfield記憶と異なる。

一方、現在の候補は手続き的な文字区間置換で、正式な平衡伝播・学習された連続energy・意味constraint topologyには未到達。

## 資源量・計算量

- Candidate生成: `O(L^4)`、実装ではtarget/value各28、候補96へ疎制限
- Probe監査: `O(QH)`
- Relaxation: `O(SH)`
- `Q=36, H≤96, S≤6`
- 1GB未満: 達成（モデル約276374 bytes）
- 5ms未満: 未達（既知約5.37ms、長文約5.82ms）
- 弱いスマートフォンCPU実機: 未検証

## 系列E固有の進展

> **Probe-nudgingは境界選択の原理であり、境界birthの原理ではない。Split–mergeで候補集合を非空にしても、正しい局所operatorが候補内に入らなければ独立probe・平衡伝播・局所学習はすべて空になる。**

## 他系列へ返す知見

- A: Probe-grounded error cancellationは、probeへ転送可能なoperator familyが候補内にあることを先に確認すべき。
- B: Probe同値類でsymbolを作る前に、同値類内に少なくとも一つ外部成功programが必要。
- C: Mechanism familyは全候補が誤る場合、応答同値類を形成しても因果機構にならない。
- D: Read/write operator familyも、独立probeで実行可能な境界pairが0ならfast/slow creditへ進めない。

## 次の仮説

**Counterexample-Driven Boundary Expansion from Near-Miss Probe Residuals**  
（near-miss probe残差による反例駆動境界拡張）

次はprobeを候補選択だけに使わず、候補生成操作へ戻す。

1. Probe上の候補afterと正解afterの最小差分を、学習時だけnear-miss residualとして取得
2. 誤候補境界を差分方向へ1文字ずつexpand / contract / shift
3. 一回の編集でprobe violationが減る局所操作だけ保持
4. 同じ操作responseが複数probe・複数surfaceで再現する場合だけ境界生成operator化
5. Final test outcomeはrankingに使用しない
6. Correct probe / shuffled residual / no residualを比較
7. Free phaseで候補birth、nudged phaseでnear-miss residualに沿う局所forceを更新
8. 未知語・曖昧性・入れ子・主語省略・計画変更・反実仮想でpair recallとexecutionを評価
9. 候補数増加ではなく、正答候補への最短編集距離減少を主評価に追加

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機: **未検証**
- 完成: **未達**
