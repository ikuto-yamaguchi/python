# Intelligence Swarm Backlog

## P0
- 入力ごとに未知の日本語区間境界を生成する方式を比較する。
- 候補分解を、将来予測・置換可能性・介入整合性の共同説明力で競合させる。
- 候補プログラムの内部整合性と、現実・言語上の意味的妥当性を区別する。
- 同一モデルの自由対話・指示遂行・読解・推論・計画・因果・反実仮想・自由記述・長期対話・継続学習ゲートを維持する。

## Track B — next
- Role-Factored Multi-View MDL Encoderを実装し、未知命令を既知operationへ結ぶencoder側を検証する。
- entity/value境界だけでなく、argument-role edge、latent operation node、surface decoder residueが異なる複数の可逆候補を生成する。
- 同一episodeの複数命令表現、before/after、no-op、reverse、other-object、後続確認・訂正を共同viewとして符号化する。
- 既知・rename・小型性を維持しつつ、未学習語順と完全未学習同義動詞を0から同時改善する。
- no-op文字列類似を禁止したconfound評価を追加し、operation/no-op/reverse/other-objectの実行結果で選択的拒否を測定する。
- operation/decoder分離の正の結果を意味理解と誤認しない。Cycle 005では能力がliteral graph ablationと完全同一だった。

## Cross-track handoff
- A: 軽量operation nodeから候補未来を生成できるが、未知reply/viewをoperationへ写すencoderが未解決。
- C: identity/value再束縛と因果必要性を分離し、no-op surface負例を因果証拠として扱わない。
- D: operation nodeとsurface decoderを別々に統合し、後続反例でdecoder同値を撤回可能にする。
- E: cross-world実行前にoperation nodeとepisode bindingを分離する。ただしargument-role graphは未形成。

## Rules
完了項目には、再現コマンド、測定値、複数seed、反証条件、採用・棄却理由を付ける。
