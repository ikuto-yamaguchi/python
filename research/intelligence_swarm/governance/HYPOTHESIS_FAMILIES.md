# Hypothesis Family Registry

この台帳は名称ではなく根本前提で仮説を管理する。FROZEN族の言い換え再試行は禁止し、外部能力または明示されたunfreeze条件を満たした場合だけ再検討する。

## HF-001 — Surface Span First, Semantic Post-selection
Status: **FROZEN**
Root premise: 文字位置・区間幅・局所shape・局所差分から候補を先に生成し、後段の予測・介入・replay・圧縮で意味へ昇格できる。
Observed failure: A〜Eで未知表現の外部能力が0またはshuffleと同一。

## HF-002 — Compression or Internal Consistency Creates Meaning
Status: **FROZEN**
Root premise: MDL、圧縮、低rank、欠測補完、内部整合性がsemantic variableやoperationを生む。
Observed failure: 記述長は減少したがexecution、exact binding、未知転移は改善しない。

## HF-003 — Memory Consolidation Before Re-identifiable Semantics
Status: **FROZEN**
Root premise: replay、fast/slow memory、reconsolidation、sleep、interference graphがsemantic addressを誕生させる。
Observed failure: 取得時closed-loopが0で保持・忘却を評価できない。
Unfreeze condition: G1を満たす再同定可能unitが供給されること。

## HF-004 — Constraint or Graph Relaxation Repairs Surface Candidates into Meaning
Status: **FROZEN**
Root premise: surface候補へenergy、attractor、synergy edge、eigenmodeを追加すればsemantic basinが形成される。
Observed failure: 外部能力が0またはshuffleと同一。

## HF-005 — Behavioral Equivalence Alone Defines Individual Identity
Status: **FROZEN**
Root premise: 同じ因果応答を示す対象は追加の個体履歴なしでも同じindividualとして同定できる。
Observed failure: PR349で網羅介入後も自己同型が残り、PR350 behavior-only acquisitionは0。
Allowed residual use: 因果的役割同値類候補。

## HF-006 — Post-Treatment Witness Implies Prospective Semantic Identity
Status: **FROZEN**
Root premise: 完成trajectoryや行為後scarとの対応をbefore+commandからのprospective能力として扱える。
Observed failure: PR352〜355でfuture censor、別domain、inverse、eligibilityを通過しない。
Allowed residual use: retrospective re-identification。

## HF-007 — Structural Equivariance or Factorization Alone Creates Cross-Domain Semantics
Status: **FROZEN**
Root premise: relation、座標可換性、identity/operation/goal分離だけでcross-domain semanticsが成立する。
Observed failure: PR357〜360で別domainのCorrect-shuffle差が消失または逆転し、eligible unit 0。
Allowed residual use: 座標/index依存除去と混線診断。

## HF-008 — Single-Domain or Averaged Consequence Signal Defines Reusable Semantics
Status: **FROZEN**
Root premise: 一つのdomain、一部seed、domain平均のconsequence signalで再利用可能unitを認定できる。
Observed failure: PR362〜365でdomain・seed間再現性がなくformal eligibility未達。
Allowed residual use: 候補接地信号探索、domain難度診断、反例生成。

## HF-009 — Predefined Consequence Codebook plus Post-selection Creates Semantics
Status: **FROZEN**
Root premise: 固定結果fingerprint、factor channel、response orbitを先に作り、consensus、transpose、cycle closure、lesionで意味へ昇格できる。
Observed failure: PR367〜370で内部channelは形成されても外部能力符号がdomain/seed間で不安定、formal eligibility 0。
Allowed residual use: failure diagnosis、counterexample construction、bridge leakage audit。

## HF-010 — Pre-Action Similarity or Error Correspondence Defines Diagram Identity
Status: **FROZEN**
Root premise: 外部識別前でもglobal低rank軸、local surprise、cross-domain failure similarity、交換子残差形状からdiagram identityを対応付けられる。
Observed failure: PR372〜374でjoint/inverseが0またはshuffle優位。
Allowed residual use: 候補生成と失敗多様性診断。identity確定には使わない。

## HF-011 — Selector or Version-Space Collapse Creates Semantics without Candidate Support
Status: **FROZEN**
Root premise: 正しいsemantic candidateが候補集合に存在しなくても、active selector、joint entropy、version-space collapse、oracle action、intervention survivalの改善で意味単位が成立する。
Observed failure:
- PR375: Correct候補も3 seed中2 seedで全滅、formal eligibility 0。
- PR376: hidden自由日本語の局所陽性が未知語順・複数段落・Rename・全seedへ再現せずstrict gate 0/3。
- PR378: Joint selectorとWorld-onlyが同一で、oracle selectorもhidden能力を改善しない。
- PR379/381: residual weightまたは固定interaction headを追加してもRandom/Shuffleが同等以上。
Allowed residual use: candidate-support監査、oracle upper bound、residual-born候補の資格認定。

