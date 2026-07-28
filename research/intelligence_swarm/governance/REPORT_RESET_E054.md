# RESET-E054 — Immutable R0.1 failure and continued screening

Date: 2026-07-26
Branch: `research/intelligence-swarm-reconstruction-001`

## Scope

A〜Dに新しいtoy仮説、別branch、新規機構族を作らせず、公開benchmark再現、prior-art audit、evaluation contract、hidden intervention-target ablationだけを累積する。既存stacked draft PRはnegative-results archiveとして扱い、新作業のbaseにしない。

## R0.1 execution result

GitHub Actions run `30203026269`を確認した。

- workflow head: `5d9f137296a64fc401560356470ac27f520cbeff`
- `r01-public-reproduction`: qualification failure
- source install、generator signature、random/schema probe、3-seed 131,072-frame training、matched evaluation、artifact upload: 完了
- R0.2: qualification failureによりskip
- artifact ID: `8633105142`
- artifact name: `r01-silg-rtfm-matched-30203026269`
- artifact size: `72,686,203 bytes`
- artifact digest: `sha256:43ab7f1df82e9eba98c132b2e84a9ec55dbfdd726795fb43f7608fe288e00eef`

各seedは`131,080` actual framesで学習完了した。

## Matched controls

- Correct: `0/60`、win rate `0.0000`、return `-2.0749993`
- Random: `4/60`、win rate `0.0667`、return `-1.1513333`
- Language-blind: `1/60`、win rate `0.0167`
- State-only: `0/60`
- Language-shuffle: `0/60`
- Correct−Random return: `-0.9236660`
- same-instance stream: 成立
- answer leakage: `false`

qualification failures:

- `zero_source_policy_success`
- `correct_not_above_random_win_rate`
- `correct_not_above_random_return`

classification:

- `initial_reproduction_failure`
- `optimization_or_policy_competence_failure`

## Resource record

- seed 1: wall `24:01.80`、peak RSS `1,442,552 KiB`
- seed 7: wall `24:10.06`、peak RSS `1,000,412 KiB`
- seed 19: wall `24:09.28`、peak RSS `1,235,964 KiB`
- matched evaluation: 約`150 s`、peak RSS `301,556 KiB`

checkpoint、raw logs、dependency freeze、matched predictions、qualification JSON、SHA-256 manifestはartifactに保存された。

## Missing diagnostics

要求済みだった以下の構造化診断はartifactで不足した。

- action histogram
- valid-action rate
- pre/post-mask logits
- invalid-action probability mass
- gradient norm

次screeningでは必須出力へ昇格する。新しいauditorは追加しない。

## Continued experiment

失敗で終了せず、次の単一要因screeningを発行した。

- factor: `entropy_cost`
- from: `0.05`
- to: `0.005`
- fixed: source pins、model family、frames、seeds、split、actors、batch、unroll、matched instances

採用条件はCorrect success > 0、Correct win/return > Random、3-seed平均改善、最低seed非悪化である。失敗した場合はentropy単独原因を棄却し、official evaluation/default parityを次の単一原因候補とする。

最大6 screening runまたは事前停止条件まで継続し、「検証したが駄目だった」で閉じない。

## Prior-art audit

最新一次文献・公式codeを再確認した。

- J-CRe3: LREC-COLING 2024一次論文を維持。日本語multimodal reference resolution baselineであり、SILGのinteractive competenceを代替しない。数値再現は未完了。
- CmIR: ACL 2026一次論文を維持。multimodal invariant/spurious decompositionは既存境界。author-official codeは未固定。
- 既存のscore-based CRL、有限標本CRL、LeGIT、GPI、Multi-View CRL、ReCITE等を差し引いても、RQ-001を採用する新しい直接証拠は得られていない。

## RQ-001 decision

- broad RQ-001: **rejected**
- narrow RQ-001: **further narrowed, not adopted**

採用には、再現済み外部baselineを超えるlanguage固有追加情報、countermodel pair、joint recoding不能な外部denotation law、事前登録済みclaim/counterexample/stopping ruleが必要である。

## Stage decision

次stageは提案しない。

- immutable R0.1 bundle: **1件・不合格**
- competent external baseline: **0件**
- qualified R0.2: **0件**
- R0.3: **棄却維持**
- novelty matrix: **未完了**
- 中心命題の事前登録: **未完了**
- 新規機構族: **未認定**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
