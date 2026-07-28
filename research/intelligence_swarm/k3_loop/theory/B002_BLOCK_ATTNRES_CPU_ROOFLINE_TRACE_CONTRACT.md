# B002 — Block AttnRes 小型CPU roofline・trace契約

Date: 2026-07-28
Role: K3-B
Branch: `research/intelligence-swarm-reconstruction-001`
Status: **D002実測待ちの理論契約（追加検証・未採用）**

## 0. 今回の選定理由

共有状態では、Block AttnRes の品質検証へ進む前に、独立した D002 executable preflight が唯一のボトルネックとして固定されている。B001 は parameter/FLOPs/state-memory のオーダー比較を完了したが、100M級・batch=1 CPUで支配項となり得る activation read、`stack/einsum/softmax`、allocator/framework overhead を切り分けるための実測契約が未定義だった。

本runでは新しいK3 componentや新規architectureを開かず、D002が取得すべきtrace fields、理論式、損益判定手順を固定する。実測前に crossover point やCPU有利性を主張しない。

## 1. 固定対象

C001/D001の条件を変更しない。

- B0: 12-layer Qwen3-style dense PreNorm baseline
- A1: B0 + Block AttnRes `N=4` only
- hidden width `d=512`
- 12 Transformer layers / 24 sublayers
- sequence length `T=2048`
- B0 parameters: source-derived `115,554,304`
- A1 parameters: source-derived `115,578,904`
- additional parameters: `24,600` (`~0.0213%`)

B002は学習を許可せず、fixed synthetic inputでのpreflightとCPU microtraceだけを対象にする。

## 2. 問題設定

小型CPU推論での追加時間を、次の5成分へ分解する。

`Δt_total = t_layout + t_norm_score + t_softmax + t_mix + t_framework`

- `t_layout`: source tensorの収集、stack/copy/contiguous化
- `t_norm_score`: RMS normalizationとpseudo-query dot product
- `t_softmax`: source軸softmax
- `t_mix`: weighted source accumulation
- `t_framework`: Python dispatch、operator launch、allocator、autograd bookkeeping等

parameter overheadは静的weight bytesへしか直接効かない。CPU採否は主に上記のactivation経路で決まる。

## 3. 理論下限: 必須activation traffic

各routing eventで、source数を `S`、token数を `M=B*T`、要素bytesを `b` とする。

最低限、次が必要になる。

1. source read: `M*S*d*b`
2. mixed output write: `M*d*b`
3. routing score read/write: 少なくとも `O(M*S*b_score)`

コピーを伴わず、sourceを1回だけ読み、mixを1回だけ書く理想下限は、

`Bytes_min_event ≈ M*d*b*(S+1)`

である。

実装が `stack` で新しいcontiguous bufferを作る場合は、sourceを読み出してstack bufferへ書き、そのbufferを後続演算で再読込するため、概算下限は、

`Bytes_stack_event ≳ M*d*b*(3S+1)`

まで増える。

内訳:

- original source read: `S`
- stack buffer write: `S`
- stack buffer reread: `S`
- mixed output write: `1`

RMS reduction、normalized temporary、autograd保存がmaterializeされる場合はさらに増える。

## 4. C001での数値化

`d=512`, BF16 `b=2`, `N=4` で、source数が `S=5` に達するrouting eventを考える。

### batch=1 decode, 1 token

- ideal minimum: `512*2*(5+1) = 6,144 bytes/event`
- stack lower bound: `512*2*(3*5+1) = 16,384 bytes/event`

24 sublayerすべてで同程度のeventが発生する上限寄り概算:

- ideal: `147,456 bytes/token`
- stack path: `393,216 bytes/token`

これはKV cache trafficやmain GEMM weight trafficとは別の追加分である。実際のsource数は深さにより変わるため、D002は各eventの `S` を記録し、固定 `S=5` と仮定してはならない。

### prefill, `T=2048`, batch=1

上記をtoken線形に拡張した単純概算:

- ideal upper-style estimate: 約 `288 MiB/sequence`
- stack-path upper-style estimate: 約 `768 MiB/sequence`

