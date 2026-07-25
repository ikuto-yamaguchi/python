# RESET-E037 — R0 Research Reconstruction integration

Date: 2026-07-26
Branch: `research/intelligence-swarm-reconstruction-001`

## Scope and governance

This integration keeps the canonical reconstruction branch as the only active work base. It adds no toy mechanism, operation/goal hypothesis, memory, replay, fast weights, sleep, forgetting, architecture family, branch, or stacked PR chain. Existing stacked draft PRs remain negative-results archives.

No external learned capability baseline has yet produced an immutable three-seed bundle that passes the unified contract. Therefore no novelty, intelligence principle, capability progress, or stage transition is recognized.

## 1. Primary literature and official-code overlap audit

### C030 — lossy projected causal abstraction

Xia and Bareinboim, “Causal Abstraction Inference under Lossy Representations” (ICML 2025), formalize projected abstractions in which multiple low-level interventions may collapse to one high-level intervention while observational, interventional, and counterfactual queries remain identifiable at the abstract level.

This removes the following from the novelty space:

- many-to-one intervention mappings are not inherently invalid;
- language is not required merely because the representation is lossy;
- exact high-level causal-query recovery does not imply recovery of the fine-grained intervention-target partition;
- a human-readable high-level label does not identify which low-level intervention occurred.

The paper-specific official reproduction repository was not verified, so no public baseline run was started.

RQ-001 is narrowed to distinctions inside a projected-abstraction fibre that remain invisible to the strongest valid non-language abstraction. Adoption requires an externally fixed denotational law that removes every fibre-preserving joint recoding. Status: **not adopted**.

## 2. SILG / J-CRe3 reproduction progress

R0.1 remains unchanged:

- pinned SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`;
- pinned RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`;
- official `multi` recurrent, no pretrained language model;
- seeds `1,7,19`;
- prior run `30158106220` completed 131,072-requested-frame training and matched controls, then failed downstream before artifact upload;
- immutable accepted 131,072-frame bundle: **0**;
- learned public capability baseline reproduction: **0**;
- J-CRe3 external Japanese baseline: **not reproduced**.

The split-job workflow remains the required next execution path: R0.1 must freeze and upload its bundle before R0.2 starts.

## 3. Controls and statistics

The preregistered method set remains exactly:

- Correct;
- Random;
- Language-blind;
- State-only;
- Target-label shuffle;
- Outcome shuffle.

D031 adds an evidence-chain auditor for prediction and statistics artifacts. Every method/seed run must declare a prediction JSONL path and SHA-256; the manifest must also declare a statistics artifact path and SHA-256. Prediction rows must match the declared method, contain finite JSON values, use exactly seeds `1,7,19`, and the statistics object must contain coverage, cell statistics, summaries, and paired gaps versus Correct. A statistics report declaring failure remains a failure even when checksummed.

The dedicated PR-triggered CI run `30171670131` completed successfully. This validates the auditor and its regression tests only; it does not qualify a real benchmark bundle.

## 4. Model, RSS, runtime, seed, and split

No new accepted model or resource measurements were produced. The only accepted resource evidence remains the earlier 32,768-requested-frame run:

- parameters `4,916,915`;
- state-dict audit `19,694,385 bytes`;
- maximum RSS `505,600 KiB`;
- three-seed training wall time `1,033.885 s`;
- CPU forward audit `6.911 ms/step`.

The 131,072-frame run's checkpoint, model bytes, RSS, training time, CPU latency, raw logs, and checksums remain unaccepted because no immutable artifact was preserved.

## 5. Leakage and provenance

The unified contract now includes D015–D031. D031 closes a post-evaluation substitution path: preserving model/data/log hashes is insufficient if predictions or the derived statistics report can be replaced after evaluation. Any missing, malformed, modified, mismatched, non-finite, incomplete, or failure-classified prediction/statistics evidence is classified as `initial_reproduction_failure`.

Accepted real R0 bundles passing the complete contract: **0**.

## 6. R0.2 fidelity boundary

The Gaddy–Klein public-code reference is now immutably pinned:

- repository `kristyelee/environment-learning`;
- historical reference `dgaddy/environment-learning`;
- commit `98c0dc68926ee9535f15019922d2ca871b0ac0b5`;
- inspected reference-file Git blob SHAs recorded in `GADDY_KLEIN_PUBLIC_REFERENCE_MANIFEST.json`.

This closes the author-code revision and inspected-file pinning gap. It does not make the SILG/RTFM port a numerical reproduction. Remaining blockers are a fail-closed author-component to SILG-component mapping, native-task execution, the language-data-efficiency curve, an immutable R0.1 source artifact, a real three-seed dynamics-holdout result, and complete resource/statistics/leakage qualification.

RTFM S1 still supports dynamics holdout only; entity and language-form holdouts remain formally inapplicable.

## 7. RQ-001 decision

Decision after C030:

> **NARROWED BEYOND LOSSY PROJECTED CAUSAL ABSTRACTIONS — NOT ADOPTED**

The surviving candidate asks whether an externally fixed language law can identify fine-grained target partitions and raw-utterance equivalence classes inside a lossy abstraction fibre after every high-level causal query available to the non-language baseline has already been identified.

Necessary but insufficient condition:

`I(P_fiber ; L | A_proj, X, A, Y, H) > 0`

Adoption additionally requires a proof that the language anchor makes the fibre-preserving joint automorphism group trivial, plus an impossibility theorem for language that merely names the high-level projected intervention.

## Formal state

- R0.1 immutable 131,072-frame bundle: **0**
- public learned capability baseline reproduction: **0**
- R0.2 formal reproduction: **0**
- real R0 bundle passing D015–D031: **0**
- R0.3 hidden intervention-target track: **rejected**
- broad RQ-001: **rejected**
- narrowed RQ-001: **not adopted**
- novelty matrix: **incomplete**
- central preregistration: **incomplete**
- evaluation classification: **`initial_reproduction_failure`**
- new intelligence principle: **none**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next-stage proposal: **none**
