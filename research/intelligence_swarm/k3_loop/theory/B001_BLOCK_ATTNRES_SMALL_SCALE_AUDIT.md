# B001 — Block Attention Residuals の小型化理論監査

Date: 2026-07-28
Role: K3-B
Branch: `research/intelligence-swarm-reconstruction-001`
Status: **追加検証候補（未採用）**

## 0. 今回の選定理由

共有状態ファイルと A/C/D/E 成果は本 run 開始時点で未作成だったため、Kimi K3 の主要構成のうち、既に独立した一次報告・スケーリング比較があり、標準 Transformer に単独 ablation として移植できる **Block Attention Residuals (Block AttnRes)** を最初の候補にした。

Kimi K3 は KDA、AttnRes、Stable LatentMoE を組み合わせるが、MoE は小型 CPU 推論で routing・ランダムアクセス・総重み読み出しが支配的になりやすく、KDA は kernel/状態更新の実装依存性が大きい。一方 Block AttnRes は残差経路だけを変更でき、標準 dense Transformer と同一 parameter/token budget で比較しやすい。

## 1. 一次資料と公開実装の状態

### 一次資料

- Kimi K3 technical report: https://arxiv.org/abs/2607.24653
- Attention Residuals: https://arxiv.org/abs/2603.15031
- Kimi K3 official repository: https://github.com/MoonshotAI/Kimi-K3
- Attention Residuals official repository: https://github.com/MoonshotAI/Attention-Residuals
- official repository pin: `85e22310fe5ee860b4a023de312d791de8a5a5e6`

公式 Attention-Residuals repository は本 run 時点で論文 PDF と説明を公開するが、再現可能な学習コードは含まない。したがって「公式 baseline code」とは扱わない。

### 公開再実装候補（非公式）

- https://github.com/wdlctc/open-attention-residuals

100M / 0.6B の学習スクリプトと checkpoint があるが、著者公式ではない。D は commit、dataset digest、token budget、optimizer、evaluation provenance を固定するまで結果を根拠に採用判定してはならない。

## 2. 比較対象

標準 PreNorm Transformer の sublayer 数を `L`、hidden width を `d`、batch-token 数を `M = B*T` とする。Transformer block ごとに attention と MLP の 2 sublayer がある場合、`L = 2 * n_layers` と数える。

### 標準残差

`h_l = h_{l-1} + f_l(Norm(h_{l-1}))`

残差経路自体の追加 parameter/FLOPs はほぼ 0。保持する主 hidden state は `M*d` 要素。

### Full AttnRes

各 sublayer は embedding と全ての過去 sublayer 出力 `v_i` を深さ方向に softmax 集約する。

`alpha_{i->l} = softmax_i(w_l^T RMSNorm(v_i))`

`h_l = sum_i alpha_{i->l} v_i`

各 sublayer に静的 pseudo-query `w_l in R^d` を持つ。

### Block AttnRes

`L` sublayer を `N` block に分割し、block 内は通常の加算、block 間だけ深さ attention を使う。現在 block の partial sum を含め、最大 `N+1` source を参照する。

## 3. Parameter 数

### 標準 residual

追加 parameter: `0`

### Full / Block AttnRes

parameter-free RMS normalizationを前提にすると、pseudo-query の追加量は概ね

`P_route = L*d`

attention/MLP の両入口に別 query を置く実装表現では、Transformer block 数 `H` に対し

`P_route = 2*H*d = L*d`

で同じである。

例:

- 12 Transformer layers, `L=24`, `d=512`: 12,288 parameters
- 24 Transformer layers, `L=48`, `d=1024`: 49,152 parameters

100M model では約 0.012%、600M model では約 0.008%。parameter overhead は小型でも事実上無視できる。

ただし input-dependent query を `W_q h_l` で作る変種は sublayer ごとに `d^2` を追加し、`L*d^2` となるため小型モデル向け候補から除外する。静的 query のわずかな性能差と引き換えに parameter/FLOP/逐次依存が急増する。

## 4. FLOPs/token

深さ source 1個に対し、query-key dot と weighted value accumulationで約 `4d` FLOPs/token（乗算加算を各2 FLOPsとして概算）。RMS normalization の reduction/scale を含めると実装定数はさらに増えるが、オーダーは同じ。

### Full AttnRes

layer `l` が `l` source を読むため、全深さの追加計算は

`F_full ~= 4d * sum_{l=1}^L l = 2d*L*(L+1)` FLOPs/token

すなわち `O(d L^2)`。

### Block AttnRes（素朴実装）

各 sublayer が平均約 `(N+1)/2` 個の完了 block と partial block を読むと、

`F_block ~= 2d*L*(N+1)` FLOPs/token

すなわち `O(d L N)`。

### 標準 Transformer 本体との比

dense SwiGLU Transformer の1 Transformer layer は概ね `~(8 to 12)d^2` FLOPs/token（sequence attention の `T` 項を除く）。`H=L/2` layers とすれば本体は `O(L d^2)`。したがって Block AttnRes の相対 overhead は概ね

