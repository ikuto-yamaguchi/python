# Causal Identifiability Audit C072

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, latent intervention-target partition `P`, and denotation `d`.
- This run completes (a) prior-art-matrix refinement and (b) theorem/assumption comparison, and fixes the exact public implementation candidate required by C071.
- Numerical training is not started; therefore model size, peak RSS, runtime, and three-seed measurements are not yet reported.

## Decision-relevant question

C071 preregistered LBQ001 and required the next admissible work to be exact public-code selection and pinning rather than a new model.

C072 asks:

> Does the paper-linked DeepMDP implementation faithfully instantiate LBQ001's principal full-consequence language-blind quotient baseline, and is it ready for the mandatory three-seed reproduction contract without changing the architecture?

## Primary source and official code link

Primary paper:

- Gelada et al., *DeepMDP: Learning Continuous Latent Space Models for Representation Learning*, ICML 2019.

The PMLR record links the paper's code to:

- repository: `jbuckman/dmdp-donutworld`
- pinned commit: `1b59ac59c6eb4935a9e2c00ea097bf0d2a14a8e0`
- parent paper-era commit: `d117abbd5840d675359d5a72635e43b5cc6059d3`

The repository README states that `python learn.py` runs the experiments and emits CSV files, while `python plot.py` produces visualizations. It also states that some visualizations differ from the paper although the data-generating script is the same.

## Exact implementation audit

### Observed objective

When `AUTOENCODER = False`, the implementation constructs:

- an encoder `phi`;
- an action-conditioned latent transition model `P`;
- an action-conditioned reward model `R`;
- reward prediction loss `L_R`;
- latent next-state discrepancy `L_pi_phi`;
- Lipschitz gradient penalties;
- a theoretical value-error bound derived from the learned losses.

This is faithful to the paper's reward/transition DeepMDP objective at the level required for a public baseline audit.

### Default execution is not DeepMDP

The pinned `learn.py` sets:

```python
AUTOENCODER = True
```

Therefore the documented command `python learn.py` runs the autoencoder path by default, not the DeepMDP reward/transition baseline. A reproduction manifest must explicitly record the one-line configuration change or a command-line-equivalent wrapper. This is a configuration correction, not a new architecture, but it must be preregistered before execution.

### Environment and scale

The default environment is `ENV = "4x"` with:

- observations: `64 x 64`;
- latent dimension: `2`;
- action count: `16`;
- training updates: `30000`;
- DeepMDP batch size: `256`;
- autoencoder batch size: `1024`;
- evaluation sequence length: `1000`.

The code periodically evaluates discounted-return prediction and writes latent heatmap CSV files.

## LBQ001 compatibility matrix

| LBQ001 requirement | Paper-linked DeepMDP code | C072 classification |
|---|---|---|
| Language-blind training input | yes | compatible |
| Action-conditioned transition model | yes | compatible |
| Reward model | yes | compatible |
| Full preregistered non-semantic consequence family | no | incompatible with principal B4 |
| Reward/transition task-relative quotient control | yes | candidate for B3 |
| Direct partition recovery metrics (ARI/AMI/VI/pairwise F1) | no | missing evaluation harness |
| Held-out consequence validation | no | missing |
| Action shuffle control | no | missing |
| Consequence-channel shuffle control | not representable with reward-only interface | missing |
| Environment-label shuffle | no explicit environment label input | mostly not applicable, must document |
| Gold-target leakage positive control | no | missing |
| Fixed seeds 17/29/43 | no seed interface | missing |
| Model bytes / parameter count | no | missing |
| Peak RSS and wall time | no | missing |
| Dataset or generated-data digest | no | missing |
| Immutable dependency lock/container | no | missing |

## Theorem/assumption comparison

