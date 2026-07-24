# Governance Cycle GOV-005

## Decision

**Continue S1 / Freeze HF-008 / Promote AF-006**

- S1 Semantic Identity Birth: 継続
- G1 Semantic Identity Gate: 未達
- G2 Operation/Goal Gate: 未達
- Formal memory eligibility: 未達
- HF-008 Single-Domain or Averaged Consequence Signal Defines Reusable Semantics: 凍結
- AF-005 Cross-Domain Consequence-Invariant Grounding: 候補生成源へ縮小
- AF-006 Cross-Lexicon Selective Consequence Consensus: 優先本線へ昇格

## External evidence only

### PR #362 — A

- Held joint: Correct 0.0694 / Shuffle 0.0347
- Rename: 0.0139 / 0.0139
- Unknown word order: 0.0208 / 0.0347
- Inverse: 0.2500 / 0.2431
- Second opaque domain free: 0.0139 / 0.0069
- Positive held gap: 2/3 seeds

Interpretation: 少数観測によるdomain-local grounding信号。cross-domain semantic identityではない。

### PR #363 — B

- Held joint: 0.2824 / 0.0694
- Cross-domain B joint: 0.1250 / 0.0324
- Cross-domain C joint: 0.1204 / 0.0509
- Cross-domain B inverse: 0.3333 / 0.1065
- Cross-domain C inverse: 0.2778 / 0.1296

Interpretation: 結果指紋は現在最も強い候補信号。ただしdomain間で日本語中核表現を一部共有しており、完全語彙非共有の証拠ではない。

### PR #364 — C

- Budget 16 held: Active 0.0833 / Random 0.1076 / Shuffle 0.0694
- Budget 16 inverse: Active 0.3056 / Random 0.2778 / Shuffle 0.2361
- Budget 16 second domain: Active 0.0729 / Random 0.0729 / Shuffle 0.0451

Interpretation: generic ensemble disagreementはRandomを安定して上回らず、identity / operation / goal / wordingのどの因子を識別する観測かを分けない。

### PR #365 — D

Opaque domain D:

- Held joint: 0.0799 / 0.0278
- Free joint: 0.0417 / 0.0521
- Eligible seeds: 0/3

Opaque domain E:

- Held joint: 0.1181 / 0.0243
- Free joint: 0.0660 / 0.0382
- Held inverse: 0.3229 / 0.0972
- Eligible seeds: 1/3

Interference in E:

- Held joint: 0.1181 → 0.0660
- Free joint: 0.0660 → 0.0347
- Held inverse: 0.3229 → 0.2188

Interpretation: 完全語彙非共有でも一部domain/seedに信号はあるが、再利用可能unitとして独立domain・全seedへ再生成されない。正式なcatastrophic forgettingではなくdomain/seed-dependent acquisition instability。

## Family-level conclusion

A/B/Dに共通する失敗は、単一domain、一部seed、またはdomain平均の陽性を、再利用可能なcross-domain semantic unitへ昇格させた点にある。これは3系列にまたがる根本前提であり、凍結規則を満たす。

HF-008として次を拒否する。

- best-domain evidence
- positive-seed selection
- domain averageで失敗domainを隠す評価
- partial lexical bridgeを完全語彙非共有転移と呼ぶこと
- acquisition資格前の干渉低下をcatastrophic forgettingと呼ぶこと

## New maximum bottleneck

完全語彙非共有の複数domainで、identity / operation / goal / wording介入に対する選択的responseまたはlesion signatureを、同じ符号で全seedに再生成すること。

## Track reassignment

- A: cross-lexicon response-consensus unit birth
- B: factor-selective counterexample generation
- C: active intervention by expected cross-domain invariance gain
- D: multi-domain all-seed eligibility consensus
- E: bridge-leakage and consensus governance

## Benchmark change

G1 benchmark v3では、平均精度だけでなく次を必須化する。

1. 2以上の完全語彙非共有domain
2. 3 seedすべての個別成績
3. prospective / inverse / free Japaneseの同時通過
4. identity / operation / goal / wordingの個別介入またはlesion
5. domain間でのsignature符号一致
6. Correct - shuffle/random >= 0.10
7. post-treatment / shared-token / shared-template / random-sequence leakage監査

## Resource judgment

PR362〜365はすべて1GB未満で、最大モデルは約65,536 bytes、推論も弱いCPUで成立し得る規模だった。現在の失敗原因は容量不足ではなく、cross-domain/seed再現性と因果選択性の欠如である。弱いスマートフォン実機検証は未達。

## Status

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
