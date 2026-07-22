# Cycle 014 最終決定論的測定値

初回測定後、観測noiseの適用scopeとPythonのランダム化`hash()`依存を監査し、noiseを1例につき1回だけ適用し、`blake2b`による決定論的hashへ置換して全条件を再測定しました。本ファイルと`results_cycle_014.json`の値を最終値とします。

| 条件 | Global | Wrong routing | Bipartite |
|---|---:|---:|---:|
| seen | 0.8269 | 0.0000 | **0.9778** |
| nested proxy | 0.7222 | 0.1074 | **0.9500** |
| plan-change proxy | 0.8019 | 0.0000 | **0.9787** |
| long distractor | 0.8148 | 0.0000 | **0.9796** |
| unmarked Japanese | 0.0000 | 0.0000 | 0.0000 |

- Bipartite seen wrong commit: 0.0093
- Bipartite seen flat rate: 0.0130
- Bipartite mean sweeps: 2.0
- Bipartite convergence: 1.0
- Bipartite model: 384 bytes
- Bipartite seen latency: 0.2274 ms/example
- Peak RSS: 112,036 KiB（Python runtime込み）
- unmarked candidate recall: 0
- unmarked Bipartite null rate: 1.0

判定は変わりません。局所cause-edge routingは制御候補graphで限定支持されますが、routing mapと引用付き候補は実験側供給であり、自由日本語の構造創発は反証です。
