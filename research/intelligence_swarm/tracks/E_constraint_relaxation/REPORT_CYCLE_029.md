# 系列E Cycle 029 研究報告

## 仮説

**Generative Candidate Birth from Energy-Lowering Boundary Split–Merge Dynamics**  
（energy低下型境界split–merge力学による生成的candidate birth）

Cycle 028では、`before + command`だけから複数after rolloutを生成し、その自己整合不一致をenergy fieldへ変換した。しかし固定edit prototypeがheld-out入力へ適用できず、主要条件で候補集合が空になった。

今回は既存edit prototypeの実行可能性をcandidate birthの前提から外し、文字列境界そのものを可変状態とした。

- 初期状態: 文字種・句読点による粗い境界
- 局所操作: split / merge / 1文字shift
- 疎探索: beam 18、最大5 sweep
- Candidate birth: beam内で支持された境界対からspanを生成
- Binding候補: before/command共通span、command固有span、before固有span
- Prospective state: before内target候補をcommand側value候補へ置換
- Energy: non-target保存、command coverage、置換shape差、境界population support、局所boundary/role credit
- Relaxation: 最小energy+0.05以内へactive集合を単調縮小、最大6 sweep

推論時に`after / future`は使用しない。固定ontology、手書きslot、辞書、RAG、外部LLMは使用しない。

## 先行研究整理

- Sander et al. (ICML 2025), *Joint Learning of Energy-based Models and their Partition Function* は、組合せ的に大きい離散空間でenergy modelとpartition functionを共同学習するmin-min formulationを提案するが、構造空間と特徴表現は与えられる。
- Dai et al., *Learning Discrete Energy-based Models via Auxiliary-variable Local Exploration* は、離散構造上の局所探索samplerを学習しprogram synthesis等でenergy-guided explorationを示すが、探索状態の意味境界は既定である。
- 2025–2026年のEquilibrium Propagation拡張はLagrangian・散逸力学・非対称結合に対する局所学習と収束条件を扱うが、node・境界・energy topologyは設計済みである。

今回の課題は、生の日本語から境界・node・binding候補をenergy dynamics自身で生む、さらに上流の問題である。

## 他系列との重複表

| 系列 | 最新中心 | Eで棄却・分離した領域 |
|---|---|---|
| A | Operator中心の反復prediction-error相殺 | 談話状態・時間方向route |
| B | 独立probeによるprogram選択 | MDL・program grammar |
| C | Target境界競合によるmechanism transport | 因果transition・world graph |
| D | 介入応答kernelによるmemory endpoint | 長期記憶・再固定化 |
| **E** | **境界split–merge・候補birth・energy固定点** | 今回の固有対象 |

Cもtarget境界を扱うが、Cはsource mechanismの因果transportを判定基準とする。Eはsource ruleを前提にせず、境界とbindingを同一energy landscape上で生成・消滅させる。

## 実験条件

- seed: 1 / 7 / 19
- train: 既知96 + Rename48 / seed
- test: 36例 / split / seed
- ablation: Fixed boundary / Unlearned split–merge / Learned split–merge
- test: 既知、未知語、曖昧性、入れ子、主語省略、複数段落、計画変更、反実仮想
- Hidden object/valueは評価器だけに使用

## 3 seed平均

| 条件 | Fixed精度 / 候補数 | Split–merge精度 / 候補数 | Learned精度 / 候補数 | Learned null率 |
|---|---:|---:|---:|---:|
| 既知 | 0 / 0 | 0 / 64.00 | 0 / 64.00 | 1.0000 |
| 未知語 | 0 / 0 | 0 / 64.00 | 0 / 64.00 | 1.0000 |
| 曖昧性 | 0 / 0 | 0 / 64.00 | 0 / 64.00 | 1.0000 |
| 入れ子 | 0 / 43.24 | 0 / 64.00 | 0 / 64.00 | 0.8241 |
| 主語省略 | 0 / 0 | 0 / 0 | 0 / 0 | 1.0000 |
| 複数段落 | 0 / 0 | 0 / 0 | 0 / 0 | 1.0000 |
| 計画変更 | 0 / 0 | 0 / 43.85 | 0 / 43.85 | 1.0000 |
| 反実仮想 | 0 / 0 | 0 / 48.59 | 0 / 48.59 | 1.0000 |

追加診断:

- Learned boundary weight: 0
- Learned role weight: 0
- Local update: 0
- モデルサイズ: Fixed 180 / Split–merge 184 / Learned 182 bytes
- 学習時間: Split–merge 2.497 sec / Learned 2.330 sec
- Learned推論: 既知 8.442 ms/example、複数段落 37.113 ms/example
- Peak RSS: 168,448 KiB（Python runtime込み）
- 入れ子wrong commit: 0.1759

