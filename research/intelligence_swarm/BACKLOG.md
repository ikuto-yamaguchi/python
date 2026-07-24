# Intelligence Swarm Backlog

## P0 — Joint Language–World Intervention Diagram Birth

- A: 結果codebookやidentity/operation/goal channelを先に定義せず、raw Japaneseの言い換え・対象変更・操作変更から局所言語変換候補を生成する。
- A: 片domainで選んだ言語変換規則を、完全に隠した別opaque domainへ適用し、同じworld変換との可換閉包が再生成されるか測る。
- B: 介入前worldと選択的結果から、名称なしの最小world変換・目的変換候補を生成し、Aの言語変換候補と共同競合させる。
- B: identity / operation / goalを既成factorとして採点せず、どの局所変換を変更するとtarget・transition・ranking criterionのどれが変わるかを外部応答から同定する。
- C: 言語変換→world介入とworld介入→言語変換の交換子残差を測り、未知domainで可換図式が閉じる最小単位だけを因果候補にする。
- C: prospective、inverse、counterfactual repair、twin discriminationを同一diagram unitで測り、片方向だけの成功を拒否する。
- D: diagram unitが2以上のopaque domain × 3 seedすべてで外部能力を通るまでmemory eligibilityを拒否する。
- E: predefined result codebook、shared factor channel、domain bridge、seed selection、post-treatment leakageを監査する。

## P0 — Common G1 benchmark v4

- 学習・評価domain間で語彙、座標、object index、surface template、乱数系列、結果符号化基底を分離する。
- 固定identity/operation/goal label、固定結果channel、対応辞書、共有token、共有IDをモデルへ渡さない。
- Correct、language-transform shuffle、world-transform shuffle、diagram-pair shuffle、domain shuffle、randomを同一seedで比較する。
- prospective target selection、transition prediction、inverse query、counterfactual repair、twin discrimination、non-target保存を同じdiagram unitで測る。
- 片domainで選択したunitを完全に隠したdomainへ転送し、再学習なし／少数観測ありを分離報告する。
- held、domain平均、domain別、seed別、unit別を分離し、平均差で失敗unitを隠さない。
- 2以上のopaque domain × 3 seedすべてでCorrect > shuffle/random、実質差0.10以上、同一diagram unit再生成を暫定昇格条件とする。

## P1 — Evidence repair

- PR367〜370へ `root_premise=predefined_consequence_codebook_then_postselect_semantics` を付与する。
- PR367の陽性を `limited factor-selective domain-local grounding` として限定する。
- PR368〜370のchannel/lesion consensusを、semantic progressではなくHF-009反証証拠として登録する。
- track-local evidenceを統合時に主台帳へ取り込み、既存台帳を破壊しない。
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
- 固定結果codebook/channelを先に構成し、consensus・transpose・lesionでsemantic unitへ後段昇格させる方式

## Cycle completion rules

- 実装は必須ではない。メタ分析、評価再設計、仮説族凍結、stage変更も完結サイクルとする。
- 採用、継続、凍結、段階遷移のいずれかを必ず明示する。
- 進歩は未知条件の外部能力とbaseline差、domain/seed/unit consensus、隠しdomain再生成で判定する。
- Retrospective matching、domain-local fit、平均cross-domain signal、固定codebook上のconsensus、再利用可能semantic groundingを混同しない。
- 再現コマンド、複数seed、反証条件、資源量、answer leakage・post-treatment leakage・domain bridge leakage監査を維持する。
