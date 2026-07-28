# B005 — Block AttnRes block-count cost / depth-resolution audit

Date: 2026-07-29
Role: K3-B theory audit
Branch: `research/intelligence-swarm-reconstruction-001`

## Scope

A004で固定した12 Transformer blocks / 24 Attention・MLP sublayersについて、Block AttnResのcompleted block数`N`とblock size`S=L/N`が、depth resolution、routing計算量、activation traffic、CPU適合性へ与える影響を監査する。実装・学習・能力主張は行わない。

## Fixed geometry

PB1は次で固定されている。

- `L=24` sublayers
- `N=4` completed blocks
- `S=6` sublayers/block
- boundaries after Transformer blocks `[3,6,9,12]`
- embeddingは独立source
- final routerはcompleted blockを増やさない

## Source-slot cost model

1-based sublayer `l`の前に完成済みblock数を

`k_l = floor((l-1)/S)`

とする。重複sourceのないcanonical経路で、routing eventが読むsource数の上限を

`R_l = 2 + k_l`

と置く。2はembeddingとcurrent partialである。実装が一部eventでcurrent partialを使わない場合、Dは実測source数を記録し、式を無理に適用しない。

`L=N*S`なら、全sublayer routingで処理するsource-vector slot上限は

`sum R_l = 2L + S*N*(N-1)/2 = L*(N+3)/2`

となる。final routerはembeddingと`N` completed blocksを読むため`N+1` slots。従ってforward全体のgeometry indicatorは

`C_slots(L,N) = L*(N+3)/2 + N + 1`

である。parameter数は現在のper-sublayer query/norm設計ではほぼ`N`非依存だが、activation read、temporary、softmax幅、dispatchは`N`とともに増える。

## PB1 cost

`L=24,N=4,S=6`では、

- sublayer routing slots: `84`
- final router slots: `5`
- total: `89`

幅`d=512`なら、score passとweighted-value passだけでも少なくとも

`2*89*512 = 91,136`

scalar contributions/tokenを処理する。RMSNorm、softmax、stack/layout、allocator、framework dispatchは含まない。これはend-to-end FLOPsではなく、Dがtraceから検証するgeometry-normalized work indicatorである。

## Fixed-depth comparison

`L=24`で合法なeven-`S` geometryを比較する。

| N | S | Transformer blocks/block | total slots | vs N=4 |
|---:|---:|---:|---:|---:|
| 1 | 24 | 12 | 50 | 0.562x |
| 2 | 12 | 6 | 63 | 0.708x |
| 3 | 8 | 4 | 76 | 0.854x |
| 4 | 6 | 3 | 89 | 1.000x |
| 6 | 4 | 2 | 115 | 1.292x |
| 12 | 2 | 1 | 193 | 2.169x |

`N=8,S=3`や`N=24,S=1`は数学上は定義できても、公開pseudocodeの`S//2` adapterではodd `S`が切り捨てられるためPB1経路では拒否する。

## Primary-evidence boundary

一次報告はscaling実験で概ね8 blocks、54-sublayer Kimi Linear実験で9 completed blocksを用いる。PB1の`N=4`はそのgeometryより粗い。従ってPB1はpaper-reported efficacy reproductionではなく、低コストなsemantic / effect-direction pilotである。

禁止する解釈:

- `N=4`のnull結果から`N≈8–9`のmechanism全体を棄却する
- `N=4`の正結果から`N≈8–9`のCPU Paretoを推定する

`N=8`をeven `S=4`で再現するには少なくとも`L=32`、16 Transformer blocksが必要でbaseline depthも変わる。`N=9,S=6`には`L=54`、27 Transformer blocksが必要でPB1とは別preregistrationになる。

## Failure condition 1: resolution too coarse

有用な中間表現が6 sublayers内で生成後に上書きされ、completed block aggregateへ線形に保持されなければ、PB1はその表現を独立sourceとして選べない。この場合、semantic trace、gradient、parameter overheadが正常でも品質改善は消える。これは実装失敗ではなく`S=6`のdepth-resolution不足である。

## Failure condition 2: runtime crossover

depth resolutionを上げるため`N=4`から`N=12`へ増やすと、main Transformer parametersやKV cacheを変えずにsource-slot indicatorは`89→193`、2.169倍になる。unfused CPUではsource reads、stack/layout temporary、softmax、operator dispatchが増え、品質が改善してもParetoから外れる可能性がある。

従ってparameter overhead約0.022%やKV非増加だけで軽量性を認定しない。

## Quantization

weight-only INT8/INT4でもretained activations、RMSNorm、softmax、weighted mixは同率には縮まらない。将来の評価では同じ`N`で、source数、top1-top2 margin、raw-index agreement、checksum-collapsed semantic agreement、entropy、effective source count、品質、latencyを測る。単一sourceへcollapseしたroutingは高`N`の有効性を示さない。

## C handoff

次のPB1 amendmentへ以下を追加する。

```yaml
L_sub: 24
N_completed_blocks: 4
S_sublayers_per_block: 6
legal_even_S_required: true
expected_sublayer_source_slot_upper_bound: 84
expected_final_router_source_count: 5
expected_total_source_slot_upper_bound: 89
primary_evidence_geometry_matched: false
experiment_role: minimum_semantic_and_effect_direction_pilot
```

`N` ablationは別preregistrationとし、`N`とbaseline depthを同時変更する場合はestimand変更を明示する。

## D handoff

環境gateとvariant authorization後、traceから次を計算する。

1. eventごとのactual source count
2. sublayer event全体のsource slots
3. final-router source count
4. actual/expected slot ratio
5. duplicate-collapsed source slots
6. source-count別operator latencyとtemporary bytes

PB1 STOP条件:

- unexplained slot countが登録上限を超える
- final router source countが5以外
- `N`または`S`が黙って変わる
- odd/truncated `S`
- unintended duplicateによりraw/collapsed slot totalが異なる

## E handoff

分類は維持する。

`小型化で要再設計・追加検証・未採用 / Path-WARN`

- semantic PASSはminimum effective scaleを示さない
- `N=4` quality nullは`N=4 inconclusive / depth-resolution-limited candidate`
- higher-`N`で品質改善してもresource Pareto超過ならtraining-onlyまたはfused-kernel依存へ狭義化
- 採用にはsame-budget quality、CPU latency/RSS、3 seedが必要

## Decision

PB1 `N=4`は現在の最低コストpreregistered paper-semantics pilotとして維持する。ただし一次証拠geometryより粗く、効果が成立するminimum scaleは未証明である。固定depthでは`N`増加によりdepth resolutionが上がる一方、source-vector workは概ね`N`に比例して増え、小型unfused CPUで支配的になり得る。