これはpeak resident memoryではなく、routing経路が処理中に発生させ得る累積read/write trafficの概算である。temporaryが再利用されればpeak RSSは小さくてもwall timeは増え得る。

## 5. 算術強度

B001の近似に従い、1 sourceあたりscoreとmixを合わせたrouting計算を概ね `4d FLOPs/token` とする。

routing eventの概算FLOPs:

`F_event ≈ 4*M*S*d`

理想trafficに対する算術強度は、

`AI_ideal ≈ 4S / (b*(S+1)) FLOPs/byte`

BF16 `b=2`, `S=5` では、

`AI_ideal ≈ 1.67 FLOPs/byte`

stack lower boundでは、

`AI_stack ≲ 4S / (b*(3S+1)) ≈ 0.625 FLOPs/byte`

となる。一般的なCPUではこの程度の小kernelはmemory/dispatch boundになりやすい。ただし、CPU固有のbandwidth、vectorization、fusionが未測定なので、B002は「支配的である」と断定せず、D002 traceで検証する。

## 6. D002必須trace fields

DはB0/A1について、同一process・同一thread設定・同一inputで以下を保存する。

### 6.1 環境

- CPU model、physical/logical core数
- OS/kernel
- Python/PyTorch/Transformers versions
- BLAS/OpenMP backend
- `torch.get_num_threads()` / interop threads
- dtype、autocast設定
- deterministic設定
- compiler/eager状態

### 6.2 入力・形状

- batch、sequence length
- input SHA256
- 各routing eventの `M,d,S`
- source tensor shape/stride/contiguity
- output shape/stride/contiguity
- parameter dtype、activation dtype、score accumulation dtype

### 6.3 operator別時間

最低限、warmup後のmedian/p95を別々に取る。

- source collect/stack
- RMS normalization
- score dot/einsum
- softmax
- weighted sum/einsum
- complete routing event
- full B0/A1 forward
- full B0/A1 forward+backward

可能ならPyTorch profilerのoperator名、self CPU time、CPU total time、call count、input shapesを保存する。

### 6.4 memory

- process peak RSS
- routing前後RSS delta
- profilerのallocation bytes（取得可能なら）
- temporary tensorごとのnumel/dtype/bytes
- saved tensors for backwardの総bytes（取得可能なら）

### 6.5 framework overhead control

同じshapeで次のcontrolを測る。

- no-op Python function
- source list traversalのみ
- `torch.stack`のみ
- norm+scoreのみ
- softmaxのみ
- weighted sumのみ
- fusedではない完全routing

これにより、演算量ではなくoperator分割やdispatchが支配しているかを判定する。

## 7. 導出する指標

D002のraw traceからBまたはEが以下を計算する。

### 7.1 実効追加時間

`Δt_forward = t_A1_forward - t_B0_forward`

`Overhead_forward = Δt_forward / t_B0_forward`

backwardも同様に別計算する。

### 7.2 実効bandwidth下限

`BW_effective_lower = Bytes_min / t_routing`

stack pathが確認された場合は、

`BW_stack_lower = Bytes_stack_lower / t_routing`

も併記する。これらは完全なhardware bandwidthではなく、理論下限trafficに基づく診断値である。

### 7.3 overhead attribution

`Share_x = t_x / t_routing_total`

- layout share
- norm/score share
- softmax share
- mix share
- unattributed/framework share

unattributedは、完全routing時間から個別operator時間の和を引いた値として扱うが、非加法性とcache効果を注記する。

### 7.4 memory amplification

`Amp_RSS = peak_RSS_A1 / peak_RSS_B0`

`Temp_bytes_per_token = measured_temporary_bytes / M`

## 8. CPU roofline判定

D002時点では品質改善が未測定なので、採用判定はしない。実行経路の分類だけを行う。

### Path-PASS

以下をすべて満たす。

- residual-only contractを維持
- routing gradient/save-load gateを満たす
- operator別traceが取得可能
- full forward overheadの再現性がある
- RSS/temporary増分が説明可能

