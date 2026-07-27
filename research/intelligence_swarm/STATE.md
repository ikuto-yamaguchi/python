# Intelligence Swarm State

## Mission

長期目標は、1GB未満で弱いスマートフォンCPU上でも高速に動作し、日本語コミュニケーション・知識・推論を備える知能モデルである。R0では新規toy仮説や新機構族を作らず、公開baselineを固定資源制約下で再現し、失敗原因を一つずつ除去して性能を最大化する。

## Current stage

- Stage: **R0 Research Reconstruction — constrained performance maximization**
- Canonical branch: `research/intelligence-swarm-reconstruction-001`
- A〜Dの新規toy仮説・別branch・新規機構族: **禁止**
- 既存stacked draft PR: **negative-results archive。新作業のbaseにしない**
- 外部baseline再現前の新規知能原理・能力進歩認定: **禁止**

## A–D responsibilities

- **A**: SILG/RTFM、J-CRe3等の公式再現とimmutable artifact保存。
- **B**: 実装・最適化・表現・探索/信号の失敗診断と、原因だけを変える最小run。
- **C**: 最新一次文献・公式codeとの重複監査とnovelty matrix。
- **D**: D015〜D035、matched controls、resource、leakage、RQ-001判定。

## Non-termination rule

「検証したが駄目だった」で終了しない。失敗runは、失敗分類、metric/log/code差分に基づく原因、最小修正、同一budget・instance再run、採用・棄却・停止判定まで未完了とする。高コスト学習済みartifactが有効なら、監査・qualification障害のために再学習しない。

## R0 status ledger

- immutable R0.1 artifacts: **5件**
- 学習済み公開能力baseline再現: **0件**
- J-CRe3 numerical reproduction: **0件**
- R0.2正式再現: **0件**
- R0.3 hidden intervention-target ablation: **棄却維持**
- 広義RQ-001: **棄却**
- 狭義RQ-001: **未採用**
- 評価分類: **`initial_reproduction_failure`**

## Closed entropy and protocol causes

Valid entropy source run `30215555334`とartifact-only requalification run `30219453396`により、`entropy_cost=0.005`単独原因とevaluation protocol mismatch主因は棄却済みである。

## Completed official-stateful screening

Primary run:

- run `30221587227`
- job `89844840438`
- artifact `8638198496`
- digest `sha256:ae28542e4bda4ca968de9d7ffc42b5ab4b4dadb518a26636a41d63b92131aa31`
- artifact size `91,615,915 bytes`
- execution commit `4b1dff1cd6cd3f6a2dc360d5689cb9968c6a4998`

Factor-routingと再現証拠:

- 全seed commandに`--stateful`: **passed**
- 全checkpointに`core.*` LSTM weights: **passed**
- 全seedのrecurrent-state norm > 0: **passed**
- same-instance controls: **passed**
- official/fresh evaluation parity: **passed**
- immutable artifact upload: **passed**
- qualification: **rejected**

Matched aggregate:

- Correct `2/60 = 0.0333`
- Random `4/60 = 0.0667`
- Language-blind `2/60 = 0.0333`
- State-only `1/60 = 0.0167`
- Language-shuffle `2/60 = 0.0333`
- Correct mean return `-1.8273327`
- Random mean return `-1.1513333`
- Correct−Random return `-0.6759995`

Resource/provenance:

- parameters `6,200,115`
- untrained state-dict bytes `24,828,505`
- trained model-state bytes `24,827,943` per seed
- actual frames `131,080` per seed
- seed 1: wall `1691.39 s`, peak RSS `1,069,864 KiB`
- seed 7: wall `1569.14 s`, peak RSS `1,334,592 KiB`
- seed 19: wall `1686.73 s`, peak RSS `1,274,272 KiB`
- CPU forward audit `8.162 ms/step`
- chosen-action valid fraction `1.0` for all seeds
- answer leakage: **false**

Decision:

> **official stateful core不足を単独主因として棄却する。statefulは正しく作動したが、CorrectはRandomを下回り、language-blind/shuffleと同率で、言語利用能力も成立していない。**

後続run `30221650935`はjob未生成であり、primary artifactが完全に保存されたためfallback evidenceとしても不要である。独立な性能証拠には数えない。

## Active single-factor screening: unroll length 20 → 80

次の単一変更要因は公式defaultとの主要差である`unroll_length: 20 → 80`。stateful=true、entropy `0.05`、actors `2`、threads `1`、batch `2`、frames `131072`、seeds `1/7/19`、split、matched instances、controlsを固定する。

追加済み:

- `patch_silg_unroll80_screening.py`
- `.github/workflows/r01_silg_unroll80_screening.yml`

全seedで`--stateful`、`--unroll_length 80`、LSTM checkpoint、non-zero recurrent stateをfail-closed確認し、random/language-blind/state-only/language-shuffle、model/RSS/runtime/CPU latency/seed/split/frames/checksums/leakage、official/fresh parity、qualificationを保存する。

有効なunroll=80 runでもCorrectがRandomを上回らない場合、unroll不足単独原因を棄却する。ただしiterationは閉じず、次の単一原因をlearner optimization parity（learning rate、gradient clipping、optimizer/checkpoint restoreのうち証拠が最も強い一件）から選ぶ。

## Evaluation contract

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。毎runでrandom/language-blind/state-only/shuffle、model/checkpoint bytes、RSS、runtime、CPU latency、seed、split、actual frames、raw logs、checksums、leakageを保存する。

## Prior-art and RQ boundary

既存のscore-based CRL、finite-sample CRL、Multi-View CRL、LeGIT、GPI、ReCITE、C3、MCDRL、CmIR、CAIR、PCMCI、CausalLens等の境界を維持する。

AAAI 2026のCTLDは、hidden confounding下のlearning-to-deferでpotential-outcome boundsからaction/deferralのcausal targetを構成する。したがって、hidden confounding下でcausal decision targetを定義し、人間へのdefer確率を学習することだけではRQ-001の新規性を認定しない。一方、これはlatent intervention-target groundingやSILG/J-CRe3能力の再現baselineではない。一次論文は確認済みだが、author-official codeとexact commitは未解決である。

正式判断:

> **RQ-001: FURTHER NARROWED BEYOND CAUSAL TARGET CONSTRUCTION FOR LEARNING-TO-DEFER UNDER HIDDEN CONFOUNDING — NOT ADOPTED**

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

2026-07-26: **RESET-E064**。official-stateful primary runをartifactまで監査し、stateful factor-routingは成功したがCorrect `2/60`対Random `4/60`でqualification rejectedとなったため、stateful不足単独原因を棄却した。次の単一要因`unroll_length 20→80`のfail-closed workflowを追加した。CTLDをprior-art境界へ追加したが、外部baseline再現0、能力進歩未認定、高校生級未達を維持する。