## HF-012 — Bridge-Free Opaque Zero-Shot Is a Valid Semantic Capability Gate
Status: **FROZEN**
Root premise: 完全語彙非共有domainへ外部接地witness、共有token、対応辞書、shared IDを一切与えなくてもhidden token→meaning対応をchance以上に同定でき、その失敗をsemantic birth機構の反証として扱える。
Observed failure:
- PR382: 8-way対応の任意置換がlearnerから観測同値。理論上限chance 0.125、実測0.1160、観測同値pair 720/720。
- 接地観測0/1/2/4/8件で精度0.1160/0.2271/0.3378/0.5559/1.0となり、外部witnessが置換対称性を破ることを確認。
- PR383〜385: oracle構造下では少数witnessで一意化できるため、bridge 0失敗と候補生成能力不足を分離する必要がある。
Prohibited aliases: zero-shot opaque transfer、bridge-free semantic rebirth、完全未知語彙の無観測一般化をG1/G2必須条件として再導入すること。chance超えbest seedを進歩と呼ぶこと。
Allowed residual use: 理論chance監査、漏洩検出、witness必要量の下限測定。
Unfreeze condition: 外部世界またはデータ生成過程に置換対称性を破る観測可能な非対称性が存在することを形式的・実測的に示すこと。

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
Current interpretation: relation necessity、座標/index依存除去、factor混線診断に限定。

## AF-005 — Cross-Domain Consequence-Invariant Grounding
Status: **ACTIVE, CANDIDATE-SIGNAL SOURCE**
Current interpretation: 候補信号と反例生成に限定。

## AF-006 — Cross-Lexicon Selective Consequence Consensus
Status: **ACTIVE, DIAGNOSTIC SCOPE**
Current interpretation: domain/seed failure pattern、factor混線、bridge leakage診断に限定。

## AF-007 — Jointly Emergent Language–World Intervention Diagrams
Status: **ACTIVE, PRINCIPLE RETAINED**
Root premise: raw Japanese局所変換とworld局所介入を相互拘束しながら共同生成する。
Current interpretation: 共同生成原理は維持。事前類似対応はHF-010、unsupported candidate選別はHF-011として凍結。

## AF-008 — Intervention-Born Diagram Identity from Minimal Discriminating Action Sets
Status: **ACTIVE, QUALIFICATION AND AUDIT SCOPE**
Root premise: 候補identityは実介入結果による一意生存後に初めて認める。
Current interpretation: candidate birth原理ではなく、候補資格、oracle gap、action leakage、survival監査に使用する。

## AF-009 — Intervention-Residual Joint Candidate Birth
Status: **ACTIVE, SUPPORTING CANDIDATE GENERATION**
Root premise: 全候補不適合episodeのlanguage/world residualから新しい局所変換候補を共同生成する。
Current interpretation: bridge 0同定不能条件での主探索から外し、AF-010で同定可能なwitness条件が確立した後の候補生成補助として比較する。

## AF-010 — Minimal-Witness Joint Segmentation–Arity–Orbit Grounding
Status: **ACTIVE PRIORITY**
Root premise: 意味単位はbridge 0で推測するのではなく、raw Japaneseのsegmentation、対象／操作／関係factorization、可変arity、causal mappingの共同version spaceを、learnerが選んだ最小外部witnessで分割することにより誕生する。
Required evidence:
1. 固定ontology、対応辞書、shared token/ID、oracle token境界、oracle factorization、oracle arityを正式条件で使わない。
2. raw Japaneseの複数segmentation、unary/binary以上のarity、target/operation/relation mappingを同時に保持する。
3. Active / Random witness、boundary shuffle、factor shuffle、arity shuffle、outcome shuffle、oracle-structure upper boundを比較する。
4. calibration witnessとfinal評価を分離し、final outcomeをwitness選択・構造生成・rankingへ使わない。
5. 最小witness後、接地未使用token、Rename、未知語順、主語省略、複数段落、自由日本語、未観測factor組合せでprospective・inverse・counterfactual composition/repairを評価する。
6. 重複しない第二witness集合でも同じsegmentation・arity・mappingへ再収束し、矛盾witnessを上書きせずconflictとして隔離する。
7. 2以上のopaque domain × 3 seedすべてでCorrectが全対照を0.10以上上回る。
G1/G2 promotion condition: 同一のraw-learned unitが上記を満たし、oracle-structure leakage、calibration-after leakage、domain bridge、seed selection bias監査を通過すること。