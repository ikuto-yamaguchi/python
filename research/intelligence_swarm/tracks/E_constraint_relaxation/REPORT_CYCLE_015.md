# 系列E Cycle 015 研究報告

## 仮説

**Self-Induced Residual Cause Nodes by Minimal Edge Surgery**  
（最小edge surgeryによる残差原因node自己誘導）

Cycle 014では、candidate edge nodeとresidual cause nodeの二部graphにより、手書きのcause→edge routing下で既知精度0.9778を得た。しかし reconstruction→value、inverse→direction などの対応を実験側が供給しており、残差原因の創発ではなかった。

本Cycleでは各候補edgeを一つずつ反転し、残差vectorの有限差分signatureを測定した。同じsignatureを持つ残差とedgeを二部接続し、手書きroutingを廃止できるか検証した。

## 先行研究整理

2025年のscore-based causal representation learningは、一般変換下の潜在因果変数同定に介入coverageが必要で、一般変換では各nodeへの複数介入が十分条件になることを示す。AISTATS 2025の一般環境下CRLも、単なる環境差ではなく十分なmechanism change条件が必要とする。2026年の有限sample研究は未知介入targetを復元できる条件を解析するが、いずれも観測空間と介入環境が定義済みであり、生の日本語からedge候補を作る問題は残る。

## 他系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | E候補との区別 |
|---|---|---|---|---|
| A | 反実仮想outcome active probe | marked seen 1.0、誤確定0 | unmarked候補生成0、probe channel手書き | 外部観測policyは棄却 |
| B | destruction-vector e-graph | executable seen 0.6222 | quotient 0.1778、未知形式0 | program商形成は棄却 |
| C | identity-selective intervention partition | 既知形式1.0 | non-target ablation差0、未知形式0 | object world modelは棄却 |
| D | bidirectional query-write address | 軽量node実装 | seen write 0.0201、read 0、過剰統合 | 長期memory addressは棄却 |
| E | edge surgeryからcause routing自己誘導 | 今回検証 | candidate proposal、実世界cause | 系列固有 |

継承知見:
- A: outcome partitionは候補が既に存在する下流でのみ機能する。
- B: 同じ有限差分vectorを持っても同じroleとは限らない。
- C: non-target保存が候補classを分割しなければ因果情報は増えない。
- D: write/readを同じnodeに入れるだけではaddressにならない。

## 実験

- seed: 1 / 7 / 19
- 例数: 60 / 180 / 360
- candidate edge: target / value / direction / scope / address
- residual: reconstruction / preservation / inverse / revision / recall
- candidate上限: 16
- sweep上限: 4
- 比較:
  1. Global residual
  2. Shuffled routing
  3. Oracle routing
  4. Self-induced surgery routing
- 条件: 既知、曖昧性、入れ子proxy、反実仮想proxy、計画変更proxy、長距離distractor、noise、引用なし

## 最大360例・3 seed平均

| 条件 | Global | Shuffled | Oracle | Self-induced |
|---|---:|---:|---:|---:|
| seen | 0.7907 | 0.7944 | 0.8046 | **0.8102** |
| ambiguous | 0.5481 | 0.5593 | 0.5713 | **0.5639** |
| nested | 0.6093 | 0.6324 | 0.6352 | **0.6296** |
| counterfactual | 0.8213 | 0.8000 | 0.8259 | **0.8250** |
| plan | 0.4389 | 0.4509 | 0.4481 | **0.4565** |
| long | 0.6046 | 0.6472 | 0.6380 | **0.6481** |
| noise | 0.3796 | 0.4259 | 0.4389 | **0.4435** |
| unmarked | 0.0000 | 0.0000 | 0.0000 | **0.0000** |

## 限定的に支持された部分

Self-induced routingは、既知条件でoracle 0.8046に対し0.8102、noise条件でoracle 0.4389に対し0.4435だった。有限差分から復元したrouting mapの完全一致率は通常条件で1.0、noise条件でも0.9991だった。

したがって、**候補edge surgeryが残差成分へ選択的な有限差分を生む制御環境では、手書きcause→edge mapを局所介入から再構成できる**という下流部品には信号がある。

