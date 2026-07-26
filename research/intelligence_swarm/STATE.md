# Intelligence Swarm State

## Mission

長期目標は、1GB未満で弱いスマートフォンCPU上でも高速に動作し、日本語コミュニケーション・知識・推論を備える知能モデルである。現在のR0では新しい機構族を作らず、公開baselineを固定資源制約下で再現し、失敗原因を潰して性能を最大化する。

## Current stage

- Stage: **R0 Research Reconstruction — constrained performance maximization**
- Canonical branch: `research/intelligence-swarm-reconstruction-001`
- A〜Dの新規toy仮説・別branch・新規機構族: **禁止**
- 既存stacked draft PR: **negative-results archive。新作業のbaseにしない**
- 外部baseline再現前の新規知能原理・能力進歩認定: **禁止**

## A–D responsibilities

- **A**: SILG/RTFM、J-CRe3/J-ORA、GPI、Multi-View CRL、ReCITEの公式再現とimmutable artifact保存。
- **B**: 実装・最適化・表現・探索/信号の失敗診断と、原因だけを変える最小run。
- **C**: 最新一次文献・公式codeとの重複監査、novelty matrix。
- **D**: frozen D015〜D035、matched controls、resource、leakage、RQ-001判定。

## Non-termination rule

「検証したが駄目だった」で終了しない。失敗runは、失敗分類、metric/log/code差分に基づく原因、最小修正、同一budget・instance再run、採用・棄却・停止判定まで未完了とする。文書・監査更新だけでiterationを閉じず、数値run requestまたは次の単一原因screening contractまで同じ統合内で発行する。

## R0 status ledger

- 公開環境control再現: **1件**
- immutable 131,072-frame R0.1 bundle: **1件・不合格**
- 学習済み公開能力baseline再現: **0件**
- J-CRe3 numerical reproduction: **0件**
- J-ORA numerical reproduction: **0件**
- GPI official-software reproduction: **0件**
- Multi-View CRL official-code reproduction: **0件**
- ReCITE official-code reproduction: **0件**
- R0.2正式再現: **0件**
- 実R0 bundleのevaluation contract通過: **0件**
- R0.3 hidden intervention-target ablation: **棄却**
- 広義RQ-001: **棄却**
- 狭義RQ-001: **未採用**
- 評価分類: **`initial_reproduction_failure` / `optimization_or_policy_competence_failure`**

## R0.1 SILG / RTFM

固定条件:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- official `multi` recurrent
- seeds `1,7,19`
- primary budget `131,072 requested frames`

### Immutable run 30203026269

- workflow head: `5d9f137296a64fc401560356470ac27f520cbeff`
- job `r01-public-reproduction`: **failure at qualification**
- training: 全seed `131,080` actual framesまで正常終了
- matched evaluation: 正常終了
- R0.2: qualification failureによりskip
- artifact ID: `8633105142`
- artifact name: `r01-silg-rtfm-matched-30203026269`
- artifact bytes: `72,686,203`
- artifact digest: `sha256:43ab7f1df82e9eba98c132b2e84a9ec55dbfdd726795fb43f7608fe288e00eef`
- answer leakage: `false`
- same-instance controls: 成立

性能:

- Correct win rate: `0/60 = 0.0000`
- Random win rate: `4/60 = 0.0667`
- Language-blind: `1/60 = 0.0167`
- State-only: `0/60 = 0.0000`
- Language-shuffle: `0/60 = 0.0000`
- Correct mean return: `-2.0749993`
- Random mean return: `-1.1513333`
- Correct−Random return: `-0.9236660`
- Correct mean episode length: `54.75`

資源:

- seed 1 training wall: `24:01.80`、peak RSS `1,442,552 KiB`
- seed 7 training wall: `24:10.06`、peak RSS `1,000,412 KiB`
- seed 19 training wall: `24:09.28`、peak RSS `1,235,964 KiB`
- matched evaluation wall: 約`150 s`
- matched evaluator peak RSS: `301,556 KiB`
- Correct CPU inference: seed別を含むartifactに保存。集約値は次screening比較時に固定する。

資格失敗:

- `zero_source_policy_success`
- `correct_not_above_random_win_rate`
- `correct_not_above_random_return`

これはimmutable artifact保存の成功であり、公開能力baseline再現または能力進歩ではない。

### Next screening

次runは公式SILG設定内の単一要因だけを変更する。

- changed factor: `entropy_cost 0.05 -> 0.005`
- rationale: pinned official `launch.py`に存在する残りのRTFM設定値を比較する
- fixed: model family、source pins、frames、seeds、split、actors、batch、unroll、same-instance controls
- required retest: Correct / Random / Language-blind / State-only / Language-shuffle
- reject entropy as sole cause if: CorrectがRandomを上回らない、またはCorrect successが0のまま
- failure後: 次の単一原因はofficial evaluation/default parity、recurrent/optimizer、learning-rate/gradientの順で選ぶ
- stop: 最大6 screening runまたは事前停止条件まで継続

## Evaluation contract

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。

毎runでrandom/language-blind/state-only/applicable shuffle、model/checkpoint bytes、peak RSS、runtime、CPU latency、seed、split、actual frames、commit、dependency、raw logs、checksums、leakageを保存する。

今回のbundleではartifact、source pins、actual frames、seeds、matched streams、checksums、leakageを保存した。一方、要求していたaction histogram、valid-action率、mask前後logit、invalid-action mass、gradient normの構造化出力は不足しており、次screening artifactで必須化する。

## Prior-art and RQ boundary

J-CRe3はLREC-COLING 2024の日本語実世界multimodal reference-resolution datasetであり、日本語groundingの外部baselineとして扱うが、SILG/RTFMのinteractive policy competenceを代替しない。

2025 score-based CRLと2026年有限標本CRLにより、unknown target、少数environment、finite-sample recoveryはRQ-001の新規性根拠から除外済みである。Markham et al.、Baumgartner et al.、LeGIT、GPI、Multi-View CRL、CmIR、ReCITEの境界を維持する。

今回の一次文献・公式code再監査では、既存境界を覆す新しい採用根拠を確認していない。CmIRはACL 2026一次論文を確認済みだがauthor-official code未固定、J-CRe3は一次論文を確認済みで数値再現未完了である。

正式判断:

> **RQ-001: NARROWED BEYOND LANGUAGE-GUIDED TARGET SELECTION, INTERVENTION-CONDITIONED COMPOSITION, GENERATIVE-REPRESENTATION CAUSAL INFERENCE, PARTIALLY OBSERVED MULTI-VIEW CRL, LOCAL-STRUCTURE DYNAMICAL-SYSTEM IDENTIFICATION, MULTIMODAL CAUSAL-INVARIANT DECOMPOSITION, AND LANGUAGE-ONLY CAUSAL-RELATION INFERENCE — NOT ADOPTED**

採用には、上記baseline再現後にも残るcountermodel pair、外部固定でjoint recoding不能なdenotation law、language固有追加情報の直接証拠、事前登録済みclaim/counterexample/stopping ruleが必要。

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Current status

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 完成: **false**

## Last integration

2026-07-26: **RESET-E054**。run `30203026269`の131,072-frame × 3-seed学習、matched controls、immutable artifact保存を確認した。qualificationはCorrect `0/60`、Random `4/60`、Correct−Random return `-0.9236660`で棄却された。R0.2をskipし、`entropy_cost 0.05 -> 0.005`だけを変える次screeningを継続する。能力進歩未認定、高校生級未達を維持する。