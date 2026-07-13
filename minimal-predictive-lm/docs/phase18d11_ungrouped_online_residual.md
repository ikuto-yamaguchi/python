# Phase 18d-11: ungrouped online residual invention

## Motivation

Phase 18d-10 invents a primitive from residual examples that are already grouped into episodes. Phase 18d-11 removes those task and residual-group boundaries.

The learner receives one ordered stream of typed input/output records containing known transformations, repeated unknown transformations, and isolated noise. Audit labels are stored separately and are never passed to the learner.

## Online protocol

For each record:

1. predict with the locally persistent active operation before reading the output;
2. reveal the output and identify a matching known or invented operation when possible;
3. otherwise append the record to an ungrouped residual pool;
4. search a generic length-preserving affine-index meta-grammar over the observed residuals;
5. promote a primitive only when a cross-type residual subset has minimum support, positive MDL gain, and a unique probe behavior.

A lookup-table control is included in the candidate space. One-off residuals remain literal noise and must not be promoted.

## Gates

- stream records contain only `input` and `output`;
- promotion uses string and number-list evidence without task IDs or residual groups;
- every support record selected for the promoted primitive is a true hidden-transformation audit record;
- the invented primitive predicts every future hidden record;
- one-type evidence, competing hidden transformations, and isolated noise do not promote;
- prediction errors are confined to unannounced change-point regret or noise;
- audit labels are not accepted by the learner API.

## Claim boundary

Records still expose typed input/output fields, the candidate meta-grammar and persistence mechanism are human-designed, and only one primitive is promoted. This is a controlled online residual-clustering experiment, not raw-byte, natural-language, or unrestricted LLM-like learning.
