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

### Completed unroll-80 evidence

- run `30226976064`, job `89867137085`
- artifact `8640762353`
- digest `sha256:4e7fbacc077121d3fd09db1f6b7ec19a00942f8dc4cbf29b6cb9fd6eb18c9f4c`
- Correct `2/60`, Random `4/60`
- Language-blind `2/60`, State-only `0/60`, Language-shuffle `2/60`
- Correct return `-1.8059994`, Random return `-1.1513333`
- parameters `6,200,115`
- actual frames `131,200` per seed
- peak RSS `1,699,780 / 1,467,976 / 2,498,024 KiB`
- wall `1479.48 / 1479.02 / 1560.07 s`
- CPU forward approximately `7.86–8.00 ms/step`
- stateful routing、unroll-80 routing、LSTM checkpoint、recurrent state、same-instance、parity、leakage: passed
- qualification: rejected

Learner logs show large sign-changing policy-gradient and total-loss oscillations through the final updates. Because unroll=80 was correctly routed yet competence remained below Random, unroll shortage is rejected as the sole cause.

### Active single-factor screening: learning rate

Change exactly one factor:

- add explicit `learning_rate=0.0001`

Keep fixed:

- `stateful=true`
- `unroll_length=80`
- entropy cost `0.05`
- actors `2`
- threads `1`
- batch size `2`
- model family `multi`
- frames、seeds、split、instances、controls

Implementation:

- patch: `patch_silg_learning_rate_screening.py`
- workflow: `.github/workflows/r01_silg_learning_rate_screening.yml`
- reference run: `30226976064`
- reference artifact: `8640762353`

Primary execution:

- run `30235108376`
- job `89881341003`
- execution commit `67556f067028edac502380c6d3de15575c996ffc`
- install、stateful/unroll/lr patch、schema、random control: passed
- active step: three-seed training
- artifact / qualification / performance: not yet available

Duplicate/fallback execution:

- run `30236217754`
- execution commit `b3f1c6775fb6be5376ff53359b6732dfb100f313`
- status: pending
- jobs: 0
- artifacts: 0
- primary runが有効artifactを保存した場合は重複証拠に数えない。
- primary runがexecution failureまたはartifact lossの場合だけfallbackとして使用する。
- 同条件を追加dispatchしない。

Fail-closed requirements:

1. Every seed command includes `--stateful`.
2. Every seed command includes `--unroll_length 80`.
3. Every seed command includes `--learning_rate 0.0001`.
4. Every checkpoint contains LSTM `core.*` weights and reaches the frame budget.
5. Correct / Random / Language-blind / State-only / Language-shuffle use identical instances.
6. Preserve model/checkpoint bytes、RSS、training wall、CPU latency.
7. Preserve seed、split、actual frames、logs、dependency lock、SHA-256.
8. Preserve leakage=false and prediction provenance.
9. Run official continuous-stream / fresh-instance parity.
10. Apply the unchanged qualification gate.

Decision rule:

- If routing is invalid, repair routing only; do not interpret performance.
- If Correct success>0 and Correct beats Random in both win rate and return, retain learning-rate reduction as a candidate and verify three-seed minimum/resource cost.
- If routing is valid but Correct remains at/below Random, reject learning rate as the sole cause and continue to exactly one of gradient clipping or optimizer/checkpoint restore based on the saved logs and official-code comparison.
- Do not close with a negative result alone.

## P0 — Evaluation contract freeze

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで監査項目を増やさない。毎runでcontrols、resource、seed/split、checksums、leakageを保存する。

## P1 — External official reproductions

### J-CRe3

Ueda et al., LREC-COLING 2024、公式repository `riken-grp/J-CRe3`。exact commit、dataset、license、checksum、official commandを固定し、random、text-only、vision-only、mention-shuffle、frame/object-shuffleをmatched評価する。数値再現は0件。

### Latest prior-art boundary

CausalDisenSeg（arXiv 2026）は、missing-modality brain-tumor segmentationに対して、CVAE+HSICによるcausal/style factor分離、region causality module、counterfactual dual-adversarial抑制でbiasのNatural Direct Effectを抑える。missing-modality下のcausal disentanglement、region-grounded causal representation、counterfactual NDE suppressionだけではRQ-001の新規性を認定しない。一次preprintは確認済みだが、author-official repository、exact commit、immutable numerical reproductionは未確認。

既存のTRACE、DCAN、PCMCI、CausalLens、CTLD、score-based CRL、finite-sample CRL、LeGIT、GPI、Multi-View CRL、ReCITE、C3、MCDRL、CmIR、CAIR、Bayesian Ablation等もnovelty matrixの別列で維持し、論文値を本研究の能力証拠へ流用しない。

## P1 — R0.2 Environment-first

immutable R0.1 competence bundleが`qualified_for_r02=true`を満たした後のみ開始する。Environment-first、parameter-matched End-to-end、State-onlyを比較する。

## Closed — R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず棄却維持する。

## RQ-001

- 広義RQ-001: **棄却**
- 狭義RQ-001: **追加狭域化・未採用**

採用には、既存baselineを差し引いた後にも残るlanguage固有追加情報、countermodel pair、joint recoding不能な外部denotation law、事前登録済みclaim/counterexample/stopping ruleが必要。

正式境界:

> **FURTHER NARROWED BEYOND COUNTERFACTUAL CAUSAL DISENTANGLEMENT UNDER MISSING MODALITIES — NOT ADOPTED**

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Status

- immutable R0.1 artifacts: **6件**
- competent external baseline: **0件**
- J-CRe3 numerical reproduction: **0件**
- active screening: **learning-rate primary run training中**
- new mechanism family: **未認定**
- new intelligence principle: **未発見**
- capability progress: **未認定**
- 高校生級知能: **未達**
- 完成: **false**