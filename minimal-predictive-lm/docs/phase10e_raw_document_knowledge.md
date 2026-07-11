# Phase 10e: raw documents, evidence correlation, and retrieval VOI

## Motivation

Phase 10d received already-grounded propositions. That leaves three major costs hidden:

1. converting raw language into a proposition,
2. preserving the exact source span for audit and retraction,
3. deciding whether two documents are independent evidence or copies of one origin.

Phase 10e makes those costs explicit. A raw document is converted into:

```text
(subject, relation, value, topic, time, source, origin, provenance span)
```

The active decision state uses the proposition. The raw document remains available through the provenance span rather than being copied into every reasoning step.

## Context-dependent trust

A source does not have one timeless reliability number. Its evidence is represented by sufficient statistics conditioned on source, topic, and era:

```text
(successes, failures)_(source, topic, era)
```

A Laplace-smoothed posterior reliability is converted into log-odds evidence. A global source estimate remains only as a fallback when a contextual cell has not been observed.

## Copy correlation

Ten pages repeating one original report are not ten independent experiments. Documents connected through `copied_from` are resolved to one origin. Claims from one origin form one evidence unit and are not allowed to multiply their vote merely through syndication.

This experiment supplies copy lineage as metadata. Future phases must infer common origin from quotation spans, publication time, URLs, and semantic overlap.

## Retrieval value

For binary propositions, the current log-odds define a belief `q`. A candidate source with calibrated reliability `r` has an expected posterior entropy. The one-step information value is:

```text
VOI = information_value * (H(q) - E[H(q | observation)]) - read_cost
```

A document is read only if its expected information gain repays the read cost. The policy may abstain when no remaining read has positive value and confidence remains insufficient.

A separate lower-bound check stops early only when the worst possible unread evidence cannot reduce confidence below the decision threshold.

## Lifetime objective

The comparison includes:

```text
extraction errors
+ proposition and provenance bits
+ trust statistics
+ copied-evidence correlation state
+ claim reads
+ abstention and answer loss
+ extraction / indexing / calibration cost
```

A smaller active belief is not counted as efficient if it relies on an unmeasured full-corpus scan or silently duplicates copied evidence.

## Result boundary

The experiment demonstrates the architecture on bounded Japanese and English sentence forms. It does not establish open-domain proposition extraction, entity resolution, arbitrary relation induction, or public retrieval-QA performance. Stage-C knowledge evidence therefore remains level 2.

## Next steps

1. infer copy lineage rather than receiving it as metadata,
2. extract multiple and nested propositions from unrestricted text,
3. learn entity and relation boundaries jointly with the concept workspace,
4. model source dependence beyond exact copies,
5. run public retrieval and open-domain QA benchmarks,
6. compare matched quality, peak RSS, latency, operations, and energy against small open models.
