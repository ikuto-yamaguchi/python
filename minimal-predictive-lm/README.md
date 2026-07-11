# Minimum Predictive Machine

Transformerを小さくするのではなく、系列予測・意味処理・仕事実行に必要な**最小記憶**と**最小計算**を、数学的下限と実測コストから逆算する研究です。

最終目標は、会話、文章作成、コーディング、ツール利用を伴うエージェント処理で、高性能LLMと同等以上の能力を、より小さい生涯総資源で実現することです。

## 中心原理

過去全文を保持する必要はありません。同じ未来分布、または同じ将来意思決定価値を与える履歴は、同一状態へ圧縮できます。

```text
h ~ h'  iff  P(future | h) = P(future | h')
```

ただし、状態だけ小さくしても、遷移表、検索、学習、検証、外部知識が巨大なら最小機械ではありません。能力ごとに別表現を追加すれば、同じ事実や目標のコピーと変換も増えます。

そのため、次を同時に会計します。

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

## ランタイム方針

- 意味理解、記憶、推論をdense neural residualへ丸投げしない
- 最終バイナリにニューラル重みを残さない研究経路を優先する
- 記憶、推論、計画、創造、文章、コード編集を別ランタイムにしない
- 正準symbol、疎な事実状態、同じ書換え原理を共有する
- 汎用IRは部分評価、規則融合、状態最小化し、実行時overheadを消す
- cache、index、新命令は、生涯目的を改善した場合だけ採用する
- 成功値だけでなく、held-out失敗と探索爆発もCIへ固定する

## Phase 1: 最小予測状態

Hankel行列から最小線形予測次元と離散因果状態を復元しました。

- IID過程: Hankel rank 1、因果状態1、実行時状態0bit
- 2〜8状態のmodulo過程で真の最小状態数を復元
- 8状態の密なSVD表現: 576bytes、64 MAC/記号
- 離散因果状態: 48bytes、0 MAC/記号
- 最大特異値gapの誤判定を、分割データ由来のnoise floorで修正

詳細: [`results/phase1.md`](results/phase1.md)

## Phase 2: 遷移法則の因数分解

K個の独立bitを持つ予測言語で、状態情報量と遷移program記述長を分離しました。

- 厳密予測には最低K bit必要
- 平坦な因果状態表はready状態だけで `2^K`
- K=32の疎な平坦表でも約5.6TB
- 因数分解レジスタ機械はK bit＋定数規則
- dense FP32状態よりdata書込み量を約6656分の1へ削減

詳細: [`results/phase2.md`](results/phase2.md)

## Phase 3a: MDLによる構造探索

必要slot数を与えず、0〜16slotと書込み規則を探索しました。

- 100,000 tokenの8-key言語から8slot・offset 0を選択
- 15,486 QUERYを0誤り
- 少ないslotは誤り、多いslotは余分な記述bitで敗北

詳細: [`results/phase3a.md`](results/phase3a.md)

## Phase 4a: コンパイル済み超軽量バイトLM

held-out NLL改善が規則自身の記述長を上回る文脈だけを残し、failure-link状態機械へコンパイルしました。

- 学習625,748bytes、別seed test 155,073bytes
- 選択規則608、コンパイル状態696
- 実行時状態10bit
- `.mplm` binary 10,999bytes
- 0.468469605 BPB
- 平均1.015644遷移確認/byte

これは表層予測の橋渡し実験であり、open-domain意味理解の主張ではありません。

詳細: [`results/phase4a.md`](results/phase4a.md)

## Phase 4b〜4c: no-neural意味・創造機械

- 未知固有名詞はexact symbol tableへ一度だけ保存
- 世界状態はtimestamp付き疎関係として更新・撤回
- 質問はqueryへコンパイルし、関連規則だけ実行
- 回答はproof traceから生成
- 創造性は意味program変形、候補生成、criticへ分解
- 外部知識、検索、候補探索も総コストへ含める

設計:

- [`docs/phase4b_minimal_semantic_machine.md`](docs/phase4b_minimal_semantic_machine.md)
- [`docs/phase4c_creative_semantic_machine.md`](docs/phase4c_creative_semantic_machine.md)

