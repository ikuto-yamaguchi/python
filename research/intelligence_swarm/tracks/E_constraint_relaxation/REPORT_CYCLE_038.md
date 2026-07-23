# 系列E Cycle 038

## 仮説

**Intervention-Orthogonal Sensor Birth from Actively Synthesized Constraint Queries**  
（能動合成constraint queryによる介入直交sensor創発）

Cycle 037では5種類の受動sensorを分離したが、再利用可能な非加法synergy hyperedgeは0件だった。今回は既存episodeからsensorを受動抽出せず、候補state対の応答を最大限分割するvalue swap・object swap・object mask・構造摂動queryを合成し、候補分割数／query記述bitが高いqueryを選んだ。さらに候補correctness応答の絶対相関が0.35未満のqueryだけをsensor nodeへ昇格し、直交sensor間に限って3項hyperedgeを形成した。

Final testの`after / future`はcandidate生成・energy rankingに使用していない。

## 重複表

| 系列 | 最新中心 | Eで棄却・分離した領域 |
|---|---|---|
| A Cycle 038 | selective lesionとobject-target birth | 時間予測状態・carry |
| B Cycle 038 | active disagreement production birth | MDL・program帰納 |
| C Cycle 038 | paired-world object-support co-segmentation | 因果world transition |
| D Cycle 038 | active replay address synthesis | 長期memory・read/write閉路 |
| **E Cycle 038** | **候補分割queryから低共分散sensor nodeとenergy hyperedgeを生成** | 今回の固有対象 |

## 実装

- 最大12 prospective state候補
- 各probeから最大18 active query候補
- value swap、object swap、object mask、prefix/suffix摂動
- 期待候補分割pair数／query bitで上位5 queryを選択
- correctness応答の絶対相関 `< 0.35` をsensor直交条件とする
- 3 sensor同時正答をhigher-order hyperedge候補とする
- No energy／Random query／Active orthogonal／Shuffled outcomeを比較
- active集合単調縮小、最大8 sweep

固定ontology、手書きslot、分類器、辞書、テンプレート、RAG、外部LLMは使用していない。

## 3 seed平均

| 条件 | No energy | Random | Active orthogonal | Shuffle | Active null |
|---|---:|---:|---:|---:|---:|
| 既知 | 0 | 0 | 0 | 0 | 1.0000 |
| 未知語 | 0 | 0 | 0 | 0 | 1.0000 |
| 曖昧性 | 0 | 0 | 0 | 0 | 1.0000 |
| 入れ子 | 0 | 0 | 0 | 0 | 1.0000 |
| 主語省略 | 0 | 0 | 0 | 0 | 1.0000 |
| 複数段落 | 0 | 0 | 0 | 0 | 1.0000 |
| 計画変更 | 0 | 0 | 0 | 0 | 1.0000 |
| 反実仮想 | 0 | 0 | 0 | 0 | 1.0000 |

追加診断：

- Query audit：**204 / seed**
- Active orthogonal sensor：**0**
- Random sensor：**0**
- Shuffled sensor：**0**
- Active higher-order hyperedge：**0**
- Exact boundary recall：**全条件0**
- Object-value pair recall：**全条件0**
- 平均／最大反復：**2／2 sweep**
- 収束率：**1.0**

## 判定

**中核仮説は強く反証された。**

### 能動queryは生成できたがsensor birthが0

各seedで204件のqueryを監査し、候補分割効率の高いqueryを選択した。しかし、候補correctness応答が非定数で、かつ他sensorと絶対相関0.35未満となるqueryは一件も残らなかった。

Random、Active、Shuffledの全方式でsensor nodeとhigher-order hyperedgeは0件だった。

> **候補対の出力不一致を増やすqueryと、正誤を独立に識別するconstraint sensorは同じではない。**

現在の候補は相対位置・文字shape・置換幅を共有するため、value/object/構造摂動に対するcorrectness応答が全候補で同時に0、または強く共変した。

### Active queryはenergy landscapeを変えない

Sensorが0件なので、No energy、Random、Active、Shuffleは全条件で完全に同一だった。