`rho_compute ~= c * N/d`

で、hidden width が小さく、block 数が多いほど不利になる。

重要な帰結:

- 大規模モデルでは `d >> N` のため overhead は小さい。
- 小型モデルでは `d` が 256–768 程度でも `N=4–8` なら算術量はまだ小さい。
- ただし CPU では FLOPs より source tensor の読み出し・stack・softmax kernel 起動が支配し得るため、算術比だけで「<2% latency」を外挿してはいけない。

## 5. 状態・activation memory

### 推論時

標準 residual は現在 hidden state `d` を保持する。Full AttnRes は現在 token の全 sublayer source `L*d`、Block は `N*d + d(partial)` を保持する。

要素数での追加状態:

- Full: `O(Ld)` / token
- Block: `O(Nd)` / token

これは sequence KV cache の `O(T * n_kv_heads * d_head * layers)` とは別の深さ状態である。autoregressive decode では現在 token の block states は一時値なので、正しく fused/streaming 実装すれば context length `T` に比例して永続保持する必要はない。

### 学習時

backprop のため source activation を保持すると、素朴には

- Full: `O(M L d)`
- Block: `O(M N d)` + block 内通常 activation

となる。activation checkpointingを使わない比較では標準 residual より peak memory が増える。公平な測定では同じ checkpoint policy を固定する必要がある。

## 6. 通信・並列性

pipeline parallel では過去 source を stage 間で渡す必要があり、Full AttnRes は深さ source 数に比例して通信が増える。Block AttnRes は block summary に圧縮し、cache-based pipeline communication と two-phase computation を前提に通信を抑える。

小型モデルの単一 CPU / 単一 GPU では分散通信上の利点は無関係であり、逆に two-phase 用の複雑な batching が小さい行列では overhead になり得る。したがって K3 の「実運用で低 overhead」という保証はそのまま小型 CPU へ移らない。

静的 pseudo-query は、同一 block 内の inter-block score をまとめて計算できる。input-dependent query ではこの並列化が崩れ、逐次実行が必要になるため不採用。

## 7. 系列長依存

AttnRes は sequence 軸でなく depth 軸の attention なので、理論上の追加 FLOPs/token は context length に直接依存しない。training batch 全体では当然 `B*T` に比例する。

長文推論における主 memory は依然 KV cache または線形 attention state であり、AttnRes 単独は KV cache を削減しない。したがって「1M context 技術」や「長文メモリ削減」として評価してはならない。

## 8. 量子化適合性

### 重み

pseudo-query は全体のごく小部分なので FP16/BF16 のまま残しても model bytes への影響は無視できる。main weights の INT8/INT4 量子化とは独立に扱える。

### activation / routing logits

routing logit は `w_l^T RMSNorm(v_i)`。source 間の小さな差を softmax で競わせるため、activation と query を低bit化すると routing 順位が反転する可能性がある。特に zero-init 近傍やほぼ一様な routing では量子化誤差の相対影響が大きい。

推奨:

- 初期 baseline は pseudo-query、RMS reduction、softmax を FP32 accumulation。
- weight-only INT8/INT4 と activation quantization を分離して測る。
- quantization 前後で routing KL、top-source agreement、validation loss を記録する。

「parameter overhead が小さい」ことは「量子化に頑健」を意味しない。

## 9. CPU 実装適合性

### 有利な点

- 追加 weight は連続な `L*d` vectorのみ。
- sequence attention のような `T^2` はない。
- `N` を小さく固定できる。
- pseudo-queryを高精度のまま保持しやすい。

### 不利な点

- 各 sublayer で複数の `d` vectorを再読込するため memory bandwidth 増加。
- `stack -> norm -> dot -> softmax -> weighted sum` の小kernel連鎖は CPU で融合しないと遅い。
- source layout が非連続だと cache miss が増える。
- batch=1 decode では GEMM 本体が小さくなるため、固定 overhead の比率が上がる。

したがって CPU 採否は、PyTorch eager の latency ではなく、最低でも contiguous source buffer と fused scalar-routing kernel の両方を測って判断する。ただし D の最初の再現は忠実性を優先し、最適化実装を先に作らない。

## 10. 小型化で効果が消える条件

1. **浅すぎる**: `L` が小さく、標準 residual の深さ希釈がまだ弱い。routing が選ぶ意味のある遠距離 source がない。
2. **block 数が多すぎる**: `N` 増加で memory traffic と softmax overhead が本体計算に対して無視できなくなる。
3. **block 数が少なすぎる**: `N=1` は実質的に通常の block 内加算に近く、深さ選択能力が消える。
4. **学習 token が少なすぎる**: pseudo-query が一様初期値から有意な routing を学ぶ前に終了する。
5. **既学習 standard-residual model への短い後付け**:本体が既存残差経路へ適応済みで、routing 学習だけでは利得が出にくい。
6. **routing source が高相似**: block summaries がほぼ同一方向なら softmax は識別可能な選択信号を得られず、平均化に留まる。
7. **CPU batch=1 で未融合**: loss改善があっても latency/RSS Paretoで敗北する。
8. **低bit activationで routing collapse**: softmax が常に直近または単一 blockを選び、通常 residual より情報経路が脆くなる。

