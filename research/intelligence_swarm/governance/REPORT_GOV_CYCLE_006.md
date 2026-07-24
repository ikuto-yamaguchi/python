# Governance Cycle 006

## 統合対象

- PR #367: A — Cross-Lexicon Selective Consequence Consensus
- PR #368: B — Cross-Lexicon Selective Consequence Subspace
- PR #369: C — Bidirectional Lesion-Consensus Causal Units
- PR #370: D — Cross-Lexicon Consensus Memory Eligibility

## 外部能力だけの集約

### PR #367

- D1 free joint: Correct 0.1875 / Shuffle 0.0312
- D2 free joint: Correct 0.0660 / Shuffle 0.0312
- D1 inverse: 0.2778 / 0.1285
- D2 inverse: 0.2847 / 0.1111
- 正式進歩gate: 未達

平均的なfactor-selective signalは2 domainで形成されたが、D2自由日本語差は+0.0347であり、全domain・全seed条件を満たさない。

### PR #368

- Consensus channels: 4.67 / 16
- D free: Correct 0.0833 / Shuffle 0.1250
- E free: Correct 0.0000 / Shuffle 0.1250
- F goal-change: Correct 0.0417 / Shuffle 0.1250
- Strict gate: 0 / 3 seed

結果側の共通channelは形成できるが、外部能力はshuffleを下回る条件が複数ある。

### PR #369

- Bidirectional consensus channels: 3.00 / 16
- Strict gate: 0 / 3 seed
- forward、inverse、cycle closureのlesion必要性を要求しても外部能力の符号がdomain間で反転

双方向lesion必要性はsemantic causal unitの十分条件ではない。

### PR #370

- d1 free: 0.1875 / 0.0312
- d2 free: 0.0764 / 0.0208
- d3 free: 0.2431 / 0.0347
- inverseは全domain平均でCorrect > shuffle
- formal memory eligibility: 0 / 3 seed

平均差は強いが、identity・goal lesion符号がdomain × seedで安定せず、同一episode unitの再生成を証明しない。

## 仮説族判定

### HF-009を凍結

**Predefined Consequence Codebook plus Post-selection Creates Semantics**

根本前提:

> 結果fingerprint、factor channel、response orbitなどを先に構成し、consensus、transpose、cycle closure、selective lesionを追加すればsemantic unitを後段選別できる。

この前提はA〜Dの4系列で検証され、内部channelやlesion structureは形成される一方、domain × seed単位の外部能力を成立させなかった。系列横断凍結条件を満たす。

### AF-006を縮小

Cross-Lexicon Selective Consequence Consensusは、semantic birth本線ではなく次へ限定する。

- domain/seed failure patternの診断
- factor混線の検出
- bridge leakage監査
- counterexample生成
- AF-007のbaseline

### AF-007を優先本線へ昇格

**Jointly Emergent Language–World Intervention Diagrams**

固定結果codebookや既成factor channelを置かず、raw Japanese上の局所変換とworld上の局所介入を同時に生成する。言語変換後にworld介入する経路と、world介入後に言語変換する経路が一致する最小変換対をsemantic unit候補とする。

## Stage判断

- S1 Semantic Identity Birth: 継続
- Substage: joint language/world emergenceへ遷移
- G1: 未達
- G2: 未達
- Memory eligibility: 未達
- Dの保存・replay・sleep・forgetting最適化: 凍結継続

## 最大上流ボトルネック

結果channelやfactor slotを先に固定せず、raw Japanese変換とworld介入変換を共同生成し、完全に隠した語彙非共有domainで同一の可換介入図式を再生成すること。

## A〜D再配分

- A: raw Japanese変換候補の創発と隠しdomain再生成
- B: 固定factorなしのworld/goal変換候補創発
- C: language–world交換子残差と因果閉包監査
- D: diagram unitの記憶資格監査のみ
- E: predefined-codebook leakage、domain bridge、seed選択、stage管理

## 次回の進歩条件

2以上の完全語彙非共有domain × 3 seedすべてで、同一の共同生成diagram unitが次を満たすこと。

- prospective target × transition
- inverse query
- counterfactual repair
- 自由日本語
- Correct − shuffle/random >= 0.10
- hidden domainで再生成
- post-treatment、domain bridge、predefined-codebook leakageなし

## 資源・運用

今回のサイクルはメタ統合であり、新しい推論モデルは実装していない。PR #367〜370はいずれも1GB未満の実験であり、弱いスマートフォン実機検証は未達。既存の実験証拠は削除せず保持する。

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
