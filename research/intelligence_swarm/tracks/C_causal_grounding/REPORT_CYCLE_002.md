# 系列C Causal Grounding Cycle 002

## 現在段階

- Active stage: **S1 Semantic Identity Birth**
- Semantic Identity Gate G1: **未達**
- G1a synthetic identifiability: 限定支持
- 今回の役割: PR352のtrajectory grounding陽性がprospective causal groundingか、観測済み結果の照合かを切り分ける

HF-001〜HF-005の凍結を維持し、span候補、after差分tensor、relation graph、MDL、energy、memory assemblyは使用していない。

## 新仮説

**Pre-Treatment Witness Necessity for Prospective Causal Identity**

> 対象identityを介入結果の予測へ使うには、予測対象の行為より前に利用可能なwitnessだけで同じunitを再同定できなければならない。行為後に完成するtrajectoryや不可逆痕跡を候補照合に使って得た正答は、prospective causal groundingではなくpost-treatment matchingである。

## 実験設計

PR352と同じraw Japanese feature、Hebbian utterance–witness matrix、192対象、8択、seed 1/7/19を再利用した。ただし候補側witnessを時間的にcensorし、同一query・同一候補集合で比較した。

- `full`: 3時点trajectory + scar。行為後の完全情報
- `prefix1`: 最初の1時点だけ
- `prefix2`: 最初の2時点だけ
- `future_only`: 最終時点だけ
- `scar_only`: trajectoryなし、弱い不可逆痕跡だけ
- `shuffle_full`: utterance–full witness対応をshuffle

queryは3時点すべてを記述するため、`full`はretrospective re-identification、`prefix1/2`は未来情報を隠したpre-treatment auditとして扱う。モデルはidentity label、span境界、final test outcomeを使用しない。

## 3 seed平均

8択chanceは **0.125**。

| Witness | Held Japanese | Disjoint domain |
|---|---:|---:|
| Full post-treatment | **0.2396** | 0.1476 |
| Prefix 1 | 0.1580 | 0.1441 |
| Prefix 2 | 0.1892 | 0.1372 |
| Future only | 0.1580 | 0.1285 |
| Scar only | 0.1337 | 0.1319 |
| Shuffled full | 0.1337 | 0.1233 |

主要gap:

- Held full − shuffle: **+0.1059**
- Held prefix1 − shuffle: **+0.0243**
- Held prefix2 − shuffle: **+0.0556**
- Domain full − shuffle: **+0.0243**
- Domain prefix2 − shuffle: **+0.0139**
- Scar-onlyはheld/domainともchance近傍

## 判定

**中核仮説は支持。外部能力の新規進歩は認定しない。PR352の陽性範囲を縮小する。**

完全trajectoryを見せたretrospective条件ではCorrectがshuffleを約0.106上回った。しかし、予測時に未来trajectoryを隠すとgapはprefix1で約0.024、prefix2で約0.056まで縮小した。別domainではfullでもgap約0.024で、pre-treatment条件はほぼchanceだった。

したがってPR352の限定陽性は、

> raw Japaneseと観測済みtrajectory predicateのcross-modal matching

には証拠を与えるが、

> before + commandだけから未知worldのafterを予測するprospective causal identity

の証拠にはならない。

不可逆scarも、そのscarが行為後に生じるなら同じ行為の作用先を事前に決めるanchorには使えない。scar-onlyがchance近傍だったことも、raw Japaneseとの接地未成立を支持する。

## 反証条件の更新

今後G1/G1aでwitness groundingを認定するには、次を分離して報告する。

1. **Pre-treatment availability**: witnessが予測対象の介入前に存在する
2. **Prospective rollout**: before + commandだけでafter/targetを選ぶ
3. **Retrospective re-identification**: 完成trajectoryやscarから過去対象を選ぶ
4. **Inverse query**: witnessから表現を選ぶ
5. **Cross-domain transfer**: 語彙を共有しないdomainでCorrect > shuffle/random
6. **Twin discrimination**: 行動同値の双子を介入前witnessで区別
7. **Post-treatment leakage audit**: 予測対象の結果をcandidate featureへ含めない

retrospectiveとprospectiveを同じaccuracyへ混ぜてはならない。

## 資源量

- Matrix: **98,304 bytes**
- Peak RSS: **177,268 KiB**（Python runtime込み）
- 3 seed runtime: **10.507 sec**
- Candidate scoring: 約**24,576 ops/candidate**
- 8候補: 約196,608 ops/query
- Complexity: `O(K*T*W)`
- 1GB未満: 達成
- 弱いスマートフォンCPU実機: 未検証

## 他系列へ返す知見

### A

PR352の陽性は`trajectory predicate grounding`のretrospective証拠へ限定する。次仮説では、未来trajectoryをfeatureへ入れず、発話変換と**介入前witness変換**のequivarianceからtarget/afterを予測する必要がある。

### B

operation proposalは、行為結果やpost-action scarを作用先選択に使ってはならない。対象選択は介入前identity witnessで行い、afterは独立に予測する。

### D

memory eligibility recordは`observed_at`と`intervention_time`を持ち、post-treatment witnessを同じepisodeのacquisition成功へ数えない。取得、retrospective再同定、prospective利用、保持を別metricにする。

### E

AF-003は継続するが、PR352のevidence labelを`limited_retrospective_trajectory_predicate_grounding`へ縮小することを提案する。G1a benchmarkへpre-treatment leakage gateを追加すべきである。

## 次仮説

**Intervention-Preceding Relational Witness Binding**

発話全体と完成trajectoryを直接結ばず、介入前に観測可能な対象間関係の変換と、commandによる将来変換の可換性を学習する。

成功条件:

- before + commandのみでtwin targetとafterを予測
- held paraphrase、rename、別domainでCorrect − shuffle >= 0.10
- operation順序反転で予測が対応して変化
- non-target保存
- inverse queryでも同一unitを使用
- post-treatment featureを完全にcensor

## 終了判定

- 進歩認定: **なし**
- 新発見: **あり。retrospective witness matchingとprospective causal groundingを分離**
- AF-003: 継続、証拠範囲縮小
- G1: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
