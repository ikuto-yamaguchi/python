# B003 — Block AttnRes D002系列長スケーリング・損益分岐監査

Date: 2026-07-28
Role: K3-B
Branch: `research/intelligence-swarm-reconstruction-001`
Status: **D003前の反証可能な理論更新（小型化で要再設計・追加検証・未採用）**

## 0. 今回の選定理由

共有状態ではBlock AttnRes以外のK3技術は凍結され、唯一のボトルネックはD003 exact-dependency fresh-process preflightである。B002はCPU rooflineとoperator trace契約を定義したが、D002で得られた系列長別routing microbenchmarkをまだ理論へ反映していなかった。

本runではD002の実測値から、短系列での近似線形領域と2048 tokenでのbreakpointを定量化し、D003が検証すべき仮説、Cがmanifestへ追加すべき閾値、Eが採否に使う条件を固定する。新規architecture、学習、品質利得、CPU crossoverの断定は行わない。

## 1. 固定観測

D002 standalone harness、CPU 1 thread、FP32、hidden width `d=512`、source数 `S=5` のrouting単体中央値:

| sequence length | median routing time |
|---:|---:|
| 1 | 0.112487 ms |
| 128 | 0.627961 ms |
| 512 | 2.252197 ms |
| 2048 | 35.944465 ms |

D002はexact third-party runtimeではなく、full-model timingと条件別RSSも未分離である。このため以下はrouting kernel pathの診断であり、end-to-end推論性能の証拠ではない。

## 2. 短系列線形モデル

`T={1,128,512}` の3点に最小二乗で、

`t_route(T) = a + bT`

を当てると、

- 固定項 `a ≈ 0.100753 ms/event`
- token係数 `b ≈ 0.004197 ms/token/event`

となる。

このモデルによる2048 token予測は、

`t_hat(2048) ≈ 8.696 ms/event`

であるのに対し、実測は、

`t_actual(2048) = 35.944 ms/event`

であり、

- 予測比 `actual/predicted ≈ 4.13x`
- 超過時間 `≈27.25 ms/event`

である。

したがって、D002の2048点は単純なtoken線形延長では説明できない。

## 3. 解釈可能な候補原因

現時点で原因を1つに断定しない。D003では少なくとも次を区別する。

1. **stack/materialization breakpoint**
   - `S*T*d` のtemporaryがcache階層を越え、copy/readbackが急増する。
2. **allocatorまたはpage-fault effect**
   - 長系列だけ新規temporary allocation、zeroing、page commitが支配する。
3. **einsum/kernel selection change**
   - shape thresholdで異なるbackend pathへ切り替わる。
4. **softmax reduction/layout effect**
   - contiguous化またはsource/token軸のstrideが長系列で不利になる。
5. **measurement artifact**
   - warmup不足、GC、CPU frequency、同一process high-water effects。

D002だけではこれらを識別できない。

## 4. CPU実装適合性の更新

### 4.1 decode

`T=1`でrouting eventあたり約0.112 msの固定費が観測された。Block AttnResでは複数sublayer/routerが存在するため、batch=1 decodeでは小kernel dispatchの累積が無視できない可能性がある。

ただし、実際のevent数・source数・full-model baseline時間がD003で分離されるまで、decode overhead率は算出しない。

### 4.2 prefill

`T=2048`で短系列線形モデルの約4.13倍へ逸脱した。これはcontext lengthを長くしたとき、depth-routing自体の理論FLOPsが線形でも、eager CPU実装のmemory/layout costが非線形化し得る反例である。

従って、

> depth attentionはsequence attentionではないためcontext lengthに対して安価

という一般化は、小型CPUの実装経路については成立未確認とする。

## 5. parameter・state・通信との比較

B0/A1の正しいparameter contract:

- B0: `115,554,304`
- A1: `115,579,929`
- delta: `25,625` (`0.02218%`)

静的parameter、active parameter、model bytes増分は極小である。一方、D002のbreakpointは静的parameterでは説明できず、activation temporaryとoperator pathが主要リスクである。

Block AttnResはKV cacheを直接増加させないが、block source activationを保持・収集するため、training activation memoryおよびprefill中のtemporary trafficは別途増える。分散学習ではparameter通信増分は小さい一方、実装がsource tensorのsharding/collectiveを必要とすればactivation communicationが発生し得る。C001/D003は単一CPU preflightなので通信利得はまだ評価対象外とする。

## 6. 量子化適合性

routing scoreは小さなpseudo-query dot productとsoftmaxで決まり、weight-only INT8/INT4で本体weightを圧縮しても、activation routing経路のmemory trafficとdispatchは残る。

また、routing logitsのmarginが小さい場合、query/normの低bit量子化誤差でsource順位やmassが変化し得る。したがって量子化後サイズが小さくてもCPU Paretoが改善するとは限らない。

