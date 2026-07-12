# Phase 14a results: pinned general ontology with proof-cache compilation

A fixed Open English WordNet 2025 archive is used as a general external knowledge source. No public benchmark example, target, handler, or item-category dictionary is used for training.

## Knowledge accounting

- source SHA-256: `38b16326159f51853626b7d24a44c453fa88ab33f06fce5ec8fc5996d1c2be93`
- full source: **9,616,299 bytes**
- noun synsets / lemmas / hypernym edges: **71,864 / 97,419 / 74,224**
- query proof cache: **82 entries / 15,089 bytes**
- cache/source ratio: **0.1569%**
- independent cross-domain checks: **6/6**

The full ontology is included in the reported model cost even though only query-relevant proof paths are cached.

## Public result

| axis | Phase 13d | Phase 14a |
|---|---:|---:|
| boolean expressions | 100% | 100% |
| direct arithmetic | 100% | 100% |
| multistep arithmetic | 100% | 100% |
| object counting | 30% | 90% |
| word sorting | 100% | 100% |

Overall: **86% → 98%**. Coverage increased from **86% to 100%**, but selective accuracy fell from **100% to 98%** because four object-counting answers were wrong.

## Residual diagnosis

The four wrong examples are:

- `bbh_object_counting_008`
- `bbh_object_counting_023`
- `bbh_object_counting_027`
- `bbh_object_counting_028`

Every error is an undercount of exactly one. All four contain garlic. Open English WordNet 2025 resolves the other vegetables but has no `garlic → vegetable` hypernym path. No garlic exception was added in this phase.

## Claim boundary

This is a zero-benchmark-training transfer result using a large human-curated external ontology. It is not autonomous world-knowledge learning, not perfect public accuracy, and not evidence of general LLM parity.
