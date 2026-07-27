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

Immutable contract audit:

- `R01_OFFICIAL_TRAINING_HORIZON_AUDIT.json`
- classification: **`public_reproduction_contract_mismatch`**

既存の`131,072`-frame runsは公式frame horizonの`0.131072%`であり、すべてshort-horizon screening evidenceへ再分類する。公式baseline再現、公式baseline failure、能力進歩には数えない。

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

## Active blocker — infrastructure qualification

artifact `8644560521`ではofficial `job.tar`が全seedで欠落しているため、optimizer state、scheduler、frame counter、model equality、resume equivalenceは判定不能。

Evidence:

- checkpoint inventory: `results_audits/SILG_RTFM_ARTIFACT_8644560521_INVENTORY.json`
- learner variance audit: `results_audits/R0_SILG_ARTIFACT_8644560521_LEARNER_VARIANCE.json`

learner logのtotal/PG lossは高分散だが、optimizer/restore failureとは認定しない。

### Next execution contract

次の実行は能力screeningではなく、公式契約の**infrastructure qualification**とする。

1. official `model=multi`, `stateful=false`, actors `30`, batch `24`, unroll `80`, threads `4`を変更しない。
2. 本番100M frames前の短いsegmentでrunner resource feasibilityだけを確認する。
3. 全seed checkpointのmodel、optimizer、scheduler、frame counter、bytes、SHA-256をfail-closed保存する。
4. 同一checkpoint、RNG、batchからのone-step resume equivalenceを確認する。
5. peak RSS、runtime、throughputから100M-frame wall/costを外挿し、resource blockerをimmutable保存する。
6. qualificationを能力証拠へ数えない。
7. runnerがofficial sampling contractを実行できない場合、縮小contractへ置換して「再現」と呼ばない。
8. actors/batchの追加単一要因screeningは停止する。

infrastructure qualificationが通過しresource feasibleな場合のみ、entropy `0.05`と`0.005`のofficial 100M-frame reproductionをseeds固定で提案する。

## P0 — Evaluation contract freeze

D015〜D035を凍結する。毎runでrandom/language-blind/state-only/shuffle、model/checkpoint bytes、RSS、runtime、CPU latency、seed、split、actual frames、raw logs、checksums、leakageを保存する。公式再現ではofficial command parity、100M horizon、checkpoint/resume integrityも必須。

## P1 — External official reproductions

### J-CRe3

Ueda et al., LREC-COLING 2024、公式repository `riken-grp/J-CRe3`。exact commit、dataset、license、checksum、official commandを固定し、random、text-only、vision-only、mention-shuffle、frame/object-shuffleをmatched評価する。数値再現は0件。

### CausalVerse

公式repository `CausalVerse/CausalVerseBenchmark`。静止画、動的物理、ロボット操作、交通場面の24 sub-scenesと、ground-truth causal mechanisms、variables、interventions、temporal dependenciesを提供する。

再現契約:

- exact commit、license、dataset/config checksumを固定する。
- 公式baselineを無改変で1 scene以上再現する。
- intervention target既知/hidden、temporal shuffle、variable shuffle、random representationをmatched比較する。
- model bytes、RSS、runtime、seed、split/config、raw output、checksums、leakageを保存する。
- SILG interactive policy competenceやJ-CRe3日本語参照解決の代替証拠にはしない。

数値再現は0件。

### Latest prior-art boundary

CausalVerseにより、設定可能な高忠実度simulation、ground-truth causal mechanism、既知の介入target、temporal dependencyを用いたCRL stress test自体は既存化されている。したがって、それだけではRQ-001の新規性を認定しない。

CaST-Bench、NoisyCausal、CodeBind、MagicBench、CausalDisenSeg、TRACE、DCAN、PCMCI、CausalLens、CTLD、score-based CRL、finite-sample CRL、LeGIT、GPI、Multi-View CRL、ReCITE、C3、MCDRL、CmIR、CAIR、Bayesian Ablation等もnovelty matrixの別列で維持し、論文値を本研究の能力証拠へ流用しない。

## P1 — R0.2 Environment-first

immutable R0.1 competence bundleが`qualified_for_r02=true`を満たした後のみ開始する。Environment-first、parameter-matched End-to-end、State-onlyを比較する。

## Closed — R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず棄却維持する。

## RQ-001

- 広義RQ-001: **棄却**
- 狭義RQ-001: **追加狭域化・未採用**

採用には、既存baselineを差し引いた後にも残るlanguage固有追加情報、countermodel pair、joint recoding不能な外部denotation law、事前登録済みclaim/counterexample/stopping ruleが必要。

正式境界:

> **FURTHER NARROWED BEYOND CONFIGURABLE GROUND-TRUTH INTERVENTION BENCHMARKING — NOT ADOPTED**

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Status

- immutable R0.1 screening artifacts: **8件**
- official SILG 100M-frame reproduction: **0件**
- competent external baseline: **0件**
- J-CRe3 numerical reproduction: **0件**
- CausalVerse numerical reproduction: **0件**
- active work: **official-contract infrastructure qualification**
- new mechanism family: **未認定**
- new intelligence principle: **未発見**
- capability progress: **未認定**
- 高校生級知能: **未達**
- 完成: **false**
