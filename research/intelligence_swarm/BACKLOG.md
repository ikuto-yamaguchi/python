# Intelligence Swarm Backlog

## Operating rule

R0はcanonical branch `research/intelligence-swarm-reconstruction-001`だけで進める。A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。

外部baselineを再現するまで、新規機構族、新しい知能原理、能力進歩、高校生級到達を認定しない。短期screeningを公式baseline再現と誤認してhyperparameter探索を続けることも禁止する。

## A–D allocation

- **A**: SILG/RTFM、J-CRe3等の公式code・dataset・command・dependency固定と無改変再現。
- **B**: 実装不一致、最適化不足、表現ボトルネック、探索・学習信号不足の診断と制約内最適化。
- **C**: 最新一次文献・公式codeとの重複監査、novelty matrix更新。
- **D**: D015〜D035、matched controls、resource provenance、leakage、RQ-001判定。

## P0 — SILG/RTFM public reproduction contract

Pinned sources:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`

Official RTFM launch contract:

- model `multi`
- stateful `false`
- entropy grid `0.05 / 0.005`
- train `silg:rtfm_train_s1-v0`
- validation `silg:rtfm_test_s1-v0`
- total frames `100,000,000`
- actors `30`
- batch `24`
- unroll `80`
- learner threads `4`
- learning rate `0.0005`
- RMSprop alpha `0.99`, momentum `0`, epsilon `0.01`
- global gradient clip norm `40`

既存の`131,072`-frame runsはすべてshort-horizon screening evidenceへ再分類する。公式baseline再現、公式baseline failure、能力進歩には数えない。

## Closed short-horizon screenings

以下は各縮小契約内の単独原因としてのみrejected。公式100M-frame baselineへ外挿しない。

1. `entropy_cost=0.005`
2. evaluation protocol mismatch
3. `stateful=true`
4. `unroll_length=20→80`
5. `learning_rate=0.0001`
6. gradient clip norm `40→10`

## Latest short-horizon negative evidence

- run `30240410850`, artifact `8644560521`
- Correct `3/60`, Random `4/60`
- Language-blind `0/60`, State-only `0/60`, Language-shuffle `3/60`
- Correct return `-1.7679994`, Random return `-1.1513333`
- parameters `6,200,115`
- actual frames `131,200` per seed
- peak RSS `1,299,228 / 1,180,104 / 1,856,556 KiB`
- wall `1528.08 / 1559.30 / 1591.64 s`
- CPU forward `8.565 ms/step`
- leakage `false`
- qualification rejected

この結果は縮小契約で言語依存能力が成立しなかったnegative evidenceであり、公式baseline失敗の証拠ではない。

## Completed P0 infrastructure probe

Run `30258965674`, job `89954109262`, artifact `8650362356`をimmutable resultとして保存した。

Passed:

- pinned sourceとofficial command parity
- official `job.tar` preservation
- checkpoint model/exported modelのtensor完全一致
- optimizer state `73` entries / `1` parameter group
- scheduler stateとframe counter
- checkpoint frames `40,320`
- checkpoint bytes `39,266,613`
- checkpoint SHA-256 `1ce3a0590611d8d26ef06330e7f5eca43e9c13deafb8d41bf3570eadaa754675`

Resource:

- peak RSS `9,305,052 KiB`
- wall `631.66 s`
- throughput `63.83 frames/s`
- projected 100M wall `18.13 runner-days` per entropy/seed run

Rejected requirements:

- `missing_rng_state_for_one_step_resume_equivalence`
- `missing_batch_state_for_one_step_resume_equivalence`

Classification: **`resume_equivalence_instrumentation_gap`**。optimizer failure、public-baseline failure、能力failureとは扱わない。

Immutable ledger:

- `benchmarks/grounded_causal/results_audits/SILG_RTFM_OFFICIAL_INFRA_RUN_30258965674.json`
- artifact digest `sha256:975d5c6223637f48c3e358d51ead0470e3f97b01826e2cd6e216fd484b8f8750`

## Active P0 — One-step resume-equivalence execution

追加済み:

- `benchmarks/grounded_causal/patch_silg_resume_equivalence.py`
- `.github/workflows/r01_silg_resume_equivalence.yml`

変更対象は証拠instrumentationだけである。model、objective、optimizer、source pins、official sampling defaults、splitは変更しない。

Probe procedure:

1. learner update直前にPython `random`、NumPy、Torch CPU RNG stateを保存する。
2. CUDA使用時だけ全CUDA RNG stateも保存する。
3. exact learner batchとinitial agent stateをtensor内容込みでdiskへ保存する。
4. model、actor model、optimizer、schedulerを保存する。
5. uninterrupted one-step updateを実行し、post-state、losses、gradient normを取得する。
6. disk payloadをreloadし、model/optimizer/scheduler/RNGをrestoreする。
7. 同一batchでresumed one-step updateを実行する。
8. model/optimizer/schedulerをbitwise比較し、losses・gradient normをexact比較する。
9. exact batch payloadのbytes、SHA-256、全tensorのdtype・shape・numelを保存する。

Fixed contract:

- SILG/RTFM commit
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
- short infrastructure segment `32,768` requested frames

この監査では能力対照を実行しない。random/language-blind/state-only/language-shuffleは能力判定上N/Aと明示し、100M-frame正式能力再現で全対照を必須復帰させる。

### Acceptance

- Python/NumPy/Torch RNG stateが保存・restoreされる。
- exact learner batch payloadがdisk reloadされ、bytes・SHA-256が保存される。
- one-step後の全model tensorがbitwise equal。
- optimizer stateとscheduler stateがbitwise equal。
- frame incrementが同一である。
- policy/value/entropy/aux/total lossとgradient normがexact equal。
- raw logs、dependency lock、host provenance、artifact checksumを保存する。

### Rejection and continuation

- 最初の不一致componentだけを次の単一修正対象にする。
- mismatchを理由にmodel、optimizer、sampling defaults、splitを変更しない。
- workflow execution failureとresume-equivalence failureを混同しない。
- workflowは発行済みだが、run ID、artifact、合否は未確認。結果取得前に同条件を重複dispatchしない。
- resume equivalence通過後にresource feasibilityを正式判定する。
- 一つの100M entropy/seed runは現runner外挿で約18.13日。entropy 2条件だけでも約36.3 runner-days、three-seed化は約108.8 runner-days。無料runner制約、checkpoint cadence、artifact retention、停止・再開条件を事前固定する。
- infrastructure qualificationを能力進歩へ数えない。

## P0 — Evaluation contract freeze

D015〜D035を凍結する。能力runではrandom/language-blind/state-only/shuffle、model/checkpoint bytes、RSS、runtime、CPU latency、seed、split、actual frames、raw logs、checksums、leakageを保存する。公式再現ではofficial command parity、100M horizon、checkpoint/resume integrityも必須。

## P1 — External official reproductions

### J-CRe3

Ueda et al., LREC-COLING 2024、公式repository `riken-grp/J-CRe3`。exact commit、dataset、license、checksum、official commandを固定し、random、text-only、vision-only、mention-shuffle、frame/object-shuffleをmatched評価する。数値再現は0件。

### CausalVerse

公式repository `CausalVerse/CausalVerseBenchmark`。exact commit、license、dataset/config checksumを固定し、公式baselineを無改変で1 scene以上再現する。known/hidden intervention target、temporal shuffle、variable shuffle、random representationをmatched比較する。数値再現は0件。

### SemEval-2026 Task 12 AER

公式dataset repository `sooo66/semeval2026-task12-dataset`。evidence-rich multiple-choice direct-cause inferenceを測るlanguage-only benchmarkとしてnovelty matrixの別列へ追加する。exact commit、dataset checksum、official split/evaluatorを固定するまで数値を能力証拠へ流用しない。SILG interactive competence、J-CRe3 multimodal reference resolution、hidden intervention-target groundingの代替にはしない。

### Latest prior-art boundary

AERは複数文書の支持証拠からtarget eventの最も妥当な直接原因を選び、distributed evidence、間接背景要因、意味的に近い非因果distractorを扱う。したがって、language-only evidence integration、direct-cause selection、abductive causal reasoningだけではRQ-001の新規性を認定しない。

score-based CRL、finite-sample CRL、Multi-View CRL、LeGIT、GPI、ReCITE、C3、MCDRL、CmIR、CAIR、PCMCI、CausalLens、CTLD、DCAN、TRACE、Bayesian Ablation、CausalDisenSeg、MagicBench、CodeBind、NoisyCausal、CaST-Bench、CausalVerse、MTG-Causal-RL、Mind Dreamer等もnovelty matrixの別列で維持する。

## P1 — R0.2 Environment-first

immutable R0.1 competence bundleが`qualified_for_r02=true`を満たした後のみ開始する。Environment-first、parameter-matched End-to-end、State-onlyを比較する。

## Closed — R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず棄却維持する。

## RQ-001

- 広義RQ-001: **棄却**
- 狭義RQ-001: **追加狭域化・未採用**

採用には、既存baselineを差し引いた後にも残るlanguage固有追加情報、countermodel pair、joint recoding不能な外部denotation law、事前登録済みclaim/counterexample/stopping ruleが必要。

正式境界:

> **FURTHER NARROWED BEYOND EVIDENCE-GROUNDED ABDUCTIVE EVENT-CAUSE INFERENCE — NOT ADOPTED**

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Status

- immutable R0.1 short-horizon screening artifacts: **8件**
- official-contract infrastructure artifacts: **1件・resume evidence不足で不合格**
- one-step resume-equivalence artifact: **0件・workflow発行済み**
- official SILG 100M-frame reproduction: **0件**
- competent external baseline: **0件**
- J-CRe3 numerical reproduction: **0件**
- CausalVerse numerical reproduction: **0件**
- AER numerical reproduction: **0件**
- active work: **one-step resume-equivalence execution**
- new mechanism family: **未認定**
- new intelligence principle: **未発見**
- capability progress: **未認定**
- 高校生級知能: **未達**
- 完成: **false**
