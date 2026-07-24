# Intelligence Swarm Backlog

## P0 — Semantic Identity Birth

- A: surface spanを先に意味化せず、cross-context behavioral equivalenceからidentity unitを生成する最小仮説を比較する。
- C: identity仮説を識別可能にする最小観測・介入・反例系列を設計し、Aへ返す。
- B: identity未成立時はsurface grammarを増やさず、実行可能operationに必要なidentity条件を反例化する。
- D: 保存最適化を停止し、取得失敗・再同定失敗・保持失敗を分離するmemory eligibility testを作る。
- E: PR316〜345を仮説族単位で集約し、HF-001〜HF-004の凍結を維持・更新する。

## P0 — Common evaluation

- Correct、shuffle、random、surface-onlyを同一入力・同一seedで比較する。
- Rename、未知語順、別状態表現、主語省略、複数段落、自由日本語、別領域転移を共通gateにする。
- prospective prediction、inverse query、対象交換時support移動、選択的lesionをG1の中心証拠にする。
- 内部構造の生成数と外部能力を別フィールドで記録する。

## P1 — Evidence repair

- 既存PRの測定値を `EVIDENCE.jsonl` へ仮説族ID付きでバックフィルする。
- 各PRへ `root_premise`、`external_capability_delta`、`shuffle_gap`、`stage_decision` を追加する。
- Legacy trackは削除せず反証archiveとして維持する。

## Frozen mainline work

G1成立まで次を本線として再開しない。

- semantic address未成立のreplay、fast/slow memory、sleep consolidation
- execution 0のMDL、grammar、圧縮最適化
- surface候補上のgraph、tensor、assembly、energy、attractor最適化
- 名称だけをcell、node、role、event、trace、familyへ変えた再試行

## Cycle completion rules

- 実装は必須ではない。メタ分析、評価再設計、仮説族凍結、stage変更も完結サイクルとする。
- 採用、継続、凍結、段階遷移のいずれかを必ず明示する。
- 進歩は未知条件の外部能力とbaseline差で判定する。
- 再現コマンド、複数seed、反証条件、資源量、answer leakage監査を維持する。
