# Phase 4a results: first compiled ultra-light byte LM

This phase crosses from known-state synthetic processes to an actual byte-level language model.
It is not a Transformer or neural layer stack. Prediction errors propose sparse context rules;
a rule is retained only when held-out NLL reduction pays for its own description length.
The selected rules are compiled into a failure-link state machine with hot fallback transitions.

Training bytes: **625,748**. Test bytes: **155,073**.
The corpus is deterministic and deliberately small, mixing Japanese dialogue, code, logs,
numbers, and key-value sequences. This is a bridge experiment, not a claim about open-domain text.

## Compiled residual LM

- selected predictive rules: **608**
- compiled automaton states: **696**
- runtime state: **10 bits**
- actual serialized model: **10,999 bytes**
- test BPB: **0.468469605**
- average transition checks: **1.015644 per byte**
- save/load round-trip BPB: **0.468469605**

## Fixed-order n-gram baselines

| order | BPB | estimated compact bytes | rules |
|---:|---:|---:|---:|
| 0 | 5.820242117 | 365 | 1 |
| 1 | 2.146307416 | 2,218 | 120 |
| 2 | 1.034265492 | 7,020 | 653 |
| 3 | 0.557296466 | 16,294 | 1,667 |
| 4 | 0.531891477 | 33,383 | 3,370 |
| 6 | 0.605688576 | 131,484 | 12,104 |
| 8 | 0.727351516 | 399,426 | 33,591 |

The sparse compiled model beats the best fixed-order baseline here while being smaller:
order-3 uses about 16.3 KB at 0.557 BPB; order-4 uses about 33.4 KB at 0.532 BPB;
the compiled residual model is 10,999 bytes at 0.468 BPB.

## Generation sample

```text
ユーザー: 山口さん、推論です。次に言語モデルネットについて教えてください。
AI: 数学では、プログラムが小さいほど効率的です。次にプログラムが小さいほど効率的です。次にプログラムが小さいほど効さいほど効ルネット | status=ok
def calc_11(x: int) -> int:
    return x * 9 + 4

AI: 数孁
```

A separate deterministic UTF-8 automaton constrains byte generation. It adds only a tiny
factorized state instead of asking the probabilistic model to relearn byte-validity rules.
The text is locally plausible but still repetitive and semantically weak, as expected from
an 11 KB model trained on a tiny generated corpus.

## Main finding

The useful object is not necessarily a dense hidden vector. It can be a compiled predictive
program: a 10-bit state identifier, sparse output distributions, and almost one transition
lookup per byte. Rare events pay the fallback cost; common events are direct shortcuts selected
by expected compute saving per stored bit.
