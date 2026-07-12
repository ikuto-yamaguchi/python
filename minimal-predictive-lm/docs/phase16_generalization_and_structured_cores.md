# Phase 16: frozen failure boundaries, proposition generalization, and structured cores

## Objective

Phase 16 stops extending the earlier benchmark formats and asks whether the existing system transfers to a fully unused public slice. When it fails, each subsequent phase must either improve calibration, introduce a reusable internal mechanism, reduce manual surface structure, or establish a benchmark-free core. Task-name dispatch and benchmark-item dictionaries remain forbidden.

The third public slice contains 200 BIG-Bench-Hard examples, forty each from causal judgement, reference resolution, formal validity, adjective order, and belief propagation. Its deterministic manifest SHA-256 is `301961a22528e4e5595ee089a7c2d20a0071b1cedf2b82d4db7bf72f6bce6f92`.

## Phase 16a: frozen third-slice boundary

The complete Phase 15d system is fingerprinted before the new prompts are evaluated. No example, target, primitive, document, handler, or surface compiler is added.

- frozen result: **0/200**
- answered / wrong / abstained: **1 / 1 / 199**
- exact overlap with the first two public slices: **0**
- model fingerprint unchanged: **true**

The only non-abstention came from a formal-validity prompt containing the club name `Bayer 04 Leverkusen`. The compact numeric learner treated the isolated `04` as an arithmetic argument and returned `8`. This exposed a routing-calibration bug rather than a reasoning capability.

## Phase 16b: sparse-number routing guard

A 133-byte generic guard admits explicit `key=value` records and compact prompts containing at least two numeric arguments. It rejects multiline text, long unstructured prose, and isolated years, versions, product numbers, or model numbers.

- third slice wrong answers: **1 → 0**
- third slice after guard: **0 answered, 200 abstained**
- original public regression: **200/200**
- second public raw regression: **198/200**
- new reasoning capability: **none**

The thresholds are human selected and remain a bounded routing rule.

## Phase 16c: shared proposition runtime

Two reusable proposition mechanisms are added:

1. a signed attributed-claim graph for base truth assignments and positive or negative reports;
2. finite-model entailment for an equality-free monadic controlled language.

Truth and attribution phrases are grounded from independent observations. Contradictions and unanchored cycles force abstention. Public task names are never passed to execution.

- independent testimony / sensor-audit / code-review / formal held-out: **5/5**
- belief propagation: **40/40**
- formal validity: **40/40**
- third public slice: **80/200**, all eighty answered predictions correct
- original public regression: **200/200**
- second public raw regression: **198/200**
- proposition payload at the measured run: **774 bytes**

This is benchmark-informed post-hoc adaptation. Public formats were inspected; it is not strict zero-shot language acquisition.

## Phase 16d: queue-based signed propagation

The signed-claim fixed point is changed from repeated full-graph scans to a queue/work-list schedule. The production `CorrectedPropositionMachine`, not only the comparison harness, uses the new runtime.

- reverse 1,024-claim chain, legacy operations: **1,049,601**
- queue operations: **3,073**
- operation reduction: **341.6×**
- randomized renamed/order-shifted chains: **100/100**
- contradiction, unanchored cycle, and unknown grounding: **all abstained**
- model size independent of chain length: **true**
- runtime payload: **822 bytes**

The operation count is linear in discovered signed values plus edges. Natural-language compilation is still outside this result.

## Phase 16e: benchmark-free norm-aware causal core

A 307-byte structured causal adjudicator separates physical dependence from normality-based responsibility selection. It supports threshold structural equations, direct interventions, normality-improving contingency search, abnormal conjunct selection, controlled expected action, goals, foreseen side effects, and accidental-realization rejection.

- renamed and event-order shifted structured scenarios: **200/200**
- intention cases: **6/6**
- irrelevant-variable metamorphic checks: **5/5**
- public causal examples or targets used: **0**
- public causal-axis claim: **not allowed**

Events, normal values, structural equations, and intention evidence are supplied as canonical structured inputs. Natural-language causal extraction, omissions, duties, proximate causation, and multi-stage preemption remain open.

## Phase 16f: supervised clause-template induction

The hand-written claim regex in the evaluated path is replaced by token-class templates induced from seven independent raw-clause plus canonical-event observations. The observations produce exactly three templates:

- `ENTITY TRUTH`
- `SPEAKER ATTRIBUTION TARGET TRUTH`
- `does ENTITY TRUTH`

The queue runtime and controlled formal-language compiler are retained.

- induced templates: **3**
- compiler payload: **665 bytes**
- public prediction equivalence with the hand-written claim compiler: **200/200**
- belief / formal retention: **40/40 / 40/40**
- randomized renamed/order-shifted claim chains: **100/100**
- unknown word order, unknown truth phrase, contradiction, and unanchored cycle: **all abstained**
- original / second public regressions: **200/200 / raw 198/200**
- manual claim surface compilers in the evaluated path: **1 → 0**

Canonical event types and argument roles are supervised. The token classes and induction algorithm are human designed, and the formal-language compiler remains manual. This is not autonomous parser induction.

## Phase 16g: induced evidence-factored reference core

Before parsing raw pronoun questions, a structured reference-resolution core is induced from seventeen canonical evidence observations. Agreement is a hard compatibility filter. Remaining signals receive bounded nonnegative integer weights selected by exhaustive search over 78,125 assignments. A unique positive maximum is resolved; ties and nonpositive maxima are ambiguous.

Induced weights:

| evidence | weight |
|---|---:|
| object control | 3 |
| subject control | 3 |
| subject continuity | 2 |
| possessive link | 2 |
| semantic fit | 2 |
| parallel role | 2 |
| recency | 1 |

Results:

- runtime payload: **376 bytes**
- calibration: **17/17**
- structured held-out: **8/8**
- renamed and candidate-order shifted: **200/200**
- incompatible-distractor invariance: **7/7**
- removing the decisive evidence restores ambiguity: **true**
- public reference-axis claim: **not allowed**

Mention candidates, agreement, grammatical-control evidence, possessive links, and semantic compatibility are supplied. A natural-language compiler is still absent.

## Current public boundary

Across the three public slices:

- first slice: **200/200**
- second slice: **raw 198/200**; the two remaining labels are preserved as annotation disagreements rather than patched
- third slice: **80/200**, with belief propagation and formal validity at 40/40 and causal judgement, reference resolution, and adjective order still unopened

The third-slice result is post-hoc and format-informed. The causal and reference cores are benchmark-free structured foundations, not raw-language capability.

## Main unresolved problems

1. infer event, proposition, causal, and reference evidence from unrestricted raw language rather than receiving canonical roles;
2. learn syntax and semantics beyond exact token-class templates;
3. ground semantic compatibility without benchmark-item dictionaries;
4. handle probabilistic credibility, graded ambiguity, causal DAGs, omissions, preemption, and cultural normality;
5. demonstrate free-form dialogue, real-repository coding, long context, open-domain generation, multimodal grounding, and continual autonomous acquisition;
6. compare against a matched open model on the third public slice without relaxing input, tools, or scoring.

No Phase 16 result authorizes general-LLM parity, human-level intelligence, or open-ended generality.
