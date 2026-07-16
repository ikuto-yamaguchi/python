# SPARC-HS4: raw Japanese curriculum induction

## Objective

Move from structured slot demonstrations to broad Japanese educational text while preserving the SPARC constraints: sparse local activity, bounded working state, no full-history attention, no growing KV cache and no dense global knowledge scan.

## Learning pipeline

1. Learn variable-length chunks from raw Japanese sentences.
2. Cluster repeated surface skeletons and discover changing spans as latent semantic slots.
3. Store latent relations without requiring a hand-written relation name.
4. Align question/answer examples to latent relations using only the answer and entities present in the question.
5. Learn whether a relation is transitive, causal, symmetric or ordered from observed closures and QA feedback.
6. Compose answers from retrieved facts and reasoning paths.
7. Consolidate repeated episodes into stable concepts; retain exceptions as sparse inhibitory edges.

## Curriculum domains

One shared model must ingest and answer across:

- Japanese language: definitions, summaries, reference resolution, argument structure and short reading comprehension;
- mathematics: arithmetic, equations, proportional reasoning, geometry relations and short proofs;
- science: physical causality, chemistry facts, biology taxonomy and Earth science;
- social studies: geography, Japanese/world history, civics and economics;
- ordinary conversation and instruction following.

Domain IDs may be used for reporting but not for routing to independent specialist models.

## High-school-level gate

No high-school-level claim is allowed until one persisted model passes all of the following:

- held-out free-response tasks in every curriculum domain;
- questions requiring facts from more than one passage;
- multi-turn correction after a counterexample;
- explanations containing auditable evidence paths;
- sustained conversation without replaying memorized whole answers;
- transfer to unseen names, quantities and wording;
- calibrated unknown responses;
- no benchmark-specific answer-key features.

## Resource gate

Every result must report:

- serialized knowledge bytes;
- peak resident memory during training and inference;
- active concepts, edges and schema candidates per answer;
- estimated sparse operations per answer;
- training time and number of surprise writes;
- scaling at 10K, 100K and 1M facts.

A larger model is accepted only if it is Pareto-efficient in capability, memory, active computation and training cost.

## Immediate HS4 milestone

Build an executable raw-pattern miner that discovers two-slot relations from unlabeled sentence groups, aligns lookup and yes/no query forms from weak QA supervision, and answers held-out questions through the existing bounded relational cortex. The first CI scale target is 100,000 raw sentences with fewer than 512 active candidates per query.
