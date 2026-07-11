# Phase 10e results: raw documents, correlated evidence, and retrieval VOI

Raw Japanese and English sentences are converted into grounded propositions
with exact provenance spans. Trust is conditioned on topic and era, copied
documents share one evidence origin, and additional reads are selected by
bounded information value.

## Raw extraction

- documents / noise documents: **3,700 / 100**
- expected / extracted claims: **3,600 / 3,600**
- precision / recall: **100.0% / 100.0%**
- exact provenance spans preserved: **True**

## Context and copy correlation

- calibration observations: **800**
- contextual trust cells: **16**
- copied documents: **2,000**
- duplicate claims collapsed: **2,000**
- independent evidence origins: **1,600**

## Retrieval policies

| policy | selective accuracy | coverage | claim reads |
|---|---:|---:|---:|
| global trust, copies independent | 93.2% | 78.2% | 3,184 |
| topic/time trust, copies independent | 96.5% | 76.4% | 3,184 |
| contextual + correlated exhaustive | 100.0% | 70.2% | 1,444 |
| contextual + correlated + VOI | 100.0% | 68.4% | 748 |

- raw full-scan reads: **1,665,000**
- VOI reduction vs full scan: **99.96%**
- VOI reduction vs correlated exhaustive: **48.20%**

## Stage-C evidence

- readiness points: **8 → 8 / 24**
- knowledge level: **2**
- Stage C ready: **False**

The architecture advanced, but the evidence remains synthetic; the score is
therefore deliberately unchanged.

## Limitations

- the raw parser supports two bounded sentence forms
- entities, relations, and values use simple token boundaries
- source correctness is supervised during calibration
- copy lineage is supplied as metadata
- the evidence model is binary and conditionally independent across origins
- the corpus is synthetic and does not justify Stage-C level 3
