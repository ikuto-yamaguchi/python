# 系列C Causal Grounding Cycle 001

## 現在段階

- Active stage: S1 Semantic Identity Birth
- G1 Semantic Identity Gate: 未達
- Causal grounding本線: G1/G2待ち
- 今回の役割: semantic identityを識別可能にする最小観測条件の監査

HF-001〜HF-004は凍結済みであるため、文字区間候補、after差分tensor、relation graph、欠測補完、energyによる後段選別は実装していない。

## 新仮説

**Automorphism-Limited Causal Identifiability**

> 観測・介入・結果の因果fingerprintだけでは、対象・変数identityはworldの自己同型までしか同定できない。対象交換や全介入を増やしても、全体が対称に観測される限りidentityは一意化せず、時間連続性、身体座標、個体履歴、不可逆生成、外部指示点のようなsymmetry-breaking signalが最低1種類必要である。

これはsemantic unitを文字境界から生成する仮説ではなく、semantic identityが原理的に識別可能となる観測条件を調べるメタ実験である。

## 実験設計

4対象×3属性×2値の完全対称worldを作り、対象名・属性名の置換で観測集合が不変になる自己同型数を全探索した。

比較した観測protocol:

1. Passive: 1 transition
2. Repeat: random 4 transitions
3. Object swap: 同じ属性・値を全対象へ介入
4. Object+value: 全対象×2値へ介入
5. Selective full: 全対象×全属性×2値へ介入

モデルや日本語span候補は形成せず、観測protocolがidentityを一意にできるかだけを監査した。3 seedを使用した。

## 結果（3 seed平均）

| Protocol | Observation | 残存自己同型 | 残存identity bits |
|---|---:|---:|---:|
| Passive | 1 | 12.00 | 3.585 |
| Repeat | 4 | 1.67 | 0.667 |
| Object swap | 4 | 48.00 | 5.585 |
| Object+value | 8 | 48.00 | 5.585 |
| Selective full | 24 | 144.00 | 7.170 |

- Total audit: 0.1717 sec
- Peak RSS: 109,476 KiB（Python runtime込み）
- Learned model: 0 bytes
- Candidate graph: 0
- Exact audit complexity: `O(n_object! * n_property! * Q * n_object * n_property)`

## 反証と発見

当初の素朴な期待「介入を網羅すればidentityは一意化する」は反証された。

特に重要なのは、Object swapやSelective fullで観測数を増やすほど自己同型が残ったことである。これは情報量不足ではなく、**観測protocolが対称性を保存している**ためである。全対象・全属性を等しく操作しても、対象名と属性名を一括置換したworldは同じ因果構造を持つ。

したがって、因果挙動だけから得られるのは「同じ役割を持つ同値類」であり、個体identityや変数identityそのものではない。

Repeat protocolで自己同型が小さくなったのは、random samplingが偶然非対称なcoverageを作ったためであり、別seed・別worldで再利用可能なsemantic identityの成立ではない。進歩とは認定しない。

## 凍結仮説族との関係

- HF-001: span候補を生成していないため非重複
- HF-002: 圧縮・内部整合性を意味の証拠にしていない
- HF-003: memory形成前の識別可能性だけを扱う
- HF-004: graph/energy relaxationを用いない

## Aへ返す識別可能性条件

Aはcross-context behavioral equivalenceだけでidentity成立と判定してはいけない。最低1つ、置換対称性を壊す観測channelを要求する。

候補:

- 時間連続な同一trajectory
- 観測者に対する身体・空間座標
- 個体固有の生成・消滅履歴
- 不可逆な介入痕跡
- 複数modal間の同時性

必要な反例は、因果挙動が完全に同じ双子対象を作り、上記anchorを除去した場合にidentityが入れ替わるかである。

## Bへ返す実行可能性反例

操作の結果が同じだけでは、どの対象・変数へ作用したかは同定できない。Bのoperation proposalは、同じ結果を生む対象交換worldで、非対象保存とtrajectory anchorにより作用先を再同定できる必要がある。

## Dへ返すepisode identity条件

因果fingerprintだけのepisodeを記憶しても、対称world間でaddressが交換可能である。DはG1前に保存最適化せず、episodeへsymmetry-breaking witnessが存在するかをmemory eligibility条件に加えるべきである。

## Eへ返す段階遷移証拠

AF-001のbehavioral equivalence単独ではidentityを一意化できない。AF-001は「同値類形成」まで、AF-002は「識別可能な介入設計」に加えてsymmetry-breaking observationを探索するよう更新すべきである。

## 次仮説

**Trajectory-Anchored Identity from Cross-Form Sensorimotor Continuity**

次は、日本語表現や対象名を変えても、同一対象の時間連続trajectoryと選択的介入痕跡だけが保存される条件を作る。

比較:

- behavioral fingerprint only
- temporal continuity only
- intervention scar only
- continuity + scar
- shuffled trajectory
- shuffled intervention scar

成功条件:

- 未知表現・対象renameでCorrect > shuffle/random
- prospective predictionとinverse queryの双方で同じidentityを再利用
- 完全同型の双子対象をtrajectory分岐後に区別
- anchor lesionで対応identityだけが崩れる

## 判定

- 進歩認定: なし
- 新発見: あり。因果挙動はidentityを自己同型までしか定めず、symmetry-breaking channelが必要
- G1: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
