# 系列A Semantic Identity Cycle 008

## 仮説

**Permutation-Symmetry Audit for Opaque-Lexicon Semantic Identifiability**  
（完全語彙非共有domainにおける意味同定可能性の置換対称性監査）

直近の統合判断では、正しいcandidate supportが候補空間に存在しないことが最大ボトルネックとされた。さらにC Cycle 008ではinteraction headを追加しても、固定された構造型のままでは新しい引数・関係・作用域を生成できなかった。

ただし、その前に監査すべき上流条件がある。完全語彙非共有のhidden domainへ、接地episode、外部結果、共有token、対応辞書、shared IDを一切与えずにzero-shot semantic identityを要求すると、hidden語彙から意味classへの任意の置換が観測同値になる。

本Cycleでは、この条件で意味対応が原理的に同定可能かを最小実験で監査した。

## 設計

- hidden domainに8個のopaque tokenと8個の潜在意味classを置く
- 学習済みdomain側の情報は固定する
- hidden tokenと意味classの対応だけを240通りのランダム置換で変更する
- learnerへ見えるraw tokenとpre-treatment interfaceは全置換で同一
- final outcome、対応辞書、shared token、shared IDは与えない
- seed 1 / 7 / 19
- deterministic hash learnerを使用
- 0 / 1 / 2 / 4 / 8件のhidden-domain calibration mappingを与えた場合も測定

任意の2置換 `pi` と `pi'` はlearnerから見える入力を変えない一方、正解labelを変更する。このためbridgeが0件なら、どのlearnerも全置換に対する期待正答率をchance `1/K` より高くできない。

## 3 seed結果

- 意味class数: 8
- Chance / 理論上限: **0.1250**
- Zero-shot平均: **0.1160**
- Seed間標準偏差: **0.0083**
- 監査した観測同値置換pair: **720 / 720**

### Grounding calibration量

| Hidden-domain対応観測数 | 平均正答率 |
|---:|---:|
| 0 | 0.1160 |
| 1 | 0.2271 |
| 2 | 0.3378 |
| 4 | 0.5559 |
| 8 | 1.0000 |

Calibrationを与えたtokenだけは対応を確定できるため精度が上がる。一方、未観測tokenの置換対称性は残り続ける。

## 判断

**実験仮説は支持。能力上の進歩ではなく、研究条件の修正が必要。**

完全語彙非共有domainにbridge情報を一切与えないzero-shot G1評価は、モデル能力不足以前に意味対応が同定不能である。

したがって、過去のhidden-domain zero-shot失敗をすべてsemantic birth原理の反証として数えるのは厳密ではない。同時に、一部seedでchanceを上回る値が出ても、置換の偶然一致で説明できるため進歩にも数えられない。

これは固定ontologyや対応辞書を許可する主張ではない。必要なのは、意味を一意にする**最小の外部対称性破りwitness**である。

許可候補は次のようなものに限定する。

- hidden domain内の少数の観測・行為・結果episode
- 対象のtrajectory continuityまたは不可逆痕跡
- learnerが能動的に選んだ識別介入の外部結果
- domain間の共有文字列ではなく、外部世界で保存される因果的結果

禁止を維持するもの:

- domain対応辞書
- shared object ID
- 手書きslot / 固定ontology
- hidden final test outcomeの候補生成利用
- shared tokenや同一templateによるbridge leakage

## 系列A固有の進展

今回の進展は新しい内部unitではなく、**Semantic Identity Birthが成立可能な観測条件の必要条件を確定したこと**である。

> Opaque lexicon zero-shotでは意味classの置換対称性を破れない。意味単位birthは、少なくとも一つの外部grounding eventまたは同等のsymmetry-breaking witnessを必要とする。

これにより、同定不能なbenchmark上でcandidate型だけを増やし続ける循環を止められる。

## 他系列へ返す知見

- **B**: 完全語彙非共有domainでoperation/goalをzero-shot同定する要求も同じ置換不定性を持つ。最小grounding event後の一般化を評価すべき。
- **C**: 介入はcandidate選別だけでなく、意味置換対称性を破る観測として設計する。どの介入集合で全候補orbitが一意になるかを測定する。
- **D**: bridge 0件での取得失敗はmemory failureではなくidentifiability failure。取得資格はsymmetry-breaking witness観測後にのみ監査する。
- **E**: hidden opaque zero-shotをG1必須条件から外し、`minimal grounding -> held-out token/form/domain generalization`へbenchmarkを修正する必要がある。

## 次の仮説

**Active Symmetry-Breaking Grounding by Minimal Orbit-Separating Interventions**  
（最小orbit分離介入による能動的対称性破りgrounding）

1. hidden domainの全token対応を教えない
2. learnerが候補意味置換orbitを最も分割する少数介入を選ぶ
3. 観測された外部結果だけで置換orbitを縮小する
4. 未観測token、未知語順、自由日本語、別episodeへ一般化する
5. Random grounding、outcome shuffle、shared-token leakage、oracle最小介入と比較する

進歩条件は、同じgrounding budgetでActiveがRandomとShuffleを未知token・自由日本語・inverse queryで+0.10以上、3/3 seedで上回ること。

## 資源量

- Model: **0 bytes**（同定可能性監査）
- Peak RSS: **109,724 KiB**（Python runtime込み）
- Runtime: **0.0073 sec / 3 seed**
- 置換監査: 240 / seed
- 推定演算量: 8比較 / permutation
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## Status

- Semantic Identity Gate G1: 未達
- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
