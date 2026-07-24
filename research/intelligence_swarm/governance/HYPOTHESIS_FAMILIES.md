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
Observed failure:
- PR352: held条件では差が出たが別domainとinverseはchance近傍。
- PR354: 完成trajectoryでheld 0.2396対shuffle 0.1337だが、prefix1 0.1580、prefix2 0.1892へ縮小し、別domainはchance近傍。
- PR355: pre-treatment prefixからacquisition・domain・inverse・cross-form consistencyを同時通過するeligible unitは0。
Prohibited aliases: future trace completion、scar-conditioned selection、completed-trajectory synchronyをprospective groundingと呼ぶ再試行。
Allowed residual use: retrospective re-identification、episode監査、取得後の照合。
Unfreeze condition: 介入後featureを完全にcensorし、未知表現・別domainのprospective predictionとinverse queryでCorrect > shuffle/randomを示すこと。

## AF-001 — Causal-role Equivalence from Cross-context Behavior
Status: **ACTIVE, SCOPE REDUCED**
Question: individual identityではなく因果的役割同値類を形成できるか。

## AF-002 — Identity from Active Identifiability
Status: **ACTIVE SUPPORTING EXPLORATION**
Question: 潜在同一性を識別可能にする最小観測・行為系列を生成できるか。

## AF-003 — Symmetry-Breaking Witness Grounding
Status: **ACTIVE, RETROSPECTIVE SCOPE**
Root premise: trajectory continuity、不可逆痕跡、個体履歴は置換対称性を壊す。
Evidence: PR349/350、およびPR352のheld retrospective signal。
Current interpretation: synthetic観測側および完成trajectoryによるretrospective re-identificationには限定支持。G1通過には数えない。

## AF-004 — Pre-Treatment Relational Change Grounding
Status: **ACTIVE PRIORITY**
Root premise: semantic identityは、介入後の完成witnessではなく、介入前に観測可能な対象間関係・履歴prefixとcommandが予測する選択的な将来変化として形成される。
Required evidence:
1. candidate featureは介入前時点のみ。
2. before+commandからtargetとafterをprospectiveに予測。
3. held paraphrase、rename、未知語順、主語省略、複数段落、自由日本語、別domainで再生成。
4. inverse query、対象交換時support移動、non-target保存を同じunitで満たす。
5. Correctがidentity/relation/temporal shuffleとrandomを3 seed以上で実質的に上回る。
6. same identity/different operation等の四方向対照でidentity・operation・goalを分離。
G1 promotion condition: 上記のprospective・inverse・domain条件を同時に満たし、post-treatment leakage監査を通過すること。