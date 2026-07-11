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

## Phase 11a: ジャンル中立program induction

一つのtyped MDL program synthesizerへ共通transition traceを渡し、ジャンル別handlerなしでprogramを誘導します。

- domain-specific handlers: 0
- expressible tasks: 8、held-out 8/8
- 新規task 2件をengine変更0・trace追加だけで獲得
- learned programs 4,616bit、trace丸暗記22,984bit、4.98倍圧縮
- depth-three targetは20,000候補で失敗
- `uppercase`はprimitive不足で表現不能

結果・設計: [`phase11a`](results/phase11a.md) / [`theory`](docs/phase11a_domain_neutral_program_induction.md)

## Phase 11b: 再利用可能macro library

異なる2つの検証済みprogramに繰り返し現れた部分木だけを、引数番号をalpha-normalizeしてtyped macroへ昇格します。一度しか現れない部分式は保存しません。

- source programs: 2、held-outとも100%
- discovered macro: `a - (b + c)`、984bit
- primitive-only: `(a-b-c)*d` が20,000候補で失敗
- macro library: 3,275候補・探索深さ1で発見
- training / held-out: 100% / 100%
- compact call 488bit、expanded 504bit
- 正規化生涯利得15,757bitで採用

macroはジャンル専用solverを追加せず、過去に検証された計算を次のtaskの探索primitiveとして再利用します。ただしraw grounding、stateful/recursive macro、library競合、forgetting、primitive発明は未解決です。

結果・設計: [`phase11b`](results/phase11b.md) / [`theory`](docs/phase11b_macro_library_induction.md)

## 次の段階

Phase 11cでは、現在のgrammarで表現不能な残差から新primitiveやstate distinctionを提案し、複数taskのheld-outで再利用できる場合だけ採用します。研究者が失敗を見て専用primitiveを手書きする方式には戻しません。

## 再現

```bash
cd minimal-predictive-lm
pip install -e .
python -m unittest discover -s tests -v
mpm-phase11a
mpm-phase11b
```

GitHub ActionsではPhase 1から最新Phaseまで全unit test・全再現実験を実行します。
