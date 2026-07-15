# CIC-003 local mixed-capability experiment

This experiment runs on CPU. It trains one serialized artifact that answers Japanese arithmetic word problems and Japanese multiple-choice commonsense questions without receiving a task ID.

## Linux or WSL2

```bash
git clone https://github.com/ikuto-yamaguchi/python.git
cd python
git checkout research/cic-mixed-001
python -m venv .venv
source .venv/bin/activate
python -m pip install -e minimal-predictive-lm pytest

git clone --depth 1 https://github.com/nlp-waseda/chain-of-thought-ja-dataset.git /tmp/cot-ja
mkdir -p minimal-predictive-lm/public_data/cic_mixed
cp /tmp/cot-ja/dataset/mawps/test.json minimal-predictive-lm/public_data/cic_mixed/mawps.json
cp /tmp/cot-ja/dataset/jcommonsenseqa/test.json minimal-predictive-lm/public_data/cic_mixed/jcommonsenseqa.json

cd minimal-predictive-lm
/usr/bin/time -v python -m minimal_predictive_lm.cic_mixed_experiment \
  public_data/cic_mixed/mawps.json \
  public_data/cic_mixed/jcommonsenseqa.json \
  --output results/cic_003_mixed.json
```

The output records held-out accuracy, model bytes, synthesis expansions, elapsed time and peak process memory. The raw holdout is split before answer-driven arithmetic synthesis. Inner validation chooses the epoch count; the held-out rows are not used for model selection.

## Chat

```bash
python -m minimal_predictive_lm.cic_mixed_chat results/cic_003_mixed.mixed.cic
```

Arithmetic input is free text. Commonsense input contains numbered options such as `(0) ...` through `(4) ...`. There is no external task label.

## Claude Code verification request

Ask Claude Code to run the commands above, inspect `results/cic_003_mixed.json`, verify that the held-out split is formed before training, and report CPU model, wall time, maximum resident memory, artifact bytes, arithmetic accuracy and commonsense accuracy. It must not tune code or thresholds using the held-out answers.
