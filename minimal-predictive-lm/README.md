# Minimum Predictive Machine

Transformerを単純に小型化するのではなく、会話・知識・数学・コード・長文・創作に必要な**最小記憶・最小読書き・最小計算**を、数学的下限と再現実験から構成する研究です。

最終目標は、高性能LLMと同等以上、さらに明確に定義された課題分布では熟練人間を上回る能力を、より小さい生涯総資源で実現することです。現時点では未達です。自由言語、公開benchmark、実repository、長文理解、創作、探索費用の失敗もCIへ固定します。

## 生涯目的

```text
prediction / task loss
+ static program and knowledge bits
+ dynamic state bits
+ bits read / written
+ primitive operations
+ external observations and effects
+ induction / training / compiler amortization
+ verification / migration / rollback
+ representation-boundary cost
+ held-out and shifted-task regret
```

小さな活動状態だけを示し、巨大な遷移表、外部検索、教師モデル、tool呼出し、探索へ費用を隠すことは許しません。

## 中心原理

- 同じ未来予測・同じ将来意思決定を与える履歴は同一因果状態へ圧縮する
- 記憶、推論、計画、会話、文章、コード編集を別々の世界モデルにしない
- 正準symbol、疎なfact/event graph、同じ書換え・選択原理を共有する
- 判断を変える期待値が費用を上回る場合だけ追加思考・観測する
- 現在の表現では最善行動を区別できないときだけ、新しいrelation・role・graphを発明する
- 新規則・新表現・自己変更は、生涯目的を改善し、検証とrollbackが可能な場合だけ採用する
- 言語は唯一の知能表現ではなく、共有概念への観測・出力codecとして扱う

## Phase 1〜3: 最小因果状態と構造探索

- IID過程: 因果状態1、実行時状態0bit
- 2〜8状態のmodulo過程で真の最小状態数を復元
- 8状態dense SVD 576bytes・64 MAC/記号 → 離散因果状態48bytes・0 MAC/記号
- K=32の疎な平坦状態表約5.6TB → 32bit＋定数規則
- MDL探索が8-key言語から8slot・offset 0を選択

結果: [`phase1`](results/phase1.md) / [`phase2`](results/phase2.md) / [`phase3a`](results/phase3a.md)

## Phase 4〜5: 実LMと統一仕事基盤

- 学習625,748bytes、別seed test 155,073bytes
- 選択規則608、コンパイル状態696
- 実行時状態10bit、`.mplm` 10,999bytes
- 0.468469605 BPB、平均1.015644遷移確認/byte
- `MATCH / DELETE / ADD / EMIT / CHOOSE_MIN`でコード、文章、行動計画のmicro-taskを処理

これはopen-domain意味理解ではなく、表層予測から意味機械への橋渡しです。

結果・設計: [`phase4a`](results/phase4a.md) / [`semantic`](docs/phase4b_minimal_semantic_machine.md) / [`creative`](docs/phase4c_creative_semantic_machine.md) / [`phase5a`](results/phase5a.md)

## Phase 6: 下限・Value of Computation・生涯大域最適

- 256段chain: 平坦規則5,376bit → 因数分解43bit、状態下限9bit
- 20bit parity: 任意表1,048,576bit → 規則27bit＋状態1bit
- 必要な20bit読取りと256依存stepは不可避として残す
- 16-query workload: 局所commit 16,384 → 生涯大域選択4,032

設計: [`scaling`](docs/phase6_scaling_and_open_ended_intelligence.md) / [`choice`](docs/phase6b_minimal_choice_machine.md) / [`global`](docs/phase6c_global_optimization.md)

## Phase 7: 会話・指示追従・失敗後の再試行

- 制御grammar: 35.3% → 82.4% → 100%
- 砕けたheld-out表現: 50%
- 個別rewrite追加後も別系列で再び50%
- 10,000反復でも不要なpersistent stateは増加なし
- 4,096事実でもindexed lookup 1 read
- test失敗 → 証拠保存 → 再試行 → 最終検証

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

## Phase 9: raw grounding・階層event graph・connector誘導

- raw Japanese、AST-like text、test output、tool traceを共有programへgrounding
- training 34例、selected rules 15、共有program 1,412bit
- exact surface near-heldout 0% → sparse grounder 100%
- 遠い語彙転換は6.25%で未達
- 条件、否定、引用、照応、発話行為、埋め込み命題を疎グラフへ分解
- single-label event recall 3.3% → graph event/edge recall 100%
- active graph 3,388bit、provenance込み7,204bit、flat JSON 22,328bit
- 未知connector 5種: 表面一致0% → interaction effectから100%誘導

結果・設計: [`9a`](results/phase9a.md) / [`9b`](results/phase9b.md) / [`9c`](results/phase9c.md) / [`raw`](docs/phase9a_raw_event_grounding.md) / [`graph`](docs/phase9b_hierarchical_event_graph.md) / [`connector`](docs/phase9c_connector_induction.md)

## Phase 10: Stage-C・concept-first・公開比較