D003では量子化を開始しない。将来の量子化gateでは最低限、routing distribution KL、top-source agreement、entropy、quality、decode latencyを同時に測る。

## 7. D003へ渡す反証可能な仮説

### H1 — 短系列線形性

exact dependency・fresh processでも、`T<=512`のrouting時間は `a+bT` で概ね説明できる。

反証条件:

- order-balanced repeatで係数変動が大きい
- 512以下でも明確な非線形breakpointが再現する

### H2 — 2048 breakpointのoperator帰属

2048点の超過時間の50%以上が、`stack/layout + framework/allocator`へ帰属する。

反証条件:

- norm/score、softmax、mixの算術kernelが主因
- fresh process/order balance後にbreakpointが消える

### H3 — temporary threshold

breakpointはtemporary bytesまたはcache/page thresholdと共変する。

D003は各caseで少なくとも次を保存する。

- source stack bytes
- normalized temporary bytes
- score bytes
- output bytes
- allocation count
- peak RSS
- operator call count

### H4 — end-to-end penalty

routing単体のbreakpointが存在しても、full-model GEMM時間に隠れてA1/B0 overheadが10%未満となる可能性がある。

このためrouting単体だけでWARNを確定せず、fresh-process full-model timingを必須とする。

## 8. Cへの最小仕様修正

C001 amendmentへ次を追加する。

1. CPU casesを `T=1,128,512,2048` に固定。
2. 各caseを別fresh processで測定。
3. B0/A1 orderをAB/BAで均衡化。
4. warmup回数、測定反復、median、p95、MADを保存。
5. 短系列線形fit `a,b,R²` と2048予測残差を機械可読保存。
6. `actual_2048 / predicted_2048` をbreakpoint ratioとして保存。
7. operator shareは個別計測の単純和だけでなくprofiler self CPU timeも併記。
8. save/load tolerance、parameter/config diff、input SHA256を維持。
9. S1学習は許可しない。

## 9. Eへの採否基準更新

D003実装経路の分類:

### Path-PASS

- exact runtimeとresidual-only差分が成立
- order-balanced timingが再現
- 2048 breakpointが消える、または原因とcostが説明可能
- A1/B0 full-model overheadが10%未満
- 条件別RSS/temporaryが説明可能

### Path-WARN

次のいずれか:

- A1/B0 full-model CPU時間またはRSSが10%以上悪化
- `stack/layout + framework/allocator`が追加routing時間の50%以上
- `actual_2048/predicted_2048 >= 2.0` がfresh-processでも再現
- breakpoint原因がeager実装に固有で、fusionなしでは解消不能

この場合、Block AttnResを品質仮説として棄却せず、**training-only候補またはfused-kernel依存候補**へ狭義化する。

### Path-STOP

- exact candidateが1回の最小compatibility patch後も動かない
- residual以外のsemantic差分が必要
- gradient/save-load gate失敗
- order-balanced timing/RSS/operator attributionを取得不能

## 10. 小型化で効果が消える条件

少なくとも次では、小型モデルへの転用価値が消える可能性が高い。

- 浅いモデルでresidual dilution自体が弱く、品質利得がない
- routing固定費がmain GEMMに対して大きい
- context 2048でlayout/temporary breakpointが継続する
- training gainが10%未満なのにCPU decode/prefillが10%以上悪化する
- fusion実装が弱いCPU/モバイルbackendで利用できない
- INT4化してもactivation routing costが残り、model bytes以外のParetoが改善しない

最低必要幅・深さ・データ量は、一次証拠の最小が約194M active、12 blocks、幅896、38.7B tokensであり、C001の115.6M・幅512・20k stepsへ直接外挿できない。D003は実装経路のみを判定し、最低規模や品質損益分岐はS1〜S3前に主張しない。

## 11. 今回の反例

追加parameterが0.02218%で、routing FLOPsが理論上token線形でも、2048 tokenのeager CPU routingが短系列fit予測の約4.13倍になる場合がある。

したがって、

> parameter overheadが小さい、KV cacheを増やさない、漸近FLOPsが線形

という3点だけでは、最小資源CPUで軽量とは判断できない。

## 12. 結論

Block AttnResの分類を維持する。

> **小型化で要再設計・追加検証・未採用**

D002は実行可能性を示したが、系列長2048で明確なbreakpoint候補を示した。次の単一ボトルネックは変わらずD003であり、exact dependency、fresh process、order balance、operator attributionによって、この非線形化が実装artifactか構造的deployment penaltyかを判定する。

新規architecture、KDA、Stable LatentMoE、S1/S2/S3、品質・知能進歩の主張は引き続き禁止する。
