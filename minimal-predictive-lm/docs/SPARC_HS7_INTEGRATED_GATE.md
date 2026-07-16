# SPARC-HS7: integrated Japanese high-school readiness gate

This gate exists to prevent narrow synthetic demonstrations from being mistaken for general intelligence.

## One-model rule

Every task must be answered by one persisted model artifact. Domain labels may be used only for reporting. They may not select independent expert models, separate answer keys or benchmark-specific feature paths.

## Capability sections

### Japanese language and reading

- read passages of 800-3,000 Japanese characters;
- resolve references across sentences;
- identify claims, evidence, contrast and causal structure;
- summarize without copying a memorized whole answer;
- answer questions that combine two separated parts of a passage;
- revise an interpretation after a counterexample.

### Mathematics

- arithmetic and percentages;
- equations and inequalities;
- functions and proportional reasoning;
- unit-aware multi-step word problems;
- geometry relations and short proof plans;
- probability and descriptive statistics;
- explain the acquired procedure and reject dimensionally invalid plans.

### Science

- retrieve facts and build causal chains in physics, chemistry, biology and Earth science;
- combine quantitative and qualitative evidence;
- distinguish correlation, mechanism and exception;
- update a conclusion when a new observation contradicts the current model.

### Social studies

- geography, Japanese history, world history, civics and introductory economics;
- chronological and causal explanations rather than isolated fact lookup;
- comparison of two institutions, events or regions;
- explicit uncertainty when evidence is insufficient.

### Conversation and agency

- sustain at least 30 turns with bounded working memory;
- preserve user-provided constraints and correct them on request;
- decompose a goal into steps, execute local reasoning programs and report failures;
- avoid replaying memorized full responses;
- learn a new concept from conversation and transfer it to a differently worded question.

## Evaluation protocol

- at least 200 held-out free-response items, 40 per capability section;
- at least half of the entities, numbers and surface forms are unseen during training;
- at least 25% require two or more retrieved facts or program steps;
- at least 10% contain misleading or contradictory information;
- answers are graded by exact quantities where appropriate and by concept/evidence rubrics elsewhere;
- per-section score must be at least 70%; overall score must be at least 75%;
- calibrated abstention is rewarded when the required evidence is absent;
- no score is accepted without resource measurements from the same run.

## Resource protocol

Report for every answer:

- active concepts, schemas, edges and program nodes;
- sparse index reads and estimated primitive operations;
- peak resident memory;
- serialized model bytes;
- latency distribution;
- number of surprise writes;
- whether any global scan, growing context cache or dense vocabulary projection occurred.

The target architecture remains:

- no full-history softmax attention;
- no KV cache growing with dialogue length;
- bounded active workspace;
- sparse event-driven concept and program activation;
- long-term capacity may grow, but routine per-answer activity must remain sublinear and locally bounded.

## Current boundary at HS6

HS6 can converse in a narrow learned surface, ingest repeated two-slot relations, perform bounded relational chains, select learned numeric microprograms and synthesize bounded arithmetic expression trees. It does not yet pass this gate. In particular, long-passage comprehension, unrestricted semantic-role induction, unit algebra, proof planning, contradiction repair and broad real curriculum knowledge remain incomplete.

## HS7 implementation milestones

1. Unit-typed expression and plan graph with dimensional checking.
2. Bounded episodic passage memory and cross-sentence reference links.
3. Contradiction-sensitive fact revision with recency and evidence provenance.
4. Multi-document evidence composition.
5. Real Japanese curriculum ingestion and the complete free-response gate above.
