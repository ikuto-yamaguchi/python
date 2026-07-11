# Minimum Predictive Machine

Transformerを単純に小型化するのではなく、会話・文章・コード・ツール利用に必要な**最小記憶・最小読書き・最小計算**を、数学的下限と実測から構成する研究です。

最終目標は、高性能LLMと同等以上、さらに明確に定義された課題分布では熟練人間を上回る能力を、より小さい生涯総資源で実現することです。現時点では未達です。成功値だけでなく、自由言語、分布外、探索爆発、学習・検証費用の失敗も結果とCIへ固定します。

## 最小化する目的

```text
prediction / task loss
+ static program and knowledge bits
+ dynamic state bits
+ bits read / written
+ primitive operations
+ external effects
+ induction / training / compiler amortization
+ verification / migration / rollback
+ representation-boundary cost
+ held-out and shifted-task regret
```

状態だけを小さくし、巨大な遷移表、外部検索、教師モデル、ツール呼出しへ費用を隠すことは許しません。

## 中心原理

- 同じ未来予測・同じ将来意思決定を与える履歴は同一状態へ圧縮する
- 記憶、推論、計画、文章、コード編集を別ランタイムにしない
- 正準symbol、疎なfact/event状態、同じ書換え・選択原理を共有する
- 汎用IRは部分評価・規則融合・状態最小化し、実行時overheadを消す
- 判断を変える期待値が費用を上回る場合だけ追加思考・観測する
- 現在の表現が異なる最善行動を区別できないときだけ表現を発明する
- 新規則・新表現・自己変更は、生涯目的を改善しrollback可能な場合だけ採用する

## Phase 1〜3: 最小状態と構造探索

- IID過程: 因果状態1、実行時状態0bit
- 2〜8状態のmodulo過程で真の最小状態数を復元
- 8状態dense SVD 576bytes・64 MAC/記号 → 離散因果状態48bytes・0 MAC/記号
- K=32の疎な平坦状態表約5.6TB → 32bit＋定数規則
- MDL探索が8-key言語から8slot・offset 0を自動選択

結果: [`phase1`](results/phase1.md) / [`phase2`](results/phase2.md) / [`phase3a`](results/phase3a.md)

## Phase 4〜5: 実LMと統一仕事基盤

実バイトLM:

- 学習625,748bytes、別seed test 155,073bytes
- 選択規則608、コンパイル状態696
- 実行時状態10bit、`.mplm` 10,999bytes
- 0.468469605 BPB、平均1.015644遷移確認/byte

一つのsymbol table、state、rule、疎index、MDL探索器と、

```text
MATCH / DELETE / ADD / EMIT / CHOOSE_MIN
```

で、コード編集、文章構成、行動計画のmicro-taskを処理しました。

結果・設計: [`phase4a`](results/phase4a.md) / [`semantic`](docs/phase4b_minimal_semantic_machine.md) / [`creative`](docs/phase4c_creative_semantic_machine.md) / [`phase5a`](results/phase5a.md)

## Phase 6: 下限・Value of Computation・生涯大域最適

- 256段chain: 平坦規則5,376bit → 因数分解43bit、状態下限9bit
- 20bit parity: 任意表1,048,576bit → 規則27bit＋状態1bit
- 必要な20bit読取りと256依存stepは不可避として残す
- 16-query workload: 局所commit 16,384、生涯大域選択4,032

設計: [`scaling`](docs/phase6_scaling_and_open_ended_intelligence.md) / [`choice`](docs/phase6b_minimal_choice_machine.md) / [`global`](docs/phase6c_global_optimization.md)

## Phase 7: 会話・指示追従・失敗後の再試行

- 制御grammar: 35.3% → 82.4% → 100%
- 砕けたheld-out表現: 50%
- 個別rewrite追加後も別系列で再び50%
- 10,000回の反復質問でも不要なpersistent stateは増加なし
- 4,096事実でもindexed lookup 1 read
- test失敗 → 証拠保存 → 再試行 → 最終検証を実装
- コード候補探索は候補数に比例し、実repositoryには未達

結果: [`phase7a`](results/phase7a.md)

## Phase 8: 潜在意味・確率・探索削減

