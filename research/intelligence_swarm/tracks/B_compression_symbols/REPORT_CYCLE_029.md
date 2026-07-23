# 系列B Cycle 029 研究報告

## 仮説

**Cross-Input Discriminating Experiments from Program-Composed Probe States**  
（program合成probe stateによる入力横断識別実験）

Cycle 028では競合binding graph自身の出力内部からtestを作ったため、全候補が自己整合的に通過し、tieを解消できなかった。今回は学習episodeを70%のprogram induction partitionと30%のindependent probe partitionへ分離し、final testは別seedとした。

Probe partition上で同じ入力に異なるafterを生成するtriangle pairを抽出し、片方だけが観測afterを再構成した場合にpairwise preferenceを記録した。Final testのafter/futureはrankingへ使用していない。

## 先行研究整理

- Program Synthesis via Test-Time Transduction (2025) は、有限program仮説集合がtest入力上で異なる出力を返す点を利用し、選択入力のoutput oracleで候補を除外する。ただし有限仮説classと外部LLM oracleを持つ。
- Active Learning for Neurosymbolic Program Synthesis (2025) は、targeted queryで非同値programを分離し、残存programのobservational equivalenceを保証する。ただしDSL、neural component、user feedbackが定義済みである。
- CodeARC (2025) はhidden functionへ新入力をqueryし、differential testing feedbackでprogramを反復修正する。
- Sparse Transductive Guidance in Program Synthesis (2025/2026) は、transductive guidanceを常時使うとinductive synthesisを誤誘導し得るため、必要時だけ使う。

今回の課題は、生の日本語からprogram候補と識別実験の双方を形成する、さらに上流の問題である。

## 他4系列との重複表

| 系列 | 最新中心 | Bで分離した領域 |
|---|---|---|
| A | Operator-centered recurrent error cancellation | 談話予測状態・再帰更新 |
| C | Target-context mechanism adapter | 因果transition transport |
| D | Functional endpoint intervention kernel | 長期memory endpoint |
| E | Boundary split–merge candidate birth | Energy・attractor dynamics |
| **B** | **独立入力上のobservational disagreementによるprogram選択とMDL** | 今回の固有対象 |

## 実験条件

- seed: 1 / 7 / 19
- 288 episode / seed
- 70% induction / 30% independent probe
- final test: 別seed、24例 / split
- endpoint上限32、triangle上限64
- ablation: Graph / Probe / Shuffled Probe / Probe+MDL
- test: 既知、未知語順、未知語彙、Rename、別状態表現、入れ子、主語省略、複数段落
- Hidden object/field/value labelは評価器のみ
- 固定ontology、RAG、外部LLMはlearnerに不使用

## 3 seed平均

| 条件 | Graph 精度/commit | Probe 精度/commit | Shuffled 精度/commit | MDL 精度/commit |
|---|---:|---:|---:|---:|
| 既知 | 0 / 0 | **0.0694 / 0.0694** | 0 / 0 | **0.0694 / 0.0694** |
| 未知語順 | 0 / 0 | **0.0417 / 0.0417** | 0 / 0 | **0.0417 / 0.0417** |
| 未知語彙 | 0 / 0 | **0.0417 / 0.0417** | 0 / 0 | **0.0417 / 0.0417** |
| Rename | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 別状態表現 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 入れ子 | 0 / 0 | **0.0417 / 0.0417** | 0 / 0 | **0.0417 / 0.0417** |
| 主語省略 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 複数段落 | 0 / 0 | **0.0417 / 0.0417** | 0 / 0 | **0.0417 / 0.0417** |

追加診断:

- binding triangle: 64
- probe pair audit: 402.67
- probe discrimination: 153
- global preference: 97.67
- context preference: 114.67
- 既知平均競合出力: 8.61
- shuffled probe discrimination: 0
- MDL description: 24,664 bits

## 判定

**一般仮説としては反証。独立probeによる競合解除に、初めて小さいが再現可能な限定信号が出た。**

