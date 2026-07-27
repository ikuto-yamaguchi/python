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

Stateful primary evidence:

- run `30221587227`, job `89844840438`
- artifact `8638198496`
- digest `sha256:ae28542e4bda4ca968de9d7ffc42b5ab4b4dadb518a26636a41d63b92131aa31`
- Correct `2/60`, Random `4/60`
- Language-blind `2/60`, State-only `1/60`, Language-shuffle `2/60`
- Correct return `-1.8273327`, Random return `-1.1513333`
- parameters `6,200,115`
- CPU forward `8.162 ms/step`
- actual frames `131,080` per seed
- peak RSS `1,069,864 / 1,334,592 / 1,274,272 KiB`
- wall `1691.39 / 1569.14 / 1686.73 s`
- stateful routing、LSTM checkpoint、recurrent state、same-instance、parity、leakage: passed
- qualification rejected

### Active single-factor screening: official unroll length

Change exactly one factor:

- `unroll_length: 20 → 80`

Keep fixed:

- `stateful=true`
- entropy cost `0.05`
- actors `2`
- threads `1`
- batch size `2`
- model family `multi`
- frames、seeds、split、instances、controls

Execution:

- patch: `patch_silg_unroll80_screening.py`
- workflow: `.github/workflows/r01_silg_unroll80_screening.yml`
- request: `R01_RUN_REQUEST.json`
- active run: `30226976064`
- active job: `89867137085`
- execution head: `344002bc8e5130cbb9a302fda1a2115baa8edb1c`
- current status: **in_progress**
- completed steps: checkout、Python setup、provenance、pinned install、stateful patch、unroll-80 patch、schema、random control
- active step: **Train official stateful multi with unroll 80**
- artifacts: **0（学習中）**

Monitoring repair:

- existing locator omitted `r01_silg_unroll80_screening.yml`
- locator matrix/path trigger fixed in commit `746d527a0d760cc4e910e13d8913c040ee8afd5f`
- locator run `30228319127` succeeded
- run `30226976064` has now created job `89867137085`; do not issue a duplicate while it is queued/in-progress

Fail-closed requirements:

1. Every seed command includes `--stateful`.
2. Every seed command has `--unroll_length 80`.
3. Every checkpoint contains LSTM `core.*` weights.
4. Every seed has non-zero recurrent-state diagnostics.
5. Correct / Random / Language-blind / State-only / Language-shuffle use identical instances.
6. Preserve model/checkpoint bytes、RSS、training wall、CPU latency.
7. Preserve seed、split、actual frames、logs、dependency lock、SHA-256.
8. Preserve leakage=false and prediction provenance.
9. Run official continuous-stream / fresh-instance parity.
10. Apply the unchanged qualification gate.

Decision rule:

- While training is active, only monitor the existing run; do not mutate model factors or dispatch duplicates.
- If factor routing is invalid, repair routing only; do not interpret performance.
- If Correct success>0 and Correct beats Random in both win rate and return, promote unroll=80 to a candidate and verify the three-seed minimum and resource cost.
- If routing is valid but Correct remains at/below Random, reject unroll shortage as the sole cause and continue to one evidence-selected learner-optimization factor.
- Do not close with a negative result alone.

Next-cause selection after a valid unroll rejection:

Choose exactly one of learning rate、gradient clipping、optimizer/checkpoint restore based on preserved learner logs and code/default comparison. Do not sweep all three simultaneously.

## P0 — Evaluation contract freeze

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで監査項目を増やさない。毎runでcontrols、resource、seed/split、checksums、leakageを保存する。

## P1 — External official reproductions

### J-CRe3

Ueda et al., LREC-COLING 2024、公式repository `riken-grp/J-CRe3`。exact commit、dataset、license、checksum、official commandを固定し、random、text-only、vision-only、mention-shuffle、frame/object-shuffleをmatched評価する。数値再現は0件。

### Latest prior-art boundary

ACL Findings 2026のTRACEは、multi-turn dialogueを通じたunderlying causal graphのonline reconstructionを定式化し、探索段階のcausal-graph reconstruction rewardと、介入段階のtargeted belief restructuring rewardを用いる。dialogue-driven causal-graph exploration、causal-graph reward、二段階のexploration/intervention RLだけではRQ-001の新規性を認定しない。ACL一次論文は確認済みだが、author-official repository、exact commit、dependency、dataset、公式commandは未確認であり、immutable reproductionは0件。SILG/J-CRe3の代替baselineではない。

DCAN、PCMCI、CausalLens、CTLD、score-based CRL、finite-sample CRL、LeGIT、GPI、Multi-View CRL、ReCITE、C3、MCDRL、CmIR、CAIR等もnovelty matrixの別列で維持し、論文値を本研究の能力証拠へ流用しない。

## P1 — R0.2 Environment-first

immutable R0.1 competence bundleが`qualified_for_r02=true`を満たした後のみ開始する。Environment-first、parameter-matched End-to-end、State-onlyを比較する。

## Closed — R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず棄却維持する。

## RQ-001

- 広義RQ-001: **棄却**
- 狭義RQ-001: **追加狭域化・未採用**

採用には、既存baselineを差し引いた後にも残るlanguage固有追加情報、countermodel pair、joint recoding不能な外部denotation law、事前登録済みclaim/counterexample/stopping ruleが必要。

正式境界:

> **FURTHER NARROWED BEYOND DIALOGUE-DRIVEN CAUSAL-GRAPH EXPLORATION AND TARGETED INTERVENTION — NOT ADOPTED**

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Status

- immutable R0.1 artifacts: **5件**
- competent external baseline: **0件**
- J-CRe3 numerical reproduction: **0件**
- active screening: **unroll-80 run 30226976064 / job 89867137085 training中**
- 新規機構族: **未認定**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- 完成: **false**