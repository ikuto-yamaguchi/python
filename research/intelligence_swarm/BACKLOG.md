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

### Completed learning-rate evidence

- run `30235108376`, job `89881341003`
- artifact `8642403437`
- digest `sha256:882e92a17ba5da5836dcf78379a484cc7ed63827ed3bf0b18196c5b18c3d8917`
- execution commit `67556f067028edac502380c6d3de15575c996ffc`
- Correct `0/60`, Random `4/60`
- Language-blind `0/60`, State-only `1/60`, Language-shuffle `0/60`
- Correct return `-2.1523326`, Random return `-1.1513333`
- parameters `6,200,115`
- model-state `24,827,943 / 24,827,943 / 24,828,026 bytes`
- actual frames `131,200` per seed
- peak RSS `1,470,976 / 1,269,884 / 2,414,924 KiB`
- wall `1441.30 / 1404.99 / 1483.19 s`
- model-audit CPU forward `7.511 ms/step`
- stateful/unroll/lr routing、LSTM checkpoint、same-instance、parity、leakage=false: passed
- qualification: rejected

Decision: explicit lower learning rate reached all seeds but did not produce a competent policy or a language-dependent advantage. Reject learning-rate shortage as the sole cause.

### Active single-factor screening: gradient clipping

Change exactly one factor in pinned official source:

- `clip_grad_norm_(model.parameters(), 40.0)` → `clip_grad_norm_(model.parameters(), 10.0)`

Keep fixed:

- `stateful=true`
- `unroll_length=80`
- learning rate: official default; no explicit override
- entropy cost `0.05`
- actors `2`, threads `1`, batch size `2`
- model family `multi`
- frames、seeds、split、instances、controls

Implementation:

- patch: `patch_silg_gradient_clip_screening.py`
- workflow: `.github/workflows/r01_silg_gradient_clip_screening.yml`
- patch commit: `2c877197b275e9c11f018479909adfe8e2a82844`
- workflow commit: `3f0c62430a27116722c22f69525b54631d93032b`
- locator integration: `2cc76a969e5b596ea5026960984b614608c39f23`
- run/job/artifact: locator更新時点では未確認

Immediate execution tasks:

1. Wait for the updated locator workflow to finish; do not redispatch gradient-clip-10 while a run is pending, queued or in progress.
2. Read the `gradient-clip-10` locator artifact and record exact run ID, job status, execution SHA and artifact list.
3. If no push run exists, classify `experiment_trigger_routing_failure`, repair only trigger/path routing, and preserve the declared factor unchanged.
4. If a run exists but has no job, inspect Actions policy/concurrency/capacity without changing model or hyperparameters.
5. If a job completes, inspect source-patch proof, all seed commands, checkpoints, matched predictions, diagnostics, resource metrics, leakage, parity and qualification.
6. If the immutable bundle is valid and Correct remains at/below Random, reject gradient-clipping threshold as the sole cause and immediately continue to optimizer/checkpoint restore integrity.
7. Do not close the iteration on an execution failure or negative performance result alone.

Fail-closed requirements:

1. The installed pinned `run_exp.py` contains clip `10.0` exactly once and clip `40.0` zero times.
2. Every seed command includes `--stateful` and `--unroll_length 80`.
3. Every seed command omits an explicit `--learning_rate` override.
4. Every checkpoint contains LSTM `core.*` weights and reaches the frame budget.
5. Correct / Random / Language-blind / State-only / Language-shuffle use identical instances.
6. Preserve model/checkpoint bytes、RSS、training wall、CPU latency.
7. Preserve seed、split、actual frames、logs、dependency lock、SHA-256.
8. Preserve leakage=false and prediction provenance.
9. Run official continuous-stream / fresh-instance parity.
10. Apply the unchanged qualification gate.

Decision rule:

- Invalid source routing: repair routing only and do not interpret performance.
- Correct success>0 and Correct beats Random in win rate and return: retain clip `10.0` as a candidate and verify three-seed minimum/resource cost.
- Valid clip `10.0` but Correct at/below Random: reject gradient-clipping threshold as sole cause and continue to optimizer/checkpoint restore integrity as exactly one next cause.
- Do not close with a negative result alone.

## P0 — Evaluation contract freeze

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで監査項目を増やさない。毎runでcontrols、resource、seed/split、checksums、leakageを保存する。

## P1 — External official reproductions

### J-CRe3

Ueda et al., LREC-COLING 2024、公式repository `riken-grp/J-CRe3`。exact commit、dataset、license、checksum、official commandを固定し、random、text-only、vision-only、mention-shuffle、frame/object-shuffleをmatched評価する。数値再現は0件。

### Latest prior-art boundary

CodeBind（Findings of ACL 2026）は、shared codebookとmodality-specific codebookによるshared/specific表現分解、compositional vector quantization、fully paired dataなしのbridging-modality alignmentを扱う。したがって、shared/specific decomposition、compositional codebook、incremental multimodal alignmentだけではRQ-001の新規性を認定しない。project pageは確認済みだが、author-official repositoryのexact commit、dependency、dataset command、immutable numerical reproductionは未完了。

既存のMagicBench、CausalDisenSeg、TRACE、DCAN、PCMCI、CausalLens、CTLD、score-based CRL、finite-sample CRL、LeGIT、GPI、Multi-View CRL、ReCITE、C3、MCDRL、CmIR、CAIR、Bayesian Ablation等もnovelty matrixの別列で維持し、論文値を本研究の能力証拠へ流用しない。

## P1 — R0.2 Environment-first

immutable R0.1 competence bundleが`qualified_for_r02=true`を満たした後のみ開始する。Environment-first、parameter-matched End-to-end、State-onlyを比較する。

## Closed — R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず棄却維持する。

## RQ-001

- 広義RQ-001: **棄却**
- 狭義RQ-001: **追加狭域化・未採用**

採用には、既存baselineを差し引いた後にも残るlanguage固有追加情報、countermodel pair、joint recoding不能な外部denotation law、事前登録済みclaim/counterexample/stopping ruleが必要。

正式境界:

> **FURTHER NARROWED BEYOND SHARED/SPECIFIC COMPOSITIONAL MULTIMODAL ALIGNMENT — NOT ADOPTED**

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Status

- immutable R0.1 artifacts: **7件**
- competent external baseline: **0件**
- J-CRe3 numerical reproduction: **0件**
- active screening: **gradient-clipping locator統合済み・run結果未確認**
- new mechanism family: **未認定**
- new intelligence principle: **未発見**
- capability progress: **未認定**
- 高校生級知能: **未達**
- 完成: **false**
