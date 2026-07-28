# RESET-E008 Integration Report

Date: 2026-07-24

## Decision

**Continue R0 Research Reconstruction. Do not advance to a new mechanism stage.**

The public-baseline reproduction count remains zero. Novelty and a central claim remain unestablished. The productive action in this integration cycle was to narrow the research question against newer causal-representation results and to turn the backlog into an executable reproduction ledger.

## Evidence integrated

### Public benchmark and code availability

- SILG remains an appropriate multi-environment interactive grounding benchmark. The official PyPI release is `silg==0.0.1` from 2021-10-20, with Python `>=3.7.10` and MIT licensing.
- Official SILG instructions require separate environment installation, dependency installation and environment-data download. The experiment entrypoints are `run_exp.py` and `launch.py`.
- SILG covers RTFM, Messenger, NetHack, ALFWorld and Touchdown, but R0.1 is deliberately limited to RTFM or Messenger to obtain one verified result before expanding scope.
- Language Dynamics Distillation is an established SILG baseline: language-conditioned next-dynamics pretraining improved sample efficiency and generalization relative to tabula-rasa and non-language demonstration pretraining.
- J-CRe3 is publicly discoverable at `riken-grp/J-CRe3`, with public metadata availability dated 2026-04-06. It is a Japanese crossmodal reference dataset, not an intervention benchmark.

### 2025–2026 novelty pressure

- Ng et al. 2025 broaden causal-representation identifiability to general environments under nonparametric mixing, subject to mechanism-change and latent-model assumptions.
- Li et al. 2025 show that arbitrary-subset interventions may identify only a causal abstraction rather than exact low-level variables.
- Lee et al. 2026 provide finite-sample recovery results with logarithmically many unknown multi-node intervention environments in their model, including unknown target recovery.

Therefore, unknown intervention targets, few environments, causal abstraction and language-conditioned dynamics cannot independently serve as the research contribution.

## Research-question change

Previous candidate:

> Can latent intervention targets and raw-language equivalence classes be jointly identified from interactive trajectories when neither a semantic parser nor intervention-axis labels are supplied?

Narrowed candidate `RQ-001-N`:

> On a fixed public interactive benchmark, can raw-language equivalence provide statistically necessary information for recovering a latent intervention partition or abstraction beyond state/action-only models, when environment identity is available for split construction but intervention-target labels, semantic parsers, object slots and pretrained language models are absent?

Status: **NARROWED, NOT ADOPTED**.

The wording now permits recovery only up to a shared permutation or abstraction. This avoids claiming exact identity when the intervention family cannot identify it.

## Rejection conditions

RQ-001-N must be rejected if:

1. a primary source already establishes the same joint recovery under equal or weaker assumptions;
2. the reproduced full-language model fails to exceed state/action-only and language-shuffle controls on held-out mechanisms;
3. gains disappear under entity Rename, environment-ID-only or transition-shuffle controls;
4. the public benchmark lacks sufficient intervention diversity and adding it requires a hand-written semantic ontology;
5. evaluation uses target labels, post-treatment state or completed trajectories unavailable at inference.

## Reproduction status

| Gate | Status | Evidence required next |
|---|---|---|
| R0.1 SILG shared recurrent baseline | NOT STARTED / no metric | pinned repository SHA, environment install, official metric |
| Random control | NOT MEASURED | same episodes and seeds as baseline |
| Language-blind control | NOT MEASURED | instruction masked with other inputs unchanged |
| State-only control | NOT MEASURED | action/history/state retained, language removed |
| LDD / language-dynamics baseline | NOT REPRODUCED | next-state objective and task-success result |
| R0.3 hidden-target ablation | BLOCKED BY R0.1–R0.2 | known / candidate-set / unknown / shuffle conditions |
| J-CRe3 realism audit | DATA SOURCE PINNED, baseline not reproduced | license, checksum, split and blind baselines |
| Model/RSS/runtime/CPU/3 seed | NOT MEASURED | mandatory when first run completes |
| Leakage contract | IMPLEMENTED, not yet exercised on real data | run against actual prediction files |

## Track control

- A: only SILG environment/baseline reproduction.
- B: only published environment-first and language-dynamics baselines.
- C: only primary-literature identifiability audit and preregistered hidden-target ablation.
- D: only evaluation, leakage, statistics and resource reproducibility.
- E: integrates all work on `research/intelligence-swarm-reconstruction-001`; no new branch chain or mechanism family.

## Progress assessment

- External capability progress: **none claimed**.
- New intelligence principle: **none**.
- Public baseline reproduced: **0**.
- Novelty: **not established**.
- High-school-level intelligence: **not achieved**.

## Next integration target

Do not write another conceptual report unless it changes an adoption/rejection decision. The next useful integration must contain at least one of:

1. a successful SILG RTFM/Messenger baseline metric with raw logs and resources;
2. a reproducible installation failure with exact dependency conflict and a minimal remediation commit;
3. a primary source that directly forces rejection or further narrowing of RQ-001-N.