## 11. 最低規模に関する現時点の境界

一次報告は scaling law 実験を activated parameter 約194M–528Mで行い、48B total / 3B active の本学習でも検証している。したがって **194M未満での一次証拠は不足**しており、50M級への有効性は未確立。

理論上は最低 width より **depth と block source diversity** が本質的である。初回検証の下限候補を以下とする。

- dense decoder-only Transformer
- 80M–120M parameters
- 12 Transformer layers (`L=24` sublayers)
- `d=512` 前後
- Block AttnRes `N=4`
- standard PreNorm baseline と同一 tokenizer/data/optimizer/token budget

`L=24, N=4` は1 block当たり6 sublayer（attention+MLP換算で3 layers）となり、複数の過去 blockを選ぶ余地を残しつつ source 数を抑える。これは「効果がある」とする値ではなく、最小識別実験の開始点である。

50M以下は、先に100M級で routing が実際に分化し、compute/latency Paretoが正であることを確認した後に縮小する。

## 12. 反例: parameter がほぼ無料でも総効率は悪化する

幅 `d=256`、浅い `H=6` layers (`L=12`)、`N=4` の非常に小さい modelを考える。pseudo-query parameter は3,072個しかなく無料に近い。しかし各 sublayerで最大5 sourceの読み出し・RMS・softmax・weighted sumが必要になる。

標準 FFN/attention GEMM が小さい batch=1 CPU decode では、この depth-routing kernel がwall timeの無視できない割合を占める。一方、6-layer modelでは深さ希釈そのものが弱く、validation loss改善がほぼ0であり得る。

この場合:

- parameter efficiency: 改善または同等
- FLOPs accounting: 小幅増
- 実測 CPU latency: 大幅悪化
- quality: 同等

となり、最終目標のParetoでは明確に棄却される。よって parameter overheadだけを根拠に小型向けと判定してはならない。

## 13. C への引き渡し: 最小 preregistration 仕様

### 必須 baseline

- 80M–120M dense PreNorm decoder Transformer
- 12 layers, `d≈512`
- standard additive residual

### 単一変更 ablation

- Block AttnRes, `N=4`
- static zero-initialized pseudo-query
- parameter-free RMS normalization for routing keys
- architecture/tokenizer/data/optimizer/schedule/token budgetを完全固定

### 禁止

- KDA、MoE、特殊activation、data curriculumを同時導入しない。
- input-dependent `dxd` queryを使わない。
- unofficial implementationの報告値を再現値として転記しない。

### 追加診断

- block-source cosine similarity
- routing entropy by layer/token
- latest-block mass
- pseudo-query norm
- hidden-state RMS by depth
- gradient norm by depth

## 14. D への測定仮説

### H1 品質

同一parameter/active compute/token budgetで、Block AttnResがstandard residualよりvalidation lossを改善する。

### H2 小型境界

改善幅は浅いmodelで縮小し、12-layerより6-layerで小さい。

### H3 CPU損益

PyTorch eager batch=1では追加latencyが2%を超える可能性が高い。source buffer/fusionなしの結果と最適化後を分離する。

### H4 量子化

weight-only INT4では品質差を保持しやすいが、activation低bit化ではrouting KLと品質が悪化する可能性がある。

### 必須計測

seed `17/29/43`、model bytes、parameter数、peak RSS/VRAM、train wall time、tokens/sec、CPU prefill/decode latency、生成tokens/sec、量子化後size、raw logs、environment/commit/checksum。

## 15. E への採否基準

### 採用候補

3 seed平均で、同一token budgetのvalidation lossが一貫して改善し、かつ以下のいずれかを満たす。

- 同一loss到達までのtraining computeを10%以上削減
- CPU decode latency悪化3%以下、peak RSS悪化5%以下
- 量子化後も改善の70%以上を保持

### 追加検証

品質改善はあるがCPU latency悪化3–10%、またはseed varianceが大きい。

### 狭義化

12+ layersでのみ有効、6 layers/50M級では無効、あるいはtraining効率だけ改善しdeployment効率は悪化。

### 棄却

- 3 seedで平均改善なし
- latency 10%以上悪化し、同一loss compute削減で相殺できない
- routing collapseまたは量子化で改善消失
- source diversityがなく一様平均から有意に離れない

## 16. 判定

**Block AttnRes は「規模非依存候補」ではあるが、最小資源モデルへの採用は未判定。**

parameter overheadと系列長依存は小さい。一方、小型CPUではmemory traffic/kernel overheadが相対的に増え、一次証拠の下限も約194M activeである。現時点の正当な次手は100M級の忠実baseline再現と単一ablationであり、新規architectureへの統合ではない。
