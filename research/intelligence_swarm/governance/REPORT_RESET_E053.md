# RESET-E053 — R0 Research Reconstruction

Date: 2026-07-26
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope lock

- A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。
- 公開benchmark再現、prior-art audit、evaluation contract、hidden intervention-target ablationだけを累積する。
- 既存stacked draft PRはnegative-results archiveであり、新作業のbaseにしない。
- 外部baseline再現前に、新規機構族、知能原理、能力進歩、高校生級到達を認定しない。
- 「検証したが駄目だった」でcycleを閉じない。停止条件未達なら、根拠付き失敗分類から次の単一原因matched rerunへ接続する。

## 1. Latest primary literature and official-code overlap audit

### CmIR — ACL 2026

Mai & Han, *Learning Invariant Modality Representation for Robust Multimodal Learning from a Causal Inference Perspective* は、各modalityをcausal invariant representationとenvironment-specific spurious representationへ分離し、invariance、mutual-information、reconstruction制約によりOOD/noisy robustnessを改善する。

RQ-001から除外する既存領域:

- multimodal invariant/spurious decomposition
- environment-invariant predictive relation
- reconstructionを伴うcausal invariant representation
- OOD/noise robustnessだけを根拠にしたlanguage固有因果grounding主張

Author-official codeとexact commitは未固定。再現済みbaselineには数えない。

### ReCITE — ACL 2026

Saklad et al., *Can Large Language Models Infer Causal Relationships from Real-World Text?* は、実世界textから因果関係を推論するbenchmark、code、datasetを公開し、既存LLMの性能不足を評価する。公式repositoryは論文上 `Ryan-Saklad/ReCITE` とされる。

RQ-001との境界:

- language-only causal-relation extraction/inferenceはhidden intervention-target recoveryではない。
- text中の因果関係を当てる能力を、環境内target groundingやcausal mechanism identificationへ流用しない。
- novelty matrixでは別列に置き、exact commit、dataset checksum、official evaluationを再現する。

## 2. SILG / J-CRe3 reproduction progress

### SILG / RTFM

Locator artifact `r0-silg-push-run-locator-30204086037` を確認した。

- active push run: `30203026269`
- run number: `285`
- workflow head: `5d9f137296a64fc401560356470ac27f520cbeff`
- job: `r01-public-reproduction`
- completed: pinned source install、generator-signature extraction test、canonical-seed random control、schema probe
- locator capture時点: official `multi` recurrent 131,072-frame trainingがin progress
- artifact count: 0

これは開始・途中到達の証拠であり、再現成功、qualification、能力改善ではない。

### J-CRe3

- official numerical reproduction: 0
- exact commit / dataset checksum / official command固定: 未完了
- random / text-only / vision-only / mention-shuffle / frame-object shuffle: 未実行

## 3. Required controls

R0.1ではsame-instanceで以下を保存する。

- Correct
- Random
- Language-blind
- State-only
- Language-shuffle

ReCITEでは以下を事前登録する。

- random label
- entity/order shuffle
- causal-marker masking
- sentence shuffle
- retrieval-only baseline

## 4. Resource and provenance contract

毎runで以下を保存する。

- model/checkpoint bytes
- peak RSS
- training/evaluation runtime
- CPU latency where applicable
- seed `1/7/19`
- split and actual frames
- source/code commit
- dependency lock
- raw logs and predictions
- artifact ID and SHA-256 manifest

## 5. Leakage

- D015〜D035を凍結する。
- 実bundleが具体的false pass/failureを示すまで新規auditorを追加しない。
- answer、gold action、after-state、reward、terminal、return、completed trajectory、post-treatment情報を拒否する。
- same-instance controlとshuffle donor provenanceを必須とする。

## 6. RQ-001 decision

> **NARROWED BEYOND LANGUAGE-GUIDED TARGET SELECTION, INTERVENTION-CONDITIONED COMPOSITION, GENERATIVE-REPRESENTATION CAUSAL INFERENCE, PARTIALLY OBSERVED MULTI-VIEW CRL, LOCAL-STRUCTURE DYNAMICAL-SYSTEM IDENTIFICATION, MULTIMODAL CAUSAL-INVARIANT DECOMPOSITION, AND LANGUAGE-ONLY CAUSAL-RELATION INFERENCE — NOT ADOPTED**

採用には、全適用可能baseline再現後にも残るcountermodel pair、外部固定でjoint recoding不能なdenotation law、language固有追加情報の直接評価、事前登録済みclaim/counterexample/stopping ruleが必要。

## Failure continuation contract

Run `30203026269`終了後:

1. job conclusionとartifact IDを取得する。
2. artifactが0件ならupload境界、`always()`、path、concurrency/cancellationを最初の単一原因候補にする。
3. artifactがあればqualification JSONとdiagnosticsを読む。
4. 最初のactionable failureを1件だけ選ぶ。
5. frames、split、instances、model familyを固定し、原因だけを変えたmatched rerunを発行する。
6. 最大6 screening runまたは事前停止条件まで継続する。
7. 失敗報告だけでiterationを閉じない。

## Formal status

- immutable R0.1 competence bundle: 0
- learned external baseline reproduction: 0
- J-CRe3 numerical reproduction: 0
- qualified R0.2: 0
- R0.3: rejected
- novelty matrix: incomplete
- central claim preregistration: incomplete
- broad RQ-001: rejected
- narrowed RQ-001: not adopted
- new mechanism family: not recognized
- new intelligence principle: none
- capability progress: not recognized
- high-school-level intelligence: not achieved
- next-stage proposal: none