| Object | DeepMDP paper/code | LBQ001 principal target |
|---|---|---|
| Quotient notion | reward and latent-transition similarity | quotient induced by all preregistered non-semantic consequences |
| Observation regime | Markov state observation in synthetic DonutWorld | controlled observation/action/consequence family declared before training |
| Guarantee | representation/model/value bounds from reward and transition losses | empirical direct recovery of the declared target partition |
| Primary metric in code | training loss and discounted-return prediction error | ARI, AMI, VI, pairwise same-block F1, block-count error |
| Semantic scope | task-relative behavioral structure | strongest language-blind operational target ontology supported by held-out consequences |

DeepMDP therefore cannot be promoted to B4 merely because its latent representation is visually structured or predicts return well. Doing so would repeat the exact metric substitution forbidden by C071.

## Identifiability boundary added in C072

Suppose two physical target blocks have identical reward and latent transition distributions under every action used by DeepMDP, but differ on a preregistered independent sensor or cost channel omitted from the model.

Then the paper-linked DeepMDP objective is identical whether the two blocks are merged or separated. A perfect optimizer can legitimately merge them while achieving:

- zero reward prediction error;
- zero latent transition error;
- a tight value-error bound;
- perfect downstream task value.

However, LBQ001-B4 must separate the blocks because the held-out non-semantic consequence differs.

Therefore:

> Perfect reproduction of the official DeepMDP objective does not identify the full-consequence quotient unless the complete consequence family is represented in the observation/objective.

This is not an implementation defect. It is the theorem's task-relative scope.

## Reproduction-readiness audit

The pinned code uses legacy TensorFlow 1 APIs, including:

- `tf.placeholder`;
- `tf.Session`;
- `tf.train.AdamOptimizer`;
- Python 2 print syntax;
- `tf.contrib.distributions.percentile`.

No dependency file, Python version, TensorFlow version, lockfile, container, seed plumbing, or deterministic execution contract is supplied.

Consequently, an immediate numerical run would either be non-hermetic or require compatibility changes. Any compatibility patch must be minimal, separately logged, and must not alter the objective or network architecture. Before execution, the branch must contain a reproduction manifest fixing:

1. upstream commit;
2. exact runtime/container;
3. minimal compatibility patch digest;
4. `AUTOENCODER=False` configuration;
5. seeds `17`, `29`, `43` for Python/NumPy/TensorFlow/environment sampling;
6. exact commands;
7. generated-data digest procedure;
8. direct partition evaluation harness;
9. resource measurement commands.

## Prior-art matrix refinement

C072 updates the matrix as follows:

- Official DeepMDP DonutWorld code is now exactly pinned and is admissible only as LBQ001 **B3 reward/transition control**.
- It is not the principal B4 full-consequence baseline.
- The official objective can be faithfully reproduced without new architecture, but the public package is not currently a hermetic three-seed bundle.
- A successful DeepMDP reproduction cannot by itself establish recovery of `P`, and cannot evaluate `Q` or `d`.

## Decision

**NARROWED TO A TWO-BASELINE EXECUTION GATE: OFFICIAL DEEPMDP FOR B3 PLUS A SEPARATE FULL-CONSEQUENCE B4 — NOT ADOPTED.**

The next admissible work is:

1. create and freeze the minimal DeepMDP reproduction manifest/compatibility patch for B3;
2. select or faithfully instantiate a non-architectural B4 estimator over the preregistered complete consequence vector;
3. run both with seeds `17`, `29`, and `43` while collecting mandatory model/resource/result digests;
4. report direct partition recovery, not only loss, value, or heatmaps.

A new neural architecture remains prohibited.

## Status

- Prior-art matrix refinement: completed.
- Theorem/assumption comparison: completed.
- Exact public implementation pin: completed.
- Official DeepMDP classification: B3 only.
- Principal full-consequence B4 implementation: pending.
- Public numerical reproduction: not started.
- Model size, RSS, runtime, three seeds: mandatory when execution starts; not yet applicable.
- New architecture: none.
- Legacy A–E toy mechanism: none added.
- RQ-001: narrowed and not adopted.
- Novelty: not established.
- Intelligence principle: not discovered.
- Capability progress: not claimed.
