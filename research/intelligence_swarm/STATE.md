# Intelligence Swarm State

## Mission

長期目標は、1GB未満で弱いスマートフォンCPU上でも高速に動作し、日本語コミュニケーション・知識・推論を備える知能モデルである。R0では新規toy仮説や新機構族を作らず、公開baselineを固定資源制約下で再現し、失敗原因を一つずつ除去して性能を最大化する。

## Current stage

- Stage: **R0 Research Reconstruction — official-contract infrastructure qualification**
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

「検証したが駄目だった」で終了しない。ただし、短期screeningを公式baseline再現と誤認して追加hyperparameter探索を続けることも禁止する。高コスト学習済みartifactが有効なら、監査・qualification障害だけのために再学習しない。

## R0 status ledger

- immutable R0.1 screening artifacts: **8件**
- official SILG RTFM 100M-frame reproduction: **0件**
- official-contract infrastructure qualification: **workflow発行済み・結果未認定**
- 学習済み公開能力baseline再現: **0件**
- J-CRe3 numerical reproduction: **0件**
- R0.2正式再現: **0件**
- R0.3 hidden intervention-target ablation: **棄却維持**
- novelty matrix: **未完了**
- 中心命題の事前登録: **未完了**
- 広義RQ-001: **棄却**
- 狭義RQ-001: **未採用**
- 主分類: **`public_reproduction_contract_mismatch`**

## Official SILG reproduction contract

Pinned official SILG `launch.py --envs rtfm`は、`model=multi`、`stateful=false`、entropy grid `0.05/0.005`、train `silg:rtfm_train_s1-v0`、validation `silg:rtfm_test_s1-v0`を指定する。parser defaultsはtotal frames `100,000,000`、actors `30`、batch `24`、unroll `80`、threads `4`、learning rate `0.0005`、RMSprop、global gradient clip `40`である。

既存の`131,072`-frame runsは公式frame horizonの`0.131072%`、推定learner update数でも公式契約の約`1/63.58`にすぎない。したがって、すべて**短期screening evidence**としてのみ保持し、公式public baseline reproductionや公式baseline failureとは呼ばない。

Immutable audit:

- `benchmarks/grounded_causal/R01_OFFICIAL_TRAINING_HORIZON_AUDIT.json`
- audit commit `4ccb3963a35d76cc8b28234f1280e7164e94df5e`

## Closed short-horizon screening causes

以下は各縮小契約内の単独原因としてのみ棄却した。公式100M-frame baselineの原因判定へ外挿しない。

- `entropy_cost=0.005`
- evaluation protocol mismatch
- `stateful=true`追加
- `unroll_length=20→80`
- `learning_rate=0.0001`
- gradient clip norm `40→10`

## Latest short-horizon negative evidence

Gradient-clipping screening run `30240410850`, artifact `8644560521`:

- Correct `3/60`
- Random `4/60`
- Language-blind `0/60`
- State-only `0/60`
- Language-shuffle `3/60`
- Correct mean return `-1.7679994`
- Random mean return `-1.1513333`
- parameters `6,200,115`
- actual frames `131,200` per seed
- peak RSS `1,299,228 / 1,180,104 / 1,856,556 KiB`
- wall `1528.08 / 1559.30 / 1591.64 s`
- CPU forward `8.565 ms/step`
- answer leakage `false`
- qualification **rejected**

この結果は縮小契約で言語依存能力が成立しなかったnegative evidenceであり、公式baseline失敗の証拠ではない。

## Active execution: official-contract infrastructure qualification

以下をcanonical branchへ追加した。

- `patch_silg_official_infrastructure_qualification.py`
- `audit_silg_infrastructure_qualification.py`
- `.github/workflows/r01_silg_official_infrastructure_qualification.yml`

workflowはseed `1`、短区間`32,768` framesで、official `model=multi`、`stateful=false`、actors `30`、batch `24`、unroll `80`、threads `4`、learning rate default `0.0005`、RMSprop、clip `40`を保持する。これは能力screeningではなくrunner/checkpoint/resource qualificationである。

Fail-closed証拠:

- official command parity
- exact official `job.tar`保存
- model stateとexported stateのtensor完全一致
- optimizer stateとparameter groups
- frame counter
- checkpoint/model bytesとSHA-256
- peak RSS、runtime、throughput、100M-frame projected wall
- scheduler/RNG/learner-batch state
- one-step resume-equivalence prerequisites

RNGまたはlearner batchがcheckpointに存在しない場合、one-step resume equivalenceを推測で通さず明示的にrejectする。不足したresume instrumentationだけを次の単一修正候補とし、モデル機構や能力進歩は認定しない。

random controlは保存する。language-blind/state-only/language-shuffleはinfrastructure-only segmentでは能力評価を行わないためnot-applicableとして明示し、100M-frame正式能力再現では再び必須とする。

## Evaluation contract

D015〜D035を凍結する。能力runではrandom/language-blind/state-only/shuffle、model/checkpoint bytes、RSS、runtime、CPU latency、seed、split、actual frames、raw logs、checksums、leakageを保存する。公式再現ではさらにofficial command parity、100M frame horizon、checkpoint/resume integrityを必須とする。infrastructure-only runを能力証拠に数えない。

## Prior-art and RQ boundary

既存のscore-based CRL、finite-sample CRL、Multi-View CRL、LeGIT、GPI、ReCITE、C3、MCDRL、CmIR、CAIR、PCMCI、CausalLens、CTLD、DCAN、TRACE、Bayesian Ablation、CausalDisenSeg、MagicBench、CodeBind、NoisyCausal、CaST-Bench、CausalVerse等の境界を維持する。

MTG-Causal-RLは、部分観測・巨大masked action space・明示SCMを持つ複雑なカードゲーム環境で、intervention effect、factor-wise credit trace、paired seeds、補正済み統計比較を含むcausal-RL benchmarkを提示する。したがって、masked sequential decision making、明示SCMによるcausal credit assignment、intervention calibrationだけではRQ-001の新規性にならない。author-official code、exact commit、immutable reproductionは未解決であり、SILG/J-CRe3の能力証拠を代替しない。

正式判断:

> **RQ-001: FURTHER NARROWED BEYOND EXPLICIT-SCM CAUSAL CREDIT ASSIGNMENT IN MASKED PARTIALLY OBSERVED RL — NOT ADOPTED**

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

2026-07-27: **RESET-E075**。短期screeningの追加hyperparameter探索を行わず、公式sampling defaultsを保持した32,768-frame infrastructure qualification workflowを実装・発行した。checkpoint/model/optimizer/frame/resourceとresume prerequisitesをfail-closed保存し、能力証拠とは分離する。MTG-Causal-RLをnovelty境界へ追加したが、外部baseline再現0、能力進歩未認定、高校生級未達を維持する。
