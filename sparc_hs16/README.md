# SPARC-HS16: strict university-exam gate baseline

SPARC-HS16 is a runnable, non-Transformer, sparse-program integration baseline.
It combines bounded sparse dialogue/fact memory with independently verified
arithmetic, one-variable linear-equation, unit-conversion and syllogism
mechanisms.

This repository intentionally uses a **fail-closed completion gate**. A model is
not allowed to claim Japanese university-entrance-exam mastery unless all 17
required domains are present, every hidden case is correct, communication gates
are perfect, the serialized artifact is at most 1,000,000,000 bytes, and p95
latency is within the weak-phone budget.

Current pilot mechanisms are only a narrow engineering milestone; they are not
university-exam mastery.

## Run

```bash
cd sparc_hs16
python -m unittest discover -s tests -v
python run_pilot.py
```

## Hard constraints

- serialized model/package: <= 1 GB
- no Transformer, dense softmax attention, growing KV cache or dense vocabulary projection
- bounded sparse activation
- exact verifier where a symbolic answer can be checked
- calibrated abstention instead of fabricated answers
- completion flags remain false until the full integrated hidden suite passes
