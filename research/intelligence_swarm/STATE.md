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

- **A**: SILG/RTFM、J-CRe3/J-ORA、GPI、Multi-View CRLの公式再現とimmutable artifact保存。
- **B**: 実装・最適化・表現・探索/信号の失敗診断と、原因だけを変える最小run。
- **C**: 最新一次文献・公式codeとの重複監査、novelty matrix。
- **D**: frozen D015〜D035、matched controls、resource、leakage、RQ-001判定。

## Non-termination rule

「検証したが駄目だった」で終了しない。失敗runは、失敗分類、metric/log/code差分に基づく原因、最小修正、同一budget・instance再run、採用・棄却・停止判定まで未完了とする。文書・監査更新だけでiterationを閉じず、数値run requestまたは次の単一原因screening contractまで同じ統合内で発行する。

## R0 status ledger

- 公開環境control再現: **1件**
- immutable 131,072-frame R0.1 bundle: **0件**
- 学習済み公開能力baseline再現: **0件**
- J-CRe3 numerical reproduction: **0件**
- J-ORA numerical reproduction: **0件**
- GPI official-software reproduction: **0件**
- Multi-View CRL official-code reproduction: **0件**
- R0.2正式再現: **0件**
- 実R0 bundleのevaluation contract通過: **0件**
- R0.3 hidden intervention-target ablation: **棄却**
- 広義RQ-001: **棄却**
- 狭義RQ-001: **未採用**
- 評価分類: **`initial_reproduction_failure`**

## R0.1 SILG / RTFM

固定条件:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- official `multi` recurrent
- seeds `1,7,19`
- primary budget `131,072 requested frames`

accepted evidenceは32,768 frames runのみ:

- parameters `4,916,915`
- state-dict `19,694,385 bytes`
- maximum RSS `505,600 KiB`
- total three-seed training wall time `1,033.885 s`
- CPU forward `6.911 ms/step`
- Correct `1/60`
- Random `4/60`
- Language-blind / State-only / Language-shuffle `1/60`

これはpolicy competence不足であり、公開能力baseline再現ではない。

## Active execution

- push workflow run: `30203026269` / run number `285`
- workflow head: `5d9f137296a64fc401560356470ac27f520cbeff`
- job: `r01-public-reproduction`
- confirmed completed steps: pinned public-source install、generator-signature test、canonical-seed random control、schema probe
- current confirmed step at locator capture: `Run official multi recurrent 131072-frame training` **in progress**
- artifact count at locator capture: **0**
- run status is execution evidence only。completion、qualification、能力改善とは認定しない。

実行契約:

1. `qualify_r01_source_policy.py`をR0.1とR0.2の間に置く。
2. R0.1終了直後にcheckpoint、matched predictions、resource、raw logs、dependency lock、checksums、qualification結果を成否にかかわらず保存する。
3. qualificationはsource pin、seeds `1/7/19`、actual checkpoint frames、全checkpoint完成、same-instance control、answer-leakage false、Correct/Randomのwin・returnをfail-closed確認する。
4. `Correct <= Random`、Correct success zero、frame未達、seed/method/instance不整合、artifact欠落ならR0.2を開始しない。
5. 不合格時は、失敗分類、固定条件、診断値、変更可能な単一原因、matched再試験、停止条件を `next_run_contract` として保存する。
6. action histogram、valid-action率、entropy、episode length、reward到達率、mask前後logit、invalid-action mass、gradient norm、policy/value lossをseed別に保存する。
7. 原因だけを変える最大6 screening runを行い、有望案だけseeds `1,7,19`へ昇格する。
8. 停止条件を満たさない限り、失敗報告だけでcycleを閉じない。

## Evaluation contract

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。

毎runでrandom/language-blind/state-only/applicable shuffle、model/checkpoint bytes、peak RSS、runtime、CPU latency、seed、split、actual frames、commit、dependency、raw logs、checksums、leakageを保存する。

## Prior-art and RQ boundary

J-CRe3はLREC-COLING 2024の日本語実世界multimodal reference-resolution datasetであり、日本語groundingの外部baselineとして扱うが、SILG/RTFMのinteractive policy competenceを代替しない。

2025 score-based CRLと2026年有限標本CRLにより、unknown target、少数environment、finite-sample recoveryはRQ-001の新規性根拠から除外済みである。

Markham et al., CLeaR 2026、Baumgartner et al., CLeaR 2026、LeGIT、GPI、Yao et al. Multi-View CRLの既存境界を維持する。

Mai & Han, ACL 2026のCmIRは、言語・音響・視覚modalitiesを因果不変表現と環境固有spurious表現へ分離し、invariance、mutual-information、reconstruction制約によってOOD・noise robustnessを改善する。したがって、multimodal invariant/spurious decomposition、環境横断の安定予測、再構成付き因果不変表現だけではRQ-001の新規性を認定しない。author-official codeとexact commitは未固定であり、再現済みbaselineには数えない。

Saklad et al., ACL 2026のReCITEは、実世界textから因果関係を抽出・推論する公開benchmarkと公式code/dataを提供し、既存LLMの性能不足を示す。これはhidden intervention-target recoveryではないが、language-only causal-relation inferenceをRQ-001のlanguage固有能力と混同しないためnovelty matrixの別列へ置く。公式repository `Ryan-Saklad/ReCITE` のexact commit、dataset checksum、evaluation command、model access条件は未固定である。

正式判断:

> **RQ-001: NARROWED BEYOND LANGUAGE-GUIDED TARGET SELECTION, INTERVENTION-CONDITIONED COMPOSITION, GENERATIVE-REPRESENTATION CAUSAL INFERENCE, PARTIALLY OBSERVED MULTI-VIEW CRL, LOCAL-STRUCTURE DYNAMICAL-SYSTEM IDENTIFICATION, MULTIMODAL CAUSAL-INVARIANT DECOMPOSITION, AND LANGUAGE-ONLY CAUSAL-RELATION INFERENCE — NOT ADOPTED**

採用には、上記baseline再現後にも残るcountermodel pair、外部固定でjoint recoding不能なdenotation law、既存のlanguage-only causal extraction・multimodal invariance・trajectory/local-structure recoveryを超えるlanguage固有追加情報の直接証拠、事前登録済みclaim/counterexample/stopping ruleが必要。

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

2026-07-26: **RESET-E053**。R0.1 push run `30203026269`が固定source導入・generator-signature・random/schema probeを通過し、131,072-frame学習工程へ到達した事実を実行中証拠として統合した。artifactは未生成であり、再現成功・能力改善とは認定しない。ACL 2026のCmIRとReCITEをprior-art/benchmark境界へ追加し、multimodal causal-invariant decompositionとlanguage-only causal-relation inferenceだけではRQ-001を採用しない。外部baseline再現0、能力進歩未認定、高校生級未達を維持する。