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
Root premise: 介入前relation、座標変換可換性、identity/operation/goal因子分離を満たせば、追加のcross-domain接地信号なしでも同じsemantic unitを別語彙・別sensor domainへ再生成できる。
Observed failure:
- PR357: domain joint Correct 0.0625 = shuffle 0.0625。
- PR358: heldの一部以外はchance近傍で、自由日本語Factorized 0.0000 < shuffle 0.0556、domain差も小さい。
- PR359: domain Equivariant 0.0389 = shuffle 0.0389。
- PR360: domain joint Correct 0.0500 < shuffle 0.0667、strict seed pass 0/3、eligible unit 0。
Prohibited aliases: paired-coordinate equivariance、anonymous factor separation、relation-only prospective bindingを、cross-domain semantic groundingと呼ぶ再試行。
Allowed residual use: coordinate/index依存除去、混線診断、必要条件のablation。
Unfreeze condition: domain対応辞書・共有IDなしで、未知domainのprospective target×transitionとinverse queryがCorrect > shuffle/randomを3 seedすべてで実質的に示すこと。

## HF-008 — Single-Domain or Averaged Consequence Signal Defines Reusable Semantics
Status: **FROZEN**
Root premise: 一つのopaque domain、一部seed、またはdomain平均でconsequence fingerprintがCorrect > shuffleを示せば、同じsemantic unitが別domainでも再生成されたとみなせる。
Observed failure:
- PR362: domain-local held差は+0.0347だがrename 0、未知語順はshuffle未満、第二domainほぼchance、正方向2/3 seed。
- PR363: 強いprospective/inverse差はあるが日本語中核表現を一部共有し、完全語彙非共有を未証明。
- PR365: opaque Eはheld 0.1181対0.0243だが、opaque D自由日本語は0.0417対0.0521。strict eligibilityはD 0/3、E 1/3 seed。
Prohibited aliases: domain-local rebirth、mean cross-domain accuracy、best-domain evidence、positive-seed selectionをcross-domain semantic identityまたはmemory eligibilityと呼ぶこと。
Allowed residual use: 候補接地信号の探索、domain difficulty診断、反例生成、次のconsensus testの初期化。
Unfreeze condition: 2以上の完全語彙非共有domain × 3 seedすべてでprospective・inverse・自由日本語がCorrect > shuffle/randomを実質差0.10以上で示し、factor-selective lesion signatureがdomain間で同符号となること。

## HF-009 — Predefined Consequence Codebook plus Post-selection Creates Semantics
Status: **FROZEN**
Root premise: 結果fingerprint、identity/operation/goal channel、response orbitなどの固定codebookを先に作り、cross-domain consensus、transpose近似、cycle closure、selective lesionで後段選別すればsemantic unitへ昇格できる。
Observed failure:
- PR367: 2 domain平均では正方向だがD2自由日本語差は+0.0347で、全domain・全seed条件を通らない。
- PR368: consensus channel 4.67/16を形成してもD/E freeとF goal-changeでCorrect < shuffle、strict gate 0/3。
- PR369: bidirectional lesion consensus channel 3/16を形成してもforward・inverse・cycle closureの外部能力符号がdomain間で反転、strict gate 0/3。
- PR370: 3 domain平均のprospective/inverse差はあるがidentity/goal lesion符号がdomain × seedで一致せず、formal eligibility 0/3。
Prohibited aliases: fixed response codebook、consequence subspace、lesion-transpose code、consensus orbitを先に置き、選別条件だけを増やしてsemantic birthと呼ぶ再試行。
Allowed residual use: failure diagnosis、counterexample construction、bridge leakage audit、共同創発方式のbaseline。
Unfreeze condition: 固定codebookなしでlanguage transformationとworld interventionを共同生成し、隠しdomainで同一unitのprospective・inverse・counterfactual能力が成立した後、その圧縮・監査用途としてのみ再評価する。

## HF-010 — Pre-Action Similarity or Error Correspondence Defines Diagram Identity
Status: **FROZEN**
Root premise: 外部識別行為で候補の正誤を確定する前でも、global低rank共同軸、single-domain surprise cluster、cross-domain failure similarity、交換子残差形状などからlanguage/world diagram identityを対応付けられる。
Observed failure:
- PR372: global raw language/world low-rank operatorはjointとinverseがほぼ0で、異なる変化因子の平均軸へ縮退。
- PR373: local surprise diagramはhidden domainのprospective/inverseが0で、world shuffleがCorrectを大幅に上回る条件が複数。
- PR374: cross-domain failure correspondenceでもjoint/inverseは全条件0。hidden domain自由日本語・未知語順・複数段落でshuffleがCorrectを上回る。
Prohibited aliases: global joint axis、local surprise square、failure-correspondence family、residual-shape matching、nearest counterexample pairingを、外部識別証拠なしにsemantic identityまたはcausal diagram identityと呼ぶ再試行。
Allowed residual use: 候補生成、失敗多様性診断、識別行為候補の初期化。identity確定には使わない。
Unfreeze condition: 類似度・誤差形状で事前対応付けせず、test正解から独立に選んだ識別行為の実結果で候補が一意に生存し、そのdiagramが複数opaque domain・全seedで外部能力を満たすこと。

