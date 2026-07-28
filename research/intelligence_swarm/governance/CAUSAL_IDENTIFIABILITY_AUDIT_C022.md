# Causal Identifiability Audit C022

Date: 2026-07-25
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + assumption/guarantee comparison + identifiability counterexample + public-code availability audit**.

No new architecture, toy mechanism, operation/goal hypothesis, intervention ontology, benchmark variant, memory mechanism, or branch was introduced.

## Primary work newly audited

### Grounding Before Generalizing: How AI Differs from Humans in Causal Transfer

Liangru Xiang, Yuxi Ma, Zhihao Cao, Yixin Zhu, and Song-Chun Zhu, arXiv:2604.24062, first posted 2026-04-27; listed by the authors as a CogSci 2026 paper.

Primary records:

- arXiv: https://arxiv.org/abs/2604.24062
- project page: https://causal-openlock.github.io/
- author publication page: https://yzhu.io/publication/openlock2026cogsci/

The author page links an official code repository at `https://github.com/caozh20/CausalLLM`, but that link returned HTTP 404 at audit time. The linked dataset archive was also not retrievable through the audit client. Therefore no public-code reproduction was started in this cycle.

## Exact empirical boundary relevant to RQ-001

The paper adapts OpenLock to evaluate interactive causal discovery and transfer by contemporary LLMs/VLMs. Each environment contains seven levers and one door. The latent task topology is either:

1. Common Cause: one first-stage lever enables three alternative second-stage levers;
2. Common Effect: three alternative first-stage levers converge on one bottleneck lever.

Across environments, lever positions, colours, and labels change while the CC/CE relational topology is retained. Agents receive action histories and outcomes and must find three successful action sequences within a fixed attempt budget.

The paper distinguishes:

- within-environment causal discovery;
- transfer after being shown complete source-environment solutions;
- text-only, image-only, and text-plus-image interfaces.

Its key empirical result is delayed or absent transfer in the tested models: unlike humans, models did not reduce first-solution search cost in the new environment and only sometimes improved after discovering an initial target-environment solution.

## What this prior art does establish

The work directly covers several claims that cannot be treated as new contributions of RQ-001:

- interactive language-mediated causal exploration can be evaluated with latent relational structure and sequential action feedback;
- surface-token changes can be separated from preservation of a known finite topology family;
- transfer can be measured prospectively at the first target-environment solution rather than only by final success;
- text-only causal interaction can outperform or match multimodal variants;
- successful within-environment causal discovery does not imply immediate abstract causal transfer;
- source solutions expressed in natural language do not guarantee portable structural grounding.

## What this prior art does not establish

The paper is an empirical behavioural evaluation, not an identifiability result. In particular it does not provide:

- a latent-variable generative model for raw utterances;
- an unknown intervention-target partition to be recovered;
- a population equivalence class over causal representations;
- a theorem jointly identifying utterance equivalence and latent target partition;
- an anti-recoding or externally anchored denotation condition;
- a consistency or finite-sample estimator guarantee for latent partition recovery.

The CC/CE topology family is fixed by the experimenter, and successful action sequences are supplied as source demonstrations. Thus the experiment probes whether a model transfers a known relational schema across remapped surface tokens; it does not infer whether two raw utterances denote the same unknown latent intervention target under an unrestricted language generator.

## Theorem/assumption comparison

| Dimension | Xiang et al. 2026 | Current RQ-001 candidate | Remaining burden |
|---|---|---|---|
| Causal object | Two experimenter-fixed topology families, CC and CE | Residual latent intervention-target partition after strongest non-language CRL | Specify the unresolved equivalence class rather than reuse a known topology label |
| Language | Symbolic state/action descriptions, histories, outcomes, and source solutions | Population raw-language channel with unknown equivalence classes | Define a generative language observation model and its invariances |
| Interaction | Sequential action selection with explicit outcome feedback | Potential interactive querying under hidden targets | Separate information contributed by language from action/outcome feedback |
| Transfer | Surface-remapped environment with preserved topology | Unseen utterance, composition, target combination, and system | Prove transfer corresponds to equivalence-class reduction, not token remapping |
| Guarantee | Behavioural success and attempt-count statistics | Joint identifiability plus estimator guarantee | Supply theorem, impossibility boundary, and finite-sample/consistency result |
| External anchor | Experimenter supplies task semantics and complete source solutions | Anchor must be non-recodable with latent model | Formalise the anchor and show why it fixes residual symmetry |

## Prior-art matrix refinement

The following claims are no longer admissible as novel:

- proposing an interactive text interface for causal structure discovery;
- testing language-conditioned causal transfer across remapped object labels;
- treating first-solution efficiency as a new transfer metric;
- showing that source-language demonstrations fail to produce immediate transfer;
- using CC/CE OpenLock success as evidence of identifying an unknown latent target partition;
- treating a text-versus-image performance difference as an identifiability result.

OpenLock is a useful behavioural baseline for prospective causal transfer, but it cannot substitute for a population identifiability baseline.

## Counterexample: prospective transfer does not identify utterance equivalence or target partition

Let the target environment have latent causal topology `T` in the known set `{CC, CE}`, surface-token assignment `M`, interaction history `H`, and source-language demonstration `D`. Let the agent policy be

`A_t ~ pi(A_t | D, M, H_t)`.

Suppose two internal models use different latent target partitions `P` and `P'` and different language-equivalence maps `q` and `q'`, but induce the same policy over every reachable interaction history:

`pi_{P,q}(A_t | D, M, H_t) = pi_{P',q'}(A_t | D, M, H_t)`.

Because OpenLock evaluation observes actions, state changes, discovered solutions, and attempt counts, the two models are observationally indistinguishable in the benchmark. They may have identical first-solution and total-transfer statistics while disagreeing about which utterances are equivalent and which latent components constitute an intervention target.

Even perfect immediate transfer only establishes that the policy uses information sufficient for the finite CC/CE task. It does not establish uniqueness of the internal causal representation. Conversely, delayed transfer does not prove absence of a causal representation; it may result from failure to bind surface tokens `M` to already represented structural roles.

Therefore:

> Prospective causal-transfer performance constrains policy behaviour but does not, without a generative model and anti-recoding assumptions, identify raw-language equivalence or a latent intervention-target partition.

## Stronger leakage boundary for interactive grounding

In the text-only condition, the model receives the initial state, executed action history, detailed state changes, explicit solution acknowledgements, and remaining-solution count. These are legitimate task observations, but for RQ-001 they are potential alternative identification channels.

A claimed language contribution must condition on or ablate:

- environment and surface-token identity;
- action history;
- state-transition feedback;
- solution-found acknowledgements;
- remaining-target counts;
- complete source action sequences;
- completed target-environment trajectories.

If the alleged target distinction can be reconstructed from these channels, language has not supplied a missing causal separation.

## Updated admissible RQ

The surviving candidate is narrowed to:

> After controlling for interactive action/outcome histories and behavioural structure-transfer information of the OpenLock kind, can an externally anchored population language channel supply a target distinction unavailable from the interaction process, strictly reduce the residual causal equivalence class, and jointly identify raw-utterance equivalence with a refined latent intervention-target partition?

This formulation is **not adopted**. It remains a preregistration candidate only.

## Adoption requirements added by C022

Before adoption, the candidate must provide:

1. an explicit non-language interactive sufficient statistic containing actions, outcomes, and environment remapping;
2. a countermodel pair indistinguishable under that statistic but separated by the proposed language anchor;
3. a language law not measurable from source solutions, environment identity, action histories, outcomes, or completed trajectories;
4. a theorem proving strict reduction of the residual equivalence class;
5. an impossibility result when language is only a paraphrase of source solutions or interaction history;
6. prospective first-target-solution transfer evaluation in addition to aggregate success;
7. an OpenLock-style source-demonstration baseline and a non-language interaction baseline;
8. unseen utterance-form, composition, target-combination, surface-remapping, and system splits;
9. public baseline reproduction and one preregistered central claim before architecture work;
10. model bytes, peak RSS, training wall time, CPU inference latency, raw logs, checksums, and seeds `1/7/19` once an experiment begins.

## Decision on RQ-001

### Decision: NARROWED BEYOND BEHAVIOURAL INTERACTIVE CAUSAL TRANSFER — NOT ADOPTED

Interactive causal discovery, remapped-surface transfer, prospective first-solution metrics, and language-demonstration transfer failure are covered empirically by OpenLock-based work. These observations do not identify internal latent partitions. The surviving question must prove that language adds information beyond the complete interaction history and fixes a residual representation symmetry rather than merely improving or delaying task transfer.

No experiment or architecture is authorised by this result.

## Resource accounting

This cycle is a prior-art, assumption/guarantee, code-availability, and counterexample audit only. No model experiment was started. Model bytes, peak RSS, training wall time, CPU inference latency, and three-seed reporting are not applicable here and remain mandatory once an experiment begins.

## Status

- completed this cycle: 2026 interactive-causal-transfer prior-art refinement, assumption/guarantee comparison, code-availability audit, and policy-equivalence counterexample
- interactive text causal discovery as a novel contribution: rejected
- OpenLock transfer performance as latent-partition identification evidence: rejected
- RQ-001: further narrowed, not adopted
- public capability baseline: not reproduced
- new architecture: none
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
