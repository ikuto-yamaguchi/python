# Intelligence Swarm Backlog

## P0 — Minimal-Witness Joint Structure Identification

- A: raw Japanese全文について複数segmentation候補を保持し、文字位置・幅をsemantic unitと仮定せず、外部witnessがどの境界仮説を排除するか測る。
- A: 単一witness集合だけでなく、重複しない第二witness集合でも同じ対象・変数単位へ再収束することを要求する。
- B: oracle operation token、固定target index、固定unary arityを外し、可変長引数・unary/binary relation・goal候補を外部結果で共同分割する。
- B: operation単独orbitではなくtarget／relation orbitと交差するwitnessを選び、未観測因子組合せへの合成を評価する。
- C: segmentation、factorization、arity、causal mappingを同一version spaceで保持し、期待posterior縮約が最大のinterventionを選ぶ。
- C: prospective、inverse、counterfactual composition、repairを接地未使用queryで測る。
- D: 重複しない二つの最小witness集合が同じraw-learned構造へ収束し、矛盾witnessを既存identityへ上書きせず取得競合として隔離できる場合だけ資格候補にする。
- E: zero-witness同定不能条件、oracle segmentation/factorization/arity、calibration-after、domain bridge、best-seed選択を監査する。

## P0 — Common G1/G2 benchmark v7

- `budget=0`は置換対称性・理論chance上限の監査として別報告し、能力進歩gateに使わない。
- calibration witness budgetを0 / 1 / 2 / 3 / 4以上で測り、Active / Random / Outcome shuffle / Oracle structural supportを比較する。
- initial candidate generation、witness selection、calibration outcome、independent second witness set、conflict audit、final held-out evaluationを分離する。
- 固定ontology、対応辞書、shared token、shared ID、oracle token境界、oracle factorization、oracle arityを正式条件では禁止する。
- raw Japaneseの複数segmentation、unary/binary以上のarity、target/operation/relation mappingを共同仮説空間へ含める。
- 接地に使っていないtoken、Rename、未知語順、主語省略、複数段落、自由日本語、未観測因子組合せを評価する。
- Correct、Random witness、boundary shuffle、factor shuffle、arity shuffle、outcome shuffle、witness-set shuffleを同一seedで比較する。
- 3 seedすべてでCorrectが全対照を0.10以上上回り、独立witness集合で同じ構造へ再収束することを暫定昇格条件とする。

## P1 — Evidence and benchmark repair

- PR375、376、378、379、381のbridge 0 hidden-domain失敗を、algorithmic failureとidentifiability failureへ再分類する。oracle条件でも失敗した部分だけを機構反証として残す。
- PR382をHF-012の理論・実測根拠として主台帳へ登録する。
- PR383〜385の1.0結果には `oracle_segmentation/factorization/arity_upper_bound` を明記し、G1/G2進歩へ数えない。
- GOV-008のHF-011凍結を維持し、selector-only再試行とzero-witness candidate expansionの双方を拒否する。
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

## Cycle completion rules

- 実装は必須ではない。メタ分析、評価再設計、仮説族凍結、stage変更も完結サイクルとする。
- 採用、継続、凍結、段階遷移のいずれかを必ず明示する。
- 進歩は最小witness後のheld-out外部能力、domain/seed/unit consensus、独立再同定で判定する。
- version-space縮約、oracle条件の1.0、witness数削減、候補数削減はsemantic progressと混同しない。
- 複数seed、反証条件、資源量、answer leakage、calibration-after leakage、domain bridge leakage、oracle-structure leakageを監査する。