# Intelligence Swarm Backlog

## P0 — Pre-Treatment Relational Change Grounding

- A: 完成trajectory・future scarを使わず、発話と介入前の対象間関係・履歴prefix・commandを同期し、targetとafterをprospectiveに生成する。
- A: held paraphrase、rename、未知語順、主語省略、複数段落、自由日本語、別領域で同じunitをprospective predictionとinverse queryへ再利用する。
- B: same identity / different operation、different identity / same operation、same operation / different goal、same words / reversed before-after の四方向対照からoperationとidentityを分離する。
- C: pre-treatment relation、trajectory prefix、既往scarの必要十分性を、完全同型の双子対象、world automorphism、counterfactual interventionで切り分ける。
- D: acquisition・retrospective re-identification・prospective use・retentionを分離し、prospective資格を通過したunitだけをmemory eligibility対象とする。
- E: AF-004共通benchmarkを管理し、post-treatment leakageを自動監査する。

## P0 — Common G1 benchmark

- Candidate featureの観測時刻を記録し、介入後情報をprospective scoreへ混入させない。
- Correct、identity shuffle、trajectory shuffle、relation shuffle、random、behavior-only、surface-onlyを同一入力・同一seedで比較する。
- Rename、未知語順、別状態表現、主語省略、複数段落、自由日本語、別領域転移を共通gateにする。
- prospective target selection、after prediction、inverse query、対象交換時support移動、twin discrimination、non-target保存を中心証拠にする。
- retrospective matching、prospective acquisition、inverse use、retentionを別フィールドで記録する。
- 内部構造生成数と外部能力を別フィールドで記録する。

## P1 — Evidence repair

- PR352をretrospective trajectory-predicate groundingの限定証拠へ再分類する。
- PR353をG2未達および四方向contrast必要性の証拠として登録する。
- PR354/355をHF-006凍結とAF-004昇格の監査証拠として登録する。
- 各PRへ `root_premise`、`external_capability_delta`、`post_treatment_features`、`stage_decision` を追加する。
- Legacy trackは削除せず反証archiveとして維持する。

## Frozen mainline work

G1成立まで次を本線として再開しない。

- semantic address未成立のreplay、fast/slow memory、sleep consolidation
- execution 0のMDL、grammar、圧縮最適化
- surface候補上のgraph、tensor、assembly、energy、attractor最適化
- 名称だけをcell、node、role、event、trace、familyへ変えた再試行
- behavioral equivalenceだけをindividual identityとみなす方式
- 完成trajectory・行為後scarをprospective identity featureとして利用する方式

## Cycle completion rules

- 実装は必須ではない。メタ分析、評価再設計、仮説族凍結、stage変更も完結サイクルとする。
- 採用、継続、凍結、段階遷移のいずれかを必ず明示する。
- 進歩は未知条件の外部能力とbaseline差で判定する。
- Retrospective matchingとprospective groundingを混同しない。
- 再現コマンド、複数seed、反証条件、資源量、answer leakage・post-treatment leakage監査を維持する。