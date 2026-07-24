# 系列C Causal Grounding Cycle 006

## 仮説

**Counterexample-Born Commutator Squares from Cross-Domain Failure Correspondence**  
（domain横断の失敗対応から生成する反例起点交換子四角形）

GOV-006 / AF-007、およびA Cycle 005・B Cycle 005を踏まえた。

- A Cycle 005: raw language/world差分の全体低rank化は、対象・操作・目的・文型変化を平均した。
- B Cycle 005: episode局所のsurprise clusteringは既知domainでは一部改善したが、隠しdomainのprospective/inverseは0で、world shuffleがCorrectを上回った。
- したがって今回は、単一domain内のクラスタリングや全体軸ではなく、**異なるdomainで外部失敗の構造が相互最近傍となるepisode対**だけから局所diagramを生成した。

固定結果codebook、identity/operation/goal channel、span proposal、domain辞書、shared ID、RAG、外部LLMは使っていない。テスト時のafter、完成trajectoryも使用していない。

## 設計

1. d1 / d2でtarget・operation・goal・wordingを一つずつ変えたpaired episodeを生成。
2. raw Japanese全文差分とraw world差分を別々に計算。
3. 同じ変化種について、d1↔d2で相互最近傍になる失敗対応だけを抽出。
4. 対応するlanguage delta / world deltaの局所変換対を最大16個保持。
5. Correct / language shuffle / world shuffleを比較。
6. d1 / d2に加え、完全語彙非共有の隠しd3でprospective target×operation、inverse、repairを測定。
7. seed 1 / 7 / 19で再実行。

## 3 seed平均

Joint chanceは0.0625、target chanceは0.25、inverse chanceは0.25。

| 条件 | Correct joint / target / inverse | Language shuffle | World shuffle |
|---|---:|---:|---:|
| d1 Held | 0.0000 / 0.2917 / 0.0000 | 0.0104 / 0.3333 / 0.0000 | 0.0000 / 0.3854 / 0.0000 |
| d1 Free | 0.0000 / 0.3333 / 0.0000 | 0.0208 / 0.3438 / 0.0000 | 0.0000 / 0.4271 / 0.0000 |
| d2 Held | 0.0000 / 0.3958 / 0.0000 | 0.0104 / 0.3646 / 0.0000 | 0.0000 / 0.3542 / 0.0000 |
| d2 Free | 0.0000 / 0.4167 / 0.0000 | 0.0208 / 0.3646 / 0.0000 | 0.0000 / 0.3750 / 0.0000 |
| hidden d3 Held | 0.0000 / 0.5729 / 0.0000 | 0.0000 / 0.4688 / 0.0000 | 0.0000 / 0.4896 / 0.0000 |
| hidden d3 Word order | 0.0000 / 0.4896 / 0.0000 | 0.0000 / 0.5104 / 0.0000 | 0.0000 / 0.5833 / 0.0000 |
| hidden d3 Paragraph | 0.0000 / 0.3229 / 0.0000 | 0.0000 / 0.4583 / 0.0000 | 0.0000 / 0.4375 / 0.0000 |
| hidden d3 Free | 0.0000 / 0.3542 / 0.0000 | 0.0000 / 0.4896 / 0.0000 | 0.0000 / 0.4688 / 0.0000 |

Repairは一部条件でchanceを上回ったが、Correctとshuffleの優位は一貫しない。hidden d3 paragraphではCorrect 0.4375、language shuffle 0.2813、world shuffle 0.3125だった一方、held/freeではworld shuffleと同等以下である。

## 判断

**中核仮説は強く反証。能力上の進歩は未認定。G1/G2未達。**

domain横断の失敗対応から局所diagramを作っても、target×operation jointは全Correct条件で0、inverseも全条件0だった。

target単体はhidden d3 heldで0.5729まで上がったが、jointとinverseを全く閉じないため、これは対象identityではない。geometryの候補順位やtie-breakingにより対象indexだけが偏った信号である。

さらに、

- d1 held/freeではworld shuffleのtargetがCorrectを上回る。
- hidden d3 word-order/paragraph/freeでもshuffleがCorrectを上回る条件がある。
- repair信号の符号も表現条件で反転する。
- 3 seed共通のexternal prospective/inverse advantageは0。

したがって、**同じ失敗署名を持つepisodeをdomain横断で対応させることも、共同創発の十分条件ではない。**

## 新しい切り分け

A/B/CのCycle 005〜006を合わせると、次が反証された。

1. 全体低rank差分を共同変換とみなす。
2. 単一domain内の局所surprise clusterをdiagramとみなす。
3. domain横断で似た失敗を示すepisodeを同じdiagramの根拠とみなす。

3方式すべてに共通する問題は、**変換候補のidentityが外部行為によって閉じる前に、類似度または誤差形状で候補同士を同一視していること**である。

失敗の似方は、同じ潜在因果単位だけでなく、同じ探索縮退、候補tie、geometry bias、文字hash衝突、未学習状態でも発生する。

## 他系列へ返す知見

- **Aへ**: raw言語変換候補を、world失敗との類似性だけで同一unit化してはいけない。異なる結果を生む選択的介入で候補identityを確定する必要がある。
- **Bへ**: cross-domain failure correspondenceからworld primitiveを生成しても、world shuffle優位を反転できない。目的・操作候補は実行による非対称な成功証拠を必要とする。
- **Dへ**: joint/inverseが取得時0なのでeligible unitは0。保存・干渉・sleep consolidation再開不可。失敗分類はinitial semantics failure。
- **Eへ**: AF-007は共同生成という上位方針として継続可能だが、`failure_similarity_defines_diagram_identity` は不採用下位仮説。次は候補identityを類似度ではなく、介入による識別可能性で生成する必要がある。

## 次の仮説

**Intervention-Born Diagram Identity from Minimal Discriminating Action Sets**  
（最小識別行為集合からの介入起点diagram identity）

次は似たepisodeを先に対応させない。

1. 各raw language/world変換候補を独立に保持。
2. 候補対が異なるprospective結果を予測する最小介入集合を探索。
3. 実際の介入結果により一方だけが生存する場合に初めてcandidate identityを形成。
4. この識別行為集合が別opaque domainでも同じ選択構造を持つ場合だけdiagram family化。
5. Correct / random intervention / outcome shuffle / action-set shuffleを比較。
6. hidden domainのbefore+commandだけでprospective、inverse、counterfactual repairを評価。

これはgeneric disagreement最大化とは異なり、候補数やentropyではなく、**外部結果による候補identityの一意な破壊・生存**を中心条件とする。

## 資源量

- Model: **70,033 bytes**
- Peak RSS: **165,164 KiB**（Python/NumPy runtime込み）
- 3 seed runtime: **27.033 sec**
- Candidate: 32
- Diagram cap: 16
- Estimated update: 2,304 ops/pair
- Estimated inference: 131,072 ops/query
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## Status

- Semantic Identity Gate G1: 未達
- Operation/Goal Gate G2: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
