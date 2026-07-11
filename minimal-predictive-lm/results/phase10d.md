# Phase 10d results: grounded external knowledge with provenance and abstention

Source reliability is learned from calibration outcomes. Claims are indexed by
grounded concept keys, contradictory values are retained with provenance, and
the machine abstains when weighted evidence is insufficient.

## Corpus

- claims: **4,000**
- known subjects / unknown queries: **1,000 / 100**
- conflicting subjects: **700**
- indexed knowledge bits: **3,354,640**

## Policies

| policy | selective accuracy | coverage | claim reads | mean reads |
|---|---:|---:|---:|---:|
| always answer | 98.0% | 90.9% | 4,000 | 3.636 |
| indexed exhaustive + abstain | 100.0% | 89.1% | 4,000 | 3.636 |
| adaptive confidence + abstain | 100.0% | 89.1% | 2,120 | 1.927 |

- naive full-scan reads: **4,400,000**
- adaptive reduction vs full scan: **99.95%**
- adaptive reduction vs indexed exhaustive: **47.00%**

## Stage-C evidence

- readiness points: **7 → 8 / 24**
- knowledge evidence level: **1 → 2**
- Stage C ready: **False**

The score remains below public-benchmark evidence because proposition extraction
and the corpus are synthetic.

## Limitations

- claims are already parsed into subject-relation-value propositions
- source observations are supervised by known truth during calibration
- source reliability is stationary and independent across claims
- the corpus is synthetic and contains one relation
- adaptive stopping optimizes this bounded evidence model, not arbitrary web retrieval
