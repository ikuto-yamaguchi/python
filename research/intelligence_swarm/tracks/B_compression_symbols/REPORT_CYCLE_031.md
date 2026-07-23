# 系列B Cycle 031 研究報告

## 仮説

**Probe-Conditioned Symbol Birth from Minimal Equivalence-Class Splits**  
（最小同値類分割からのprobe条件付き記号創発）

Cycle 030では独立probeを25件から16件へ圧縮し、極小のexecution信号を維持できた。しかしprobeは既存surface-local triangleの選択にしか使われず、記号・変数・program候補のbirthには至らなかった。

今回は各binding triangleを、inductionから分離したactive probe集合に対する三値応答列へ写像した。

- `+1`: probe outcomeを正しく生成
- `-1`: 実行できるが誤ったoutcome
- `0`: 実行不能

具体的なobject/value文字列ではなく、probe応答列と局所state-change consequenceが同じtriangle群を匿名symbol classへ統合した。Singletonは再利用可能記号とみなさず棄却した。

## 先行研究整理

Program Synthesis via Test-Time Transductionは、program出力で有限仮説集合を分割し、少数queryで候補を除外する。ただしprogram classと外部LLM oracleは事前に与えられる。Active Learning for Neurosymbolic Program Synthesisも、targeted feedbackで残存programを観測同値へ絞るが、DSL・neural component・user feedbackを持つ。

Metric Program Synthesisは観測同値を距離に緩和し、近似同値類を圧縮してrepairする。近年のbisimulation研究も、同じ将来応答を持つ状態の表現統合を扱うが、state/action/rewardの構造は既知である。

今回の課題は、生の日本語から生成された候補programを独立probe応答で同値類化し、その同値類自体を匿名記号として再利用できるかである。

## 他4系列との重複回避

| 系列 | 最新中心 | Bで棄却・分離した領域 |
|---|---|---|
| A | Probe-grounded operator birth | 時間予測状態・再帰誤差相殺 |
| C | Intervention-equivalence mechanism family | 因果world transition |
| D | Probe-grounded read/write operator birth | 長期memory・再固定化 |
| E | Counterexample-driven boundary expansion | Energy・attractor・境界力学 |
| **B** | **Probe応答同値類の匿名記号化・共同MDL** | 今回の固有対象 |

構造的にはCのmechanism familyに近いが、Cは因果介入結果とworld transitionを基準にする。Bはprogram実行応答、再利用、圧縮利得、共同記述長を採否基準とする。

## 実装

- 固定ontology、手書きslot、辞書、RAG、外部LLMなし
- 288 episodeを190 induction / 98 independent probeへ分離
- Final testは別seed
- Active probe上限16件
- Triangleごとの三値response vector
- State-change consequenceとresponse vectorによる同値類
- 2 member以上のみanonymous symbol化
- Graph / Probe / Symbol / Shuffled-symbol比較
- Final test outcomeはrankingへ不使用

## 3 seed平均

| 条件 | Graph | Probe | Symbol | Shuffled symbol |
|---|---:|---:|---:|---:|
| 既知 | 0.0139 | 0.0694 | **0.0972** | 0.0278 |
| 未知語順 | 0.0139 | 0.0417 | **0.0833** | 0 |
| 未知語彙 | 0.0139 | 0.0417 | **0.0833** | 0 |
| Rename | 0 | 0 | 0 | 0 |
| 別状態表現 | 0 | 0 | 0 | 0 |
| 入れ子 | 0.0139 | 0.0417 | **0.0833** | 0 |
| 主語省略 | 0 | 0 | 0 | 0 |
| 複数段落 | 0.0139 | 0.0417 | **0.0833** | 0 |

追加診断:

- Binding triangle: 64
- Active probe: 13.67
- Probe discrimination: 126
- Anonymous symbol class: 16.67
- Symbol member: 56.33
- Symbol description: 26,522 bits
- Probe-only description: 24,861 bits
- Literal baseline: 283,507 bits
- Model: 8,570 bytes
- Training: 0.505138 sec
- Inference: seen 8.637ms / nested 12.939ms / paragraph 23.328ms
- Peak RSS: 160,256 KiB（Python runtime込み）

## 判定

**一般的な記号創発仮説としては反証。局所的なprobe応答記号によるprogram選択には限定支持。**

### 独立probe応答同値類でaccuracyが増加

既知ではProbe 0.0694からSymbol 0.0972、未知語順・未知語彙・入れ子・複数段落では0.0417から0.0833へ増加した。Wrong commitは全条件0だった。

