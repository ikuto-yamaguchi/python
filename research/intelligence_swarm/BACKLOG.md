# Intelligence Swarm Backlog

## P0 — Transformation-Indexed Cross-Expression Causal Equivariance

- A: raw表現のn-gram共有やresponse equalityを使わず、target identity/state交換に対する共変則から対象・変数候補を生成する。
- A: Rename、未知語順、主語省略、複数段落、自由日本語で同じ変換則が再生成される反例を作る。
- B: target/source/goal/argumentを個別交換し、対応するtransition成分だけが変化し他成分が保存されるoperation signatureを生成する。
- B: same-delta、paired token差、set-valued surface coreをidentity birthへ使わない。
- C: target-state、target-identity、non-target、argument-order、intervention-order、causal-direction、goalの軸別equivarianceを同時監査する。
- C: response equality controlと、State-axis / Target-link / Argument-link / Direction / Goal shuffleを必須化する。
- D: 二つの独立取得集合が各集合単独で同じtransformation-indexed unitへsame-unique再収束した場合だけ資格候補化する。
- D: Pair shuffleで能力が維持されるunit、tensor-equivalent collision、集合予測だけで高精度なunitを拒否する。
- E: HF-015の言い換え再試行とoracle intervention-axis漏洩を監査する。

## P0 — Common G1/G2 benchmark v11

- candidate birth、介入軸発見、calibration outcome、independent second acquisition set、conflict audit、final held-out evaluationを分離する。
- `identity vs set-zero`、`set-one vs toggle`、target同値/non-target破壊、argument-order、intervention-order、causal-direction、goal反転を必須反例とする。
- response value equalityではなく、各介入軸に対するselective covariance/invariance matrixを評価する。
- 各独立集合が単独でsame-unique再収束しなければ不合格。intersection、ensemble、tensor-cluster rescueは禁止。
- Active / Random / State-static / Global-template / Boundary / Factor / Family / Arity / Pair / State-axis / Target-link / Argument-link / Direction / Goal / Outcome shuffleを同一seedで比較する。
- fixed ontology、辞書、shared token/ID、oracle token境界、role cardinality、operation family、state interface、scope、arity、介入軸ラベルを正式条件では禁止する。
- surface語順、余剰語、省略、段落構造はepisode-local nuisance orbitとして保持する。
- 接地未使用token、Rename、未知語順、主語省略、複数段落、自由日本語、未観測state×target×operation/relation組合せを評価する。
- 3 seedすべて・2以上のopaque domainでCorrectが全対照を0.10以上上回ることを暫定昇格条件とする。
- conflictはsupport非重複、将来予測不一致、変換軸別の選択的矛盾で隔離する。

## P1 — Evidence and benchmark repair

- PR402を `surface_shared_paired_difference_failure` として登録する。
- PR403を `paired_role_lesion_birth_failure` として登録する。
- PR404を `same_delta_cross_expression_failure` として登録する。
- PR405を `response_tensor_equality_collision_memory_failure` として登録する。
- HF-015とAF-014を仮説族台帳へ追加する。
- track-local evidenceを主台帳へ安全に追記し、既存証拠を削除しない。

## Frozen mainline work

G1成立まで次を本線として再開しない。

- semantic address未成立のreplay、fast/slow memory、sleep consolidation
- execution 0のMDL、grammar、圧縮最適化
- surface候補上のgraph、tensor、assembly、energy、attractor最適化
- 名称だけをcell、node、role、event、trace、familyへ変えた再試行
- behavioral equivalenceだけをindividual identityとみなす方式
- 完成trajectory・行為後scarをprospective identity featureとして利用する方式
- relation、座標可換性、factorizationだけでcross-domain semanticsが生まれるとみなす方式
- 単一domain、domain平均、一部seedだけの陽性を再利用可能semantic unitとみなす方式
- generic disagreement、固定結果codebook、consensus/transpose/lesionによる後段意味化
- 外部識別前の低rank軸、surprise、失敗形状類似度によるidentity確定
- 正しいcandidate supportなしのselector、version-space collapse、oracle action改善
- bridge 0の完全未知語彙zero-shot失敗に対し候補型・head・selectorを追加する方式
- 全episodeへ単一の固定segmentation/order/templateを強制する方式
- 有限role/program vocabularyを先に列挙し、posterior intersectionでidentityへ昇格する方式
- **paired difference、same-delta、response tensor/function equalityだけでsemantic・causal・episode identityを確定する方式**

## Cycle completion rules

- 実装は必須ではない。メタ分析、評価再設計、仮説族凍結、stage変更も完結サイクルとする。
- 採用、継続、凍結、段階遷移のいずれかを必ず明示する。
- 進歩は非oracle介入後のheld-out外部能力、domain/seed/unit consensus、各集合単独の独立再同定で判定する。
- response equality、tensor cluster、intersection rescue、候補縮約、oracle高精度、witness数削減、棄権増加はsemantic progressと混同しない。
- 複数seed、反証条件、資源量、answer leakage、calibration-after leakage、domain bridge leakage、oracle-structure leakage、global-template leakageを監査する。
