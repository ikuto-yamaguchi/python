# B006 — PB1 falsifiability / escalation boundary audit

Date: 2026-07-29
Role: K3-B theory audit
Branch: `research/intelligence-swarm-reconstruction-001`

## Scope

B005でPB1 (`L_sub=24, N=4, S=6`) が一次報告の`N≈8–9` geometryより粗いminimum semantic/effect-direction pilotであることを固定した。本監査では、PB1の結果から何を棄却・採用できるかを、仮定と観測の組として明示する。新しいarchitecture、実装、学習、CPU crossover主張は行わない。

## Estimands

PB1が直接検証できるestimandを次に限定する。

- `E_sem`: paper semanticsを満たす`N=4,S=6` routing graphが実行可能か
- `E_dir`: 同一baseline・同一budgetで、PB1が少なくとも品質指標の方向性改善を示すか
- `E_res`: PB1の追加resource costが事前登録閾値内か

PB1が直接検証できないestimand:

- `E_primary`: 一次報告相当`N≈8–9` geometryでの品質効果
- `E_min`: Block AttnResが有効になるminimum depth / block count / data scale
- `E_cpu*`: fused実装を含む最適CPU Pareto

従って、`E_dir=0`から`E_primary=0`は一般には導けない。

## Assumption comparison

PB1 nullをmechanism-wide nullへ昇格するには、少なくとも次が必要である。

1. **Resolution invariance**: `N=4,S=6`と`N≈8–9`で保持される有用depth feature集合が同一
2. **Optimization invariance**: routing gradient、entropy、source utilizationの収束挙動がgeometryに依存しない
3. **Scale invariance**: 幅、深さ、token budgetを縮小しても効果符号が保存される
4. **Implementation invariance**: unfused小型runtimeと著者のoptimized runtimeで数値・最適化挙動が同等

現時点では4仮定とも未証明である。特にB005のcoarse-resolution counterexampleにより1は自明でない。

## Proposition B006.1 — PB1 null is non-falsifying for the primary geometry

モデル族を`M(N,S,D,W,T)`、品質差を

`Delta(N,S,D,W,T) = quality(AttnRes) - quality(baseline)`

とする。PB1は`Delta(4,6,12,512,T_pb1)`を観測する。

もし`Delta`が`N,S,D,W,T`に関して符号不変である保証が無ければ、

`Delta(4,6,12,512,T_pb1) <= 0`

から

`Delta(8,4,16,W,T) <= 0`

または

`Delta(9,6,27,W,T) <= 0`

は導けない。

従ってPB1の品質nullは、PB1 geometryの棄却候補にはなるが、Block AttnRes全体または一次報告geometryの棄却根拠にはならない。

## Proposition B006.2 — PB1 positive is also non-adoptive

PB1で品質改善があっても、採用には不十分である。

理由:

- `N=4`はdepth resolutionが低く、一次報告geometryを再現しない
- CPU/resource costはsource-slot `89`に対する値であり、higher-`N`へ外挿できない
- 3 seed、same-budget quality、量子化、CPU decode/prefillが未測定

従ってPB1 positiveは`effect-direction positive`までであり、mechanism adoptionや1GB最終設計への採用を意味しない。

## Escalation rule

PB1 semantic PASS後の品質pilot結果を次に分類する。

### Case A — PB1 positive and resource PASS

- 分類: `additional validation`
- 次: 同一baseline depthを維持できる合法geometry内で、事前登録済み`N` ablationを検討
- 禁止: 一次報告再現、CPU Pareto採用、能力進歩の主張

### Case B — PB1 positive but resource WARN

- 分類: `narrow to training-only or fused-kernel-dependent candidate`
- 次: 品質再現前にoperator attributionとfusion feasibilityを評価

### Case C — PB1 null with healthy routing

healthy routing条件:

- semantic PASS
- finite/non-zero routing gradients
- semantic effective source countがcollapseしていない
- entropy/usageが極端にlatest-onlyでない

分類:

- `PB1 inconclusive / possible depth-resolution limit`
- mechanism-wide rejectionは禁止
- higher-`N` escalationは、追加resource予算と別preregistrationが成立する場合だけ許可

### Case D — PB1 null with routing collapse

- 分類: `optimization failure at PB1 scale`
- mechanism-wide rejectionは禁止
- routing初期化やgateを事後追加して救済することは禁止
- 既存公開baselineまたは事前登録済み初期化条件が無ければSTOP

### Case E — semantic STOP

- 現在のPB1 implementation pathをSTOP
- Block AttnRes仮説全体は未判定

## Escalation resource lower bounds

B005のslot式

`C_slots(L,N)=L*(N+3)/2+N+1`

から、一次報告寄りの合法geometryはPB1より高いrouting workを要求する。

- PB1: `L=24,N=4` -> `89 slots`
- `N=8,S=4`: `L=32` -> `185 slots` (`2.079x PB1`)
- `N=9,S=6`: `L=54` -> `334 slots` (`3.753x PB1`)

これはend-to-end FLOPsではなくsource-vector work indicatorである。higher-`N` escalationは、少なくとも約2.08xまたは3.75xのrouting-slot増加を事前に受け入れる別実験であり、PB1と同じCPU cost classではない。

## Counterexample

有用な特徴`z`が各4 sublayersで一時的に生成され、6 sublayers目までに上書きされるとする。

- PB1 `S=6`: `z`はcompleted sourceとして保持されず、`Delta<=0`
- `N=8,S=4`: `z`がblock境界で保持され、`Delta>0`

両者は同じmechanism familyでも結果符号が異なる。この反例は、PB1 nullのmechanism-wide外挿を禁止するのに十分である。

## C handoff

後続preregistrationへ以下を追加する。

```yaml
pb1_estimand: minimum_semantic_and_effect_direction
pb1_null_mechanism_falsifying: false
pb1_positive_adoption_sufficient: false
higher_n_requires_separate_preregistration: true
higher_n_slot_lower_bounds:
  n8_s4_l32: 185
  n9_s6_l54: 334
routing_health_required_for_null_interpretation: true
```

## D handoff

PB1品質pilotへ進む場合、品質値だけでなく次を保存する。

- semantic effective source count
- raw / semantic entropy
- latest-source mass
- per-source utilization
- routing gradient norm
- collapse判定
- `actual_slots / expected_slots`

これらが無ければPB1 nullの原因をresolution不足とoptimization collapseへ分離できない。

## E handoff

- PB1 null: `PB1 inconclusive`を既定とし、mechanism-wide rejection禁止
- PB1 positive: `additional validation`まで。採用禁止
- resource WARN: training-only / fused-kernel-dependentへ狭義化
- semantic STOP: PB1 implementation pathのみSTOP
- higher-`N` escalationは別budget・別preregistration・別Pareto判定を要求

## Decision

PB1は低コストsemantic/effect-direction pilotとして維持するが、正負どちらの結果も単独ではBlock AttnRes全体の採否を決めない。PB1 nullを有効な機構棄却へ昇格するために必要なresolution・optimization・scale・implementation invarianceは未証明である。一次報告寄りgeometryへの移行はrouting-slot指標でPB1の約2.08〜3.75倍を要する別実験であり、暗黙の追加検証として扱ってはならない。