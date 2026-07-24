# 系列D Memory Eligibility Cycle 006

## 仮説

**Intervention-Certified Memory Eligibility from Minimal Discriminating Action-Set Survival**  
（最小識別行為集合での候補生存による介入証明付き記憶資格）

## 研究段階と重複回避

現在は S1 Semantic Identity Birth / joint language-world emergence substage であり、G1/G2は未達である。HF-001〜HF-009の凍結を維持する。semantic identity未成立のままaddress、replay、assembly、fast/slow memoryを構築する方式は再開しない。

最新系列との分離：

- A PR #372: raw language/world変化のglobal low-rank共同化。混合軸となり反証。
- B PR #373: single-domain局所surprise diagram。hidden domainで全面0。
- C PR #374: cross-domain failure correspondence。joint/inverseが全面0。
- D Cycle 006: 類似度で候補を同一視せず、外部観測された介入結果で候補を逐次破壊し、唯一生存した候補だけを記憶資格へ通せるか監査。

## 設計

1. d1/d2のraw Japanese変化とpre-treatment world上の仮想変化から最大24候補を生成。
2. 候補間で予測行為が最も分割されるcalibration episodeを選ぶ。
3. 実際の観測結果と一致しない候補を局所的に除去。
4. 最大12 probeまで反復し、唯一生存した候補だけを資格候補とする。
5. Active / Random action selection / Outcome shuffleを比較。
6. d1/d2と完全語彙非共有hidden d3でprospective target×operation、inverse、closed-loopを評価。
7. test時のafter、completed trajectory、domain辞書、shared ID、固定codebook、span proposal、RAG、外部LLMは不使用。

## 3 seed平均

- Active survivors: **0.3333**
- Random survivors: **0.3333**
- Outcome-shuffle survivors: **0.0000**
- Active probes: **1.6667**
- Random probes: **1.3333**
- Shuffle probes: **2.0000**

| 条件 | Active joint / inverse / closed | Random joint / inverse / closed | Shuffle joint / inverse / closed |
|---|---:|---:|---:|
| d1_held | 0.0104 / 0.2083 / 0.0104 | 0.0104 / 0.2708 / 0.0104 | 0.0000 / 0.2396 / 0.0000 |
| d1_free | 0.0312 / 0.2188 / 0.0312 | 0.0208 / 0.2292 / 0.0208 | 0.0000 / 0.2604 / 0.0000 |
| d2_held | 0.0000 / 0.2396 / 0.0000 | 0.0417 / 0.3021 / 0.0417 | 0.0000 / 0.2812 / 0.0000 |
| d2_free | 0.0312 / 0.2083 / 0.0312 | 0.0312 / 0.2396 / 0.0312 | 0.0000 / 0.2188 / 0.0000 |
| d3_held | 0.0104 / 0.2292 / 0.0104 | 0.0312 / 0.2396 / 0.0312 | 0.0000 / 0.2708 / 0.0000 |
| d3_word_order | 0.0208 / 0.2500 / 0.0208 | 0.0000 / 0.2500 / 0.0000 | 0.0000 / 0.2812 / 0.0000 |
| d3_paragraph | 0.0104 / 0.2083 / 0.0104 | 0.0104 / 0.2188 / 0.0104 | 0.0000 / 0.2083 / 0.0000 |
| d3_free | 0.0104 / 0.3021 / 0.0104 | 0.0000 / 0.2812 / 0.0000 | 0.0000 / 0.2917 / 0.0000 |

## 判定

**中核仮説は強く反証された。能力上の進歩は未認定で、formal memory eligibilityは0である。**

外部結果による候補破壊はoutcome shuffleの候補を全seedで消去したため、介入監査そのものは誤対応排除に機能した。しかしCorrect条件でも平均生存候補は0.333で、3 seed中2 seedでは候補集合が空になった。唯一候補が残ったseedでも、未知domain d3のclosed-loopは各条件0〜0.03125であり、ActiveはRandomを一貫して上回らなかった。

したがって、現在の候補集合には、複数介入結果と未知domainのforward/inverseを同時に説明するsemantic unitがほぼ含まれていない。最小識別行為集合は**既存の正しい候補を証明する資格条件**にはなり得るが、正しい候補そのものをbirthする原理ではない。

## 取得失敗と保持失敗の分離

- Acquisition / certification: 未成立
- Retrospective re-identification: 未成立
- Prospective closed-loop use: 未成立
- Retention / interference: 評価対象外
- Catastrophic forgetting: 未観測
- Failure class: **initial semantics failure / candidate-support failure**

資格unitが0なので、fast weights、replay、sleep consolidation、selective forgetting、latest/obsolete競合、容量最適化は再開しない。

## RAG・検索との差

文章や近傍vectorを検索して回答していない。候補が仮定するprospective action responseを外部介入結果で反証し、未知domainのforward/inverseで同じ内部unitを利用できるか監査している。ただし有資格unitは形成されなかった。

## 資源量

- Model bytes mean: **1,031.3 bytes**
- Peak RSS: **115,072 KiB**
- Runtime (3 seeds): **31.674 sec**
- Candidate cap: **24**
- Probe budget: **12**
- Estimated train: **2,304 ops/pair**
- Estimated inference: **98,304 ops/query**
- 1GB未満: 達成
- 弱いスマートフォンCPU実機: 未検証

## 他系列へ返す知見

- A: 候補間を識別する介入を追加しても全候補が消えるなら、問題は選別不足ではなくlanguage/world transformation候補のsupport不足である。
- B: operation候補は単一観測で正解するだけでなく、複数の独立介入結果を同時に生存する必要がある。
- C: minimal action-set survivalは資格監査として有効だが、候補birthを類似度・誤差形状に依存したままでは空集合へ収束する。
- E: AF-007を維持できるが、「識別介入を後付けすれば既存候補からsemantic unitを選べる」という下位仮説は凍結候補。

## 次の仮説

**Intervention-Residual Candidate Birth before Memory Eligibility**  
（記憶資格判定前の介入残差からの候補創発）

次は既存候補を介入で選ぶだけにしない。

1. 候補集合が外部結果を一件も説明できなかったprobeをbirth triggerにする。
2. 予測結果と観測結果の差から、raw Japanese変換とworld介入変換を同時に修正する局所候補を生成する。
3. 同じ残差修復が別episode・別opaque domainで再利用された場合だけcandidate identityを認める。
4. Birthなし / Residual birth / Residual shuffle / Random mutationを比較する。
5. Candidate birth後にのみminimal action-set survivalを適用する。
6. d3のprospective・inverse・自由日本語でCorrect−shuffle/random +0.10、3/3 seedを必須化する。

- Semantic Identity Gate G1: 未達
- Operation/Goal Gate G2: 未達
- Formal memory eligibility: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
