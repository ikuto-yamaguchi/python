# Phase 15d: temporal state and annotation audit

## Representation

Date prompts compile into a `today` state, exactly one calendar transition, and option projection. Supported transitions are day, month, and year shifts. Anchor derivation covers explicit dates, tomorrow/yesterday references, locale ordering, elapsed days, monthly recurrence, anniversaries, first weekdays, month/year boundaries, and named calendar anchors.

The same 164-byte runtime passes six independent held-out prompts. No task-name branch is used.

## Public result

The previously unsupported date axis reaches 38/40 under the raw benchmark labels. Combined with Phase 15c, the second public suite reaches 198/200 scored correct, while the original public suite remains 200/200.

## Annotation audit

Two residuals are not ordinary implementation errors:

- A prompt states a marriage on January 2, 1958 and a five-year anniversary today. The entailed answer one week later is January 9, 1963, present as option C, while the label is January 9, 1961.
- A prompt states that 2015 begins in 36 hours. Subtracting 36 hours from the start of 2015 yields December 30, 2014; one week earlier is December 23, option B, while the label is December 22.

The implementation does not add incorrect exceptions to reproduce these labels. Raw benchmark accuracy remains reported as 38/40, with the disagreement recorded separately.

## Limitations

The temporal compiler is benchmark-informed and rule-bounded. Special anchors are human-specified, natural-language temporal resolution is not induced, and the result does not imply open-ended calendar reasoning or general LLM parity.
