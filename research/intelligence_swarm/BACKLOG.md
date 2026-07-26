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

### Closed cause: entropy cost

Valid source run `30215555334` and requalification run `30219453396` established:

- `entropy_cost=0.005` reached every seed command
- Correct `0/60`
- Random `4/60`
- Language-blind `2/60`
- State-only `0/60`
- Language-shuffle `0/60`
- corrected official continuous-stream parity audit passed
- qualification rejected with `zero_source_policy_success`, `correct_not_above_random_win_rate`, `correct_not_above_random_return`

Decision:

- entropy reduction as sufficient single cause: **rejected**
- evaluation protocol mismatch as main cause: **rejected**

### Active single-factor screening: official stateful flag

公式`vzhong/silg`の`model.multi.Model`は`flags.stateful=true`の場合だけ`nn.LSTM` coreを生成する。parser defaultはfalseである。従来training commandは`--stateful`を含まず、全seedのdiagnostic recurrent-state normは常に0だった。

したがって従来bundleの正確な名称は`official multi non-stateful`であり、competent recurrent baseline再現ではない。

次runの変更要因は一つだけ:

- `stateful: false → true`

固定するもの:

- entropy cost `0.05`
- actors `2`
- threads `1`
- batch size `2`
- unroll length `20`
- model family `multi`
- frame budget、seeds、split、instances、controls

実行経路:

- patch contract: `patch_silg_stateful_screening.py`
- workflow: `.github/workflows/r01_silg_stateful_screening.yml`

必須fail-closed証拠:

1. 全seed commandに`--stateful`
2. 全checkpointに`core.*` LSTM weight
3. 全seedのdiagnostic `recurrent_state_l2_after_mean > 0`
4. Correct / Random / Language-blind / State-only / Language-shuffle
5. same-instance topology
6. model/checkpoint bytes、RSS、training wall、CPU latency
7. seed、split、actual frames、raw logs、dependency lock、SHA-256
8. leakage false
9. official continuous-stream / fresh-instance parity
10. unchanged qualification gate

判定:

- CorrectがRandomを上回りCorrect success>0ならstateful factorを採用候補とし、three-seed最低値と資源制約を確認する。
- recurrent stateが有効でもcompetenceがない場合、stateful不足単独原因を棄却し、次は公式defaultとの最大差である`unroll_length: 20 → 80`を単一要因として検証する。
- factor routingやcheckpoint core証明が失敗した場合は性能結果として扱わず、配線だけを修復して同一runを再実行する。
- 「駄目だった」で終了しない。

## P0 — Evaluation contract freeze

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで監査項目を増やさない。毎runでcontrols、resource、seed/split、checksums、leakageを保存する。

## P1 — External official reproductions

### J-CRe3

Ueda et al., LREC-COLING 2024、公式repository `riken-grp/J-CRe3`。exact commit、dataset、license、checksum、official commandを固定し、random、text-only、vision-only、mention-shuffle、frame/object-shuffleをmatched評価する。数値再現は0件。

### Adjacent prior art

score-based CRL、finite-sample CRL、LeGIT、GPI、Multi-View CRL、ReCITE、C3、MCDRL、CmIR、CAIRをnovelty matrixの別列で維持する。論文値を本研究の能力証拠へ流用しない。

CAIRはrationaleをcausal mediatorとして扱い、interventional utilityをreward化するmultimodal emotion reasoningである。causal-mediator reward、information bottleneck adaptive optimization、rationale faithfulnessだけではRQ-001を採用しない。

## P1 — R0.2 Environment-first

immutable R0.1 competence bundleが`qualified_for_r02=true`を満たした後のみ開始する。Environment-first、parameter-matched End-to-end、State-onlyを比較する。

## Closed — R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず棄却維持する。

## RQ-001

- 広義RQ-001: **棄却**
- 狭義RQ-001: **追加狭域化・未採用**

採用には、既存baselineを差し引いた後にも残るlanguage固有追加情報、countermodel pair、joint recoding不能な外部denotation law、事前登録済みclaim/counterexample/stopping ruleが必要。

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Status

- immutable R0.1 artifacts: **4件**
- competent external baseline: **0件**
- J-CRe3 numerical reproduction: **0件**
- active stateful screening: **実行要求発行対象**
- 新規機構族: **未認定**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- 完成: **false**
