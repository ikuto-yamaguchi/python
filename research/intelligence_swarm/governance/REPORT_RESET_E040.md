# RESET-E040 — R0 Research Reconstruction Integration

Date: 2026-07-26
Branch: `research/intelligence-swarm-reconstruction-001`

## Scope lock

This integration keeps one canonical reconstruction branch and does not authorize new toy mechanisms, operation/goal hypotheses, memory/replay/fast-weights/sleep/forgetting work, architecture families, branches, or stacked PR chains. Existing stacked drafts remain negative-results archives only.

## Newly integrated evidence

### C033 — Partially shared multimodal causal representation identifiability

Benhamza, Clausel, and Tami (2026), *Identifiable Multimodal Causal Representation Learning under Partial Latent Sharing*, was added to the novelty boundary.

Under explicit full-column-rank, properness, partial-sharing graph, independence, non-overlap, mixing-density, and sparsity assumptions, shared and modality-specific latent variables can be identified observationally up to permutation and component-wise smooth bijections. A language channel can therefore be treated as an ordinary modality for this prior-art comparison.

The following do not establish RQ-001 novelty or joint semantic identification:

- aligning language and trajectory through a shared latent block;
- discovering partially shared latent incidence;
- cross-modal reconstruction, Wasserstein alignment, or shared-latent transfer;
- naming an identified shared component with readable language;
- task success or language-shuffle gaps that depend only on that component.

A within-component joint recoding of fine target members, utterance classes, denotation, and language encoder/decoder can preserve the full observable multimodal law and all such metrics. Therefore raw-language equivalence and a fine latent intervention-target partition remain unidentified without an externally fixed anti-recoding denotation law.

Formal decision:

> **NARROWED BEYOND PARTIALLY SHARED MULTIMODAL COMPONENT-WISE IDENTIFIABILITY — NOT ADOPTED**

No paper-specific author-controlled immutable code repository was verified, so no baseline run was started.

### D034 — Alias-normalized leakage audit

A concrete schema bypass was closed. Exact snake_case checks could miss semantically identical keys such as `goldStateAfter`, `gold-action`, `completedTrajectory`, `terminalObservation`, or `episodeReturn`.

The new recursive auditor case-folds keys and removes non-alphanumeric characters before comparison. It inspects:

- `model_input_fields`;
- nested dictionaries/lists under `model_input`;
- prediction top-level keys;
- unregistered prediction fields.

Any oracle, post-treatment, outcome, terminal, or completed-trajectory alias fails closed as `initial_reproduction_failure`.

Current-head pull-request workflow runs:

- unified acceptance gate `30177596329`: success;
- prediction method topology `30177596328`: success.

These are audit-code regression results only. No real benchmark bundle has passed.

### R0.2 holdout provenance

The typed-trajectory/holdout-manifest path now strengthens duplicate, missing-row, and domain/split/seed/episode-seed mismatch rejection. This improves provenance but creates no accepted Environment-first result.

## Benchmark status

R0.1 accepted evidence remains the earlier 32,768-requested-frame three-seed run. Run `30158106220` completed 131,072-requested-frame training and matched controls but lost every artifact after downstream R0.2 failure. Therefore no checkpoint, performance value, model bytes, RSS, wall time, CPU latency, raw log, or checksum from that run is accepted.

`R01_RUN_REQUEST.json` was updated, but a run request is not evidence. The next accepted attempt must freeze and upload the complete R0.1 bundle before R0.2 starts.

R0.2 remains a method transfer, not an ACL 2019 numerical reproduction. Native author-code execution, the language-data-efficiency curve, immutable R0.1 input, and qualified three-seed dynamics-holdout results remain missing. RTFM S1 still supports only a real dynamics holdout; entity and language-form holdouts remain formally inapplicable.

## Stage decision

- immutable 131,072-frame R0.1 bundle: **0**
- accepted learned public capability baseline: **0**
- formal R0.2 reproduction: **0**
- real R0 bundle passing D015–D034: **0**
- R0.3 hidden intervention-target track: **rejected**
- broad RQ-001: **rejected**
- narrowed RQ-001: **further narrowed, not adopted**
- novelty matrix: **incomplete**
- central preregistration: **incomplete**
- evaluation classification: **`initial_reproduction_failure`**
- new intelligence principle: **none**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next stage: **not proposed**
