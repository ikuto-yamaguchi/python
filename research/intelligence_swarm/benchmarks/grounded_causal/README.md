# Grounded Causal Baseline

This directory replaces one-off toy experiments with a fixed evaluation contract for public benchmark reproduction.

## First benchmark

Primary candidate: SILG Messenger or RTFM.

Selection criteria:

- public environment and code
- interactive language grounding
- multiple entities/dynamics
- supports recurrent baseline without pretrained language model
- feasible on a single local GPU or CPU for reduced reproduction
- objective task success

J-CRe3 is used as an external Japanese reference-grounding audit, not averaged with SILG task success.

## Required methods

- `correct`: the implemented model
- `random`: random action or matched random predictor
- `language_blind`: state/action history without utterance
- `state_only`: current state without language/history
- `target_label_shuffle`: intervention-target correspondence shuffled
- `outcome_shuffle`: transition outcomes shuffled
- `official_baseline`: faithful public baseline when available

## Files

- `evaluation_contract.py`: validates split integrity and scores external metrics.
- Future files must include a pinned environment manifest, exact commands, raw logs and resource measurements.

## Evaluation data schema

Each JSONL row requires:

- `instance_id`
- `domain`
- `seed`
- `split`
- `condition`
- `utterance`
- `state_before`
- `gold_action`
- `gold_state_after`

Optional:

- `gold_inverse`
- `model_input_fields`

Predictions require:

- `instance_id`
- `method`
- `pred_action`
- `pred_state_after`
- optional `pred_inverse`

## Commands

```bash
python evaluation_contract.py validate instances.jsonl
python evaluation_contract.py score instances.jsonl predictions.jsonl
```

## Progress

Progress is not declared from internal latent quality. It requires held-out task success or next-state/action/inverse ability on at least two domains and three seeds, with paired controls on identical instances.