## 判定

**中核仮説は強く反証された。Boundary dynamicsは候補集合を非空にしたが、意味境界・実行可能binding・局所学習を形成しなかった。**

### Candidate birthだけは発生

Fixed boundaryでは主要条件の候補数が0だった。Split–mergeを導入すると、既知・未知語・曖昧性で平均64候補、計画変更で43.85候補、反実仮想で48.59候補まで増えた。

Cycle 028の「候補集合が空でenergy dynamicsを開始できない」状態からは脱した。境界のbirth/death操作は候補生成器として機能した。

### しかし正答境界は残らない

全splitでpair recallとexecution accuracyは0だった。生成候補はobject/valueの部分span、助詞・句読点を含む境界、before内の無関係な短区間、長文前置きの断片に支配された。

> **候補数を増やすことと、意味境界を生むことは別である。**

### Local learningは0 update

Training episodeでも、生成上位64候補内に正しいafterを再構成する候補が一件も入らなかった。そのためfree/nudged差分を計算できず、boundary weight、role weight、updateはすべて0となった。Learned方式はUnlearned方式と完全同一である。

### 入れ子でjunk attractor

入れ子条件ではSplit–merge方式が候補を生成し一部を確定したが、accuracy 0、wrong commit 0.1759だった。候補が空ではなくなったことでsurface断片からなるjunk attractorへ収束した。

### 停止条件

Active集合は各sweepで単調に縮小し、固定点または最大6 sweepで有限停止する。実測最大sweepは2で、発散は観測されなかった。

## 失敗分類

- 境界候補崩壊: 候補は多数あるが正しいobject/value/target境界が上位集合外
- Binding崩壊: 境界候補間の役割結合が形成されない
- Nudged phase崩壊: 正答candidateがなく局所weight更新0
- Junk attractor: 入れ子で誤候補へ安定収束
- Null安全停止: 多数条件で同点候補を棄権
- 発散: 未観測

仮説支持には、Split–mergeがFixedよりpair recall・accuracyを改善し、Learned方式で正の局所updateが生じ、未知語・計画変更・反実仮想へ転移する必要があった。すべて未達。

## Hopfield記憶・既存NNとの差

固定patternを保存・想起するのではなく、境界状態を生成し、split/merge/shiftで離散構造を探索し、境界対から候補をbirthし、prospective afterを構成し、energyで競合し、free/nudged局所差分でboundary creditを更新する設計である。

ただし現状は手続き的離散探索で、正式な連続energy network・平衡伝播・意味constraint topologyには未到達。

## 資源量・計算量

- Initial segmentation `O(L)`
- Split–merge beam `O(SBL)`
- Candidate binding `O(B²OVT)`
- Relaxation `O(RH)`
- `S≤5, B≤18, H≤64, R≤6`
- 1GB未満: 達成
- 短文5ms目標: 未達（既知約8.44ms）
- 複数段落: 約37.11ms
- 弱いスマートフォンCPU実機: 未検証

## 系列E固有の進展

> **境界split–mergeはcandidate collapseを空集合から多数のsurface候補へ移した。しかしenergy低下だけでは意味境界を選べず、正候補がnudged phaseへ届かない。次に必要なのは候補数を増やすことではなく、独立観測で境界候補を能動的に分割する制約である。**

## 他系列へ返す知見

- A: Operator候補を大量生成しても、正operatorが上位集合へ残らなければerror-cancellation学習は開始できない。
- B: 独立probeは既存program選択に限定信号があるため、境界candidate birthにもprobe outcomeを直接使う価値がある。
- C: Target全境界へのsource mechanism適用では候補爆発とjunk attractorを監視し、独立witnessで境界を絞る必要がある。
- D: Functional endpoint kernel前に大量spanを生成するだけではsurface endpointが増える。独立sessionのread差を境界birthへ使う必要がある。

## 次の仮説

**Probe-Nudged Boundary Attractors from Independent Cross-Input Constraint Violations**  
（独立入力の制約違反でnudgeされる境界アトラクタ）

1. 境界候補ごとに別入力へ転送可能な最小局所operatorを構成
2. Inductionと分離したprobe episodeで各operatorのnon-target保存・inverse復元を監査
3. Probe上で一方だけ違反する境界pairへnegative local force
4. Probe outcomeを使ったnudged phaseで境界weightを直接更新
5. Final test outcomeはrankingへ使用しない
6. `expected eliminated boundary candidates / probe bits`でprobeを疎選択
7. Probeなし・shuffle probe・正probeを比較
8. 未知語・曖昧性・主語省略・計画変更・反実仮想でcandidate recallとexecution accuracyを評価
9. Probe boundary grammarとenergy weightの共同容量を測定

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機: **未検証**
- 完成: **未達**
