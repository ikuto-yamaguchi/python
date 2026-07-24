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
- AF-014 transformation-indexed equivariance: **PAUSED**
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

## Candidate research question — not a novelty claim

**RQ-001: Can latent intervention targets and raw-language equivalence classes be jointly identified from interactive trajectories when neither a semantic parser nor intervention-axis labels are supplied?**

既存研究には以下が別々に存在する。

- interventional causal representation learning
- unknown multi-node intervention identifiability
- environment-first instruction grounding
- incremental action-observation grounding
- multi-domain interactive language grounding
- Japanese real-world reference grounding

現時点では、これらの交差領域が未解決である可能性があるだけであり、新規性は主張しない。体系的文献監査とbaseline reproduction後に、既存研究が同じ問題を既に解いていない場合のみ正式仮説へ昇格する。

## Progress rule

R0の進歩は以下のみ。

- 公開baselineの再現成功
- 同一benchmark・同一split・同一seedでの外部能力改善
- 既存理論との差分が明確な定理、反例、または識別可能性条件
- 再現可能なデータ・コード・測定ログ

候補数、graph、tensor、圧縮、低rank、version-space縮約、toy環境内の一意化は進歩へ数えない。

## Canonical branch policy

今後の研究は一本のcanonical reconstruction branchから進める。過去のstacked draft PRは反証archiveとして保持し、新しい実験のbaseには使用しない。

## Current status

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: false

## Last integration

2026-07-24: **RESET-001**。旧A〜E toy hypothesis loopを停止し、研究段階をR0 prior-art / reproduction / benchmark constructionへ戻した。