## 決定的な反証

**中核仮説は反証。**

### 1. Oracleに対する意味のある優位がない

Self-inducedはoracleとほぼ同等だが、global・shuffledとの差も小さい。既知ではglobal 0.7907、self 0.8102に過ぎず、cause routingが能力の支配要因ではない。

### 2. Cause nodeは実験器の残差basisを復元しただけ

residual channel自体が reconstruction / preserve / inverse / revision / recall として手で定義されている。自己誘導したのはchannelとedgeの対応であり、残差原因概念そのものではない。

### 3. Edge候補も固定ontology

target / value / direction / scope / address のedge種別を実験側が供給した。生の日本語から対象・値・scope・memory addressを生成していない。

### 4. 引用なしcandidate recallは0

unmarked条件では全方式accuracy 0。正答候補が集合外のため、surgery routingは何も救えない。

### 5. 有限差分評価が高コスト

Self-inducedは1例平均約79回のfactor評価を必要とした。候補16、edge5、residual5の小規模制御条件では軽いが、自由日本語の候補爆発下では `O(HER)` がボトルネックになる。

### 6. 自然言語統合ではない

入れ子・反実仮想・計画変更はbit graph proxyであり、主語省略、複数段落、自然な撤回、目的・制約・因果計画を理解した証拠ではない。

### 7. 平衡伝播は未成立

局所有限差分と反復選択を実装したが、free phase / nudged phaseの相関差によるweight更新ではない。

## 停止条件と失敗分類

- 一意停止: active candidateが1
- 平坦停止: sweep間でactive集合が変わらず複数候補
- 発散: 4 sweepで安定しない
- 局所最適: 一意候補だが誤答
- 候補崩壊: 正答候補が集合外
- cause崩壊: surgery signatureが残差channelを識別しない

今回の主失敗は候補崩壊と、固定された残差・edge ontologyへの依存。

## 資源量

- model: 144 bytes
- Peak RSS: 111176 KiB（Python runtime込み）
- candidate: 最大16
- edge: 5
- residual: 5
- sweep: 最大4
- self-induced factor evaluations: seen 79.0/例
- 推定計算量: proposal `O(L²)`、surgery `O(HER)`、relaxation `O(SHR)`
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 系列E固有の進展

必要条件を10段階へ更新する。

1. Candidate recall
2. Outcome non-isomorphism
3. Local factor separability
4. Factor minimality
5. Reality calibration / null
6. Adaptive factor中の絶対残差校正
7. Residual identifiability
8. Residual-cause-to-edge routing
9. **Cause/edge basis self-generation**
10. Attractor relaxation・局所学習

本Cycleは第9段階のうち「既知basis間の対応回復」を限定支持した。しかしbasis自体の生成は未成立。

## 他系列へ返す新知見

- A: probe program自己生成では、固定outcome channel間の対応回復とoutcome channel自体の生成を分けて評価する。
- B: rank-increasing介入basisも、固定edge ontologyのrankを増やしただけではrole創発にならない。
- C: identity basis発見ではobject候補spanと介入残差basisの双方をopen-set生成する必要がある。
- D: object/relation traceを固定軸として与えると、双方向address発見ではなく軸対応学習に留まる。

## 次の仮説

**Open-Basis Residual Discovery from Raw Outcome Compression**  
（raw outcome圧縮からの開放残差basis発見）

次は residual channel名とedge種別を廃止する。

1. raw before / candidate execution / after / future observationの文字差分を取得
2. 差分を固定カテゴリへ割り当てず、cross-episodeで再現する局所変化patternへ圧縮
3. candidate spanの削除・反転・再束縛が、どのraw差分patternを変えるか二部graph化
4. rankと再現性を増やすpatternだけをcause basisへ昇格
5. basisで説明できない残差はunknown-causeへ保持

最低成功条件:
- 固定residual名・固定edge名なし
- oracle routingの80%以上
- unmarked candidate recallを0から改善
- cause basis 3～12
- candidate 16以下
- sweep 4以下
- 32KB以下
- 5ms/example以下

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
