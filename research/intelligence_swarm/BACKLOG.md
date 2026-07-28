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

Official contract:

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
- seeds `1 / 7 / 19`

既存の`131,072`-frame runsはすべてshort-horizon screening evidenceへ再分類する。公式baseline再現、公式baseline failure、能力進歩には数えない。

## Closed short-horizon screenings

以下は各縮小契約内の単独原因としてのみrejected。公式100M-frame baselineへ外挿しない。

1. `entropy_cost=0.005`
2. evaluation protocol mismatch
3. `stateful=true`
4. `unroll_length=20→80`
5. `learning_rate=0.0001`
6. gradient clip norm `40→10`

Latest short-horizon negative evidence:

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

Run `30258965674`, job `89954109262`, artifact `8650362356`:

- official command parity: pass
- official `job.tar`: preserved
- checkpoint/exported model tensors: equal
- optimizer state: `73` entries / `1` parameter group
- scheduler and frame counter: present
- checkpoint frames `40,320`
- checkpoint SHA-256 `1ce3a0590611d8d26ef06330e7f5eca43e9c13deafb8d41bf3570eadaa754675`
- peak RSS `9,305,052 KiB`
- wall `631.66 s`
- throughput `63.83 frames/s`
- projected 100M wall `18.13 runner-days` per entropy/seed run

## Completed P0 resume-equivalence qualification

Canonical immutable evidence:

- run `30300067389`
- job `90090542489`
- artifact `8666312079`
- artifact SHA-256 `34f02c802f6db15b55336a0547e3914846aad6d74783ebfc371d12ca6ac08115`
- frames `3840 -> 5760`

Accepted: exact learner batch and initial recurrent state、learner/actor model synchronization、optimizer/scheduler state、Python/NumPy/Torch RNG、losses/gradient/stats/frame increment、uninterrupted and reload-resumed one-step equivalence。

これはcaptured official learner updateのexact replayだけを証明し、asynchronous continuation、100M horizon、benchmark competenceは証明しない。

## Active P0 — official seed-1 first checkpoint

Workflow: `.github/workflows/r01_silg_official_100m_chunk.yml`

Fixed first chunk:

- seed `1`
- entropy `0.05`
- official model / optimizer / sampling defaults
- target `1,000,000` frames as first durable continuation checkpoint toward `100,000,000`

Initial attempt:

- run `30308447687`
- failed before training because pinned SILG has no `--seed` CLI argument
- immutable failure artifact `8669383695`
- artifact SHA-256 `9a5518b1a5e5338886ed2d3f2429d0e0246f0ba9cd919de7627e6f01c74dccd4`

Applied single-cause correction:

- commit `ce6909baf0e0879d1547c34beb457d59d2027b9e`
- remove unsupported `--seed`
- patch only RNG seeding in pinned `run_exp.py`
- global Python/NumPy/Torch seed from `SILG_EXPERIMENT_SEED=1`
- deterministic actor seed `experiment_seed * 1000003 + actor_index`
- preserve before/after source and SHA-256
- no model、loss、optimizer、environment、action schema、sampling default、frame-budget change

Current state verified for RESET-E083:

- inspected PR head: `f83a72610d37a5dc8d43a9c053b02b5134c082fd`
- replacement run/job/artifact/qualification: **unconfirmed**
- 12 connector-visible PR-triggered workflows: **all `completed / action_required`, jobs未生成**
- classification: **`workflow_execution_approval_or_policy_blocker`**
- do not classify this as model、optimizer、SILG baseline、evaluation logic or capability failure
- do not duplicate-dispatch the same first chunk

Required artifact after execution is allowed:

- exact command and pinned source provenance
- pre/post seed patch and SHA-256
- complete `job.tar`
- model / optimizer / scheduler / frame state
- checkpoint bytes and SHA-256
- host / dependency / raw logs
- peak RSS / wall / throughput
- qualification JSON with `checkpoint_frames >= 1,000,000`

Continuation after first checkpoint:

1. checkpoint frames、optimizer/scheduler state、command parity、bytes、SHA-256、RSS、runtimeを検査する。
2. execution failureならmodel条件を変えず、最初のinfrastructure root causeだけを修正する。
3. durable checkpointがqualifiedなら同じseed/entropy/contractでcontinuation cadenceとartifact retentionを固定する。
4. trained checkpoint評価時にCorrect/random/language-blind/state-only/shuffleをsame-instanceで実行する。
5. model/checkpoint bytes、RSS、runtime、CPU latency、seed、split、actual frames、raw logs、checksums、leakageを保存する。
6. 100M horizonとmatched controlsが揃うまでpublic baseline reproductionを認定しない。

