# Intelligence Swarm Backlog

## Operating rule

R0はcanonical branch `research/intelligence-swarm-reconstruction-001`だけで進める。A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。

外部baselineを再現するまで、新規機構族、新しい知能原理、能力進歩、高校生級到達を認定しない。単発失敗で終了せず、失敗分類、根拠、原因だけを変える最小修正、同一budget再run、採用・棄却・停止判定までを1サイクルとする。高コスト学習済みartifactが有効なら、監査障害だけを直すために再学習してはならない。

## A–D allocation

- **A**: SILG/RTFM、J-CRe3、J-ORA、GPI、Multi-View CRL、ReCITEの公式code・dataset・command・dependency固定と無改変再現。
- **B**: 実装不一致、最適化不足、表現ボトルネック、探索・学習信号不足の診断と制約内最適化。
- **C**: 最新一次文献・公式codeとの重複監査、novelty matrix更新。
- **D**: D015〜D035、matched controls、resource provenance、leakage、RQ-001判定。

## P0 — SILG/RTFM R0.1 screening cycle

固定条件:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- official `multi` recurrent
- seeds `1,7,19`
- `131,072 requested frames`
- train `silg:rtfm_train_s1-v0`
- test `silg:rtfm_test_s1-v0`

### Baseline immutable failure: run 30203026269

- artifact ID `8633105142`
- Correct `0/60`、Random `4/60`、Language-blind `1/60`、State-only `0/60`、Language-shuffle `0/60`
- Correct return `-2.0749993`、Random return `-1.1513333`
- same-instance成立、answer leakage `false`

### Invalid screening execution: run 30208660095

要求`entropy_cost=0.005`に対し全seedの実commandが`0.05`だった。artifact `8634594371`は0.05の追加negative resultとしてのみ保存する。

### Valid screening execution: run 30215555334

- job ID `89830932884`
- execution commit `cbd4af3d89718df76cc481f7c730ed80334ef223`
- artifact ID `8636643017`
- artifact digest `sha256:094ba8d6fba428c15e1dfa43298f3af9943d9fae840a072a691d3f420c5bcec2`
- artifact size `72,690,803 bytes`
- `entropy_cost=0.005`は全seedの完全commandへ到達済み
- actual framesは全seed `131,080`
- peak RSS `1,370,676 / 1,337,440 / 1,247,468 KiB`
- training wall `1447.61 / 1519.27 / 1436.77 s`
- Correct `0/60`
- Random `4/60`
- Language-blind `2/60`
- State-only `0/60`
- Language-shuffle `0/60`
- Correct return `-2.1523326`
- Random return `-1.1513333`
- same-instance成立
- chosen-action valid fractionは全seed `1.0`
- masked policy entropy平均はseed 1/7/19で`1.273 / 1.216 / 1.133`

数値上、entropy低下はbaseline competenceを改善せず、`entropy_cost`単独原因は棄却候補。ただしqualificationが監査実装障害でskipされたため、以下を完了するまでiterationを閉じない。

### Immediate recovery task: artifact-only requalification

1. `.github/workflows/r01_silg_entropy_requalify.yml`でsource run `30215555334`、artifact `r01-silg-rtfm-entropy-0005-30215555334`を取得する。
2. source bundleのentropy値、seed topology、checkpoint、actual framesをfail-closed確認する。
3. pinned SILG/RTFMを再導入する。
4. 修正済み`audit_silg_official_eval_parity.py`でofficial continuous streamとfresh seeded instancesを再比較する。
5. 既存matched resultへ`qualify_r01_source_policy.py`を無変更適用する。
6. requalification run ID、artifact ID/digest、parity JSON、qualification JSON、checksumを保存する。
7. 高コストtrainingは再実行しない。

### Root cause fixed

`Environment.initial()`は新しいepisodeの境界として`done=True`を含むが、parity監査のfresh-instance経路だけがこれを終了済みと解釈してstepを0回にした。`run_silg_matched_eval.py`と同様にlocal `done=False`で開始し、最初の`env.step()`後からdoneを読むよう修正した。

### Decision after requalification

- qualificationが`zero_source_policy_success`、`correct_not_above_random_win_rate`、`correct_not_above_random_return`なら、entropy単独原因を正式棄却する。
- parityに大きな差がありofficial protocolだけがcompetenceを示す場合、次の単一原因をevaluation/default parityとする。
- 両protocolでcompetenceがない場合、次の単一原因をrecurrent state / optimizer restoreへ進める。
- いずれの場合も「駄目だった」で終了せず、次screening contractを同じcanonical branchへ発行する。

## P0 — Evaluation contract freeze

D015〜D035を凍結する。今回の変更は新規auditorではなく、既存parity監査のzero-step bug修正である。実bundleが具体的なfalse pass/failureを示すまで監査項目を増やさない。

毎runでrandom/language-blind/state-only/applicable shuffle、model/checkpoint bytes、RSS、runtime、CPU latency、seed、split、actual frames、commit、dependency、raw logs、checksums、leakageを保存する。

## P1 — External official reproductions

### J-CRe3

Ueda et al., LREC-COLING 2024、公式repository `riken-grp/J-CRe3`。exact commit、dataset、license、checksum、official commandを固定し、random、text-only、vision-only、mention-shuffle、frame/object-shuffleをmatched評価する。

### ReCITE

ACL 2026のlanguage-only causal relation benchmarkとして別列で扱う。exact commit、dataset release、official split、prompt/model/temperature/seed、RSS/runtime、raw predictions、random/entity-order/marker/sentence shuffleを保存する。

### Multi-View CRL / GPI / C3 / MCDRL / CmIR

各official codeの有無、exact commit、dependency、dataset、主表command、model/RSS/runtime/seed/split/raw output/checksumを固定する。論文値を本研究の能力証拠へ流用しない。

## P1 — R0.2 Environment-first

immutable R0.1 competence bundleが`qualified_for_r02=true`を満たした後のみ開始する。Environment-first、parameter-matched End-to-end、State-onlyを比較し、source policy competence、3-seed平均改善、最低seed非悪化、next-state prediction、action accuracy、online task successを確認する。

## Closed — R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず棄却維持する。

## Prior-art and RQ-001

score-based CRL、finite-sample CRL、LeGIT、GPI、Multi-View CRL、CmIR、ReCITE、C3、MCDRL等の境界を維持する。

C038としてACL 2026 **Learning Invariant Modality Representation for Robust Multimodal Learning from a Causal Inference Perspective**を明示する。各modalityのcausal-invariant / environment-specific spurious分解、invariance・mutual-information・reconstruction制約、OOD/noise robustnessだけではRQ-001の新規性を認定しない。ACL Anthology一次論文は確認済みだが、掲載ページ上にauthor-official codeは確認できず、公式再現は0件である。

- 広義RQ-001: **棄却**
- 狭義RQ-001: **追加狭域化・未採用**

採用には、既存baselineを差し引いた後にも残るlanguage固有追加情報、countermodel pair、joint recoding不能な外部denotation law、事前登録済みclaim/counterexample/stopping ruleが必要。

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Status

- immutable R0.1 bundle: **3件**
- valid entropy=0.005 screening: **artifact保存済み・requalification中**
- 外部baseline再現: **0件**
- 新規機構族: **未認定**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- 完成: **false**
