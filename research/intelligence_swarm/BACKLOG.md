# Intelligence Swarm Backlog

## P0 — Cross-Domain Consequence-Invariant Grounding

- A: 語彙、座標系、object indexが完全に異なるdomain間で、同じ選択的結果・失敗修正・inverse応答を生む発話—観測単位を形成する。
- A: domain対応辞書、共有identity、手書きslot、文字列検索なしでheld / rename / free / domainを同一latent unitへ結ぶ。
- B: identity / operation / goal / wording / domain表現の五方向対照を生成し、対応factorだけが変化するか監査する。
- C: domain間で保存される最小因果証拠を、target選択、transition、non-target保存、反実仮想、inverseで切り分ける。
- D: cross-domain prospective、inverse、cross-form consistencyを同時通過するunitだけをmemory eligibleとする。
- E: domain bridge leakage、共有token、暗黙対応表、同一乱数系列による漏洩を監査する。

## P0 — Common G1 benchmark v2

- 学習domainと評価domainで語彙、座標、object index、surface templateを分離する。
- Correct、identity shuffle、operation shuffle、goal shuffle、domain shuffle、randomを同一seedで比較する。
- prospective target selection、transition prediction、inverse query、twin discrimination、non-target保存を同じunitで測る。
- held条件とdomain条件を別々に報告し、held改善をG1通過へ数えない。
- post-treatment feature、domain対応辞書、共有ID、answer leakageを自動検査する。
- 3 seedすべてでdomain Correct > shuffle/random、かつ実質差0.10以上を暫定昇格条件とする。

## P1 — Evidence repair

- PR357〜360へ `root_premise=pre_treatment_structure_without_cross_domain_anchor` を付与する。
- Equivariance、factorization、relation necessityは必要条件診断へ再分類する。
- HF-007とAF-005の証拠を各系列の次サイクルから参照する。
- Legacy trackは削除せず反証archiveとして維持する。

## Frozen mainline work

G1成立まで次を本線として再開しない。

- semantic address未成立のreplay、fast/slow memory、sleep consolidation
- execution 0のMDL、grammar、圧縮最適化
- surface候補上のgraph、tensor、assembly、energy、attractor最適化
- 名称だけをcell、node、role、event、trace、familyへ変えた再試行
- behavioral equivalenceだけをindividual identityとみなす方式
- 完成trajectory・行為後scarをprospective identity featureとして利用する方式
- pre-treatment relation、座標可換性、identity/operation factorizationだけでcross-domain semanticsが生まれるとみなす方式

## Cycle completion rules

- 実装は必須ではない。メタ分析、評価再設計、仮説族凍結、stage変更も完結サイクルとする。
- 採用、継続、凍結、段階遷移のいずれかを必ず明示する。
- 進歩は未知条件の外部能力とbaseline差で判定する。
- Retrospective matching、held-family fit、cross-domain groundingを混同しない。
- 再現コマンド、複数seed、反証条件、資源量、answer leakage・post-treatment leakage・domain bridge leakage監査を維持する。