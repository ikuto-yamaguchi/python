# Intelligence Swarm Backlog

## P0 — Episode-Local Nuisance Orbit / Raw Structural Core Reconvergence

- A: 対象文字集合・操作文字集合を与えず、raw全文の境界、余剰語、主語省略、複数段落、語順変動をepisode-local候補として保持する。
- A: 表層形が異なっても、重複しない第二witness集合で同じ対象・変数・関係の構造核へ再収束することを要求する。
- B: operation familyとarity候補multisetをoracleで与えず、zero/unary/binary以上の引数構造、goal、argument linkを外部結果から保守的にbirthする。
- B: 全episode共通の単一parseへ強制せず、counterfactual coverageを失わない局所syntax orbitを維持する。
- C: segmentation、factorization、arity、argument link、causal mappingの構造核と、episode-local surface nuisanceを分離した共同version spaceを監査する。
- C: prospective、inverse、object permanence、causal direction、goal change、counterfactual composition/repairを接地未使用queryで測る。
- D: 二つの独立witness集合が同じraw-learned構造核へ収束し、矛盾取得を既存identityへ上書きせず隔離できる場合だけ資格候補にする。
- E: global-template leakage、character-class oracle、operation-family oracle、arity-multiset oracle、calibration-after、domain bridge、best-seed選択を監査する。

## P0 — Common G1/G2 benchmark v8

- `budget=0`は置換対称性・理論chance上限の監査として別報告し、能力進歩gateに使わない。
- calibration witness budgetを段階的に測り、Active / Random / Global-template control / Outcome shuffle / Oracle structural supportを比較する。
- initial candidate generation、witness selection、calibration outcome、independent second witness set、conflict audit、final held-out evaluationを分離する。
- 固定ontology、対応辞書、shared token、shared ID、oracle token境界、oracle character class、oracle factorization、oracle operation family、oracle arity multisetを正式条件では禁止する。
- surface語順・余剰語・省略・段落構造は、外部結果が共通構造を要求するまでepisode-local nuisance orbitとして保持する。
- 接地に使っていないtoken、Rename、未知語順、主語省略、複数段落、自由日本語、未観測因子組合せを評価する。
- Correct、Random witness、global-template control、boundary shuffle、factor shuffle、arity shuffle、argument-link shuffle、outcome shuffle、witness-set shuffleを同一seedで比較する。
- 3 seedすべてでCorrectが全対照を0.10以上上回り、独立witness集合で同じ構造核へ再収束することを暫定昇格条件とする。
- ActiveとRandomの最終能力が同率の場合、witness効率差だけを能力進歩へ数えない。

## P1 — Evidence and benchmark repair

- PR387の部分同定を `raw_boundary_orbit_upper_bound` として登録し、Active-Random差が0.10未満であることを維持する。
- PR388の失敗をselector failureだけでなく `global_surface_template_support_failure` として再分類する。
- PR389〜390の高精度へ `oracle_character_classes/operation_family/arity_multiset_upper_bound` を明記し、G1/G2進歩へ数えない。
- HF-013を主台帳へ登録し、prefix/suffix/interleave/reverse等の名前変更によるglobal-template再試行を拒否する。
- track-local evidenceを主台帳へ安全に追記し、既存証拠を削除しない。
- Legacy trackは反証archiveとして保持する。

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
- bridge 0の完全未知語彙zero-shot失敗に対し、候補型・head・selectorを追加して意味能力を主張する方式
- 全episodeへ単一の固定segmentation/order/templateを強制し、その候補消去をsemantic structure discoveryとみなす方式

## Cycle completion rules

- 実装は必須ではない。メタ分析、評価再設計、仮説族凍結、stage変更も完結サイクルとする。
- 採用、継続、凍結、段階遷移のいずれかを必ず明示する。
- 進歩は最小witness後のheld-out外部能力、domain/seed/unit consensus、独立再同定で判定する。
- version-space縮約、oracle条件の高精度、witness数削減、候補数削減、surface orbit数はsemantic progressと混同しない。
- 複数seed、反証条件、資源量、answer leakage、calibration-after leakage、domain bridge leakage、oracle-structure leakage、global-template leakageを監査する。