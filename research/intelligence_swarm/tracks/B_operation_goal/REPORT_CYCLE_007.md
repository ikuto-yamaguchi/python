# 系列B Operation / Goal Cycle 007

## 仮説

**Active Orbit-Separating Witnesses for Operation Birth**  
（操作置換orbitを分割する能動witnessによる操作同定）

A Cycle 008は、完全語彙非共有hidden domainへbridge情報を一切与えない場合、opaque token→semantic class対応が任意置換に対して観測同値であり、zero-shot意味同定はchanceを超えられないことを示した。

系列Bではこの必要条件を操作へ移し、候補programやsurface grammarを増やさず、未知domain内の少数の観測・行為・結果witnessによって、匿名操作tokenと匿名world transitionの置換orbitをどこまで縮小できるかを監査した。

## 重要な限定

このサイクルは**操作創発能力の実証ではなく、識別可能性の上限監査**である。

モデルには評価器が切り出したopaque token identityを与えている。したがって、生の自由日本語からtoken境界や対象同一性を創発した結果ではない。このoracle lexical segmentationを使っても最小witnessが必要か、必要なら何件かを測るためのメタ設計であり、能力進歩には数えない。

## 設計

- hidden domain: 4 opaque operation token
- latent transition: 4個の匿名一対象変位
- token→transition対応: seedごとにランダム置換
- 初期version space: 24 permutation
- calibration witness budget: 0 / 1 / 2 / 3 / 4
- Active: 期待version-space減少最大
- Random: 同数の無作為witness
- Outcome shuffle: commandと外部結果の対応を破壊
- Oracle: 真の対応を使う上限probe selector
- seed: 1 / 7 / 19
- final test afterは候補選択・rankingに不使用
- held / rename / 未知語順 / 入れ子 / 複数段落 / 自由記述
- prospective / inverse / goal変更 / failure repair

## 主要結果

### witness 0件

- Version space: 24
- Prospective: 全条件 0
- Inverse: 全条件 0
- Goal変更: 0
- Failure repair: 0

複数候補が同数投票となるため棄権した。Aの置換対称性監査と一致する。

### witness 1件

- Active version space: 6
- Held prospective: 0.2535
- Rename prospective: 0.3056
- Free prospective: 0.2257
- Goal変更: 0.2222
- Failure repair: 0.2361

1件では操作orbitの1/4だけが確定し、外部能力は約chance 0.25に留まった。

### witness 2件

- Active version space: 2
- Held prospective: 0.4826
- Rename prospective: 0.5451
- 未知語順 prospective: 0.5347
- Free prospective: 0.4826
- Goal変更: 0.7292
- Failure repair: 0.4271

2件では残り2 permutationとなり、prospective/inverseは約0.5まで上昇したが一意同定には至らない。

### witness 3件

| 指標 | Active | Random | Shuffle | Oracle |
|---|---:|---:|---:|---:|
| Version space | 1.00 | 3.33 | 0.00 | 1.00 |
| Held prospective | 1.0000 | 0.4097 | 0.0000 | 1.0000 |
| Rename prospective | 1.0000 | 0.3924 | 0.0000 | 1.0000 |
| 未知語順 prospective | 1.0000 | 0.4375 | 0.0000 | 1.0000 |
| 複数段落 prospective | 1.0000 | 0.4132 | 0.0000 | 1.0000 |
| 自由記述 prospective | 1.0000 | 0.4097 | 0.0000 | 1.0000 |
| Goal変更 | 1.0000 | 0.4201 | 0.0000 | 1.0000 |
| Failure repair | 1.0000 | 0.4271 | 0.0000 | 1.0000 |

Activeは3件で全seedのversion spaceを1へ縮小し、prospective、inverse、goal変更、failure repairが全条件1.0となった。Randomは平均3.33候補を残し、外部能力は約0.4に留まった。Outcome shuffleは候補集合を空にし、能力0だった。

## 判断

**識別可能性仮説は支持。能力上の進歩は未認定。G1/G2は未達。**

得られた結論は次である。

> 4操作の完全語彙非共有domainでは、oracle lexical segmentationと正しいtransition familyが既に存在する上限条件でも、対応を一意化するには少なくとも3個の独立witnessが必要である。Active orbit splittingはRandomより効率よく最小件数へ到達する。

これは「3件で生の日本語から操作が創発した」という結果ではない。現在の実験は次を外部から与えている。

- opaque token境界
- target index
- transition候補family
- 一対象操作というarity
- world state correspondence

したがって、実際の最大ボトルネックは、Aが指摘した最小symmetry-breaking witnessの存在だけではなく、raw Japaneseとworld transitionから、どの部分が同じ匿名操作tokenで、どの対象へ何項の作用を持つかをwitnessと同時に生成することである。

## 凍結・重複回避

HF-011のselector-only再試行ではない。正しい候補supportが既にある上限条件を明示し、selectorの性能ではなく必要witness数を測った。

以下は引き続き不採用。

- surface grammarを先に形成
- 固定32 tupleへの残差weight追加
- 結果codebookの後段選別
- bridge 0件hidden domainでzero-shot G2を要求
- 候補数削減だけを進歩認定

## 他系列へ返す知見

### Aへ

operation identityを同定可能にする最低条件として、4-way orbitでは3個の独立witnessが必要だった。次のA評価では、hidden domainのgrounding budgetを0と少数witnessに分離し、raw発話境界とworld変化を同時にorbit分割する必要がある。

### Cへ

介入可能なoperation proposalは、3つの独立witnessで同じtransitionへ一意化された後にのみ因果監査へ渡せる。ただし今回のproposalはoracle segmentation依存のため、Cへ渡せる正式unitは0。

### Dへ

witness 3件後のclosed-loopは上限条件で成立したが、raw Japaneseからの再同定ではないためmemory eligibilityは0。保存・干渉研究は再開不可。

### Eへ

bridge 0件zero-shotを必須gateから外し、`minimal witness + unobserved expression/domain generalization`へ評価を修正すべき。一方、oracle segmentation上の成功をG2進歩へ数えてはいけない。

## 資源量

- Model upper bound: 232 bytes
- Initial hypothesis orbit: 24
- Candidate operations: 4
- Peak RSS: 111,500 KiB（Python runtime込み）
- 3 seed runtime: 0.2156 sec
- Probe評価: 最大96 transition simulations
- 1GB未満: 達成
- 弱いスマートフォンCPU見込み: 十分軽量
- 実機検証: 未実施

## 次の仮説

**Joint Segmentation-and-Orbit Birth from Minimal Action Witnesses**  
（最小行為witnessからの共同分節・操作orbit創発）

次はoracle token identityと固定arityを外す。

1. raw Japanese全文の複数区切り候補を独立維持
2. world transitionから可変arityの匿名作用候補を生成
3. 各witnessがlanguage segmentation orbitとtransition orbitを同時に分割
4. 3件以内で一意化されない候補は棄却せず、追加witness要求としてAへ返す
5. Active / Random / boundary shuffle / outcome shuffle / oracle segmentationを比較
6. 未観測言い換え、対象交換、値交換、目的変更、入れ子、複数段落、自由記述で評価
7. prospective、inverse、goal変更、failure repairがCorrect条件でshuffle/randomを+0.10以上上回ることを進歩条件とする

- Stage: S1 Semantic Identity Birth継続
- G1: 未達
- G2: 未達
- 正式operation proposal: 0
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
