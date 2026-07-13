# Phase 19c: causal long-memory gate

Phase 19a established small file-disjoint scaling. Phase 19b established partial leave-one-domain-out transfer, with positive transfer to code and prose but negative transfer to structured data.

Phase 19c asks whether the predictor benefits from state that reaches beyond a local n-gram window.

## Protocol

1. Split the training partition again into core-training and calibration files.
2. Learn the byte dictionary and trigram on core-training files only.
3. Select memory confidence and minimum support on calibration files only.
4. Retrain the dictionary/trigram on the full training partition.
5. Evaluate file-disjoint held-out files causally from left to right.

The memory stores only prior occurrences of exact token contexts inside the current file. It never observes future tokens. Two windows are compared:

- short memory: 64 encoded tokens,
- long memory: 4096 encoded tokens.

A memory prediction is used only when all previously observed continuations of the longest available context agree.

## Required gates

- core-training, calibration, and held-out file paths are pairwise disjoint,
- appending a future suffix cannot alter any prefix token probability,
- long memory beats the frozen trigram baseline,
- long memory beats short memory,
- long memory wins in at least two of code/prose/structured,
- causal memory predictions exceed 75% precision,
- a synthetic dependency beyond the 64-token window is solved only by long memory.

## Interpretation

Passing demonstrates useful causal prefix memory for compression on unseen files. The held-out file prefix is used for online adaptation, so this is not a frozen zero-shot language model result. It does not demonstrate semantic understanding, question answering, reasoning, or high-school intelligence.
