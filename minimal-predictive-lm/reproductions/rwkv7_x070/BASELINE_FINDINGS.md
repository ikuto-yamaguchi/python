# RWKV-7 matched-baseline reproduction

## Purpose

PR #129 reproduced the RWKV-7 x070 recurrent update and confirmed constant recurrent-state size, but answer accuracy stayed near chance. This follow-up adds parameter-matched GRU and small causal Transformer baselines under the same data, seeds, loss, optimizer, and evaluation splits.

## Conditions

- training examples: 128 / 512 / 1024
- seeds: 1 / 7 / 19
- epochs: 2
- independent held-out episodes
- overwrite stress depth: 16
- chance answer accuracy: 1/6 = 0.1667
- no task-specific branch, retrieval, external model, answer candidate list, or label side channel

## Local results

Three-seed means:

| architecture | examples | answer accuracy | overwrite stress | validation NLL | parameters | model bytes | state bytes at context 64 | token latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| GRU | 128 | 0.1172 | 0.1406 | 7.2723 | 3,160 | 15,697 | 80 | 0.058 ms |
| GRU | 512 | 0.1823 | 0.1615 | 3.1974 | 3,160 | 15,697 | 80 | 0.061 ms |
| GRU | 1024 | 0.1693 | 0.1771 | 1.6987 | 3,160 | 15,697 | 80 | 0.057 ms |
| Transformer | 128 | 0.0365 | 0.0000 | 9.7935 | 4,784 | 24,947 | 8,192 | 0.30 ms |
| Transformer | 512 | 0.1484 | 0.1354 | 5.7321 | 4,784 | 24,947 | 8,192 | 0.31 ms |
| Transformer | 1024 | 0.1536 | 0.1693 | 3.2781 | 4,784 | 24,947 | 8,192 | 0.35 ms |

PR #129 RWKV-7 at 1024 examples was 0.1484 answer accuracy, 0.1823 stress accuracy, and 1.5772 validation NLL with 3,888 parameters.

## Falsification result

All three architectures stay around chance and none shows monotonic ability scaling. RWKV-7 has lower validation NLL than the two baselines at 1024 examples, but this does not translate into reliable state-tracking accuracy. Therefore the experiment does not support an RWKV-specific intelligence advantage.

The only robust difference is execution structure:

- GRU and RWKV retain fixed-size recurrent state.
- The Transformer's cache/state accounting grows linearly with context.
- The tiny GRU is fastest in this Python/PyTorch CPU run.
- PyTorch process RSS is dominated by the framework and is not a weak-phone measurement.

## Completion boundary

- high-school-level Japanese intelligence: false
- native Japanese communication: false
- free dialogue / instruction following / reading / reasoning / planning / causal counterfactuals / free writing / long dialogue / continual learning: not established
- below 1 GB model files: true for these toy models
- weak-smartphone deployment: not established
- completion: false

## Next bottleneck

The current benchmark is too weak and too undertrained to distinguish useful memory algorithms. The next reproduction must use official-checkpoint logit parity or an official training configuration, then evaluate associative recall, multi-query recall, overwrite, and length extrapolation with enough optimization steps for at least one baseline to rise substantially above chance. Until that sanity condition is met, architecture comparisons are not evidence about general intelligence.