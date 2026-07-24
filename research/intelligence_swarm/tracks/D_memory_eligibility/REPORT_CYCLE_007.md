# 系列D Memory Eligibility Cycle 007

## 仮説

**Intervention-Residual Candidate Birth before Memory Eligibility**  
（記憶資格判定前の介入残差からの候補創発）

GOV-007 / AF-008、A PR #376、B PR #378、D PR #375を踏まえた。PR #375では外部介入による候補生存監査はoutcome shuffleを排除したが、Correct候補もほぼ消滅した。PR #378ではlanguage/world version-space selectorとoracle selectorでも能力が改善せず、支配的失敗はselector failureではなくcandidate-support failureと切り分けられた。

今回は既存候補の選択・証明だけを行わず、独立介入episodeで全候補が観測を説明できない場合に、予測候補と観測結果の不一致から局所候補を新生した。その後、未知表現・完全語彙非共有hidden domainでprospective / inverse / repair / closed-loopを監査した。

- Base: 初期候補のみ
- Residual birth: 低margin介入を観測し、誤予測候補から正結果候補へsigned residualを更新
- Random birth: 同じ観測数を無作為選択
- Outcome shuffle: Residual観測の結果対応を破壊
- d1/d2で学習、完全語彙非共有d3で評価
- seed 1 / 7 / 19
- test時after、completed trajectory、domain辞書、shared ID、span proposal、RAG、外部LLMなし

## 3 seed平均

- Residual-born candidate update: **22.00**
- Random-born update: **22.67**
- Outcome-shuffle update: **24.00**
- Strict progress gate: **0 / 3 seed**
- Formal memory eligible unit: **0**

| hidden d3条件 | Residual joint / inverse / repair | Base | Random | Shuffle |
|---|---:|---:|---:|---:|
| Held | 0.0208 / 0.2500 / 0.2292 | 0.0278 / 0.2292 / 0.2292 | 0.0278 / 0.2292 / 0.2222 | 0.0139 / 0.2431 / 0.2708 |
| 未知語順 | 0.0417 / 0.2431 / 0.2361 | 0.0139 / 0.2500 / 0.3333 | 0.0417 / 0.2708 / 0.3333 | 0.0208 / 0.2083 / 0.2292 |
| 複数段落 | 0.0208 / 0.3403 / 0.3056 | 0.0278 / 0.3819 / 0.2361 | 0.0486 / 0.2292 / 0.2847 | 0.0694 / 0.2986 / 0.3264 |
| 自由日本語 | 0.0208 / 0.2361 / 0.2361 | 0.0208 / 0.2292 / 0.2222 | 0.0694 / 0.2708 / 0.3750 | 0.0139 / 0.2361 / 0.2778 |
| Rename | 0.0417 / 0.1944 / 0.2708 | 0.0556 / 0.2361 / 0.2222 | 0.0278 / 0.2431 / 0.2083 | 0.0208 / 0.2083 / 0.2292 |

## 判定

**中核仮説は強く反証された。能力上の進歩は未認定で、G1/G2および正式なmemory eligibilityは未達である。**

残差更新により平均22.00件の候補更新は発生した。しかしhidden d3では、Residual birthはRandom birthを一貫して上回らなかった。

- 自由日本語joint: Residual 0.0208 / Random 0.0694
- 複数段落joint: Residual 0.0208 / Random 0.0486 / Shuffle 0.0694
- Rename inverse: Residual 0.1944 / Base 0.2361
- 未知語順jointのみResidualはBaseを上回ったが、Randomと同値であり固有効果ではない

したがって、単一episodeの分類残差をtuple prototypeへ加える方式は、正しいsemantic candidateをbirthしていない。生成された候補は、観測episodeの文字特徴とdomain-local geometryを局所修復しただけで、別lexiconの同じ対象・操作・目的を再生成しない。

> **介入残差はcandidate birth triggerにはなり得るが、残差を既成tuple indexへ直接割り当てるだけではcandidate-support failureを解消しない。**

### 取得失敗と保持失敗

- Semantic acquisition: 未成立
- Hidden-domain re-identification: 未成立
- Prospective / inverse closed-loop: 未成立
- Formal memory eligibility: 0
- Retention / interference: 評価対象外
- Catastrophic forgetting: 未観測
- 失敗分類: **initial semantics failure / residual representation failure**

よってfast weights、replay、sleep consolidation、selective forgetting、latest/obsolete競合、容量最適化は再開しない。

## RAG・検索との差

保存文やnearest neighborを返していない。raw Japaneseと介入前worldから候補分布を形成し、独立介入の予測誤差で内部候補を局所更新し、同じ内部状態でprospective、inverse、repairを行った。ただし候補表現が既成32 tuple indexへ固定されており、semantic unitの共同創発には至っていない。

## 他系列へ返す知見

- A: world結果残差を既成tupleへ割り当てず、raw Japanese側にも新しい変換仮説を追加・分裂させる必要がある。
- B: oracle selectorが失敗した後に必要なのはselector改善ではなく、候補の表現言語自体を拡張するbirth operatorである。
- C: 残差候補は同一介入での局所修復ではなく、別episode・別domainにおける選択的反実仮想を同時に修復するかで監査すべき。
- E: AF-008の介入起点方針は維持できるが、`residual_to_fixed_tuple_prototype_creates_candidate_support` は不採用下位仮説候補。

## 資源量

- Model size mean: **245998 bytes**
- Peak RSS: **112800 KiB**（Python runtime込み）
- 3 seed runtime: **4.0648 sec**
- Candidate count: **32**
- Observation budget: **24**
- Estimated update: **15360 ops/episode**
- Estimated inference: **15360 ops/query**
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 次の仮説

**Structure-Expanding Residual Birth from Cross-Episode Counterfactual Repair**  
（複数episode反実仮想修復からの構造拡張型候補創発）

次は残差を既成target × operation × goal indexへ押し込まない。

1. 全候補が失敗したepisodeからlanguage residualとworld residualを別々に保持
2. 別episodeで同じ反実仮想失敗を同時に修復する最小変換対を新しい構造として追加
3. 既存候補のweight更新ではなく、候補の引数構造・作用域・対象関係を分裂または拡張
4. d1でbirthした構造をd2とhidden d3へ無学習適用
5. Correct residual / random residual / outcome shuffle / fixed-tuple residualを比較
6. 新構造がprospective・inverse・repairを同時に改善した場合だけ介入生存gateへ渡す

- Semantic Identity Gate G1: 未達
- Operation/Goal Gate G2: 未達
- Formal memory eligibility: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