## AF-001 — Causal-role Equivalence from Cross-context Behavior
Status: **ACTIVE, SCOPE REDUCED**
Question: individual identityではなく因果的役割同値類を形成できるか。

## AF-002 — Identity from Active Identifiability
Status: **ACTIVE SUPPORTING EXPLORATION**
Question: 潜在同一性を識別可能にする最小観測・行為系列を生成できるか。

## AF-003 — Symmetry-Breaking Witness Grounding
Status: **ACTIVE, RETROSPECTIVE SCOPE**
Root premise: trajectory continuity、不可逆痕跡、個体履歴は置換対称性を壊す。
Current interpretation: synthetic観測側および完成trajectoryによるretrospective re-identificationには限定支持。G1通過には数えない。

## AF-004 — Pre-Treatment Relational Change Grounding
Status: **ACTIVE, NECESSARY-CONDITION DIAGNOSTIC**
Root premise: 介入前に観測可能な対象間関係とcommandが選択的な将来変化を予測する。
Current interpretation: relation necessity、座標/index依存除去、factor混線診断には有効だが、cross-domain semantic identityの十分条件ではない。

## AF-005 — Cross-Domain Consequence-Invariant Grounding
Status: **ACTIVE, CANDIDATE-SIGNAL SOURCE**
Root premise: semantic unitは名称・座標・object indexそのものではなく、異なるdomainで保存される選択的結果、失敗修正、inverse応答、non-target保存の共同不変量として形成される。
Current interpretation: 有望な結果指紋信号は得られたが、domain/seed consensus不足。単独ではG1通過に使わず、反例生成と共同創発候補の監査に限定する。

## AF-006 — Cross-Lexicon Selective Consequence Consensus
Status: **ACTIVE, DIAGNOSTIC SCOPE**
Root premise: 完全語彙非共有domain間でidentity / operation / goal / wording介入への選択的responseまたはlesion signatureを比較する。
Current interpretation: PR367〜370により固定codebook上のconsensusはsemantic birthの十分条件ではない。domain/seed failure pattern、factor混線、bridge leakageの診断に限定する。

## AF-007 — Jointly Emergent Language–World Intervention Diagrams
Status: **ACTIVE, PRINCIPLE RETAINED / MATCHING SUBFAMILY FROZEN**
Root premise: semantic unitを既成の文字span、結果channel、factor slotから選ばず、raw Japanese上の局所変換とworld上の局所介入を同時に生成し、言語変換→world介入とworld介入→言語変換の可換図式として形成する。
Current interpretation: 共同生成という上位方針は維持する。ただし外部識別行為前のglobal軸・surprise cluster・failure correspondenceによる事前対応付けはHF-010として凍結。

## AF-008 — Intervention-Born Diagram Identity from Minimal Discriminating Action Sets
Status: **ACTIVE PRIORITY**
Root premise: 候補diagramのidentityは類似度で事前に与えず、候補対が異なる結果を予測する最小行為集合をtest正解から独立に選び、実際の外部結果で一方だけが生存したときに初めて形成する。
Required evidence:
1. 固定identity/operation/goal label、固定結果codebook、domain対応辞書、共有token、共有IDを用いない。
2. 候補生成、識別行為選択、外部結果観測、final評価をデータ分離する。
3. Correct minimal intervention、random intervention、action-set shuffle、outcome shuffle、oracle action selectorを比較する。
4. 介入後に一意に生存した同じdiagramでprospective target×transition、inverse query、counterfactual repair、twin discriminationを満たす。
5. 片domainで得た識別行為構造が完全に隠したopaque domainでも再生成される。
6. 2以上のopaque domain × 3 seedすべてでCorrect > random/action-set shuffle/outcome shuffle、暫定実質差0.10以上。
G1 promotion condition: 同一のintervention-born diagramが上記を満たし、test outcome leakage、oracle action leakage、domain bridge leakage、seed selection bias監査を通過すること。