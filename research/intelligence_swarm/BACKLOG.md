# Intelligence Swarm Backlog

## Operating rule

R0はcanonical branch `research/intelligence-swarm-reconstruction-001`だけで進める。A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。

外部baselineを再現するまで、新規機構族、新しい知能原理、能力進歩、高校生級到達を認定しない。単発失敗で終了せず、失敗分類、根拠、原因だけを変える最小修正、同一budget再run、採用・棄却・停止判定までを1サイクルとする。宣言した変更値が実commandへ到達していないrunは仮説検証として無効とする。

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
- digest `sha256:43ab7f1df82e9eba98c132b2e84a9ec55dbfdd726795fb43f7608fe288e00eef`
- Correct `0/60`、Random `4/60`、Language-blind `1/60`、State-only `0/60`、Language-shuffle `0/60`
- Correct return `-2.0749993`、Random return `-1.1513333`
- answer leakage `false`、same-instance成立

### Invalid screening execution: run 30208660095

- artifact ID `8634594371`
- digest `sha256:aa2efd6a30d26074a4ddf39195b93f8dc046f164f87446a384e7d808bd5e5fbf`
- intended factor: `entropy_cost=0.005`
- actual factor in every seed command: `entropy_cost=0.05`
- Correct `3/60`、Random `4/60`、Language-blind `3/60`、State-only `1/60`、Language-shuffle `3/60`
- Correct return `-1.6356662`、Random return `-1.1513333`
- qualification: `correct_not_above_random_win_rate`、`correct_not_above_random_return`
- answer leakage `false`、same-instance成立

このrunは0.005仮説の採否に使わない。0.05の追加seed反復としてnegative result archiveへ保存する。

### Active corrected run: R01-SCREEN-002-E057

変更要因は1つだけ:

- `entropy_cost: 0.05 -> 0.005`

実行修正:

- `.github/workflows/r01_silg_entropy_screening.yml`
- commit `54a1f1f3c09ed0a8d526ae4d877057cfa33cd3d6`
- training summary top-level、各seed record、各seed commandの3箇所で`0.005`をfail-closed検証する。
- 1箇所でも不一致ならmatched evaluation前に失敗させ、性能仮説の結果として扱わない。

固定:

- architecture、source pins、dataset、frames、seeds、split、actors、batch、unroll、matched instances

必須出力:

1. Correct / Random / Language-blind / State-only / Language-shuffleのsame-instance結果。
2. checkpoint bytes・SHA-256・actual frames。
3. model parameters/state bytes、peak RSS、training wall、CPU latency。
4. seed、split、dependency lock、raw logs、artifact digest。
5. answer leakage、schema leakage、prediction provenance。
6. action histogram、valid-action率、policy entropy、episode length、reward到達率。
7. mask前後logit、invalid-action mass、gradient norm、policy/value loss。
8. 実際に適用されたentropy valueと完全command。

採用条件:

- Correct success > 0
- Correct win rate > Random
- Correct return > Random
- 3-seed平均改善かつ最低seedを悪化させない
- Language-blind / State-only / Language-shuffleを上回る

棄却条件:

- `0.005`適用が証明された同一契約runでCorrectがRandomを上回らない、またはCorrect successが0なら、entropy cost単独原因を棄却する。

次の原因順序:

1. official evaluation/default parity
2. recurrent reset/detach、optimizer/checkpoint restore
3. learning rate、gradient clipping、unroll
4. parameter数±2%以内の容量配分
5. language/state fusion位置

最大6 screening runまたは事前停止条件まで継続する。「検証したが駄目」でcycleを閉じない。

## P0 — Evaluation contract freeze

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。

毎runで、matched random/language-blind/state-only/applicable shuffle、model/checkpoint bytes、peak RSS、training runtime、CPU latency、seed、split、actual frames、commit、dependency、raw logs、checksums、leakageを保存する。監査codeの回帰成功は数値baseline再現には数えない。

## P1 — External official reproductions

### J-CRe3

一次論文はUeda et al., LREC-COLING 2024、公式repositoryは `riken-grp/J-CRe3`。exact commit、dataset、license、checksum、official commandを固定し、random、text-only、vision-only、mention-shuffle、frame/object-shuffleをmatched評価する。

### ReCITE

ACL 2026のlanguage-only causal relation benchmarkとして別列で扱う。exact commit、dataset release、official split、prompt/model/temperature/seed、RSS/runtime、raw predictions、random/entity-order/marker/sentence shuffleを保存する。

### Multi-View CRL / GPI / C3 / MCDRL

各official codeのexact commit、dependency、dataset、主表command、model/RSS/runtime/seed/split/raw output/checksumを固定する。これらの論文値を本研究の能力証拠へ流用しない。

## P1 — R0.2 Environment-first

immutable R0.1 competence bundleが `qualified_for_r02=true` を満たした後のみ開始する。Environment-first、parameter-matched End-to-end、State-onlyを比較し、source policy competence、3-seed平均改善、最低seed非悪化、next-state prediction、action accuracy、online task successを確認する。

## Closed — R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず棄却維持する。

## Prior-art and RQ-001

score-based CRL、finite-sample CRL、LeGIT、GPI、Multi-View CRL、CmIR、ReCITE、C3 Regularization、MCDRL等の境界を維持する。今回の最新一次文献再監査でも、これらを越えるRQ-001採用根拠は得られていない。

- 広義RQ-001: **棄却**
- 狭義RQ-001: **追加狭域化・未採用**

採用には、既存baselineを差し引いた後にも残るlanguage固有追加情報、countermodel pair、joint recoding不能な外部denotation law、事前登録済みclaim/counterexample/stopping ruleが必要。

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Status

- immutable R0.1 bundle: **2件・不合格**
- valid entropy=0.005 screening: **未完了**
- 外部baseline再現: **0件**
- 新規機構族: **未認定**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- 完成: **false**