# Reproduction Sequence

## Step 1 — Pin public benchmark

Use the official SILG package and select Messenger or RTFM after verifying that the environment installs and produces deterministic seeded trajectories.

Record:

- repository/package commit
- Python version
- dependency lock
- environment name
- train/dev/test counts
- observation/action schema
- seed list
- checksum of generated manifests

## Step 2 — Reproduce non-pretrained baseline

Required outputs:

- official or faithful recurrent baseline task success
- random policy
- language-blind policy
- state-only policy
- parameter count
- serialized model bytes
- peak RSS
- training wall time
- CPU inference latency

Do not add a new architecture until this step is within a documented tolerance of the public result.

## Step 3 — Environment-first baseline

Pretrain an action-conditioned next-state representation from language-free trajectories, freeze or fine-tune it, then learn instruction following. Match the end-to-end baseline parameter budget and training data.

Primary comparisons:

- task success
- next-state exact prediction
- action accuracy
- held-out entity/dynamics transfer
- language-form transfer

## Step 4 — Hidden intervention target ablation

Evaluate the same model and trajectories with intervention targets:

- known
- candidate-set known
- hidden
- label shuffled

This separates a language-grounding failure from a causal-variable identifiability failure.

## Step 5 — Decide RQ-001

Adopt, narrow or reject RQ-001. No mechanism-family PR is allowed before this decision.
