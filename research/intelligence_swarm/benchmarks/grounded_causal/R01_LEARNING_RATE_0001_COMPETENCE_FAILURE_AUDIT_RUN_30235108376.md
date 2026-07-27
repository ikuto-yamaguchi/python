# R0.1 learning-rate 0.0001 competence-failure audit

## Scope

This is a negative-result audit for GitHub Actions run `30235108376` on canonical branch `research/intelligence-swarm-reconstruction-001`.

The run changed exactly one learner factor relative to the completed stateful + unroll-80 screening:

- `learning_rate: 0.0005 -> 0.0001`

The following remained fixed:

- SILG commit `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM commit `58f17955595b5a127c96d045d896fcbcc7d4b570`
- official `multi` model
- `stateful=true`
- `unroll_length=80`
- `entropy_cost=0.05`
- `num_actors=2`
- `batch_size=2`
- `num_threads=1`
- requested frames `131072`
- seeds `1 / 7 / 19`
- train/test environments, split, evaluation instances, and matched controls

No architecture, operation/goal toy hypothesis, or new mechanism family was introduced.

## Immutable artifact

- run: `30235108376`
- job: `89881341003`
- execution commit: `67556f067028edac502380c6d3de15575c996ffc`
- artifact ID: `8642403437`
- artifact name: `r01-silg-rtfm-learning-rate-30235108376`
- artifact bytes: `91609969`
- artifact digest: `sha256:882e92a17ba5da5836dcf78379a484cc7ed63827ed3bf0b18196c5b18c3d8917`

Training, checkpoint verification, matched controls, policy diagnostics, official-evaluation parity, dependency/resource capture, and artifact upload all completed. The unchanged qualification gate rejected the policy.

## Qualification result

Classification:

`optimization_or_policy_competence_failure`

Failures:

- `zero_source_policy_success`
- `correct_not_above_random_win_rate`
- `correct_not_above_random_return`

Three-seed aggregate:

| Metric | Correct | Random | Correct - Random |
|---|---:|---:|---:|
| Win rate | 0.0000 | 0.0667 | -0.0667 |
| Mean return | -2.1523 | -1.1513 | -1.0010 |

Other control win rates:

- Language-blind: `0.0000`
- Language-shuffle: `0.0000`
- State-only: `0.0167`

The lower learning rate did not recover instruction following and performed worse than the preceding stateful + unroll-80 run. Therefore `learning_rate=0.0005` being too high is rejected as the sole cause of the R0.1 competence failure.

## Official learner facts relevant to the next diagnosis

At the pinned SILG commit, `run_exp.py` already performs global gradient clipping:

```python
total_loss.backward()
nn.utils.clip_grad_norm_(model.parameters(), 40.0)
optimizer.step()
scheduler.step()
```

The learner uses RMSprop with the launcher flags and saves/restores model, optimizer, scheduler, and frame state in `Train.state_dict` / `Train.load_state_dict`.

Consequently, the next step is not an arbitrary clipping-value sweep. It is a behavior-preserving parity audit that records:

1. actual optimizer hyperparameters at construction and after checkpoint restore;
2. scheduler state and effective learning rate over updates;
3. pre-clip and post-clip global gradient norms and clipping frequency;
4. non-finite gradients;
5. whether actor and learner parameters remain synchronized after each update;
6. whether checkpoint restore reproduces the same next optimizer step on a fixed batch.

Only an evidenced mismatch may become the next single changed factor. If parity holds, optimizer/checkpoint-restore mismatch is rejected and the next factor must be selected from preserved diagnostics without inventing a new architecture.

## Formal status

- learning-rate reduction as sole cause: **rejected**
- R0.1 competent public baseline reproduction: **not achieved**
- R0.2 Environment-first comparison: **not started**
- task success / next-state prediction / action accuracy / dynamics transfer: **not recognized**
- entity and language-form transfer in RTFM S1: **not applicable**
- new intelligence principle or capability progress: **not claimed**
