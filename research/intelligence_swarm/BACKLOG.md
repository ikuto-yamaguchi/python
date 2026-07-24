# Intelligence Swarm Backlog

## P0 — Symmetry-Breaking Witness Grounding

- A: 発話時刻・指示・説明とtrajectory continuity／不可逆痕跡を同期させ、文字区間を先に意味候補化せずwitness-bearing unitを形成する。
- A: held-out paraphrase、rename、未知語順、主語省略、複数段落、別領域で同じunitをprospective predictionとinverse queryへ再利用する。
- C: 行動同値・trajectory・不可逆痕跡・joint witnessの必要十分性を、完全同型の双子対象、world automorphism、counterfactual interventionで切り分ける。
- D: witness-bearing unitだけをmemory eligibility対象とし、日本語との結合成立前は保存最適化を再開しない。
- B: operation/goal候補が対象identityの誤同定で壊れる反例を生成し、A/Cへ返す。
- E: PR349/350のpilotを共通G1a benchmarkへ変換し、synthetic観測識別と日本語semantic groundingを別スコアで管理する。

## P0 — Common evaluation

- Correct、identity shuffle、trajectory shuffle、scar shuffle、random、behavior-only、surface-onlyを同一入力・同一seedで比較する。
- Rename、未知語順、別状態表現、主語省略、複数段落、自由日本語、別領域転移を共通gateにする。
- prospective prediction、inverse query、対象交換時support移動、twin-object discrimination、選択的witness lesionをG1の中心証拠にする。
- acquisition、re-identification、retentionを別フィールドで記録し、取得時0をforgettingと呼ばない。
- 内部構造の生成数と外部能力を別フィールドで記録する。

## P1 — Evidence repair

- PR349をAF-001の限定／棄却証拠およびAF-003の理論根拠としてバックフィルする。
- PR350をAF-003のsynthetic pilot evidenceとしてバックフィルし、G1未達を明示する。
- 既存PRの測定値を `EVIDENCE.jsonl` へ仮説族ID付きでバックフィルする。
- 各PRへ `root_premise`、`external_capability_delta`、`shuffle_gap`、`stage_decision` を追加する。
- Legacy trackは削除せず反証archiveとして維持する。

## Frozen mainline work

G1成立まで次を本線として再開しない。

- semantic address未成立のreplay、fast/slow memory、sleep consolidation
- execution 0のMDL、grammar、圧縮最適化
- surface候補上のgraph、tensor、assembly、energy、attractor最適化
- 名称だけをcell、node、role、event、trace、familyへ変えた再試行
- behavioral equivalenceだけをindividual identityとみなす方式

## Cycle completion rules

- 実装は必須ではない。メタ分析、評価再設計、仮説族凍結、stage変更も完結サイクルとする。
- 採用、継続、凍結、段階遷移のいずれかを必ず明示する。
- 進歩は未知条件の外部能力とbaseline差で判定する。
- Synthetic観測pilotとraw Japanese semantic能力を混同しない。
- 再現コマンド、複数seed、反証条件、資源量、answer leakage監査を維持する。