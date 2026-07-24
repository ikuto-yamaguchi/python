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

過去サイクルは、合成opaque token環境上で候補機構を変更し、Correctとshuffle/randomの差が出ないことを反復確認した。評価漏れや不可能条件の発見はあったが、以下が欠けていた。

1. 先行研究に対する新規性監査
2. 公開benchmark上の既存baseline再現
3. 同一benchmark・同一splitでの累積改善
4. 数学的に反証可能な単一中心命題
5. 一つのcanonical実装への統合

したがって、これまでの成果を新しい知能原理または基礎研究上の発見とは扱わない。

## R0 reproduction gate

新しい仮説族を開始する前に、次を順番に完了する。

1. **SILG reproduction**  
   MessengerまたはRTFMの公式環境を固定し、pretrained LMなしの共有recurrent baselineを再現する。
2. **Environment-first baseline**  
   言語なしstate transitionから環境表現を先に学ぶbaselineと、language/actionを同時学習するbaselineを同じsplitで比較する。
3. **Intervention-target ablation**  
   介入対象が既知、部分既知、未知の3条件を同じ軌跡上で比較し、表現同定とinstruction following能力を分離する。
4. **Japanese realism audit**  
   J-CRe3を実世界日本語参照接地の外部監査として使用する。J-CRe3は行為因果benchmarkではないため、主性能値と混同しない。
5. **Resource gate**  
   推論モデル1GB未満、CPU推論時間、RSS、学習時間を実測する。

R0では再現値が原論文または公開実装の許容範囲へ入るまで、新規原理の成功・失敗を主張しない。

## Candidate research question — narrowed, not adopted

**RQ-001-N:** On a fixed public interactive benchmark, can raw-language equivalence provide statistically necessary information for recovering a latent intervention partition or abstraction beyond state/action-only models, when environment identity is available for split construction but intervention-target labels, semantic parsers, object slots and pretrained language models are absent?

## Latest prior-art consequence

2025〜2026の一次文献監査により、次は既に独立に研究されていることを確認した。

- unknown intervention target下の非パラメトリック識別可能性
- arbitrary-subset interventionからのcausal abstraction識別
- 少数環境・有限標本でのunknown multi-node target回復
- multi-domain interactive language grounding
- language-conditioned dynamics pretraining
- 実世界日本語のcrossmodal reference grounding

したがって、`unknown intervention target`、`language-conditioned dynamics`、`multi-environment grounding`のいずれか単独では新規性にならない。正確な低レベル変数identityではなく、共有置換またはcausal abstractionまでしか識別できない可能性も正式に許容する。

## Pinned reproduction facts

- SILG: PyPI `silg==0.0.1`、2021-10-20公開、Python `>=3.7.10`、MIT。
- SILGは個別環境の導入、依存install、environment data取得が必要。初回対象はRTFMまたはMessengerに限定する。
- SILG official experiment entrypoint: `run_exp.py` / `launch.py`。
- J-CRe3: official public repository `riken-grp/J-CRe3`、公開メタデータ上のavailable dateは2026-04-06。
- J-CRe3は日本語realism auditであり、R0.1の因果・行為baselineの代替ではない。

## Current blocker

**公開baselineの実行値がまだ1件もない。**

次の統合作業は、新しい理論名やモデルを作ることではなく、SILG RTFMまたはMessengerの環境pinning、公式shared recurrent baselineの実行、random/language-blind/state-only対照の同一seed測定である。

## Progress rule

R0の進歩は以下のみ。

- 公開baselineの再現成功
- 同一benchmark・同一split・同一seedでの外部能力改善
- 既存理論との差分が明確な定理、反例、または識別可能性条件
- 再現可能なデータ・コード・測定ログ

候補数、graph、tensor、圧縮、低rank、version-space縮約、toy環境内の一意化は進歩へ数えない。

## Canonical branch policy

今後の研究は一本のcanonical reconstruction branchから進める。過去のstacked draft PRはnegative-results archiveとして保持し、新しい実験のbaseには使用しない。

## Current status

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: false

## Last integration

2026-07-24: **RESET-E008**。2025〜2026のCRL一次文献と公式benchmark公開情報を追加監査し、RQ-001をRQ-001-Nへ狭義化した。新規性は未確立、baseline再現0件のためR0継続。
