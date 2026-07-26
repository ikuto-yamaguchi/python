# Intelligence Swarm Backlog

## Operating rule

R0はcanonical branch `research/intelligence-swarm-reconstruction-001`だけで進める。A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。

外部baselineを再現するまで、新規機構族、新しい知能原理、能力進歩、高校生級到達を認定しない。単発失敗で終了せず、失敗分類、根拠、原因だけを変える最小修正、同一budget再run、採用・棄却・停止判定までを1サイクルとする。

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
- `131,072 requested frames`、actual `131,080` frames
- train `silg:rtfm_train_s1-v0`
- test `silg:rtfm_test_s1-v0`

### Completed immutable failure: run 30203026269

- job: `r01-public-reproduction`
- conclusion: qualification failure
- artifact ID: `8633105142`
- artifact bytes: `72,686,203`
- artifact digest: `sha256:43ab7f1df82e9eba98c132b2e84a9ec55dbfdd726795fb43f7608fe288e00eef`
- three checkpoints: 保存済み
- same-instance matched controls: 成立
- answer leakage: `false`
- R0.2: skip

Results:

- Correct `0/60`、win rate `0.0000`、return `-2.0749993`
- Random `4/60`、win rate `0.0667`、return `-1.1513333`
- Language-blind `1/60`
- State-only `0/60`
- Language-shuffle `0/60`
- Correct−Random return `-0.9236660`

Resources:

- seed 1: wall `24:01.80`、peak RSS `1,442,552 KiB`
- seed 7: wall `24:10.06`、peak RSS `1,000,412 KiB`
- seed 19: wall `24:09.28`、peak RSS `1,235,964 KiB`
- matched evaluation: 約`150 s`、peak RSS `301,556 KiB`

Classification:

- `initial_reproduction_failure`
- substantive: `optimization_or_policy_competence_failure`
- failures: `zero_source_policy_success`、`correct_not_above_random_win_rate`、`correct_not_above_random_return`

このrunはimmutable evidence保存の前進だが、公開能力baseline再現ではない。

### Active next run: R01-SCREEN-002

変更する要因は1つだけ:

- `entropy_cost: 0.05 -> 0.005`

根拠:

- pinned official SILG `launch.py`にRTFM用として両値が存在する。
- 直近immutable runは`0.05`だけを評価した。
- architecture、source、data、frames、seeds、split、actors、batch、unroll、matched instancesは変更しない。

必須出力:

1. Correct / Random / Language-blind / State-only / Language-shuffleのsame-instance結果。
2. checkpoint bytes・SHA-256・actual frames。
3. model parameters/state bytes、peak RSS、training wall、CPU latency。
4. seed、split、dependency lock、raw logs、artifact digest。
5. answer leakage、schema leakage、prediction provenance。
6. action histogram、valid-action率、policy entropy、episode length、reward到達率。
7. mask前後logit、invalid-action mass、gradient norm、policy/value loss。

採用条件:

- Correct success > 0
- Correct win rate > Random
- Correct return > Random
- 3-seed平均改善かつ最低seedを悪化させない
- language使用案ではLanguage-blind / State-only / Language-shuffleを上回る

棄却条件:

- 同一契約でCorrectがRandomを上回らない、またはCorrect successが0なら、`entropy_cost`単独原因を棄却する。

次の原因順序:

1. official evaluation/default parity
2. recurrent reset/detach、optimizer/checkpoint restore
3. learning rate、gradient clipping、unroll
4. parameter数±2%以内の容量配分
5. language/state fusion位置

最大6 screening runまたは事前停止条件まで継続する。「検証したが駄目」でcycleを閉じない。

## P0 — Evaluation contract freeze

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。

毎runで、matched random/language-blind/state-only/applicable shuffle、model/checkpoint bytes、peak RSS、training runtime、CPU latency、seed、split、actual frames、commit、dependency、raw logs、checksums、leakageを保存する。

run `30203026269`では主要artifactとleakageは保存できたが、action histogram、valid-action率、mask前後logit、invalid-action mass、gradient normの構造化診断が不足した。次runではこれを欠落させない。監査codeの回帰成功は数値baseline再現には数えない。

## P1 — J-CRe3

一次論文はUeda et al., LREC-COLING 2024、公式repositoryは `riken-grp/J-CRe3`。

1. exact commit、dataset、license、容量、checksumを固定する。
2. official baseline、dependency、evaluation commandを無改変で実行する。
3. model bytes、RSS、runtime、seed、split、prediction、raw log、checksumを保存する。
4. random、text-only、vision-only、mention-shuffle、frame/object-shuffleを事前登録する。
5. 失敗分類と最小修正を行い、単発失敗で終了しない。

J-CRe3は日本語multimodal reference resolution baselineであり、SILGのinteractive policy competenceを代替しない。

## P1 — ReCITE official-code reproduction

Saklad et al., ACL 2026のReCITEは実世界textから因果関係を抽出・推論するbenchmarkであり、hidden intervention-target recoveryやinteractive policy competenceとは別列で扱う。

1. exact commit、dataset release、license、checksum、task schemaを固定する。
2. official evaluation commandとreported splitを無改変で再現する。
3. model、prompt、temperature、seed、runtime、peak RSS、raw predictions、scoreを保存する。
4. random label、entity/order shuffle、causal-marker masking、sentence shuffle、retrieval-onlyを事前登録する。
5. 失敗時は単一原因rerunへ接続する。

## P1 — Multi-View CRL official-code reproduction

Yao et al., ICLR 2024の公式repository `CausalLearningAI/multiview-crl` を対象とする。exact commit・environment・dataset checksumを固定し、official three-view実験とtext/image removal、text/cross-instance shuffle、random representationを比較する。

## P1 — GPI official-software reproduction

canonical repository、PyPI、documentation version、exact commitを固定し、text-as-treatment公開exampleを無改変再現する。representationなし、random、shuffle、alternative frozen representationをmatched比較する。

## P1 — R0.2 Environment-first

immutable R0.1 competence bundleが `qualified_for_r02=true` を満たした後のみ開始する。Environment-first、parameter-matched End-to-end、State-onlyを比較し、source policy competence、3-seed平均改善、最低seed非悪化、next-state prediction、action accuracy、online task successを確認する。

## Closed — R0.3

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず棄却維持する。

## Prior-art and RQ-001

既存境界として、score-based CRL、有限標本CRL、Markham et al.、Baumgartner et al.、LeGIT、GPI、Multi-View CRL、CmIR、ReCITEを維持する。

今回の最新一次文献・公式code再監査では、この境界を覆す採用根拠を確認していない。CmIRはACL 2026一次論文確認済み・author-official code未固定、J-CRe3は一次論文確認済み・数値再現未完了である。

- 広義RQ-001: **棄却**
- 狭義RQ-001: **追加狭域化・未採用**

採用には、既存baselineを差し引いた後にも残るlanguage固有追加情報、countermodel pair、joint recoding不能な外部denotation law、事前登録済みclaim/counterexample/stopping ruleが必要。

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Status

- immutable R0.1 bundle: **1件・不合格**
- 外部baseline再現: **0件**
- 新規機構族: **未認定**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- 完成: **false**
