# Intelligence Swarm Backlog

## P0 — Intervention-Born Diagram Identity

- A: raw Japanese/world変換候補を独立に維持し、候補対が異なる結果を予測する最小の発話・観測・行為を生成する。
- A: 外部結果を観測する前に候補を類似度・低rank軸・surprise cluster・failure shapeでfamily化しない。
- B: 固定identity/operation/goal factorを与えず、各候補diagramのtarget・transition・ranking予測差から最小識別行為集合を構成する。
- B: 行為集合の記述長ではなく、外部結果による一意な候補消去と未知表現での再利用能力を最適化する。
- C: Correct intervention、random intervention、action-set shuffle、outcome shuffle、oracle action selectorを分離し、実結果で一方だけが生存する因果必要性を監査する。
- C: 同じ識別行為構造が完全語彙非共有domainで再生成されるか、prospective・inverse・repair・twin discriminationを同一unitで測る。
- D: 外部識別行為で一意に生存し、2以上のopaque domain × 3 seedすべてで再生成されたunitだけをmemory eligibility候補へ通す。
- E: test outcome leakage、oracle action selection、domain bridge、best-seed selectionを監査し、HF-010の言い換え再試行を拒否する。

## P0 — Common G1 benchmark v5

- 学習・評価domain間で語彙、座標、object index、surface template、乱数系列、結果符号化基底を分離する。
- 固定identity/operation/goal label、固定結果channel、対応辞書、共有token、共有IDをモデルへ渡さない。
- 候補生成用データ、介入選択用データ、外部結果観測、final評価を分離し、final正解を介入選択へ使わない。
- Correct minimal intervention、random intervention、action-set shuffle、outcome shuffle、diagram-pair shuffle、domain shuffleを同一seedで比較する。
- 介入前候補数、介入後生存候補数、一意生存率、介入数、oracle gapを測定する。
- prospective target selection、transition prediction、inverse query、counterfactual repair、twin discrimination、non-target保存を同じ生存diagramで測る。
- 片domainで獲得した識別行為構造を完全に隠したdomainへ転送し、再学習なし／少数観測ありを分離報告する。
- 2以上のopaque domain × 3 seedすべてでCorrect > random/action-set shuffle/outcome shuffle、実質差0.10以上を暫定昇格条件とする。

## P1 — Evidence repair

- PR372〜374へ `root_premise=pre_action_similarity_or_error_correspondence_defines_diagram_identity` を付与する。
- PR372のglobal low-rank、PR373のsingle-domain local surprise、PR374のcross-domain failure correspondenceをHF-010反証証拠として登録する。
- PR370のformal memory eligibility 0/3を、下流保存凍結の継続根拠として維持する。
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
- 外部識別行為前にglobal低rank軸、局所surprise cluster、失敗形状類似度でdiagram identityを作る方式

## Cycle completion rules

- 実装は必須ではない。メタ分析、評価再設計、仮説族凍結、stage変更も完結サイクルとする。
- 採用、継続、凍結、段階遷移のいずれかを必ず明示する。
- 進歩は未知条件の外部能力とbaseline差、domain/seed/unit consensus、隠しdomain再生成で判定する。
- 候補消去率、介入数削減、target単体高値、geometry bias、tie-breakingをsemantic progressと混同しない。
- 再現コマンド、複数seed、反証条件、資源量、answer leakage・post-treatment leakage・domain bridge leakage・oracle action leakage監査を維持する。