- 会話、知識、数学、コード、長文、創作を証拠level 0〜4で管理
- 非言語interactionから概念を先に獲得し、言語を後付けcodec化
- provenance・矛盾・source trust・棄権・VOIを持つ外部知識
- 公開BIG-bench直接算術200問で100%
- SmolLM2-135M-Instruct matched runは9%
- GSM8Kは0/1,319で、多段文章題parityは不成立

結果: [`10a`](results/phase10a.md) / [`10b`](results/phase10b.md) / [`10c`](results/phase10c.md) / [`10d`](results/phase10d.md) / [`10e`](results/phase10e.md) / [`10f`](results/phase10f.md) / [`10g`](results/phase10g.md) / [`10h`](results/phase10h.md) / [`10i`](results/phase10i.md)

## Phase 11: ジャンル別手設計からの脱出

- 共通typed MDL synthesizerが8 taskをheld-out 8/8で誘導
- 新規task 2件はengine変更0・trace追加だけで獲得
- 2 taskの共通部分から `a-(b+c)` をmacro化
- 20,000候補で失敗したtargetをmacro込み3,275候補・深さ1で解決
- 固定grammarで表現不能な文字変換からASCII offset primitiveを発明
- raw Japanese、code diff、tool trace、dialogue、test logから2 primitive clusterを誘導
- Unicode residual extension、過剰更新rollback、context splitをversioned libraryで管理
- record/channel labelなしのcontinuous streamでevent・primitiveを100%復元

ただしbounded meta-grammar、短いsynthetic stream、ASCII中心の候補表現は残っています。

結果・設計: [`11a`](results/phase11a.md) / [`11b`](results/phase11b.md) / [`11c`](results/phase11c.md) / [`11d`](results/phase11d.md) / [`11e`](results/phase11e.md)

## Phase 12: mixed multi-axis learnerと探索的open-model比較

同じlearnerへ算術、state更新、条件分岐、文字変換、composition、provenance、event抽出を混在させました。

### Phase 12a

- calibration interactions: 40
- routing rules: 11
- compiled payload: 7,136bit / 892bytes
- induction candidate evaluations: 108,238
- domain-specific handlers: 0
- public arithmetic 40/40
- synthetic 6軸30/30
- 全7軸70/70
- calibrationとbenchmarkのexact prompt overlap: 0

### Phase 12b exploratory comparison

同じ70問と40 prompt-output demonstrationsをSmolLM2-135M-Instructにも与えました。

| system | accuracy | model bytes | peak RSS | wall time |
|---|---:|---:|---:|---:|
| MPM | 100.0% | 892 | 50,737,152 | 4.329s |
| SmolLM2 | 35.7% | 538,060,032 | 1,856,081,920 | 174.368s |

これは厳密なmulti-domain parityではありません。6軸がsyntheticであり、state calibrationの構造化evidenceも一致しないため、strict quality / runtime Pareto / general LLM claimはすべて不許可です。

結果・設計: [`12a`](results/phase12a.md) / [`12b`](results/phase12b.md) / [`12a theory`](docs/phase12a_mixed_multi_axis_learner.md) / [`12b theory`](docs/phase12b_exploratory_mixed_open_model_comparison.md)

## Public reality evidence

公開raw benchmarkへ移った後の凍結結果は、controlled gateより大幅に弱いものでした。

- Phase 13a: 40/200。直接算術以外の4軸は0%。
- Phase 15a: 新規5軸で0/200。
- Phase 16a: さらに新規5軸で0/200。

この結果を無視してcontrolled relation gateを増やしても、高校生級への見通しにはなりません。CAP-SEM-001〜005はcomponent evidenceとして保存しますが、critical pathから凍結します。

## Current critical path: CAP-GEN

[`intelligence roadmap`](docs/intelligence_roadmap_and_stop_rules.md) に従い、現在の最優先は `CAP-GEN-001` です。

- 過去3回の公開sliceを統合した15軸600問
- 単一worker・単一fingerprint
- model入力からtask/axis名を隠す
- aggregate scoreと最低axis scoreを同時評価
- micro-gateではなく、複数の無関係axisが同時に改善した場合だけ進展と認定

3回の大規模architecture iterationで統合accuracyが合計15ポイント以上改善しなければ、現core architectureを放棄します。2回の大規模iteration後も0%のaxisが残る場合、local solver追加ではなくshared representationまたはlearning objectiveを変更します。

## 到達条件

「日本の賢い高校生」は曖昧な呼称ではなく、[`high-school target`](docs/phase18_japanese_high_school_intelligence_target.md) の凍結gateで判定します。

- aggregate 80%以上
- 全domain 70%以上
- 新規未見問題75%以上
- 記述式70%以上
- 誤答訂正80%以上
- 日本語、数学、英語、理科、地歴公民、情報、長文統合、実repository作業を含む

現状から1〜2個の能力追加で到達する段階ではありません。CAP-GEN-002とCAP-GEN-003を先に通し、その後に初めて高校生級候補となります。

## Reproduction

```bash
cd minimal-predictive-lm
pip install -e .
python -m unittest discover -s tests -v
python -m minimal_predictive_lm.cap_gen_001_integrated_public_reality_gate
```

GitHub ActionsではPhase 1から最新の軽量Phaseまで全unit test・全再現実験を実行します。重い比較は専用workflowへ分離します。
