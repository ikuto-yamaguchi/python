# Governance Cycle GOV-003

## Decision

- **Stage:** S1 Semantic Identity Birth を継続
- **Freeze:** HF-006 Post-Treatment Witness Implies Prospective Semantic Identity
- **Continue with reduced scope:** AF-003 Symmetry-Breaking Witness Grounding はretrospective re-identificationに限定
- **Promote:** AF-004 Pre-Treatment Relational Change Grounding
- **G1:** 未達
- **G2:** 未達

## External capability evidence only

### PR352 — A

- Held: Correct 0.2431 / Shuffle 0.1233
- Domain: Correct 0.1128 / Shuffle 0.1181
- Inverse held: 0.1736

Held表現では信号があるが、別domainでは消失し、inverseも弱い。

### PR353 — B

- Held prospective: 0.1500 / Shuffle 0.1437
- Domain: 0.1146 / Shuffle 0.1146
- Goal change: 0.5125 / Shuffle 0.5083
- Failure repair: 0.1292 / Shuffle 0.1250

Operation/goal能力はchance近傍でG2未達。

### PR354 — C

- Held full trajectory: 0.2396
- Held prefix1: 0.1580
- Held prefix2: 0.1892
- Held shuffled full: 0.1337
- Domain full: 0.1476

大きなheld gapは完成したpost-treatment trajectoryに依存する。future censor後は縮小し、別domainはchance近傍。

### PR355 — D

- Full: Correct 0.1944 / Shuffle 0.1319
- Prefix1: 0.1319
- Prefix2: 0.1528
- Memory eligible units: 0

Pre-treatment witnessはacquisition・domain・inverse・cross-form consistencyを同時通過せず、retention評価を解禁できない。

## Family-level interpretation

A、C、Dの3系列で、完成trajectoryや行為後scarを利用した照合と、介入前情報によるprospective identityが分離された。したがって同じ根本前提をHF-006として凍結する。

AF-003は置換対称性を壊すwitnessの必要性とretrospective re-identificationには有効だが、prospective semantic identityの証拠ではない。本線をAF-004へ移す。

## Maximum upstream bottleneck

Raw Japaneseを介入前の対象間関係・履歴prefix・commandへ結び、future outcomeを見ずにtargetとafterを予測し、同じunitを別domainとinverse queryで再生成すること。

## Track reassignment

- A: Japanese-to-pre-treatment relational change unit birth
- B: four-way identity / operation / goal contrast
- C: pre-treatment witness necessity and causal audit
- D: time-indexed eligibility gate only
- E: prospective G1 benchmark and post-treatment leakage audit

## Resource and safety status

入力となったPR352〜355はすべて3 seed、answer leakage禁止、1GB未満を満たす。弱いスマートフォン実機は未検証。

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
