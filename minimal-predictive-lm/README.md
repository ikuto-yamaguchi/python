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

結果: [`phase7a`](results/phase7a.md)

## Phase 8: 潜在意味・確率・探索削減

- intent/type labelなしでinteraction traceから `SET / GET` とlatent roleを誘導
- 部分観測、noise、遅延effectから複数relationを復元
- Bell数の全partition探索を残差split＋bounded beamへ置換
- 32 templatesの約1.28×10^26 partitionに対し101候補でhidden構造を復元
- 1,200 probabilistic episodesを126bitの十分統計へ圧縮
- VOIは常時観測と同じ87.9%で、3,000回中1,127 sensor readを削減
- 会話・文章・コード・toolの16 surface actionsを4 shared operationsへ統合

結果: [`8a`](results/phase8a.md) / [`8b`](results/phase8b.md) / [`8c`](results/phase8c.md) / [`8d`](results/phase8d.md) / [`8e`](results/phase8e.md) / [`8f`](results/phase8f.md) / [`8g`](results/phase8g.md)

## Phase 9a〜9b: raw groundingと階層event graph

- raw Japanese、AST-like text、test output、tool traceを共有programへgrounding
- training 34例、selected rules 15、共有program 1,412bit
- exact surface near-heldout 0% → sparse grounder 100%
- 遠い語彙転換は6.25%で未達
- 条件、否定、引用、照応、発話行為、埋め込み命題を疎グラフへ分解
- single-label event recall 3.3% → graph event/edge recall 100%
- active graph 3,388bit、provenance込み7,204bit、flat JSON 22,328bit
- failure → rollback → repair → PASSをgraphから実行

結果・設計: [`9a`](results/phase9a.md) / [`9b`](results/phase9b.md) / [`raw grounding`](docs/phase9a_raw_event_grounding.md) / [`event graph`](docs/phase9b_hierarchical_event_graph.md)

## Phase 9c: interaction effectからのconnector意味誘導

connector文字列へrelation labelを直接与えず、action実行、参照、内容、時間順序の観測からMDLでroleを選択しました。

- 基本connector 5種、10 interaction: 100%
- 新connector 5種、表面一致0% → interaction誘導100%
- connector 10種のlexicon 1,144bit
- event graph 6ケース: event/edge recall 100%、unresolved 0

候補relation inventory自体はまだ与えており、open-ended構文・長距離談話は未達です。

結果・設計: [`phase9c`](results/phase9c.md) / [`theory`](docs/phase9c_connector_induction.md)

## Phase 10a: Stage-C readiness gate

会話、知識、数学、コード、長文、創作の6軸を、証拠level 0〜4で管理します。Stage Cは全軸で公開open-domain benchmark、matched input、実測resource、対象open model以上を満たした場合だけ成立します。

初期scorecard:

- 5 / 24点、20.8%
- Stage C ready: false
- parity/Pareto claim allowed: false
- syntheticで100%でも公開比較へ昇格させない

結果・設計: [`phase10a`](results/phase10a.md) / [`Stage-C bridge`](docs/phase10_stage_c_bridge.md)

## Phase 10b: 最小自然言語数学program

問題文と答えから演算labelなしで `ADD / SUB / MUL / DIV / PERCENT_OF` を逆同定し、数値を規則へ保存せず引数としてbindingします。

- training 20例、5 programs、6 feature rules
- program description 642bit
- exact-surface held-out 0% → program held-out 100%
- 未見数値1,000問: 100%
- 遠い数学語彙20% → 10 interaction後100%
- 追加program 282bit
- Stage-C score 7 / 24、29.2%

一段二項算術のみで、文章題、複数step、式変形、証明、幾何、公開benchmarkは未達です。

結果・設計: [`phase10b`](results/phase10b.md) / [`theory`](docs/phase10b_minimal_math_program.md)

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

Phase 10cでは、外部文書から必要な事実だけを取得し、provenance、矛盾検出、confidence、abstentionを同じ疎workspaceへ追加します。その後、数学を複数step・方程式・公開benchmarkへ、コードを小さな実repositoryへ移行します。

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
mpm-phase9c
mpm-phase10a
mpm-phase10b
```

GitHub ActionsでPhase 1〜10bの全unit test・全実験をゼロから再現します。
