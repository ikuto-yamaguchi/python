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

**RQ-001-N2:** On a fixed public interactive benchmark, does raw language contain statistically necessary information about an intervention partition or causal abstraction beyond state, action, history and environment identity, and can that information be recovered up to joint permutation without intervention-target labels, semantic parsers, object slots, pretrained language models or supplied perturbation-feature semantics?

The broad `language features -> intervention distribution` formulation is not novel after Generative Intervention Models. Exact latent-variable names and exact utterance-target names are not identifiable under a joint latent/language permutation without an observable anchor. Evaluation must therefore be permutation- or abstraction-aware.

## Causal identifiability audit C002

- Added closest-overlap audit for Generative Intervention Models, Isolated Causal Effects of Natural Language and real-system CRL sanity checking.
- Added an exact finite counterexample with three latent variables and six joint permutations.
- All six joint relabelings induce one identical observable table.
- Exact latent and utterance-target names are therefore not identifiable; recovery is only valid up to joint permutation or a coarser causal abstraction.
- Required language evidence is now `full - state/action/history-only` on held-out mechanisms, with utterance, transition and target-label shuffles plus rename/paraphrase controls.
- This is an identifiability restriction, not a new intelligence mechanism or capability result.

## Pinned reproduction facts

- SILG: PyPI `silg==0.0.1`、2021-10-20公開、Python `>=3.7.10`、MIT。
- Public SILG code URLs expose commit `2af07578e1264029a240fcfb78d4ac0aea16f5de`。
- Official requirements are only partly pinned: `gym>=0.15.4`, `torch`, `torchvision`, `pyyaml`, `expman`, `submitit`; exact pin is `py-getch==1.0.1`。
- SILGは個別環境の導入、依存install、environment data取得が必要。初回対象はRTFMに限定する。
- Official experiment entrypoint: `run_exp.py` / `launch.py`; learner sets `OMP_NUM_THREADS=1` and uses V-trace actor-learner training。
- J-CRe3は日本語realism auditであり、R0.1の因果・行為baselineの代替ではない。

## R0.2 cycle 001 result

Gaddy & Klein 2019のconditional-autoencoder方式に忠実な再現harnessをcanonical branchへ追加した。

- language-free transition pretraining: `E(s,s') -> z`, `D(s,z) -> s'`
- pretrained decoderへlanguage encoder `L(c) -> z`を接続
- matched end-to-end baseline
- language-blind / language-shuffle controls
- SILG Gym trajectory JSONL exporter
- model bytes、peak RSS、training time、CPU inference time、held-out entity/dynamics/language-form fields

Synthetic fixtureでseed 1/7/19のpipeline smoke testを完了したが、これは公開SILG再現でも能力証拠でもない。environment-first action accuracy 0.5028、end-to-end 0.4097だった一方、task successは0.0042対0.2069でenvironment-firstが劣った。fixture結果は研究判断に使用しない。

## Current blocker

**公開baselineの実行値がまだ1件もない。**

実行sandboxは外部DNSを解決できず、GitHub cloneとACL software archive downloadが失敗した。SILG/RTFM環境、environment data、互換Python 3.7/3.8 runtimeが存在しない。分類は `initial_public_environment_installation_failure`。

次の有効作業は、公式DockerまたはUbuntu x86_64でSILG commitとRTFM環境を固定し、公式shared recurrent baselineを実行した後、同一trajectory・seed 1/7/19でenvironment-first、end-to-end、random、language-blind、state-only、history-only、language-shuffle、transition-shuffleを測定すること。

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

2026-07-24: **C-AUDIT-002**。GIM等の重複監査、joint latent/language permutation no-go、permutation-aware評価条件を追加。RQ-001をRQ-001-N2へさらに狭義化。公開baseline再現は0件のためR0継続、新規性・能力進歩の主張なし。
