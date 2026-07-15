# CIC local run

Run `python -m minimal_predictive_lm.cic_experiment DATASET --output results/cic.json` on the local CPU. Then start the current arithmetic chat with `python -m minimal_predictive_lm.cic_chat results/cic.compact.cic`.

Keep the outer test split frozen. Record unseen accuracy, artifact bytes, wall time, process RSS, synthesis expansions, and checked mechanisms. Do not use outer test answers when changing the learner.