## Phase 5a: coding / writing / agentの統一基盤

能力ごとに部品を継ぎ足さず、次の5命令を共有します。

```text
MATCH
DELETE
ADD
EMIT
CHOOSE_MIN
```

一つのsymbol table、state、rule、疎index、MDL探索器で、コード編集、文章構成、行動計画を処理しました。

詳細:

- [`results/phase5a.md`](results/phase5a.md)
- [`docs/phase5_unified_work_machine.md`](docs/phase5_unified_work_machine.md)

## Phase 6: 下限、スケーリング、生涯大域最適

- 256段chain: 平坦規則5,376bit → 因数分解43bit
- 位置状態は理論下限9bit
- 20bit parity: 任意表1,048,576bit → 規則27bit＋状態1bit
- 必要な20bit読取りや256依存stepは不可避として残す
- Value of Computationで、判断を変える期待値が費用を上回る場合だけ追加思考
- 16-query workload: 局所commit 16,384、生涯大域選択4,032

詳細:

- [`docs/phase6_scaling_and_open_ended_intelligence.md`](docs/phase6_scaling_and_open_ended_intelligence.md)
- [`docs/phase6b_minimal_choice_machine.md`](docs/phase6b_minimal_choice_machine.md)
- [`docs/phase6c_global_optimization.md`](docs/phase6c_global_optimization.md)
- [`results/phase6a.md`](results/phase6a.md)
- [`results/phase6c.md`](results/phase6c.md)

## Phase 7a: 会話・指示追従・失敗後の再試行

- 制御grammar: 35.3% → 82.4% → 100%
- 砕けたheld-out表現: 50%
- 観測失敗表現を個別rewriteすると、別系列で再び50%
- 10,000回の反復質問でもpersistent state量は増加なし
- 4,096事実でもindexed lookupは1 read
- test失敗 → 証拠保存 → 再試行 → 最終検証のtask loopを実装
- コード候補探索は候補数に比例し、実repositoryには未達

詳細:

- [`docs/phase7_scaling_to_conversation.md`](docs/phase7_scaling_to_conversation.md)
- [`results/phase7a.md`](results/phase7a.md)

## Phase 8a: 残差駆動の意味program誘導

固有名詞と場所をtyped slotへ置換し、1〜2個の構造・文字特徴からなる最小規則をMDLで選びました。

| parser | 未知組合せ | distractor拒否 | 未知言い換え |
|---|---:|---:|---:|
| exact surface | 0.0% | 100.0% | 0.0% |
| typed slot templates | 100.0% | 100.0% | 0.0% |
| induced feature program | 100.0% | 87.5% | 33.3% |

- entity/location各128: 表面列挙22,112,432bit → program＋symbol 13,989bit
- 約1,580.7倍削減
- 別の言い換え系列では16.7%で、open-domain意味理解は未達

詳細:

- [`docs/phase8_residual_semantic_program_induction.md`](docs/phase8_residual_semantic_program_induction.md)
- [`results/phase8a.md`](results/phase8a.md)

## Phase 8b: interaction traceから潜在操作・役割を誘導

intent名やentity/location型を与えず、`pre-state / utterance / post-state / response`から操作を逆算しました。

- 9/9 interactionから操作を復元
- `SET(key,value) / GET(key)` を誘導
- key/value latent role purity 100% / 100%
- exact surface objective 4,130
- untyped symbols objective 1,964
- 2 latent roles objective 953、held-out 100%
- surface intent 202bit → state effect 163bit
- 新symbolは文字列bitだけを払い、追加rule 0bitで再利用

詳細:

- [`docs/phase8b_latent_roles_and_operations.md`](docs/phase8b_latent_roles_and_operations.md)
- [`results/phase8b.md`](results/phase8b.md)

## Phase 8c: 複数relation・部分観測・noise・遅延effect

意味名を持たない3つのopaque effect channelへ言語を接地しました。

