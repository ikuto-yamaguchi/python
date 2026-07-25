# RESET-E035 — R0 Research Reconstruction integration

Date: 2026-07-26
Branch: `research/intelligence-swarm-reconstruction-001`
Classification: `initial_reproduction_failure`

## Scope

This integration keeps one canonical reconstruction branch. It does not authorize a new toy mechanism, operation/goal hypothesis, memory/replay/fast-weights/sleep/forgetting mechanism, architecture family, synthetic benchmark, branch, or stacked PR chain. Existing stacked drafts remain negative-results archives only.

## 1. Primary literature and official-code boundary

No new admissible prior-art result appeared in the branch after C025. The current boundary therefore remains C023–C025:

- state-dependent local dynamics can identify system parameters without language under explicit assumptions;
- isolated causal effects of specified language interventions do not identify raw-utterance equivalence or a latent intervention-target partition;
- mechanistic-independence criteria can identify latent components without language, and naming such a component does not identify its internal partition.

RQ-001 remains narrowed and not adopted. Adoption still requires an explicit residual countermodel pair after the strongest non-language criteria, an externally fixed anti-recoding language anchor, a strict joint-identification theorem, an impossibility result without that anchor, finite-sample or consistency guarantees, public baseline reproduction, and exactly one preregistered claim with a stopping rule.

## 2. R0.1 / SILG reproduction

Run `30158106220` remains the latest substantive long run. It completed pinned SILG/RTFM installation, schema/random probing, official recurrent training at 131,072 requested frames for seeds `1,7,19`, and matched Correct/Random/Language-blind/State-only/Language-shuffle evaluation. It then failed in the downstream R0.2 step before dependency freeze and artifact upload. Workflow artifacts were empty.

Therefore no checkpoint, performance value, model bytes, peak RSS, wall time, CPU inference latency, raw log, or checksum from that run is accepted evidence. The canonical split-job workflow remains mandatory: R0.1 must freeze and upload its immutable bundle before R0.2 may consume it.

## 3. Controls and statistics

The preregistered prediction topology remains exactly:

- `correct`
- `random`
- `language_blind`
- `state_only`
- `target_label_shuffle`
- `outcome_shuffle`

All methods must use the same evaluation instances and the same observed `domain × seed × split × condition` topology. Mean gaps, minimum-cell gaps, confidence intervals and paired tests remain required. No real bundle has passed these requirements.

## 4. Resources, seeds and splits

Required seeds remain exactly `1,7,19`. Each observed evaluation cell must contain all seeds and all six methods. Model bytes, peak RSS, training wall time, CPU inference latency, raw logs, source/model/data/prediction checksums, full code commit, and immutable split/domain metadata remain required.

## 5. Leakage and provenance — D029 integration

D029 closes a core-contract bypass that remained after the companion auditors were added.

`evaluation_contract.py` itself now rejects:

- any prediction or artifact method outside the exact six-method registry;
- mixed full code commits within one bundle;
- different `data_path + data_sha256` identities across methods in one `seed × domain × split × condition` cell.

This prevents callers that invoke only the core contract from bypassing the stricter method-topology and artifact-identity checks. Existing utterance-overlap, entity/dynamics split, gold action/after-state, completed-trajectory/post-treatment, semantic-alias, seed/domain, prediction-coverage, shuffle-provenance, resource and checksum audits remain in force.

The focused local regression reported by D029 passed, but the current head has no published combined-status checks. This is code-path evidence only, not a benchmark result.

## 6. R0.2 and hidden intervention-target track

R0.2 still has no accepted three-seed result for task success, next-state prediction, action accuracy, or dynamics transfer. RTFM S1 supports a genuine dynamics holdout only; entity and language-form holdouts remain formally inapplicable.

R0.3 remains rejected because SILG/RTFM does not expose the required ground-truth latent intervention family, target, mechanism operator, or causal abstraction. No researcher-authored ontology may be introduced to manufacture that supervision.

## Integrated decision

- accepted learned public capability baseline: **0**
- immutable 131,072-frame R0.1 bundle: **0**
- formal R0.2 reproduction: **0**
- real R0 bundle passing the unified contract: **0**
- R0.3 hidden intervention-target track: **rejected**
- broad RQ-001: **rejected**
- narrowed RQ-001: **not adopted**
- novelty matrix: **incomplete**
- central preregistration: **incomplete**
- new intelligence principle: **none**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next-stage proposal: **none**

The formal classification remains `initial_reproduction_failure`.