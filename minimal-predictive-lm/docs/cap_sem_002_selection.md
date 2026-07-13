# CAP-SEM-002 implementation selection

## Decision

`cap_sem_002_raw_japanese_bridge` is the canonical CAP-SEM-002 implementation.

`cap_sem_002_raw_japanese_grounding` is retained only as a parser-search ablation.

## Why the higher-search candidate was not promoted

Both implementations reach perfect held-out scores on their declared controlled distributions. Score alone is not the capability definition.

CAP-SEM-002 requires the complete CAP-SEM-001 relation map and graph runtime to remain frozen while only the raw-surface bridge is learned. The canonical bridge fingerprints the semantic payload before and after bridge fitting and requires byte identity.

The experimental grounding candidate calls `learn_meaning` from its CAP-SEM-002 fitting path. It therefore relearns the semantic map after parsing the raw training set. This violates the dependency contract even though its parser search is useful and its accuracy is high.

## Canonical evidence

The selected bridge learns from continuous controlled Japanese strings paired only with final Boolean labels. It induces delimiter roles, entity spans, six recurring surface skeletons, and argument orientation, then sends every recovered record to the unchanged CAP-SEM-001 predictor.

The gate requires:

- at least 95% held-out accuracy and coverage;
- at least a 25-point gain over raw-text memorization;
- template, fact-order, and punctuation transfer;
- a byte-identical CAP-SEM-001 fingerprint;
- at most 4,096 learned bridge bytes;
- fewer than 128 average semantic inference operations.

## Scientific lesson

A more flexible search procedure is not automatically a more general intelligence mechanism. Relearning a downstream semantic solver can hide a failure of modular transfer. Capability promotion therefore depends on dependency preservation, not only task score.

## Claim boundary

CAP-SEM-002 removes supplied clause arrays and argument slots for a finite controlled Japanese grammar. It does not establish unrestricted Japanese understanding, morphology, ellipsis, coreference, world knowledge, dialogue, or high-school-level intelligence.

## Next capability

CAP-SEM-003 must learn genuinely unseen relation expressions from definitions and usage in a mixed continuous stream while preserving the same graph runtime. Adding another relation-specific parser or solver does not count.
