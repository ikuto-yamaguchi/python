# Intelligence Swarm Backlog

## P0 — Cross-Lexicon Selective Consequence Consensus

- A: 2以上の完全語彙非共有domainで、同じidentity / operation / goal / wording介入に同じ選択的response signatureを返す発話—観測unitを形成する。
- A: 単一domain内の平均精度ではなく、domainごとのunit再生成率と全seed consensusを報告する。
- B: identityだけ、operationだけ、goalだけ、wordingだけを変える四方向反例を生成し、対応channel以外が不変か監査する。
- C: generic ensemble disagreementを使わず、期待cross-domain invariance gainとfactor-selective responseで観測・介入を選ぶ。
- D: 2 domain × 3 seedの全条件でprospective / inverse / free Japanese / lesion sign consensusを通るunitだけをmemory eligibleとする。
- E: domain bridge leakage、共有token、共通template、同一乱数系列、結果符号化の暗黙対応を監査する。

## P0 — Common G1 benchmark v3

- 学習・評価の各domainで語彙、座標、object index、surface template、乱数系列を分離する。
- Correct、identity shuffle、operation shuffle、goal shuffle、wording shuffle、domain shuffle、randomを同一seedで比較する。
- prospective target selection、transition prediction、inverse query、twin discrimination、failure repair、non-target保存を同じunitで測る。
- identity / operation / goal / wording channelを個別lesionし、対応能力だけが崩れるか測る。
- held、domain平均、domain別、seed別を分離報告し、平均差で失敗domainを隠さない。
- post-treatment feature、domain対応辞書、共有ID、共有token、answer leakageを自動検査する。
- 2以上のopaque domain × 3 seedすべてでCorrect > shuffle/random、実質差0.10以上、lesion符号一致を暫定昇格条件とする。

## P1 — Evidence repair

- PR362〜365へ `root_premise=consequence_signal_without_cross_domain_seed_consensus` を付与する。
- PR363の陽性を `limited consequence grounding with partial lexical bridge` として限定する。
- PR365の干渉低下は正式なcatastrophic forgettingではなく `domain_seed_dependent_acquisition_instability` として保持する。
- PR364のactive selectionは `generic disagreement not factor-selective` として反例登録する。
- track-local evidenceを次の統合時に主台帳へ取り込む。
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
- 単一domain、domain平均、一部seedだけのconsequence signalを再利用可能semantic unitとみなす方式
- generic prediction disagreement最大化だけでsemantic factorを識別できるとみなす方式

## Cycle completion rules

- 実装は必須ではない。メタ分析、評価再設計、仮説族凍結、stage変更も完結サイクルとする。
- 採用、継続、凍結、段階遷移のいずれかを必ず明示する。
- 進歩は未知条件の外部能力とbaseline差、domain/seed consensus、選択的lesionで判定する。
- Retrospective matching、domain-local fit、平均cross-domain signal、再利用可能semantic groundingを混同しない。
- 再現コマンド、複数seed、反証条件、資源量、answer leakage・post-treatment leakage・domain bridge leakage監査を維持する。