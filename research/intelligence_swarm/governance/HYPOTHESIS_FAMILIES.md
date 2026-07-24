# Hypothesis Family Registry

## HF-001 — Surface Span First, Semantic Post-selection
Status: **FROZEN**
Root premise: 文字位置、区間幅、局所shape、局所差分から候補を先に生成し、後段の予測・介入・replay・lesion・圧縮でsemantic unitへ昇格できる。
Observed failure: A〜Eで未知表現の外部能力が0またはshuffleと同一。
Unfreeze condition: surface候補を前提にしない観測信号が未知表現上のCorrect-shuffle差を示すこと。

## HF-002 — Compression or Internal Consistency Creates Meaning
Status: **FROZEN**
Root premise: MDL、可逆圧縮、低rank性、欠測補完、内部整合性、削除必要性がsemantic variableやoperationを生む。
Observed failure: 記述長は減少したがexecution、exact binding、未知転移は改善しない。
Unfreeze condition: 外部実行能力成立後に圧縮が未知転移を保持または改善する証拠。

## HF-003 — Memory Consolidation Before Re-identifiable Semantics
Status: **FROZEN**
Root premise: replay、fast/slow memory、reconsolidation、sleep、interference graphがsemantic addressを誕生させる。
Observed failure: 取得時closed-loopが0で保持・干渉・忘却を評価できない。
Unfreeze condition: G1を満たす再同定可能unitが供給されること。

## HF-004 — Constraint or Graph Relaxation Repairs Surface Candidates into Meaning
Status: **FROZEN**
Root premise: surface候補へenergy、attractor、synergy edge、eigenmode、homotopyを追加すればsemantic basinが形成される。
Observed failure: 外部能力が0またはshuffleと同一。
Unfreeze condition: semantic identityを持つnodeが先に成立し、その統合用途に限定すること。

## HF-005 — Behavioral Equivalence Alone Defines Individual Identity
Status: **FROZEN**
Root premise: 同じ因果応答を示す対象は追加の個体履歴なしでも同じindividualとして同定できる。
Observed failure: PR349で網羅介入後も自己同型が残り、PR350 behavior-only acquisitionは0.0000。
Allowed residual use: 因果的役割同値類候補としてのみ利用。

## HF-006 — Post-Treatment Witness Implies Prospective Semantic Identity
Status: **FROZEN**
Root premise: 完成trajectoryや行為後scarと日本語の対応で得た再同定能力を、before+commandからのprospective identity能力として扱える。
Observed failure: PR352〜355でfuture censor、別domain、inverse、eligibility gateを通過しない。
Allowed residual use: retrospective re-identification、episode監査、取得後の照合。

## HF-007 — Structural Equivariance or Factorization Alone Creates Cross-Domain Semantics
Status: **FROZEN**
Root premise: 介入前relation、座標変換可換性、identity/operation/goal因子分離だけでcross-domain semanticsが成立する。
Observed failure: PR357〜360で別domain Correct-shuffle差が消失または逆転し、eligible unit 0。
Allowed residual use: coordinate/index依存除去、混線診断、必要条件ablation。

## HF-008 — Single-Domain or Averaged Consequence Signal Defines Reusable Semantics
Status: **FROZEN**
Root premise: 一つのdomain、一部seed、domain平均のconsequence signalで再利用可能semantic unitを認定できる。
Observed failure: PR362〜365でdomain・seed間再現性がなくformal eligibility未達。
Allowed residual use: 候補接地信号探索、domain difficulty診断、反例生成。

## HF-009 — Predefined Consequence Codebook plus Post-selection Creates Semantics
Status: **FROZEN**
Root premise: 固定結果fingerprint、factor channel、response orbitを先に作り、consensus、transpose、cycle closure、lesionで意味へ昇格できる。
Observed failure: PR367〜370で内部channelは形成されても外部能力符号がdomain/seed間で不安定、formal eligibility 0。
Allowed residual use: failure diagnosis、counterexample construction、bridge leakage audit。

## HF-010 — Pre-Action Similarity or Error Correspondence Defines Diagram Identity
Status: **FROZEN**
Root premise: 外部識別行為前でもglobal低rank軸、local surprise、cross-domain failure similarity、交換子残差形状からdiagram identityを対応付けられる。
Observed failure: PR372〜374でjoint/inverseが0またはshuffle優位。類似度はgeometry、tie、未学習、hash衝突をsemantic identityと区別できない。
Allowed residual use: 候補生成、失敗多様性診断、識別行為候補初期化。identity確定には使わない。

