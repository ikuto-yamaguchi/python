# Hypothesis Family Registry

## HF-001 — Surface Span First, Semantic Post-selection

Status: **FROZEN**

Root premise: 文字位置、区間幅、局所shape、局所差分から候補を先に生成し、後段の予測・介入・replay・lesion・圧縮でsemantic unitへ昇格できる。

Observed failure: A〜Eの複数系列で、内部候補やgraphは形成されても未知表現の外部能力が0、またはshuffleと同一。支配的失敗はsemantic unitの初期形成。

Prohibited aliases: cell、role、event、address、trace、node、family、generator、assemblyへの単純名称変更。

Unfreeze condition: surface候補を前提にしない新しい観測信号が、pilotで未知表現上のCorrect-shuffle差を示すこと。

## HF-002 — Compression or Internal Consistency Creates Meaning

Status: **FROZEN**

Root premise: MDL、可逆圧縮、低rank性、欠測補完、内部整合性、削除必要性がsemantic variableやoperationを生む。

Observed failure: 記述長と候補entropyは減少したが、execution、exact binding、未知転移は改善しない。短い全面棄権やsurface共分散を選ぶ。

Unfreeze condition: 圧縮前に外部実行能力が成立し、圧縮により未知転移を保持または改善する証拠。

## HF-003 — Memory Consolidation Before Re-identifiable Semantics

Status: **FROZEN**

Root premise: replay、fast/slow memory、reconsolidation、sleep、interference graphがsemantic addressを誕生させる。

Observed failure: 取得時closed-loopが0のため、保持・干渉・忘却を評価できない。memory structureは形成されてもshuffleとの差がない。

Unfreeze condition: G1を満たす再同定可能unitがA/Cから供給されること。

## HF-004 — Constraint or Graph Relaxation Repairs Surface Candidates into Meaning

Status: **FROZEN**

Root premise: surface候補へenergy、attractor、synergy edge、eigenmode、homotopyを追加すればsemantic basinが形成される。

Observed failure: active集合や収束は変化しても外部能力が0、またはshuffleと同一。誤surface basinを強化する。

Unfreeze condition: semantic identityを持つnodeが先に成立し、その統合・曖昧性解消としてのみ利用すること。

## HF-005 — Behavioral Equivalence Alone Defines Individual Identity

Status: **FROZEN**

Root premise: 複数contextで同じ因果応答を示す対象は、追加の個体履歴なしでも同じsemantic individualとして一意に同定できる。

Observed failure: PR349では完全対称worldに対する網羅介入後も最大144個の自己同型が残り、介入数の増加がindividual identityを一意化しなかった。PR350のbehavior-only acquisitionは0.0000だった。

Allowed residual use: behavioral equivalenceはindividual identityではなく、因果的役割の同値類候補としてのみ利用できる。

Unfreeze condition: symmetry-breaking witnessなしで、双子対象をheld-out表現・別world上でCorrect > shuffle/randomに再同定する証拠。

## AF-001 — Causal-role Equivalence from Cross-context Behavior

Status: **ACTIVE, SCOPE REDUCED**

Question: 異なる表現・介入で同じ予測と選択的変化を生む最小内部原因を、individual identityではなく因果的役割同値類として形成できるか。

Required evidence: prospective + inverse再利用、対象交換へのsupport移動、Correct-shuffle差、未知表現転移。ただし個体識別の証拠には数えない。

## AF-002 — Identity from Active Identifiability

Status: **ACTIVE SUPPORTING EXPLORATION**

Question: 既存候補を区別するqueryではなく、潜在的な同一性仮説そのものを識別可能にする最小観測・行為系列を生成できるか。

Required evidence: query後に新しいcross-form unitが形成され、random queryより未知実行能力が改善すること。完全対称な介入反復だけでは不十分で、対称性を壊す観測channelが必要。

## AF-003 — Symmetry-Breaking Witness Grounding

Status: **ACTIVE PRIORITY**

Root premise: individual identityには因果的役割同値だけでなく、trajectory continuity、不可逆痕跡、個体履歴など置換対称性を壊すwitnessが必要である。意味単位は文字区間を先に候補化せず、raw Japaneseの発話・指示・説明とwitnessの同期から形成される。

Supporting evidence:

- PR349: 因果挙動だけではidentityはworld automorphismまでしか定まらない。網羅介入でも自己同型が残る。
- PR350: behavior-only acquisition 0.0000、trajectory 0.9663、irreversible scar 1.0000、joint witness 1.0000、identity shuffle 0.0236。96件干渉後はtrajectory 0.8333、scar/joint 1.0000。

Current interpretation: synthetic観測側のindividual re-identificationには限定支持。ただし日本語文字列をretrieval keyから除外したpilotであり、semantic identity gate G1は未達。

Required next evidence:

1. raw Japaneseとwitnessの同期からlatent unitを形成する。
2. held-out paraphrase、rename、未知語順、主語省略、複数段落、別領域で再生成する。
3. 同じunitをprospective predictionとinverse queryの双方へ利用する。
4. trajectory shuffle、scar shuffle、identity shuffle、random、behavior-onlyを上回る。
5. witness lesionで対応個体の再同定能力だけが選択的に崩れる。

G1 promotion condition: 上記を少なくとも3 seedで満たし、Correct-shuffle gapがsynthetic worldだけでなく自由日本語・別領域へ転移すること。