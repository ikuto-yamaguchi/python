# Reproduce Cycle 005

```bash
cd research/intelligence_swarm/tracks/D_memory_eligibility
python cross_lexicon_lesion_eligibility_cycle005.py > MEASUREMENTS_CYCLE_005.json
```

Requirements:

- Python 3.11+
- NumPy
- Linux/macOS/WSL (`resource` module)
- external model/APIなし

固定seed: `1, 7, 19`。

出力JSONの `strict_gate_pass_seeds`、`per_seed[*].eligibility`、`mean[*].lesion_drop` を確認する。
test時after、完成trajectory、domain辞書、shared object ID、span proposal、string retrieval、RAG、external LLMは使用しない。