## HF-011 — Selector or Version-Space Collapse Creates Semantics without Candidate Support
Status: **FROZEN**
Root premise: 正しいsemantic candidateが初期候補集合に含まれていなくても、active action selection、language/world joint entropy、version-space collapse、oracle selector、intervention survivalを改善すれば意味単位が成立する。
Observed failure:
- PR375: outcome shuffle候補は排除できたがCorrect候補も3 seed中2 seedで全滅し、formal memory eligibility 0。
- PR376: hidden d3自由日本語に局所陽性は出たが未知語順・複数段落・Rename・d1・全seedへ再現せずstrict gate 0/3。
- PR378: Joint selectorとWorld-onlyが全条件で完全同一。言語entropyは観測順位を変えず、oracle selectorでもhidden-domain prospective/inverse/goal/repairは改善しない。
Prohibited aliases: joint version-space collapse、language-conditioned entropy selection、better active query、oracle action optimization、survival-only certificationを、candidate-support監査なしにsemantic birthと呼ぶ再試行。
Allowed residual use: 候補集合の十分性監査、oracle upper bound、action leakage検査、残差birth後の資格認定。
Unfreeze condition: residual-born候補が複数opaque domain・全seedで外部能力を満たした後、その候補の選択・資格監査用途としてのみ再評価する。

## AF-001 — Causal-role Equivalence from Cross-context Behavior
Status: **ACTIVE, SCOPE REDUCED**
Question: individual identityではなく因果的役割同値類を形成できるか。

## AF-002 — Identity from Active Identifiability
Status: **ACTIVE SUPPORTING EXPLORATION**
Question: 潜在同一性を識別可能にする最小観測・行為系列を生成できるか。

## AF-003 — Symmetry-Breaking Witness Grounding
Status: **ACTIVE, RETROSPECTIVE SCOPE**
Root premise: trajectory continuity、不可逆痕跡、個体履歴は置換対称性を壊す。
Current interpretation: retrospective re-identificationには限定支持。G1通過には数えない。

## AF-004 — Pre-Treatment Relational Change Grounding
Status: **ACTIVE, NECESSARY-CONDITION DIAGNOSTIC**
Root premise: 介入前関係とcommandが選択的将来変化を予測する。
Current interpretation: relation necessity、座標/index依存除去、factor混線診断に限定。

## AF-005 — Cross-Domain Consequence-Invariant Grounding
Status: **ACTIVE, CANDIDATE-SIGNAL SOURCE**
Root premise: semantic unitをdomain間で保存される選択的結果・inverse・repairの共同不変量として探す。
Current interpretation: 候補信号と反例生成に限定。

## AF-006 — Cross-Lexicon Selective Consequence Consensus
Status: **ACTIVE, DIAGNOSTIC SCOPE**
Root premise: 語彙非共有domain間でfactor-selective response/lesion signatureを比較する。
Current interpretation: domain/seed failure pattern、factor混線、bridge leakage診断に限定。

## AF-007 — Jointly Emergent Language–World Intervention Diagrams
Status: **ACTIVE, PRINCIPLE RETAINED**
Root premise: raw Japanese局所変換とworld局所介入を相互拘束しながら共同生成する。
Current interpretation: 共同生成という上位方針を維持。事前類似対応はHF-010、既存候補選別だけの方式はHF-011として凍結。

## AF-008 — Intervention-Born Diagram Identity from Minimal Discriminating Action Sets
Status: **ACTIVE, QUALIFICATION AND AUDIT SCOPE**
Root premise: 候補identityは実介入結果による一意生存後に初めて認める。
Current interpretation: 既存候補からsemantic unitをbirthする主原理としてはHF-011により凍結。residual-born候補の資格認定、oracle gap、action leakage、survival監査として維持する。

## AF-009 — Intervention-Residual Joint Candidate Birth
Status: **ACTIVE PRIORITY**
Root premise: 全候補がcalibration介入結果を説明できないepisodeをbirth triggerとし、raw Japaneseの説明不能残差とworldの予測―観測残差から、新しい局所language/world変換候補を共同生成する。
Required evidence:
1. 文字span、固定factor label、固定結果codebook、domain辞書、共有token/IDを用いない。
2. 候補生成、calibration介入、residual birth、資格監査、final評価を分離する。
3. Existing-candidate selector、Random birth、Language-residual-only、World-residual-only、Joint residual birth、Residual shuffle、Pair shuffle、Outcome shuffle、Oracle candidate-supportを比較する。
4. calibration afterはresidual計算にのみ利用し、final after/test outcomeをbirth・rankingへ使用しない。
5. born candidateが独立episodeと完全に隠したopaque domainでprospective target×transition、inverse、counterfactual repairを同一unitとして説明する。
6. born candidateがAF-008の実介入一意生存監査を通る。
7. 2以上のopaque domain × 3 seedすべてでCorrect > baselines、暫定実質差0.10以上。
G1 promotion condition: 同一のresidual-born unitが上記を満たし、after leakage、oracle candidate leakage、domain bridge leakage、seed selection bias監査を通過すること。
