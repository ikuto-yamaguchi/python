# Intelligence Swarm State

## Mission

1GB未満・弱いスマートフォンCPUで実行可能な知能モデルを目標とし、生の日本語と環境相互作用から対象・状態・操作・因果構造を獲得する原理を研究する。

## Current stage

- Stage: **R0 Research Reconstruction — prior art, baseline reproduction, benchmark contract**
- Semantic Identity Gate G1: **未達**
- Operation/Goal Gate G2: **未達**
- Formal memory eligibility: **未達**
- 学術的新規性: **未確立**
- 再現済み外部baseline: **0**
- 公開環境control実測: **1件（SILG/RTFM S1 random-valid-action）**
- 査読可能な中心命題: **未確立**
- Active mechanism family: **なし**
- AF-001〜AF-014: **PAUSED**
- A〜Dの新規toy仮説生成: **停止**
- Memory/consolidation最適化: **停止継続**

## Why the program was reset

過去サイクルは、合成opaque token環境上で候補機構を変更し、Correctとshuffle/randomの差が出ないことを反復確認した。評価漏れや不可能条件の発見はあったが、先行研究に対する新規性監査、公開benchmark上の既存baseline再現、同一benchmark・同一splitでの累積改善、数学的に反証可能な単一中心命題、一つのcanonical実装が欠けていた。したがって、これまでの成果を新しい知能原理または基礎研究上の発見とは扱わない。

## R0 reproduction gate

新しい仮説族を開始する前に、次を順番に完了する。

1. **SILG reproduction** — MessengerまたはRTFMの公式環境を固定し、pretrained LMなしの共有recurrent baselineを再現する。
2. **Environment-first baseline** — 言語なしstate transitionから環境表現を先に学ぶbaselineと、language/actionを同時学習するbaselineを同じsplitで比較する。
3. **Intervention-target ablation** — 介入対象が既知、部分既知、未知の3条件を同じ軌跡上で比較し、表現同定とinstruction following能力を分離する。
4. **Japanese realism audit** — J-CRe3を実世界日本語参照接地の外部監査として使用する。主性能値とは混同しない。
5. **Resource gate** — 推論モデル1GB未満、CPU推論時間、RSS、学習時間を実測する。

R0では再現値が原論文または公開実装の許容範囲へ入るまで、新規原理の成功・失敗を主張しない。

## Candidate research question — narrowed again, not adopted

**RQ-001-N3:** On a fixed public interactive benchmark, does raw language provide predictive information about held-out mechanism changes beyond state, action, history, reward and environment identity; and, conditional on that gain, can an utterance-conditioned intervention partition be recovered up to joint permutation or the finest intervention-supported causal abstraction, without target labels, semantic parsers, object slots, pretrained language models or supplied perturbation semantics?

The broad `language features -> intervention distribution` formulation is not novel after Generative Intervention Models. Exact latent-variable names and exact utterance-target names are not identifiable under a joint latent/language permutation without an observable anchor. Evaluation must therefore be permutation- or abstraction-aware.

## Causal identifiability audit C003

- Split the candidate claim into two gates.
- **Gate L:** language-specific predictive information beyond state, action, history, reward and environment identity on matched held-out episodes.
- **Gate I:** conditional on Gate L, joint utterance/intervention partition recovery up to shared permutation or the finest intervention-supported abstraction.
- Gate L does not imply Gate I; language may be only an environment, policy, reward-density or episode-phase proxy.
- Environment-indexed CRL guarantees do not directly establish recovery when the environment/intervention partition must itself be inferred from raw trajectories and language.
- Unknown-target recovery, unknown soft-intervention inference and supervised perturbation-target prediction are prior art; they are not standalone contributions.
- No new architecture is authorized until Gate L is operationalized on a reproduced public baseline and Gate I is shown to be well-defined for the selected benchmark.

## Pinned reproduction facts

