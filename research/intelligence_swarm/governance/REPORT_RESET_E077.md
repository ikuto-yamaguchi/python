# RESET-E077 — R0 Research Reconstruction

Date: 2026-07-28
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope lock

- A〜Dの新規toy仮説、別branch、新規機構族は禁止を維持。
- 既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。
- 外部baseline再現前の新規知能原理・能力進歩認定は禁止。
- R0.1〜R0.3、novelty matrix、中心命題の事前登録が完了するまで次stageを提案しない。

## Integrated execution change

前回のofficial-contract infrastructure artifactでは、official command、checkpoint、model、optimizer、scheduler、frame counter、resource計測は保存できたが、RNG stateとexact learner batchがなく、one-step resume equivalenceを判定できなかった。

今回は、pinned SILG sourceに対する証拠instrumentationだけを追加した。

- `patch_silg_resume_equivalence.py`
- `.github/workflows/r01_silg_resume_equivalence.yml`

固定したもの:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- model `multi`
- stateful `false`
- actors `30`
- batch `24`
- unroll `80`
- threads `4`
- learning rate `0.0005`
- RMSprop
- gradient clip `40`
- seed `1`
- train/validation split

instrumentationは、learner update境界でPython/NumPy/Torch RNG、exact batch、initial agent state、model、actor model、optimizer、schedulerをdiskへ保存する。uninterrupted one-step後にdisk payloadをreloadし、同一batchでresumed one-stepを再実行する。

受理条件:

- model tensors: bitwise equal
- optimizer state: bitwise equal
- scheduler state: bitwise equal
- frame increment: equal
- policy/value/entropy/aux/total loss: exact equal
- gradient norm: exact equal
- exact batch payload: bytes、SHA-256、tensor dtype/shape/numel保存

これは能力runではない。random/language-blind/state-only/language-shuffleは能力判定上N/Aと明示し、100M-frame正式再現で必須復帰させる。workflowはcanonical pushで発行済みだが、run ID、artifact、合否はまだ認定していない。

## Existing numerical evidence

最新のshort-horizon negative artifactはrun `30240410850`、artifact `8644560521`。

- Correct `3/60`
- Random `4/60`
- Language-blind `0/60`
- State-only `0/60`
- Language-shuffle `3/60`
- Correct return `-1.7679994`
- Random return `-1.1513333`
- parameters `6,200,115`
- actual frames `131,200` per seed
- peak RSS `1,299,228 / 1,180,104 / 1,856,556 KiB`
- wall `1528.08 / 1559.30 / 1591.64 s`
- CPU forward `8.565 ms/step`
- leakage `false`
- qualification rejected

これは公式100M-frame baseline failureではなく、縮小契約で言語依存能力が成立しなかったnegative evidenceである。

## Prior-art audit

SemEval-2026 Task 12 AERをnovelty matrix境界へ追加した。AERは複数文書の支持証拠からtarget eventの最も妥当な直接原因を選ぶevidence-grounded abductive causal reasoning benchmarkで、distributed evidence、間接背景要因、意味的に近い非因果distractorを扱い、公式dataset repositoryも公開されている。

したがって、次だけではRQ-001の新規性を認定しない。

- language-only evidence integration
- direct-cause multiple-choice selection
- abductive event-cause inference
- non-causal distractor rejection

AERはSILG interactive policy competence、J-CRe3 multimodal reference resolution、hidden intervention-target groundingの代替baselineではない。exact commit、dataset checksum、official evaluatorを固定した数値再現は0件。

## RQ-001

> **RQ-001: FURTHER NARROWED BEYOND EVIDENCE-GROUNDED ABDUCTIVE EVENT-CAUSE INFERENCE — NOT ADOPTED**

広義RQ-001は棄却、狭義RQ-001は未採用を維持する。

## Formal status

- immutable R0.1 short-horizon artifacts: **8件**
- official-contract infrastructure artifacts: **1件・不合格**
- one-step resume-equivalence artifacts: **0件・workflow発行済み**
- official SILG 100M-frame reproduction: **0件**
- competent external baseline reproduction: **0件**
- J-CRe3 numerical reproduction: **0件**
- R0.2: **0件**
- R0.3 hidden intervention-target ablation: **棄却維持**
- novelty matrix: **未完了**
- 中心命題の事前登録: **未完了**
- 新規機構族: **未認定**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- 次stage: **提案なし**