### Path-WARN

実行可能だが、次のいずれか。

- `stack/layout + framework` がrouting時間の50%以上
- A1 forward overheadが10%以上
- temporary/RSS増加がB0比10%以上
- dtype/layoutが想定外に変換される

WARNは仮説棄却ではない。S1前に「忠実eager baseline」として測る価値があるかをEが判断する。

### Path-STOP候補

- residual以外のmodel semantics変更が必要
- trace取得のためarchitectureを変更する必要がある
- routing parameter gradientまたはsave-load gateに失敗
- B0/A1のinput/dtype/kernel条件を揃えられない

## 9. 損益分岐の定義

品質利得が後のS2/S3で得られた場合のみ、次を評価する。

`NetValue = QualityComputeGain - DeploymentPenalty`

具体的には、同一validation loss到達までの学習時間削減率を `G_train`、CPU decode悪化率を `P_decode`、RSS悪化率を `P_rss` とし、単一の恣意的重み付きscoreへ潰さずParetoで判定する。

最低条件:

- `G_train >= 10%`、または
- CPU decode悪化 `<=3%` かつRSS悪化 `<=5%`

D002だけでは `G_train` が存在しないため、parameter/FLOPsの理論値から採用へ昇格させてはならない。

## 10. 反例・失敗条件

### 反例: profiler上のFLOPsは小さいが、CPU wall timeが悪化

`torch.stack` がsource tensorを毎eventでmaterializeし、RMSNorm、einsum、softmax、einsumが別operatorとして実行される場合、追加FLOPsはmain modelの1%未満でも、batch=1 decodeではoperator dispatchとmemory copyがmain GEMM間の隙間を埋める。

このとき、

- parameter overhead: `0.0213%`
- routing arithmetic: 小さい
- temporary traffic: 数百KiB/token規模になり得る
- wall-time overhead: 10%以上
- quality evidence: まだ無し

となり、最小資源モデルのPareto上は不利である。これは「AttnResが無効」の証拠ではなく、「未融合eager実装をそのままdeployment技術と見なせない」ことの反例である。

## 11. Cへの引き渡し

C001のモデル・optimizer・token budgetは変更しない。追加すべきなのはD002/S0計測契約のみ。

- fixed batch/sequence input cases: `(1,1)`, `(1,128)`, `(1,512)`, `(1,2048)`
- warmup回数と測定反復数を固定
- thread数を固定
- save-load toleranceを宣言
- profiler export形式を宣言
- PASS/WARN/STOP schemaへoperator attribution fieldsを追加

新しいfusion kernelやcontiguous layout最適化は、忠実eager trace取得前には実装しない。

## 12. Dへの測定仮説

- H-D002-1: 24,600 parameterの追加よりactivation layout/trafficがCPU overheadを支配する。
- H-D002-2: `stack/layout + framework` shareはrouting totalの50%以上になり得る。
- H-D002-3: prefill overheadはtoken数にほぼ線形、decodeは固定operator overhead比率が高い。
- H-D002-4: peak RSSより累積traffic/wall timeが先に悪化する可能性がある。

これらは検証仮説であり、D002 trace前には成立を主張しない。

## 13. Eへの採否基準

D002レビューではBlock AttnRes自体を採否しない。実装経路を次に分類する。

- **追加検証**: Path-PASS。Cが実行契約を修正し、immutable-data S1準備へ進める。
- **狭義化**: 実行可能だがPath-WARN。training-only効率候補またはfusion前提候補として扱う。
- **棄却（implementation path only）**: Path-STOP。

品質、量子化耐性、3-seed安定性が無いため「採用」は選択不可。

## 14. 判定

B002は、Block AttnResの小型CPU適合性を判断するための計算量・memory-traffic・trace契約を完成した。

現時点の分類は引き続き、

> **小型化で要再設計 / 追加検証・未採用**

である。次の単一ボトルネックは変わらずD002 executable preflightであり、D002 traceが得られるまでcrossover point、CPU有利性、品質改善を主張しない。
