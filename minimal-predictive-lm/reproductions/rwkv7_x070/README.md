# RWKV-7 x070 minimal reproduction cycle

This directory starts a reproduction-first research track. It does **not** claim a new intelligence principle or general Japanese ability.

## Primary sources

- Paper: RWKV-7 "Goose" with Expressive Dynamic State Evolution, arXiv:2503.14456
- Official implementation: `BlinkDL/RWKV-LM/RWKV-v7/rwkv_v7_demo_rnn.py`

The readable implementation in `rwkv7_reproduction.py` follows the official recurrent x070 update:

```text
S_t = S_{t-1} * w_t
    + S_{t-1} @ (-kk_t outer (kk_t * a_t))
    + v_t outer k_t
```

It retains vector decay, the in-context learning-rate gate, relaxed value replacement across layers, token shift, group normalization, and the RWKV channel mixer. The code is intentionally small and CPU-readable rather than kernel-optimized.

## Reproduction questions

1. Does streaming execution exactly match unsplit recurrent execution?
2. Is recurrent-state memory independent of context length?
3. Does the RWKV-7 delta correction improve unseen Japanese state tracking over an equal-parameter no-delta ablation?
4. What are model bytes, state bytes, process RSS, training time, token latency, candidate count, and recurrent state reads?

## Controlled benchmark

The model is trained autoregressively on procedurally generated Japanese token sequences containing records, overwrites, distractors, a query, and an answer token. Validation uses independent episodes. A longer overwrite-heavy split tests context-depth extrapolation.

This is a controlled architecture probe, not evidence of free Japanese understanding. The answer chance rate is `1/6`.

## Local measured result

Environment: CPU PyTorch 2.10, one thread.

- Parameters: **3,888**
- Serialized checkpoint: **27,063 bytes**
- Recurrent state: **640 bytes/model instance** in the measured training configuration
- Reference state-size probe: **2,560 bytes** at context lengths 16, 64, 256, and 1,024
- Streaming versus unsplit maximum absolute error: **0.0**
- Mean single-token latency: about **0.23 ms**
- Full softmax candidates: **30**
- Active recurrent state elements: **160/token**
- PyTorch process peak RSS: **742,052 KiB**; this includes the framework and is not a mobile deployment measurement

### Data scaling, three seeds

| Architecture | Examples | Answer accuracy | Long overwrite accuracy | Validation NLL |
|---|---:|---:|---:|---:|
| RWKV-7 update | 128 | 0.0000 | 0.0000 | 12.2586 |
| RWKV-7 update | 512 | 0.1797 | 0.1667 | 4.3194 |
| RWKV-7 update | 1,024 | 0.1484 | 0.1823 | 1.5772 |
| No-delta ablation | 1,024 | 0.1849 | 0.1797 | 1.6389 |

## Interpretation

The recurrence-level claims were reproduced:

- streaming state produces exactly the same outputs as an unsplit pass;
- state size is constant with context length;
- the model and recurrent state are far below 1 GB.

The capability claim was **not** reproduced at this scale. Validation NLL improved with data, but answer accuracy remained around the `1/6` chance rate and was non-monotonic. The full delta update had slightly better NLL than the equal-parameter ablation but did not consistently improve answer accuracy. Therefore this cycle does not establish useful Japanese state tracking, dialogue, reasoning, or smartphone deployment.

## Run

```bash
python -m pip install pytest
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
pytest -q test_rwkv7_reproduction.py
python rwkv7_reproduction.py --output artifacts/rwkv7_reproduction_report.json
```

## Claim boundary

- `highschool_level_passed=false`
- `native_japanese_communication_passed=false`
- `completion=false`

The next reproduction step is to validate the same recurrence against official checkpoint logits or an official training configuration, then add a matched Transformer/GRU baseline and a stronger associative-recall suite. No new architecture should be proposed before those controls are complete.
