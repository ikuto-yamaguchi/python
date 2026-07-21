# Sequence architecture map: reproduction before invention

This reproduction stage widens the research program beyond one recurrent mechanism. It does **not** claim that a 10k-parameter diagnostic model is a Japanese general intelligence model.

## Why this stage exists

PR #116 through PR #128 repeatedly narrowed into local symbolic or string-processing mechanisms. PR #129 restarted from a published architecture and reproduced the RWKV-7 x070 recurrence, but one architecture and one state-tracking task are still too narrow.

The new program separates four axes that must not be conflated:

1. **Sequence architecture**: softmax attention, classical gated recurrence, state-space models, RWKV, delta-rule linear attention.
2. **Learning rule and optimizer**: AdamW, Muon, delta updates, meta-learning, and test-time training.
3. **Language/data scale**: synthetic mechanism probes first, then real Japanese pretraining with matched tokens.
4. **Deployment**: serialized weights, explicit recurrent state, clean native RSS, latency, energy, and actual weak-phone measurements.

## Primary research map

| Family | Primary reference | What must be reproduced before use |
|---|---|---|
| RWKV-7 | arXiv:2503.14456 | Official recurrence/logit parity, state tracking, multilingual scaling |
| Mamba-2 / SSD | arXiv:2405.21060 | Selective SSM behavior, recurrent/parallel equivalence, throughput |
| Kimi Delta Attention | arXiv:2510.26692 | Channel-wise decay, retrieval behavior, hybrid-vs-pure trade-off |
| Gated DeltaNet-2 | arXiv:2605.22791 | Separate erase/write gates and long-context retrieval |
| xLSTM | arXiv:2405.04517 | Exponential gates and scalar/matrix-memory baselines |
| TTT-E2E | arXiv:2512.23675 | Test-time adaptation and context-length scaling |
| Self-Guided TTT | arXiv:2607.09415 | Evidence selection before adaptation; random-span negative control |
| MobileLLM | arXiv:2402.14905 | Sub-billion mobile baseline and depth/width trade-off |

TTT is deliberately not mixed into the first architecture sweep: it changes the **inference-time learning process**, not only the recurrent layer. It requires a separate matched experiment.

## Implemented matched-budget sweep

Five models share the same vocabulary, autoregressive next-token objective, training examples, answer loss, seeds, and evaluation episodes:

- GRU
- selective diagonal SSM mechanism probe
- gated DeltaNet mechanism probe
- RWKV-7 x070 mechanism probe
- one-layer causal Transformer

The suite mixes four abilities in one model:

- key-value overwrite and retrieval
- multiple queries in one sequence
- modular arithmetic state updates
- parity/regular-state tracking

Validation uses independent episodes. A stress split triples the update/noise depth. This is still a diagnostic suite, not free Japanese dialogue.

### Matched tiny regime

Configuration: 256 and 1024 episodes, three seeds, three epochs, roughly 8k-12k parameters.

The answer-weighted random baseline is **7/30 = 0.2333** because multi-query examples contain two answers and parity is binary.

| Architecture | Parameters | 1024-example answer accuracy | Depth-18 stress | State bytes at context 128 | Validation NLL |
|---|---:|---:|---:|---:|---:|
| GRU | 11,680 | **0.2313** | **0.2500** | **160** | **6.7813** |
| DeltaNet probe | 10,152 | 0.1688 | 0.1646 | 1,024 | 19.6958 |
| RWKV-7 probe | 8,160 | 0.1354 | 0.0958 | 960 | 14.8232 |
| Transformer | 10,200 | 0.1083 | 0.0750 | 20,480 | 11.3490 |
| Diagonal SSM probe | 9,984 | 0.0896 | 0.1208 | **128** | 22.2774 |

**Verdict:** no model reliably beats the weighted chance baseline. These values do not support an architecture ranking. They show that a tiny, lightly trained sweep is an optimization/data-regime falsification rather than evidence for a new mechanism.

### Learnability controls

To verify that the suite itself is not broken, stronger GRU and Transformer controls use 2048 episodes, 30 epochs, and three seeds.

| Control | Parameters | Answer accuracy mean | Seed population SD | Depth-18 stress mean |
|---|---:|---:|---:|---:|
| GRU | 16,320 | 0.3073 | 0.0447 | **0.2792** |
| Transformer | 20,160 | **0.3427** | 0.0307 | 0.1406 |

Both controls exceed chance in-distribution, so the suite is learnable. The small Transformer gains more on the short validation distribution, largely from parity, but collapses under length extrapolation. The GRU retains substantially more stress accuracy. This is a warning against novelty bias: a classical GRU is currently the strongest recurrent baseline in this experiment.

## Measurement caveats

- `token_latency_ms` is full-sequence forward throughput divided by tokens, **not** incremental decoding latency.
- Transformer state bytes estimate one layer of K/V cache; recurrent state bytes are explicit recurrent tensors.
- PyTorch process RSS is dominated by the framework and is not a weak-phone deployment measurement.
- The SSM and DeltaNet implementations are mechanism probes. They are not official Mamba-2, KDA, or Gated DeltaNet-2 reproductions.
- Better loss or synthetic recall is not evidence of free Japanese communication.

## Decision policy from the broad view

No original architecture will be proposed until the following are complete:

1. **Faithfulness:** official-checkpoint or official-training parity for at least RWKV-7 and one DeltaNet/SSM family.
2. **Strong baselines:** GRU, Transformer, and xLSTM remain in every matched comparison.
3. **Optimization axis:** optimizer and training recipe are swept separately from architecture.
4. **Multiple memory regimes:** overwrite, retrieval, algorithmic state, long noise, and real text loss all move together.
5. **Test-time learning:** TTT-E2E and evidence-selected TTT receive an independent reproduction with negative controls.
6. **Deployment:** native or framework-free inference is measured on an actual weak Android phone.
7. **Japanese gate:** only models that show stable scaling proceed to real Japanese pretraining and the unified dialogue/reading/reasoning/planning gate.

## Current completion status

- `highschool_level_passed=false`
- `native_japanese_communication_passed=false`
- `weak_smartphone_verified=false`
- `completion=false`

The next highest-information experiment is not another invented mechanism. It is an **official-faithfulness + optimizer-controlled comparison** of RWKV-7, a DeltaNet-family model, GRU, and Transformer, followed by an independent TTT track.
