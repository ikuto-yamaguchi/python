# Minimum Predictive Machine

Transformerを単純に小型化するのではなく、会話・文章・コード・ツール利用に必要な**最小記憶・最小読書き・最小計算**を数学的下限と実測から構成する研究です。

最終目標は、高性能LLMと同等以上の総合能力を、より小さい生涯総資源で実現することです。現時点では未達です。成功値だけでなく、自由言語、分布外、探索爆発、学習・検証費用の失敗も結果とCIへ固定します。

## 最小化する目的

```text
prediction / task loss
+ static program bits
+ static knowledge bits
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
- 新しい規則、cache、index、命令は、生涯目的を改善した場合だけ採用する
- 判断を変える期待値が費用を上回る場合だけ追加思考・観測を行う

## Phase 1〜3: 最小状態と構造探索

- IID過程: 因果状態1、実行時状態0bit
- 2〜8状態のmodulo過程で真の最小状態数を復元
- 8状態dense SVD 576bytes・64 MAC/記号 → 離散因果状態48bytes・0 MAC/記号
- K=32の疎な平坦状態表約5.6TB → 32bit＋定数規則
- MDL探索が8-key言語から8slot・offset 0を自動選択

結果: [`phase1`](results/phase1.md) / [`phase2`](results/phase2.md) / [`phase3a`](results/phase3a.md)

## Phase 4: 実バイトLMと意味・創造設計

- 学習625,748bytes、別seed test 155,073bytes
- 選択規則608、コンパイル状態696
- 実行時状態10bit、`.mplm` 10,999bytes
- 0.468469605 BPB、平均1.015644遷移確認/byte

これは表層予測の橋渡しであり、open-domain意味理解ではありません。

結果・設計: [`phase4a`](results/phase4a.md) / [`semantic machine`](docs/phase4b_minimal_semantic_machine.md) / [`creative machine`](docs/phase4c_creative_semantic_machine.md)

## Phase 5: coding / writing / agentの統一基盤

```text
MATCH
DELETE
ADD
EMIT
CHOOSE_MIN
```

一つのsymbol table、state、rule、疎index、MDL探索器で、コード編集、文章構成、行動計画のmicro-taskを処理しました。

結果: [`phase5a`](results/phase5a.md)

## Phase 6: 下限・Value of Computation・生涯大域最適

- 256段chain: 平坦規則5,376bit → 因数分解43bit、状態下限9bit
- 20bit parity: 任意表1,048,576bit → 規則27bit＋状態1bit
- 必要な20bit読取りと256依存stepは不可避として残す
- 16-query workload: 局所commit 16,384、生涯大域選択4,032

設計・結果: [`scaling`](docs/phase6_scaling_and_open_ended_intelligence.md) / [`choice`](docs/phase6b_minimal_choice_machine.md) / [`global optimization`](docs/phase6c_global_optimization.md)

## Phase 7: 会話・指示追従・失敗後の再試行

- 制御grammar: 35.3% → 82.4% → 100%
- 砕けたheld-out表現: 50%
- 個別rewrite追加後も別系列で再び50%
- 10,000回の反復質問でも不要なpersistent stateは増加なし
- 4,096事実でもindexed lookup 1 read
- test失敗 → 証拠保存 → 再試行 → 最終検証を実装
- コード候補探索は候補数に比例し、実repositoryには未達

結果: [`phase7a`](results/phase7a.md)

## Phase 8a〜8b: 表面記憶から潜在操作へ

- typed slotは未知symbol組合せ100%
- entity/location各128: 表面列挙22,112,432bit → program＋symbol 13,989bit
- intent/type labelを与えずinteraction traceから `SET / GET` を9/9復元
- key/value latent role purity 100% / 100%
- exact surface objective 4,130、untyped 1,964、latent roles 953
- 別の言い換え系列では16.7%で、自由言語理解は未達

結果: [`phase8a`](results/phase8a.md) / [`phase8b`](results/phase8b.md)

## Phase 8c〜8e: 複数relation発見と探索削減

- 部分観測、noise、遅延effectを処理
- relation channelを外し、anonymous sensorからrelation partitionとlagを復元
- 正しい因数分解だけが新entityの未観測paraphraseへ100%転移
- Bell数の全partition探索を残差split＋bounded beamへ置換

| templates | Bell partitions | evaluated | exact partition | oracle gap |
|---:|---:|---:|---:|---:|
| 4 | 15 | 13 | yes | 0 |
| 8 | 4,140 | 35 | yes | 0 |
| 12 | 4,213,597 | 55 | yes | n/a |
| 32 | 128,064,670,049,908,713,818,925,644 | 101 | yes | n/a |

結果: [`phase8c`](results/phase8c.md) / [`phase8d`](results/phase8d.md) / [`phase8e`](results/phase8e.md)

## Phase 8f: 確率effect・欠測・Value of Information

- 1,200 episodesを126bitの十分統計へ圧縮
- compact raw event 10,800bit、圧縮比85.71x
- learned Brier 0.157493、uniform 0.25
- VOIは常時観測と同じ87.9%で、3,000回中1,127 sensor readを削減
- provenance ledgerとresolved active viewを分離

| policy | accuracy | probes | objective |
|---|---:|---:|---:|
| none | 77.6% | 0 | 43,072 |
| always | 87.9% | 3,000 | 35,232 |
| VOI | 87.9% | 1,873 | 30,724 |

結果: [`phase8f`](results/phase8f.md)

## Phase 8g: 会話・文章・コード・ツールの共有確率eventモデル

16個の領域別surface actionを、結果・成功率・遅延分布から4つの共有操作 `SET / VERIFY / RETRACT / EMIT` へ統合しました。隠れたoperation名はlearnerへ渡していません。

- 8-template oracle: 全4,140 partitionと同じ解、gap 0
- 16 templates: 31,652 merge候補を評価し、4 latent operationsを完全復元
- 領域別16 schema objective 2,118.346 → 共有4 schema 1,192.948
- 十分統計560bit、compact event stream 8,320bit
- 新しいtool領域は各surface 6 eventsで既存operationへ100%接続
- pooled Brier 0.131574、6-shot単独0.134095

非定常operationでは真のchange point 200に対し201を検出し、stationary Brier 0.280289 → adaptive 0.248998。400bit履歴を45bitの2区間summaryへ圧縮しました。

3種類のsensorを持つ有限binary POMDPでは、全action・全outcomeを動的計画で厳密列挙しました。

| policy | mean total cost | mean error | mean probes |
|---|---:|---:|---:|
| none | 17.777778 | 0.277778 | 0.000000 |
| one probe | 10.726222 | 0.106833 | 0.777778 |
| exact bounded | 9.759698 | 0.092136 | 1.013220 |
| always | 13.642492 | 0.072539 | 3.000000 |

結果・設計: [`phase8g`](results/phase8g.md) / [`theory`](docs/phase8g_shared_stochastic_event_intelligence.md)

### Phase 8gの限界

- 自由文ではなくpersistent surface template IDを使う
- effect categoryが潜在operationのanchorとして観測可能
- change pointは1回の急変のみ
- exact POMDPはbinary state・3 probesのみ
- 実repository、長文執筆、自由会話ではなくsynthetic micro-world

## 次の実験

Phase 9aではpersistent template IDを外し、raw text / AST / test output / tool traceから共通のevent programを誘導します。

1. 自由な言い換えとAST差分を同じeffectへgrounding
2. 会話依頼 → コード編集 → test → rollback → 修正 → 報告を一つのstateで実行
3. domain別pipelineとのbit・copy・conversion・tool・失敗率比較
4. unknown paraphrase、unknown repository symbol、hidden testsで評価
5. 汎用IRを部分評価し、最終runtimeからparser・unifier・search overheadを削除

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
```

`mpm-phase4a` は実モデル `results/phase4a.mplm` も生成します。GitHub ActionsでPhase 1〜8gの全テスト・全実験をゼロから再現します。