- SILG: `silg==0.0.1`、Python `>=3.7.10`、MIT。
- Target SILG commit: `2af07578e1264029a240fcfb78d4ac0aea16f5de`。
- RTFM commit: `58f17955595b5a127c96d045d896fcbcc7d4b570`。
- Reproduced runner: Ubuntu 22.04、Python 3.8.18、4 vCPU AMD EPYC 7763、15 GiB RAM。
- Resolved core pins: `torch==1.13.1+cpu`, `torchvision==0.14.1+cpu`, `gym==0.21.0`, `numpy==1.24.4`, `transformers==4.30.2`。
- Official experiment entrypoint: `run_exp.py`; local launch: `OMP_NUM_THREADS=1 python launch.py --local --envs rtfm`。
- RTFM registers `rtfm_train_s1..s4-v0` and `rtfm_test_s1..s4-v0`。
- Observed S1 keys: `name/name_len`, `wiki/wiki_len`, `task/task_len`, `inv/inv_len`, `valid`, `rel_pos`, `pos`。
- Observed shapes: grid-name `[6,6,1,8]`, wiki `[80]`, task `[40]`, inventory `[8]`, valid action mask `[5]`, relative positions `[6,6,2]`, player position `[2]`。
- Action space: 5 actions; maximum episode length: 80。
- J-CRe3は日本語realism auditであり、R0.1の因果・行為baselineの代替ではない。

## R0.1 public-environment control result

GitHub Actions run `30101406916` successfully installed the pinned SILG and RTFM repositories and executed a public RTFM S1 random-valid-action probe.

- Artifact: `r0-silg-rtfm-probe-30101406916`
- Artifact digest: `sha256:ed463e76d5c528b2cf25d740847c77978dbe66d0ed5455a57289519ba0455afd`
- Environment: `silg:rtfm_train_s1-v0`
- Seeds: `0,1,2`
- Episodes: 20 per seed, 60 total
- Wins: 8 / 60
- Mean seed win rate: `0.1333` (seed range `0.05–0.25`)
- Aggregate win rate: `0.1333`
- Mean return: `-1.0237`
- Mean episode length: `15.5167`
- Total environment wall time: `2.7652 s`
- Random action-selection latency: `7.324 µs/action`
- Raw logs, pip freeze and SHA-256 manifest: captured in the workflow artifact

This is a **public environment/control reproduction**, not the official shared recurrent baseline. It resolves the previous DNS/source-acquisition blocker but does not complete R0.1.

The workflow used seeds `0,1,2`, while the canonical research seeds are `1,7,19`; therefore the run is accepted as an installation/schema/control proof only. The next controlled run must use `1,7,19` and identical episode instances across all methods.

## R0.2 cycle 001 result

Gaddy & Klein 2019のconditional-autoencoder方式に忠実な再現harnessをcanonical branchへ追加した。

- language-free transition pretraining: `E(s,s') -> z`, `D(s,z) -> s'`
- pretrained decoderへlanguage encoder `L(c) -> z`を接続
- matched end-to-end baseline
- language-blind / language-shuffle controls
- SILG Gym trajectory JSONL exporter
- model bytes、peak RSS、training time、CPU inference time、held-out entity/dynamics/language-form fields

Synthetic fixtureでseed 1/7/19のpipeline smoke testを完了したが、これは公開SILG再現でも能力証拠でもない。environment-first action accuracy 0.5028、end-to-end 0.4097だった一方、task successは0.0042対0.2069でenvironment-firstが劣った。fixture結果は研究判断に使用しない。

## Current bottleneck

**SILG/RTFM公式shared recurrent baselineと、同一episode上のlanguage-blind/state-only/shuffle対照が未実行。**

Source acquisition and environment installation now succeed in GitHub Actions. The next bottleneck is no longer DNS; it is faithful training/evaluation orchestration, deterministic instance replay, complete artifact accounting, and operationalizing Gate L. Gate I must not be implemented until the benchmark's intervention diversity is shown to define a nontrivial evaluation-only partition.

## Progress rule

R0の進歩は、公開baselineの再現成功、同一benchmark・同一split・同一seedでの外部能力改善、既存理論との差分が明確な定理・反例・識別可能性条件、再現可能なデータ・コード・測定ログのみ。候補数、graph、tensor、圧縮、low-rank、version-space縮約、toy環境内の一意化は進歩へ数えない。

## Canonical branch policy

今後の研究は一本のcanonical reconstruction branchから進める。過去のstacked draft PRはnegative-results archiveとして保持し、新しい実験のbaseには使用しない。

## Current status

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: false

## Last integration

2026-07-25: **C-AUDIT-003**。一次文献監査からRQをGate L（言語固有の予測情報）とGate I（介入partitionの共同同定）へ分離し、RQ-001-N3へ狭義化。予測改善だけをsemantic identifiabilityとみなす経路を禁止。公開recurrent baselineとmatched controlsが未完了のため、新規性・知能原理・能力進歩の認定なし。