- intent/type labelなしでinteraction traceから `SET / GET` とlatent roleを誘導
- 部分観測、noise、遅延effectから複数relationを復元
- Bell数の全partition探索を残差split＋bounded beamへ置換
- 32 templatesの約1.28×10^26 partitionに対し101候補でhidden構造を復元
- 1,200 probabilistic episodesを126bitの十分統計へ圧縮
- VOIは常時観測と同じ87.9%で、3,000回中1,127 sensor readを削減
- 会話・文章・コード・toolの16 surface actionsを4 shared operationsへ統合
- 新しいtool領域を各surface 6 eventsで既存operationへ100%接続

結果: [`8a`](results/phase8a.md) / [`8b`](results/phase8b.md) / [`8c`](results/phase8c.md) / [`8d`](results/phase8d.md) / [`8e`](results/phase8e.md) / [`8f`](results/phase8f.md) / [`8g`](results/phase8g.md)

## Phase 9a: template IDなしのraw grounding

raw Japanese、AST-like text、test output、tool traceを一つの `SET / VERIFY / RETRACT / EMIT` programへgroundingしました。

- training 34例、selected rules 15、共有program 1,412bit
- exact surfaceのnear-heldout 0% → 共有sparse grounder 100%
- 4つの領域別モデル1,881bit・94.4%に対し、共有モデル1,412bit・100%
- 遠い語彙転換は6.25%で未達
- 8 interactionで新語follow-up 0% → 87.5%、追加387bit
- repair workflowで `SET → VERIFY → RETRACT → SET → VERIFY → EMIT`
- domain-separated JSON handoffは6,704bit/workflow

結果・設計: [`phase9a`](results/phase9a.md) / [`theory`](docs/phase9a_raw_event_grounding.md)

## Phase 9b: 階層的疎event graph

単一ラベルでは表現できない、条件、否定、引用、照応、発話行為と埋め込み命題を疎グラフへ分解しました。

- benchmark 5ケース
- single-label event recall 3.3%
- graph event recall 100%
- graph edge recall 100%
- unresolved clause 0
- active graph 3,388bit
- raw provenanceを残した合計7,204bit
- flat JSON handoff 22,328bit
- failure → rollback → repair → PASSをgraphから実行
- event graphの表現発明は今回の損失尺度で5回再利用時にbreak-even

結果・設計: [`phase9b`](results/phase9b.md) / [`event graph`](docs/phase9b_hierarchical_event_graph.md)

## 人類を超える知能への条件

「人類超え」は万能性ではなく、同じ情報・道具・期限の下で、品質、信頼性、速度、資源のPareto frontierが熟練人間を上回ることとして定義します。

必要な機構:

1. decision-sufficient stateと正確なprovenance
2. causal modelとcounterfactual simulation
3. candidate generationとrepresentation invention
4. VOI/VOCで停止するbounded search
5. external memoryとcross-domain reuse
6. held-out・shift・adversarial検証付き自己改善
7. rollback可能なcompiler・planner・index更新
8. 人間・強いLLMとの同条件比較

固定有限機械が無限知識を持つことはできません。目標は、知識・観測・探索・コンパイル技能を増やせるopen-ended familyです。

理論: [`superhuman scaling`](docs/phase10_superhuman_intelligence_scaling.md)

## 次の実験

Phase 9cでは、Phase 9bで一部手書きだったconnector・condition・reference構造をinteraction traceから誘導します。その後、小さな実repositoryで、会話依頼 → file read → patch → test → rollback → fix → reportを同じevent graphで実行します。

## 実行

```bash
cd minimal-predictive-lm
python -m venv .venv
source .venv/bin/activate
pip install -e .

python -m unittest discover -s tests -v
mpm-phase1
mpm-phase2
mpm-phase3a
mpm-phase4a
mpm-phase5a
mpm-phase6a
mpm-phase6c
mpm-phase7a
mpm-phase8a
mpm-phase8b
mpm-phase8c
mpm-phase8d
mpm-phase8e
mpm-phase8f
mpm-phase8g
mpm-phase9a
mpm-phase9b
```

GitHub ActionsでPhase 1〜9bの全unit test・全実験をゼロから再現します。
