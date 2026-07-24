# Intelligence Swarm Backlog

## P0 — Intervention-Residual Joint Candidate Birth

- A: 既存候補が全滅するcalibration episodeから、raw Japanese側の説明不能残差とworld側の予測―観測残差を抽出する。
- A: 文字span、固定factor、固定結果channelへ戻らず、残差を同時に減らす最小language/world局所変換対を生成する。
- B: oracle candidate-support監査で、target・transition・goalのどの成分が候補集合に欠落しているかを分離する。
- B: selector改善ではなく、欠落成分を新生するoperation/goal candidate birthを比較する。
- C: residual-born候補を別episode・別opaque domainへ転送し、prospective・inverse・repairをCorrect / residual shuffle / pair shuffle / outcome shuffleで監査する。
- C: calibration afterは候補birthに利用可能だが、final評価afterとtest outcomeは完全に隔離する。
- D: residual-born候補が複数domain × 全seedで再生成され、外部介入で一意生存した場合だけmemory eligibility候補へ通す。
- E: after leakage、oracle candidate leakage、domain bridge、best-seed selection、residual label leakageを監査する。

## P0 — Common G1 benchmark v6

- 候補生成用episode、residual birth用calibration介入、候補資格監査、final評価を4分割する。
- 学習・評価domain間で語彙、座標、object index、surface template、乱数系列、結果符号化基底を分離する。
- 固定identity/operation/goal label、固定結果channel、対応辞書、共有token、共有IDをモデルへ渡さない。
- Existing-candidate selector、Random birth、Language-residual-only、World-residual-only、Joint residual birth、Residual shuffle、Pair shuffle、Outcome shuffle、Oracle candidate-supportを比較する。
- birth前候補数、birth数、独立episode再利用率、hidden-domain再生成率、AF-008 survival率を測定する。
- prospective target selection、transition prediction、inverse query、counterfactual repair、twin discrimination、non-target保存を同じborn unitで測る。
- 2以上のopaque domain × 3 seedすべてでCorrect > baselines、実質差0.10以上を暫定昇格条件とする。

## P1 — Evidence repair

- PR375、PR376、PR378へ `root_premise=selector_or_version_space_collapse_succeeds_without_candidate_support` を付与する。
- HF-011の根拠として、PR375のCorrect候補全滅、PR376のstrict gate 0/3、PR378のJoint=World-onlyおよびoracle失敗を登録する。
- track-local evidenceを統合時に主台帳へ安全に取り込み、既存台帳を破壊しない。
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
- 正しい候補が候補集合に存在しないまま、active selector、joint entropy、version-space collapse、oracle actionだけを改良する方式

## Cycle completion rules

- 実装は必須ではない。メタ分析、評価再設計、仮説族凍結、stage変更も完結サイクルとする。
- 採用、継続、凍結、段階遷移のいずれかを必ず明示する。
- 進歩は未知条件の外部能力とbaseline差、domain/seed/unit consensus、隠しdomain再生成で判定する。
- 候補数、残差低下、介入数削減、target単体高値、oracleだけの成功をsemantic progressと混同しない。
- 再現コマンド、複数seed、反証条件、資源量、answer leakage・post-treatment leakage・domain bridge leakage・oracle leakage監査を維持する。
