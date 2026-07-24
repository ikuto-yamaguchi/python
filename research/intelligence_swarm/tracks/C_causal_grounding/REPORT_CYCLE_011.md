# Causal Grounding Cycle 011

## Hypothesis

**State-Crossing Witnesses Identify Nonparametric Unary Operation Families**

系列A Cycle 010が返したraw character-role proposalを暫定入力とし、operation familyを `noop/mark/swap` の固定集合として与えず、binary state上の全4 unary function（constant-0, constant-1, identity, negation）から、3個のopaque operation tokenに対応する3関数を選ぶ24候補worldを保持した。

同じtokenをstate=0でだけ観測すると constant-1 と negation、constant-0 と identity が観測同値になる。そこでlearnerが候補worldを最も分割するbefore-state付き介入を選び、state-crossing witnessが因果方向と反実仮想を識別するかを監査した。

## Conditions

- Active state-crossing witness
- Random witness
- State-0-only witness
- Outcome shuffle
- 5 witnesses, seed 1/7/19
- final評価はbefore + commandのみ
- final afterはselector、candidate generation、rankingに不使用

## Results

| Metric | Active | Random | State-0 only | Outcome shuffle |
|---|---:|---:|---:|---:|
| surviving program mappings | 1.00 | 3.33 | 5.33 | 0 or inconsistent |
| prospective | 1.0000 | 0.8333 | 0.4444 | 0.0000 |
| inverse | 1.0000 | 0.8333 | 0.4444 | 0.0000 |
| counterfactual repair | 1.0000 | 0.8333 | 0.4444 | 0.0000 |

Active−Randomは+0.1667で、3 seedすべてでActiveはunique mappingへ到達した。

## Integrated judgment

**因果同定可能性の上限仮説は支持された。しかし能力上の正式な進歩、G1、G2は未達。**

今回の重要な識別条件は、同じoperation tokenを異なるbefore-stateで観測することだった。state=0だけの反復観測では、異なる因果programが同じafterを生成し続け、独立witness数を増やしてもoperation identityは一意にならない。

したがってA/Bへ返す条件は次である。

1. operation candidateは局所差分の見た目ではなく、複数初期状態に対する応答関数として提案する。
2. witness generatorはtoken coverageだけでなく、同一tokenのstate crossingを必須化する。
3. `set-to-one` と `toggle`、`noop` と `set-to-zero`を分ける反例を共通benchmarkへ追加する。
4. object permanenceはnon-target stateを保存したままtarget before-stateだけを変えるpaired worldで監査する。

ただし本実験はAの文字role proposal、binary-state interface、unary作用域を利用している。raw自由日本語からoperation family・state variable・作用域が同時創発した証拠ではなく、別domain再生成も未評価である。よって正式分類は `state_crossing_causal_identifiability_upper_bound` とする。

## Next hypothesis

**Scope-and-Arity Birth from State-Crossing and Non-Target Preservation Witnesses**

次はunary作用域を外し、同じraw operation expressionについて、単一target変化、二対象関係変化、non-target保存違反を分離する最小paired interventionを設計する。候補はstate transition tableを先に固定せず、必要な引数数と作用域がwitnessによって分裂した場合だけ生成する。

比較はActive / Random / state-static / arity shuffle / argument-link shuffle / outcome shuffleとし、2 opaque domain、3 seed、未知語順・主語省略・複数段落・自由日本語でprospective、inverse、object permanence、counterfactual repairを測る。

## Resources and status

- candidate worlds: 24
- model upper bound: 576 bytes
- estimated probe evaluations: 2,880
- peak RSS: about 113,000 KiB including Python runtime
- 1GB未満: 達成
- weak smartphone実機: 未検証
- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 完成: 未達
