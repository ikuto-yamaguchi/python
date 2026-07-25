# Intelligence Swarm Backlog

## Operating rule

R0の目的は、監査項目を増やすことではなく、**固定された資源制約下で公開baseline性能を最大化し、その改善原因を反証可能に特定すること**である。

- canonical branchは`research/intelligence-swarm-reconstruction-001`のみ。
- A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。
- 既存stacked draft PRはnegative-results archiveとして扱い、新作業のbaseにしない。
- 新規監査は、実bundleで具体的なfalse pass／false failureが発生した場合だけ追加する。
- 外部baseline再現までは、新しい知能原理・能力進歩・高校生級到達を認定しない。

## P0 — R0.1 SILG/RTFM baseline competence recovery

### 固定条件

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- train `silg:rtfm_train_s1-v0`
- test `silg:rtfm_test_s1-v0`
- official `multi` recurrent
- pretrained language modelなし
- seeds `1,7,19`
- primary budget `131,072 requested frames`
- identical initial instances and evaluation budget

現accepted evidenceは32,768 requested framesのみで、Correct `1/60`、Random `4/60`。これはbaseline competence未達であり、性能改善研究の出発点とする。

### 失敗診断順序

性能不振を次の4分類で切り分ける。分類前に改善案を乱発しない。

1. **実装・再現不一致**: config、optimizer、unroll、mask、termination、frame counting、checkpoint restore。
2. **最適化不足**: loss停滞、gradient異常、action entropy崩壊、value/policy imbalance。
3. **表現ボトルネック**: state/wiki/task/inventory/relative-positionの融合不足。
4. **探索・学習信号不足**: action collapse、reward sparsity、episode curriculum不整合。

### 実験規律

各実験は実行前に、期待原因、反証条件、追加計算量を記録する。

- seed `1`でscreening。
- 有望案のみseeds `1,7,19`へ昇格。
- favorable seed、instance選別、追加frameによる見かけ改善は禁止。
- 1サイクルの上限は6 screening run + 3-seed confirmation 2案。
- 改善が出ない場合も、どの原因分類を棄却したかを成果として残す。

### E1 — Official-fidelity reconstruction

- 公式README、config、CLI default、dependency、frame countingを差分監査する。
- 公式checkpointまたは報告値があれば同一評価条件で照合する。
- 成功: public baseline許容範囲へ到達、または数値差の最小原因を1件特定。
- 停止: 同一設定3回で差が再現し、原因候補が実装外に限定される。

### E2 — Action-collapse diagnosis

保存項目:

- action histogram
- valid-action率
- policy entropy
- episode length
- reward到達率
- invalid-action mask前後logit
- recurrent-state reset/detach挙動

目的はCorrectがRandomを下回る理由を、mask不具合、policy collapse、探索不足へ分類すること。

### E3 — Optimization budget allocation

新規architectureは作らず、official family内の学習条件だけを比較する。

候補:

- learning rate 3水準
- entropy coefficient 3水準
- rollout/unroll length 2水準
- gradient clipping on/off
- recurrent-state detach/reset条件

全探索はしない。E2の診断結果から最大6 runを選ぶ。

採用条件:

- 同一parameter数・同一frame budgetで3-seed平均改善。
- 最低seedでも悪化しない。
- model bytes、RSS、runtime増加だけでは説明できない。

### E4 — Capacity allocation within the official family

総parameter数を±2%以内に固定し、既存component間の容量配分だけを比較する。

- recurrent hidden size
- state encoder width
- language/wiki encoder width
- fusion projection width

目的は約4.9M parameterをどこへ配るとtask successが最大になるか特定すること。モデル大型化は成果に数えない。

### E5 — Fusion timing ablation

既存入力とofficial familyを維持し、融合位置だけを比較する。

- early fusion
- recurrent-input fusion
- late policy-head fusion
- language-blind
- state-only
- language-shuffle

採用条件は、Correctが同一instance上でlanguage-blind/state-only/shuffleを安定して上回ること。

### 必須記録

各runで必ず保存する。

- model/checkpoint bytes
- peak RSS
- training wall time
- CPU latency
- seed/split/frame count
- exact config and commit
- raw logs and checksums
- Correct/Random/Language-blind/State-only/Target-label-shuffle/Outcome-shuffle
- action histogram、entropy、reward到達率、episode長

## P0 — Evaluation contract freeze

D015〜D035を凍結する。次の実bundleまでは新規auditorを追加しない。

許可作業:

1. preserved R0.1 artifactへ既存gateを適用。
2. fail componentと最初のactionable root causeを保存。
3. 実bundleが具体的な監査欠陥を示した場合だけ修正。

監査CI成功、文書更新、queued/cancelled runは能力進歩に数えない。

## P1 — J-CRe3 external Japanese baseline

1. 最新一次文献、公式code、exact commit、dataset/licenseを確認。
2. 公式評価commandをそのまま再現。
3. model bytes、RSS、runtime、seed、split、raw logs、checksumsを保存。
4. random／language-blind／state-only／shuffleの定義可否を明示。
5. 公式値との差を、実装・最適化・表現・データの4分類で診断。

公式再現が完了するまで独自改善を入れない。再現後のみ同一resource budget下で改善案をscreeningする。

## P1 — R0.2 Environment-first

R0.2はimmutable R0.1 competence bundle通過後のみ開始する。

比較:

- Environment-first
- parameter-matched End-to-end
- State-only

目的は新規表現の主張ではなく、**同一parameter/frame budgetでlanguage-data efficiencyまたはdynamics holdout性能を改善できるか**の検証である。

採用条件:

- source policy competence成立。
- 3-seed平均改善。
- 最低seed悪化なし。
- next-state prediction、action accuracy、online task successの少なくとも2指標で整合。

## Closed — R0.3 hidden intervention-target track

SILG/RTFMにはground-truth latent intervention family、target、mechanism operator、causal abstractionがない。研究者作成ontologyを追加せず棄却維持する。

## P1 — Prior-art and novelty matrix

prior-art auditは、性能実験を止めない範囲で並行する。

各回確認:

1. 最新一次文献と公式codeの重複。
2. SILG/J-CRe3等の再現進捗。
3. random/language-blind/state-only/shuffle対照。
4. model/RSS/runtime/seed/split。
5. leakage。
6. RQ-001の採用・狭域化・棄却条件。

新規文献追加だけのiterationは禁止する。各iterationには必ず、性能実験結果、失敗原因、または再現差分のいずれか1件を含める。

## P2 — RQ-001

広義RQ-001は棄却。狭義RQ-001は未採用を維持する。

採用前条件:

- 最強の適用可能な非言語baseline再現。
- residual countermodel pairの提示。
- externally fixed anti-recoding law。
- exactly one preregistered claim/counterexample/stopping rule。

## Stage transition

次stageは以下すべての完了後だけ提案する。

1. competent learned external public capability baseline 1件以上。
2. immutable matched controls。
3. canonical three-seed qualification。
4. qualified R0.2 comparison。
5. R0.3 rejection維持。
6. novelty matrix完了。
7. 中心命題の事前登録完了。

## Status

- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 高校生級知能: **未達**
- 完成: **false**