Seed別には、既知でseed 1のみ0→0.0833、seed 7/19はProbeと同値だった。未知語順・未知語彙・入れ子・複数段落ではseed 1と19に増分、seed 7は同値だった。全seedで一様な増分ではないため、強い支持とはしない。

### Shuffled symbolで信号が低下

Symbol class間のprobe preferenceを反転すると、既知0.0278、未知語順・未知語彙・入れ子・複数段落0へ低下した。改善はclass数や再利用priorだけでなく、独立probeで観測した応答方向に依存する。

### 記号classは形成されたがsemanticではない

平均16.67 class、56.33 triangle memberが形成された。Singletonを除外しているため、形式上は複数programを再利用可能な匿名symbolへまとめた。

しかし、このsymbolは意味変数ではなく、同じtraining surface family上の外部応答同値類である。

### Rename・別状態表現・主語省略は0

- Rename accuracy / pair recall: 0 / 0
- 別状態表現: candidate 0
- 主語省略: accuracy / pair recall 0 / 0

Object identity、relation、scope、談話継続を跨ぐsymbolではない。

### Pair recallが改善していない

既知pair recallはProbe 0.0556からSymbol 0.0417へ低下した。未知語順・未知語彙でも低下した。

Execution accuracy増加は、正しいobject/value境界が増えた結果ではなく、既存surface-local after候補のtieをsymbol preferenceで解いた結果である。

> **Probe応答同値類は局所program選択を改善できるが、semantic symbol birthやopen-form variable bindingの証拠にはならない。**

### MDL評価

- Probe-only: 24,861 bits
- Symbol: 26,522 bits
- Symbol overhead: 1,661 bits
- Literal baseline比: 約90.6%短縮

Symbol metadataはProbe-onlyより約6.7%増えた。小さなaccuracy増加はあるが、Probe-onlyより短くはない。したがって「記号化が追加圧縮を生む」という仮説は未支持である。

## 反証条件

仮説を強く支持するには次が必要だった。

1. 複数seedでSymbolがProbeを一貫して上回る
2. Rename・別状態表現へ同じsymbol classが転移
3. 主語省略で前turn symbolを再起動
4. Exact pair recallまたはexecution candidate birthが増加
5. Symbol metadata込みMDLがProbe-onlyより短くなる
6. Shuffled probeで信号が消える

今回は6と局所accuracy増分のみ成立し、2〜5は未達。

## 探索爆発抑制

- Endpoint上限32
- Triangle上限64
- Active probe上限16
- Response vectorは三値で固定長
- Symbol classはhash grouping `O(TV log T)`
- Singleton classを棄却
- 推論候補はtriangleごとobject最大4、value最大8

推定計算量:

- Triangle induction `O(NKₒKᵥ)`
- Probe response `O(VT)`
- Equivalence grouping `O(TV log T)`
- Inference `O(TL² + T²)`
- `T≤64, V≤16`

## 資源量

1GB未満は達成した。既知推論は8.64msで5msを超え、複数段落は23.33msだった。弱いスマートフォンCPUでの速度条件と実機検証は未達。

## 系列B固有の進展

> **独立probe応答でprogramを匿名同値類へまとめると、少数のsurface-local execution tieをwrong commitなしで追加解消できる。しかしclassはsemantic variableを表さず、追加MDL overheadも回収できない。**

## 他系列へ返す知見

- A: probe-grounded operatorを同値類化する場合、execution応答増分だけでなく主語省略carryと時間的再起動を別評価すべき。
- C: intervention-equivalence familyが多数形成されても、未知表記へのtransferとtarget境界recallが増えなければ因果変数ではない。
- D: read/write consequence classはslow化前にRename transferとlatest-value address精度を要求すべき。
- E: probe応答同値類は候補選択に使えるが、正しい境界birthやnudged candidate生成の代替にはならない。

## 次の仮説

**Probe-Driven Symbol Refinement by Counterexample Boundary Repair**  
（反例境界修復によるprobe駆動記号精錬）

次は既存triangleを同値類化するだけでなく、同値類内のnear-miss programを修復する。

1. Symbol class内でprobe outcomeに最も近いwrong programを抽出
2. Predicted afterとprobe afterの最小差分を学習時だけ計測
3. Object/value/endpoint境界をexpand・contract・shiftする修復operatorを生成
4. 複数probeで同じ修復が成功した場合だけsymbol production rule化
5. Correct probe / shuffled probe / no repairを比較
6. Final test outcomeはrepair・rankingに使わない
7. Rename・別状態表現で新しいbinding候補が生まれるか評価
8. Symbol library + repair grammar + probe grammarの共同MDLを最小化
9. Pair recallとexecution accuracyが同時に上がらなければ棄却

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
