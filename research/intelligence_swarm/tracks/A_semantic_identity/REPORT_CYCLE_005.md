# 系列A Semantic Identity Cycle 005

## 仮説

**Jointly Emergent Language–World Intervention Diagrams from Paired Change Commutators**  
（対になった変化交換子からの言語―世界介入図式の共同創発）

GOV-006 / AF-007に従い、結果codebook、identity/operation/goal channel、span候補を先に構成せず、raw Japanese全体の変化とraw world geometryの変化を同時に低rank化した。言語変換とworld変換が同じ潜在方向を持つ場合だけ、介入図式候補としてtarget × move × goalをrankした。

- 学習domain: d1 / d2
- 完全語彙非共有の隠しdomain: d3
- raw Japaneseのpaired change
- raw pre-treatment world geometryとhypothetical intervention change
- SVDによるjoint change operator生成
- Correct / language-change shuffle / world-change shuffle
- seed 1 / 7 / 19
- test時after、完成trajectory、固定factor label、結果codebook、domain辞書、shared ID、RAG、外部LLMなし

## 主要結果

Joint chanceは1/64 = 0.015625。ただし本最小実装は各条件8例/seedの探索的監査であり、差0.125は1例相当なので統計的確証には使わない。

| Domain / 条件 | Correct joint | Language shuffle | World shuffle |
|---|---:|---:|---:|
| d1 held | 0.0000 | 0.0000 | 0.0417 |
| d1 free | 0.0000 | 0.0000 | 0.0000 |
| d2 held | 0.0417 | 0.0000 | 0.0000 |
| d2 free | 0.0000 | 0.0833 | 0.0417 |
| d3 held | 0.0417 | 0.0000 | 0.0000 |
| d3 free | 0.0000 | 0.0000 | 0.0417 |
| d3 paragraph | 0.0417 | 0.0417 | 0.0000 |

Inverse queryは全domain・全方式で0だった。Counterfactual repairはd2 correctで0.5417だったが、shuffleも0.4167であり、固有能力ではない。

## 判定

**中核仮説は反証。能力上の進歩は未認定。G1未達。**

低rankのjoint change operator自体は生成でき、target単体は複数条件でchance 0.125を上回った。しかし、target・move・goalを同じdiagram unitで閉じるjoint能力はほぼ0で、隠しdomain d3の自由日本語はCorrect 0、world shuffle 0.0417だった。seed別gapも符号が反転し、strict progress gateはfalseだった。

重要な切り分けは次である。

> raw言語差分とraw world差分を同時に低rank化しても、その共分散は「同じ変換」を同定しない。発話対の差分には対象変更・操作変更・目的変更・文型変更が重なり、world側のgeometry差分にもtarget・move・goalが重なるため、SVDは共同創発ではなく混合変化の平均軸を作った。

したがってAF-007の中心思想そのものは継続可能だが、**一括したpaired-change共分散を共同生成とみなす下位仮説は不採用**とする。

## 凍結族との違い

- 固定結果codebookを先に置いていない
- identity/operation/goal channelをモデルへ与えていない
- span・位置・幅候補を生成していない
- 後段consensus/lesionだけで意味へ昇格していない

ただし、変換候補を一つの線形潜在空間へ平均したため、実質的には異質な変換を後から分離できない別の混合問題へ退化した。

## 他系列へ返す知見

- B: world変換候補を単一delta vectorへ畳まず、同じ局所supportに対する互いに競合する小さな変換生成器として保持する必要がある。
- C: 交換子残差は平均cross-covarianceではなく、個別episodeの二経路差を直接監査し、片方の変換だけを交換した四角形で測る必要がある。
- D: eligible diagram unitは0。保存・干渉・sleep consolidationは再開不可。
- E: AF-007は継続。ただし `global_low_rank_pair_change_is_joint_emergence` を不採用下位仮説として登録すべき。

## 資源量

- Model: **1824 bytes**
- Peak RSS: **111564 KiB**（Python/NumPy runtime込み）
- Runtime: **20.245 sec / 3 seeds**
- Train pairs: **24 / domain / seed**
- Candidate: **64**
- Estimated update: **768 ops/pair**
- Estimated inference: **29184 ops/query**
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 次の仮説

**Locally Competing Commutator Squares from Single-Factor Surprise Splits**  
（単一因子surprise分岐からの局所競合交換子四角形）

次は全paired changeを一つのSVDへ平均しない。

1. 各episode対について、言語変換候補とworld変換候補を複数保持する。
2. 一方の経路だけが閉じないcounterexampleから、交換子残差を減らす最小局所変換対をbirthする。
3. 同じ変換対が対象変更・操作変更・目的変更のうち一種類だけへ選択的に反応することを、名称なしで外部応答から判定する。
4. 片domainで形成した局所diagramを、完全に隠したd3へ再学習なしで適用する。
5. Correct / language-transform shuffle / world-transform shuffle / diagram-pair shuffle / randomを比較する。

進歩条件は、2 opaque domain × 3 seedすべてで自由日本語・prospective・inverse・repairのCorrect差が+0.10以上、かつ同一diagram unitの隠しdomain再生成である。

- Semantic Identity Gate G1: 未達
- Operation/Goal Gate G2: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
