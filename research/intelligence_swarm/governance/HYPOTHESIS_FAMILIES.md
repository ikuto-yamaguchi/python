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
Status: **ACTIVE PRIORITY**
Root premise: semantic unitは名称・座標・object indexそのものではなく、異なるdomainで保存される選択的結果、失敗修正、inverse応答、non-target保存の共同不変量として形成される。
Required evidence:
1. 学習domainと評価domainで語彙、座標、object index、surface templateを分離。
2. domain対応辞書、共有identity、手書きslot、文字列検索を禁止。
3. before+commandからtargetとtransitionをprospectiveに予測。
4. inverse query、goal変更、failure repair、twin discrimination、non-target保存を同じunitで満たす。
5. Correctをidentity/operation/goal/domain shuffleとrandomへ比較。
6. 3 seedすべてで未知domain Correct > shuffle/random、暫定実質差0.10以上。
G1 promotion condition: prospective・inverse・domain条件を同時に満たし、post-treatment leakageとdomain bridge leakage監査を通過すること。