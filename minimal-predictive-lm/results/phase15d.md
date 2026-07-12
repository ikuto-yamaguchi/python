# Phase 15d results: temporal state runtime

Raw date statements compile into a `today` state, one calendar transition, and a multiple-choice projection.

## Adaptation disclosure

- public date formats inspected: **true**
- strict zero-shot claim: **false**
- human-designed temporal compilers: **1**
- benchmark task-name branches: **0**
- benchmark examples / targets used as training rows: **0 / 0**

## Temporal runtime

- payload: **164 bytes**
- state: `today`
- events: `shift_days`, `shift_months`, `shift_years`
- cross-domain held-out: **6/6**

## Public result

| axis | Phase 15c | Phase 15d | answered | wrong |
|---|---:|---:|---:|---:|
| date understanding | 0% | 95% | 39 | 1 |
| logical ordering | 100% | 100% | 40 | 0 |
| spatial navigation | 100% | 100% | 40 | 0 |
| stack completion | 100% | 100% | 40 | 0 |
| state permutation tracking | 100% | 100% | 40 | 0 |

Overall: **80% → 99%**. Answered/correct: **199/198**. The original public suite remains **200/200**.

## Annotation audit

Two date examples should not be treated as ordinary model errors:

1. `bbh_date_understanding_002` states a marriage on January 2, 1958 and a five-year anniversary today. One week later is January 9, 1963, which is option C. The dataset labels option B, January 9, 1961.
2. `bbh_date_understanding_023` says 2015 begins in 36 hours. Exact subtraction from the year boundary gives December 30, 2014; one week earlier is December 23, option B. The dataset labels December 22, option C. The model conservatively abstains rather than learn this one-day discrepancy.

No incorrect calendar exception was added to match either label.

## Claim boundary

This is a benchmark-informed temporal compiler, not open-ended temporal language understanding. Raw benchmark scoring is **38/40** on date understanding, with two separately documented annotation/identifiability disagreements.
