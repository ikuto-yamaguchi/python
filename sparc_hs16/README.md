# SPARC-HS16: strict university-exam gate baseline

SPARC-HS16 is a runnable, non-Transformer, sparse-program integration baseline.
It combines bounded sparse dialogue/fact memory with independently verified
arithmetic, one-variable linear-equation, unit-conversion and syllogism
mechanisms.

HS16 also contains a task-independent minimum-description numeric program
inducer. It receives prompt/answer demonstrations, searches a compact arithmetic
program grammar, accepts only a program that exactly reproduces every example,
routes unseen prompts with sparse signatures, and serializes the learned program
bank. Distance and two-step inventory mechanisms are learned without supplying
their formulas.

This repository intentionally uses a **fail-closed completion gate**. A model is
not allowed to claim Japanese university-entrance-exam mastery unless all 17
required domains are present, every hidden case is correct, communication gates
are perfect, the serialized artifact is at most 1,000,000,000 bytes, and p95
latency is within the weak-phone budget.

Current automated evaluation contains:

- 404-case integrated pilot for verified arithmetic, equations, units and dialogue
- 200 unseen numeric cases solved by two programs induced from eight demonstrations
- serialization round-trip and strict false completion-flag checks

These mechanisms are a real research increment but remain a narrow engineering
milestone. They are not university-exam mastery.

## Run

```bash
python -m unittest discover -s tests -v
python run_pilot.py
python run_induction_pilot.py
```

## Hard constraints

- serialized model/package: <= 1 GB
- no Transformer, dense softmax attention, growing KV cache or dense vocabulary projection
- bounded sparse activation
- exact verifier where a symbolic answer can be checked
- calibrated abstention instead of fabricated answers
- completion flags remain false until the full integrated hidden suite passes