- 27 traces、正解operation 24
- full SET 6/6、partial SET 3/3、delayed SET 3/3、GET 12/12
- raw operation推定: recall 100%、precision 96%
- 偶然のexogenous changeを1本だけ誤相関
- support 1 schemaは誤規則を保存し、held-out 94.7%
- support 2＋confidence schemaは誤規則を除去し、held-out 19/19

| hypothesis | bits | validation | lifetime objective |
|---|---:|---:|---:|
| exact surface | 6,400 | 36.8% | 18,688 |
| support 1 schema | 3,983 | 94.7% | 5,007 |
| robust multi-relation schema | 3,703 | 100.0% | 3,703 |

- 12-rule線形走査: 12 checks/input
- cue index: 平均0.789 checks/input
- index pointer 48bitもdescription lengthへ含む
- 新opaque relation: 2 traces、1 rule、357bit、held-out recombination 100%

ただしeffect channel IDは観測可能でした。

詳細:

- [`docs/phase8c_multi_relation_semantics.md`](docs/phase8c_multi_relation_semantics.md)
- [`results/phase8c.md`](results/phase8c.md)

## Phase 8d: anonymous sensorからrelation partitionを発見

relation channelを与えず、entityごとに割り当てが異なる2つのanonymous sensor cell、utterance、value、4-step timelineだけを与えました。

hidden world:

```text
location relation: lag 2
owner relation:    lag 1
```

4 surface templatesの全set partition 15通りをoracleとして比較しました。

- training traces: 16
- true effect candidate recall: 100%
- ambiguous noise trace: 1、共有構造で正しいcell/lagへ解決
- hidden relation partition: exact recovery
- recovered relation数: 2
- recovered lag: 1 / 2
- training error: 0
- 新entityでrelationごと1回calibration後、未観測paraphrase: 100%

| hypothesis | clusters | train errors | bits | new-entity validation | objective |
|---|---:|---:|---:|---:|---:|
| merged one relation | 1 | 7 | 35 | 50% | 5,667 |
| best three relation | 3 | 0 | 101 | 50% | 2,149 |
| flat four relation | 4 | 0 | 132 | 0% | 4,228 |
| selected two relation | 2 | 0 | 66 | 100% | 66 |

4-cluster modelは訓練誤り0でも、新entityではcalibration templateから同relationのparaphraseへ転移できません。正しい2-relation因数分解だけが100%転移しました。

### 表現スケーリング

32 surface templatesが2 latent relationsから生成される例:

| entities | flat assignment bits | latent partition bits | ratio |
|---:|---:|---:|---:|
| 8 | 256 | 102 | 2.51x |
| 32 | 1,024 | 150 | 6.83x |
| 128 | 4,096 | 342 | 11.98x |
| 512 | 16,384 | 1,110 | 14.76x |

### 探索スケーリングの失敗

全partition探索はBell numberで爆発します。

| templates | partitions |
|---:|---:|
| 4 | 15 |
| 6 | 203 |
| 8 | 4,140 |
| 10 | 115,975 |
| 12 | 4,213,597 |

したがって、この全探索は小世界のoracle・下限比較用であり、そのまま汎用learnerにはなりません。

詳細:

- [`docs/phase8d_latent_relation_partition.md`](docs/phase8d_latent_relation_partition.md)
- [`results/phase8d.md`](results/phase8d.md)

## 次の実験

Phase 8eではBell全探索を廃止し、現在のclusterで予測できない**残差衝突**だけから必要なsplitを提案します。

1. 同じ内部状態なのに異なるeffectを要求するtraceを検出
2. cell、lag、resultの最小差分を抽出
3. cluster split候補を局所生成
4. held-out regret削減が追加bit、探索、検証、移行費用を上回る場合だけ採用
5. 不要clusterはmerge / delete

さらに、固定relation数、固定lag、value完全一致、deterministic effectを順に外し、会話、文章、コード、tool actionを同じ評価へ混在させます。

## 実行

```bash
cd minimal-predictive-lm
python -m venv .venv
source .venv/bin/activate
pip install -e .

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
python -m unittest discover -s tests -v
```

`mpm-phase4a` は実モデル `results/phase4a.mplm` も生成します。GitHub Actionsで全テストと全実験をゼロから再現します。
