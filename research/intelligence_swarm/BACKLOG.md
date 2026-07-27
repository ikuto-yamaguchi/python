# Intelligence Swarm Backlog

## Operating rule

R0はcanonical branch `research/intelligence-swarm-reconstruction-001`だけで進める。A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。

外部baselineを再現するまで、新規機構族、新しい知能原理、能力進歩、高校生級到達を認定しない。単発失敗で終了せず、失敗分類、根拠、原因だけを変える最小修正、同一budget再run、採用・棄却・停止判定までを1サイクルとする。

## A–D allocation

- **A**: SILG/RTFM、J-CRe3等の公式code・dataset・command・dependency固定と無改変再現。
- **B**: 実装不一致、最適化不足、表現ボトルネック、探索・学習信号不足の診断と制約内最適化。
- **C**: 最新一次文献・公式codeとの重複監査、novelty matrix更新。
- **D**: D015〜D035、matched controls、resource provenance、leakage、RQ-001判定。

## P0 — SILG/RTFM R0.1 screening cycle

固定条件:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- seeds `1,7,19`
- `131,072 requested frames`
- train `silg:rtfm_train_s1-v0`
- test `silg:rtfm_test_s1-v0`
- random / language-blind / state-only / language-shuffle
- same-instance matched evaluation

### Closed causes

1. `entropy_cost=0.005`単独原因: **rejected**
2. evaluation protocol mismatch主因: **rejected**
3. official stateful core不足単独原因: **rejected**
4. `unroll_length=20`不足単独原因: **rejected**
5. `learning_rate=0.0001`単独原因: **rejected**
6. gradient clip norm `40.0`不足単独原因: **rejected**

### Completed gradient-clipping evidence

- run `30240410850`, job `89896249118`
- artifact `8644560521`
- digest `sha256:987bc842229a8a9d03dcced3387c4c8a17a2049fdc2aadfad6c7560027e11e19`
- execution commit `3f0c62430a27116722c22f69525b54631d93032b`
- Correct `3/60`, Random `4/60`
- Language-blind `0/60`, State-only `0/60`, Language-shuffle `3/60`
- Correct return `-1.7679994`, Random return `-1.1513333`
- parameters `6,200,115`
- model-state `24,827,943 / 24,827,943 / 24,828,026 bytes`
- actual frames `131,200` per seed
- peak RSS `1,299,228 / 1,180,104 / 1,856,556 KiB`
- wall `1528.08 / 1559.30 / 1591.64 s`
- model-audit CPU forward `8.565 ms/step`
- source clip-10 routing、stateful/unroll、LSTM checkpoint、same-instance、parity、leakage=false: passed
- qualification: rejected

Decision: clip 10.0 reached all seeds and Correct success increased to 3/60, but Correct remained below Random in win rate and return and exactly matched language-shuffle. Reject gradient-clipping threshold as the sole cause.

### Active cause: optimizer/checkpoint restore integrity

Do not start another three-seed training run before inspecting the preserved gradient-clip artifact. Use:

- auditor: `audit_silg_optimizer_checkpoint_integrity.py`
- implementation commit: `9afd2bae16aa317c63979ebc9406b86d9b4d8e70`
- source artifact: `8644560521`

Immediate tasks:

1. Download and verify artifact digest before extraction.
2. Locate all seed `1/7/19` official `job.tar` files and standalone trained model-state files.
3. Run the auditor with `--min-frames 131072`.
4. Require non-empty optimizer `state` and `param_groups` for every seed.
5. Require a finite frame counter at or above budget.
6. Require checkpoint model tensors to exactly equal the standalone exported model tensors.
7. Preserve checkpoint/model bytes, SHA-256, top-level keys, optimizer entry counts, frame-key provenance and full JSON result.
8. If rejected, change only the missing restore component and verify resume-equivalence from the same checkpoint; do not change model, split, seeds, frames or hyperparameters.
9. If accepted, reject optimizer/checkpoint restore integrity as the principal cause and select exactly one next cause from learner logs.
10. Do not call an artifact-integrity pass a capability improvement.

Resume-equivalence acceptance, only if repair is needed:

- uninterrupted continuation and save→load→continuation begin from tensor-identical model and optimizer states;
- one controlled learner update on identical batch/RNG yields equal parameters, optimizer slots, frame count and reported losses within preregistered numerical tolerance;
- no high-cost end-to-end run is authorized until this local equivalence passes.

## P0 — Evaluation contract freeze

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで受入auditorを増やさない。optimizer/checkpoint auditorは事前指定済み原因の診断であり、能力受入条件の追加ではない。毎runでcontrols、resource、seed/split、checksums、leakageを保存する。

## P1 — External official reproductions

### J-CRe3

Ueda et al., LREC-COLING 2024、公式repository `riken-grp/J-CRe3`。exact commit、dataset、license、checksum、official commandを固定し、random、text-only、vision-only、mention-shuffle、frame/object-shuffleをmatched評価する。数値再現は0件。

### Latest prior-art boundary

NoisyCausal（ACL 2026）は、structured noiseを加えた因果推論benchmarkと、言語文脈から変数・因果グラフを抽出してstructured promptへ変換する手法を扱う。したがって、language-to-causal-graph extraction、symbolic structuring、noise-robust causal promptingだけではRQ-001の新規性を認定しない。hidden intervention-target groundingやSILGのinteractive policy competenceとは別能力である。

CodeBind、MagicBench、CausalDisenSeg、TRACE、DCAN、PCMCI、CausalLens、CTLD、score-based CRL、finite-sample CRL、LeGIT、GPI、Multi-View CRL、ReCITE、C3、MCDRL、CmIR、CAIR、Bayesian Ablation等もnovelty matrixの別列で維持し、論文値を本研究の能力証拠へ流用しない。

## P1 — R0.2 Environment-first

immutable R0.1 competence bundleが`qualified_for_r02=true`を満たした後のみ開始する。Environment-first、parameter-matched End-to-end、State-onlyを比較する。

## Closed — R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず棄却維持する。

## RQ-001

- 広義RQ-001: **棄却**
- 狭義RQ-001: **追加狭域化・未採用**

採用には、既存baselineを差し引いた後にも残るlanguage固有追加情報、countermodel pair、joint recoding不能な外部denotation law、事前登録済みclaim/counterexample/stopping ruleが必要。

正式境界:

> **FURTHER NARROWED BEYOND LANGUAGE-TO-CAUSAL-GRAPH STRUCTURING UNDER NOISE — NOT ADOPTED**

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Status

- immutable R0.1 artifacts: **8件**
- competent external baseline: **0件**
- J-CRe3 numerical reproduction: **0件**
- active work: **optimizer/checkpoint artifact-only integrity audit**
- new mechanism family: **未認定**
- new intelligence principle: **未発見**
- capability progress: **未認定**
- 高校生級知能: **未達**
- 完成: **false**