### 独立probeでexecution accuracyが0から増加

既知ではGraph baselineのaccuracy / commit率が0だったのに対し、Probe方式は0.0694まで増加し、wrong commitは0だった。未知語順・未知語彙・入れ子・複数段落でも0.0417の正答commitが生じた。

### Shuffled ablationでは信号消失

Probe outcomeを別episodeへ循環shuffleすると、probe discrimination、accuracy、commit率はいずれも0へ戻った。したがって限定改善はtriangle順序や一律score追加ではなく、inductionから分離した正しい観測差へ依存する。

### ただしsemantic generalizationではない

- Rename: 0
- 別状態表現: 0
- 主語省略: 0
- 既知pair recall: 0.0139

得られたのは少数のsurface-local triangle preferenceであり、object・relation・scope・operationの意味bindingではない。Probeは既存triangleのtieを部分的に解くが、欠けたprogram候補を新生しない。

> **独立観測はprogram選択には有効だが、program候補birthやsemantic bindingの代替にはならない。**

### MDL

Probe+MDLはProbe方式と同じ能力を保ち、description lengthを約283,045 bitsから24,664 bitsへ短縮した。今回は極小のexecution信号を保持して圧縮できたが、能力範囲が狭いため意味文法の証拠ではない。

## 反証条件

支持条件のうち、以下は達成した。

1. Probeとfinal testを分離したままGraphを上回る
2. Shuffled probeで改善が消える
3. Wrong commitを増やさない
4. Probe library込みMDLがliteralより短い

以下は未達だった。

5. Rename・別状態表現・主語省略へ転移
6. Pair boundaryとexecutionの双方を改善

よって一般的program induction仮説は反証、局所選択機構だけ限定支持とする。

## 探索爆発抑制・資源量

- endpoint: 32
- triangle: 64
- object候補: triangle当たり最大3
- value候補: triangle当たり最大6
- probe pair: 同じprobe入力で実行可能なtriangle pairのみ
- モデル: 8,812 bytes
- 学習: 0.3899 sec
- 推論: 既知4.77ms、入れ子8.20ms、複数段落17.41ms
- Peak RSS: 111,904 KiB（Python runtime込み）
- 計算量: candidate `O(NL²)`、triangle audit `O(NKoKv)`、probe audit `O(VT²)`、推論 `O(TL²+T²)`、`T≤64`

1GB未満は達成。長文5ms未満と弱いスマートフォンCPU実機は未達。

## 系列B固有の進展

> **Program自身の内部整合testではtieを解けなかったが、inductionから分離した別入力上の独立観測は、少数の競合triangleをwrong commitなしで識別できた。識別実験はprogram選択原理として機能する。ただし候補birthとsemantic bindingは別問題である。**

## 他系列へ返す知見

- A: 候補の自己整合性ではなく、別turnで異なる予測を生む独立観測がoperator選択に有効。
- C: Adapter候補間の出力差を独立target episodeで監査すると選択情報を得られる可能性がある。
- D: Endpoint必要性は同一episodeの再構成だけでなく、独立sessionのquery結果差で検証すべき。
- E: Energy tieは自己整合fieldだけでなく、候補ごとに異なる独立rollout観測で解く必要がある。

## 次の仮説

**Active Probe Grammar from Maximum Expected Program Elimination per Description Bit**  
（記述bit当たり期待program除外数を最大化する能動probe文法）

1. 競合triangle集合を入力ごとに構成
2. 各triangle pairが異なる出力を返す最小before/command editを生成
3. Probe記述長と予想分割比を計測
4. `expected eliminated programs / probe bits`を最大化
5. 観測済みepisodeに近いprobeだけ実行可能候補として保持
6. 観測不能probeはunknownとして保持
7. 少数probeでrelation/scope同値類を分割
8. Probe grammarとprogram libraryの共同MDLを最小化
9. Rename・別状態表現・主語省略でcandidate birthも評価

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