## P0 — Evaluation contract freeze

D015〜D035を凍結する。能力runではrandom/language-blind/state-only/shuffle、model/checkpoint bytes、RSS、runtime、CPU latency、seed、split、actual frames、raw logs、checksums、leakageを保存する。公式再現ではofficial command parity、100M horizon、checkpoint/resume integrityも必須。

Normalized-cell workflowはread-only fail-closed CIへ変更済み。fixtureは明示holdout契約に合わせて修正済みである。RESET-E083で観測した`action_required`は承認/policy層のblockerとして扱い、evaluation logic regressionとは混同しない。

Standalone `audit_canonical_instance_identity.py`はpassしているが、direct integration into `validate_dataset()` and `score()` remains incomplete。統合完了までclaimed bundleからstandalone auditを省略しない。

## P1 — External official reproductions

### J-CRe3

Ueda et al., LREC-COLING 2024、公式repository `riken-grp/J-CRe3`。exact commit、dataset、license、checksum、official commandを固定し、random、text-only、vision-only、mention-shuffle、frame/object-shuffleをmatched評価する。数値再現は0件。

### CausalVerse

公式repository `CausalVerse/CausalVerseBenchmark`。exact commit、license、dataset/config checksumを固定し、公式baselineを無改変で1 scene以上再現する。known/hidden intervention target、temporal shuffle、variable shuffle、random representationをmatched比較する。数値再現は0件。

### Unknown multi-node intervention CRL

NeurIPS 2024のUMN-CRLにはauthor-official repository `acarturk-e/umni-crl`がある。2026年のfew-environment finite-sample CRLは、少数のunknown multi-node interventionからlatent graph、mixing/representation、unknown intervention targetsを回復する保証を提示する。現時点ではexact commit、dependency、dataset/config、public numerical contractを固定したimmutable reproductionは0件。novelty matrixへ「再現済み」としては追加しない。

### SemEval-2026 Task 12 AER

公式dataset repository `sooo66/semeval2026-task12-dataset`。exact commit、dataset checksum、official split/evaluatorを固定するまで数値を能力証拠へ流用しない。SILG interactive competence、J-CRe3 multimodal reference resolution、hidden intervention-target groundingの代替にはしない。

### COGS

一次論文境界のみ維持する。author-official repository、exact commit、dependency、dataset、公式commandを固定できていないため再現対象への昇格は保留する。

## Prior-art audit rule

score-based CRL、finite-sample CRL、unknown multi-node intervention CRL、Multi-View CRL、LeGIT、GPI、ReCITE、C3、MCDRL、CmIR、CAIR、PCMCI、CausalLens、CTLD、DCAN、TRACE、Bayesian Ablation、CausalDisenSeg、MagicBench、CodeBind、NoisyCausal、CaST-Bench、CausalVerse、MTG-Causal-RL、Mind Dreamer、AER、COGS等をnovelty matrixの既存境界として維持する。

2026-07-28の再監査でも、既存境界を実質変更する新しい「一次文献 + author-official code + exact commit + public numerical contract」の組は確認できなかった。文献名だけを毎回追加せず、immutable reproductionが可能になったものだけをnovelty matrixへ昇格する。

## P1 — R0.2 Environment-first

immutable R0.1 competence bundleが`qualified_for_r02=true`を満たした後のみ開始する。Environment-first、parameter-matched End-to-end、State-onlyを比較する。

## Closed — R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず棄却維持する。

## RQ-001

- 広義RQ-001: **棄却**
- 狭義RQ-001: **追加狭域化・未採用**

採用には、既存baselineを差し引いた後にも残るlanguage固有追加情報、countermodel pair、joint recoding不能な外部denotation law、事前登録済みclaim/counterexample/stopping ruleが必要。

正式境界:

> **FURTHER NARROWED — NOT ADOPTED**

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Status

- immutable R0.1 short-horizon screening artifacts: **8件**
- official-contract infrastructure artifact: **1件**
- exact one-step resume-equivalence artifact: **1件・accepted**
- active official 100M reproduction: **initial seed CLI defect fixed; replacement execution blocked/unconfirmed**
- official SILG 100M-frame reproduction: **0件**
- competent external baseline: **0件**
- official-horizon matched controls: **0件**
- J-CRe3 numerical reproduction: **0件**
- CausalVerse numerical reproduction: **0件**
- qualified R0.2: **0件**
- R0.3 hidden intervention-target ablation: **棄却維持**
- novelty matrix: **未完了**
- 中心命題の事前登録: **未完了**
- new mechanism family: **未認定**
- new intelligence principle: **未発見**
- capability progress: **未認定**
- 高校生級知能: **未達**
- 完成: **false**
