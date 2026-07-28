# Causal Identifiability Audit C007

Date: 2026-07-25
Track: C — causal grounding / world identity / counterfactuals
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + benchmark qualification decision**.

No new architecture, toy mechanism, ontology, slot inventory, knowledge graph, RAG component, or external-LLM dependency was introduced.

## Question under audit

Can episode-aligned raw language and a latent intervention partition be jointly identified from interactive trajectories, without supplied intervention targets, semantic parsers, object slots, pretrained language models, or researcher-authored mechanism labels?

The latest narrowed empirical form required a public benchmark where:

1. raw language is episode-aligned;
2. state/action/history trajectories are available;
3. mechanism-changing variation is defined independently of the language answer;
4. intervention family or a theoretically justified causal abstraction is available as evaluation ground truth;
5. held-out targets or mechanisms exist;
6. evaluation can be permutation- or abstraction-aware.

## New primary-source audit

### CausalPhys — Tang et al., 2026

CausalPhys contains 3,062 image/video questions spanning perception, anticipation, intervention and goal orientation. Each item includes an expert-authored typed causal DAG over object, attribute and event nodes.

It is useful for causal physical reasoning evaluation, but it does **not** qualify for Gate I:

- it is question answering over curated media, not an interactive action trajectory;
- the causal graph is expert annotation supplied after dataset construction, not a latent intervention partition recoverable from behavior;
- the intervention and goal-oriented categories are questions about hypothetical manipulations, not repeated environment distributions with unknown intervention targets;
- the graph schema explicitly supplies semantic node types and names;
- its graph-grounded rationale metric uses an external judge LLM, which is incompatible with the present no-external-LLM constraint;
- it does not establish that raw language contributes mechanism information after conditioning on complete non-language trajectories.

Therefore CausalPhys is an external causal-reasoning audit candidate, not a joint-identifiability benchmark.

Primary source: https://arxiv.org/abs/2606.05966

### Language Agents Meet Causality — Gkountouras et al., ICLR 2025

This work integrates causal representation learning with an LLM and links learned causal variables to natural-language expressions, using the causal world model as a simulator for reasoning and planning.

Consequence for novelty:

- `causal variables <-> natural-language expressions` as an interface is already explicit prior art;
- combining an LLM reasoner with a learned causal world model is not a new central claim;
- the remaining candidate cannot be a generic language–causal-world-model integration claim;
- the work relies on an LLM and an already learned causal representation, rather than identifying raw-language equivalence and unknown intervention partitions jointly from unlabelled interaction.

Primary source: https://proceedings.iclr.cc/paper_files/paper/2025/hash/5c5bc3553815adb4d1a8a5b8701e41a9-Abstract-Conference.html

### General agents need world models — Richens, Everitt & Abel, ICML 2025

This work formally shows that sufficiently general multi-step goal-directed competence entails a predictive environment model extractable from the policy.

Consequence for novelty:

- demonstrating that a capable agent internally supports prediction is not itself a novel intelligence principle;
- a future claim must specify the *additional identifiability supplied by language*, not merely the existence or usefulness of a world model.

Primary source: https://proceedings.mlr.press/v267/richens25a.html

## Identifiability distinction

Let:

- `X` be the complete non-language information: state, action, history, reward, time, policy phase and environment identity;
- `L` be raw episode-aligned language;
- `M` be an independently defined mechanism or intervention-supported causal abstraction.

A necessary condition for language to refine the trajectory-only equivalence class is:

`I(M; L | X) > 0`.

This is not sufficient. Even when the conditional mutual information is positive, the signal may encode a benchmark annotation convention, question template, environment label, or answer leakage rather than a recoverable intervention partition.

An empirical Gate-I benchmark must additionally make at least two competing latent partitions observationally equivalent under `X`, separate them under correct `L`, and make that separation disappear under matched language shuffle while preserving paraphrases.

No audited public benchmark currently supplies this complete test.

## Decision

### Empirical RQ-001 track: REJECTED

The empirical claim of jointly identifying raw-language equivalence and a latent intervention partition is closed under the current public-benchmark constraint.

Reason:

- SILG/RTFM supplies interaction and language but no independent latent intervention ground truth;
- J-CRe3 supplies Japanese language and reference grounding but no mechanism interventions;
- CausalTriplet supplies intervention structure but no episode-aligned free language;
- ACCESS and MIB concern different causal objects;
- CausalPhys supplies expert causal graphs and language questions but no unknown-target interactive trajectory identification problem;
- adding the missing labels ourselves would reintroduce the prohibited researcher-authored ontology.

This is a benchmark/claim qualification result, not a claim that the scientific question is impossible in every conceivable dataset.

### Surviving theory-only candidate: RQ-001-T1 — NOT ADOPTED

> Under explicitly stated observation and intervention assumptions, characterize when raw language can strictly refine the causal equivalence class identifiable from trajectories alone, and prove impossibility when `M` is conditionally independent of `L` given complete non-language history or when no intervention family separates competing partitions.

Before adoption, T1 requires:

1. a formal observation model;
2. a precise equivalence relation;
3. a theorem that is not a restatement of multimodal nonlinear ICA, environment-indexed CRL, or conditional independence;
4. at least one nontrivial positive and one negative construction;
5. preregistered claims and counterexamples;
6. no new architecture until R0.1 public capability reproduction is complete.

## Transfers

- **A:** do not treat language-correlated clusters as semantic identity without an independently separable world variable and permutation-aware recovery criterion.
- **B:** executable operation identity requires interventions that distinguish alternative target/source/goal assignments; language prediction gain alone is insufficient.
- **D:** no episode unit is formally re-identifiable for Gate I without an independent mechanism label or theorem-backed abstraction.
- **E:** close empirical Gate I; keep Gate L reproduction active; permit only a preregistered theory-only proposal after novelty comparison.

## Status

- Public capability baseline reproduced: no
- Empirical Gate I: rejected
- Theory-only RQ-001-T1: candidate, not adopted
- New architecture: none
- Novelty: not established
- Intelligence principle: not discovered
- Capability progress: not recognized
- High-school-level intelligence: not achieved
