# Phase 11c results: residual-driven primitive invention

The fixed Phase 11a grammar cannot express the string transformation. Candidate
representations are proposed from aligned residuals and selected by cross-family
validation plus a normalized lifetime objective.

## Fixed grammar boundary

- unexpressible detected: **True**
- fixed-grammar candidates before failure: **1,182**

## Candidate proposals

| kind | bits | train | cross-family validation |
|---|---:|---:|---:|
| conditional_character_offset | 760 | 100.0% | 100.0% |
| character_map | 2,176 | 100.0% | 100.0% |
| lookup | 2,784 | 100.0% | 0.0% |

No task-specific `UPPERCASE` candidate is supplied. The selected rule is induced as a conditional codepoint interval plus offset.

## Selected primitive

- kind: **conditional_character_offset**
- learned interval: **97–122**
- learned offset: **−32**
- primitive bits: **760**
- program bits: **1,280**
- validation families: **3**
- validation accuracy: **100.0%**
- unseen application-domain accuracy: **100.0%**
- Unicode distribution-shift accuracy: **0.0%**

## Lifetime adoption

- one expected call adopted: **False**
- one-call normalized gain: **−3,720 bits**
- 100 expected calls adopted: **True**
- 100-call normalized gain: **2,616 bits**

The result is representation extension inside a bounded meta-grammar, not proof of unrestricted autonomous primitive invention.

## Limitations

- the proposal language is a fixed meta-grammar rather than an unrestricted primitive generator
- training strings collectively expose the complete ASCII lowercase interval
- the learned codepoint offset does not handle accented letters or one-to-many Unicode case mappings
- task boundaries and aligned input/output demonstrations are supplied
- cross-family validation is small and synthetic
- the normalized lifetime objective uses an explicit experimental error price rather than measured physical energy
