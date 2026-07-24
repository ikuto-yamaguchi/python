# 系列B Operation / Goal Cycle 005

## 仮説

**Locally Competing Commutator Squares from Single-Factor Surprise Splits**  
（単一因子surprise分割からの局所競合交換子四角形）

GOV-006で固定結果codebookを先に作るHF-009が凍結され、AF-007 `Jointly Emergent Language–World Intervention Diagrams` が優先本線へ移った。PR #372ではraw言語差分とworld差分を一括低rank化したが、対象・操作・目的・文型変化が平均軸へ混線し、hidden domainのjoint能力はほぼ0だった。

今回はglobal low-rankをやめ、episodeごとのraw Japanese変化とworld介入変化を結合したsurprise方向を局所的に競合させ、12個の匿名diagram候補を共同生成した。identity / operation / goal label、固定結果channel、span proposal、domain辞書、RAG、外部LLMはモデルへ与えていない。

## 重複回避

| 系列 | 最新中心 | Bで成果対象にしない領域 |
|---|---|---|
| A | global paired-change joint operatorの反証、局所diagram候補へ移行 | semantic identityそのもの |
| C | 言語→worldとworld→言語の交換子残差監査 | 因果grounding・world identity |
| D | diagram成立前のmemory eligibility拒否 | 保存・再固定化 |
| E | HF-009凍結、AF-007段階管理 | 仮説族管理 |
| **B** | **局所diagramがprospective operation・goal・inverse・repairを生むか** | 今回の固有対象 |

## 実験設計

- 学習domain: d1 / d2
- 完全語彙非共有hidden domain: d3
- raw Japanese全文をbyte n-gram hashで符号化するが、文字列検索・辞書照合は行わない
- worldは6対象の連続座標
- target × move × goal = 32候補
- 局所diagram 12個をfarthest-first + 5回競合更新で共同生成
- Correct local diagrams
- language-transform shuffle
- world-transform shuffle
- global single-axis baseline
- seed: 1 / 7 / 19
- test時after・完成trajectory不使用

## 3 seed平均

Joint chanceは1/16 = 0.0625、inverse chanceは0.25、goal chanceは0.5。

| 条件 | Local joint | Language shuffle | World shuffle | Global axis | Local inverse | Local repair |
|---|---:|---:|---:|---:|---:|---:|
| d1 held | 0.1111 | 0.0556 | 0.4028 | 0.1528 | 0.0000 | 0.2500 |
| d1 free | 0.0833 | 0.0833 | 0.3056 | 0.1667 | 0.0000 | 0.3472 |
| d2 held | 0.0278 | 0.0139 | 0.2083 | 0.0417 | 0.0000 | 0.2500 |
| d2 paragraph | 0.2361 | 0.0417 | 0.3750 | 0.0972 | 0.0000 | 0.3750 |
| d2 free | 0.2222 | 0.1111 | 0.4028 | 0.0694 | 0.0000 | 0.2639 |
| hidden d3 held | 0.0000 | 0.0000 | 0.0000 | 0.0417 | 0.0000 | 0.2639 |
| hidden d3 free | 0.0000 | 0.0000 | 0.0000 | 0.0278 | 0.0000 | 0.2778 |

## 判断

**中核仮説は強く反証。能力上の進歩は認定しない。G1 / G2未達。**

### 局所分割はglobal axisを一部条件で上回る

d2 paragraphはlocal 0.2361、global axis 0.0972、d2 freeはlocal 0.2222、global 0.0694となった。全差分を一軸へ平均するより局所競合の方が既知domain内の一部prospective能力を保持した。

### hidden domainでは全面0

完全語彙非共有d3ではheld / word order / paragraph / freeの全条件でlocal joint = 0、inverse = 0。局所diagramは別語彙domainで再生成されず、AF-007の外部進歩条件を満たさない。

### world shuffleがCorrectを上回る

d1 heldはCorrect 0.1111に対しworld shuffle 0.4028、d2 freeは0.2222に対し0.4028。これは局所squareがworld介入の正しい対応ではなく、候補生成時のsurface geometryやscore degeneracyへ依存している強い反証である。

### Goal成績は偽陽性

Local goalは多くの条件で0.8〜1.0だが、jointとinverseが成立せず、hidden d3でも常に1.0になった。候補rankingが一方のgoalへ縮退した結果であり、目的理解ではない。

### Failure repairもchance近傍

Repairは0.25〜0.38程度で、4方向chance 0.25から実質差0.10を安定して超えない。prospectiveと同じdiagram unitによる修正ではない。

## 反証条件

1. d1 / d2 / hidden d3の全seedでCorrect > language/world shuffle +0.10
2. prospectiveとinverseを同一unitで改善
3. goal変更とfailure repairも同時改善
4. free Japanese / paragraphで同符号
5. hidden domainへ再学習なしで再生成

すべて未達。

## 資源量

- Model: 38,984 bytes
- Peak RSS: 115,624 KiB
- Mean training: 0.0323 sec
- 3 seed total runtime: 20.617 sec
- Candidate: 32
- Estimated update: 3,200 ops / pair
- Estimated inference: 122,880 ops / query
- 1GB未満: 達成
- 弱いスマートフォンCPU実機: 未検証

## 他系列へ返す知見

- A: 局所surprise splitだけでは語彙非共有domainに言語変換unitを再生成できない。候補生成時からhidden-domain不変性を制約する必要がある。
- C: world shuffleがCorrectを上回るdiagramは因果候補として即棄却し、交換子残差だけでなくbaseline orderingをgateに含めるべき。
- D: prospective / inverse資格がhidden domainで0のためmemory eligible unitは0。保存本線は再開不可。
- E: `local_competing_commutator_squares_are_joint_emergence` をAF-007の不採用下位仮説候補として登録すべき。

## 次仮説

**Counterexample-Born Commutator Squares from Cross-Domain Failure Correspondence**

次は同一domain内のsurprise方向をclusterしない。

1. d1で失敗したqueryとd2で同じ外部失敗を示すqueryを対応辞書なしで組にする
2. 両domainでCorrectとworld shuffleの順位が反転する最小language/world変換対を生成
3. hidden d3の一切のlabelを使わず、diagramの外部失敗署名だけで再生成
4. target / transition / goal / repairのどれを直すsquareかを出力結果で競合させる
5. Correct / language shuffle / world shuffle / pair shuffle / randomを比較
6. 2 opaque domain × 3 seed × free Japaneseで+0.10を必須化

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
