# Intelligence Swarm Backlog

## P0 — Paired Intervention Basis / Acquisition-Time Unique Reconvergence

- A: fixed role cardinalityなしで、raw自由日本語から対象・状態変数・nuisance候補を生成する。
- A: target-state交換、non-target-state交換、対象交換、値交換でのみ分離できるidentity反例を作る。
- B: 単一tokenまたはset-valued token coreの列挙を本線から外す。
- B: target/source/goal/argumentを個別に交換し、対応するworld transitionだけが選択的に変わるoperation候補を生成する。
- C: 同一operationに対するtarget-state、non-target-state、argument-order、intervention-order、causal-direction reversalをpaired witness basisとして選択する。
- C: prospective、inverse、object permanence、causal direction、goal change、counterfactual repairを同じheld-out queryで測る。
- D: 二つの独立witness集合が各集合単独で同じunique scope–arity–argument-link–programへ再収束した場合だけ資格候補化する。
- D: intersection rescueを禁止し、conflict quarantineをposterior support非重複＋将来予測分布不一致で判定する。
- E: finite role/program vocabulary、posterior intersection、oracle parser/state interface、calibration-after、domain bridge、best-seed漏洩を監査する。

## P0 — Common G1/G2 benchmark v10

- initial candidate birth、paired witness selection、calibration outcome、independent second witness set、conflict audit、final held-out evaluationを分離する。
- `set-one vs toggle`、`noop vs set-zero`、unary vs binary relation、non-target破壊、argument-order交換、intervention-order交換、causal-direction reversalを必須反例とする。
- 各独立集合が単独でunique再収束しなければ不合格。集合intersection後だけの一意化は診断に限定する。
- Active / Random / State-static / Global-template / Boundary shuffle / Factor shuffle / Family shuffle / Arity shuffle / Argument-link shuffle / Pair shuffle / Outcome shuffleを同一seedで比較する。
- fixed ontology、辞書、shared token/ID、oracle token境界、character class、role cardinality、operation family、state interface、scope、arity multisetを正式条件では禁止する。
- surface語順、余剰語、省略、段落構造はepisode-local nuisance orbitとして保持する。
- 接地未使用token、Rename、未知語順、主語省略、複数段落、自由日本語、未観測state×target×operation/relation組合せを評価する。
- 3 seedすべて・2以上のopaque domainでCorrectが全対照を0.10以上上回ることを暫定昇格条件とする。
- conflictはversion-space emptyだけでなく、正常posteriorとのsupport非重複とprospective disagreementを測る。

## P1 — Evidence and benchmark repair

- PR397を `finite_role_vocabulary_alias_upper_bound` として登録する。State-static最終能力1.0を明記する。
- PR398を `set_valued_surface_operation_core_failure` として登録する。外部能力0、formal proposal 0を維持する。
- PR399を `oracle_scope_arity_identifiability_partial_support` として登録する。inverse/object permanenceのgate不足を明記する。
- PR400を `intersection_rescue_confounded_memory_eligibility` として登録する。
- HF-014とAF-013を仮説族台帳へ追加する。
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
- **有限role/program vocabularyを先に列挙し、posterior intersectionでsemantic identityまたはmemory eligibilityへ昇格する方式**

## Cycle completion rules

- 実装は必須ではない。メタ分析、評価再設計、仮説族凍結、stage変更も完結サイクルとする。
- 採用、継続、凍結、段階遷移のいずれかを必ず明示する。
- 進歩は最小非oracle paired witness後のheld-out外部能力、domain/seed/unit consensus、各集合単独の独立再同定で判定する。
- intersection rescue、version-space縮約、oracle高精度、witness数削減、候補数削減、棄権増加はsemantic progressと混同しない。
- 複数seed、反証条件、資源量、answer leakage、calibration-after leakage、domain bridge leakage、oracle-structure leakage、global-template leakageを監査する。