- Execution accuracy：0
- Wrong commit：0
- Null率：1.0
- Active状態：12
- Exact boundary：0
- Pair recall：0

候補生成後の能動識別ではなく、paired worldを同時分節してqueryと候補nodeを共同生成する必要がある。

### 主語省略・計画変更・反実仮想

- Object permanence：未成立
- 長距離constraint：未成立
- 撤回goalと最終goalの分離：未成立
- 実行worldと非実行worldの分離：未成立
- 曖昧候補の並行固定点：未成立

## 反証条件と失敗分類

仮説支持には、Correct active queryでのみ低共分散sensorとhyperedgeが形成され、Random／Shuffleより正答固定点が増え、sensor lesionで対応固定点だけが崩れる必要があった。

結果：

- Active query synthesis：成立
- Candidate disagreement exposure：成立
- Orthogonal sensor birth：**崩壊**
- Hyperedge birth：**前提不成立**
- Semantic boundary：崩壊
- Flat landscape：全面tie/null
- Wrong attractor：安全閾値により未確定
- 発散：未観測

## 先行研究との位置づけ

Active constraint acquisitionは、疑わしいconstraintを壊すqueryや候補空間を分割するqueryにより、受動学習の過適合を減らせる。ただし候補変数・constraint language・query oracleが存在することを前提とする。今回の失敗点は、その前段にある生の日本語からの意味nodeと独立constraint channelの生成である。

Predictive coding／equilibrium propagationも反復energy最小化と局所更新を提供するが、内部状態・層・error channelは定義済みである。今回の方式は入力ごとにqueryとsensor候補を生成する点で異なるが、sensor topologyの創発には至らなかった。

## 資源量

- モデルサイズ：**3,917 bytes**
- 学習時間：**0.023003秒**
- Peak RSS：**111,808 KiB**（Python runtime込み）
- 推論時間：
  - 既知：**0.664 ms/example**
  - 複数段落：**0.877 ms/example**
  - 反実仮想：**0.982 ms/example**
- 推定計算量：
  - Candidate生成 `O(L^4)`、12候補へ制限
  - Query synthesis `O(Q)`
  - Disagreement `O(QH^2)`
  - Orthogonal selection `O(S^2H)`
  - Relaxation `O(RHS)`

1GB未満・小規模5ms未満は達成した。弱いスマートフォンCPU実機は未検証。

## 系列E固有の進展

> **受動sensorの相関問題を、能動queryによる候補分割へ置き換えても、候補correctness応答が全面定数または共変なら直交constraint nodeは生まれない。Queryを候補選別器として後付けせず、query worldと元worldを同時分節してconstraint node自体を共同生成する必要がある。**

## 他系列へ返す知見

- A：候補cell対の不一致最大化だけではobject sensor birthにならない。queryとstate cellの共同分節が必要。
- B：短いactive query grammarはproduction birthを保証しない。query-induced partitionとlatent productionを同時生成すべき。
- C：paired-world co-segmentationでobject/value/operationを一つのeventへ共同生成する方向は、Eのsensor birthにも必要。
- D：active replay queryはsurface addressを分割できてもsemantic addressを生成しない。paired replay worldの共同分節が必要。

## 次の仮説

**Co-Segmented Constraint Node Birth from Paired Query Worlds**  
（paired query world共同分節によるconstraint node創発）

1. 元episodeとactive query worldを同時に分節
2. 変化したcommand区間、state support、future traceを一つのlatent nodeから共同生成
3. Value-only、object-only、structure-onlyのpaired worldを別channel化
4. 各nodeが一つのpaired differenceを説明し、他channel差分を保存することを要求
5. Node間応答共分散が低い場合だけhyperedgeを許可
6. Factorized／co-segmented／shuffled pair／no-energyを比較
7. Node removalで対応constraintだけが崩れることを必須化
8. 曖昧性、主語省略、計画変更、反実仮想で複数固定点を評価

**高校生級知能：未達**  
**ネイティブ日本語コミュニケーション：未達**  
**弱いスマートフォン実機検証：未達**  
**完成：未達**
